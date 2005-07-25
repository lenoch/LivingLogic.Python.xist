#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

## Copyright 1999-2005 by LivingLogic AG, Bayreuth/Germany.
## Copyright 1999-2005 by Walter D�rwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license


"""
This module contains classes that are used for dumping elements
to the terminal.
"""


__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$

import sys, os, keyword

import ll
from ll import ansistyle, url

import xsc, options


def getenvint(name, default):
	try:
		return int(os.environ[name], 0)
	except KeyError:
		return default


def getenvcolors(name, default1, default2):
	if options.repransi == 1:
		return getenvint(name, default1)
	elif options.repransi == 2:
		return getenvint(name, default2)
	else:
		return -1


# ANSI escape sequence to be used for tabs
color4tab = getenvcolors("LL_XIST_REPRANSI_TAB", 0040, 0100)


# ANSI escape sequence to be used for quotes (delimiters for text and attribute nodes)
color4quote = getenvcolors("LL_XIST_REPRANSI_QUOTE", 0030, 0170)


color4slash = getenvcolors("LL_XIST_REPRANSI_SLASH", 0030, 0170)


# ANSI escape sequence to be used for brackets
color4bracket = getenvcolors("LL_XIST_REPRANSI_BRACKET", 0030, 0170)


# ANSI escape sequence to be used for colon (i.e. namespace separator)
color4colon = getenvcolors("LL_XIST_REPRANSI_COLON", 0030, 0170)


# ANSI escape sequence to be used for question marks (delimiters for processing instructions)
color4question = getenvcolors("LL_XIST_REPRANSI_QUESTION", 0030, 0170)


# ANSI escape sequence to be used for exclamation marks (used in comments and doctypes)
color4exclamation = getenvcolors("LL_XIST_REPRANSI_EXCLAMATION", 0030, 0170)


# ANSI escape sequence to be used for & (used in entity)
color4amp = getenvcolors("LL_XIST_REPRANSI_AMP", 0030, 0170)


# ANSI escape sequence to be used for semicolons (used in entities)
color4semi = getenvcolors("LL_XIST_REPRANSI_SEMI", 0030, 0170)


# ANSI escape sequence to be used for text
color4text = getenvcolors("LL_XIST_REPRANSI_TEXT", 0070, 0070)


# ANSI escape sequence to be used for namespaces
color4namespace = getenvcolors("LL_XIST_REPRANSI_NAMESPACE", 0170, 0040)


# ANSI escape sequence to be used for element names
color4elementname = getenvcolors("LL_XIST_REPRANSI_ELEMENTNAME", 0160, 0140)


# ANSI escape sequence to be used for attribute names
color4attrname = getenvcolors("LL_XIST_REPRANSI_ATTRNAME", 0170, 0140)


# ANSI escape sequence to be used for attrs class name
color4attrsname = getenvcolors("LL_XIST_REPRANSI_ATTRSNAME", 0160, 0140)


# ANSI escape sequence to be used for entity names
color4entityname = getenvcolors("LL_XIST_REPRANSI_ENTITYNAME", 0050, 0050)


# ANSI escape sequence to be used for document types marker (i.e. !DOCTYPE)
color4doctypemarker = getenvcolors("LL_XIST_REPRANSI_DOCTYPEMARKER", 0170, 0170)


# ANSI escape sequence to be used for document types
color4doctypetext = getenvcolors("LL_XIST_REPRANSI_DOCTYPETEXT", 0170, 0170)


# ANSI escape sequence to be used for comment markers (i.e. --)
color4commentmarker = getenvcolors("LL_XIST_REPRANSI_COMMENTMARKER", 0170, 0170)


# ANSI escape sequence to be used for comment text
color4commenttext = getenvcolors("LL_XIST_REPRANSI_COMMENTTEXT", 0100, 0100)


# ANSI escape sequence to be used for attribute values
color4attrvalue = getenvcolors("LL_XIST_REPRANSI_ATTRVALUE", 0020, 0060)


