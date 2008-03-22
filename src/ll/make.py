#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Copyright 2002-2008 by LivingLogic AG, Bayreuth/Germany.
## Copyright 2002-2008 by Walter Dörwald
##
## All Rights Reserved
##
## See __init__.py for the license


"""
:mod:`ll.make` provides tools for building projects.

Like make it allows you to specify dependencies between files and actions to be
executed when files don't exist or are out of date with respect to one of their
sources. But unlike make you can do this in an object oriented way and targets
are not only limited to files.

Relevant classes are:

*	:class:`Project`, which is the container for all actions in a project and

*	:class:`Action` (and subclasses), which are used to transform input data
	and read and write files (or other entities like database records).

A simple script that copies a file :file:`foo.txt` to :file:`bar.txt`
reencoding it from ``"latin-1"`` to ``"utf-8"`` in the process looks like
this::

	from ll import make, url

	class MyProject(make.Project):
		def create(self):
			make.Project.create(self)
			source = self.add(make.FileAction(url.File("foo.txt")))
			target = self.add(
				source /
				make.DecodeAction("iso-8859-1") /
				make.EncodeAction("utf-8") /
				make.FileAction(url.File("bar.txt"))
			)
			self.writecreatedone()

	p = MyProject()
	p.create()

	if __name__ == "__main__":
		p.build("bar.txt")
"""


from __future__ import with_statement

import sys, os, os.path, optparse, warnings, re, datetime, cStringIO, errno, tempfile, operator, types, cPickle, gc, contextlib

from ll import misc, url

try:
	import astyle
except ImportError:
	from ll import astyle


__docformat__ = "reStructuredText"


###
### Constants and helpers
###

nodata = misc.Const("nodata") # marker object for "no new data available"
newdata = misc.Const("newdata") # marker object for "new data available"

bigbang = datetime.datetime(1900, 1, 1) # there can be no timestamp before this one
bigcrunch = datetime.datetime(3000, 1, 1) # there can be no timestamp after this one


def filechanged(key):
	"""
	Get the last modified date (or :const:`bigbang`, if the file doesn't exist).
	"""
	try:
		return key.mdate()
	except (IOError, OSError):
		return bigbang


class Level(object):
	"""
	Stores information about the recursive execution of :class:`Action`\s.
	"""
	__slots__ = ("action", "since", "infoonly", "reportable", "reported")

	def __init__(self, action, since, infoonly, reportable, reported=False):
		self.action = action
		self.since = since
		self.infoonly = infoonly
		self.reportable = reportable
		self.reported = reported

	def __repr__(self):
		return "<%s.%s object action=%r since=%r infoonly=%r reportable=%r reported=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.action, self.since, self.infoonly, self.reportable, self.reported, id(self))


def report(func):
	"""
	Standard decorator for :meth:`Action.get` methods.

	This decorator handles proper reporting of nested action calls. If it isn't
	used, only the output of calls to :meth:`Project.writestep` will be visible
	to the user.
	"""
	def reporter(self, project, since, infoonly):
		reported = False
		reportable = project.showaction is not None and isinstance(self, project.showaction)
		if reportable:
			if project.showidle:
				args = ["Starting ", project.straction(self)]
				if project.showtimestamps:
					args.append(" since ")
					args.append(project.strdatetime(since))
					if infoonly:
						args.append(" (info only)")
				project.writestack(*args)
				reported = True
		level = Level(self, since, infoonly, reportable, reported)
		project.stack.append(level)
		t1 = datetime.datetime.utcnow()
		try:
			data = func(self, project, since, infoonly)
		except Exception, exc:
			project.actionsfailed += 1
			if project.ignoreerrors: # ignore changes in failed subgraphs
				data = nodata # Return "everything is up to date" in this case
				error = exc.__class__
			else:
				raise
		else:
			project.actionscalled += 1
			error = None
		finally:
			project.stack.pop(-1)
		t2 = datetime.datetime.utcnow()
		if level.reportable or error is not None:
			if (not project.showidle and data is not nodata) or error is not None:
				project._writependinglevels() # Only outputs something if the action hasn't called writestep()
			if level.reported:
				if error is not None:
					text1 = "Failed"
					text2 = " after "
				else:
					text1 = "Finished"
					text2 = " in "
				args = [text1, " ", project.straction(self)]
				if project.showtime:
					args.append(text2)
					args.append(project.strtimedelta(t2-t1))
				if project.showtimestamps:
					args.append(" (changed ")
					args.append(project.strdatetime(self.changed))
					args.append(")")
				if project.showdata:
					args.append(": ")
					if error is not None:
						if error.__module__ != "exceptions":
							text = "%s.%s" % (error.__module__, error.__name__)
						else:
							text = error.__name__
						args.append(s4error(text))
					elif data is nodata:
						args.append("nodata")
					elif data is newdata:
						args.append("newdata")
					elif isinstance(data, str):
						args.append(s4data("str (%db)" % len(data)))
					elif isinstance(data, unicode):
						args.append(s4data("unicode (%dc)" % len(data)))
					else:
						dataclass = data.__class__
						if dataclass.__module__ != "__builtin__":
							text = "%s.%s @ 0x%x" % (dataclass.__module__, dataclass.__name__, id(data))
						else:
							text = "%s @ 0x%x" % (dataclass.__name__, id(data))
						args.append(s4data(text))
				project.writestack(*args)
		return data
	reporter.__dict__.update(func.__dict__)
	reporter.__doc__ = func.__doc__
	reporter.__name__ = func.__name__
	return reporter


###
### exceptions & warnings
###

class RedefinedTargetWarning(Warning):
	"""
	Warning that will be issued when a target is added to a project and a target
	with the same key already exists.
	"""

	def __init__(self, key):
		self.key = key

	def __str__(self):
		return "target with key=%r redefined" % self.key


class UndefinedTargetError(KeyError):
	"""
	Exception that will be raised when a target with the specified key doesn't
	exist within the project.
	"""

	def __init__(self, key):
		self.key = key

	def __str__(self):
		return "target %r undefined" % self.key


###
### Actions
###

def getoutputs(project, since, infoonly, input):
	"""
	Recursively iterate through the object :var:`input` (if it's a
	:class:`tuple`, :class:`list` or :class:`dict`) and return a tuple
	containing:

	*	An object (:var:`data`) of the same structure as :var:`input` where every
		action object encountered is replacd with the output of that action;

	*	A timestamp (:var:`changed`) which the newest timestamp among all the
		change timestamps of the actions encountered.

	*	If none of the actions has any data newer than :var:`since` (i.e. none
		of the actions produces any new data) :var:`data` will be :const:`nodata`.
		If :var:`infoonly` is true and some of the actions would return output,
		:var:`data` will be :const:`newdata`.
	"""
	if isinstance(input, Action):
		return (input.get(project, since, infoonly), input.changed)
	elif isinstance(input, (list, tuple)):
		if infoonly:
			resultdata = nodata
			resultchanged = bigbang
			for item in input:
				(data, changed) = getoutputs(project, since, infoonly, item)
				resultchanged = max(resultchanged, changed)
				if data is not nodata:
					resultdata = data
			return (resultdata, resultchanged)
		else:
			resultdata = []
			havedata = False
			resultchanged = bigbang
			for item in input:
				(data, changed) = getoutputs(project, since, infoonly, item)
				resultchanged = max(resultchanged, changed)
				if data is not nodata and not havedata: # The first real output
					since = bigbang # force inputs to produce data for the rest of the loop
					resultdata = [getoutputs(project, since, infoonly, item)[0] for item in input[:len(resultdata)]] # refetch data from previous inputs
					havedata = True
				resultdata.append(data)
			if havedata:
				if isinstance(input, tuple):
					resultdata = tuple(resultdata)
				return (resultdata, resultchanged)
			return (nodata, resultchanged)
	elif isinstance(input, dict):
		if infoonly:
			resultdata = nodata
			resultchanged = bigbang
			for (key, value) in input.iteritems():
				(data, changed) = getoutputs(project, since, infoonly, value)
				resultchanged = max(resultchanged, changed)
				if data is not nodata:
					resultdata = data
			return (resultdata, resultchanged)
		else:
			resultdata = {}
			havedata = False
			resultchanged = bigbang
			for (key, value) in input.iteritems():
				(data, changed) = getoutputs(project, since, infoonly, value)
				resultchanged = max(resultchanged, changed)
				if data is not nodata and not havedata: # The first real output
					since = bigbang # force inputs to produce data for the rest of the loop
					resultdata = dict((key, getoutputs(project, since, infoonly, input[key])) for key in resultdata) # refetch data from previous inputs
					havedata = True
				resultdata[key] = output
			if not havedata:
				resultdata = nodata
			return (resultdate, resultchanged)
	else:
		raise TypeError("can't handle %r" % type(input))


