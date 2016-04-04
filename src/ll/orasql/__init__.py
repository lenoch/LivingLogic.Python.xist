# -*- coding: utf-8 -*-
# cython: language_level=3, always_allow_keywords=True

## Copyright 2004-2016 by LivingLogic AG, Bayreuth/Germany
## Copyright 2004-2016 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/xist/__init__.py for the license


"""
:mod:`ll.orasql` contains utilities for working with cx_Oracle__:

*	It allows calling procedures and functions with keyword arguments (via the
	classes :class:`Procedure` and :class:`Function`).

*	Query results will be put into :class:`Record` objects, where database
	fields are accessible as object attributes.

*	The :class:`Connection` class provides methods for iterating through the
	database metadata.

*	Importing this module adds support for URLs with the scheme ``oracle`` to
	:mod:`ll.url`. Examples of these URLs are::

		oracle://user:pwd@db/
		oracle://user:pwd@db/view/
		oracle://user:pwd@db/view/USER_TABLES.sql
		oracle://sys:pwd:sysdba@db/

__ http://cx-oracle.sourceforge.net/
"""


import urllib.request, urllib.parse, urllib.error, datetime, itertools, io, errno, re, fnmatch, unicodedata, collections

from cx_Oracle import *

from ll import misc, url as url_


__docformat__ = "reStructuredText"


bigbang = datetime.datetime(1970, 1, 1, 0, 0, 0) # timestamp for Oracle "directories"


ALL = misc.Const("ALL", "ll.orasql") # marker object for specifying a user


_sql_fixed_tables = "select name from v$fixed_table where type='TABLE'"
_sql_fixed_views = "select name from v$fixed_table where type='VIEW'"


class SQLObjectNotFoundError(IOError):
	def __init__(self, obj):
		IOError.__init__(self, errno.ENOENT, "no such {}: {}".format(obj.type, obj.getfullname()))
		self.obj = obj


class SQLNoSuchObjectError(Exception):
	def __init__(self, name, owner):
		self.name = name
		self.owner = owner

	def __repr__(self):
		return "<{}.{} name={!r} owner={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.name, self.owner, id(self))

	def __str__(self):
		if self.owner is None:
			return "no object named {!r}".format(self.name)
		else:
			return "no object named {!r} for owner {!r}".format(self.name, self.owner)


class UnknownModeError(ValueError):
	def __init__(self, mode):
		self.mode = mode

	def __repr__(self):
		return "<{}.{} mode={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.mode, id(self))

	def __str__(self):
		return "unknown mode {!r}".format(self.mode)


class ConflictError(ValueError):
	def __init__(self, object, message):
		self.object = object
		self.message = message

	def __repr__(self):
		return "<{}.{} object={!r} message={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.object, self.message, id(self))

	def __str__(self):
		return "conflict in {!r}: {}".format(self.object, self.message)


class NotConnectedError(ValueError):
	def __init__(self, object):
		self.object = object

	def __repr__(self):
		return "<{}.{} object={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.object, id(self))

	def __str__(self):
		return "{!r} is not connected to a database".format(self.object)


class Args(dict):
	"""
	An :class:`Args` object is a subclass of :class:`dict` that is used for
	passing arguments to procedures and functions. Both item and attribute access
	(i.e. :meth:`__getitem__` and :meth:`__getattr__`) are available. Names are
	case insensitive.
	"""
	def __init__(self, arg=None, **kwargs):
		dict.__init__(self)
		self.update(arg, **kwargs)

	def update(self, arg=None, **kwargs):
		if arg is not None:
			# if arg is a mapping use iteritems
			dict.update(self, ((key.lower(), value) for (key, value) in getattr(arg, "iteritems", arg)))
		dict.update(self, ((key.lower(), value) for (key, value) in kwargs.items()))

	def __getitem__(self, name):
		return dict.__getitem__(self, name.lower())

	def __setitem__(self, name, value):
		dict.__setitem__(self, name.lower(), value)

	def __delitem__(self, name):
		dict.__delitem__(self, name.lower())

	def __getattr__(self, name):
		try:
			return self.__getitem__(name)
		except KeyError:
			raise AttributeError(name)

	def __setattr__(self, name, value):
		self.__setitem__(name, value)

	def __delattr__(self, name):
		try:
			self.__delitem__(name)
		except KeyError:
			raise AttributeError(name)

	def __repr__(self):
		return "{}.{}({})".format(self.__class__.__module__, self.__class__.__qualname__, ", ".join("{}={!r}".format(*item) for item in self.items()))


class LOBStream:
	"""
	A :class:`LOBStream` object provides streamlike access to a ``BLOB`` or ``CLOB``.
	"""

	def __init__(self, value):
		self.value = value
		self.pos = 0

	def readall(self):
		"""
		Read all remaining data from the stream and return it.
		"""
		result = self.value.read(self.pos+1)
		self.pos = self.value.size()
		return result

	def readchunk(self):
		"""
		Read a chunk of data from the stream and return it. Reading is done in
		optimally sized chunks.
		"""
		size = self.value.getchunksize()
		bytes = self.value.read(self.pos+1, size)
		self.pos += size
		if self.pos >= self.value.size():
			self.pos = self.value.size()
		return bytes

	def read(self, size=None):
		"""
		Read :obj:`size` bytes/characters from the stream and return them.
		If :obj:`size` is :const:`None` all remaining data will be read.
		"""
		if size is None:
			return self.readall()
		if size <= 0:
			return self.readchunk()
		data = self.value.read(self.pos+1, size)
		self.pos += size
		if self.pos >= self.value.size():
			self.pos = self.value.size()
		return data

	def reset(self):
		"""
		Reset the stream so that the next :meth:`read` call starts at the
		beginning of the LOB.
		"""
		self.pos = 0

	def seek(self, offset, whence=0):
		"""
		Seek to the position :obj:`offset` in the LOB. The :obj:`whence` argument
		is optional and defaults to ``0`` (absolute file positioning);
		The other allowed value is ``1`` (seek relative to the current position).
		"""
		if whence == 0:
			self.pos = whence
		elif whence == 1:
			self.pos += whence
		else:
			raise ValueError("unkown whence: {!r}".format(whence))
		size = self.value.size()
		if self.pos >= size:
			self.pos = size
		elif self.pos < 0:
			self.pos = 0


def _decodelob(value, readlobs):
	if value is not None:
		if readlobs is True or (isinstance(readlobs, int) and value.size() <= readlobs):
			value = value.read()
		else:
			value = LOBStream(value)
	return value


class RecordMaker:
	def __init__(self, cursor):
		self._readlobs = cursor.readlobs
		self._index2name = tuple(d[0].lower() for d in cursor.description)
		self._index2conv = tuple(getattr(self, d[1].__name__, self.DEFAULT) for d in cursor.description)

	def __call__(self, *row):
		row = tuple(conv(value) for (conv, value) in zip(self._index2conv, row))
		name2index = dict(zip(self._index2name, itertools.count()))
		return Record(self._index2name, name2index, row)

	def CLOB(self, value):
		return _decodelob(value, self._readlobs)

	def NCLOB(self, value):
		return _decodelob(value, self._readlobs)

	def BLOB(self, value):
		return _decodelob(value, self._readlobs)

	def DEFAULT(self, value):
		return value


class Record(tuple, collections.Mapping):
	"""
	A :class:`Record` is a subclass of :class:`tuple` that is used for storing
	results of database fetches and procedure and function calls. Both item and
	attribute access (i.e. :meth:`__getitem__` and :meth:`__getattr__`) are
	available. Field names are case insensitive.
	"""

	def __new__(cls, index2name, name2index, values):
		record = tuple.__new__(cls, values)
		record._index2name = index2name
		record._name2index = name2index
		return record

	def __getitem__(self, arg):
		if isinstance(arg, str):
			arg = self._name2index[arg.lower()]
		return tuple.__getitem__(self, arg)

	def __getattr__(self, name):
		try:
			index = self._name2index[name.lower()]
		except KeyError:
			raise AttributeError("'{}.{}' object has no attribute {!r}".format(self.__class__.__module__, self.__class__.__qualname__, name))
		return tuple.__getitem__(self, index)

	def get(self, name, default=None):
		"""
		Return the value for the field named :obj:`name`. If this field doesn't
		exist in :obj:`self`, return :obj:`default` instead.
		"""
		try:
			index = self._name2index[name.lower()]
		except KeyError:
			return default
		return tuple.__getitem__(self, index)

	def __contains__(self, name):
		return name.lower() in self._name2index

	def keys(self):
		"""
		Return an iterator over field names.
		"""
		return iter(self._index2name)

	def items(self):
		"""
		Return an iterator over (field name, field value) tuples.
		"""
		return ((key, tuple.__getitem__(self, index)) for (index, key) in enumerate(self._index2name))

	def __repr__(self):
		return "<{}.{} {} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, ", ".join("{}={!r}".format(*item) for item in self.items()), id(self))


class SessionPool(SessionPool):
	"""
	:class:`SessionPool` is a subclass of :class:`cx_Oracle.SessionPool`.
	"""

	def __init__(self, user, password, database, min, max, increment, connectiontype=None, threaded=False, getmode=SPOOL_ATTRVAL_NOWAIT, homogeneous=True):
		if connectiontype is None:
			connectiontype = Connection
		super().__init__(user, password, database, min, max, increment, connectiontype, threaded, getmode, homogeneous)

	def connectstring(self):
		return "{}@{}".format(self.username, self.tnsentry)

	def __repr__(self):
		return "<{}.{} object db={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.connectstring(), id(self))


