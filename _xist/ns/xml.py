#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

## Copyright 1999-2005 by LivingLogic AG, Bayreuth/Germany.
## Copyright 1999-2005 by Walter D�rwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license

"""
<par>Contains the global attributes for the &xml; namespace (like <lit>xml:lang</lit>),
and classes for the &xml; declaration.</par>
"""

__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$

from ll.xist import xsc, utils, sims


class XML(xsc.ProcInst):
	"""
	&xml; declaration. The encoding will be automatically set when publishing.
	"""
	xmlname = "xml"

	def publish(self, publisher):
		content = self.content
		encodingfound = utils.findattr(content, u"encoding")
		versionfound = utils.findattr(content, u"version")
		standalonefound = utils.findattr(content, u"standalone")
		if publisher.encoding != encodingfound: # if self has the wrong encoding specification (or none) we construct a new XML ProcInst and publish that (this doesn't lead to infinite recursion, because the next call will skip it)
			node = XML(u"version='%s' encoding='%s'" % (versionfound, publisher.encoding))
			if standalonefound is not None:
				node += u" standalone='%s'" % standalonefound
			return node.publish(publisher) # return a generator
		return xsc.ProcInst.publish(self, publisher) # return a generator


class XML10(XML):
	"""
	&xml; declaration with <lit>version="1.0"</lit>.
	"""
	xmlname = "xml10"
	register = False # don't register this ProcInst, because it will never be parsed from a file, this is just a convenience class

	def __init__(self):
		super(XML10, self).__init__(u'version="1.0"')


class XMLStyleSheet(xsc.ProcInst):
	"""
	XML stylesheet declaration.
	"""
	xmlname = "xml-stylesheet"


class declaration(xsc.Element):
	"""
	<par>The &xml; declaration as an element. This makes it possible to generate
	a declaration from within an &xml; file.
	"""
	model = sims.Empty()

	def convert(self, converter):
		node = XML10()
		return node.convert(converter)


class __ns__(xsc.Namespace):
	xmlname = "xml"
	xmlurl = "http://www.w3.org/XML/1998/namespace"

	class Attrs(xsc.Namespace.Attrs):
		class space(xsc.TextAttr):
			xmlprefix = "xml"
			needsxmlns = 1
			values = (u"default", u"preserve")
		class lang(xsc.TextAttr):
			xmlprefix = "xml"
			needsxmlns = 1
		class base(xsc.URLAttr):
			xmlprefix = "xml"
			needsxmlns = 1
__ns__.makemod(vars())