def _ipipe_type(obj):
	try:
		return obj.type
	except AttributeError:
		return "%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)
_ipipe_type.__xname__ = "type"


def _ipipe_key(obj):
	return obj.getkey()
_ipipe_key.__xname__ = "key"


class Action(object):
	"""
	An :class:`Action` is responsible for transforming input data into output
	data. It may have no, one or many input actions. It fetches, combines and
	transforms the output data of those actions and returns its own output data.
	"""

	def __init__(self):
		"""
		Create a new :class:`Action` instance.
		"""
		self.changed = bigbang

	def __div__(self, output):
		return output.__rdiv__(self)

	@misc.notimplemented
	def get(self, project, since, infoonly):
		"""
		This method (i.e. the implementations in subclasses) is the workhorse of
		:mod:`ll.make`. :meth:`get` must return the output data of the action if
		this data has changed since :var:`since` (which is a
		:class:`datetime.datetime` object in UTC). If the data hasn't changed
		since :var:`since` the special object :const:`nodata` must be returned.
		
		In both cases the action must make sure that the data is internally
		consistent, i.e. if the input data is the output data of other actions
		:var:`self` has to ensure that those other actions update their data too,
		independent from the fact whether :meth:`get` will return new data or not.

		Two special values can be passed for :var:`since`:

		:const:`bigbang`
			This timestamp is older than any timestamp that can appear in real
			life. Since all data is newer than this, :meth:`get` must always
			return output data.

		:const:`bigcrunch`
			This timestamp is newer than any timestamp that can appear in real
			life. Since there can be no data newer than this, :meth:`get` can
			only return output data in this case if ensuring internal consistency
			resulted in new data.

		If :var:`infoonly` is true :meth:`get` must return the constant
		:const:`newdata` instead of real data, if any new data is available.

		In all cases :meth:`get` must set the instance attribute :attr:`changed`
		to the timestamp of the last change to the data before returning. In most
		cases this if the newest :attr:`changed` timestamp of the input actions.
		"""

	def getkey(self):
		"""
		Get the nearest key from :var:`self` or its inputs. This is used by
		:class:`ModuleAction` for the filename.
		"""
		return getattr(self, "key", None)

	@misc.notimplemented
	def __iter__(self):
		"""
		Return an iterator over the input actions of :var:`self`.
		"""

	def iterallinputs(self):
		"""
		Return an iterator over all input actions of :var:`self`
		(i.e. recursively).
		"""
		for input in self:
			yield input
			for subinput in input.iterallinputs():
				yield subinput

	def findpaths(self, input):
		"""
		Find dependency paths leading from :var:`self` to the other action
		:var:`input`. I.e. if :var:`self` depends directly or indirectly on
		:var:`input`, this generator will produce all paths ``p`` where
		``p[0] is self`` and ``p[-1] is input`` and ``p[i+1] in p[i]`` for all
		``i`` in ``xrange(len(p)-1)``.
		"""
		if input is self:
			yield [self]
		else:
			for myinput in self:
				for path in myinput.findpaths(input):
					yield [self] + path

	def __xattrs__(self, mode="default"):
		if mode == "default":
			return (_ipipe_type, _ipipe_key)
		return dir(self)

	def __xrepr__(self, mode="default"):
		if mode in ("cell", "default"):
			name = self.__class__.__name__
			if name.endswith("Action"):
				name = name[:-6]
			yield (s4action, name)
			if hasattr(self, "key"):
				yield (astyle.style_default, "(")
				key = self.key
				if isinstance(key, url.URL) and key.islocal():
					here = url.here()
					home = url.home()
					s = str(key)
					test = str(key.relative(here))
					if len(test) < len(s):
						s = test
					test = "~/%s" % key.relative(home)
					if len(test) < len(s):
						s = test
				else:
					s = str(key)
				yield (s4key, s)
				yield (astyle.style_default, ")")
		else:
			yield (astyle.style_default, repr(self))


class PipeAction(Action):
	"""
	A :class:`PipeAction` depends on exactly one input action and transforms
	the input data into output data.
	"""
	def __init__(self):
		Action.__init__(self)
		self.input = None

	def __rdiv__(self, input):
		"""
		Register the action :var:`input` as the input action for :var:`self` and
		return :var:`self` (which enables chaining :class:`PipeAction` objects).
		"""
		self.input = input
		return self

	def getkey(self):
		return self.input.getkey()

	def __iter__(self):
		yield self.input

	@misc.notimplemented
	def execute(self, project, data):
		"""
		Execute the action: transform the input data :var:`data` and return
		the resulting output data. This method must be implemented in subclasses.
		"""

	@report
	def get(self, project, since, infoonly):
		assert isinstance(self.input, Action)
		(data, self.changed) = getoutputs(project, since, infoonly, self.input)
		if data is not nodata and not infoonly:
			data = self.execute(project, data)
		return data


class CollectAction(PipeAction):
	"""
	A :class:`CollectAction` is a :class:`PipeAction` that simply outputs its
	input data unmodified, but updates a number of other actions in the process.
	"""
	def __init__(self, *inputs):
		PipeAction.__init__(self)
		self.inputs = list(inputs)

	def addinputs(self, *inputs):
		"""
		Register all actions in :var:`inputs` as additional actions that have
		to be updated before :var:`self` is updated.
		"""
		self.inputs.extend(inputs)
		return self

	def __iter__(self):
		yield self.input
		for input in self.inputs:
			yield input

	@report
	def get(self, project, since, infoonly):
		assert isinstance(self.input, Action)
		assert all(isinstance(input, Action) for input in self.inputs)
		# We don't need the data itself, use infoonly mode for the inputs
		(data, changedinputs) = getoutputs(project, since, True, self.inputs)
		if data is not nodata:
			since = bigbang
		(data, changedinput) = getoutputs(project, since, infoonly, self.input)
		self.changed = max(changedinputs, changedinput)
		return data

	def __repr__(self):
		return "<%s.%s object at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, id(self))


class PhonyAction(Action):
	"""
	A :class:`PhonyAction` doesn't do anything. It may depend on any number of
	additonal input actions which will be updated when this action gets updated.
	If there's new data from any of these actions, a :class:`PhonyAction` will
	return :const:`None` (and :const:`nodata` otherwise as usual).
	"""
	def __init__(self, doc=None):
		"""
		Create a :class:`PhonyAction` object. :var:`doc` describes the action and
		is printed by the method :meth:`Project.writephonytargets`.
		"""
		Action.__init__(self)
		self.doc = doc
		self.inputs = []
		self.buildno = None

	def addinputs(self, *inputs):
		"""
		Register all actions in :var:`inputs` as additional actions that have to
		be updated once :var:`self` is updated.
		"""
		self.inputs.extend(inputs)
		return self

	def __iter__(self):
		return iter(self.inputs)

	@report
	def get(self, project, since, infoonly):
		assert all(isinstance(input, Action) for input in self.inputs)
		# Caching the result object of a :class:`PhonyAction` is cheap (it's either :const:`None` or :const:`nodata`),
		# so we always do the caching as this optimizes away the traversal of a complete subgraph
		# for subsequent calls to :meth:`get` during the same build round
		if self.buildno != project.buildno:
			(data, self.changed) = getoutputs(project, since, True, self.inputs)
			self.buildno = project.buildno
		if self.changed > since:
			return None if not infoonly else newdata
		return nodata

	def __repr__(self):
		s = "<%s.%s object" % (self.__class__.__module__, self.__class__.__name__)
		if hasattr(self, "key"):
			s += " with key=%r" % self.key
		s += " at 0x%x>" % id(self)
		return s


