#! /usr/bin/env python

## Copyright 1999-2001 by LivingLogic AG, Bayreuth, Germany.
## Copyright 1999-2001 by Walter D�rwald
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
This file contains everything you need to parse XIST DOMs from files, strings, URLs etc.

It contains different SAX2 parser driver classes. (In fact in contains one one, the
sgmlop driver, everything else is from PyXML) and various classes derived from
xml.sax.xmlreader.InputSource.
"""

import sys, os, os.path, types, cStringIO as StringIO, urllib

from xml import sax
from xml.parsers import sgmlop
from xml.sax import expatreader
from xml.sax import saxlib

#try:
#	import timeoutsocket
#except ImportError:
timeoutsocket = None

import xsc, url as url_, errors, utils

class StringInputSource(sax.xmlreader.InputSource):
	def __init__(self, text):
		sax.xmlreader.InputSource.__init__(self)
		self.setSystemId("STRING")
		if type(text) is types.UnicodeType:
			encoding = "utf-8"
			text = text.encode(encoding)
		else:
			encoding = sys.getdefaultencoding()
		self.setByteStream(StringIO.StringIO(text))
		self.setEncoding(encoding)

class FileInputSource(sax.xmlreader.InputSource):
	def __init__(self, filename):
		sax.xmlreader.InputSource.__init__(self)
		self.setSystemId(filename)
		self.setByteStream(open(os.path.expanduser(filename), "r"))

class URLInputSource(sax.xmlreader.InputSource):
	def __init__(self, url):
		sax.xmlreader.InputSource.__init__(self)
		if isinstance(url, url_.URL):
			url = url.asString()
		self.setSystemId(url)
		if type(url) is types.UnicodeType:
			url = url.encode("utf-8")
		self.setByteStream(urllib.urlopen(url))

	def setTimeout(self, secs):
		if timeoutsocket is not None:
			timeoutsocket.setDefaultSocketTimeout(sec)

	def getTimeout(self):
		if timeoutsocket is not None:
			timeoutsocket.getDefaultSocketTimeout()

class TidyURLInputSource(sax.xmlreader.InputSource):
	def __init__(self, url):
		sax.xmlreader.InputSource.__init__(self)
		self.tidyin = None
		self.tidyout = None
		self.tidyerr = None
		if isinstance(url, url_.URL):
			url = url.asString()
		self.setSystemId(url)
		if type(url) is types.UnicodeType:
			url = url.encode("utf-8")
		try:
			(self.tidyin, self.tidyout, self.tidyerr) = os.popen3("tidy --tidy-mark no --wrap 0 --output-xhtml --numeric-entities yes --show-warnings no --quiet yes -asxml -quiet", "b") # open the pipe to and from tidy
			self.tidyin.write(urllib.urlopen(url).read()) # get the desired file from the url and pipe it to tidy
			self.tidyin.close() # tell tidy, that we're finished
			self.tidyin = None
			self.setByteStream(self.tidyout)
		except:
			if self.tidyin is not None:
				self.tidyin.close()
			if self.tidyout is not None:
				self.tidyout.close()
			if self.tidyerr is not None:
				self.tidyerr.close()
			urllib.urlcleanup() # throw away the temporary filename
			raise

	def close(self):
		if self.tidyin is not None:
			self.tidyin.close()
		if self.tidyout is not None:
			self.tidyout.close()
		if self.tidyerr is not None:
			self.tidyerr.close()
		urllib.urlcleanup()

	def __del__(self):
		self.close()

class SGMLOPParser(sax.xmlreader.IncrementalParser, sax.xmlreader.Locator):
	"""
	This is a rudimentary, buggy, halfworking, untested SAX2 drivers for sgmlop.
	And I didn't even know, what I was doing, but it seems to work.
	"""
	encoding = "latin-1"

	def __init__(self, namespaceHandling=0, bufsize=2**16-20, defaultEncoding="utf-8"):
		sax.xmlreader.IncrementalParser.__init__(self, bufsize)
		self.bufsize = bufsize
		self.defaultEncoding = defaultEncoding
		self.reset()

	def reset(self):
		try:
			self.parser = sgmlop.XMLUnicodeParser()
		except AttributeError:
			self.parser = sgmlop.XMLParser()
		self._parsing = 0
		self.encoding = self.defaultEncoding
		self.source = None
		self.lineNumber = -1

	def feed(self, data):
		if not self._parsing:
			self.content_handler.startDocument()
			self._parsing = 1
		self.parser.feed(data)

	def close(self):
		self.parser.close()
		self.content_handler.endDocument()

	def parse(self, source):
		self.source = source
		file = source.getByteStream()
		self._parsing = 1
		self.content_handler.setDocumentLocator(self)
		self.content_handler.startDocument()
		self.lineNumber = 1
		# nothing done for the column number, because otherwise parsing would be much to slow.

		try:
			while 1:
				data = file.read(self.bufsize)
				if not data:
					break
				while 1:
					pos = data.find("\n")
					if pos==-1:
						break
					self.parser.feed(data[:pos+1])
					data = data[pos+1:]
					self.lineNumber += 1
				self.parser.feed(data)
			self.close()
		except Exception, ex: # FIXME: really catch everything?
			if self.error_handler is not None:
				self.error_handler.fatalError(ex)
			else:
				raise
		self.source = None

	def setErrorHandler(self, handler):
		self.parser.register(self)
		self.error_handler = handler

	def setContentHandler(self, handler):
		self.parser.register(self)
		self.content_handler = handler

	def setDTDHandler(self, handler):
		self.parser.register(self)
		self.dtd_handler = handler

	def setEntityResolver(self, handler):
		self.parser.register(self)
		self.entity_resolver = handler

	# Locator methods will be called by the application
	def getColumnNumber(self):
		return -1

	def getLineNumber(self):
		if self.parser is None:
			return -1
		return self.lineNumber

	def getPublicId(self):
		if self.source is None:
			return None
		return self.source.getPublicId()

	def getSystemId(self):
		if self.source is None:
			return None
		return self.source.getSystemId()

	def handle_comment(self, data):
		self.content_handler.comment(unicode(data, self.encoding))

	# don't define handle_charref or handle_cdata, so we will get those through handle_data

	def handle_data(self, data):
		self.content_handler.characters(unicode(data, self.encoding))

	def handle_proc(self, target, data):
		target = unicode(target, self.encoding)
		data = unicode(data, self.encoding)
		if target!=u'xml': # Don't report <?xml?> as a processing instruction
			self.content_handler.processingInstruction(target, data)
		else: # extract the encoding
			encodingFound = utils.findAttr(data, u"encoding")
			if encodingFound is not None:
				self.encoding = encodingFound

	def handle_entityref(self, name):
		if hasattr(self.content_handler, "entity"):
			self.content_handler.entity(unicode(name, self.encoding))

	def finish_starttag(self, name, attrs):
		newattrs = sax.xmlreader.AttributesImpl(attrs)
		for (attrname, attrvalue) in attrs.items():
			newattrs._attrs[unicode(attrname, self.encoding)] = self.__string2Fragment(unicode(attrvalue, self.encoding))
		self.content_handler.startElement(unicode(name, self.encoding), newattrs)

	def finish_endtag(self, name):
		self.content_handler.endElement(unicode(name, self.encoding))

	def __string2Fragment(self, text):
		"""
		parses a string that might contain entities into a fragment
		with text nodes, entities and character references.
		"""
		if text is None:
			return xsc.Null
		node = xsc.Frag()
		while 1:
			try:
				i = text.index("&")
				if i != 0:
					node.append(text[:i])
					text = text[i:]
				try:
					i = text.index(";")
					if text[1] == "#":
						if text[2] == "x":
							node.append(unichr(int(text[3:i], 16)))
						else:
							node.append(unichr(int(text[2:i])))
					else:
						try:
							node.append(self.content_handler.namespaces.entityFromName(text[1:i])())
						except KeyError:
							raise errors.UnknownEntityError(text[1:i])
					text = text[i+1:]
				except ValueError:
					raise errors.MalformedCharRefError(text)
			except ValueError:
				if len(text):
					node.append(text)
				break
		return node

ExpatParser = expatreader.ExpatParser

class Handler:
	"""
	contains the parser and the options and functions for handling XML files
	"""

	def __init__(self, parser=None, namespaces=None):
		if parser is None:
			parser = SGMLOPParser()
		self.parser = parser

		if namespaces is None:
			namespaces = xsc.defaultNamespaces
		self.namespaces = namespaces

		parser.setErrorHandler(self)
		parser.setContentHandler(self)
		parser.setDTDHandler(self)
		parser.setEntityResolver(self)

	def parse(self, source):
		self.source = source
		self.parser.parse(source)

	def setDocumentLocator(self, locator):
		self._locator = locator

	def startDocument(self):
		# our nodes do not have a parent link, therefore we have to store the active
		# path through the tree in a stack (which we call nesting, because stack is
		# already used by the base class (there is no base class anymore, but who cares))

		# after we've finished parsing, the Frag that we put at the bottom of the stack will be our document root
		self.__nesting = [ xsc.Frag() ]

	def endDocument(self):
		self.root = self.__nesting[0]
		self.__nesting = None

	def startElement(self, name, attrs):
		node = self.namespaces.elementFromName(name)()
		for name in attrs.keys():
			node[name] = attrs[name]
			if isinstance(node[name], xsc.URLAttr):
				base = url_.URL("*/") + url_.URL(self.source.getSystemId())
				node[name].base = base
		self.__appendNode(node)
		self.__nesting.append(node) # push new innermost element onto the stack

	def endElement(self, name):
		element = self.namespaces.elementFromName(name)
		currentelement = self.__nesting[-1].__class__
		if element != currentelement:
			raise errors.ElementNestingError(currentelement, element)
		self.__nesting[-1].endLoc = self.getLocation()
		self.__nesting.pop() # pop the innermost element off the stack

	def characters(self, content):
		if content:
			last = self.__nesting[-1]
			if len(last) and isinstance(last[-1], xsc.Text):
				last[-1]._content += content # join consecutive Text nodes (this violates the "immutable Text restriction", but there is only one reference to the Text object)
			else:
				self.__appendNode(xsc.Text(content))

	def comment(self, content):
		self.__appendNode(xsc.Comment(content))

	def processingInstruction(self, target, data):
		self.__appendNode(self.namespaces.procInstFromName(target)(data))

	def entity(self, name):
		node = self.namespaces.entityFromName(name)()
		if isinstance(node, xsc.CharRef):
			self.characters(unichr(node.codepoint))
		else:
			self.__appendNode(node)

	def __decorateException(self, exception):
		if not isinstance(exception, saxlib.SAXParseException):
			exception = saxlib.SAXParseException("%s: %s" % (exception.__class__.__name__, exception), exception, self._locator)
		return exception

	def error(self, exception):
		"Handle a recoverable error."
		raise self.__decorateException(exception)

	def fatalError(self, exception):
		"Handle a non-recoverable error."
		raise self.__decorateException(exception)

	def warning(self, exception):
		"Handle a warning."
		print self.__decorateException(exception)

	def getLocation(self):
		return xsc.Location(self._locator)

	def __appendNode(self, node):
		node.startLoc = self.getLocation()
		self.__nesting[-1].append(node) # add the new node to the content of the innermost element (or fragment)

def parse(source, parser=None, namespaces=None):
	handler = Handler(parser, namespaces)
	handler.parse(source)
	return handler.root

def parseString(text, parser=None, namespaces=None):
	return parse(StringInputSource(text), parser, namespaces)

def parseFile(filename, namespaces=None, parser=None):
	return parse(FileInputSource(filename), parser, namespaces)

def parseURL(url, namespaces=None, parser=None):
	return parse(URLInputSource(url), parser, namespaces)

def parseTidyURL(url, namespaces=None, parser=None):
	source = TidyURLInputSource(url)
	result = parse(source, parser, namespaces)
	source.close()
	return result