class Connection(Connection):
	"""
	:class:`Connection` is a subclass of :class:`cx_Oracle.Connection`.
	"""
	def __init__(self, *args, **kwargs):
		"""
		Create a new connection. In addition to the parameters supported by
		:func:`cx_Oracle.connect` the following keyword argument is supported.

		:obj:`readlobs` : bool or integer
			If :obj:`readlobs` is :const:`False` all cursor fetches return
			:class:`LOBStream` objects for LOB object. If :obj:`readlobs` is an
			:class:`int` LOBs with a maximum size of :obj:`readlobs` will be
			returned as :class:`bytes`/:class:`str` objects. If :obj:`readlobs`
			is :const:`True` all LOB values will be returned as
			:class:`bytes`/:class:`str` objects.

		Furthermore the ``clientinfo`` will be automatically set to the name
		of the currently running script (except if the :obj:`clientinfo` keyword
		argument is given and :const:`None`).
		"""
		if "readlobs" in kwargs:
			kwargs = kwargs.copy()
			self.readlobs = kwargs.pop("readlobs", False)
		else:
			self.readlobs = False
		clientinfo = kwargs.pop("clientinfo", misc.sysinfo.short_script_name[-64:])
		super().__init__(*args, **kwargs)
		if clientinfo is not None:
			self.clientinfo = clientinfo
			self.commit()
		self.mode = kwargs.get("mode")
		self._ddprefix = None # Do we have access to the ``DBA_*`` views?
		self._ddprefixargs = None # Do we have access to the ``DBA_ARGUMENTS`` view (which doesn't exist in Oracle 10)?

	def connectstring(self):
		return "{}@{}".format(self.username, self.tnsentry)

	def cursor(self, readlobs=None):
		"""
		Return a new cursor for this connection. For the meaning of
		:obj:`readlobs` see :meth:`__init__`.
		"""
		return Cursor(self, readlobs=readlobs)

	def __repr__(self):
		return "<{}.{} object db={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.connectstring(), id(self))

	def itertables(self, owner=ALL, mode="flat"):
		"""
		Generator that yields all table definitions in the current users schema
		(or all users schemas). :obj:`mode` specifies the order in which tables
		will be yielded:

		``"create"``
			Create order, inserting records into the table in this order will not
			violate foreign key constraints.

		``"drop"``
			Drop order, deleting records from the table in this order will not
			violate foreign key constraints.

		``"flat"``
			Unordered.

		:obj:`owner` specifies from which user tables should be yielded. It can be
		:const:`None` (for the current user), :const:`ALL` (for all users
		(the default)) or a user name.

		Tables that are materialized views will be skipped in all cases.
		"""
		if mode not in ("create", "drop", "flat"):
			raise UnknownModeError(mode)

		cursor = self.cursor()

		tables = Table.iterobjects(self, owner)

		if mode == "flat":
			yield from tables
		else:
			done = set()

			tables = {(table.name, table.owner): table for table in tables}
			def do(table):
				if table not in done:
					done.add(table)
					cursor.execute("select ac1.table_name, decode(ac1.owner, user, null, ac1.owner) as owner from {0}_constraints ac1, {0}_constraints ac2 where ac1.constraint_type = 'R' and ac2.table_name=:name and ac2.owner = nvl(:owner, user) and ac1.r_constraint_name = ac2.constraint_name and ac1.r_owner = ac2.owner".format(cursor.ddprefix()), name=table.name, owner=table.owner)
					for rec in cursor.fetchall():
						try:
							t2 = tables[(rec.table_name, rec.owner)]
						except KeyError:
							pass
						else:
							yield from do(t2)
					yield table
			for table in tables.values():
				yield from do(table)

	def itersequences(self, owner=ALL):
		"""
		Generator that yields sequences. :obj:`owner` can be :const:`None`,
		:const:`ALL` (the default) or a user name.
		"""
		return Sequence.iterobjects(self, owner)

	def iterfks(self, owner=ALL):
		"""
		Generator that yields all foreign key constraints. :obj:`owner` can be
		:const:`None`, :const:`ALL` (the default) or a user name.
		"""
		return ForeignKey.iterobjects(self, owner)

	def iterprivileges(self, owner=ALL):
		"""
		Generator that yields object privileges. :obj:`owner` can be :const:`None`,
		:const:`ALL` (the default) or a user name.
		"""
		return Privilege.iterobjects(self, owner)

	def iterusers(self):
		"""
		Generator that yields all users.
		"""
		return User.iterobjects(self)

	def iterobjects(self, owner=ALL, mode="create"):
		"""
		Generator that yields the sequences, tables, primary keys, foreign keys,
		comments, unique constraints, indexes, views, functions, procedures,
		packages and types in the current users schema (or all users schemas)
		in a specified order.

		:obj:`mode` specifies the order in which objects will be yielded:

		``"create"``
			Create order, i.e. recreating the objects in this order will not lead
			to errors;

		``"drop"``
			Drop order, i.e. dropping the objects in this order will not lead to
			errors;

		``"flat"``
			Unordered.

		:obj:`owner` specifies from which schema objects should be yielded:

			:const:`None`
				All objects belonging to the current user (i.e. via the view
				``USER_OBJECTS``);

			:const:`ALL`
				All objects for all users (via the views ``ALL_OBJECTS`` or
				``DBA_OBJECTS``);

			username : string
				All objects belonging to the specified user
		"""
		if mode not in ("create", "drop", "flat"):
			raise UnknownModeError(mode)

		done = set()

		cursor = self.cursor()

		def do(obj):
			if not obj.generated():
				if mode == "create":
					yield from obj.iterreferencesall(done)
				elif mode == "drop":
					yield from obj.iterreferencedbyall(done)
				else:
					if obj not in done:
						done.add(obj)
						yield obj

		def dosequences():
			for sequence in Sequence.iterobjects(self, owner):
				yield from do(sequence)

		def dotables():
			for table in Table.iterobjects(self, owner):
				if mode == "create" or mode == "flat":
					yield from do(table)

				# Primary key
				pk = table.pk()
				if pk is not None:
					yield from do(pk)

				# Comments
				for comment in table.itercomments():
					# No dependency checks neccessary, but use ``do`` anyway
					yield from do(comment)

				if mode == "drop":
					yield from do(table)

		def dorest():
			for type in (CheckConstraint, UniqueConstraint, ForeignKey, Preference, Index, Synonym, View, MaterializedView, Function, Procedure, Package, PackageBody, Type, TypeBody, Trigger, JavaSource):
				for obj in type.iterobjects(self, owner):
					yield from do(obj)

		funcs = [dosequences, dotables, dorest]
		if mode == "drop":
			funcs = reversed(funcs)

		for func in funcs:
			yield from func()

	def _getobject(self, name, owner=None):
		cursor = self.cursor()
		cursor.execute("select object_name, decode(owner, user, null, owner) as owner, object_type from {0}_objects where object_name = :object_name and owner = nvl(:owner, user)".format(cursor.ddprefix()), object_name=name, owner=owner)
		rec = cursor.fetchone()
		if rec is not None:
			type = rec.object_type.lower()
			try:
				cls = Object.name2type[type]
			except KeyError:
				raise TypeError("type {} not supported".format(type))
			else:
				return cls(rec.object_name, rec.owner, self)
		raise SQLNoSuchObjectError(name, owner)

	def getobject(self, name, owner=None):
		"""
		Return the object named :obj:`name` from the schema. If :obj:`owner` is
		:const:`None` the current schema is queried, else the specified one is
		used. :obj:`name` and :obj:`owner` are treated case insensitively.
		"""
		if isinstance(name, str):
			name = str(name)
		if isinstance(owner, str):
			owner = str(owner)
		cursor = self.cursor()
		if "." in name:
			name = name.split(".")
			query = """
				select
					decode(owner, user, null, owner) as owner,
					object_name || '.' || procedure_name as object_name,
					decode((select count(*) from {prefix}_arguments where owner = nvl(:owner, user) and lower(object_name) = lower(:object_name) and lower(package_name) = lower(:package_name) and argument_name is null), 0, 'procedure', 'function') as object_type
				from
					{prefix}_procedures
				where
					lower(procedure_name) = lower(:object_name) and
					lower(owner) = lower(nvl(:owner, user)) and
					lower(object_name) = lower(:package_name)
			"""
			kwargs = {"object_name": name[1], "package_name": name[0], "owner": owner}
		else:
			query = """
				select
					object_name,
					decode(owner, user, null, owner) as owner,
					object_type
				from
					{prefix}_objects
				where
					lower(object_name) = lower(:object_name) and
					lower(owner) = lower(nvl(:owner, user))
			"""
			kwargs = {"object_name": name, "owner": owner}
		cursor.execute(query.format(prefix=cursor.ddprefix()), **kwargs)

		rec = cursor.fetchone()
		if rec is not None:
			type = rec.object_type.lower()
			try:
				cls = Object.name2type[type]
			except KeyError:
				raise TypeError("type {} not supported".format(type))
			else:
				return cls(rec.object_name, rec.owner, self)
		raise SQLNoSuchObjectError(name, owner)


def connect(*args, **kwargs):
	"""
	Create a connection to the database and return a :class:`Connection` object.
	"""
	return Connection(*args, **kwargs)


class Cursor(Cursor):
	"""
	A subclass of the cursor class in :mod:`cx_Oracle`. The "fetch" methods
	will return records as :class:`Record` objects and  ``LOB`` values will be
	returned as :class:`LOBStream` objects or :class:`str`/:class:`bytes` objects
	(depending on the cursors :attr:`readlobs` attribute).
	"""
	def __init__(self, connection, readlobs=None):
		"""
		Return a new cursor for the connection :obj:`connection`. For the meaning
		of :obj:`readlobs` see :meth:`Connection.__init__`.
		"""
		super().__init__(connection)
		self.readlobs = (readlobs if readlobs is not None else connection.readlobs)

	def ddprefix(self):
		"""
		Return whether the user has access to the ``DBA_*`` views (``"dba"``) or
		not (``"all"``).
		"""
		if self.connection._ddprefix is None:
			try:
				self.execute("select /*+FIRST_ROWS(1)*/ table_name from dba_tables")
			except DatabaseError as exc:
				if exc.args[0].code == 942: # ORA-00942: table or view does not exist
					self.connection._ddprefix = "all"
				else:
					raise
			else:
				self.connection._ddprefix = "dba"
		return self.connection._ddprefix

	def ddprefixargs(self):
		"""
		Return whether the user has access to the ``DBA_ARGUMENTS`` view
		(``"dba"``) or not (``"all"``).
		"""
		# This method is separate from :meth:`ddprefix`, because Oracle 10 doesn't
		# have a ``DBA_ARGUMENTS`` view.
		if self.connection._ddprefixargs is None:
			try:
				self.execute("select /*+FIRST_ROWS(1)*/ object_name from dba_arguments")
			except DatabaseError as exc:
				if exc.args[0].code == 942: # ORA-00942: table or view does not exist
					self.connection._ddprefixargs = "all"
				else:
					raise
			else:
				self.connection._ddprefixargs = "dba"
		return self.connection._ddprefixargs

	def execute(self, statement, parameters=None, **kwargs):
		if parameters is not None:
			result = super().execute(statement, parameters, **kwargs)
		else:
			result = super().execute(statement, **kwargs)
		if self.description is not None:
			self.rowfactory = RecordMaker(self)
		return result

	def executemany(self, statement, parameters):
		result = super().executemany(statement, parameters)
		if self.description is not None:
			self.rowfactory = RecordMaker(self)
		return result

	def __repr__(self):
		return "<{}.{} statement={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.statement, id(self))


def formatstring(value, latin1=False):
	result = []
	current = []

	if latin1:
		upper = 255
	else:
		upper = 127
	# Helper function: move the content of current to result

	def shipcurrent(force=False):
		if current and (force or (len(current) > 2000)):
			if result:
				result.append(" || ")
			result.append("'{}'".format("".join(current)))

	for c in value:
		if c == "'":
			current.append("''")
			shipcurrent()
		elif ord(c) < 32 or ord(c) > upper:
			shipcurrent(True)
			current = []
			if result:
				result.append(" || ")
			result.append("chr({})".format(ord(c)))
		else:
			current.append(c)
			shipcurrent()
	shipcurrent(True)
	return "".join(result)


def makeurl(name):
	return urllib.request.pathname2url(name.encode("utf-8")).replace("/", "%2f")


###
### Classes used for database meta data
###

class MixinNormalDates:
	"""
	Mixin class that provides methods for determining creation and modification
	dates for objects.
	"""
	def cdate(self):
		cursor = self.getcursor()
		cursor.execute("select created, to_number(to_char(systimestamp, 'TZH')), to_number(to_char(systimestamp, 'TZM')) from {}_objects where lower(object_type)=:type and object_name=:name and owner=nvl(:owner, user)".format(cursor.ddprefix()), type=self.__class__.type, name=self.name, owner=self.owner)
		row = cursor.fetchone()
		if row is None:
			raise SQLObjectNotFoundError(self)
		# FIXME: This is only correct 50% of the time, but Oracle doesn't provide anything better
		return row[0]-datetime.timedelta(seconds=60*(row[1]*60+row[2]))

	def udate(self):
		cursor = self.getcursor()
		cursor.execute("select last_ddl_time, to_number(to_char(systimestamp, 'TZH')), to_number(to_char(systimestamp, 'TZM')) from {}_objects where lower(object_type)=:type and object_name=:name and owner=nvl(:owner, user)".format(cursor.ddprefix()), type=self.__class__.type, name=self.name, owner=self.owner)
		row = cursor.fetchone()
		if row is None:
			raise SQLObjectNotFoundError(self)
		# FIXME: This is only correct 50% of the time, but Oracle doesn't provide anything better
		return row[0]-datetime.timedelta(seconds=60*(row[1]*60+row[2]))