class FileAction(PipeAction):
	"""
	A :class:`FileAction` is used for reading and writing files (and other
	objects providing the appropriate interface).
	"""
	def __init__(self, key):
		"""
		Create a :class:`FileAction` object with :var:`key` as the "filename".
		:var:`key` must be an object that provides a method :meth:`open` for
		opening readable and writable streams to the file.
		
		"""
		PipeAction.__init__(self)
		self.key = key
		self.buildno = None

	def getkey(self):
		return self.key

	def write(self, project, data):
		"""
		Write :var:`data` to the file and return it.
		"""
		project.writestep(self, "Writing data to ", project.strkey(self.key))
		with contextlib.closing(self.key.open("wb")) as file:
			file.write(data)
			project.fileswritten += 1

	def read(self, project):
		"""
		Read the content from the file and return it.
		"""
		project.writestep(self, "Reading data from ", project.strkey(self.key))
		with contextlib.closing(self.key.open("rb")) as file:
			return file.read()

	@report
	def get(self, project, since, infoonly):
		"""
		If a :class:`FileAction` object doesn't have an input action it reads the
		input file and returns the content if the file has changed since
		:var:`since` (otherwise :const:`nodata` is returned).

		If a :class:`FileAction` object does have an input action and the output
		data from this input action is newer than the file ``self.key`` the data
		will be written to the file. Otherwise (i.e. the file is up to date) the
		data will be read from the file.
		"""
		if self.buildno != project.buildno: # a new build round
			self.changed = filechanged(self.key) # Get timestamp of the file (or :const:`bigbang` if it doesn't exist)
			self.buildno = project.buildno

		if self.input is not None:
			(data, self.changed) = getoutputs(project, self.changed, False, self.input)
			if data is not nodata: # We've got new data from our input =>
				self.write(project, data) # write new data to disk
				self.changed = filechanged(self.key) # update timestamp
				if infoonly: # no need for the real data
					data = newdata
				return data
		else: # We have no inputs (i.e. this is a "source" file)
			if self.changed is bigbang:
				raise ValueError("source file %r doesn't exist" % self.key)
		if self.changed > since: # We are up to date now and newer than the output action
			if infoonly:
				args = ["Have new data for ", project.strkey(self.key)]
				if project.showtimestamps:
					args.append(" (changed ")
					args.append(project.strdatetime(self.changed))
					args.append(")")
				project.writestep(self, *args)
				return newdata
			return self.read(project) # return file data (to output action or client)
		# else fail through and return :const:`nodata`
		return nodata

	def __repr__(self):
		return "<%s.%s object key=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.key, id(self))


class UnpickleAction(PipeAction):
	"""
	This action unpickles a string.
	"""
	def execute(self, project, data):
		project.writestep(self, "Unpickling")
		return cPickle.loads(data)

	def __repr__(self):
		return "<%s.%s object at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, id(self))


class PickleAction(PipeAction):
	"""
	This action pickles the input data into a string.
	"""
	def __init__(self, protocol=0):
		"""
		Create a new :class:`PickleAction` instance. :var:`protocol` is used as
		the pickle protocol.
		"""
		PipeAction.__init__(self)
		self.protocol = protocol

	def execute(self, project, data):
		project.writestep(self, "Unpickling")
		return cPickle.dumps(data, self.protocol)

	def __repr__(self):
		return "<%s.%s object with protocol=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.protocol, id(self))


class JoinAction(Action):
	"""
	This action joins the input of all its input actions.
	"""
	def __init__(self, *inputs):
		Action.__init__(self)
		self.inputs = list(inputs)

	def addinputs(self, *inputs):
		"""
		Register all actions in :var:`inputs` as input actions, whose data gets
		joined (in the order in which they have been passed to :meth:`addinputs`).
		"""
		self.inputs.extend(inputs)
		return self

	def __iter__(self):
		return iter(self.inputs)

	@report
	def get(self, project, since, infoonly):
		assert all(isinstance(input, Action) for input in self.inputs)
		(data, self.changed) = getoutputs(project, since, infoonly, self.inputs)
		if data is newdata:
			project.writestep(self, "Have new data for join")
		elif data is not nodata:
			project.writestep(self, "Joining data")
			data = "".join(data)
		return data


class ExternalAction(PipeAction):
	"""
	:class:`ExternalAction` is like its baseclass :class:`PipeAction` except
	that :meth:`execute` will be called even if :var:`infoonly` is true.
	"""
	@misc.notimplemented
	def execute(self, project):
		"""
		Will be called to execute the action (even if :var:`infoonly` is true).
		:meth:`execute` doesn't get passed the data object.
		"""

	@report
	def get(self, project, since, infoonly):
		assert isinstance(self.input, Action)
		(data, self.changed) = getoutputs(project, since, infoonly, self.input)
		if data is not nodata:
			self.execute(project)
		return data


class MkDirAction(ExternalAction):
	"""
	This action creates the a directory (passing through its input data).
	"""

	def __init__(self, key, mode=0777):
		"""
		Create a :class:`MkDirAction` instance. :var:`mode` (which defaults to
		:const:`0777`) will be used as the permission bit pattern for the new
		directory.
		"""
		PipeAction.__init__(self)
		self.key = key
		self.mode = mode

	def execute(self, project):
		"""
		Create the directory with the permission bits specified in the
		constructor.
		"""
		project.writestep(self, "Making directory ", project.strkey(self.key), " with mode ", oct(self.mode))
		self.key.makedirs(self.mode)

	def __repr__(self):
		return "<%s.%s object with mode=0%03o at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.mode, id(self))


class CacheAction(PipeAction):
	"""
	A :class:`CacheAction` is a :class:`PipeAction` that passes through its
	input data, but caches it, so that it can be reused during the same build
	round.
	"""
	def __init__(self):
		PipeAction.__init__(self)
		self.since = bigcrunch
		self.data = nodata
		self.buildno = None

	@report
	def get(self, project, since, infoonly):
		assert isinstance(self.input, Action)
		if self.buildno != project.buildno or (since < self.since and self.data is nodata): # If this is a new build round or we're asked about an earlier date and didn't return data last time
			(self.data, self.changed) = getoutputs(project, since, False, self.input)
			self.since = since
			self.buildno = project.buildno
			if infoonly:
				return newdata
		elif self.data is not nodata:
			if infoonly:
				project.writenote(self, "New data is cached")
				return newdata
			project.writenote(self, "Reusing cached data")
		return self.data


class GetAttrAction(PipeAction):
	"""
	This action gets an attribute from its input object.
	"""

	def __init__(self, attrname):
		PipeAction.__init__(self)
		self.attrname = attrname

	def execute(self, project, data):
		project.writestep(self, "Getting attribute ", self.attrname)
		return getattr(data, self.attrname)

	def __repr__(self):
		return "<%s.%s object with attrname=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.attrname, id(self))


class PoolAction(Action):
	"""
	This action collect all its input data into a :class:`ll.misc.Pool` object.
	"""

	def __init__(self, *inputs):
		"""
		Create an :class:`PoolAction` object. Arguments in :var:`inputs` must be
		:class:`ImportAction` or :class:`ModuleAction` objects.
		"""
		Action.__init__(self)
		self.inputs = list(inputs)

	def addinputs(self, *inputs):
		"""
		Registers additional inputs.
		"""
		self.inputs.extend(inputs)
		return self

	def __iter__(self):
		return iter(self.inputs)

	def _getpool(self, *data):
		return misc.Pool(*data)

	@report
	def get(self, project, since, infoonly):
		assert all(isinstance(input, Action) for input in self.inputs)
		(data, self.changed) = getoutputs(project, since, infoonly, self.inputs)

		if data is not nodata and data is not newdata:
			data = self._getpool(*data)
			project.writestep(self, "Created ", data.__class__.__module__, ".", data.__class__.__name__," object")
		return data

	def __repr__(self):
		return "<%s.%s object at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, id(self))


class XISTPoolAction(PoolAction):
	"""
	This action collect all its input data into an :class:`ll.xist.xsc.Pool`
	object.
	"""

	def _getpool(self, *data):
		from ll.xist import xsc
		return xsc.Pool(*data)