# ANSI escape sequence to be used for URLs
color4url = getenvcolors("LL_XIST_REPRANSI_URL", 0130, 0020)


# ANSI escape sequence to be used for processing instruction targets
color4procinsttarget = getenvcolors("LL_XIST_REPRANSI_PROCINSTTARGET", 0110, 0110)


# ANSI escape sequence to be used for processing instruction content
color4procinstcontent = getenvcolors("LL_XIST_REPRANSI_PROCINSTCONTENT", 0070, 0070)


# ANSI escape sequence to be used for numbers in error messages etc.
color4number = getenvcolors("LL_XIST_REPRANSI_NUMBER", 0040, 0040)


# ANSI escape sequence to be used for variable strings in error messages etc.
color4string = getenvcolors("LL_XIST_REPRANSI_STRING", 0050, 005)


class EscInlineText(ansistyle.EscapedText):
	ascharref = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f<>&"
	ascolor   = "\x09\x0a"

	def __init__(self, *content):
		ansistyle.EscapedText.__init__(self, -1, *content)

	def escapechar(self, char):
		if char in self.ascolor:
			return ansistyle.Text(color4tab, char)
		else:
			ascharref = char in self.ascharref
			if not ascharref:
				try:
					char.encode(options.reprencoding)
				except:
					ascharref = True
			if ascharref:
				charcode = ord(char)
				try:
					entity = xsc.defaultPrefixes.charref(charcode)
				except LookupError:
					return ansistyle.Text(color4entityname, "&#", str(charcode), ";")
				else:
					return ansistyle.Text(color4entityname, "&", entity.xmlname, ";")
		return char


class EscInlineAttr(EscInlineText):
	ascharref = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f<>\"&"
	ascolor   = "\x09\x0a"


class EscOutlineText(EscInlineText):
	ascharref = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f<>&"
	ascolor   = ""


class EscOutlineAttr(EscInlineText):
	ascharref = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f<>\"&"
	ascolor   = ""


def strBracketOpen():
	return ansistyle.Text(color4bracket, "<")


def strBracketClose():
	return ansistyle.Text(color4bracket, ">")


def strAmp():
	return ansistyle.Text(color4amp, "&")


def strSemi():
	return ansistyle.Text(color4semi, ";")


def strSlash():
	return ansistyle.Text(color4slash, "/")


def strColon():
	return ansistyle.Text(color4colon, ":")


def strQuestion():
	return ansistyle.Text(color4question, "?")


def strExclamation():
	return ansistyle.Text(color4exclamation, "!")


def strQuote():
	return ansistyle.Text(color4quote, '"')


def strTab(count):
	return ansistyle.Text(color4tab, options.reprtab*count)


def strNumber(number):
	return ansistyle.Text(color4number, str(number))


def strString(string):
	return ansistyle.Text(color4string, string)


def strURL(u):
	if isinstance(u, url.URL):
		u = u.url
	return ansistyle.Text(color4url, EscInlineText(u))


def strDocTypeMarker():
	return ansistyle.Text(color4doctypemarker, "DOCTYPE")


def strDocTypeText(text):
	return ansistyle.Text(color4doctypetext, EscInlineText(text))


def strCommentMarker():
	return ansistyle.Text(color4commentmarker, "--")


def strCommentText(text):
	return ansistyle.Text(color4commenttext, EscInlineText(text))


def strNamespace(namespace):
	return ansistyle.Text(color4namespace, EscInlineText(namespace))


def strElementName(name):
	return ansistyle.Text(color4elementname, EscInlineText(name))


def strAttrName(name):
	return ansistyle.Text(color4attrname, EscInlineText(name))


def strAttrsName(name):
	return ansistyle.Text(color4attrsname, EscInlineText(name))


def strEntityName(name):
	return ansistyle.Text(color4entityname, EscInlineText(name))


