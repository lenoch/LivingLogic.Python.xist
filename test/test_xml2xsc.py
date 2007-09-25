#! /usr/bin/env/python
# -*- coding: utf-8 -*-

## Copyright 2007 by LivingLogic AG, Bayreuth/Germany.
## Copyright 2007 by Walter Dörwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license


from __future__ import with_statement

import cStringIO, types

from ll.xist import xsc, sims
from ll.xist.scripts import xml2xsc

try:
	import lxml
except ImportError:
	parser = "etree"
else:
	parser = "lxml"


def xml2mod(s, parser="etree"):
	with xsc.Pool():
		xnd = xml2xsc.stream2xnd(cStringIO.StringIO(s), parser=parser)

		code = xnd.aspy().encode()
		code = compile(code, "test.py", "exec")

		mod = types.ModuleType("test")
		mod.__file__ = "test.py"
		exec code in mod.__dict__
		return mod


def test_basics():
	xml = "<foo><bar/><?baz gurk?></foo>"
	mod = xml2mod(xml, parser=parser)

	assert issubclass(mod.foo, xsc.Element)
	assert isinstance(mod.foo.model, sims.Any)
	assert issubclass(mod.bar, xsc.Element)
	assert isinstance(mod.bar.model, sims.Empty)
	if parser == "lxml":
		assert issubclass(mod.baz, xsc.ProcInst)


def test_attrs():
	xml = "<foo a='1'><foo b='2'/></foo>"
	mod = xml2mod(xml, parser=parser)

	assert set(a.xmlname for a in mod.foo.Attrs.allowedattrs()) == set("ab")