class XISTParseAction(PipeAction):
	"""
	This action parses the input data (a string) into an XIST node.
	"""

	def __init__(self, builder=None, pool=None, base=None):
		"""
		Create an :class:`XISTParseAction` object. :var:`builder` must be an
		instance of :class:`ll.xist.parsers.Builder`. If :var:`builder` is
		:const:`None` a builder will be created for you. :var:`pool` must be an
		action that returns an XIST pool object. :var:`base` will be the base
		URL used for parsing.
		"""
		PipeAction.__init__(self)
		if builder is None:
			from ll.xist import parsers
			builder = parsers.Builder()
		self.builder = builder
		self.pool = pool
		self.base = base

	def __iter__(self):
		yield self.pool
		yield self.input

	@report
	def get(self, project, since, infoonly):
		assert isinstance(self.input, Action)
		(data, self.changed) = getoutputs(project, since, infoonly, (self.pool, self.input))

		if data is not nodata and data is not newdata:
			# We really have to do some work
			from ll.xist import xsc
			(pool, data) = data
			oldpool = self.builder.pool
			try:
				self.builder.pool = xsc.Pool(pool, oldpool)

				project.writestep(self, "Parsing XIST input with base ", self.base)
				data = self.builder.parsestring(data, self.base)
			finally:
				self.builder.pool = oldpool # Restore old pool
		return data

	def __repr__(self):
		return "<%s.%s object with base=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.base, id(self))


class XISTConvertAction(PipeAction):
	"""
	This action transform an XIST node.
	"""

	def __init__(self, mode=None, target=None, stage=None, lang=None, targetroot=None):
		"""
		Create a new :class:`XISTConvertAction` object. The arguments will be
		used to create a :class:`ll.xist.converters.Converter` object for each
		call to :meth:`execute`.
		"""
		PipeAction.__init__(self)
		self.mode = mode
		self.target = target
		self.stage = stage
		self.lang = lang
		self.targetroot = targetroot

	def converter(self, project):
		"""
		Create a new :class:`ll.xist.converters.Converter` object to be used by
		this action. The attributes of this new converter (:attr:`mode`,
		:attr:`target`, :attr:`stage`, etc.) will correspond to those specified
		in the constructor.

		The :attr:`makeaction` attribute of the converter will be set to
		:var:`self` and the :attr:`makeproject` attribute will be set to
		:var:`project`.
		"""
		from ll.xist import converters
		return converters.Converter(root=self.targetroot, mode=self.mode, stage=self.stage, target=self.target, lang=self.lang, makeaction=self, makeproject=project)

	def execute(self, project, data):
		"""
		Convert the XIST node :var:`data` using a converter provided by
		:meth:`converter` and return the converted node.
		"""
		args = []
		for argname in ("mode", "target", "stage", "lang", "targetroot"):
			arg = getattr(self, argname, None)
			if arg is not None:
				args.append("%s=%r" % (argname, arg))
		if args:
			args = " with %s" % ", ".join(args)
		else:
			args = ""
		project.writestep(self, "Converting XIST node", args)
		return data.convert(self.converter(project))

	def __repr__(self):
		args = []
		for argname in ("mode", "target", "stage", "lang", "targetroot"):
			arg = getattr(self, argname, None)
			if arg is not None:
				args.append("%s=%r" % (argname, arg))
		if args:
			args = " with %s" % ", ".join(args)
		else:
			args = ""
		return "<%s.%s object%s at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, "".join(args), id(self))


class XISTPublishAction(PipeAction):
	"""
	This action publishes an XIST node as a byte string.
	"""

	def __init__(self, publisher=None, base=None):
		"""
		Create an :class:`XISTPublishAction` object. :var:`publisher` must be an
		instance of :class:`ll.xist.publishers.Publisher`. If :var:`publisher` is
		:const:`None` a publisher will be created for you. :var:`base` will be
		the base URL used for publishing.
		"""
		PipeAction.__init__(self)
		if publisher is None:
			from ll.xist import publishers
			publisher = publishers.Publisher()
		self.publisher = publisher
		self.base = base

	def execute(self, project, data):
		"""
		Use the publisher specified in the constructor to publish the input XIST
		node :var:`data`. The output data is the generated XML string.
		"""
		project.writestep(self, "Publishing XIST node with base ", self.base)
		return "".join(self.publisher.publish(data, self.base))

	def __repr__(self):
		return "<%s.%s object with base=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.base, id(self))


class XISTTextAction(PipeAction):
	"""
	This action creates a plain text version of an HTML XIST node.
	"""
	def __init__(self, encoding="iso-8859-1", width=72):
		PipeAction.__init__(self)
		self.encoding = encoding
		self.width = width

	def execute(self, project, data):
		project.writestep(self, "Converting XIST node to text with encoding=%r, width=%r" % (self.encoding, self.width))
		from ll.xist.ns import html
		return html.astext(data, encoding=self.encoding, width=self.width)


class FOPAction(PipeAction):
	"""
	This action transforms an XML string (containing XSL-FO) into PDF. For it
	to work `Apache FOP`__ is required. The command line is hardcoded but it's
	simple to overwrite the class attribute :attr:`command` in a subclass.

	__ http://xmlgraphics.apache.org/fop/
	"""
	command = "/usr/local/src/fop-0.20.5/fop.sh -q -c /usr/local/src/fop-0.20.5/conf/userconfig.xml -fo %s -pdf %s"

	def execute(self, project, data):
		project.writestep(self, "FOPping input")
		(infd, inname) = tempfile.mkstemp(suffix=".fo")
		(outfd, outname) = tempfile.mkstemp(suffix=".pdf")
		try:
			infile = os.fdopen(infd, "wb")
			os.fdopen(outfd).close()
			infile.write(data)
			infile.close()
			os.system(self.command % (inname, outname))
			data = open(outname, "rb").read()
		finally:
			os.remove(inname)
			os.remove(outname)
		return data


class DecodeAction(PipeAction):
	"""
	This action decodes an input :class:`str` object into an output
	:class:`unicode` object.
	"""

	def __init__(self, encoding=None):
		"""
		Create a :class:`DecodeAction` object with :var:`encoding` as the name of
		the encoding. If :var:`encoding` is :const:`None` the system default
		encoding will be used.
		"""
		PipeAction.__init__(self)
		if encoding is None:
			encoding = sys.getdefaultencoding()
		self.encoding = encoding

	def execute(self, project, data):
		project.writestep(self, "Decoding input with encoding ", self.encoding)
		return data.decode(self.encoding)

	def __repr__(self):
		return "<%s.%s object encoding=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.encoding, id(self))


class EncodeAction(PipeAction):
	"""
	This action encodes an input :class:`unicode` object into an output
	:class:`str` object.
	"""

	def __init__(self, encoding=None):
		"""
		Create an :class:`EncodeAction` object with :var:`encoding` as the name
		of the encoding. If :var:`encoding` is :const:`None` the system default
		encoding will be used.
		"""
		PipeAction.__init__(self)
		if encoding is None:
			encoding = sys.getdefaultencoding()
		self.encoding = encoding

	def execute(self, project, data):
		project.writestep(self, "Encoding input with encoding ", self.encoding)
		return data.encode(self.encoding)

	def __repr__(self):
		return "<%s.%s object encoding=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.encoding, id(self))


class TOXICAction(PipeAction):
	"""
	This action transforms an XML string into an Oracle procedure body via the
	:mod:`ll.xist.ns.toxic` namespace module.
	"""

	def execute(self, project, data):
		project.writestep(self, "Toxifying input")
		from ll import toxic
		return toxic.xml2ora(data)


class TOXICPrettifyAction(PipeAction):
	"""
	This action tries to fix the indentation of a PL/SQL snippet via the
	:func:`ll.xist.ns.toxic.prettify` function.
	"""

	def execute(self, project, data):
		project.writestep(self, "Prettifying input")
		from ll import toxic
		return toxic.prettify(data)


class SplatAction(PipeAction):
	"""
	This action transforms an input string by replacing regular expressions.
	"""

	def __init__(self, patterns):
		"""
		Create a new :class:`SplatAction` object. :var:`patterns` are pattern
		pairs. Each first entry will be replaced by the corresponding second
		entry.
		"""
		PipeAction.__init__(self)
		self.patterns = patterns

	def execute(self, project, data):
		for (search, replace) in self.patterns:
			project.writestep(self, "Replacing ", search, " with ", replace)
			data = re.sub(search, replace, data)
		return data


class XPITAction(PipeAction):
	"""
	This action transform an input string via :mod:`ll.xpit`.
	"""

	def __init__(self, nsinput=None):
		PipeAction.__init__(self)
		self.nsinput = nsinput

	def addnsinput(self, input):
		"""
		Register :var:`input` as the namespace action. This action must return
		a namespace to be used in evaluating the input string from the normal
		input action.
		"""
		self.nsinput = input
		return self

	def __iter__(self):
		yield self.nsinput
		yield self.input

	def execute(self, project, data, ns):
		from ll import xpit
		globals = dict(makeaction=self, makeproject=project)
		project.writestep(self, "Converting XPIT input")
		return xpit.convert(data, globals, ns)

	@report
	def get(self, project, since, infoonly):
		assert isinstance(self.nsinput, Action)
		assert isinstance(self.input, Action)
		(data, self.changed) = getoutputs(project, since, infoonly, (self.nsinput, self.input))
		if data is not nodata and data is not newdata:
			data = self.execute(project, data[1], data[0])
		return data