class MixinCodeDDL:
	"""
	Mixin class that provides methods returning the create and drop statements
	for various objects.
	"""
	def _fetch(self, cursor):
		cursor.execute("select text from {}_source where lower(type)=lower(:type) and owner=nvl(:owner, user) and name=:name order by line".format(cursor.ddprefix()), type=self.__class__.type, owner=self.owner, name=self.name)
		code = "\n".join((rec.text or "").rstrip() for rec in cursor) # sqlplus strips trailing spaces when executing SQL scripts, so we do that too
		if not code:
			self._exists = False
		else:
			self._exists = True
			self._code = code

	def createddl(self, term=True):
		if not self._code:
			return ""
		code = " ".join(self._code.split(None, 1)) # compress "PROCEDURE          FOO"
		code = code.strip()
		type = self.__class__.type
		code = code[code.lower().find(type)+len(type):].strip() # drop "procedure" etc.
		# drop our own name (for triggers this includes the schema name)
		if code.startswith('"'):
			code = code[code.find('"', 1)+1:]
		else:
			while code and (code[0].isalnum() or code[0] in "_$."):
				code = code[1:]
		code = "create or replace {} {}{}\n".format(type, self.getfullname(), code)
		if term:
			code += "\n/\n"
		else:
			code += "\n"
		return code

	def dropddl(self, term=True):
		if self.owner is not None:
			name = "{}.{}".format(self.owner, self.name)
		else:
			name = self.name
		code = "drop {} {}".format(self.__class__.type, name)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		if code:
			code = code.split(None, 5)
			code = "create or replace {} {}\n{}".format(code[3], self.getfullname(), code[5])
		return code


def getfullname(name, owner):
	parts = []
	if owner is not None:
		if owner != owner.upper() or not all(c.isalnum() or c == "_" for c in owner):
			part = '"{}"'.format(owner)
		parts.append(owner)
	for part in name.split("."):
		if part != part.upper() or not all(c.isalnum() or c == "_" for c in part):
			part = '"{}"'.format(part)
		parts.append(part)
	return ".".join(parts)


class _Object_meta(type):
	def __new__(mcl, name, bases, dict):
		typename = None
		if "type" in dict and name != "Object":
			typename = dict["type"]
		cls = type.__new__(mcl, name, bases, dict)
		if typename is not None:
			Object.name2type[typename] = cls
		return cls


