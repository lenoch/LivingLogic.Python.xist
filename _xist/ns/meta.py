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
<dbl:para>An &xist; module that contains elements that simplify handling
meta data. All elements in this module will generate a <pyref module="xist.ns.html" class="meta">html.meta</pyref>
element when converted.</dbl:para>
"""

__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$

from xist import xsc
import html

class contenttype(html.meta):
	"""
	<dbl:para>can be used for a <code>&lt;meta http-equiv="Content-Type" content="text/html"/&gt;</code>, where
	the character set will be automatically inserted on a call to <code>publish()</code>.</dbl:para>

	<dbl:para>Usage is simple: <code>&lt;meta:contenttype/&gt;</code></dbl:para>
	"""
	empty = 1
	attrHandlers = html.meta.attrHandlers.copy()
	del attrHandlers["http-equiv"]
	del attrHandlers["http_equiv"]
	del attrHandlers["name"]
	del attrHandlers["content"]

	def convert(self, converter):
		e = html.meta()
		e.attrs = self.attrs.copy()
		e["http-equiv"] = "Content-Type"
		e["content"] = "text/html"
		return e.convert(converter)

class keywords(html.meta):
	"""
	<dbl:para>can be used for a <code>&lt;meta name="keywords" content="..."/&gt;</code>.</dbl:para>

	<dbl:para>Usage is simple: <code>&lt;meta:keywords&gt;foo, bar&lt;/meta:keywords&gt;</code></dbl:para>
	"""
	empty = 0
	attrHandlers = html.meta.attrHandlers.copy()
	del attrHandlers["http-equiv"]
	del attrHandlers["http_equiv"]
	del attrHandlers["name"]
	del attrHandlers["content"]

	def convert(self, converter):
		e = html.meta()
		e.attrs = self.attrs.copy()
		e["name"] = "keywords"
		e["content"] = self.content.convert(converter).asPlainString()
		return e.convert(converter)

class description(html.meta):
	"""
	<par noindent>can be used for a <code>&lt;meta name="description" content="..."/&gt;</code>.</par>

	<par>Usage is simple: <code>&lt;meta:description&gt;foo, bar&lt;/meta:description&gt;</code></par>
	"""
	empty = 0
	attrHandlers = html.meta.attrHandlers.copy()
	del attrHandlers["http-equiv"]
	del attrHandlers["http_equiv"]
	del attrHandlers["name"]
	del attrHandlers["content"]

	def convert(self, converter):
		e = html.meta()
		e.attrs = self.attrs.copy()
		e["name"] = "description"
		e["content"] = self.content.convert(converter).asPlainString()
		return e.convert(converter)

class stylesheet(html.link):
	"""
	<par noindent>can be used for a <code>&lt;link rel="stylesheet" type="text/css" href="..."/&gt;</code>.</par>

	<par>Usage is simple: <code>&lt;meta:stylesheet href="root:stylesheets/main.css"/&gt;</code></par>
	"""
	empty = 1
	attrHandlers = html.link.attrHandlers.copy()
	del attrHandlers["rel"]
	del attrHandlers["type"]

	def convert(self, converter):
		e = html.link()
		e.attrs = self.attrs.copy()
		e["rel"] = "stylesheet"
		e["type"] = "text/css"
		return e.convert(converter)

class made(html.link):
	"""
	<par noindent>can be used for a <code>&lt;link rel="made" href="mailto:..."/&gt;</code>.</par>

	<par>Usage is simple: <code>&lt;meta:made href="foobert@bar.org"/&gt;</code>.</par>
	"""
	empty = 1
	attrHandlers = html.link.attrHandlers.copy()
	del attrHandlers["rel"]

	def convert(self, converter):
		e = html.link()
		e.attr = self.attrs.copy()
		e["rel"] = "made"
		e["href"] = ("mailto:", e["href"])
		return e.convert(converter)

class author(xsc.Element):
	"""
	<par noindent>can be used to embed author information in the header.
	It will generate &lt;link rel="made"/&gt; and &lt;meta name="author"/&gt; elements.</par>
	"""
	empty = 1
	attrHandlers = {"lang": xsc.TextAttr, "name": xsc.TextAttr, "email": xsc.TextAttr}

	def convert(self, converter):
		e = xsc.Frag()
		if self.hasAttr("name"):
			e.append(html.meta(name="author", content=self["name"]))
			if self.hasAttr("lang"):
				e[-1]["lang"] = self["lang"]
		if self.hasAttr("email"):
			e.append(html.link(rel="made", href=("mailto:", self["email"])))
		return e.convert(converter)

class javascript(xsc.Element):
	"""
	<par noindent>can be used to embed a reference to an external javascript file
	in the page header</par>
	"""
	empty = 0
	attrHandlers = {"href": xsc.TextAttr}

	def convert(self, converter):
		e = html.script(*self.content, language="javascript", type="text/javascript", src=self["href"])
		return e.convert(converter)

namespace = xsc.Namespace("meta", "http://www.livinglogic.de/DTDs/meta.dtd", vars())
