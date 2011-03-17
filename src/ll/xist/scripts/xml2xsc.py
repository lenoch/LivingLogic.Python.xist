#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Copyright 1999-2011 by LivingLogic AG, Bayreuth/Germany
## Copyright 1999-2011 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/__init__.py for the license


import sys, argparse, cStringIO

from ll import misc, url
from ll.xist import xsc, xnd, sims


__docformat__ = "reStructuredText"


def iterpath(node):
	yield [node]
	if hasattr(node, "text") and node.text:
		yield [node, node.text]
	if hasattr(node, "getchildren"):
		for child in node:
			for path in iterpath(child):
				yield [node] + path
	if hasattr(node, "tail") and node.tail:
		yield [node, node.tail]


def getelementname(node):
	xmlns = None
	name = node.tag
	if name.startswith("{"):
		(xmlns, sep, name) = name[1:].partition("}")
	return (name, xmlns)


def addetree2xnd(ns, node, elements):
	# Iterate through the tree and collect which elements are encountered and how they are nested
	for path in iterpath(node):
		node = path[-1]
		if "Element" in type(node).__name__:
			(name, xmlns) = getelementname(node)
			if (name, xmlns) in ns.elements:
				xndnode = ns.elements[(name, xmlns)]
			else:
				xndnode = xnd.Element(name, xmlns=xmlns)
				ns += xndnode
				elements[(name, xmlns)] = set()
			for attrname in node.keys():
				if not attrname.startswith("{") and attrname not in xndnode.attrs:
					xndnode += xnd.Attr(attrname, type=xsc.TextAttr)
		elif "ProcessingInstruction" in type(node).__name__:
			name = node.target
			if name not in ns.procinsts:
				ns += xnd.ProcInst(name)
		elif "Comment" in type(node).__name__:
			xndnode = "#comment"
		elif isinstance(node, basestring):
			if node.isspace():
				xndnode = "#whitespace"
			else:
				xndnode = "#text"
		if len(path) >= 2:
			parent = path[-2]
			if "Element" in type(parent).__name__:
				parententry = elements[getelementname(parent)]
				parententry.add(xndnode)


def makexnd(urls, parser="etree", shareattrs="dupes", model="simple", defaultxmlns=None):
	elements = {} # maps (name, xmlns) to content set
	ns = xnd.Module(defaultxmlns=defaultxmlns)
	with url.Context():
		for u in urls:
			if isinstance(u, url.URL):
				u = u.openread()
			elif isinstance(u, str):
				u = cStringIO.StringIO(u)
			if parser == "etree":
				from xml.etree import cElementTree
				node = cElementTree.parse(u).getroot()
			elif parser == "lxml":
				from lxml import etree
				node = etree.parse(u).getroot()
			else:
				raise ValueError("unknown parser {!r}".format(parser))
			addetree2xnd(ns, node, elements)

	# Put sims info into the element definitions
	if model == "none":
		pass
	elif model == "simple":
		for (fullname, modelset) in elements.iteritems():
			ns.elements[fullname].modeltype = bool(modelset)
	elif model in ("fullall", "fullonce"):
		for (fullname, modelset) in elements.iteritems():
			element = ns.elements[fullname]
			if not modelset:
				element.modeltype = "sims.Empty"
			else:
				elements = [el for el in modelset if isinstance(el, xnd.Element)]
				if not elements:
					if "#text" in modelset:
						element.modeltype = "sims.NoElements"
					else:
						element.modeltype = "sims.NoElementsOrText"
				else:
					if "#text" in modelset:
						element.modeltype = "sims.ElementsOrText"
					else:
						element.modeltype = "sims.Elements"
					element.modelargs = elements
	else:
		raise ValueError("unknown sims mode {!r}".format(model))

	if shareattrs=="dupes":
		ns.shareattrs(False)
	elif shareattrs=="all":
		ns.shareattrs(True)
	return ns


def main(args=None):
	p = argparse.ArgumentParser(description="Convert XML files to XIST namespace (on stdout)")
	p.add_argument("urls", metavar="urls", type=url.URL, help="ULRs of DTDs to be parsed", nargs="+")
	p.add_argument("-p", "--parser", dest="parser", help="parser module to use for XML parsing (default: %(default)s)", choices=("etree", "lxml"), default="etree")
	p.add_argument("-s", "--shareattrs", dest="shareattrs", help="Should identical attributes be shared among elements? (default: %(default)s)", choices=("none", "dupes", "all"), default="dupes")
	p.add_argument("-m", "--model", dest="model", help="Create sims info? (default: %(default)s)", choices=("none", "simple", "fullall", "fullonce"), default="simple")
	p.add_argument("-x", "--defaultxmlns", dest="defaultxmlns", metavar="NAME", help="Force elements without a namespace into this namespace")

	args = p.parse_args(args)
	print makexnd(**args.__dict__)


if __name__ == "__main__":
	sys.exit(main())