class Object(object, metaclass=_Object_meta):
	"""
	The base class for all Python classes modelling schema objects in the
	database.
	"""
	name2type = {} # maps the Oracle type name to the Python class (populated by the metaclass)

	def __init__(self, name, owner=None, connection=None):
		self.name = name
		self.owner = owner
		self.connection = connection
		self._exists = None
		self._generated = False
		if name.startswith("BIN$"):
			raise ValueError
		if connection is not None:
			self._fetch(connection.cursor())

	def __repr__(self):
		if self.owner is not None:
			return "{}.{}({!r}, {!r})".format(self.__class__.__module__, self.__class__.__qualname__, self.name, self.owner)
		else:
			return "{}.{}({!r})".format(self.__class__.__module__, self.__class__.__qualname__, self.name)

	def __str__(self):
		if self.owner is not None:
			return "{}({}, {})".format(self.__class__.__qualname__, self.name, self.owner)
		else:
			return "{}({})".format(self.__class__.__qualname__, self.name)

	def __eq__(self, other):
		return self.__class__ is other.__class__ and self.name == other.name and self.owner == other.owner

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.__class__.__name__) ^ hash(self.name) ^ hash(self.owner)

	@misc.notimplemented
	def _fetch(self, cursor):
		pass

	def refresh(self):
		self._fetch(self.getcursor())

	def fromconnection(self, connection):
		return self.__class__(self.name, self.owner, connection)

	def connect(self, connection):
		self.connection = connection
		self.refresh()

	def getcursor(self):
		if self.connection is None:
			raise NotConnectedError(self)
		return self.connection.cursor()

	@property
	def connectstring(self):
		if self.connection:
			return self.connection.connectstring()
		return None

	def getfullname(self):
		return getfullname(self.name, self.owner)

	@misc.notimplemented
	def createddl(self, term=True):
		"""
		Return SQL code to create this object.
		"""

	@misc.notimplemented
	def dropddl(self, term=True):
		"""
		Return SQL code to drop this object
		"""

	@misc.notimplemented
	def fixname(self, code):
		"""
		Replace the name of the object in the SQL code :obj:`code` with
		the name of :obj:`self`.
		"""

	def exists(self):
		"""
		Return whether the object :obj:`self` really exists in the database
		specified by :obj:`connection`.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		return self._exists

	def generated(self):
		"""
		Return whether the object :obj:`self` was generated automatically by
		another object (like an index that gets generated for a primary key or
		a "not null" check constraint that gets generated for a ``not null``
		clause in a ``create table ...`` statement.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._generated

	@misc.notimplemented
	def cdate(self):
		"""
		Return a :class:`datetime.datetime` object with the creation date of
		:obj:`self` in the database specified by :obj:`connection` (or
		:const:`None` if such information is not available).
		"""

	@misc.notimplemented
	def udate(self):
		"""
		Return a :class:`datetime.datetime` object with the last modification
		date of :obj:`self` in the database specified by :obj:`connection`
		(or :const:`None` if such information is not available).
		"""

	def iterreferences(self):
		"""
		Objects directly used by :obj:`self`.

		If :obj:`connection` is not :const:`None` it will be used as the database
		connection from which to fetch data. If :obj:`connection` is :const:`None`
		the connection from which :obj:`self` has been extracted will be used. If
		there is not such connection, you'll get an exception.
		"""
		cursor = self.getcursor()
		query = """
			select distinct
				referenced_type,
				decode(referenced_owner, user, null, referenced_owner) as referenced_owner,
				referenced_name
			from
				{prefix}_dependencies
			where
				type = upper(:type) and
				name = :name and
				owner = nvl(:owner, user) and
				type != 'NON-EXISTENT' and
				(referenced_type != 'TABLE' or ((referenced_owner != 'SYS' or referenced_name not in ({ft})) and referenced_name not like 'BIN$%' and referenced_name not like 'DR$%')) and
				(referenced_type != 'VIEW' or ((referenced_owner != 'SYS' or referenced_name not in ({fv})) and referenced_name not like 'BIN$%' and referenced_name not like 'DR$%'))
			order by
				referenced_owner,
				referenced_name
		"""
		query = query.format(prefix=cursor.ddprefix(), ft=_sql_fixed_tables, fv=_sql_fixed_views)
		cursor.execute(query, type=self.type, name=self.name, owner=self.owner)
		for rec in cursor.fetchall():
			try:
				cls = Object.name2type[rec.referenced_type.lower()]
			except KeyError:
				pass # FIXME: Issue a warning?
			else:
				yield cls(rec.referenced_name, rec.referenced_owner, self.connection)

	def iterreferencesall(self, done=None):
		"""
		All objects used by :obj:`self` (recursively).

		For the meaning of :obj:`connection` see :meth:`iterreferences`.

		:obj:`done` is used internally and shouldn't be passed.
		"""
		if done is None:
			done = set()
		if self not in done:
			done.add(self)
			for obj in self.iterreferences():
				yield from obj.iterreferencesall(done)
			yield self

	def iterreferencedby(self):
		"""
		Objects using :obj:`self`.

		For the meaning of :obj:`connection` see :meth:`iterreferences`.
		"""
		cursor = self.getcursor()
		cursor.execute("select type, decode(owner, user, null, owner) as owner, name from {}_dependencies where referenced_type=upper(:type) and referenced_name=:name and referenced_owner=nvl(:owner, user) and type != 'NON-EXISTENT' order by owner, name".format(cursor.ddprefix()), type=self.type, name=self.name, owner=self.owner)
		for rec in cursor.fetchall():
			try:
				type = Object.name2type[rec.type.lower()]
			except KeyError:
				pass # FIXME: Issue a warning?
			else:
				yield type(rec.name, rec.owner, self.connection)

	def iterreferencedbyall(self, done=None):
		"""
		All objects depending on :obj:`self` (recursively).

		For the meaning of :obj:`connection` see :meth:`iterreferences`.

		:obj:`done` is used internally and shouldn't be passed.
		"""
		if done is None:
			done = set()
		if self not in done:
			done.add(self)
			for obj in self.iterreferencedby():
				yield from obj.iterreferencedbyall(done)
			yield self

	@classmethod
	def iternames(cls, connection, owner=ALL):
		"""
		Generator that yields the names of all objects of this type. The argument
		:obj:`owner` specifies whose objects are yielded:

			:const:`None`
				All objects belonging to the current user (i.e. via the view
				``USER_OBJECTS``).

			:const:`ALL`
				All objects for all users (via the views ``ALL_OBJECTS`` or
				``DBA_OBJECTS``)

			username : string
				All objects belonging to the specified user

		Names will be in ascending order.
		"""
		cursor = connection.cursor()
		if owner is None:
			query = """
				select
					null as owner,
					object_name
				from
					user_objects
				where
					lower(object_type) = :type and
					object_name not like 'BIN$%' and
					object_name not like 'DR$%' and
					(object_type != 'TABLE' or user != 'SYS' or object_name not in ({ft})) and
					(object_type != 'VIEW' or user != 'SYS' or object_name not in ({fv}))
				order by
					object_name
			"""
			kwargs = {"type": cls.type}
		elif owner is ALL:
			query = """
				select
					decode(owner, user, null, owner) as owner,
					object_name from {prefix}_objects
				where
					lower(object_type) = :type and
					object_name not like 'BIN$%' and
					object_name not like 'DR$%' and
					(object_type != 'TABLE' or owner != 'SYS' or object_name not in ({ft})) and
					(object_type != 'VIEW' or owner != 'SYS' or object_name not in ({fv}))
				order by
					owner,
					object_name
			"""
			kwargs = {"type": cls.type}
		else:
			query = """
				select
					decode(owner, user, null, owner) as owner,
					object_name from {prefix}_objects
				where
					lower(object_type) = :type and
					object_name not like 'BIN$%' and
					object_name not like 'DR$%' and
					owner=:owner and
					(object_type != 'TABLE' or owner != 'SYS' or object_name not in ({ft})) and
					(object_type != 'VIEW' or owner != 'SYS' or object_name not in ({fv}))
				order by
					owner,
					object_name
			"""
			kwargs = {"type": cls.type, "owner": owner}
		cursor.execute(query.format(prefix=cursor.ddprefix(), ft=_sql_fixed_tables, fv=_sql_fixed_views), **kwargs)
		return ((row.object_name, row.owner) for row in cursor)

	@classmethod
	def iterobjects(cls, connection, owner=ALL):
		"""
		Generator that yields all objects of this type in the current users schema.
		The argument :obj:`owner` specifies whose objects are yielded:

			:const:`None`
				All objects belonging to the current user (i.e. via the view
				``USER_OBJECTS``).

			:const:`ALL`
				All objects for all users (via the views ``ALL_OBJECTS`` or
				``DBA_OBJECTS``)

			username : string
				All objects belonging to the specified user
		"""
		return (cls(name[0], name[1], connection) for name in cls.iternames(connection, owner))


class Sequence(MixinNormalDates, Object):
	"""
	Models a sequence in the database.
	"""
	type = "sequence"

	def _fetch(self, cursor):
		cursor.execute("select * from {}_sequences where sequence_owner=nvl(:owner, user) and sequence_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._increment_by = rec.increment_by
			self._last_number = rec.last_number
			self._max_value = rec.max_value
			self._min_value = rec.min_value
			self._cycle = rec.cycle_flag == "Y"
			self._cache_size = rec.cache_size

	def _createddl(self, term, copyvalue):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		code  = "create sequence {}\n".format(self.getfullname())
		code += "\tincrement by {}\n".format(self._increment_by)
		if copyvalue:
			code += "\tstart with {}\n".format(self._last_number + self._increment_by)
		else:
			code += "\tstart with {}\n".format(self._min_value)
		code += "\tmaxvalue {}\n".format(self._max_value)
		code += "\tminvalue {}\n".format(self._min_value)
		code += "\t{}cycle\n".format("" if self._cycle else "no")
		if self._cache_size:
			code += "\tcache {}\n".format(self._cache_size)
		else:
			code += "\tnocache\n"
		code += "\t{}order".format("" if self._cycle else "no")
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def exists(self):
		if self.connection is None:
			raise NotConnectedError(self)
		return self._exists

	def createddl(self, term=True):
		return self._createddl(term, False)

	def createddlcopy(self, term=True):
		"""
		Return SQL code to create an identical copy of this sequence.
		"""
		return self._createddl(term, True)

	def dropddl(self, term=True):
		code = "drop sequence {}".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		code = code.split(None, 3)
		code = "create sequence {}\n{}".format(self.getfullname(), code[3])
		return code

	def iterreferences(self, done=None):
		# Shortcut: a sequence doesn't depend on anything
		if False:
			yield None


def _columntype(data, data_precision=None, data_scale=None, char_length=None):
	ftype = data["_data_type"].lower()
	if data_precision is None:
		data_precision = data["_data_precision"]
	if data_scale is None:
		data_scale = data["_data_scale"]
	if char_length is None:
		char_length = data["_char_length"]

	fsize = data_precision
	fprec = data_scale
	if ftype == "number" and fprec == 0 and fsize is None:
		ftype = "integer"
	elif ftype == "number" and fprec is None and fsize is None:
		ftype = "number"
	elif ftype == "number" and fprec == 0:
		ftype = "number({})".format(fsize)
	elif ftype == "number":
		ftype = "number({}, {})".format(fsize, fprec)
	elif ftype == "raw":
		ftype = "raw({})".format(data["_data_length"])
	else:
		if char_length != 0:
			fsize = char_length
		if fsize is not None:
			ftype += "({}".format(fsize)
			if data["_char_used"] == "B":
				ftype += " byte"
			elif data["_char_used"] == "C":
				ftype += " char"
			if fprec is not None:
				ftype += ", {}".format(fprec)
			ftype += ")"
	return ftype


def _columndefault(data):
	default = data["_data_default"]
	if default is not None and default != "null\n":
		return default.rstrip("\n")
	return "null"


class Table(MixinNormalDates, Object):
	"""
	Models a table in the database.
	"""
	type = "table"

	def _fetch(self, cursor):
		ddprefix = cursor.ddprefix()
		cursor.execute("select iot_type from {}_tables where owner=nvl(:owner, user) and table_name=:name".format(ddprefix), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._organization = "heap" if rec.iot_type is None else "index"

			cursor.execute("select mview_name from {}_mviews where owner=nvl(:owner, user) and mview_name=:name".format(ddprefix), owner=self.owner, name=self.name)
			rec = cursor.fetchone()
			self._generated = rec is not None

			# Find the fields that where used for an inline primary key constraint, as we want to regenerate it as part of the create table statement
			cursor.execute("select column_name from {}_constraints c, {}_cons_columns cc where c.constraint_type='P' and c.generated = 'GENERATED NAME' and c.owner=nvl(:owner, user) and c.table_name=:name and c.constraint_name=cc.constraint_name".format(ddprefix, ddprefix), owner=self.owner, name=self.name)
			_pkfields = {rec.column_name for rec in cursor}

			cursor.execute("select column_name, comments from {}_col_comments where owner=nvl(:owner, user) and table_name=:name and comments is not null".format(cursor.ddprefix()), owner=self.owner, name=self.name)
			comments = {rec.column_name: rec.comments for rec in cursor if rec.comments is not None}

			self._columns = []
			cursor.execute('select * from {}_tab_columns where owner=nvl(:owner, user) and table_name=:name order by column_id asc'.format(cursor.ddprefix()), owner=self.owner, name=self.name)
			self._columns = [
				{
					"_column_name": rec.column_name,
					"_data_type": rec.data_type,
					"_data_precision": rec.data_precision,
					"_data_scale": rec.data_scale,
					"_char_length": rec.char_length,
					"_char_used": rec.char_used,
					"_data_default": rec.data_default,
					"_nullable": rec.nullable == "N",
					"_comment": comments.get(rec.column_name),
					"_pk": rec.column_name in _pkfields
				}
				for rec in cursor
			]

	def createddl(self, term=True):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)

		code = ["create table {}\n(\n".format(self.getfullname())]
		for (i, column) in enumerate(self._columns):
			if i:
				code.append(",\n")
			code.append("\t{} {}".format(getfullname(column["_column_name"], None), _columntype(column)))
			default = _columndefault(column)
			if default != "null":
				code.append(" default {}".format(default))
			if column["_nullable"]:
				code.append(" not null")
			if column["_pk"]:
				code.append(" primary key")
		if term:
			code.append("\n);\n")
		else:
			code.append("\n)\n")
		return "".join(code)

	def dropddl(self, term=True):
		code = "drop table {}".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		code = code.split(None, 3)
		code = "create table {}\n{}".format(self.getfullname(), code[3])
		return code

	# :meth:`generated` returns whether this table a materialized view

	def mview(self):
		"""
		The materialized view this table belongs to (or :const:`None` if it's a
		real table).
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		if self._generated:
			return MaterializedView(self.name, self.owner, self.connection)
		return None

	def organization(self, connection=None):
		"""
		Return the organization of this table: either ``"heap"`` (for "normal"
		tables) or ``"index"`` (for index organized tables).
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._organization

	@classmethod
	def iternames(cls, connection, owner=ALL):
		cursor = connection.cursor()
		if owner is None:
			query = """
				select
					null as owner,
					table_name
				from
					user_tables
				where
					table_name not like 'BIN$%' and
					table_name not like 'DR$%' and
					table_name not in ({ft})
			"""
			kwargs = {}
		elif owner is ALL:
			query = """
				select
					decode(owner, user, null, owner) as owner,
					table_name
				from
					{prefix}_tables
				where
					table_name not like 'BIN$%' and
					table_name not like 'DR$%' and
					(owner != 'SYS' or table_name not in ({ft}))
			"""
			kwargs = {}
		else:
			query = """
				select
					decode(owner, user, null, owner) as owner,
					table_name
				from
					{prefix}_tables
				where
					table_name not like 'BIN$%' and
					table_name not like 'DR$%' and
					owner=:owner and
					(owner != 'SYS' or table_name not in ({ft}))
			"""
			kwargs = {"owner": owner}
		cursor.execute(query.format(prefix=cursor.ddprefix(), ft=_sql_fixed_tables, fv=_sql_fixed_views), **kwargs)
		return ((row.table_name, row.owner) for row in cursor)

	def itercolumns(self):
		"""
		Generator that yields all column objects of this table.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)

		for data in self._columns:
			column = Column("{}.{}".format(self.name, data["_column_name"]), self.owner)
			column._exists = True
			for (key, value) in data.items():
				if key != "_column_name":
					setattr(column, key, value)
			column.connection = self.connection
			yield column

	def itercomments(self):
		"""
		Generator that yields all column comments of this table.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)

		for data in self._columns:
			name = data["_column_name"]
			comment = Comment("{}.{}".format(self.name, name), self.owner)
			comment._exists = True
			comment._text = data["_comment"]
			comment.connection = self.connection
			yield comment

	def iterrecords(self):
		"""
		Generator that yields all records of this table.
		"""
		cursor = self.getcursor()
		query = "select * from {}".format(self.getfullname())
		cursor.execute(query)
		return iter(cursor)

	def _iterconstraints(self, cond):
		cursor = self.getcursor()
		cursor.execute("select decode(owner, user, null, owner) as owner, constraint_type, constraint_name from {}_constraints where {} and owner=nvl(:owner, user) and table_name=:name".format(cursor.ddprefix(), cond), owner=self.owner, name=self.name)
		types = {"P": PrimaryKey, "U": UniqueConstraint, "R": ForeignKey, "C": CheckConstraint}
		return (types[rec.constraint_type](rec.constraint_name, rec.owner, self.connection) for rec in cursor)

	def iterconstraints(self):
		"""
		Generator that yields all constraints for this table.
		"""
		return self._iterconstraints("constraint_type in ('P', 'U', 'R', 'C')")

	def pk(self):
		"""
		Return the primary key constraint for this table (or :const:`None` if the
		table has no primary key constraint).
		"""
		return misc.first(self._iterconstraints("constraint_type = 'P'"), None)

	def iterreferences(self):
		# A table doesn't depend on anything ...
		mview = self.mview()
		if mview is not None:
			# ... unless it was created by a materialized view, in which case it depends on the view
			yield mview

	def iterreferencedby(self):
		if not self.generated():
			yield from self.itercomments()
			yield from self.iterconstraints()
		for obj in super().iterreferencedby():
			# skip the materialized view
			if not isinstance(obj, MaterializedView) or obj.name != self.name or obj.owner != self.owner:
				yield obj


class Column(Object):
	"""
	Models a single column of a table in the database. This is used to output
	``ALTER TABLE`` statements for adding, dropping and modifying columns.
	"""
	type = "column"

	def _fetch(self, cursor):
		ddprefix = cursor.ddprefix()
		name = self.name.split(".")
		cursor.execute("select * from {}_tab_columns where owner=nvl(:owner, user) and table_name=:table_name and column_name=:column_name".format(ddprefix), owner=self.owner, table_name=name[0], column_name=name[1])
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._data_type = rec.data_type
			self._data_precision = rec.data_precision
			self._data_scale = rec.data_scale
			self._char_length = rec.char_length
			self._char_used = rec.char_used
			self._data_default = rec.data_default
			self._nullable = rec.nullable == "N"

			cursor.execute("select comments from {}_col_comments where owner=nvl(:owner, user) and table_name=:table_name and column_name=:column_name".format(ddprefix), owner=self.owner, table_name=name[0], column_name=name[1])
			rec = cursor.fetchone()
			self._comment = rec.comments if rec is not None else None

			cursor.execute("select 1 from {}_constraints c, {}_cons_columns cc where c.constraint_type='P' and c.generated = 'GENERATED NAME' and c.owner=nvl(:owner, user) and c.table_name=:table_name and c.constraint_name=cc.constraint_name and cc.column_name=:column_name".format(ddprefix, ddprefix), owner=self.owner, table_name=name[0], column_name=name[1])
			rec = cursor.fetchone()
			self._pk = rec is not None

	def addddl(self, term=True):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		name = self.name.split(".")
		code = ["alter table {} add {}".format(getfullname(name[0], self.owner), getfullname(name[1], None))]
		code.append(" {}".format(_columntype(self.__dict__)))
		default = _columndefault(self.__dict__)
		if default != "null":
			code.append(" default {}".format(default))
		if self._nullable:
			code.append(" not null")
		if self._pk:
			code.append(" primary key")
		if term:
			code.append(";\n")
		else:
			code.append("\n")
		return "".join(code)

	def modifyddl(self, old, new, term=True):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)

		if old.connection is None:
			raise NotConnectedError(old)
		if not old._exists:
			raise SQLObjectNotFoundError(old)

		if new.connection is None:
			raise NotConnectedError(new)
		if not new._exists:
			raise SQLObjectNotFoundError(new)

		name = self.name.split(".")

		code = ["alter table {} modify {}".format(getfullname(name[0], self.owner), getfullname(name[1], None))]
		# Has the type changed?
		if old._data_precision != new._data_precision or old._data_scale != new._data_scale or old._char_length != new._char_length or old._data_type != new._data_type:
			# Has only the size changed?
			if self._data_type == old._data_type == new._data_type:
				try:
					data_precision = max(r._data_precision for r in (self, old, new) if r._data_precision is not None)
				except ValueError:
					data_precision = None
				try:
					data_scale = max(r._data_scale for r in (self, old, new) if r._data_scale is not None)
				except ValueError:
					data_scale = None
				try:
					char_length = max(r._char_length for r in (self, old, new) if r._char_length is not None)
				except ValueError:
					char_length = None
				code.append(" {}".format(_columntype(self, data_precision=data_precision, data_scale=data_scale, char_length=char_length)))
			else: # The type has changed too
				if new._data_type != self._data_type:
					raise ConflictError(self, "data_type unmergeable")
				elif new._data_precision != self._data_precision:
					raise ConflictError(self, "data_precision unmergeable")
				elif new._data_scale != self._data_scale:
					raise ConflictError(self, "data_scale unmergeable")
				elif new._char_length != self._char_length:
					raise ConflictError(self, "char_length unmergeable")
				code.append(" {}".format(_columntype(new)))

		# Has the default changed?
		default = _columndefault(self)
		olddefault = _columndefault(old)
		newdefault = _columndefault(new)
		if olddefault != newdefault:
			if newdefault != default:
				raise ConflictError(self, "default value unmergable")
			code.append(" default {}".format(newdefault))

		# Check nullability
		if old._nullable != new._nullable:
			if not new._nullable:
				code.append(" not null")
			else:
				code.append(" null")

		if term:
			code.append(";\n")
		else:
			code.append("\n")

		return "".join(code)

	def dropddl(self, term=True):
		name = self.name.split(".")
		code = "alter table {} drop column {}".format(getfullname(name[0], self.owner), getfullname(name[1], None))
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def table(self):
		name = self.name.split(".")
		return Table(name[0], self.owner, self.connection)

	def cdate(self):
		# The column creation date is the table creation date
		return self.table().cdate()

	def udate(self):
		# The column modification date is the table modification date
		return self.table().udate()

	def iterreferences(self):
		yield Table(self.name.split(".")[0], self.owner, self.connection)

	def iterreferencedby(self):
		if False:
			yield None

	def datatype(self):
		"""
		The SQL type of this column.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return _columntype(self.__dict__)

	def default(self):
		"""
		The SQL default value for this column.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return _columndefault(self.__dict__)

	def nullable(self, connection=None):
		"""
		Is this column nullable?
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._nullable

	def comment(self):
		"""
		The comment for this column.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._comment


