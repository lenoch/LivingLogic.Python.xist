# -*- coding: utf-8 -*-

## Copyright 1999-2010 by LivingLogic AG, Bayreuth/Germany
## Copyright 1999-2010 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/__init__.py for the license


"""
This module contains presenter classes, which are used for displaying XIST
nodes on screen (either on the terminal or via :mod:`ipipe` browsers).
"""


__docformat__ = "reStructuredText"


import sys, os, keyword, codecs

# IPython/ipipe support
try:
	import ipipe
	table = ipipe.Table
except ImportError:
	table = object

from ll import misc, url

import xsc


__docformat__ = "reStructuredText"


###
### Colors for output
###

try:
	import astyle
except ImportError:
	from ll import astyle


# style to be used for tabs
s4tab = astyle.Style.fromenv("LL_XIST_STYLE_TAB", "blue:black")


# style to be used for quotes (delimiters for text and attribute nodes)
s4quote = astyle.Style.fromenv("LL_XIST_STYLE_QUOTE", "white:black:bold")


# style to be used for text
s4text = astyle.Style.fromenv("LL_XIST_STYLE_TEXT", "white:black")


# style to be used for namespaces
s4ns = astyle.Style.fromenv("LL_XIST_STYLE_NAMESPACE", "magenta:black")


# style to be used for Null object
s4null = astyle.Style.fromenv("LL_XIST_STYLE_NULL", "red:black")


# style to be used for Null name
s4nullname = astyle.Style.fromenv("LL_XIST_STYLE_NULLNAME", "red:black")


# style to be used a Frag object
s4frag = astyle.Style.fromenv("LL_XIST_STYLE_FRAG", "yellow:black")


# style to be used for Frag name
s4fragname = astyle.Style.fromenv("LL_XIST_STYLE_FRAGNAME", "yellow:black")


# style to be used for elements (i.e. the <, > and / characters
s4element = astyle.Style.fromenv("LL_XIST_STYLE_ELEMENT", "yellow:black")


# style to be used for element names
s4elementname = astyle.Style.fromenv("LL_XIST_STYLE_ELEMENTNAME", "yellow:black")


# style to be used for processing instructions
s4procinst = astyle.Style.fromenv("LL_XIST_STYLE_PROCINST", "magenta:black")


# style to be used for processing instruction targets
s4procinsttarget = astyle.Style.fromenv("LL_XIST_STYLE_PROCINSTTARGET", "magenta:black:bold")


# style to be used for processing instruction content
s4procinstcontent = astyle.Style.fromenv("LL_XIST_STYLE_PROCINSTCONTENT", "white:black")


# style to be used for attributes (i.e. the quotes around their value)
s4attr = astyle.Style.fromenv("LL_XIST_STYLE_ATTR", "yellow:black")


# style to be used for attribute names
s4attrname = astyle.Style.fromenv("LL_XIST_STYLE_ATTRNAME", "cyan:black")


# style to be used for attrs class name
s4attrs = astyle.Style.fromenv("LL_XIST_STYLE_ATTRS", "yellow:black")


# style to be used for attrs class name
s4attrsname = astyle.Style.fromenv("LL_XIST_STYLE_ATTRSNAME", "yellow:black:bold")


# style to be used for entities
s4entity = astyle.Style.fromenv("LL_XIST_STYLE_ENTITY", "magenta:black")


# style to be used for entity names
s4entityname = astyle.Style.fromenv("LL_XIST_STYLE_ENTITYNAME", "magenta:black:bold")


# style to be used for charref names or codepoints
s4charrefname = astyle.Style.fromenv("LL_XIST_STYLE_CHARREFNAME", "magenta:black")


# style to be used for document types
s4doctype = astyle.Style.fromenv("LL_XIST_STYLE_DOCTYPE", "white:black:bold")


# style to be used for document types
s4doctypetext = astyle.Style.fromenv("LL_XIST_STYLE_DOCTYPETEXT", "white:black:bold")