def strProcInstTarget(target):
	return ansistyle.Text(color4procinsttarget, EscInlineText(target))


def strProcInstContent(content):
	return ansistyle.Text(color4procinstcontent, EscInlineText(content))


def strTextOutsideAttr(text):
	return ansistyle.Text(color4text, EscInlineText(text))


def strTextInAttr(text):
	return ansistyle.Text(color4attrvalue, EscInlineAttr(text))


def strAttrValue(attrvalue):
	return ansistyle.Text(color4attrvalue, EscInlineAttr(attrvalue))


class Presenter(object):
	"""
	<par>This class is the base of the presenter classes. It is abstract
	and only serves as documentation for the methods.</par>
	<par>A <class>Presenter</class> generates a specific
	string representation of a node to be printed on the screen.</par>
	"""

	def present(self, node):
		"""
		<par>create a string presentation for <arg>node</arg> and an iterator the resulting string
		fragments.</par>
		"""
		for part in node.present(self):
			yield part

	
	@ll.notimplemented
	def presentText(self, node):
		"""
		<par>present a <pyref module="ll.xist.xsc" class="Text"><class>Text</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentFrag(self, node):
		"""
		<par>present a <pyref module="ll.xist.xsc" class="Frag"><class>Frag</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentComment(self, node):
		"""
		<par>present a <pyref module="ll.xist.xsc" class="Comment"><class>Comment</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentDocType(self, node):
		"""
		<par>present a <pyref module="ll.xist.xsc" class="DocType"><class>DocType</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentProcInst(self, node):
		"""
		<par>present a <pyref module="ll.xist.xsc" class="ProcInst"><class>ProcInst</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentAttrs(self, node):
		"""
		<par>present an <pyref module="ll.xist.xsc" class="Attrs"><class>Attrs</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentElement(self, node):
		"""
		<par>present an <pyref module="ll.xist.xsc" class="Element"><class>Element</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentEntity(self, node):
		"""
		<par>present a <pyref module="ll.xist.xsc" class="Entity"><class>Entity</class></pyref> node.</par>
		"""

	@ll.notimplemented
	def presentNull(self, node):
		"""
		<par>present the <class>Null</class> node.</par>
		"""

	@ll.notimplemented
	def presentAttr(self, node):
		"""
		<par>present an <pyref module="ll.xist.xsc" class="Attr"><class>Attr</class></pyref> node.</par>
		"""


class PlainPresenter(Presenter):
	"""
	<par>This presenter shows only the root node of the tree (with a little additional
	information about the number of nested nodes). It is used as the default presenter
	in <pyref module="ll.xist.xsc" class="Node" method="__repr__"><method>Node.__repr__</method></pyref>.</par>
	"""
	def __init__(self, maxlen=60):
		self.maxlen = maxlen

	def presentCharacterData(self, node):
		content = node.content
		if len(content)>self.maxlen:
			content = content[:self.maxlen/2] + u"..." + content[-self.maxlen/2:]
		yield "<%s:%s object content=%r at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), content, id(node))

	presentText = presentCharacterData

	def presentFrag(self, node):
		l = len(node)
		if l==0:
			info = "with no children"
		elif l==1:
			info = "with 1 child"
		else:
			info = "with %d children" % l
		yield "<%s:%s object %s at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), info, id(node))

	def presentAttr(self, node):
		l = len(node)
		if l==0:
			info = "with no children"
		elif l==1:
			info = "with 1 child"
		else:
			info = "with %d children" % l
		yield "<%s:%s attr object %s at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), info, id(node))

	presentComment = presentCharacterData
	presentDocType = presentCharacterData
	def presentProcInst(self, node):
		content = node.content
		if len(content)>self.maxlen:
			content = content[:self.maxlen/2] + u"..." + content[-self.maxlen/2:]
		yield "<%s:%s procinst object content=%r at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), content, id(node))

	def presentAttrs(self, node):
		l = len(node)
		if l==0:
			info = "with no attributes"
		elif l==1:
			info = "with 1 attribute"
		else:
			info = "with %d attributes" % l
		yield "<%s:%s attrs object %s at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), info, id(node))

	def presentElement(self, node):
		lc = len(node.content)
		if lc==0:
			infoc = "with no children"
		elif lc==1:
			infoc = "with 1 child"
		else:
			infoc = "with %d children" % lc
		la = len(node.attrs)
		if la==0:
			infoa = "and no attributes"
		elif la==1:
			infoa = "and 1 attribute"
		else:
			infoa = "and %d attributes" % la
		yield "<%s:%s element object %s %s at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), infoc, infoa, id(node))

	def presentEntity(self, node):
		yield "<%s:%s entity object at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), id(node))

	def presentNull(self, node):
		yield "<%s:%s object at 0x%x>" % (node.__class__.__module__, node.__class__.__fullname__(), id(node))


class NormalPresenter(Presenter):
	def present(self, node):
		self.buffer = ansistyle.Colorizer()
		self.inattr = 0
		for part in node.present(self):
			yield part
		for part in self.buffer.feed(None):
			yield part
		yield "\n"
		self.buffer = None

	def presentText(self, node):
		if self.inattr:
			s = strTextInAttr(node.content)
		else:
			s = strTextOutsideAttr(node.content)
		return self.buffer.feed(s) # return a generator-iterator

	def presentFrag(self, node):
		for child in node:
			for part in child.present(self):
				yield part

	def presentComment(self, node):
		for part in self.buffer.feed(
			strBracketOpen(),
			strExclamation(),
			strCommentMarker(),
			strCommentText(node.content),
			strCommentMarker(),
			strBracketClose()
		):
			yield part

	def presentDocType(self, node):
		for part in self.buffer.feed(
			strBracketOpen(),
			strExclamation(),
			strDocTypeMarker(),
			" ",
			strDocTypeText(node.content),
			strBracketClose()
		):
			yield part

	def presentProcInst(self, node):
		for part in self.buffer.feed(
			strBracketOpen(),
			strQuestion(),
			node._str(fullname=1, xml=0, decorate=0),
			" ",
			strProcInstContent(node.content),
			strQuestion(),
			strBracketClose()
		):
			yield part

	def presentAttrs(self, node):
		self.inattr += 1
		for (attrname, attrvalue) in node.items():
			for part in self.buffer.feed(" "):
				yield part
			if isinstance(attrname, tuple):
				s = attrvalue._str(fullname=0, xml=0, decorate=0)
			else:
				s = strAttrName(attrname)
			for part in self.buffer.feed(s, "=", strQuote()):
				yield part
			for part in attrvalue.present(self):
				yield part
			for part in self.buffer.feed(strQuote()):
				yield part
		self.inattr -= 1

	def presentElement(self, node):
		if node.model and node.model.empty:
			for part in self.buffer.feed(strBracketOpen(), node._str(fullname=1, xml=0, decorate=0)):
				yield part
			for part in node.attrs.present(self):
				yield part
			for part in self.buffer.feed(strSlash(), strBracketClose()):
				yield part
		else:
			for part in self.buffer.feed(strBracketOpen(), node._str(fullname=1, xml=0, decorate=0)):
				yield part
			for part in node.attrs.present(self):
				yield part
			for part in self.buffer.feed(strBracketClose()):
				yield part
			for child in node:
				for part in child.present(self):
					yield part
			for part in self.buffer.feed(strBracketOpen(), strSlash(), node._str(fullname=1, xml=0, decorate=0), strBracketClose()):
				yield part

	def presentEntity(self, node):
		for part in self.buffer.feed(node._str(fullname=1, xml=0, decorate=1)):
			yield part

	def presentNull(self, node):
		for part in self.buffer.feed(node._str(fullname=1, xml=0, decorate=0)):
			yield part

	def presentAttr(self, node):
		for part in xsc.Frag.present(node, self):
			yield part


class TreePresenter(Presenter):
	"""
	This presenter shows the object as a nested tree.
	"""
	def __init__(self, showlocation=True, showpath=1):
		"""
		<par>Create a <class>TreePresenter</class> instance. Arguments have the
		following meaning:</par>
		<dlist>
		<term><arg>showlocation</arg></term><item>Should the location of the
		node (i.e. system id, line and column number) be displayed as the first
		column? (default <lit>True</lit>).</item>
		<term><arg>showpath</arg></term><item><par>This specifies if and how
		the path (i.e. the position of the node in the tree) should be displayed.
		Possible values are:</par>
		<ulist>
		<item><lit>0</lit>: Don't show a path.</item>
		<item><lit>1</lit>: Show a path (e.g. as <lit>0/2/3</lit>,
		i.e. this node is the 4th child of the 3rd child of the 1st child of the
		root node). This is the default.</item>
		<item><lit>2</lit>: Show a path as a usable Python
		expression (e.g. as <lit>[0,2,3]</lit>).</item>
		</ulist>
		</item>
		</dlist>
		"""
		self.showlocation = showlocation
		self.showpath = showpath

	def present(self, node):
		self._inattr = 0
		self._lines = [] # the final lines consisting of (location, numerical path, nesting, content)
		self._currentpath = [] # numerical path
		self._buffers = [] # list of ansistyle.Text objects used for formatting attributes (this is a list for elements that contains elements in their attributes)

		try:
			node.present(self)
	
			lenloc = 0
			lennumpath = 0
			for line in self._lines:
				if self.showpath:
					newline1 = []
					if self.showpath == 1:
						for comp in line[1]:
							if isinstance(comp, tuple):
								newline1.append("%s:%s" % (comp[0].xmlname, comp[1]))
							else:
								newline1.append(str(comp))
						line[1] = "/".join(newline1)
					else:
						for comp in line[1]:
							if isinstance(comp, tuple):
								newline1.append("(%s,%r)" % (comp[0].xmlname, comp[1]))
							else:
								newline1.append(repr(comp))
						line[1] = "[%s]" % ",".join(newline1)
				line[3] = ansistyle.Text(strTab(line[2]), line[3])
				if self.showlocation:
					if line[0] is not None:
						line[0] = str(line[0])
						lenloc = max(lenloc, len(line[0]))
					else:
						line[0] = str(xsc.Location())
				lennumpath = max(lennumpath, len(line[1]))
			newlines = []
			for line in self._lines:
				if self.showlocation:
					newlines.append("%-*s " % (lenloc, line[0]))
				if self.showpath:
					newlines.append("%-*s " % (lennumpath, line[1]))
				newlines.append("%s\n" % line[3])
		finally:
			del self._inattr
			del self._lines
			del self._buffers
			del self._currentpath
		return "".join(newlines)

	def _domultiline(self, node, lines, indent, formatter, head=None, tail=None):
		loc = node.startloc
		nest = len(self._currentpath)
		l = len(lines)
		for i in xrange(max(1, l)):
			if loc is not None:
				hereloc = loc.offset(i)
			else:
				hereloc = None
			mynest = nest
			if i<len(lines):
				s = lines[i]
			else:
				s = ""
			if isinstance(s, basestring):
				if indent:
					while len(s) and s[0] == "\t":
						mynest += 1
						s = s[1:]
			s = formatter(s)
			if i == 0 and head is not None:
				s.insert(0, head)
			if i >= l-1 and tail is not None:
				s.append(tail)
			self._lines.append([hereloc, self._currentpath[:], mynest, s])

	def strTextLineOutsideAttr(self, text):
		return ansistyle.Text(strQuote(), ansistyle.Text(color4text, EscOutlineText(text)), strQuote())

	def strTextInAttr(self, text):
		return ansistyle.Text(color4attrvalue, EscOutlineAttr(text))

	def strProcInstContentLine(self, text):
		return ansistyle.Text(color4procinstcontent, EscOutlineText(text))

	def strCommentTextLine(self, text):
		return ansistyle.Text(color4commenttext, EscOutlineText(text))

	def strDocTypeTextLine(self, text):
		return ansistyle.Text(color4doctypetext, EscOutlineText(text))

	def presentFrag(self, node):
		if self._inattr:
			for child in node:
				child.present(self)
		else:
			if len(node):
				self._lines.append([node.startloc, self._currentpath[:], len(self._currentpath), ansistyle.Text(strBracketOpen(), node._str(fullname=1, xml=0, decorate=0), strBracketClose())])
				self._currentpath.append(0)
				for child in node:
					child.present(self)
					self._currentpath[-1] += 1
				del self._currentpath[-1]
				self._lines.append([node.endloc, self._currentpath[:], len(self._currentpath), ansistyle.Text(strBracketOpen(), strSlash(), node._str(fullname=1, xml=0, decorate=0), strBracketClose())])
			else:
				self._lines.append([node.startloc, self._currentpath[:], len(self._currentpath), ansistyle.Text(strBracketOpen(), node._str(fullname=1, xml=0, decorate=0), strSlash(), strBracketClose())])

	def presentAttrs(self, node):
		if self._inattr:
			for (attrname, attrvalue) in node.items():
				self._buffers[-1].append(" ")
				if isinstance(attrname, tuple):
					self._buffers[-1].append(strNamespace(attrname[0].xmlname), strColon(), strAttrName(attrname[1]))
				else:
					self._buffers[-1].append(strAttrName(attrname))
				self._buffers[-1].append("=", strQuote())
				attrvalue.present(self)
				self._buffers[-1].append(strQuote())
		else:
			s = ansistyle.Text(strBracketOpen(), node._str(fullname=1, xml=0, decorate=0), strBracketClose())
			self._lines.append([node.startloc, self._currentpath[:], len(self._currentpath), s])
			self._currentpath.append(None)
			for (attrname, attrvalue) in node.items():
				self._currentpath[-1] = attrname
				attrvalue.present(self)
			self._currentpath.pop()
			s = ansistyle.Text(strBracketOpen(), strSlash(), node._str(fullname=1, xml=0, decorate=0), strBracketClose())
			self._lines.append([node.endloc, self._currentpath[:], len(self._currentpath), s])

	def presentElement(self, node):
		if self._inattr:
			self._buffers[-1].append(strBracketOpen(), node._str(fullname=1, xml=0, decorate=0))
			self._inattr += 1
			node.attrs.present(self)
			self._inattr -= 1
			if len(node):
				self._buffers[-1].append(strBracketClose())
				node.content.present(self)
				self._buffers[-1].append(strBracketOpen(), strSlash(), node._str(fullname=1, xml=0, decorate=0), strBracketClose())
			else:
				self._buffers[-1].append(strSlash(), strBracketClose())
		else:
			self._buffers.append(ansistyle.Text(strBracketOpen(), node._str(fullname=1, xml=0, decorate=0)))
			self._inattr += 1
			node.attrs.present(self)
			self._inattr -= 1
			if len(node):
				self._buffers[-1].append(strBracketClose())
				self._lines.append([node.startloc, self._currentpath[:], len(self._currentpath), ansistyle.Text(*self._buffers)])
				self._buffers = [] # we're done with the buffers for the header
				self._currentpath.append(0)
				for child in node:
					child.present(self)
					self._currentpath[-1] += 1
				self._currentpath.pop()
				self._lines.append([node.endloc, self._currentpath[:], len(self._currentpath), ansistyle.Text(strBracketOpen(), strSlash(), node._str(fullname=1, xml=0, decorate=0), strBracketClose())])
			else:
				self._buffers[-1].append(strSlash(), strBracketClose())
				self._lines.append([node.startloc, self._currentpath[:], len(self._currentpath), ansistyle.Text(*self._buffers)])
				self._buffers = [] # we're done with the buffers for the header

	def presentNull(self, node):
		if not self._inattr:
			self._lines.append([node.startloc, self._currentpath[:], len(self._currentpath), node._str(fullname=1, xml=0, decorate=1)])

	def presentText(self, node):
		if self._inattr:
			self._buffers[-1].append(strTextInAttr(node.content))
		else:
			lines = node.content.splitlines(1)
			self._domultiline(node, lines, 0, self.strTextLineOutsideAttr)

	def presentEntity(self, node):
		if self._inattr:
			self._buffers[-1].append(node._str(fullname=1, xml=0, decorate=1))
		else:
			self._lines.append([node.startloc, self._currentpath[:], len(self._currentpath), node._str(fullname=1, xml=0, decorate=1)])

	def presentProcInst(self, node):
		if self._inattr:
			self._buffers[-1].append(
				strBracketOpen(),
				strQuestion(),
				node._str(fullname=1, xml=0, decorate=0),
				" ",
				ansistyle.Text(color4procinstcontent, EscOutlineAttr(node.content)),
				strQuestion(),
				strBracketClose()
			)
		else:
			head = ansistyle.Text(strBracketOpen(), strQuestion(), node._str(fullname=1, xml=0, decorate=0), " ")
			tail = ansistyle.Text(strQuestion(), strBracketClose())
			lines = node.content.splitlines()
			if len(lines)>1:
				lines.insert(0, "")
			self._domultiline(node, lines, 1, self.strProcInstContentLine, head, tail)

	def presentComment(self, node):
		if self._inattr:
			self._buffers[-1].append(
				strBracketOpen(),
				strExclamation(),
				strCommentMarker(),
				EnvTextForCommentText(EscOutlineAttr(node.content)),
				strCommentMarker(),
				strBracketClose()
			)
		else:
			head = ansistyle.Text(strBracketOpen(), strExclamation(), strCommentMarker())
			tail = ansistyle.Text(strCommentMarker(), strBracketClose())
			lines = node.content.splitlines()
			self._domultiline(node, lines, 1, self.strCommentTextLine, head, tail)

	def presentDocType(self, node):
		if self._inattr:
			self._buffers[-1].append(
				strBracketOpen(),
				strExclamation(),
				strDocTypeMarker(),
				" ",
				EnvTextForDocTypeText(EscOutlineAttr(node.content)),
				strBracketClose()
			)
		else:
			head = ansistyle.Text(strBracketOpen(), strExclamation(), strDocTypeMarker(), " ")
			tail = ansistyle.Text(strBracketClose())
			lines = node.content.splitlines()
			self._domultiline(node, lines, 1, self.strDocTypeTextLine, head, tail)

	def presentAttr(self, node):
		if self._inattr:
			# this will not be popped at the and of this method, because presentElement needs it
			self._buffers.append(ansistyle.Text(color4attrvalue))
		self.presentFrag(node)


class CodePresenter(Presenter):
	"""
	<par>This presenter formats the object as a nested Python object tree.</par>
	
	<par>This makes it possible to quickly convert &html;/&xml; files to &xist;
	constructor calls.</par>
	"""
	def present(self, node):
		self._inattr = 0
		self._first = True
		self._level = 0
		for part in node.present(self):
			if part:
				yield part
		del self._level
		del self._first
		del self._inattr

	def _indent(self):
		s = ""
		if not self._inattr:
			if not self._first:
				s = "\n"
			if self._level:
				s += "\t"*self._level
		self._first = False
		return s

	def _text(self, text):
		try:
			s = text.encode("us-ascii")
		except UnicodeError:
			s = text
		try:
			i = int(s)
		except ValueError:
			pass
		else:
			if str(i) == s:
				s = i
		return s

	def presentFrag(self, node):
		yield self._indent()
		if not self._inattr:
			yield "%s.%s" % (node.__module__, node.__fullname__())
		yield "("
		if len(node):
			i = 0
			self._level += 1
			for child in node:
				if i:
					yield ","
					if self._inattr:
						yield " "
				for part in child.present(self):
					yield part
				i += 1
			self._level -= 1
			yield self._indent()
		yield ")"

	def presentAttrs(self, node):
		yield self._indent()
		yield "{"
		self._level += 1
		i = 0
		for (attrname, attrvalue) in node.iteritems():
			if i:
				yield ","
				if self._inattr:
					yield " "
			yield self._indent()
			self._inattr += 1
			if isinstance(attrname, tuple):
				ns = attrname[0].__module__
				attrname = attrname[1]
				if keyword.iskeyword(attrname):
					attrname += "_"
				yield "(%s, %r): " % (ns, attrname)
			else:
				if keyword.iskeyword(attrname):
					attrname += "_"
				yield "%r: " % attrname
			if len(attrvalue)==1: # optimize away the tuple ()
				for part in attrvalue[0].present(self):
					yield part
			else:
				for part in attrvalue.present(self):
					yield part
			yield self._indent()
			self._inattr -= 1
			i += 1
		self._level -= 1
		yield self._indent()
		yield "}"

	def presentElement(self, node):
		yield self._indent()
		yield "%s.%s(" % (node.__module__, node.__class__.__fullname__())
		if len(node.content) or len(node.attrs):
			i = 0
			self._level += 1
			for child in node:
				if i:
					yield ","
					if self._inattr:
						yield " "
				for part in child.present(self):
					yield part
				i += 1
			globalattrs = {}
			for (attrname, attrvalue) in node.attrs.iteritems():
				if isinstance(attrname, tuple):
					globalattrs[attrname] = attrvalue
			if len(globalattrs):
				for (attrname, attrvalue) in globalattrs.iteritems():
					if i:
						yield ", "
						if self._inattr:
							yield " "
					yield self._indent()
					yield "{ "
					self._inattr += 1
					ns = attrname[0].__module__
					attrname = attrname[1]
					yield "(%s, %r): " % (ns, attrname)
					if len(attrvalue)==1: # optimize away the tuple ()
						for part in attrvalue[0].present(self):
							yield part
					else:
						for part in attrvalue.present(self):
							yield part
					self._inattr -= 1
					yield " }"
					i += 1
			for (attrname, attrvalue) in node.attrs.iteritems():
				if not isinstance(attrname, tuple):
					if i:
						yield ","
						if self._inattr:
							yield " "
					yield self._indent()
					self._inattr += 1
					yield "%s=" % attrname
					if len(attrvalue)==1: # optimize away the tuple ()
						for part in attrvalue[0].present(self):
							yield part
					else:
						for part in attrvalue.present(self):
							yield part
					self._inattr -= 1
					i += 1
			self._level -= 1
			yield self._indent()
		yield ")"

	def presentNull(self, node):
		pass

	def presentText(self, node):
		yield self._indent()
		yield "%r" % self._text(node.content)

	def presentEntity(self, node):
		yield self._indent()
		yield "%s.%s()" % (node.__module__, node.__class__.__fullname__())

	def presentProcInst(self, node):
		yield self._indent()
		yield "%s.%s(%r)" % (node.__module__, node.__class__.__fullname__(), self._text(node.content))

	def presentComment(self, node):
		yield self._indent()
		yield "xsc.Comment(%r)" % self._text(node.content)

	def presentDocType(self, node):
		yield self._indent()
		yield "xsc.DocType(%r)" % self._text(node.content)

	def presentAttr(self, node):
		return self.presentFrag(node)


defaultpresenter = PlainPresenter() # used for __repr__
hookpresenter = TreePresenter() # used in the displayhook below


def displayhook(obj):
	if isinstance(obj, xsc.Node):
		for part in obj.repr(hookpresenter):
			sys.stdout.write(part)
		return True
	return False
