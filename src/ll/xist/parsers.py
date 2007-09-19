# -*- coding: utf-8 -*-

## Copyright 1999-2007 by LivingLogic AG, Bayreuth/Germany.
## Copyright 1999-2007 by Walter Dörwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license


"""
<par>This file contains everything you need to parse &xist; objects from files, strings, &url;s etc.</par>

<par>It contains different &sax;2 parser driver classes (mostly for sgmlop, everything else
is from <app moreinfo="http://pyxml.sf.net/">PyXML</app>). It includes a
<pyref class="HTMLParser"><class>HTMLParser</class></pyref> that uses sgmlop
to parse &html; and emit &sax;2 events.</par>
"""

import sys, os, os.path, warnings, cStringIO, codecs, pyexpat

from xml.parsers import expat

from ll import url, xml_codec
from ll.xist import xsc, utils, sgmlop
from ll.xist.ns import html

# from PyXML/dom/html/__init__.py
HTML_OPT_END = ["body", "colgroup", "dd", "dt", "head", "html", "li", "option", "p", "tbody", "td", "tfoot", "th", "thead", "tr"]

HTML_FORBIDDEN_END = ["area", "base", "basefont", "br", "col", "frame", "hr", "img", "input", "isindex", "link", "meta", "param"]

HTML_DTD = {
	"col": [],
	"u": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"p": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"caption": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"q": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"i": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"textarea": ["#PCDATA"],
	"center": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"script": ["#PCDATA"],
	"ol": ["li"],
	"a": ["#PCDATA", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"legend": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"strong": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"address": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"br": [],
	"base": [],
	"object": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "param", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"basefont": [],
	"map": ["address", "area", "blockquote", "center", "del", "dir", "div", "dl", "fieldset", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "ins", "isindex", "menu", "noframes", "noscript", "ol", "p", "pre", "script", "table", "ul"],
	"body": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"samp": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"dl": ["dd", "dt"],
	"acronym": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"html": ["body", "frameset", "head"],
	"em": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"label": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"tbody": ["tr"],
	"bdo": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"sub": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"meta": [],
	"ins": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"frame": [],
	"s": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"title": ["#PCDATA"],
	"frameset": ["frame", "frameset", "noframes"],
	"pre": ["#PCDATA", "a", "abbr", "acronym", "b", "bdo", "br", "button", "cite", "code", "dfn", "em", "i", "input", "kbd", "label", "map", "q", "s", "samp", "select", "span", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"dir": ["li"],
	"div": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"small": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"iframe": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"del": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"applet": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "param", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"ul": ["li"],
	"isindex": [],
	"button": ["#PCDATA", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "font", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "small", "span", "strike", "strong", "sub", "sup", "table", "tt", "u", "ul", "var"],
	"colgroup": ["col"],
	"b": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"table": ["caption", "col", "colgroup", "tbody", "tfoot", "thead", "tr"],
	"dt": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"optgroup": ["option"],
	"abbr": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"link": [],
	"h4": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"dd": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"big": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"hr": [],
	"form": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"option": ["#PCDATA"],
	"fieldset": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "legend", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"blockquote": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"head": ["base", "isindex", "link", "meta", "object", "script", "style", "title"],
	"thead": ["tr"],
	"cite": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"td": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"input": [],
	"var": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"th": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"tfoot": ["tr"],
	"dfn": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"li": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"param": [],
	"tr": ["td", "th"],
	"tt": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"menu": ["li"],
	"area": [],
	"img": [],
	"span": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"style": [],
	"noscript": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"noframes": ["#PCDATA", "a", "abbr", "acronym", "address", "applet", "b", "basefont", "bdo", "big", "blockquote", "br", "button", "center", "cite", "code", "del", "dfn", "dir", "div", "dl", "em", "fieldset", "font", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "map", "menu", "noframes", "noscript", "object", "ol", "p", "pre", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "table", "textarea", "tt", "u", "ul", "var"],
	"select": ["optgroup", "option"],
	"font": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"strike": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"sup": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"h5": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"kbd": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"h6": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"h1": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"h3": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"h2": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"],
	"code": ["#PCDATA", "a", "abbr", "acronym", "applet", "b", "basefont", "bdo", "big", "br", "button", "cite", "code", "del", "dfn", "em", "font", "i", "iframe", "img", "input", "ins", "kbd", "label", "map", "noscript", "object", "q", "s", "samp", "script", "select", "small", "span", "strike", "strong", "sub", "sup", "textarea", "tt", "u", "var"]
}


class LLParser(object):
	def __init__(self):
		self.application = None

	def register(self, application):
		self.application = application

	def begin(self):
		pass

	def end(self):
		pass

	def feed(self, data, final):
		pass


class SGMLOPParser(LLParser):
	def __init__(self, encoding=None):
		LLParser.__init__(self)
		self.encoding = encoding
		self._decoder = None
		self._parser = None

	def reset(self):
		self.close()
		self.source = None
		self.lineNumber = -1

	def begin(self):
		if self._decoder is None:
			self._decoder = codecs.getincrementaldecoder("xml")(self.encoding)
		if self._parser is None:
			self._parser = sgmlop.XMLParser()
			self._parser.register(self)

	def end(self):
		if self._parser is not None:
			self._parser.register(None)
			self._parser = None
		self._decoder = None

	def handle_comment(self, data):
		self.application.handle_comment(data)

	def handle_data(self, data):
		self.application.handle_data(data)

	def handle_cdata(self, data):
		self.application.handle_cdata(data)

	def handle_proc(self, target, data):
		self.application.handle_proc(target, data)

	def handle_entityref(self, name):
		self.application.handle_entityref(name)

	def finish_starttag(self, name, attrs):
		self.application.handle_enterstarttag(name)
		for (key, value) in attrs.iteritems():
			self.application.handle_enterattr(key)
			self.application.handle_data(value)
			self.application.handle_leaveattr(key)
		self.application.handle_leavestarttag(name)

	def finish_endtag(self, name):
		self.application.handle_endtag(name)


class BadEntityParser(SGMLOPParser):
	"""
	<par>A &sax;2 parser that recognizes the character entities
	defined in &html; and tries to pass on unknown or malformed
	entities to the handler literally.</par>
	"""

	def handle_entityref(self, name):
		try:
			c = {"lt": u"<", "gt": u">", "amp": u"&", "quot": u'"', "apos": u"'"}[name]
		except KeyError:
			name = self._makestring(name)
			try:
				self.getContentHandler().skippedEntity(name)
			except xsc.IllegalEntityError:
				self.getContentHandler().characters(u"&%s;" % name)
		else:
			self.getContentHandler().characters(c)
		self.headerJustRead = False

	def _string2fragment(self, text):
		"""
		This version tries to pass illegal content literally.
		"""
		if text is None:
			return xsc.Null
		node = xsc.Frag()
		pool = getattr(self.getContentHandler(), "pool", None)
		ct = (pool.text if pool is not None else xsc.Text)
		while True:
			texts = text.split(u"&", 1)
			text = texts[0]
			if text:
				node.append(ct(text))
			if len(texts)==1:
				break
			texts = texts[1].split(u";", 1)
			name = texts[0]
			if len(texts)==1: # no ; found, so it's no entity => append it literally
				name = u"&" + name
				warnings.warn(xsc.MalformedCharRefWarning(name))
				node.append(ct(name))
				break
			else:
				if name.startswith(u"#"): # character reference
					try:
						if name.startswith(u"#x"): # hexadecimal character reference
							node.append(ct(unichr(int(name[2:], 16))))
						else: # decimal character reference
							node.append(ct(unichr(int(name[1:]))))
					except (ValueError, OverflowError): # illegal format => append it literally
						name = u"&%s;" % name
						warnings.warn(xsc.MalformedCharRefWarning(name))
						node.append(ct(name))
				else: # entity reference
					try:
						entity = {"lt": u"<", "gt": u">", "amp": u"&", "quot": u'"', "apos": u"'"}[name]
					except KeyError:
						try:
							entity = self.getContentHandler().createEntity(name)
						except xsc.IllegalEntityError:
							name = u"&%s;" % name
							warnings.warn(xsc.MalformedCharRefWarning(name))
							entity = ct(name)
					else:
						entity = ct(entity)
					node.append(entity)
			text = texts[1]
		return node

	def handle_charref(self, data):
		data = self._makestring(data)
		try:
			if data.startswith("x"):
				data = unichr(int(data[1:], 16))
			else:
				data = unichr(int(data))
		except (ValueError, OverflowError):
			data = u"&#%s;" % data
		if not self.headerJustRead or not data.isspace():
			self.getContentHandler().characters(data)
			self.headerJustRead = False


class HTMLParser(BadEntityParser):
	"""
	<par>A &sax;2 parser that can parse &html;.</par>
	"""

	_whichparser = sgmlop.SGMLParser

	def __init__(self, bufsize=2**16-20):
		BadEntityParser.__init__(self, bufsize)
		self._stack = []
		self.pool = xsc.Pool(html)

	def reset(self):
		self._stack = []
		BadEntityParser.reset(self)

	def close(self):
		while self._stack: # close all open elements
			self.finish_endtag(self._stack[-1])
		BadEntityParser.close(self)

	def finish_starttag(self, name, attrs):
		name = name.lower()

		# guess omitted close tags
		while self._stack and self._stack[-1] in HTML_OPT_END and name not in HTML_DTD.get(self._stack[-1], []):
			BadEntityParser.finish_endtag(self, self._stack[-1])
			del self._stack[-1]

		# Check whether this element is allowed in the current context
		if self._stack and name not in HTML_DTD.get(self._stack[-1], []):
			warnings.warn(xsc.IllegalDTDChildWarning(name, self._stack[-1]))

		# Skip unknown attributes (but warn about them)
		newattrs = {}
		element = self.pool.element_xml(name, html)
		for (attrname, attrvalue) in attrs:
			if attrname=="xmlns" or ":" in attrname or element.Attrs.isallowed_xml(attrname.lower()):
				newattrs[attrname.lower()] = attrvalue
			else:
				warnings.warn(xsc.IllegalAttrError(attrname.lower(), None, True))
		BadEntityParser.finish_starttag(self, name, newattrs)

		if name in HTML_FORBIDDEN_END:
			# close tags immediately for which we won't get an end
			BadEntityParser.finish_endtag(self, name)
			return 0
		else:
			self._stack.append(name)
		return 1

	def finish_endtag(self, name):
		name = name.lower()
		if name in HTML_FORBIDDEN_END:
			# do nothing: we've already closed it
			return
		if name in self._stack:
			# close any open elements that were not closed explicitely
			while self._stack and self._stack[-1] != name:
				BadEntityParser.finish_endtag(self, self._stack[-1])
				del self._stack[-1]
			BadEntityParser.finish_endtag(self, name)
			del self._stack[-1]
		else:
			warnings.warn(xsc.IllegalCloseTagWarning(name))


class ExpatParser(LLParser):
	def __init__(self, encoding=None, transcode=False):
		LLParser.__init__(self)
		self.encoding = encoding
		self._parser = None
		self._decoder = None
		self._encoder = None
		self._transcode = transcode

	def begin(self):
		self._parser = expat.ParserCreate(self.encoding)
		self._parser.buffer_text = True
		self._parser.ordered_attributes = True
		self._parser.UseForeignDTD(True)
		self._parser.CharacterDataHandler = self.application.handle_data # Pass directly to the application
		self._parser.StartElementHandler = self.handle_startelement
		self._parser.EndElementHandler = self.handle_endelement
		self._parser.ProcessingInstructionHandler = self.application.handle_proc # Pass directly to the application
		self._parser.CommentHandler = self.application.handle_comment # Pass directly to the application
		self._parser.DefaultHandler = self.handle_default
		if self._transcode:
			self._decoder = codecs.getincrementaldecoder("xml")()
			self._encoder = codecs.getincrementalencoder("xml")(encoding="utf-8")

	def end(self):
		self._parser = None
		self._encoder = None
		self._decoder = None

	def handle_default(self, data):
		if data.startswith("&") and data.endswith(";"):
			self.application.handle_entityref(data[1:-1])

	# No handle_comment(self, data) (directly passed on to the application)

	# No handle_data(self, data) (directly passed on to the application)

	def handle_startelement(self, name, attrs):
		self.application.handle_enterstarttag(name)
		for i in xrange(0, len(attrs), 2):
			key = attrs[i]
			self.application.handle_enterattr(key)
			self.application.handle_data(attrs[i+1])
			self.application.handle_leaveattr(key)
		self.application.handle_leavestarttag(name)

	def handle_endelement(self, name):
		self.application.handle_endtag(name)

	# No handle_proc(self, target, data) (directly passed on to the application)

	def feed(self, data, final):
		if self._transcode:
			data = self._decoder.decode(data, final)
			data = self._encoder.encode(data, final)
		self._parser.Parse(data, final)


class LaxAttrs(xsc.Attrs):
	@classmethod
	def _allowedattrkey(cls, name, xmlns=None):
		if xmlns is not None:
			xmlns = xsc.nsname(xmlns)
			try:
				return (xsc.getpoolstack()[-1].attrname(name, xmlns), xmlns) # ask namespace about global attribute
			except xsc.IllegalAttrError:
				return (name, xmlns)
		return name

	@classmethod
	def _allowedattrkey_xml(cls, name, xmlns=None):
		if xmlns is not None:
			xmlns = xsc.nsname(xmlns)
			try:
				return (xsc.getpoolstack()[-1].attrname_xml(name, xmlns), xmlns) # ask namespace about global attribute
			except xsc.IllegalAttrError:
				return (name, xmlns)
		return name

	def set(self, name, xmlns=None, value=None):
		attr = self.allowedattr(name, xmlns)(value)()
		attr.xmlname = name
		dict.__setitem__(self, self._allowedattrkey(name, xmlns), attr) # put the attribute in our dict
		return attr

	def set_xml(self, name, xmlns=None, value=None):
		attr = self.allowedattr_xml(name, xmlns)(value)()
		attr.xmlname = name
		dict.__setitem__(self, self._allowedattrkey_xml(name, xmlns), attr) # put the attribute in our dict
		return attr

	@classmethod
	def allowedattr(cls, name, xmlns):
		if xmlns is not None:
			xmlns = xsc.nsname(xmlns)
			try:
				return xsc.getpoolstack()[-1].attrclass(name, xmlns) # return global attribute
			except xsc.IllegalAttrError:
				return xsc.TextAttr
		else:
			return xsc.TextAttr

	@classmethod
	def allowedattr(cls, name, xmlns, xml=False):
		if xmlns is not None:
			xmlns = xsc.nsname(xmlns)
			try:
				return xsc.getpoolstack()[-1].attrclass_xml(name, xmlns) # return global attribute
			except xsc.IllegalAttrError:
				return xsc.TextAttr
		else:
			return xsc.TextAttr


class LaxElement(xsc.Element):
	register = None
	Attrs = LaxAttrs


class Parser(object):
	"""
	<par>It is the job of a <class>Parser</class> to create the object tree from the
	&sax; events generated by the underlying &sax; parser.</par>
	"""

	def __init__(self, saxparser=None, prefixes=None, tidy=False, loc=True, validate=True, encoding=None, pool=None):
		"""
		<par>Create a new <class>Parser</class> instance.</par>

		<par>Arguments have the following meaning:</par>
		<dlist>
		<term><arg>saxparser</arg></term><item><par>a callable that returns an instance of a &sax;2 compatible parser.
		&xist; itself provides several &sax;2 parsers
		(all based on Fredrik Lundh's <app>sgmlop</app> from <app moreinfo="http://pyxml.sf.net/">PyXML</app>):</par>
		<ulist>
		<item><pyref module="ll.xist.parsers" class="SGMLOPParser"><class>SGMLOPParser</class></pyref>
		(which is the default if the <arg>saxparser</arg> argument is not given);</item>
		<item><pyref module="ll.xist.parsers" class="BadEntityParser"><class>BadEntityParser</class></pyref>
		(which is based on <class>SGMLOPParser</class> and tries to pass on unknown entity references as literal content);</item>
		<item><pyref module="ll.xist.parsers" class="HTMLParser"><class>HTMLParser</class></pyref> (which is
		based on BadEntityParser and tries to make sense of &html; sources).</item>
		</ulist>
		</item>

		<term><arg>tidy</arg></term><item>If <arg>tidy</arg> is true, <link href="http://xmlsoft.org/">libxml2</link>'s
		&html; parser will be used for parsing broken &html;.</item>
		<term><arg>nspool</arg></term><item>an instance of <pyref module="ll.xist.xsc" class="NSPool"><class>ll.xist.xsc.NSPool</class></pyref>;
		From this namespace pool namespaces will be taken when the parser
		encounters <lit>xmlns</lit> attributes.</item>

		<term><arg>loc</arg></term><item>Should location information be attached to the generated nodes?</item>

		<term><arg>validate</arg></term><item>Should the parsed &xml; nodes be validated after parsing?</item>

		<term><arg>encoding</arg></term><item>The default encoding to use, when the
		source doesn't provide an encoding. The default <lit>None</lit> results in
		<lit>"utf-8"</lit> for parsing &xml; and <lit>"iso-8859-1"</lit> when parsing
		broken &html; (when <lit><arg>tidy</arg></lit> is true).</item>

		<term><arg>pool</arg></term><item>A <pyref module="ll.xist.xsc" class="Pool"><class>ll.xist.xsc.Pool</class></pyref>
		object which will be used for instantiating all nodes.</item>
		</dlist>
		"""
		self.saxparser = saxparser

		self.pool = (pool if pool is not None else xsc.getpoolstack()[-1])

		# the currently active prefix mapping (will be replaced once xmlns attributes are encountered)
		if prefixes is None:
			# make all currently known namespaces available without prefix
			# (if there are elements with colliding namespace, which one will be used is random (based on dict iteration order))
			self.prefixes = {None: list(set(c.xmlns for c in self.pool.elements()))}
		else:
			self.prefixes = {}
			for (prefix, xmlns) in prefixes.iteritems():
				if prefix is not None and not isinstance(prefix, basestring):
					raise TypeError("Prefix must be None or string, not %r" % prefix)
				if isinstance(xmlns, (list, tuple)):
					self.prefixes[prefix] = map(xsc.nsname, xmlns)
				else:
					self.prefixes[prefix] = xsc.nsname(xmlns)

		self._locator = None
		self.tidy = tidy
		self.loc = loc
		self.validate = validate
		self.encoding = encoding
		self._attr = None
		self._attrs = None

	def _parseHTML(self, stream, base, sysid, encoding):
		"""
		Internal helper method for parsing &html; via <module>libxml2</module>.
		"""
		import libxml2 # This requires libxml2 (see http://www.xmlsoft.org/)

		def decode(s):
			try:
				return s.decode("utf-8")
			except UnicodeDecodeError:
				return s.decode("iso-8859-1")

		def toxsc(node):
			if node.type == "document_html":
				newnode = xsc.Frag()
				child = node.children
				while child is not None:
					newnode.append(toxsc(child))
					child = child.next
			elif node.type == "element":
				name = decode(node.name).lower()
				try:
					newnode = self.pool.element_xml(name, html)
					if self.loc:
						newnode.startloc = xsc.Location(sysid=sysid, line=node.lineNo())
				except xsc.IllegalElementError:
					newnode = xsc.Frag()
				else:
					attr = node.properties
					while attr is not None:
						name = decode(attr.name).lower()
						if attr.content is None:
							content = u""
						else:
							content = decode(attr.content)
						try:
							attrnode = newnode.attrs.set_xml(name, value=content)
						except xsc.IllegalAttrError:
							pass
						else:
							attrnode = attrnode.parsed(self)
							newnode.attrs.set_xml(name, value=attrnode)
						attr = attr.next
					newnode.attrs = newnode.attrs.parsed(self)
					newnode = newnode.parsed(self, start=True)
				child = node.children
				while child is not None:
					newnode.append(toxsc(child))
					child = child.next
				if isinstance(node, xsc.Element): # if we did recognize the element, otherwise we're in a Frag
					newnode = newnode.parsed(self, start=False)
			elif node.type in ("text", "cdata"):
				newnode = self.pool.text(decode(node.content))
				if self.loc:
					newnode.startloc = xsc.Location(sysid=sysid, line=node.lineNo())
			elif node.type == "comment":
				newnode = self.pool.comment(decode(node.content))
				if self.loc:
					newnode.startloc = xsc.Location(sysid=sysid, line=node.lineNo())
			else:
				newnode = xsc.Null
			return newnode

		self.base = base

		data = stream.read()
		try:
			olddefault = libxml2.lineNumbersDefault(1)
			doc = libxml2.htmlReadMemory(data, len(data), sysid, encoding, 0x160)
			try:
				node = toxsc(doc)
			finally:
				doc.freeDoc()
		finally:
			libxml2.lineNumbersDefault(olddefault)
		return node

	def begin(self, base=None, encoding=None):
		if self.saxparser is None:
			parser = SGMLOPParser(encoding=encoding)
		else:
			parser = self.saxparser
		parser.register(self)
		self.base = url.URL(base)
		self._nesting = [ (xsc.Frag(), self.prefixes) ]
		parser.begin()
		return parser

	def end(self, parser):
		parser.end()
		return self._nesting[0][0]

	def parsestring(self, data, base=None, encoding=None):
		parser = self.begin(base=base, encoding=encoding)
		parser.feed(data, True)
		return self.end(parser)

	def parseiter(self, data, base=None, encoding=None):
		parser = self.begin(base=base, encoding=encoding)
		for d in data:
			parser.feed(d, False)
		parser.feed("", True)
		return self.end(parser)

	def parsestream(self, stream, base=None, encoding=None, size=8192):
		parser = self.begin(base=base, encoding=encoding)
		while True:
			data = stream.read(size)
			final = not data
			parser.feed(data, final)
			if final:
				return self.end(parser)


	def _parse(self, stream, base, sysid, encoding):
		self.base = url.URL(base)

		parser = self.saxparser()
		# register us for callbacks
		parser.setErrorHandler(self)
		parser.setContentHandler(self)
		parser.setDTDHandler(self)
		parser.setEntityResolver(self)

		# Configure the parser
		try:
			parser.setFeature(handler.feature_namespaces, False) # We do our own namespace processing
		except sax.SAXNotSupportedException:
			pass
		try:
			parser.setFeature(handler.feature_external_ges, False) # Don't process external entities, but pass them to skippedEntity
		except sax.SAXNotSupportedException:
			pass

		self.skippingwhitespace = False

		if self.tidy:
			if encoding is None:
				encoding = "iso-8859-1"
			return self._parseHTML(stream, base, sysid, encoding)

		if encoding is None:
			encoding = "utf-8"

		source = sax.xmlreader.InputSource(sysid)
		source.setByteStream(stream)
		source.setEncoding(encoding)

		# XIST nodes do not have a parent link, therefore we have to store the
		# active path through the tree in a stack (which we call _nesting)
		# together with the namespace prefixes defined by each element.
		#
		# After we've finished parsing, the Frag that we put at the bottom of the
		# stack will be our document root.
		#
		# The parser provides the ability to skip illegal elements, attributes,
		# processing instructions or entity references, but for illegal elements,
		# it must still record the new namespaces defined by the illegal element.
		# In this case None is stored in the stack instead of the element node.

		try:
			parser.parse(source)
		finally:
			self._nesting = None
		return root

	def parse(self, stream, base=None, sysid=None):
		"""
		Parse &xml; from the stream <arg>stream</arg> into an &xist; tree.
		<arg>base</arg> is the base &url; for the parsing process, <arg>sysid</arg>
		is the &xml; system identifier (defaulting to <arg>base</arg> if it is <lit>None</lit>).
		"""
		if sysid is None:
			sysid = base
		return self._parse(stream, base, sysid, self.encoding)

	def parseString(self, text, base=None, sysid=None):
		"""
		Parse the string <arg>text</arg> (<class>str</class> or <class>unicode</class>)
		into an &xist; tree. <arg>base</arg> is the base &url; for the parsing process, <arg>sysid</arg>
		is the &xml; system identifier (defaulting to <arg>base</arg> if it is <lit>None</lit>).
		"""
		if isinstance(text, unicode):
			encoding = "utf-8"
			text = text.encode(encoding)
		else:
			encoding = self.encoding
		stream = cStringIO.StringIO(text)
		if base is None:
			base = url.URL("STRING")
		if sysid is None:
			sysid = str(base)
		return self._parse(stream, base, sysid, encoding)

	def parseURL(self, name, base=None, sysid=None, *args, **kwargs):
		"""
		Parse &xml; input from the &url; <arg>name</arg> which might be a string
		or an <pyref module="ll.url" class="URL"><class>URL</class></pyref> object
		into an &xist; tree. <arg>base</arg> is the base &url; for the parsing process
		(defaulting to the final &url; of the response (i.e. including redirects)),
		<arg>sysid</arg> is the &xml; system identifier (defaulting to <arg>base</arg>
		if it is <lit>None</lit>). <arg>*args</arg> and <arg>**kwargs</arg> will
		be passed on to the <method>open</method> call.
		"""
		name = url.URL(name)
		stream = name.open("rb", *args, **kwargs)
		if base is None:
			base = stream.finalurl()
		if sysid is None:
			sysid = str(base)
		encoding = self.encoding
		if encoding is None:
			encoding = stream.encoding()
		result = self._parse(stream, base, sysid, encoding)
		stream.close()
		return result

	def parseFile(self, filename, base=None, sysid=None):
		"""
		Parse &xml; input from the file named <arg>filename</arg>. <arg>base</arg> is
		the base &url; for the parsing process (defaulting to <arg>filename</arg>),
		<arg>sysid</arg> is the &xml; system identifier (defaulting to <arg>base</arg>).
		"""
		filename = os.path.expanduser(filename)
		stream = open(filename, "rb")
		if base is None:
			base = url.File(filename)
		if sysid is None:
			sysid = str(base)
		result = self._parse(stream, base, sysid, self.encoding)
		stream.close()
		return result

	def setDocumentLocator(self, locator):
		self._locator = locator

	def handle_enterstarttag(self, name):
		self._attrs = {}

	def handle_enterattr(self, name):
		node = xsc.Frag()
		self._attrs[name] = node
		self._nesting.append((node, self._nesting[-1][1]))

	def handle_leaveattr(self, name):
		self._nesting.pop()

	def handle_leavestarttag(self, name):
		oldprefixes = self.prefixes

		newprefixes = {}
		for (attrname, xmlns) in self._attrs.iteritems():
			if attrname==u"xmlns" or attrname.startswith(u"xmlns:"):
				prefix = attrname[6:] or None
				newprefixes[prefix] = unicode(xmlns)

		if newprefixes:
			prefixes = oldprefixes.copy()
			prefixes.update(newprefixes)
			self.prefixes = newprefixes = prefixes
		else:
			newprefixes = oldprefixes

		(prefix, sep, name) = name.rpartition(u":")
		prefix = prefix or None

		try:
			xmlns = newprefixes[prefix]
		except KeyError:
			raise xsc.IllegalPrefixError(prefix)
		else:
			node = self.pool.element_xml(name, xmlns)

		for (attrname, attrvalue) in self._attrs.iteritems():
			if attrname != u"xmlns" and not attrname.startswith(u"xmlns:"):
				if u":" in attrname:
					(attrprefix, attrname) = attrname.split(u":", 1)
					if attrprefix == "xml":
						xmlns = xsc.xml_xmlns
					else:
						try:
							xmlns = newprefixes[attrprefix]
						except KeyError:
							raise xsc.IllegalPrefixError(attrprefix)
				else:
					xmlns = None
				if xmlns is not None:
					attrname = self.pool.attrclass_xml(attrname, xmlns)
				attrvalue = node.attrs.set_xml(attrname, attrvalue)
				node.attrs.set_xml(attrname, attrvalue.parsed(self))
		node.attrs = node.attrs.parsed(self)
		node = node.parsed(self, start=True)
		self.__appendNode(node)
		# push new innermost element onto the stack, together with the list of prefix mappings to which we have to return when we leave this element
		self._nesting.append((node, oldprefixes))
		self._attrs = None

	def handle_endtag(self, name):
		currentelement = self._nesting[-1][0]

		(prefix, sep, name) = name.rpartition(u":")
		xmlns = self.prefixes[prefix or None]
		element = self.pool.element_xml(name, xmlns) # Unfortunately this creates the element a second time.
		if  element.__class__ is not currentelement.__class__:
			raise xsc.ElementNestingError(currentelement.__class__, element.__class__)

		currentelement.parsed(self, start=False) # ignore return value

		if self.validate:
			currentelement.checkvalid()
		if self.loc:
			currentelement.endloc = self.getLocation()

		self.prefixes = self._nesting.pop()[1] # pop the innermost element off the stack and restore the old prefixes mapping (from outside this element)

	def handle_data(self, content):
		if content:
			node = self.pool.text(content)
			node = node.parsed(self)
			last = self._nesting[-1][0]
			if len(last) and isinstance(last[-1], xsc.Text):
				node = last[-1] + unicode(node) # join consecutive Text nodes
				node.startloc = last[-1].startloc # make sure the replacement node has the original location
				last[-1] = node # replace it
			else:
				self.__appendNode(node)

	def handle_comment(self, content):
		node = self.pool.comment(content)
		node = node.parsed(self)
		self.__appendNode(node)

	def handle_proc(self, target, content):
		if target != "xml":
			node = self.pool.procinst_xml(target, content)
			node = node.parsed(self)
			self.__appendNode(node)

	def handle_entityref(self, name):
		try:
			c = {u"lt": u"<", u"gt": u">", u"amp": u"&", u"quot": u'"', u"apos": u"'"}[name]
		except KeyError:
			node = self.pool.entity_xml(name)
			if isinstance(node, xsc.CharRef):
				self.handle_data(unichr(node.codepoint))
			else:
				node = node.parsed(self)
				self.__appendNode(node)
		else:
			self.handle_data(c)

	def getLocation(self):
		return xsc.Location(self._locator)

	def __appendNode(self, node):
		if self.loc:
			node.startloc = self.getLocation()
		self._nesting[-1][0].append(node) # add the new node to the content of the innermost element/fragment/(attribute)


def parse(stream, base=None, sysid=None, **parserargs):
	"""
	Parse &xml; from the stream <arg>stream</arg> into an &xist; tree.
	For the arguments <arg>base</arg> and <arg>sysid</arg> see the method
	<pyref class="Parser" method="parse"><method>parse</method></pyref>
	in the <class>Parser</class> class. You can pass any other argument that the
	<pyref class="Parser" method="__init__"><class>Parser</class> constructor</pyref>
	takes as keyword arguments via <arg>parserargs</arg>.
	"""
	parser = Parser(**parserargs)
	return parser.parse(stream, base, sysid)


def parsestring(text, base=None, **parserargs):
	"""
	Parse the string <arg>text</arg> (<class>str</class> or <class>unicode</class>) into an
	&xist; tree. For the argument <arg>base</arg> see the method
	<pyref class="Parser" method="parseString"><method>parsestring</method></pyref>
	in the <class>Parser</class> class. You can pass any other argument that the
	<pyref class="Parser" method="__init__"><class>Parser</class> constructor</pyref>
	takes as keyword arguments via <arg>parserargs</arg>.
	"""
	parser = Parser(**parserargs)
	return parser.parsestring(text, base)


def parseiter(iterable, base=None, **parserargs):
	"""
	Parse the string <arg>text</arg> (<class>str</class> or <class>unicode</class>) into an
	&xist; tree. For the argument <arg>base</arg> see the method
	<pyref class="Parser" method="parseString"><method>parsestring</method></pyref>
	in the <class>Parser</class> class. You can pass any other argument that the
	<pyref class="Parser" method="__init__"><class>Parser</class> constructor</pyref>
	takes as keyword arguments via <arg>parserargs</arg>.
	"""
	parser = Parser(**parserargs)
	return parser.parseiter(iterable, base)


def parseURL(url, base=None, sysid=None, headers=None, data=None, **parserargs):
	"""
	Parse &xml; input from the &url; <arg>name</arg> which might be a string
	or an <pyref module="ll.url" class="URL"><class>URL</class></pyref> object
	into an &xist; tree. For the arguments <arg>base</arg>, <arg>sysid</arg>,
	<arg>headers</arg> and <arg>data</arg> see the method
	<pyref class="Parser" method="parseURL"><method>parseURL</method></pyref>
	in the <class>Parser</class> class. You can pass any other argument that the
	<pyref class="Parser" method="__init__"><class>Parser</class> constructor</pyref>
	takes as keyword arguments via <arg>parserargs</arg>.
	"""
	parser = Parser(**parserargs)
	parseargs = {}
	if headers is not None:
		parseargs["headers"] = headers
	if data is not None:
		parseargs["data"] = data
	return parser.parseURL(url, base, sysid, *parseargs)


def parseFile(filename, base=None, sysid=None, **parserargs):
	"""
	Parse &xml; input from the file named <arg>filename</arg>. For the arguments
	<arg>base</arg> and <arg>sysid</arg> see the method
	<pyref class="Parser" method="parseFile"><method>parseFile</method></pyref>
	in the <class>Parser</class> class. You can pass any other argument that the
	<pyref class="Parser" method="__init__"><class>Parser</class> constructor</pyref>
	takes as keyword arguments via <arg>parserargs</arg>.
	"""
	parser = Parser(**parserargs)
	return parser.parseFile(filename, base, sysid)
