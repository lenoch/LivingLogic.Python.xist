#! /usr/bin/env/python
# -*- coding: utf-8 -*-

## Copyright 1999-2012 by LivingLogic AG, Bayreuth/Germany
## Copyright 1999-2012 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/xist/__init__.py for the license

import pytest

from ll.xist import xsc, xfind
from ll.xist.ns import html, xml

import xist_common as common


def test_walk_coverage():
	node = common.createfrag()

	# call only for code coverage
	for c in node.walk(entercontent=True, enterattrs=True, enterattr=True, startelementnode=True, endelementnode=True, startattrnode=True, endattrnode=True):
		pass


def dowalk(*args, **kwargs):
	node = html.div(
		html.tr(
			html.th("gurk"),
			html.td("hurz"),
			id=html.b(42)
		),
		class_=html.i("hinz")
	)

	def path2str(path):
		return ".".join("#" if isinstance(node, xsc.Text) else node.xmlname for node in path)

	return [path2str(s) for s in node.walkpaths(*args, **kwargs)]


def test_walk_result():
	# Elements top down
	assert ["div", "div.tr", "div.tr.th", "div.tr.td"] == dowalk(xsc.Element)

	# Elements bottom up
	assert ["div.tr.th", "div.tr.td", "div.tr", "div"] == dowalk(xsc.Element, startelementnode=False, endelementnode=True)

	# Elements top down (including elements in attributes)
	assert ["div", "div.class.i", "div.tr", "div.tr.id.b", "div.tr.th", "div.tr.td"] == dowalk(xsc.Element, enterattrs=True, enterattr=True)

	# Elements bottom up (including elements in attributes)
	assert ["div.class.i", "div.tr.id.b", "div.tr.th", "div.tr.td", "div.tr", "div"] == dowalk(xsc.Element, enterattrs=True, enterattr=True, startelementnode=False, endelementnode=True)

	# Elements, attributes and texts top down (including elements in attributes)
	assert ["div", "div.class", "div.tr", "div.tr.id", "div.tr.th", "div.tr.th.#", "div.tr.td", "div.tr.td.#"] == dowalk(xsc.Element, xsc.Attr, xsc.Text, enterattrs=True)

	def textonlyinattr(path):
		node = path[-1]
		if isinstance(node, xsc.Element):
			return True
		if isinstance(node, xsc.Text) and any(isinstance(node, xsc.Attr) for node in path):
			return True
		else:
			return False

	# Elements, attributes and texts top down (including elements in attributes, but text only if they are in attributes)
	assert ["div", "div.class.i", "div.class.i.#", "div.tr", "div.tr.id.b", "div.tr.id.b.#", "div.tr.th", "div.tr.td"] == dowalk(textonlyinattr, enterattrs=True, enterattr=True)


def test_walkgetitem():
	e = html.div(
		1,
		html.div(
			2,
			html.div(
				3
			)
		)
	)
	isdiv = xfind.selector(html.div)

	# Test ``walknodes``
	assert str(e.walknodes(isdiv)[0]) == "123"
	assert str(e.walknodes(isdiv)[-1]) == "3"
	with pytest.raises(IndexError):
		e.walknodes(isdiv)[3]
	with pytest.raises(IndexError):
		e.walknodes(isdiv)[-4]

	# Test ``walkpaths``
	assert str(e.walkpaths(isdiv)[0][-1]) == "123"
	assert str(e.walkpaths(isdiv)[-1][-1]) == "3"
	with pytest.raises(IndexError):
		e.walkpaths(isdiv)[3]
	with pytest.raises(IndexError):
		e.walkpaths(isdiv)[-4]
