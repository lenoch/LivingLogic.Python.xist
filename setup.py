#!/usr/bin/env python

# Setup script for XIST

__version__ = "$Revision$"[11:-2]
# $Source$

from distutils.core import setup, Extension

setup(
	name = "XIST",
	version = "0.4.7",
	description = "An XML based extensible HTML generator",
	author = "Walter D�rwald",
	author_email = "walter@livinglogic.de",
	#url = "http://",
	licence = "Python",
	packages = ['xist'],
	ext_modules = [Extension("xist.helpers", ["xist/helpers.c"])]
)