# style to be used for comment (i.e. <!-- and -->)
s4comment = astyle.Style.fromenv("LL_XIST_STYLE_COMMENT", "blue:black")


# style to be used for comment text
s4commenttext = astyle.Style.fromenv("LL_XIST_STYLE_COMMENTTEXT", "blue:black")


# style to be used for attribute values
s4attrvalue = astyle.Style.fromenv("LL_XIST_STYLE_ATTRVALUE", "green:black")


# style to be used for URLs
s4url = astyle.Style.fromenv("LL_XIST_STYLE_URL", "green:black")


# style to be used for numbers in error messages etc.
s4number = astyle.Style.fromenv("LL_XIST_STYLE_NUMBER", "blue:black")


# style to be used for variable strings in error messages etc.
s4string = astyle.Style.fromenv("LL_XIST_STYLE_STRING", "magenta:black")


# style to be used for IDs in repr()
s4id = astyle.Style.fromenv("LL_XIST_STYLE_ID", "yellow:black")


# specifies how to represent an indentation in the DOM tree
reprtab = os.environ.get("LL_XIST_REPR_TAB", u"  ")


def strtab(count):
	return s4tab(unicode(reprtab)*count)


def strtext(text):
	return s4text(s4quote(u'"'), text, s4quote(u'"'))


class Presenter(table):
	"""
	This class is the base of the presenter classes. It is abstract and only
	serves as documentation for the methods.

	A :class:`Presenter` generates a specific string representation of a node
	to be printed on the screen.
	"""

	def __init__(self, node):
		self.node = node

	@misc.notimplemented
	def presentText(self, node):
		"""
		Present a :class:`ll.xist.xsc.Text` node.
		"""

	@misc.notimplemented
	def presentFrag(self, node):
		"""
		Present a :class:`ll.xist.xsc.Frag` node.
		"""

	@misc.notimplemented
	def presentComment(self, node):
		"""
		Present a :class:`ll.xist.xsc.Comment` node.
		"""

	@misc.notimplemented
	def presentDocType(self, node):
		"""
		Present a :class:`ll.xist.xsc.DocType` node.
		"""

	@misc.notimplemented
	def presentProcInst(self, node):
		"""
		Present a :class:`ll.xist.xsc.ProcInst` node.
		"""

	@misc.notimplemented
	def presentAttrs(self, node):
		"""
		Present an :class:`ll.xist.xsc.Attrs` node.
		"""

	@misc.notimplemented
	def presentElement(self, node):
		"""
		Present an :class:`ll.xist.xsc.Element` node.
		"""

	@misc.notimplemented
	def presentEntity(self, node):
		"""
		Present a :class:`ll.xist.xsc.Entity` node.
		"""

	@misc.notimplemented
	def presentNull(self, node):
		"""
		Present the :data:`ll.xist.xsc.Null` node.
		"""

	@misc.notimplemented
	def presentAttr(self, node):
		"""
		Present an :class:`ll.xist.xsc.Attr` node.
		"""


class Line(object):
	__slots__ = ("node", "loc", "path", "content")

	def __init__(self, node, loc, path, content):
		self.node = node
		self.loc = loc
		self.path = path
		self.content = content

	def __iter__(self):
		return iter(defaultpresenter(self.node))

	def __xattrs__(self, mode="default"):
		if mode == "detail":
			return ("node", "loc", "path", "content")
		return ("loc", "path", "content")


