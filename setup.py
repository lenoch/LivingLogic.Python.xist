#! /usr/bin/env python
# -*- coding: Latin-1 -*-

# Setup script for XIST

__version__ = tuple(map(int,"$Revision$"[11:-2].split(".")))
# $Source$

from distutils.core import setup, Extension

setup(
	name="XIST",
	version="2.0.2",
	description="An XML-based extensible HTML generator",
	long_description="XIST is an XML based extensible HTML generator. XIST is also a DOM parser (built on top of SAX2)\n"
		"with a very simple and pythonesque tree API. Every XML element type corresponds to a Python class and these\n"
		"Python classes provide a conversion method to transform the XML tree (e.g. into HTML).\n"
		"XIST can be considered 'object oriented XSL'.",
	author="Walter D�rwald",
	author_email="walter@livinglogic.de",
	url="http://www.livinglogic.de/Python/xist/",
	license="Python",
	packages=['ll.xist', 'll.xist.ns'],
	package_dir={"ll.xist": "_xist"},
	ext_modules=[
		Extension("ll.xist.csstokenizer", ["_xist/csstokenizer.cxx"]),
		Extension("ll.xist.helpers", ["_xist/helpers.c"])
	],
	scripts=["scripts/dtd2xsc.py", "scripts/doc2txt.py", "scripts/xscmake.py" ]
)