class CommandAction(ExternalAction):
	"""
	This action executes a system command (via :func:`os.system`) and passes
	through the input data.
	"""

	def __init__(self, command):
		"""
		Create a new :class:`CommandAction` object. :var:`command` is the command
		that will executed when :meth:`execute` is called.
		"""
		ExternalAction.__init__(self)
		self.command = command

	def execute(self, project):
		project.writestep(self, "Executing command ", self.command)
		os.system(self.command)

	def __repr__(self):
		return "<%s.%s object command=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.command, id(self))


class ModeAction(ExternalAction):
	"""
	:class:`ModeAction` changes file permissions and passes through the input data.
	"""

	def __init__(self, mode=0644):
		"""
		Create an :class:`ModeAction` object. :var:`mode` (which defaults to
		:const:`0644`) will be use as the permission bit pattern.
		"""
		PipeAction.__init__(self)
		self.mode = mode

	def execute(self, project):
		"""
		Change the permission bits of the file ``self.getkey()``.
		"""
		key = self.getkey()
		project.writestep(self, "Changing mode of ", project.strkey(key), " to 0%03o" % self.mode)
		key.chmod(self.mode)

	def __repr__(self):
		return "<%s.%s object mode=0%03o at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.mode, id(self))


class OwnerAction(ExternalAction):
	"""
	:class:`OwnerAction` changes the user and/or group ownership of a file and
	passes through the input data.
	"""

	def __init__(self, user=None, group=None):
		"""
		Create a new :class:`OwnerAction` object. :var:`user` can either be a
		numerical user id or a user name or :const:`None`. If it is :const:`None`
		no user ownership will be changed. The same applies to :var:`group`.
		"""
		PipeAction.__init__(self)
		self.id = id
		self.user = user
		self.group = group

	def execute(self, project):
		"""
		Change the ownership of the file ``self.getkey()``.
		"""
		key = self.getkey()
		project.writestep(self, "Changing owner of ", project.strkey(key), " to ", self.user, " and group to ", self.user)
		key.chown(self.user, self.group)

	def __repr__(self):
		return "<%s.%s object user=%r group=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.user, self.group, id(self))


class ModuleAction(PipeAction):
	"""
	This action will turn the input string into a Python module.
	"""
	def __init__(self):
		"""
		Create an :class:`ModuleAction`.

		This object must have an input action (which might be a :class:`FileAction`
		that creates the source file).
		"""
		PipeAction.__init__(self)
		self.inputs = []
		self.changed = bigbang
		self.data = nodata
		self.buildno = None

	def addinputs(self, *inputs):
		"""
		Register all actions in :var:`inputs` as modules used by this module.
		These actions must be :class:`ModuleAction` objects too.

		Normally it isn't neccessary to call the method explicitely. Instead
		fetch the required module inside your module like this::

			from ll import make

			mymodule = make.currentproject.get("mymodule.py")

		This will record your module as depending on :mod:`mymodule`, so if
		:mod:`mymodule` changes your module will be reloaded too. For this to
		work you need to have an :class:`ModuleAction` added to the project with
		the key ``"mymodule.py"``.
		"""
		self.inputs.extend(inputs)
		return self

	def __iter__(self):
		yield self.input
		for input in self.inputs:
			yield input

	def execute(self, project, data):
		key = self.getkey()
		project.writestep(self, "Importing module as ", project.strkey(key))

		if key is None:
			filename = name = "<string>"
		elif isinstance(key, url.URL):
			try:
				filename = key.local()
			except ValueError: # is not local
				filename = str(key)
			name = key.withoutext().file.encode("ascii", "ignore")
		else:
			filename = name = str(key)

		del self.inputs[:] # The module will be reloaded => drop all dependencies (they will be rebuilt during import)

		# Normalize line feeds, so that :func:`compile` works (normally done by import)
		data = data.replace("\r\n", "\n")

		mod = types.ModuleType(name)
		mod.__file__ = filename

		try:
			project.importstack.append(self)
			code = compile(data, filename, "exec")
			exec code in mod.__dict__
		finally:
			project.importstack.pop(-1)
		return mod

	@report
	def get(self, project, since, infoonly):
		assert isinstance(self.input, Action)
		# Is this module required by another?
		if project.importstack:
			if self not in project.importstack[-1].inputs:
				project.importstack[-1].addinputs(self) # Append to inputs of other module

		# Is this a new build round?
		if self.buildno != project.buildno:
			(data, changed) = getoutputs(project, self.changed, False, self.input) # Get the source code
			if data is not nodata or self.data is nodata: # The file itself has changed or this is the first call
				needimport = True
			else: # Only check the required inputs, if ``self.input`` has *not* changed
				(data2, changed2) = getoutputs(project, self.changed, False, self.inputs)
				needimport = data2 is not nodata

			if needimport:
				if data is nodata:
					(data, changed) = getoutputs(project, bigbang, infoonly, self.input) # We *really* need the source
				self.data = self.execute(project, data) # This will (re)create dependencies
				gc.collect() # Make sure classes from the previous module (which have cycles via the :attr:`__mro__`) are gone
				# Timestamp of import is the timestamp of the newest module file
				self.changed = changed
				if self.inputs:
					changed = max(changed, max(input.changed for input in self.inputs))
				self.changed = changed
			self.buildno = project.buildno
			if self.changed > since:
				if infoonly:
					return newdata
				return self.data
		# Are we newer then the specified date?
		elif self.changed > since:
			key = self.getkey()
			project.writenote(self, "Reusing cached module ", project.strkey(key))
			if infoonly:
				return newdata
			return self.data
		return nodata

	def __repr__(self):
		return "<%s.%s object key=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.getkey(), id(self))


class ModuleName(str):
	"""
	:class:`ModuleName` objects are automatically created by
	:class:`ImportAction` as keys to be able to distinguish those keys from the
	keys for PhonyActions (which are normally :class:`str` objects).
	"""
	def __eq__(self, other):
		return self.__class__ is other.__class__ and str.__eq__(self, other)

	def __ne__(self, other):
		return not self == other

	def __repr__(self):
		return "%s.%s(%s)" % (self.__class__.__module__, self.__class__.__name__, str.__repr__(self))


class ImportAction(Action):
	"""
	This action imports a module specified by module name. It has no inputs.
	"""
	def __init__(self, key):
		"""
		Create a :class:`ImportAction` object. :var:`key` must be the module name
		as a :class:`str`.
		"""
		Action.__init__(self)
		self.key = ModuleName(key)
		self.changed = bigbang
		self.module = None

	def __iter__(self):
		if False:
			yield None

	@report
	def get(self, project, since, infoonly):
		if self.module is None:
			module = __import__(self.key)
			for subname in self.key.split(".")[1:]:
				module = getattr(module, subname)
			self.changed = filechanged(url.File(module.__file__))
			self.module = module
			args = ["Imported module %s" % self.key]
			if project.showtimestamps:
				args.append(" (changed ")
				args.append(project.strdatetime(self.changed))
				args.append(")")
			project.writestep(self, *args)
		if self.changed > since:
			if infoonly:
				return newdata
			return self.module
		return nodata

	def __repr__(self):
		return "<%s.%s object key=%r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.key, id(self))


class AlwaysAction(Action):
	"""
	This action always returns :const:`None` as new data.
	"""
	def __init__(self):
		Action.__init__(self)
		self.changed = bigcrunch

	def __iter__(self):
		if False:
			yield None

	@report
	def get(self, project, since, infoonly):
		if infoonly:
			return newdata
		project.writestep(self, "Returning None")
		return None
alwaysaction = AlwaysAction() # this action can be reused as it has no inputs


class NeverAction(Action):
	"""
	This action never returns new data.
	"""
	def __iter__(self):
		if False:
			yield None

	@report
	def get(self, project, since, infoonly):
		return nodata
neveraction = NeverAction() # this action can be reused as it has no inputs


###
### Classes for target keys (apart from strings for :const:`PhonyAction` objects and URLs for :class:`FileAction` objects)
###

