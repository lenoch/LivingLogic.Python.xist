# -*- coding: utf-8 -*-

## Copyright 2008 by LivingLogic AG, Bayreuth/Germany
## Copyright 2008 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/__init__.py for the license


from ll.xist import xsc


###
### Processing instructions for output
###

class print_(xsc.ProcInst):
	"""
	Prints the expression in the processing instruction data.
	"""
	xmlname = "print"


class printx(xsc.ProcInst):
	"""
	Prints the expression in the processing instruction data and escapes
	the characters ``&``, ``<``, ``>``, ``'`` and ``"``.
	"""

	def convert(self, converter):
		return print_("xmlescape(%s)" % self.content)

###
### Processing instruction for statements
###

class code(xsc.ProcInst):
	"""
	A :class:`code` processing instruction contains a statement (such as an
	assignment or augmented assignment).
	"""


###
### Processing instructions for block structures (if/elif/else and for)
###

class if_(xsc.ProcInst):
	xmlname = "if"


class elif_(xsc.ProcInst):
	xmlname = "elif"


class else_(xsc.ProcInst):
	xmlname = "else"


class end(xsc.ProcInst):
	"""
	Ends an :class:`if_` or :class:`for_`. The PI value may be the type of the
	block (either ``"if"`` or ``"for"``). If the value is empty the innermost
	block will be closed without any checks for the type of block.
	"""


class for_(xsc.ProcInst):
	xmlname = "for"