class TreePresenter(Presenter):
	"""
	This presenter shows the object as a nested tree.
	"""

	# When inside attributes the presenting methods yield astyle.Text objects
	# Outside of attributes Line objects are yielded

	def __init__(self, node, indent=None):
		"""
		Create a :class:`TreePresenter` object for the XIST node :var:`node` using
		:var:`indent` for indenting each tree level. If :var:`indent` is
		:const:`None` use the value of the environment variable ``LL_XIST_INDENT``
		as the indent string (falling back to a tab if the environment variable
		doesn't exist).
		"""
		Presenter.__init__(self, node)
		if indent is None:
			indent = os.environ.get("LL_XIST_INDENT", "\t")
		self.indent = indent

	def __str__(self):
		return "\n".join(str(line.content) for line in self)

	def strindent(self, level):
		indent = self.indent
		if indent == "\t":
			indent = "   "
		return s4tab(level*indent)

	def text(self, text):
		return repr(text)[2:-1]

	def __iter__(self):
		self._inattr = 0
		self._path = [] # numerical path

		for line in self.node.present(self):
			yield line

		del self._inattr
		del self._path

	def _domultiline(self, node, lines, indent, formatter, head=None, tail=None):
		loc = node.startloc
		nest = len(self._path)
		l = len(lines)
		for i in xrange(max(1, l)): # at least one line
			if loc is not None:
				hereloc = loc.offset(i)
			else:
				hereloc = None
			mynest = nest
			if i<len(lines):
				s = lines[i]
			else:
				s = u""
			if indent:
				oldlen = len(s)
				s = s.lstrip(u"\t")
				mynest += len(s)-oldlen
			s = formatter(self.text(s))
			if i == 0 and head is not None: # prepend head to first line
				s = head + s
			if i >= l-1 and tail is not None: # append tail to last line
				s = s + tail
			yield Line(node, hereloc, self._path[:], self.strindent(mynest) + s)

	def presentFrag(self, node):
		if self._inattr:
			for child in node:
				for text in child.present(self):
					yield text
		else:
			indent = self.strindent(len(self._path))
			ns = s4ns(node.__class__.__module__)
			name = s4fragname(node.__fullname__)
			if len(node):
				yield Line(
					node,
					node.startloc,
					self._path[:],
					s4frag(indent, "<", ns, ":", name, ">"),
				)
				self._path.append(0)
				for child in node:
					for line in child.present(self):
						yield line
					self._path[-1] += 1
				self._path.pop(-1)
				yield Line(
					node,
					node.endloc,
					self._path[:],
					s4frag(indent, "</", ns, ":", name, ">"),
				)
			else:
				yield Line(
					node,
					node.startloc,
					self._path[:],
					s4frag(indent, "<", ns, ":", name, "/>"),
				)

	def presentAttrs(self, node):
		if self._inattr:
			for (attrclass, attrvalue) in node.iteritems():
				yield " "
				if attrclass.xmlns is not None:
					yield s4attr(s4ns(self.text(unicode(attrclass.__module__))), ":", s4attrname(self.text(unicode(attrclass.__fullname__))))
				else:
					yield s4attrname(self.text(unicode(attrclass.__name__)))
				yield s4attr('="')
				for text in attrvalue.present(self):
					yield text
				yield s4attr('"')
		else:
			indent = self.strindent(len(self._path))
			ns = s4ns(node.__class__.__module__)
			name = s4attrsname(node.__fullname__)
			yield Line(
				node,
				node.startloc,
				self._path[:],
				s4attrs(indent, "<", ns, ":", name, ">"),
			)
			self._path.append(None)
			for (attrclass, attrvalue) in node.iteritems():
				self._path[-1] = attrclass
				for line in attrvalue.present(self):
					yield line
			self._path.pop()
			yield Line(
				node,
				node.endloc,
				self._path[:],
				s4attrs(indent, "</", ns, ":", name, ">"),
			)

	def presentElement(self, node):
		ns = s4ns(node.__class__.__module__)
		name = s4elementname(node.__fullname__)
		if self._inattr:
			yield s4element("<", ns, ":", name)
			self._inattr += 1
			for text in node.attrs.present(self):
				yield text
			self._inattr -= 1
			if len(node):
				yield s4element(">")
				for text in node.content.present(self):
					yield text
				yield s4element("</", ns, ":", name, ">")
			else:
				yield s4element("/>")
		else:
			firstline = s4element("<", ns, ":", name)
			indent = self.strindent(len(self._path))

			self._inattr += 1
			for text in node.attrs.present(self):
				firstline.append(text)
			self._inattr -= 1
			if len(node):
				firstline.append(s4element(">"))
				yield Line(
					node,
					node.startloc,
					self._path[:],
					indent + firstline,
				)
				self._path.append(0)
				for child in node:
					for line in child.present(self):
						yield line
					self._path[-1] += 1
				self._path.pop()
				yield Line(
					node,
					node.endloc,
					self._path[:],
					s4element(indent, "</", ns, ":", name, ">"),
				)
			else:
				firstline.append(s4element("/>"))
				yield Line(
					node,
					node.startloc,
					self._path[:],
					indent + firstline,
				)

	def presentNull(self, node):
		if not self._inattr:
			indent = self.strindent(len(self._path))
			ns = s4ns(node.__class__.__module__)
			name = s4nullname(node.__fullname__)
			yield Line(
				node,
				node.startloc,
				self._path[:],
				s4null(indent, "<", ns, ":", name, "/>"),
			)

	def presentText(self, node):
		if self._inattr:
			yield s4attrvalue(self.text(node.content))
		else:
			lines = node.content.splitlines(True)
			for line in self._domultiline(node, lines, 0, strtext):
				yield line

	def presentEntity(self, node):
		ns = s4ns(node.__class__.__module__)
		name = s4entityname(node.__fullname__)
		if self._inattr:
			yield s4entity("&", ns, ":", name, ";")
		else:
			indent = self.strindent(len(self._path))
			yield Line(
				node,
				node.startloc,
				self._path[:],
				s4entity(indent, "&", ns, ":", name, ";"),
			)

	def presentProcInst(self, node):
		ns = s4ns(node.__class__.__module__)
		name = s4procinsttarget(node.__fullname__)
		if self._inattr:
			yield s4procinst("<?", ns, ":", name, " ", s4procinstcontent(self.text(node.content)), "?>")
		else:
			head = s4procinst("<?", ns, ":", name, " ")
			tail = s4procinst("?>")
			lines = node.content.splitlines()
			if len(lines)>1:
				lines.insert(0, "")
			for line in self._domultiline(node, lines, 1, s4procinstcontent, head, tail):
				yield line

	def presentComment(self, node):
		if self._inattr:
			yield s4comment("<!--", s4commenttext(self.text(node.content)), "-->")
		else:
			head = s4comment("<!--")
			tail = s4comment("-->")
			lines = node.content.splitlines()
			for line in self._domultiline(node, lines, 1, s4commenttext, head, tail):
				yield line

	def presentDocType(self, node):
		if self._inattr:
			yield s4doctype("<!DOCTYPE ", s4doctypetext(self.text(node.content)), ">")
		else:
			head = s4doctype("<!DOCTYPE ")
			tail = s4doctype(">")
			lines = node.content.splitlines()
			for line in self._domultiline(node, lines, 1, s4doctypetext, head, tail):
				yield line

	def presentAttr(self, node):
		return self.presentFrag(node)


