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
This modules contains the base class for the converter objects used in the call to the
<pyref module="xist.xsc" class="Node" method="convert"><method>convert</method></pyref> method.
"""

__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$

import types

class Context:
	"""
	This is an empty class, that can be used by the
	<pyref module="xist.xsc" class="Node" method="convert"><method>convert</method></pyref>
	method to hold element specific data during the convert call. The method
	<pyref class="Converter" method="__getitem__"><method>Converter.__getitem__</method></pyref>
	will return a unique instance of this class.
	"""
	
	def __init__(self):
		pass

class Converter:
	"""
	<doc:par>An instance of this class is passed around in calls to the
	<pyref module="xist.xsc" class="Node" method="convert"><method>convert</method></pyref> method.
	This instance can be used when some element needs to keep state across a nested convert call.
	A typical example are nested chapter/subchapter elements with automatic numbering.
	For an example see the element <pyref module="xist.ns.doc" class="section"><class>section</class></pyref>.</doc:par>
	"""
	def __init__(self, root=None, mode=None, stage=None, target=None, lang=None):
		"""
		<doc:par>Create a <class>Converter</class>.</doc:par>
		<doc:par>Arguments are:
		<doc:ulist>
		<doc:item><arg>root</arg>: The root URL specifies the directory
		into which the converted tree will be published. If there are any elements that
		need to have access to files in this directory, you have to pass in this URL (an example
		is <pyref module="xist.ns.specials" class="autoimg"><class>autoimg</class></pyref>)</doc:item>
		<doc:item><arg>mode</arg>: The conversion mode. This corresponds
		directy with the mode in &xslt;. The default is <code>None</code>.</doc:item>
		<doc:item><arg>stage</arg>: If your conversion is done in multiple
		steps or stages you can use this argument to specify in which stage the conversion
		process currently is. The default is <lit>"deliver"</lit>.</doc:item>
		<doc:item><arg>target</arg>: Specifies the conversion target. This
		could be <lit>"text"</lit>, <lit>"html"</lit>, <lit>"wml"</lit>, <lit>"docbook"</lit>
		or anything like that. The default is <lit>"html"</lit>.</doc:item>
		<doc:item><arg>lang</arg>: The target language. The default is <lit>None</lit>.</doc:item>
		<doc:item><arg>makeaction</arg>, <arg>maketarget</arg>, <arg>makeproject</arg>: These parameters are used by
		the <pyref module="make"><module>make</module></pyref> module.</doc:item>
		</doc:ulist>
		</doc:par>
		"""
		self.root = root
		self.mode = mode
		if stage is None:
			self.stage = "deliver"
		else:
			self.stage = stage
		if target is None:
			self.target = "html"
		else:
			self.target = target
		self.lang = lang
		self.contexts = {}
		self.makeaction = None
		self.maketarget = None
		self.makeproject = None

	def __getitem__(self, class_):
		"""
		<doc:par>Return a context object that is unique for <arg>class_</arg>,
		which should be the class object of an element type. This means that every element type
		gets its own context and can store information there that needs to be available
		across calls to <pyref module="xist.xsc" class="Node" method="convert"><method>convert</method></pyref>.</doc:par>
		"""
		return self.contexts.setdefault(class_, Context())