class Comment(Object):
	"""
	Models a column comment in the database.
	"""
	type = "comment"

	def _fetch(self, cursor):
		cursor = self.getcursor()
		name = self.name.split(".")
		cursor.execute("select comments from {}_col_comments where owner=nvl(:owner, user) and table_name=:table_name and column_name=:column_name".format(cursor.ddprefix()), owner=self.owner, table_name=name[0], column_name=name[1])
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._text = rec.comments

	def text(self):
		"""
		Return the comment text for this column.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._text

	def createddl(self, term=True):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)

		name = self.getfullname()
		code = "comment on column {} is '{}'".format(name, (self._text or "").replace("'", "''"))
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def dropddl(self, connection=None, term=True):
		# will be dropped with the table
		return ""

	def fixname(self, code):
		code = code.split(None, 5)
		code = "comment on column {} is {}".format(self.getfullname(), code[5])
		return code

	def cdate(self):
		return None

	def udate(self):
		return None

	def table(self):
		return Table(self.name.split(".")[0], self.owner, self.connection)

	def iterreferences(self):
		yield self.table()

	def iterreferencedby(self):
		if False:
			yield None


class Constraint(Object):
	"""
	Base class of all constraints (primary key constraints, foreign key
	constraints, unique constraints and check constraints).
	"""

	def _fetch(self, cursor):
		cursor = self.getcursor()
		cursor.execute("select table_name, decode(r_owner, user, null, r_owner) as r_owner, r_constraint_name, generated, status, search_condition, last_change, to_number(to_char(systimestamp, 'TZH')) tzh, to_number(to_char(systimestamp, 'TZM')) tzm from {}_constraints where constraint_type=:type and constraint_name=:name and owner=nvl(:owner, user)".format(cursor.ddprefix()), type=self.constraint_type, name=self.name, owner=self.owner)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._table_name = rec.table_name
			self._r_owner = rec.r_owner
			self._r_constraint_name = rec.r_constraint_name
			self._generated = rec.generated == "GENERATED NAME"
			self._enabled = rec.status == "ENABLED"
			self._search_condition = rec.search_condition
			self._date = rec.last_change-datetime.timedelta(seconds=60*(rec.tzh*60+rec.tzm))

	def cdate(self):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._date

	def udate(self):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._date

	def _ddl(self, term, command):
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)

		tablename = getfullname(self._table_name, self.owner)
		checkname = getfullname(self.name, None)
		code = "alter table {} {} constraint {}".format(tablename, command, checkname)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def dropddl(self, term=True):
		return self._ddl(term, "drop")

	def enableddl(self, term=True):
		return self._ddl(term, "enable")

	def disableddl(self, term=True):
		return self._ddl(term, "disable")

	def isenabled(self):
		"""
		Return whether this constraint is enabled.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return self._enabled

	@classmethod
	def iternames(cls, connection, owner=ALL):
		cursor = connection.cursor()
		if owner is None:
			query = """
				select
					null as owner,
					constraint_name
				from
					user_constraints
				where
					constraint_type=:type and
					constraint_name not like 'BIN$%'
				order by
					constraint_name
			"""
			kwargs = {"type": cls.constraint_type}
		elif owner is ALL:
			query = """
				select
					decode(owner, user, null, owner) as owner,
					constraint_name
				from
					{prefix}_constraints
				where
					constraint_type=:type and
					constraint_name not like 'BIN$%'
				order by
					owner,
					constraint_name
			"""
			kwargs = {"type": cls.constraint_type}
		else:
			query = """
				select
					decode(owner, user, null, owner) as owner,
					constraint_name
				from
					{prefix}_constraints
				where
					constraint_type=:type and
					constraint_name not like 'BIN$%' and
					owner=:owner
				order by
					owner,
					constraint_name
			"""
			kwargs = {"type": cls.constraint_type, "owner": owner}
		cursor.execute(query.format(prefix=cursor.ddprefix()), **kwargs)
		return ((rec.constraint_name, rec.owner) for rec in cursor)

	def fixname(self, code):
		code = code.split(None, 6)
		code = "alter table {} add constraint {} {}".format(code[2], self.getfullname(), code[6])
		return code

	def table(self):
		"""
		Return the :class:`Table` :obj:`self` belongs to.
		"""
		if self.connection is None:
			raise NotConnectedError(self)
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		return Table(self._table_name, self.owner, self.connection)