class CodePresenter(Presenter):
	"""
	This presenter formats the object as a nested Python object tree.

	This makes it possible to quickly convert HTML/XML files to XIST constructor
	calls.
	"""
	def __init__(self, node, indent=None):
		"""
		Create a :class:`CodePresenter` object for the XIST node :var:`node` using
		:var:`indent` for indenting each tree level. If :var:`indent` is
		:const:`None` use the value of the environment variable ``LL_XIST_INDENT``
		as the indent string (falling back to a tab if the environment variable
		doesn't exist).
		"""
		Presenter.__init__(self, node)
		if indent is None:
			indent = os.environ.get("LL_XIST_INDENT", "\t")
		self.indent = indent

	def __str__(self):
		return "\n".join(str(line.content) for line in self)

	def __iter__(self):
		self._inattr = 0
		self._level = 0
		self._path = []
		for line in self.node.present(self):
			yield line
		del self._path
		del self._level
		del self._inattr

	def _indent(self):
		if self._inattr:
			return ""
		else:
			indent = self.indent
			if indent == "\t":
				indent = "   "
			return s4tab(self.indent*self._level)

	def _text(self, text):
		# Find the simplest object to display
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
		name = s4frag(s4ns(node.__class__.__module__), ".", s4fragname(node.__fullname__))
		if len(node):
			if not self._inattr: # skip "(" for attributes, they will be added by presentElement()
				yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "("))
			self._level += 1
			self._path.append(0)
			for (i, child) in enumerate(node):
				if i==len(node)-1:
					for line in child.present(self):
						yield line
				else:
					lines = list(child.present(self))
					for (j, line) in enumerate(lines):
						if j==len(lines)-1:
							line.content += ","
						yield line
				self._path[-1] += 1
			self._level -= 1
			self._path.pop()
			if not self._inattr:
				yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), ")"))
		else:
			if not self._inattr:
				yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "()"))

	def _formatattrvalue(self, attrvalue):
		attrtext = astyle.Text()
		if len(attrvalue)==1: # optimize away the tuple ()
			for part in attrvalue[0].present(self):
				if attrtext:
					attrtext.append(" ")
				attrtext.append(part.content)
		else:
			for part in attrvalue.present(self):
				if attrtext:
					attrtext.append(" ")
				else:
					attrtext.append("(")
				attrtext.append(part.content)
			attrtext.append(")")
		return attrtext

	def presentAttrs(self, node):
		name = s4attrs(s4ns(node.__class__.__module__), ".", s4attrsname(node.__fullname__))
		if len(node):
			globalattrs = {}
			localattrs = {}
			for (attrclass, attrvalue) in node.iteritems():
				if attrclass.xmlns is not None:
					globalattrs[attrclass] = attrvalue
				else:
					localattrs[attrclass] = attrvalue

			yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "("))
			self._level += 1
			if globalattrs:
				yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), "{"))
				for (i, (attrclass, attrvalue)) in enumerate(globalattrs.iteritems()):
					self._path.append(attrclass)
					attrname = astyle.style_default(s4ns(attrclass.__module__), ".", s4attrname(attrclass.__fullname__))
					self._inattr += 1
					attrtext = self._formatattrvalue(attrvalue)
					self._inattr -= 1
					self._level += 1
					line = astyle.style_default(self._indent(), attrname, ": ", s4attrvalue(attrtext))
					if i != len(globalattrs) or not localattrs:
						line += ","
					yield Line(attrvalue, attrvalue.startloc, self._path[:], line)
					self._path.pop()
					self._level -= 1
				line = astyle.style_default(self._indent(), "}")
				if localattrs:
					line += ","
				yield Line(node, node.startloc, self._path[:], line)
			for (i, (attrclass, attrvalue)) in enumerate(localattrs.iteritems()):
				self._path.append(attrclass.__name__)
				self._inattr += 1
				attrtext = self._formatattrvalue(attrvalue)
				self._inattr -= 1
				line = astyle.style_default(self._indent(), s4attrname(attrclass.__name__), "=", s4attrvalue(attrtext))
				if i != len(localattrs)-1:
					line += ","
				yield Line(attrvalue, attrvalue.startloc, self._path[:], line)
				self._path.pop()
			self._level -= 1
			yield Line(node, node.endloc, self._path[:], astyle.style_default(self._indent(), ")"))
		else:
			yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "()"))

	def presentElement(self, node):
		name = s4element(s4ns(node.__class__.__module__), ".", s4elementname(node.__fullname__))
		if len(node.content) or len(node.attrs):
			yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "("))
			self._level += 1
			self._path.append(0)
			for (i, child) in enumerate(node):
				if i==len(node)-1 and not node.attrs:
					for line in child.present(self):
						yield line
				else:
					lines = list(child.present(self))
					for (j, line) in enumerate(lines):
						if j == len(lines)-1:
							line.content += ","
						yield line
				self._path[-1] += 1
			self._path.pop()

			globalattrs = {}
			localattrs = {}
			for (attrclass, attrvalue) in node.attrs.iteritems():
				if attrclass.xmlns is not None:
					globalattrs[attrclass] = attrvalue
				else:
					localattrs[attrclass] = attrvalue

			if globalattrs:
				yield Line(node.attrs, node.attrs.startloc, self._path[:], astyle.style_default(self._indent(), "{"))
				for (i, (attrclass, attrvalue)) in enumerate(globalattrs.iteritems()):
					self._path.append(attrclass)
					attrname = astyle.style_default(s4ns(attrclass.__module__), ".", s4attrname(attrclass.__fullname__))
					self._inattr += 1
					attrtext = self._formatattrvalue(attrvalue)
					self._inattr -= 1
					self._level += 1
					line = astyle.style_default(self._indent(), attrname, ": ", s4attrvalue(attrtext))
					if i != len(globalattrs) or not localattrs:
						line += ","
					yield Line(attrvalue, attrvalue.startloc, self._path[:], line)
					self._path.pop()
					self._level -= 1
				line = astyle.style_default(self._indent(), "}")
				if localattrs:
					line += ","
				yield Line(node.attrs, node.attrs.startloc, self._path[:], line)
			for (i, (attrclass, attrvalue)) in enumerate(localattrs.iteritems()):
				self._inattr += 1
				attrtext = self._formatattrvalue(attrvalue)
				self._inattr -= 1
				line = astyle.style_default(self._indent(), s4attrname(attrclass.__name__), "=", s4attrvalue(attrtext))
				if i != len(localattrs)-1:
					line += ","
				self._path.append(attrclass.__name__)
				yield Line(attrvalue, attrvalue.startloc, self._path[:], line)
				self._path.pop()
			self._level -= 1
			yield Line(node, node.endloc, self._path[:], astyle.style_default(self._indent(), ")"))
		else:
			yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "()"))

	def presentNull(self, node):
		name = s4null(s4ns(node.__class__.__module__), ".", s4nullname(node.__fullname__))
		yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name))

	def presentText(self, node):
		if self._inattr:
			formatter = s4attrvalue
		else:
			formatter = s4text
		yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), formatter(repr(self._text(node.content)))))

	def presentEntity(self, node):
		name = s4entity(s4ns(node.__class__.__module__), ".", s4entityname(node.__fullname__))
		yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "()"))

	def presentProcInst(self, node):
		name = s4procinst(s4ns(node.__class__.__module__), ".", s4procinsttarget(node.__fullname__))
		yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "(", s4procinstcontent(repr(self._text(node.content))), ")"))

	def presentComment(self, node):
		name = s4comment(s4ns(node.__class__.__module__), ".", node.__fullname__)
		yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "(", s4commenttext(repr(self._text(node.content))), ")"))

	def presentDocType(self, node):
		name = s4doctype(s4ns(node.__class__.__module__), ".", node.__fullname__)
		yield Line(node, node.startloc, self._path[:], astyle.style_default(self._indent(), name, "(", s4doctypetext(repr(self._text(node.content))), ")"))

	def presentAttr(self, node):
		return self.presentFrag(node)


# used by the IPython displayhook below (set to :const:`None` to disable)
defaultpresenter = TreePresenter

try:
	from IPython import ipapi, generics
	import ipipe
except Exception:
	pass
else:
	if hasattr(ipipe, "display_tableobject"):
		@generics.result_display.when_type(xsc.Node)
		def displayhook(obj):
			if defaultpresenter is not None:
				return ipipe.display_tableobject(defaultpresenter(obj))
			raise ipapi.TryNext
	else:
		@generics.result_display.when_type(xsc.Node)
		def displayhook(obj):
			if defaultpresenter is not None:
				return ipipe.displayhook(None, defaultpresenter(obj))
			raise ipapi.TryNext