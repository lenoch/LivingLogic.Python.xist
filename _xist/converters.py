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
This modules contains the base class for the converter objects
used in the call to the convert method.
"""

__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$

class Context:
	"""
	This is an empty class, that can be used by
	the convert method to hold element specific
	data during the convert call. For a more extensive
	explanation see <pyref module="xist.xsc" class="Node" method="getConverterContext">getConverterContext</pyref>.
	"""
	
	def __init__(self):
		pass

class Converter:
	def __init__(self, mode=None, stage=None, target=None):
		self.mode = mode
		self.stage = stage
		self.target = target
		self.contexts = {}

	def getContext(self, nodeClass):
		return self.contexts.setdefault(nodeClass, Context())