class PrimaryKey(Constraint):
	"""
	Models a primary key constraint in the database.
	"""
	type = "pk"
	constraint_type = "P"

	def itercolumns(self):
		"""
		Return an iterator over the columns this primary key consists of.
		"""
		cursor = self.getcursor()
		tablename = getfullname(self._table_name, self.owner)
		cursor.execute("select column_name from {}_cons_columns where owner=nvl(:owner, user) and constraint_name=:name order by position".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		return (Column("{}.{}".format(tablename, rec.column_name), self.owner, self.connection) for rec in cursor)

	def createddl(self, term=True):
		cursor = self.getcursor()
		cursor.execute("select column_name from {}_cons_columns where owner=nvl(:owner, user) and constraint_name=:name order by position".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		tablename = getfullname(self._table_name, self.owner)
		pkname = getfullname(self.name, None)
		code = "alter table {} add constraint {} primary key({})".format(tablename, pkname, ", ".join(r.column_name for r in cursor))
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def iterreferencedby(self):
		cursor = self.getcursor()
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		cursor.execute("select decode(owner, user, null, owner) as owner, constraint_name from {}_constraints where constraint_type='R' and r_owner=nvl(:owner, user) and r_constraint_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		for rec in cursor.fetchall():
			yield ForeignKey(rec.constraint_name, rec.owner, self.connection)
		# Normally there is an index for this primary key, but we ignore it, as for the purpose of :mod:`orasql` this index doesn't exist

	def iterreferences(self):
		yield self.table()


class ForeignKey(Constraint):
	"""
	Models a foreign key constraint in the database.
	"""
	type = "fk"
	constraint_type = "R"

	def createddl(self, term=True):
		cursor = self.getcursor()
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		cursor.execute("select column_name from {}_cons_columns where owner=nvl(:owner, user) and constraint_name=:name order by position".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		fields1 = ", ".join(r.column_name for r in cursor)
		cursor.execute("select table_name, column_name from {}_cons_columns where owner=nvl(:owner, user) and constraint_name=:name order by position".format(cursor.ddprefix()), owner=self._r_owner, name=self._r_constraint_name)
		fields2 = ", ".join("{}({})".format(getfullname(r.table_name, self._r_owner), r.column_name) for r in cursor)
		tablename = getfullname(self._table_name, self.owner)
		fkname = getfullname(self.name, None)
		code = "alter table {} add constraint {} foreign key ({}) references {}".format(tablename, fkname, fields1, fields2)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def iterreferencedby(self):
		# Shortcut: Nobody references a foreign key
		if False:
			yield None

	def iterreferences(self):
		yield self.table()
		yield self.pk()

	def pk(self):
		"""
		Return the primary key referenced by :obj:`self`.
		"""
		cursor = self.getcursor()
		cursor.execute("select decode(r_owner, user, null, r_owner) as r_owner, r_constraint_name from {}_constraints where constraint_type='R' and owner=nvl(:owner, user) and constraint_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		return PrimaryKey(rec.r_constraint_name, rec.r_owner, self.connection)

	def itercolumns(self):
		"""
		Return an iterator over the columns this foreign key consists of.
		"""
		cursor = self.getcursor()
		cursor.execute("select decode(owner, user, null, owner) as owner, table_name, column_name from {}_cons_columns where constraint_name=:name and owner=nvl(:owner, user) order by position".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		for r in cursor:
			yield Column("{}.{}".format(r.table_name, r.column_name), r.owner, self.connection)


class UniqueConstraint(Constraint):
	"""
	Models a unique constraint in the database.
	"""
	type = "unique"
	constraint_type = "U"

	def createddl(self, connection=None, term=True):
		cursor = self.getcursor()
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		tablename = getfullname(self._table_name, self.owner)
		uniquename = getfullname(self.name, None)
		cursor.execute("select column_name from all_cons_columns where owner=nvl(:owner, user) and constraint_name=:name", owner=self.owner, name=self.name)
		code = "alter table {} add constraint {} unique({})".format(tablename, uniquename, ", ".join(r.column_name for r in cursor))
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def iterreferencedby(self):
		cursor = self.getcursor()
		cursor.execute("select decode(owner, user, null, owner) as owner, constraint_name from {}_constraints where constraint_type='R' and r_owner=nvl(:owner, user) and r_constraint_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		for rec in cursor.fetchall():
			yield ForeignKey(rec.constraint_name, rec.owner, self.connection)

		# Normally there is an index for this constraint, but we ignore it, as for the purpose of :mod:`orasql` this index doesn't exist

	def iterreferences(self):
		cursor = self.getcursor()
		cursor.execute("select decode(owner, user, null, owner) as owner, table_name from {}_constraints where constraint_type='U' and owner=nvl(:owner, user) and constraint_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		for rec in cursor.fetchall():
			yield Table(rec.table_name, rec.owner, self.connection)


class CheckConstraint(Constraint):
	"""
	Models a check constraint in the database.
	"""
	type = "check"
	constraint_type = "C"

	def createddl(self, term=True):
		cursor = self.getcursor()
		if not self._exists:
			raise SQLObjectNotFoundError(self)
		tablename = getfullname(self._table_name, self.owner)
		checkname = getfullname(self.name, None)
		code = "alter table {} add constraint {} check ({})".format(tablename, checkname, self._search_condition)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def iterreferencedby(self):
		# Shortcut: Nobody references a check constraint
		if False:
			yield None

	def iterreferences(self):
		cursor = self.getcursor()
		cursor.execute("select decode(owner, user, null, owner) as owner, table_name from {}_constraints where constraint_type='C' and owner=nvl(:owner, user) and constraint_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		for rec in cursor.fetchall():
			yield Table(rec.table_name, rec.owner, self.connection)


class Index(MixinNormalDates, Object):
	"""
	Models an index in the database.
	"""
	type = "index"

	def _fetch(self, cursor):
		cursor.execute("select table_name, uniqueness, index_type, ityp_owner, ityp_name, parameters from {}_indexes where owner=nvl(:owner, user) and index_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._table_name = rec.table_name
			self._unique = rec.uniqueness == "UNIQUE"
			self._index_type = rec.index_type
			self._ityp_owner = rec.ityp_owner
			self._ityp_name = rec.ityp_name
			self._parameters = rec.parameters

	def createddl(self, term=True):
		cursor = self.getcursor()
		indexname = self.getfullname()
		unique = " unique" if self._unique else ""
		cursor.execute("select aie.column_expression, aic.column_name from {0}_ind_columns aic, {0}_ind_expressions aie where aic.index_owner=aie.index_owner(+) and aic.index_name=aie.index_name(+) and aic.column_position=aie.column_position(+) and aic.index_owner=nvl(:owner, user) and aic.index_name=:name order by aic.column_position".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		code = "create{} index {} on {} ({})".format(unique, indexname, self._table_name, ", ".join(r.column_expression or r.column_name for r in cursor))
		if self._index_type == "DOMAIN":
			if self._parameters:
				parameters = " parameters ('{}')".format(self_.parameters.replace("'", "''"))
			else:
				parameters = ""
			code += " indextype is {}.{}{}".format(self._ityp_owner, self._ityp_name, parameters)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def dropddl(self, term=True):
		code = "drop index {}".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def rebuildddl(self, term=True):
		"""
		Return SQL code to rebuild this index.
		"""
		code = "alter index {} rebuild".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	@classmethod
	def iternames(cls, connection, owner=ALL):
		# We skip those indexes that are generated by a constraint
		cursor = connection.cursor()
		if owner is None:
			cursor.execute("select null as owner, index_name from (select index_name from user_indexes where index_type not in ('LOB', 'IOT - TOP') minus select index_name from user_constraints where constraint_type in ('U', 'P') and owner=user) where index_name not like 'BIN$%' order by index_name")
		elif owner is ALL:
			cursor.execute("select decode(owner, user, null, owner) as owner, index_name from (select owner, index_name from {0}_indexes where index_type not in ('LOB', 'IOT - TOP') minus select index_owner, index_name from {0}_constraints where constraint_type in ('U', 'P')) where index_name not like 'BIN$%' order by owner, index_name".format(cursor.ddprefix()))
		else:
			cursor.execute("select decode(owner, user, null, owner) as owner, index_name from (select owner, index_name from {0}_indexes where index_type not in ('LOB', 'IOT - TOP') and owner = :owner minus select index_owner, index_name from {0}_constraints where constraint_type in ('U', 'P') and index_owner = :owner) where index_name not like 'BIN$%' order by owner, index_name".format(cursor.ddprefix()), owner=owner)
		return ((rec.index_name, rec.owner) for rec in cursor)

	def fixname(self, code):
		if code.lower().startswith("create unique"):
			code = code.split(None, 5)
			code = "create unique index {} {}".format(self.getfullname(), code[5])
		else:
			code = code.split(None, 4)
			code = "create index {} {}".format(self.getfullname(), code[4])
		return code

	def constraint(self):
		"""
		If this index is generated by a constraint, return the constraint
		otherwise return :const:`None`.
		"""
		cursor = self.getcursor()
		cursor.execute("select constraint_type from {}_constraints where owner=nvl(:owner, user) and constraint_name=:name and constraint_type in ('U', 'P')".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is not None:
			rec = {"U": UniqueConstraint, "P": PrimaryKey}[rec.constraint_type](self.name, self.owner, self.connection)
		return rec

	def generated(self):
		"""
		Is this index generated by a constraint?
		"""
		cursor = self.getcursor()
		cursor.execute("select 1 from {}_constraints where owner=nvl(:owner, user) and constraint_name=:name and constraint_type in ('U', 'P')".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		return rec is not None

	def iterreferences(self):
		# If this is a domain index, reference the preferences defined there
		if self._index_type == "DOMAIN":
			parameters = re.split('\\b(datastore|memory|lexer|stoplist|wordlist)\\b', self._parameters, flags=re.IGNORECASE)
			foundparameter = None
			for parameter in parameters:
				if foundparameter:
					if foundparameter.lower() in ("datastore", "lexer", "stoplist", "wordlist"):
						(prefowner, sep, prefname) = parameter.strip().partition(".")
						if sep:
							yield Preference(prefname.upper(), prefowner, self.connection)
						else:
							yield Preference(prefowner.upper(), None, self.connection)
					foundparameter = None
				elif parameter.lower() in ("datastore", "lexer", "stoplist", "wordlist"):
					foundparameter = parameter

		yield from super().iterreferences()

	def table(self):
		"""
		Return the :class:`Table` :obj:`self` belongs to.
		"""
		cursor = self.getcursor()
		cursor.execute("select table_name, decode(table_owner, user, null, table_owner) as table_owner from {}_indexes where owner=nvl(:owner, user) and index_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		return Table(rec.table_name, rec.table_owner, self.connection)

	def itercolumns(self):
		"""
		Return an iterator over the columns this index consists of.
		"""
		cursor = self.getcursor()
		table = self.table()
		cursor.execute("select aie.column_expression, aic.column_name from {0}_ind_columns aic, {0}_ind_expressions aie where aic.index_owner=aie.index_owner(+) and aic.index_name=aie.index_name(+) and aic.column_position=aie.column_position(+) and aic.index_owner=nvl(:owner, user) and aic.index_name=:name order by aic.column_position".format(cursor.ddprefix()), owner=self.owner, name=self.name)

		for rec in cursor:
			if rec.column_expression is not None:
				raise TypeError("{!r} contains an index expression".format(self))
			yield Column("{}.{}".format(table.name, rec.column_name), table.owner, self.connection)


class Synonym(Object):
	"""
	Models a synonym in the database.
	"""
	type = "synonym"

	def _fetch(self, cursor):
		cursor.execute("select table_owner, table_name, db_link from {}_synonyms where owner=nvl(:owner, user) and synonym_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._table_owner = rec.table_owner
			self._table_name = rec.table_name
			self._db_link = rec.db_link

	def createddl(self, term=True):
		owner = self.owner
		if owner == "PUBLIC":
			public = "public "
			owner = None
		else:
			public = ""
		name = getfullname(self.name, owner)
		name2 = getfullname(self._table_name, self._table_owner)
		code = "create or replace {}synonym {} for {}".format(public, name, name2)
		if self._db_link is not None:
			code += "@{}".format(self._db_link)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def dropddl(self, term=True):
		owner = self.owner
		if owner == "PUBLIC":
			public = "public "
			owner = None
		else:
			public = ""
		name = getfullname(self.name, owner)
		code = "drop {}synonym {}".format(public, name)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		if code.lower().startswith("create or replace public"):
			code = code.split(None, 6)
			code = "create or replace public synonym {} {}".format(self.getfullname(), code[6])
		else:
			code = code.split(None, 5)
			code = "create or replace synonym {} {}".format(self.getfullname(), code[5])
		return code

	def cdate(self):
		return None

	def udate(self):
		return None

	def iterreferences(self, done=None):
		# Shortcut: a synonym doesn't depend on anything
		if False:
			yield None

	def getobject(self):
		"""
		Get the object for which :obj:`self` is a synonym.
		"""
		cursor = self.getcursor()
		cursor.execute("select table_owner, table_name, db_link from {}_synonyms where owner=nvl(:owner, user) and synonym_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			raise SQLObjectNotFoundError(self)
		return connection._getobject(rec.table_name, rec.table_owner)


class View(MixinNormalDates, Object):
	"""
	Models a view in the database.
	"""
	type = "view"

	def _fetch(self, cursor):
		cursor.execute("select text from {}_views where owner=nvl(:owner, user) and view_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._text = rec.text

	def createddl(self, term=True):
		code = "\n".join(line.rstrip() for line in self._text.strip().splitlines()) # Strip trailing whitespace
		code = "create or replace force view {} as\n\t{}".format(self.getfullname(), code)
		if term:
			code += "\n/\n"
		else:
			code += "\n"
		return code

	def dropddl(self, term=True):
		code = "drop view {}".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		code = code.split(None, 6)
		code = "create or replace force view {} {}".format(self.getfullname(), code[6])
		return code

	def iterrecords(self):
		cursor = self.getcursor()
		query = "select * from {}".format(self.getfullname())
		cursor.execute(query)
		return iter(cursor)


class MaterializedView(View):
	"""
	Models a meterialized view in the database.
	"""
	type = "materialized view"

	def _fetch(self, cursor):
		cursor.execute("select * from {}_mviews where owner=nvl(:owner, user) and mview_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._query = rec.query
			self._refresh_method = rec.refresh_method
			self._refresh_mode = rec.refresh_mode

	def createddl(self, term=True):
		code = "\n".join(line.rstrip() for line in self._query.strip().splitlines()) # Strip trailing whitespace
		code = "create materialized view {}\nrefresh {} on {} as\n\t{}".format(self.getfullname(), self._refresh_method, self._refresh_mode, code)
		if term:
			code += "\n/\n"
		else:
			code += "\n"
		return code

	def dropddl(self, term=True):
		code = "drop materialized view {}".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		code = code.split(None, 4)
		code = "create materialized view {} {}".format(self.getfullname(), code[4])
		return code

	# def iterreferences(self):
	# 	# skip the table
	# 	for obj in super().iterreferences(connection):
	# 		if not isinstance(obj, Table) or obj.name != self.name or obj.owner != self.owner:
	# 			yield obj

	# def iterreferencedby(self, connection=None):
	# 	connection = self.getconnection(connection)
	# 	yield Table(self.name, self.owner, connection)


class Library(Object):
	"""
	Models a library in the database.
	"""
	type = "library"

	def _fetch(self, cursor):
		cursor.execute("select file_spec from {}_libraries where owner=nvl(:owner, user) and library_name=:name".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._filespec = rec.file_spec

	def createddl(self, term=True):
		return "create or replace library {} as {!r}".format(self.getfullname(), self._filespec)
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def dropddl(self, term=True):
		code = "drop library {}".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		code = code.split(None, 5)
		code = "create or replace library {} {}".format(self.getfullname(), code[5])
		return code


class Argument:
	"""
	:class:`Argument` objects hold information about the arguments of a
	stored procedure.
	"""
	def __init__(self, name, position, datatype, isin, isout):
		self.name = name
		self.position = position
		self.datatype = datatype
		self.isin = isin
		self.isout = isout

	def __repr__(self):
		return "<{}.{} name={!r} position={!r} datatype={!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.name, self.position, self.datatype, id(self))


class Callable(MixinNormalDates, MixinCodeDDL, Object):
	"""
	Models a callable object in the database, i.e. functions and procedures.
	"""

	_ora2cx = {
		"date": datetime.datetime,
		"timestamp": datetime.datetime,
		"timestamp with time zone": datetime.datetime,
		"number": float,
		"varchar2": str,
		"clob": CLOB,
		"blob": BLOB,
	}

	def __init__(self, name, owner=None, connection=None):
		Object.__init__(self, name, owner, connection)
		self._argsbypos = None
		self._argsbyname = None
		self._returnvalue = None

	def _calcargs(self, cursor):
		if self._argsbypos is None:
			if "." in self.name:
				(package_name, procedure_name) = self.name.split(".")
				cursor.execute("select object_name from {}_procedures where owner=nvl(:owner, user) and object_name=:package_name and procedure_name=:procedure_name".format(cursor.ddprefix()), owner=self.owner, package_name=package_name, procedure_name=procedure_name)
			else:
				package_name = None
				procedure_name = self.name
				cursor.execute("select object_name from {}_procedures where owner=nvl(:owner, user) and object_name=:name and procedure_name is null".format(cursor.ddprefix()), owner=self.owner, name=procedure_name)
			if cursor.fetchone() is None:
				raise SQLObjectNotFoundError(self)
			self._argsbypos = []
			self._argsbyname = {}
			if package_name is not None:
				cursor.execute("select lower(argument_name) as name, lower(in_out) as in_out, lower(data_type) as datatype from {}_arguments where owner=nvl(:owner, user) and package_name=:package_name and object_name=:procedure_name and data_level=0 order by sequence".format(cursor.ddprefixargs()), owner=self.owner, package_name=package_name, procedure_name=procedure_name)
			else:
				cursor.execute("select lower(argument_name) as name, lower(in_out) as in_out, lower(data_type) as datatype from {}_arguments where owner=nvl(:owner, user) and package_name is null and object_name=:procedure_name and data_level=0 order by sequence".format(cursor.ddprefixargs()), owner=self.owner, procedure_name=procedure_name)
			i = 0 # argument position (skip return value)
			for record in cursor:
				arginfo = Argument(record.name, i, record.datatype, "in" in record.in_out, "out" in record.in_out)
				if record.name is None: # this is the return value
					self._returnvalue = arginfo
				else:
					self._argsbypos.append(arginfo)
					self._argsbyname[arginfo.name] = arginfo
					i += 1

	def _getargs(self, cursor, *args, **kwargs):
		queryargs = {}

		if len(args) > len(self._argsbypos):
			raise TypeError("too many parameters for {!r}: {} given, {} expected".format(self, len(args), len(self._argsbypos)))

		# Handle positional arguments
		for (arg, arginfo) in zip(args, self._argsbypos):
			queryargs[arginfo.name] = self._wraparg(cursor, arginfo, arg)

		# Handle keyword arguments
		for (argname, arg) in kwargs.items():
			argname = argname.lower()
			if argname in queryargs:
				raise TypeError("duplicate argument for {!r}: {}".format(self, argname))
			try:
				arginfo = self._argsbyname[argname]
			except KeyError:
				raise TypeError("unknown parameter for {!r}: {}".format(self, argname))
			queryargs[arginfo.name] = self._wraparg(cursor, arginfo, arg)

		# Add out parameters for anything that hasn't been specified
		for arginfo in self._argsbypos:
			if arginfo.name not in queryargs and arginfo.isout:
				queryargs[arginfo.name] = self._wraparg(cursor, arginfo, None)

		return queryargs

	def _wraparg(self, cursor, arginfo, arg):
		try:
			if arg is None:
				t = self._ora2cx[arginfo.datatype]
			else:
				t = type(arg)
		except KeyError:
			raise TypeError("can't handle parameter {} of type {} with value {!r} in {!r}".format(arginfo.name, arginfo.datatype, arg, self))
		if isinstance(arg, bytes): # ``bytes`` is treated as binary data, always wrap it in a ``BLOB``
			t = BLOB
		elif isinstance(arg, str) and len(arg) >= 2000:
			t = CLOB
		var = cursor.var(t)
		var.setvalue(0, arg)
		return var

	def _unwraparg(self, arginfo, cursor, value):
		if isinstance(value, LOB):
			value = _decodelob(value, cursor.readlobs)
		return value

	def _makerecord(self, cursor, args):
		index2name = []
		values = []
		for arginfo in self._argsbypos:
			name = arginfo.name
			if name in args:
				index2name.append(name)
				values.append(self._unwraparg(arginfo, cursor, args[name].getvalue(0)))
		name2index = dict(zip(index2name, itertools.count()))
		return Record(index2name, name2index, values)

	def iterarguments(self):
		"""
		Generator that yields all arguments of the function/procedure :obj:`self`.
		"""
		cursor = self.getcursor()
		self._calcargs(cursor)
		yield from self._argsbypos


class Procedure(Callable):
	"""
	Models a procedure in the database. A :class:`Procedure` object can be
	used as a wrapper for calling the procedure with keyword arguments.
	"""

	type = "procedure"

	def __call__(self, cursor, *args, **kwargs):
		"""
		Call the procedure with arguments :obj:`args` and keyword arguments
		:obj:`kwargs`. :obj:`cursor` must be a :mod:`ll.orasql` cursor. This will
		return a :class:`Record` object containing the result of the call (i.e.
		this record will contain all specified and all out parameters).
		"""
		self._calcargs(cursor)

		if self.owner is None:
			name = self.name
		else:
			name = "{}.{}".format(self.owner, self.name)

		queryargs = self._getargs(cursor, *args, **kwargs)

		query = "begin {}({}); end;".format(name, ", ".join("{0}=>:{0}".format(name) for name in queryargs))

		cursor.execute(query, queryargs)

		return self._makerecord(cursor, queryargs)


class Function(Callable):
	"""
	Models a function in the database. A :class:`Function` object can be
	used as a wrapper for calling the function with keyword arguments.
	"""
	type = "function"

	def __call__(self, cursor, *args, **kwargs):
		"""
		Call the function with arguments :obj:`args` and keyword arguments
		:obj:`kwargs`. :obj:`cursor` must be an :mod:`ll.orasql` cursor.
		This will return a tuple containing the result and a :class:`Record`
		object containing the modified parameters (i.e. this record will contain
		all specified and out parameters).
		"""
		self._calcargs(cursor)

		if self.owner is None:
			name = self.name
		else:
			name = "{}.{}".format(self.owner, self.name)

		queryargs = self._getargs(cursor, *args, **kwargs)

		returnvalue = "r"
		while returnvalue in queryargs:
			returnvalue += "_"
		queryargs[returnvalue] = self._wraparg(cursor, self._returnvalue, None)

		query = "begin :{} := {}({}); end;".format(returnvalue, name, ", ".join("{0}=>:{0}".format(name) for name in queryargs if name != returnvalue))

		cursor.execute(query, queryargs)

		returnvalue = self._unwraparg(self._returnvalue, cursor, queryargs.pop(returnvalue).getvalue(0))

		return (returnvalue, self._makerecord(cursor, queryargs))


class Package(MixinNormalDates, MixinCodeDDL, Object):
	"""
	Models a package in the database.
	"""
	type = "package"


class PackageBody(MixinNormalDates, MixinCodeDDL, Object):
	"""
	Models a package body in the database.
	"""
	type = "package body"


class Type(MixinNormalDates, MixinCodeDDL, Object):
	"""
	Models a type definition in the database.
	"""
	type = "type"


class TypeBody(MixinNormalDates, MixinCodeDDL, Object):
	"""
	Models a type body in the database.
	"""
	type = "type body"


class Trigger(MixinNormalDates, MixinCodeDDL, Object):
	"""
	Models a trigger in the database.
	"""
	type = "trigger"


class JavaSource(MixinNormalDates, Object):
	"""
	Models Java source code in the database.
	"""
	type = "java source"

	def _fetch(self, cursor):
		cursor.execute("select text from {}_source where type='JAVA SOURCE' and owner=nvl(:owner, user) and name=:name order by line".format(cursor.ddprefix()), owner=self.owner, name=self.name)
		code = "\n".join((rec.text or "").rstrip() for rec in cursor)
		if not code:
			self._exists = False
		else:
			self._exists = True
			self._source = code

		code = "\n".join((rec.text or "").rstrip() for rec in cursor)
		code = code.strip()

	def createddl(self, term=True):
		code = self._source.strip()

		code = "create or replace and compile java source named {} as\n{}\n".format(self.getfullname(), code)
		if term:
			code += "/\n"
		return code

	def dropddl(self, term=True):
		code = "drop java source {}".format(self.getfullname())
		if term:
			code += ";\n"
		else:
			code += "\n"
		return code

	def fixname(self, code):
		code = code.split(None, 9)
		code = "create or replace and compile java source named {} {}".format(self.getfullname(), code[9])
		return code


class Privilege:
	"""
	Models a database object privilege (i.e. a grant).

	A :class:`Privilege` object has the following attributes:

		``privilege`` : string
			The type of the privilege (``EXECUTE`` etc.)

		``name`` : string
			The name of the object for which this privilege grants access

		``owner`` : string or :const:`None`
			the owner of the object

		``grantor`` : string or :const:`None`
			Who granted this privilege?

		``grantee`` : string or :const:`None`
			To whom has this privilege been granted?

		``connection`` : :class:`Connection` or :const:`None`
			The database connection
	"""

	type = "privilege"

	def __init__(self, privilege, name, grantor, grantee, owner=None, connection=None):
		self.privilege = privilege
		self.name = name
		self.grantor = grantor
		self.grantee = grantee
		self.owner = owner
		self.connection = connection

	def __repr__(self):
		if self.owner is not None:
			return "{}.{}({!r}, {!r}, {!r}, {!r})".format(self.__class__.__module__, self.__class__.__qualname__, self.privilege, self.name, self.grantee, self.owner)
		else:
			return "{}.{}({!r}, {!r}, {!r})".format(self.__class__.__module__, self.__class__.__qualname__, self.privilege, self.name, self.grantee)

	def __str__(self):
		if self.owner is not None:
			return "{}({!r}, {!r}, {!r}, {!r})".format(self.__class__.__qualname__, self.privilege, self.name, self.grantee, self.owner)
		else:
			return "{}({!r}, {!r}, {!r})".format(self.__class__.__qualname__, self.privilege, self.name, self.grantee)

	@misc.notimplemented
	def _fetch(self, cursor):
		pass

	def generated(self):
		return False

	def refresh(self):
		self._fetch(self.getcursor())

	def fromconnection(self, connection):
		return self.__class__(self.name, self.owner, connection)

	def connect(self, connection):
		self.connection = connection
		self.refresh()

	def getcursor(self):
		if self.connection is None:
			raise NotConnectedError(self)
		return self.connection.cursor()

	@property
	def connectstring(self):
		if self.connection:
			return self.connection.connectstring()
		return None

	@classmethod
	def iterobjects(cls, connection, owner=ALL):
		"""
		Generator that yields object privileges. For the meaning of :obj:`owner`
		see :meth:`Object.iternames`.
		"""
		cursor = connection.cursor() # can't use :meth:`getcursor` as we're in a classmethod

		if owner is None:
			cursor.execute("select null as owner, privilege, table_name as object, decode(grantor, user, null, grantor) as grantor, grantee from user_tab_privs where owner=user order by table_name, privilege")
		elif owner is ALL:
			ddprefix = cursor.ddprefix()
			# The column names in ``ALL_TAB_PRIVS`` and ``DBA_TAB_PRIVS`` are different, so we have to use two different queries
			if ddprefix == "all":
				cursor.execute("select decode(table_schema, user, null, table_schema) as owner, privilege, table_name as object, decode(grantor, user, null, grantor) as grantor, grantee from all_tab_privs order by table_name, privilege")
			else:
				cursor.execute("select decode(owner, user, null, owner) as owner, privilege, table_name as object, decode(grantor, user, null, grantor) as grantor, grantee from dba_tab_privs order by table_name, privilege")
		else:
			cursor.execute("select decode(table_schema, user, null, table_schema) as owner, privilege, table_name as object, decode(grantor, user, null, grantor) as grantor, grantee from {}_tab_privs where table_schema=:owner order by table_schema, table_name, privilege".format(cursor.ddprefix()), owner=owner)
		return (Privilege(rec.privilege, rec.object, rec.grantor, rec.grantee, rec.owner, connection) for rec in cursor)

	def grantddl(self, term=True, mapgrantee=True):
		"""
		Return SQL code to grant this privilege. If :obj:`mapgrantee` is a list
		or a dictionary and ``self.grantee`` is not in this list (or dictionary)
		no command will be returned. If it's a dictionary and ``self.grantee`` is
		in it, the privilege will be granted to the user specified as the value
		instead of the original one. If :obj:`mapgrantee` is true (the default)
		the privilege will be granted to the original grantee.
		"""
		cursor = self.getcursor()
		if mapgrantee is True:
			grantee = self.grantee
		elif isinstance(mapgrantee, (list, tuple)):
			if self.grantee.lower() in (g.lower() for g in mapgrantee):
				grantee = self.grantee
			else:
				grantee = None
		else:
			mapgrantee = {key.lower(): value for (key, value) in mapgrantee.items()}
			grantee = mapgrantee.get(self.grantee.lower(), None)
		if grantee is None:
			return ""
		code = "grant {} on {} to {}".format(self.privilege, self.name, grantee)
		if term:
			code += ";\n"
		return code


class User(Object):
	"""
	Models a user in the database.
	"""

	def __init__(self, name, connection=None):
		super().__init__(name, None, connection)

	def _fetch(self, cursor):
		cursor.execute("select username from {}_users order by username".format(cursor.ddprefix()))
		rec = cursor.fetchone()
		self._exists = rec is not None

	@classmethod
	def iternames(cls, connection):
		"""
		Generator that yields the names of all users in ascending order
		"""
		cursor = connection.cursor()
		cursor.execute("select username from {}_users order by username".format(cursor.ddprefix()))
		return (row.username for row in cursor)

	@classmethod
	def iterobjects(cls, connection):
		"""
		Generator that yields all user objects.
		"""
		return (cls(name[0], connection) for name in cls.iternames(connection))


class Preference(Object):
	"""
	Models a preference in the database.
	"""
	type = "preference"

	def _fetch(self, cursor):
		cursor.execute("select pre_object from ctx_preferences where pre_owner=nvl(:owner, user) and pre_name=:name", owner=self.owner, name=self.name)
		rec = cursor.fetchone()
		if rec is None:
			self._exists = False
		else:
			self._exists = True
			self._pre_object = rec.pre_object
			cursor.execute("select prv_attribute, prv_value from ctx_preference_values where prv_owner=nvl(:owner, user) and prv_preference=:name", owner=self.owner, name=self.name)
			self._prv_values = [(rec.prv_attribute, rec.prv_value) for rec in cursor]

	def createddl(self, term=True):
		name = self.getfullname()
		code = ["begin\n"]
		code.append("\tctx_ddl.create_preference('{}', '{}');\n".format(name.replace("'", "''"), self._pre_object.replace("'", "''")))
		name = self.getfullname().replace("'", "''")
		for (name, value) in self._prv_values:
			code.append("\tctx_ddl.set_attribute('{}', '{}', '{}');\n".format(name, name.replace("'", "''"), value.replace("'", "''")))
		code.append("end;\n")
		code = "".join(code)
		if term:
			code += "/\n"
		return code

	def dropddl(self, term=True):
		name = self.getfullname()
		code = "begin\n\tctx_ddl.drop_preference('{}');\nend;\n".format(name.replace("'", "''"))
		if term:
			code += "/\n"
		return code

	def cdate(self):
		return None

	def udate(self):
		return None

	def iterreferencedby(self):
		# FIXME: Parse the parameters of all domain indexes and output those indexes here that reference us in any of their parameters
		if False:
			yield None

	def iterreferences(self, done=None):
		if False:
			yield None

	@classmethod
	def iternames(cls, connection, owner=ALL):
		"""
		Generator that yields the names of all preferences.
		"""
		cursor = connection.cursor()
		try:
			if owner is None:
				cursor.execute("select null as owner, pre_name from ctx_preferences where pre_owner=user order by pre_name")
			elif owner is ALL:
				cursor.execute("select pre_owner as owner, pre_name from ctx_preferences order by pre_owner, pre_name")
			else:
				cursor.execute("select decode(pre_owner, user, null, pre_owner) as owner, pre_name from ctx_preferences where pre_owner=:owner order by pre_name", owner=owner)
		except DatabaseError as exc:
			if exc.args[0].code == 942: # ORA-00942: table or view does not exist
				return iter(())
			else:
				raise
		else:
			return ((row.pre_name, row.owner) for row in cursor)

	@classmethod
	def iterobjects(cls, connection, owner=ALL):
		"""
		Generator that yields all preferences.
		"""
		return (cls(name[0], name[1], connection) for name in cls.iternames(connection, owner=owner))


###
### Classes that add an ``oracle`` scheme to the urls supported by :mod:`ll.url`.
###

class OracleURLConnection(url_.Connection):
	def __init__(self, context, connection, mode):
		self.dbconnection = connect(connection, mode=mode) if mode is not None else connect(connection)

	def open(self, url, mode="rb", encoding="utf-8", errors="strict"):
		return OracleFileResource(self, url, mode, encoding, errors)

	def close(self):
		self.dbconnection.close()

	def _type(self, url):
		path = url.path
		if path and not path[-1]:
			path = path[:-1]
		lp = len(path)
		if lp == 0:
			return "root"
		elif lp == 1:
			if path[0] == "user":
				return "allusers"
			else:
				return "type"
		elif lp == 2:
			if path[0] == "user":
				return "user"
			else:
				return "object"
		elif lp == 3:
			if path[0] == "user":
				return "usertype"
		elif lp == 4:
			if path[0] == "user":
				return "userobject"
		raise FileNotFoundError(errno.ENOENT, "no such file or directory: {!r}".format(url)) from None

	def _infofromurl(self, url):
		type = self._type(url)
		if type == "root":
			owner = None
			objectype = None
			name = None
		elif type == "allusers":
			owner = None
			objectype = None
			name = None
		elif type == "type":
			owner = None
			objectype = None
			name = None
		elif type == "user":
			owner = url.path[1]
			objectype = None
			name = None
		elif type == "object":
			owner = None
			objectype = url.path[0]
			name = url.path[1]
		elif type == "usertype":
			owner = url.path[1]
			objectype = url.path[2]
			name = None
		else:
			owner = url.path[1]
			objectype = url.path[2]
			name = url.path[3]
		if name is not None:
			if name.lower().endswith(".sql"):
				name = name[:-4]
			name = unicodedata.normalize('NFC', name)
		return (type, owner, objectype, name)

	def _objectfromurl(self, url):
		(type, owner, objecttype, name) = self._infofromurl(url)
		if objecttype not in Object.name2type:
			raise ValueError("don't know how to handle {0!r}".format(url))
		return Object.name2type[objecttype](name, owner, self.dbconnection)

	def isdir(self, url):
		return not self._type(url).endswith("object")

	def isfile(self, url):
		return self._type(url).endswith("object")

	def mimetype(self, url):
		if self.isdir(url):
			return "application/octet-stream"
		return "text/x-oracle-{}".format(url.path[0 if url.path[0] != "user" else 2])

	def owner(self, url):
		if len(url.path) >= 2 and url.path[0] == "user" and url.path[1]:
			return url.path[1]
		else:
			c = self.dbconnection.cursor()
			c.execute("select user from dual")
			return c.fetchone()[0]

	def exists(self, url):
		try:
			type = self._type(url)
		except FileNotFoundError:
			return False
		if type.endswith("object"):
			return self._objectfromurl(url).exists()
		else:
			return True

	def cdate(self, url):
		if self.isdir(url):
			return bigbang
		try:
			obj = self._objectfromurl(url)
		except SQLNoSuchObjectError:
			raise FileNotFoundError(errno.ENOENT, "no such file: {!r}".format(type, url))
		return obj.cdate()

	def mdate(self, url):
		if self.isdir(url):
			return bigbang
		try:
			obj = self._objectfromurl(url)
		except SQLNoSuchObjectError:
			raise FileNotFoundError(errno.ENOENT, "no such file: {!r}".format(type, url))
		return obj.udate()

	def _walk(self, cursor, url):
		def _event(url, event):
			cursor.url = url
			cursor.event = event
			cursor.isdir = event != "file"
			cursor.isfile = not cursor.isdir
			return cursor

		def _dir(childname):
			emitbeforedir = cursor.beforedir
			emitafterdir = cursor.afterdir
			enterdir = cursor.enterdir
			if emitbeforedir or enterdir or emitafterdir:
				childurl = url / childname
			if emitbeforedir:
				yield _event(childurl, "beforedir")
				emitbeforedir = cursor.beforedir
				emitafterdir = cursor.afterdir
				enterdir = cursor.enterdir
				cursor.restore()
			if enterdir:
				yield from self._walk(cursor, childurl)
			if emitafterdir:
				yield _event(childurl, "afterdir")
				cursor.restore()

		absurl = cursor.rooturl / url
		type = self._type(absurl)
		if type == "root": # directory of types for the current user
			for childname in sorted(Object.name2type):
				if childname not in ("comment", "column"):
					yield from _dir("{}/".format(childname))
		elif type == "type": # directory of objects of the specified type for current user
			path = absurl.path
			type = path[0]
			try:
				class_ = Object.name2type[type]
			except KeyError:
				raise FileNotFoundError(errno.ENOENT, "no such file or directory: {!r}".format(url)) from None
			for (name, owner) in class_.iternames(self.dbconnection, None):
				if cursor.file:
					yield _event(url / "{}.sql".format(makeurl(name)), "file")
					cursor.restore()
		elif type == "allusers": # directory of all users
			path = url.path
			for name in User.iternames(self.dbconnection):
				yield from _dir("{}/".format(makeurl(name)))
		elif type == "user": # directory of types for a specific user
			path = absurl.path
			for childname in sorted(Object.name2type):
				if childname not in ("comment", "column"):
					yield from _dir("{}/".format(childname))
		elif type == "usertype": # directory of objects of the specified type for a specific user
			path = absurl.path
			type = path[2]
			try:
				class_ = Object.name2type[type]
			except KeyError:
				raise FileNotFoundError(errno.ENOENT, "no such file or directory: {!r}".format(url)) from None
			for (name, owner) in class_.iternames(self.dbconnection, path[1]):
				if cursor.file:
					yield _event(url / "{}.sql".format(makeurl(name)), "file")
					cursor.restore()
		else:
			raise NotADirectoryError(errno.ENOTDIR, "Not a directory: {}".format(url))

	def walk(self, url, beforedir=True, afterdir=False, file=True, enterdir=True):
		cursor = url_.Cursor(url, beforedir=beforedir, afterdir=afterdir, file=file, enterdir=enterdir)
		return self._walk(cursor, url_.URL())

	def __repr__(self):
		return "<{}.{} to {!r} at {:#x}>".format(self.__class__.__module__, self.__class__.__qualname__, self.connection.connectstring(), id(self))


class OracleFileResource(url_.Resource):
	"""
	An :class:`OracleFileResource` wraps an Oracle database object (like a
	table, view, function, procedure etc.) in a file-like API for use with
	:mod:`ll.url`.
	"""
	def __init__(self, connection, url, mode="r", encoding="utf-8", errors="strict"):
		self.connection = connection
		self.url = url
		self.mode = mode
		self.encoding = encoding
		self.errors = errors
		self.closed = False
		self.name = str(self.url)

		if "w" in self.mode:
			if "b" in self.mode:
				self.stream = io.BytesIO()
			else:
				self.stream = io.StringIO()
		else:
			code = self.connection._objectfromurl(url).createddl(term=False)
			if "b" in self.mode:
				code = code.encode(self.encoding, self.errors)
				self.stream = io.BytesIO(code)
			else:
				self.stream = io.StringIO(code)

	def read(self, size=-1):
		if self.closed:
			raise ValueError("I/O operation on closed file")
		return self.stream.read(size)

	def write(self, data):
		if self.closed:
			raise ValueError("I/O operation on closed file")
		return self.stream.write(data)

	def mimetype(self):
		return self.connection.mimetype(self.url)

	def cdate(self):
		return self.connection.cdate(self.url)

	def mdate(self):
		return self.connection.mdate(self.url)

	def __iter__(self):
		data = self.read()
		return iter(data.splitlines(True))

	def close(self):
		if not self.closed:
			if "w" in self.mode:
				obj = self.connection._objectfromurl(self.url)
				code = self.stream.getvalue()
				if isinstance(code, bytes):
					code = code.decode(self.encoding, self.errors)
				code = obj.fixname(code)
				cursor = self.connection.dbconnection.cursor()
				cursor.execute(code)
			self.stream = None
			self.closed = True


class OracleSchemeDefinition(url_.SchemeDefinition):
	def _connect(self, url, context=None, **kwargs):
		context = url_.getcontext(context)
		# Use one :class:`OracleURLConnection` for each ``user@host`` combination
		server = url.server
		try:
			connections = context.schemes["oracle"]
		except KeyError:
			connections = context.schemes["oracle"] = {}
		try:
			connection = connections[server]
		except KeyError:
			userinfo = url.userinfo.split(":")
			lui = len(userinfo)
			if lui == 2:
				mode = None
			elif lui == 3:
				try:
					mode = dict(sysoper=SYSOPER, sysdba=SYSDBA, normal=None)[userinfo[2]]
				except KeyError:
					raise ValueError("unknown connect mode {!r}".format(userinfo[2]))
			else:
				raise ValueError("illegal userinfo {!r}".format(url.userinfo))
			connection = connections[server] = OracleURLConnection(context, "{}/{}@{}".format(userinfo[0], userinfo[1], url.host), mode)
		return (connection, kwargs)

	def open(self, url, mode="rb", context=None):
		(connection, kwargs) = self._connect(url, context)
		return OracleFileResource(connection, url, mode, **kwargs)

	def closeall(self, context):
		for connection in context.schemes["oracle"].values():
			connection.close()


url_.schemereg["oracle"] = OracleSchemeDefinition("oracle", usehierarchy=True, useserver=True, usefrag=False, islocal=False, isremote=True)