class DBKey(object):
	"""
	This class provides a unique identifier for database content. This can be
	used as an key for :class:`FileAction` objects and other actions that are
	not files, but database records, function, procedures etc.
	"""
	name = None

	def __init__(self, connection, type, name, key=None):
		"""
		Create a new :class:`DBKey` instance. Arguments are:

		:var:`connection` : string
			A string that specifies the connection to the database. E.g.
			``"user/pwd@db.example.com"`` for Oracle.

		:var:`type` : string
			The type of the object. Values may be ``"table"``, ``"view"``,
			``"function"``, ``"procedure"`` etc.

		:var:`name` : string
			The name of the object

		:var:`key` : any object
			If :var:`name` refers to a table, :var:`key` can be used to specify
			a row in this table.
		"""
		self.connection = connection
		self.type = type.lower()
		self.name = name.lower()
		self.key = key

	def __eq__(self, other):
		res = self.__class__ == other.__class__
		if not res:
			res = self.connection==other.connection and self.type==other.type and self.name==other.name and self.key==other.key
		return res

	def __hash__(self):
		return hash(self.connection) ^ hash(self.type) ^ hash(self.name) ^ hash(self.key)

	def __repr__(self):
		args = []
		for attrname in ("connection", "type", "name", "key"):
			attrvalue = getattr(self, attrname)
			if attrvalue is not None:
				args.append("%s=%r" % (attrname, attrvalue))
		return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

	def __str__(self):
		s = "%s:%s|%s:%s" % (self.__class__.name, self.connection, self.type, self.name)
		if self.key is not None:
			s += "|%s" % (self.key,)
		return s


class OracleConnection(url.Connection):
	def __init__(self, context, connection):
		self.context = context
		import cx_Oracle
		self.cursor = cx_Oracle.connect(connection).cursor()

	def open(self, url, mode="rb"):
		return OracleResource(self, url, mode)

	def mimetype(self, url):
		return "text/x-oracle-%s" % url.type

	def cdate(self, url):
		# FIXME: This isn't the correct time zone, but Oracle doesn't provide anything better
		self.cursor.execute("select created, to_number(to_char(systimestamp, 'TZH')), to_number(to_char(systimestamp, 'TZM')) from user_objects where lower(object_type)=:type and lower(object_name)=:name", type=url.type, name=url.name)
		row = self.cursor.fetchone()
		if row is None:
			raise IOError(errno.ENOENT, "no such %s: %s" % (url.type, url.name))
		return row[0]-datetime.timedelta(seconds=60*(row[1]*60+row[2]))

	def mdate(self, url):
		# FIXME: This isn't the correct time zone, but Oracle doesn't provide anything better
		self.cursor.execute("select last_ddl_time, to_number(to_char(systimestamp, 'TZH')), to_number(to_char(systimestamp, 'TZM')) from user_objects where lower(object_type)=:type and lower(object_name)=:name", type=url.type, name=url.name)
		row = self.cursor.fetchone()
		if row is None:
			raise IOError(errno.ENOENT, "no such %s: %s" % (url.type, url.name))
		return row[0]-datetime.timedelta(seconds=60*(row[1]*60+row[2]))

	def __repr__(self):
		return "<%s.%s to %r at 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.cursor.connection.connectstring(), id(self))


class OracleKey(DBKey):
	name = "oracle"

	def connect(self, context=None):
		context = url.getcontext(context)
		if context is url.defaultcontext:
			raise ValueError("oracle URLs need a custom context")

		# Use one OracleConnection for each connectstring
		try:
			connections = context.schemes["oracle"]
		except KeyError:
			connections = context.schemes["oracle"] = {}
		try:
			connection = connections[self.connection]
		except KeyError:
			connection = connections[self.connection] = OracleConnection(context, self.connection)
		return connection

	def __getattr__(self, name):
		def realattr(*args, **kwargs):
			try:
				context = kwargs["context"]
			except KeyError:
				context = None
			else:
				kwargs = kwargs.copy()
				del kwargs["context"]
			connection = self.connect(context=context)
			return getattr(connection, name)(self, *args, **kwargs)
		return realattr

	def mimetype(self):
		return "text/x-oracle-%s" % self.type

	def open(self, mode="rb", context=None, *args, **kwargs):
		connection = self.connect(context=context)
		return connection.open(self, mode, *args, **kwargs)


class OracleResource(url.Resource):
	"""
	An :class:`OracleResource` wraps a function or procedure in an Oracle
	database in a file-like API.
	"""
	def __init__(self, connection, url, mode="rb"):
		self.connection = connection
		self.url = url
		self.mode = mode
		self.closed = False
		self.name = str(self.url)

		if self.url.type not in ("function", "procedure"):
			raise ValueError("don't know how to handle %r" % self.url)
		if "w" in self.mode:
			self.stream = cStringIO.StringIO()
			self.stream.write("create or replace %s %s\n" % (self.url.type, self.url.name))
		else:
			cursor = self.connection.cursor
			cursor.execute("select text from user_source where lower(name)=lower(:name) and type='%s' order by line" % self.url.type.upper(), name=self.url.name)
			code = "\n".join((row[0] or "").rstrip() for row in cursor)
			if not code:
				raise IOError(errno.ENOENT, "no such %s: %s" % (self.url.type, self.url.name))
			# drop type
			code = code.split(None, 1)[1]
			# skip name
			for (i, c) in enumerate(code):
				if not c.isalpha() and c != "_":
					break
			code = code[i:]
			self.stream = cStringIO.StringIO(code)

	def __getattr__(self, name):
		if self.closed:
			raise ValueError("I/O operation on closed file")
		return getattr(self.stream, name)

	def mimetype(self):
		return "text/x-oracle-%s" % self.url.type

	def cdate(self):
		return self.connection.cdate(self.url)

	def mdate(self):
		return self.connection.mdate(self.url)

	def close(self):
		if not self.closed:
			if "w" in self.mode:
				c = self._cursor()
				c.execute(self.stream.getvalue())
			self.stream = None
			self.closed = True


###
### Colors for output
###

s4indent = astyle.Style.fromenv("LL_MAKE_REPRANSI_INDENT", "black:black:bold")
s4key = astyle.Style.fromenv("LL_MAKE_REPRANSI_KEY", "green:black")
s4action = astyle.Style.fromenv("LL_MAKE_REPRANSI_ACTION", "yellow:black")
s4time = astyle.Style.fromenv("LL_MAKE_REPRANSI_TIME", "magenta:black")
s4data = astyle.Style.fromenv("LL_MAKE_REPRANSI_DATA", "cyan:black")
s4size = astyle.Style.fromenv("LL_MAKE_REPRANSI_SIZE", "magenta:black")
s4counter = astyle.Style.fromenv("LL_MAKE_REPRANSI_COUNTER", "red:black:bold")
s4error = astyle.Style.fromenv("LL_MAKE_REPRANSI_ERROR", "red:black:bold")


###
### The project class
###

