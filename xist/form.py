#! /usr/bin/env python

"""
A XSC module that contains elements that are useful for
forms. These are just abbreviations for the various
<input type=...> elements.
"""

__version__ = "$Revision$"[11:-2]
# $Source$

import xsc,html

class checkbox(xsc.Element:
	def asHTML(self):
		e = html.input(self.attrs)
		e["type"] = "checkbox"
		if self.hasAttr("value") and int(self["value"].asPlainString()) != 0:
			e["checked"] = None
		else:
			del e["checked"]
		return e.asHTML()

class edit(xsc.Element):
	attrHandlers = xsc.appendDict(control.attrHandlers,{ "size" : xsc.TextAttr })

	def asHTML(self):
		e = html.input(self.attrs)
		return e.asHTML()

class memo(xsc.Element):
	attrHandlers = xsc.appendDict(control.attrHandlers,html.textarea.attrHandlers)

	def asHTML(self):
		e = html.textarea()
		if self.hasAttr("value"):
			e.extend(self["value"])
		for attr in self.attrs.keys():
			if attr != "value":
				e[attr] = self[attr]
		return e.asHTML()

class hidden(xsc.Element):
	def asPlainString(self):
		return ""

	def asHTML(self):
		e = html.input(type="hidden",name=self["name"])
		if self.hasAttr("value"):
			e["value"] = self["value"]
		return e.asHTML()

namespace = xsc.Namespace("form","http://www.livinglogic.de/DTDs/form.dtd",vars())

if __name__ == "__main__":
	xsc.make()
