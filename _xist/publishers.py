#! /usr/bin/env python
# -*- coding: Latin-1 -*-

## Copyright 1999-2002 by LivingLogic AG, Bayreuth, Germany.
## Copyright 1999-2002 by Walter D�rwald
##
## All Rights Reserved
##
## Permission to use, copy, modify, and distribute this software and its documentation
## for any purpose and without fee is hereby granted, provided that the above copyright
## notice appears in all copies and that both that copyright notice and this permission
## notice appear in supporting documentation, and that the name of LivingLogic AG or
## the author not be used in advertising or publicity pertaining to distribution of the
## software without specific, written prior permission.
##
## LIVINGLOGIC AG AND THE AUTHOR DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
## INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL
## LIVINGLOGIC AG OR THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
## DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
## IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR
## IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
<doc:par>This module contains classes that may be used as publishing
handler in <pyref module="ll.xist.xsc" class="Node" method="publish"><method>publish</method></pyref>.</doc:par>
"""

__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$

import sys, codecs, types

from ll import url

import xsc, options, utils, errors, helpers

class Publisher(object):
	"""
	base class for all publishers.
	"""

	def __init__(self, base=None, root=None, encoding=None, xhtml=None, prefixes=None, elementmode=1, procinstmode=0, entitymode=0):
		"""
		<doc:par><arg>base</arg> specifies the url to which the result
		will be output.</doc:par>

		<doc:par><arg>encoding</arg> specifies the encoding to be used.
		The encoding itself (i.e. calling <method>encode</method> on the
		unicode strings) must be done by <pyref method="publish"><method>xist.publishers.Publisher.publish</method></pyref>
		and not by <pyref module="ll.xist.xsc" class="Node"><method>xist.xsc.Node.publish</method></pyref>.</doc:par>

		<doc:par>The only exception is in the case of encodings that can't encode
		the full range of unicode characters like <lit>us-ascii</lit>
		or <lit>iso-8859-1</lit>. In this case non encodable characters will be replaced
		by characters references (if possible, if not (e.g. in comments or processing
		instructions) an exception will be raised) before they are passed to
		<pyref method="publish"><method>publish</method></pyref>.</doc:par>

		<doc:par>With the parameter <arg>xhtml</arg> you can specify if you want &html; output
		(i.e. elements with a content model EMPTY as <markup>&lt;foo&gt;</markup>) with
		<code><arg>xhtml</arg>==0</code>, or XHTML output that is compatible with &html; browsers
		(element with an empty content model as <markup>&lt;foo /&gt;</markup> and others that
		just happen to be empty as <markup>&lt;foo&gt;&lt;/foo&gt;</markup>) with
		<code><arg>xhtml</arg>==1</code> or just plain XHTML with
		<code><arg>xhtml</arg>==2</code> (all empty elements as <markup>&lt;foo/&gt;</markup>).
		When you use the default (<code>None</code>) that value of the global variable
		<code>outputXHTML</code> will be used, which defaults to 1, but can be overwritten
		by the environment variable <code>XSC_OUTPUT_XHTML</code> and can of course be
		changed dynamically.</doc:par>

		<doc:par><arg>prefixes</arg> is and instance of <pyref module="ll.xist.xsc" class="Prefixes"><class>Prefixes</class></pyref>
		and maps <pyref module="ll.xist.xsc" class="Namespace"><class>Namespace</class></pyref>
		objects to prefixes that should be used (or <lit>None</lit>, if no prefix should be used.).
		With <arg>elementmode</arg> you can specify how prefixes for elements should be
		treated:</doc:par>
		<doc:ulist>
		<doc:item><lit>0</lit>: Never publish a prefix;</doc:item>
		<doc:item><lit>1</lit>: Publish prefixes, but do not use <lit>xmlns</lit> attributes;</doc:item>
		<doc:item><lit>2</lit>: Publish prefixes and issue the appropriate <lit>xmlns</lit> attributes.</doc:item>
		</doc:ulist>
		<doc:par><arg>procinstmode</arg> is used for processing instructions
		and <arg>entitymode</arg> for entities.</doc:par>
		"""
		self.base = url.URL(base)
		self.root = url.URL(root)
		if encoding is None:
			encoding = options.outputEncoding
		self.encoding = encoding
		if xhtml is None:
			xhtml = options.outputXHTML
		if xhtml<0 or xhtml>2:
			raise ValueError("xhtml must be 0, 1 or 2, not %r" % (xhtml,))
		self.xhtml = xhtml

		if prefixes is None:
			prefixes = xsc.OldPrefixes()
		self.prefixes = prefixes
		self.elementmode = elementmode
		self.procinstmode = procinstmode
		self.entitymode = entitymode

		self.inAttr = 0
		self.__textFilters = [ helpers.escapeText ]
		self.__currentTextFilter = helpers.escapeText

	def publish(self, text):
		"""
		receives the strings to be printed.
		The strings are still unicode objects, and you have to do the encoding yourself.
		overwrite this method.
		"""
		pass

	def publishText(self, text):
		"""
		<doc:par>is used to publish text data. This uses the current
		text filter, which is responsible for escaping characters.</doc:par>
		"""
		self.publish(self.__currentTextFilter(text, self.encoding))

	def pushTextFilter(self, filter):
		"""
		<doc:par>pushes a new text filter function.</doc:par>
		"""
		self.__textFilters.append(filter)
		self.__currentTextFilter = filter

	def popTextFilter(self):
		self.__textFilters.pop()
		if self.__textFilters:
			self.__currentTextFilter = self.__textFilters[-1]
		else:
			self.__currentTextFilter = None

	def _neededxmlnsdefs(self, node):
		"""
		<doc:par>Return a list of nodes in <arg>node</arg> that
		need a <lit>xmlns</lit> attribute.</doc:par>
		"""
		if isinstance(node, (xsc.Element, xsc.ProcInst, xsc.Entity)):
			if node.needsxmlns(self)==2:
				return [node]
		elif isinstance(node, xsc.Frag):
			nodes = []
			for child in node:
				nodes.extend(self._neededxmlnsdefs(child))
			return nodes
		return []

	def beginPublication(self):
		"""
		<doc:par>called once before the publication of the node <arg>node</arg> begins.</doc:par>
		"""
		# Determine if we have to introduce an artificial root element that gets the xmlns attributes
		if not isinstance(self.node, xsc.Element): # An element is the wrapper itself
			needed = self._neededxmlnsdefs(self.node)
			if needed:
				if len(needed)>1 or not isinstance(needed[0], xsc.Element):
					from xist.ns import specials
					self.node = specials.wrap(self.node)

		prefixes2use = {}
		# collect all the namespaces that are used and their required mode
		for child in self.node.walk(attrs=True):
			if isinstance(child, xsc.Element):
				index = 0
			elif isinstance(child, xsc.ProcInst):
				index = 1
			elif isinstance(child, xsc.Entity):
				index = 2
			else:
				continue
			prefixes2use[(index, child.xmlns)] = max(prefixes2use.get((index, child.xmlns), 0), child.needsxmlns(self))
		self.prefixes2use = {}
		if len(prefixes2use):
			self.publishxmlns = None # signal to the first element that it should generate xmlns attributes
			# get the prefixes for all namespaces from the prefix mapping
			for (index, ns) in prefixes2use:
				nsprefix = [u"xmlns", u"procinstns", u"entityns"][index]
				self.prefixes2use[(nsprefix, ns)] = (prefixes2use[(index, ns)], self.prefixes._prefix4ns(index, ns)[0])

	def endPublication(self):
		"""
		<doc:par>called once after the publication of the node <arg>node</arg> has ended.</doc:par>
		"""
		del self.prefixes2use
		del self.node

	def doPublication(self, node):
		"""
		<doc:par>performs the publication of the node <arg>node</arg>.</doc:par>
		"""
		self.node = node
		self.beginPublication()
		self.node.publish(self) # use self.node, because it might have been replaced by beginPublication
		return self.endPublication()

class FilePublisher(Publisher):
	"""
	writes the strings to a file.
	"""
	def __init__(self, stream, base=None, root=None, encoding=None, xhtml=None, prefixes=None, elementmode=1, procinstmode=0, entitymode=0):
		super(FilePublisher, self).__init__(base=base, root=root, encoding=encoding, xhtml=xhtml, prefixes=prefixes, elementmode=elementmode, procinstmode=procinstmode, entitymode=entitymode)
		(encode, decode, streamReaderClass, streamWriterClass) = codecs.lookup(self.encoding)
		self.stream = streamWriterClass(stream)

	def publish(self, text):
		self.stream.write(text)

	def tell(self):
		"""
		return the current position.
		"""
		return self.stream.tell()

class PrintPublisher(FilePublisher):
	"""
	writes the strings to <code>sys.stdout</code>.
	"""
	def __init__(self, base=None, root=None, encoding=None, xhtml=None, prefixes=None, elementmode=1, procinstmode=0, entitymode=0):
		super(PrintPublisher, self).__init__(sys.stdout, base=base, root=root, encoding=encoding, xhtml=xhtml, prefixes=prefixes, elementmode=elementmode, procinstmode=procinstmode, entitymode=entitymode)

class StringPublisher(Publisher):
	"""
	collects all strings in an array.
	The joined strings are available via
	<pyref module="ll.xist.publishers" class="StringPublisher" method="asString"><method>asString</method></pyref>
	"""

	def __init__(self, base=None, root=None, xhtml=None, prefixes=None, elementmode=1, procinstmode=0, entitymode=0):
		super(StringPublisher, self).__init__(base=base, root=root, encoding="utf16", xhtml=xhtml, prefixes=prefixes, elementmode=elementmode, procinstmode=procinstmode, entitymode=entitymode)

	def publish(self, text):
		self.texts.append(text)

	def beginPublication(self):
		super(StringPublisher, self).beginPublication()
		self.texts = []

	def endPublication(self):
		result = u"".join(self.texts)
		del self.texts
		super(StringPublisher, self).endPublication()
		return result

class BytePublisher(Publisher):
	"""
	collects all strings in an array.
	The joined strings are available via
	<pyref method="asBytes"><method>asBytes</method></pyref> as a byte
	string suitable for writing to a file.
	"""

	def publish(self, text):
		self.texts.append(text)

	def beginPublication(self):
		super(BytePublisher, self).beginPublication()
		self.texts = []

	def endPublication(self):
		result = u"".join(self.texts).encode(self.encoding)
		del self.texts
		super(BytePublisher, self).endPublication()
		return result