class Project(dict):
	"""
	A :class:`Project` collects all :class:`Action` objects from a project. It
	is responsible for initiating the build process and for generating a report
	about the progress of the build process.
	"""
	def __init__(self):
		super(Project, self).__init__()
		self.actionscalled = 0
		self.actionsfailed = 0
		self.stepsexecuted = 0
		self.fileswritten = 0
		self.starttime = None
		self.ignoreerrors = False
		self.here = None # cache the current directory during builds (used for shortening URLs)
		self.home = None # cache the home directory during builds (used for shortening URLs)
		self.stack = [] # keep track of the recursion during calls to :meth:`Action.get`
		self.importstack = [] # keep track of recursive imports
		self.indent = os.environ.get("LL_MAKE_INDENT", "   ") # Indentation string to use for output of nested actions
		self.buildno = 0 # Build number; This gets incremented on each call to :meth:`build`. Can be used by actions to determine the start of a new build round

		self.showsummary = self._getenvbool("LL_MAKE_SHOWSUMMARY", True)
		self.showaction = os.environ.get("LL_MAKE_SHOWACTION", "filephony")
		self.showstep = os.environ.get("LL_MAKE_SHOWSTEP", "all")
		self.shownote = os.environ.get("LL_MAKE_SHOWNOTE", "none")
		self.showidle = self._getenvbool("LL_MAKE_SHOWIDLE", False)
		self.showregistration = os.environ.get("LL_MAKE_SHOWREGISTRATION", "phony")
		self.showtime = self._getenvbool("LL_MAKE_SHOWTIME", True)
		self.showtimestamps = self._getenvbool("LL_MAKE_SHOWTIMESTAMPS", False)
		self.showdata = self._getenvbool("LL_MAKE_SHOWDATA", False)

	def __repr__(self):
		return "<%s.%s with %d targets at 0x%x>" % (self.__module__, self.__class__.__name__, len(self), id(self))

	class showaction(misc.propclass):
		"""
		This property specifies which actions should be reported during the build
		process. On setting, the value can be:

		:const:`None` or ``"none"``
			No actions will be reported;

		``"file"``
			Only :class:`FileAction`\s will be reported;

		``"phony"``
			Only :class:`PhonyAction`\s will be reported;

		``"filephony"``
			Only :class:`FileAction`\s and :class:`PhonyAction`\s will be
			reported;

		a class or tuple of classes
			Only actions that are instances of those classes will be reported.
		"""
		def __get__(self):
			return self._showaction
		def __set__(self, value):
			if value == "none":
				self._showaction = None
			elif value == "file":
				self._showaction = FileAction
			elif value == "phony":
				self._showaction = PhonyAction
			elif value == "filephony":
				self._showaction = (PhonyAction, FileAction)
			elif value == "all":
				self._showaction = Action
			else:
				self._showaction = value

	class showstep(misc.propclass):
		"""
		This property specifies which for which actions tranformation steps
		should be reported during the build process. For allowed values on
		setting see :prop:`showaction`.
		"""
		def __get__(self):
			return self._showstep
		def __set__(self, value):
			if value == "none":
				self._showstep = None
			elif value == "file":
				self._showstep = FileAction
			elif value == "phony":
				self._showstep = PhonyAction
			elif value == "filephony":
				self._showstep = (PhonyAction, FileAction)
			elif value == "all":
				self._showstep = Action
			else:
				self._showstep = value

	class shownote(misc.propclass):
		"""
		This property specifies which for which actions tranformation notes
		(which are similar to step, but not that important, e.g. when an
		information that is already there gets reused) be reported during the
		build process. For allowed values on setting see :prop:`showaction`.
		"""
		def __get__(self):
			return self._shownote
		def __set__(self, value):
			if value == "none":
				self._shownote = None
			elif value == "file":
				self._shownote = FileAction
			elif value == "phony":
				self._shownote = PhonyAction
			elif value == "filephony":
				self._shownote = (PhonyAction, FileAction)
			elif value == "all":
				self._shownote = Action
			else:
				self._shownote = value

	class showregistration(misc.propclass):
		"""
		This property specifies for which actions registration (i.e. call to the
		:meth:`add` should be reported. For allowed values on setting see
		:prop:`showaction`.
		"""
		def __get__(self):
			return self._showregistration
		def __set__(self, value):
			if value == "none":
				self._showregistration = None
			elif value == "file":
				self._showregistration = FileAction
			elif value == "phony":
				self._showregistration = PhonyAction
			elif value == "filephony":
				self._showregistration = (PhonyAction, FileAction)
			elif value == "all":
				self._showregistration = Action
			else:
				self._showregistration = value

	def _getenvbool(self, name, default):
		return bool(int(os.environ.get(name, default)))

	def strtimedelta(self, delta):
		"""
		Return a nicely formatted and colored string for the
		:class:`datetime.timedelta` value :var:`delta`. :var:`delta`
		may also be :const:`None` in with case ``"0"`` will be returned.
		"""
		if delta is None:
			text = "0"
		else:
			rest = delta.seconds
	
			(rest, secs) = divmod(rest, 60)
			(rest, mins) = divmod(rest, 60)
			rest += delta.days*24
	
			secs += delta.microseconds/1000000.
			if rest:
				text = "%d:%02d:%06.3fh" % (rest, mins, secs)
			elif mins:
				text = "%02d:%06.3fm" % (mins, secs)
			else:
				text = "%.3fs" % secs
		return s4time(text)

	def strdatetime(self, dt):
		"""
		Return a nicely formatted and colored string for the
		:class:`datetime.datetime` value :var:`dt`.
		"""
		return s4time(dt.strftime("%Y-%m-%d %H:%M:%S"), ".%06d" % (dt.microsecond))

	def strcounter(self, counter):
		"""
		Return a nicely formatted and colored string for the counter value
		:var:`counter`.
		"""
		return s4counter("%d." % counter)

	def strerror(self, text):
		"""
		Return a nicely formatted and colored string for the error text
		:var:`text`.
		"""
		return s4error(text)

	def strkey(self, key):
		"""
		Return a nicely formatted and colored string for the action key
		:var:`key`.
		"""
		s = str(key)
		if isinstance(key, url.URL) and key.islocal():
			if self.here is None:
				self.here = url.here()
			if self.home is None:
				self.home = url.home()
			test = str(key.relative(self.here))
			if len(test) < len(s):
				s = test
			test = "~/%s" % key.relative(self.home)
			if len(test) < len(s):
				s = test
		return s4key(s)

	def straction(self, action):
		"""
		Return a nicely formatted and colored string for the action
		:var:`action`.
		"""
		name = action.__class__.__name__
		if name.endswith("Action"):
			name = name[:-6]

		if hasattr(action, "key"):
			return s4action(name, "(", self.strkey(action.key), ")")
		else:
			return s4action(name)

	def __setitem__(self, key, target):
		"""
		Add the action :var:`target` to :var:`self` as a target and register it
		under the key :var:`key`.
		"""
		if key in self:
			self.warn(RedefinedTargetWarning(key), 5)
		if isinstance(key, url.URL) and key.islocal():
			key = key.abs(scheme="file")
		target.key = key
		super(Project, self).__setitem__(key, target)

	def add(self, target, key=None):
		"""
		Add the action :var:`target` as a target to :var:`self`. If :var:`key`
		is not :const:`None`, :var:`target` will be registered under this key
		(and ``target.key`` will be set to it), otherwise it will be registered
		under its own key (i.e. ``target.key``).
		"""
		if key is None: # Use the key from the target
			key = target.getkey()

		self[key] = target

		self.stepsexecuted += 1
		if self.showregistration is not None and isinstance(target, self.showregistration):
			self.writestacklevel(0, self.strcounter(self.stepsexecuted), " Registered ", self.strkey(target.key))

		return target

	def _candidates(self, key):
		"""
		Return candidates for alternative forms of :var:`key`. This is a
		generator, so when the first suitable candidate is found, the rest of the
		candidates won't have to be created at all.
		"""
		yield key
		key2 = key
		if isinstance(key, basestring):
			yield ModuleName(key)
			key2 = url.URL(key)
			yield key2
		if isinstance(key2, url.URL):
			key2 = key2.abs(scheme="file")
			yield key2
			key2 = key2.real(scheme="file")
			yield key2
		if isinstance(key, basestring) and ":" in key:
			(prefix, rest) = key.split(":", 1)
			if prefix == "oracle":
				if "|" in rest:
					(connection, rest) = rest.split("|", 1)
					if ":" in rest:
						(type, name) = rest.split(":", 1)
						if "|" in rest:
							(name, key) = rest.split("|")
						else:
							key = None
						yield OracleKey(connection, type, name, key)

	def __getitem__(self, key):
		"""
		Return the target with the key :var:`key`. If an key can't be found, it
		will be wrapped in a :class:`ll.url.URL` object and retried. If
		:var:`key` still can't be found a :exc:`UndefinedTargetError` will be
		raised.
		"""
		sup = super(Project, self)
		for key2 in self._candidates(key):
			try:
				return sup.__getitem__(key2)
			except KeyError:
				pass
		raise UndefinedTargetError(key)

	def has_key(self, key):
		"""
		Return whether the target with the key :var:`key` exists in the project.
		"""
		return key in self

	def __contains__(self, key):
		"""
		Return whether the target with the key :var:`key` exists in the project.
		"""
		sup = super(Project, self)
		for key2 in self._candidates(key):
			has = sup.has_key(key2)
			if has:
				return True
		return False

	def create(self):
		"""
		Create all dependencies for the project. Overwrite in subclasses.

		This method should only be called once, otherwise you'll get lots of
		:exc:`RedefinedTargetWarning`\s. But you can call :meth:`clear`
		to remove all targets before calling :meth:`create`. You can also
		use the method :meth:`recreate` for that.
		"""
		self.stepsexecuted = 0
		self.starttime = datetime.datetime.utcnow()
		self.writeln("Creating targets...")

	def recreate(self):
		"""
		Calls :meth:`clear` and :meth:`create` to recreate all project
		dependencies.
		"""
		self.clear()
		self.create()

	def optionparser(self):
		"""
		Return an :mod:`optparse` parser for parsing the command line options.
		This can be overwritten in subclasses to add more options.
		"""
		p = optparse.OptionParser(usage="usage: %prog [options] [targets]")
		p.add_option("-x", "--ignore", dest="ignoreerrors", help="Ignore errors", action="store_true", default=None)
		p.add_option("-X", "--noignore", dest="ignoreerrors", help="Don't ignore errors", action="store_false", default=None)
		p.add_option("-c", "--color", dest="color", help="Use colored output", action="store_true", default=None)
		p.add_option("-C", "--nocolor", dest="color", help="No colored output", action="store_false", default=None)
		p.add_option("-a", "--showaction", dest="showaction", help="Show actions?", choices=["all", "file", "filephony", "none"], default="filephony")
		p.add_option("-s", "--showstep", dest="showstep", help="Show steps?", choices=["all", "file", "filephony", "none"], default="all")
		p.add_option("-n", "--shownote", dest="shownote", help="Show steps?", choices=["all", "file", "filephony", "none"], default="none")
		p.add_option("-i", "--showidle", dest="showidle", help="Show actions that didn't produce data?", action="store_true", default=False)
		p.add_option("-d", "--showdata", dest="showdata", help="Show data?", action="store_true", default=False)
		return p

	def parseoptions(self, commandline=None):
		"""
		Use the parser returned by :meth:`optionparser` to parse the option
		sequence :var:`commandline`, modify :var:`self` accordingly and return
		the result of the parsers :meth:`parse_args` call.
		"""
		p = self.optionparser()
		(options, args) = p.parse_args(commandline)
		if options.ignoreerrors is not None:
			self.ignoreerrors = options.ignoreerrors
		if options.color is not None:
			self.color = options.color
		if options.showaction is not None:
			self.showaction = options.showaction
		if options.showstep is not None:
			self.showstep = options.showstep
		if options.shownote is not None:
			self.shownote = options.shownote
		self.showidle = options.showidle
		self.showdata = options.showdata
		return (options, args)

	def _get(self, target, since, infoonly):
		"""
		:var:`target` must be an action registered in :var:`self` (or the id of
		one). For this target the :meth:`Action.get` will be called with
		:var:`since` and :var:`infoonly` as the arguments.
		"""
		global currentproject

		if not isinstance(target, Action):
			target = self[target]

		oldproject = currentproject
		try:
			currentproject = self
			data = target.get(self, since, infoonly)
		finally:
			currentproject = oldproject
		return data

	def get(self, target):
		"""
		Get up-to-date output data from the target :var:`target` (which must be
		an action registered with :var:`self` (or the id of one). During the call
		the global variable ``currentproject`` will be set to :var:`self`.
		"""
		return self._get(target, bigbang, False)

	def build(self, *targets):
		"""
		Rebuild all targets in :var:`targets`. Items in :var:`targets` must be
		actions registered with :var:`self` (or their ids).
		"""
		global currentproject

		self.starttime = datetime.datetime.utcnow()

		with url.Context():
			self.stack = []
			self.importstack = []
			self.actionscalled = 0
			self.actionsfailed = 0
			self.stepsexecuted = 0
			self.fileswritten = 0
	
			self.buildno += 1 # increment build number so that actions that stored the old one can detect a new build round
	
			for target in targets:
				data = self._get(target, bigcrunch, True)
			now = datetime.datetime.utcnow()
	
			if self.showsummary:
				args = []
				self.write(
					"built ",
					s4action(self.__class__.__module__, ".", self.__class__.__name__),
					": ",
					s4data(str(len(self))),
					" registered targets; ",
					s4data(str(self.actionscalled)),
					" actions called; ",
					s4data(str(self.stepsexecuted)),
					" steps executed; ",
					s4data(str(self.fileswritten)),
					" files written; ",
					s4data(str(self.actionsfailed)),
					" actions failed",
				)
				if self.showtime:
					self.write(" [t+", self.strtimedelta(now-self.starttime), "]")
				self.writeln()

	def buildwithargs(self, commandline=None):
		"""
		For calling make scripts from the command line. :var:`commandline`
		defaults to ``sys.argv[1:]``. Any positional arguments in the command
		line will be treated as target ids. If there are no positional arguments,
		a list of all registered :class:`PhonyAction` objects will be output.
		"""
		if not commandline:
			commandline = sys.argv[1:]
		(options, args) = self.parseoptions(commandline)

		if args:
			self.build(*args)
		else:
			self.writeln("Available phony targets are:")
			self.writephonytargets()

	def write(self, *texts):
		"""
		All screen output is done through this method. This makes it possible
		to redirect the output (e.g. to logfiles) in subclasses.
		"""
		astyle.stderr.write(*texts)

	def writeln(self, *texts):
		"""
		All screen output is done through this method. This makes it possible to
		redirect the output (e.g. to logfiles) in subclasses.
		"""
		astyle.stderr.writeln(*texts)
		astyle.stderr.flush()

	def writeerror(self, *texts):
		"""
		Output an error.
		"""
		self.write(*texts)

	def warn(self, warning, stacklevel):
		"""
		Issue a warning through the Python warnings framework
		"""
		warnings.warn(warning, stacklevel=stacklevel)

	def writestacklevel(self, level, *texts):
		"""
		Output :var:`texts` indented :var:`level` levels.
		"""
		self.write(s4indent(level*self.indent), *texts)
		if self.showtime and self.starttime is not None:
			self.write(" [t+", self.strtimedelta(datetime.datetime.utcnow() - self.starttime), "]")
		self.writeln()

	def writestack(self, *texts):
		"""
		Output :var:`texts` indented properly for the current nesting of
		action execution.
		"""
		count = misc.count(level for level in self.stack if level.reportable)
		self.writestacklevel(count, *texts)

	def _writependinglevels(self):
		for (i, level) in enumerate(level for level in self.stack if level.reportable):
			if not level.reported:
				args = ["Started  ", self.straction(level.action)]
				if self.showtimestamps:
					args.append(" (since ")
					args.append(self.strdatetime(level.since))
					if level.infoonly:
						args.append(" (info only)")
					args.append(")")
				self.writestacklevel(i, *args)
				level.reported = True

	def writestep(self, action, *texts):
		"""
		Output :var:`texts` as the description of the data transformation
		done by the action :var:`arction`.
		"""
		self.stepsexecuted += 1
		if self.showstep is not None and isinstance(action, self.showstep):
			if not self.showidle:
				self._writependinglevels()
			self.writestack(self.strcounter(self.stepsexecuted), " ", *texts)

	def writenote(self, action, *texts):
		"""
		Output :var:`texts` as the note for the data transformation done by
		the action :var:`action`.
		"""
		self.stepsexecuted += 1
		if self.shownote is not None and isinstance(action, self.shownote):
			if not self.showidle:
				self._writependinglevels()
			self.writestack(self.strcounter(self.stepsexecuted), " ", *texts)

	def writecreatedone(self):
		"""
		Can be called at the end of an overwritten :meth:`create` to report
		the number of registered targets.
		"""
		self.writestacklevel(0, "done: ", s4data(str(len(self))), " registered targets")

	def writephonytargets(self):
		"""
		Show a list of all :class:`PhonyAction` objects in the project and
		their documentation.
		"""
		phonies = []
		maxlen = 0
		for key in self:
			if isinstance(key, basestring):
				maxlen = max(maxlen, len(key))
				phonies.append(self[key])
		phonies.sort(key=operator.attrgetter("key"))
		for phony in phonies:
			text = astyle.Text(self.straction(phony))
			if phony.doc:
				text.append(" ", s4indent("."*(maxlen+3-len(phony.key))), " ", phony.doc)
			self.writeln(text)

	def findpaths(self, target, source):
		"""
		Find dependency paths leading from :var:`target` to :var:`source`.
		:var:`target` and :var:`source` may be actions or the ids of registered
		actions. For more info see :meth:`Action.findpaths`.
		"""
		if not isinstance(target, Action):
			target = self[target]
		if not isinstance(source, Action):
			source = self[source]
		return target.findpaths(source)


# This will be set to the project in :meth:`build` and :meth:`get`
currentproject = None