#! /usr/bin/env/python
# -*- coding: iso-8859-1 -*-

## Copyright 1999-2003 by LivingLogic AG, Bayreuth, Germany.
## Copyright 1999-2003 by Walter D�rwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license

import sys, unittest, cStringIO, warnings

from xml.sax import saxlib

from ll import url
from ll.xist import xsc, parsers, presenters, converters, helpers, errors, options
from ll.xist.ns import wml, ihtml, html, css, abbr, specials, htmlspecials, php, xml, xndl

# set to something ASCII, so presenters work, even if the system default encoding is ascii
options.reprtab = "  "

class XISTTest(unittest.TestCase):
	def check_lenunicode(self, node, _len, content):
		self.assertEqual(len(node), _len)
		self.assertEqual(unicode(node), content)

	def test_frageq(self):
		self.assertEqual(xsc.Frag(), xsc.Frag())
		self.assertEqual(xsc.Frag(1), xsc.Frag(1))
		self.assertEqual(xsc.Frag(1, 2), xsc.Frag(1, 2, None))
		self.assertNotEqual(xsc.Frag(1, 2), xsc.Frag(12))
		self.assertNotEqual(xsc.Frag(), xsc.Frag(""))
		self.assertNotEqual(xsc.Frag(""), xsc.Frag("", ""))

	def test_elementeq(self):
		self.assertEqual(html.div(), html.div())
		self.assertEqual(html.div(1), html.div(1))
		self.assertEqual(html.div(1, 2), html.div(1, 2, None))
		self.assertNotEqual(html.div(1, 2), html.div(12))
		self.assertNotEqual(html.div(), html.div(""))
		self.assertNotEqual(html.div(""), html.div("", ""))
		self.assertEqual(html.div(1, html.div(2, html.div(3))), html.div(1, html.div(2, html.div(3))))

	def test_texteq(self):
		self.assertEqual(xsc.Text(), xsc.Text())
		self.assertEqual(xsc.Text(1), xsc.Text(1))
		self.assertEqual(xsc.Text("1"), xsc.Text(1))
		self.assertEqual(xsc.Text(u"1"), xsc.Text(1))

	def test_commenteq(self):
		self.assertEqual(xsc.Comment(), xsc.Comment())
		self.assertEqual(xsc.Comment(1), xsc.Comment(1))
		self.assertEqual(xsc.Comment("1"), xsc.Comment(1))
		self.assertEqual(xsc.Comment(u"1"), xsc.Comment(1))

	def test_doctypeeq(self):
		self.assertEqual(xsc.DocType(), xsc.DocType())
		self.assertEqual(xsc.DocType(1), xsc.DocType(1))
		self.assertEqual(xsc.DocType("1"), xsc.DocType(1))
		self.assertEqual(xsc.DocType(u"1"), xsc.DocType(1))

	def test_mixeq(self):
		self.assertNotEqual(xsc.Comment(1), xsc.Text(1))
		self.assertNotEqual(xsc.DocType(1), xsc.Text(1))
		self.assertNotEqual(xsc.DocType(1), xsc.Text(1))

	def test_fraglen(self):
		self.check_lenunicode(xsc.Frag(), 0, u"")
		self.check_lenunicode(xsc.Frag(1), 1, u"1")
		self.check_lenunicode(xsc.Frag(1, 2, 3), 3, u"123")
		self.check_lenunicode(xsc.Frag(None), 0, u"")
		self.check_lenunicode(xsc.Frag(None, None, None), 0, u"")
		self.check_lenunicode(xsc.Frag(1, None, 2, None, 3, None, 4), 4, u"1234")
		self.check_lenunicode(xsc.Frag(1, (2, 3)), 3, u"123")
		self.check_lenunicode(xsc.Frag(1, (None, None)), 1, u"1")

	def test_append(self):
		for cls in (xsc.Frag, html.div):
			node = cls()
			node.append(1)
			self.check_lenunicode(node, 1, u"1")
			node.append(2)
			self.check_lenunicode(node, 2, u"12")
			node.append()
			self.check_lenunicode(node, 2, u"12")
			node.append(3, 4)
			self.check_lenunicode(node, 4, u"1234")
			node.append(None)
			self.check_lenunicode(node, 4, u"1234")
			node.append((5, 6))
			self.check_lenunicode(node, 6, u"123456")

	def test_extend(self):
		for cls in (xsc.Frag, html.div):
			node = cls()
			node.extend([1])
			self.check_lenunicode(node, 1, u"1")
			node.extend([2])
			self.check_lenunicode(node, 2, u"12")
			node.extend([])
			self.check_lenunicode(node, 2, u"12")
			node.extend([None])
			self.check_lenunicode(node, 2, u"12")
			node.extend([3, 4])
			self.check_lenunicode(node, 4, u"1234")
			node.extend([[], [[], [5], []]])
			self.check_lenunicode(node, 5, u"12345")

	def test_insert(self):
		for cls in (xsc.Frag, html.div):
			node = cls()
			node.insert(0, 1)
			self.check_lenunicode(node, 1, u"1")
			node.insert(0, 2)
			self.check_lenunicode(node, 2, u"21")
			node.insert(0, 3, 4)
			self.check_lenunicode(node, 4, u"3421")
			node.insert(0, None)
			self.check_lenunicode(node, 4, u"3421")
			node.insert(0, (5, 6))
			self.check_lenunicode(node, 6, u"563421")

	def test_iadd(self):
		for cls in (xsc.Frag, html.div):
			node = cls()
			node += [1]
			self.check_lenunicode(node, 1, u"1")
			node += [2]
			self.check_lenunicode(node, 2, u"12")
			node += []
			self.check_lenunicode(node, 2, u"12")
			node += [None]
			self.check_lenunicode(node, 2, u"12")
			node += [3, 4]
			self.check_lenunicode(node, 4, u"1234")
			node += [[], [[], [5], []]]
			self.check_lenunicode(node, 5, u"12345")

	def test_len(self):
		for cls in (xsc.Frag, html.div):
			self.check_lenunicode(cls(), 0, u"")
			self.check_lenunicode(cls(1), 1, u"1")
			self.check_lenunicode(cls(1, 2, 3), 3, u"123")
			self.check_lenunicode(cls(None), 0, u"")
			self.check_lenunicode(cls(None, None, None), 0, u"")
			self.check_lenunicode(cls(1, None, 2, None, 3, None, 4), 4, u"1234")
			self.check_lenunicode(cls(1, (2, 3)), 3, u"123")
			self.check_lenunicode(cls(1, (None, None)), 1, u"1")

	def createattr(self):
		return html.span.Attrs.lang(
			True,
			False,
			url.URL("http://www.python.org/"),
			html.abbr(
				xml.XML10(),
				"hurz",
				specials.tab(),
				abbr.xist(),
				None,
				1,
				2.0,
				"3",
				u"4",
				(5, 6),
				[7, 8],
				html.span("gurk"),
				title="hurz"
			)
		)

	def createattrs(self):
		return html.span.Attrs(
			lang=(
				True,
				False,
				url.URL("http://www.python.org/"),
				html.abbr(
					xml.XML10(),
					"hurz",
					specials.tab(),
					abbr.xist(),
					None,
					1,
					2.0,
					"3",
					u"4",
					(5, 6),
					[7, 8],
					html.span("gurk"),
					title="hurz"
				)
			)
		)

	def createelement(self):
		return html.span(
			1,
			2,
			class_="gurk",
			id=(1, 2, (3, 4)),
			lang=(
				True,
				False,
				url.URL("http://www.python.org/"),
				html.abbr(
					xml.XML10(),
					"hurz",
					specials.tab(),
					abbr.xist(),
					None,
					1,
					2.0,
					"3",
					u"4",
					(5, 6),
					[7, 8],
					html.span("gurk"),
					title="hurz"
				)
			)
		)

	def createfrag(self):
		return xsc.Frag(
			xml.XML10(),
			html.DocTypeHTML401transitional(),
			xsc.Comment("gurk"),
			"hurz",
			specials.tab(),
			abbr.xist(),
			None,
			True,
			False,
			1,
			2.0,
			"3",
			u"4",
			(5, 6),
			[7, 8],
			html.div(
				align="left"
			),
			url.URL("http://www.python.org/"),
			html.span(
				1,
				2,
				class_="gurk",
				id=(1, 2, (3, 4)),
				lang=(
					True,
					False,
					url.URL("http://www.python.org/"),
					html.abbr(
						xml.XML10(),
						"hurz",
						specials.tab(),
						abbr.xist(),
						None,
						1,
						2.0,
						"3",
						u"4",
						(5, 6),
						[7, 8],
						html.span("gurk"),
						title="hurz"
					)
				)
			)
		)

	def allnodes(self):
		return (xsc.Null, self.createattr(), self.createattrs(), self.createelement(), self.createfrag())

	def visit(self, node):
		pass

	def test_standardmethods(self):
		for node in self.allnodes():
			node.compact()
			node.normalized()
			list(node.walk((True, xsc.enterattrs, xsc.entercontent)))
			node.visit((self.visit, xsc.enterattrs, xsc.entercontent))
			node.find((True, xsc.enterattrs, xsc.entercontent))
			node.pretty()
			node.clone()
			node.conv()
			node.normalized().compact().pretty()

	def test_standardmethods2(self):
		for node in (self.createelement(), self.createfrag()):
			node.sorted()
			node.shuffled()
			node.reversed()

	def test_stringify(self):
		for node in self.allnodes():
			unicode(node)
			str(node)
			node.asString()
			node.asBytes()

	def test_asText(self):
		for node in self.allnodes():
			node.asText()
			node.asText(monochrome=True)
			node.asText(squeezeBlankLines=True)
			node.asText(lineNumbers=True)
			node.asText(width=120)

	def test_number(self):
		node = html.div(class_=1234)
		self.assertEqual(int(node["class_"]), 1234)
		self.assertEqual(long(node["class_"]), 1234L)
		self.assertAlmostEqual(float(node["class_"]), 1234.)
		node = html.div(class_="1+1j")
		compl = complex(node["class_"])
		self.assertAlmostEqual(compl.real, 1.)
		self.assertAlmostEqual(compl.imag, 1.)

	def test_prefix(self):
		node = html.div()
		self.assertEqual(node.xmlprefix(), "html")

	def test_write(self):
		node = html.div()
		io = cStringIO.StringIO()
		node.write(io, xhtml=2)
		self.assertEqual(io.getvalue(), "<div/>")

	def test_mul(self):
		node = xsc.Frag("a")
		self.assertEqual(3*node, xsc.Frag(list("aaa")))
		self.assertEqual(node*3, xsc.Frag(list("aaa")))

		node = html.div()
		self.assertEqual(3*node, xsc.Frag(html.div(), html.div(), html.div()))
		self.assertEqual(node*3, xsc.Frag(html.div(), html.div(), html.div()))

	def test_text(self):
		node = xsc.Text("test")
		hash(node)
		self.assertEqual(len(node), 4)
		self.assertEqual(node[1], xsc.Text("e"))
		self.assertEqual(3*node, xsc.Text(3*node.content))
		self.assertEqual(node*3, xsc.Text(node.content*3))
		self.assertEqual(node[1:3], xsc.Text("es"))
		self.assertEqual(node.capitalize(), xsc.Text("Test"))
		self.assertEqual(node.center(8), xsc.Text("  test  "))
		self.assertEqual(node.count("t"), 2)
		self.assertEqual(node.endswith("st"), True)
		self.assertEqual(node.index("s"), 2)
		self.assertEqual(node.isalpha(), True)
		self.assertEqual(node.isalnum(), True)
		self.assertEqual(node.isdecimal(), False)
		self.assertEqual(node.isdigit(), False)
		self.assertEqual(node.islower(), True)
		self.assertEqual(node.isnumeric(), False)
		self.assertEqual(node.isspace(), False)
		self.assertEqual(node.istitle(), False)
		self.assertEqual(node.isupper(), False)
		self.assertEqual(node.join(xsc.Frag(list("abc"))), xsc.Frag("a", "test", "b", "test", "c"))
		self.assertEqual(node.ljust(6), xsc.Text("test  "))
		self.assertEqual(node.lower(), xsc.Text("test"))
		self.assertEqual(xsc.Text("  test").lstrip(), xsc.Text("test"))
		self.assertEqual(node.replace("s", "x"), xsc.Text("text"))
		self.assertEqual(node.rjust(6), xsc.Text("  test"))
		self.assertEqual(xsc.Text("test  ").rstrip(), xsc.Text("test"))
		self.assertEqual(node.rfind("s"), 2)
		self.assertEqual(node.rindex("s"), 2)
		self.assertEqual(node.split("e"), xsc.Frag("t", "st"))
		self.assertEqual(xsc.Text("a\nb\n").splitlines(), xsc.Frag("a", "b"))
		self.assertEqual(node.startswith("te"), True)
		self.assertEqual(xsc.Text("  test  ").strip(), xsc.Text("test"))
		self.assertEqual(node.swapcase(), xsc.Text("TEST"))
		self.assertEqual(node.title(), xsc.Text("Test"))
		self.assertEqual(node.upper(), xsc.Text("TEST"))

	def test_getsetitem(self):
		for cls in (xsc.Frag, html.div):
			for attr in ("class_", (xml, "lang")):
				node = cls(html.div(html.div({attr: "gurk"})))
				self.assertEqual(str(node[[0, 0, attr]]), "gurk")
				node[[0, 0, attr]] = "hurz"
				self.assertEqual(str(node[[0, 0, attr]]), "hurz")

	def test_mixedattrnames(self):
		class xmlns(xsc.Namespace):
			xmlname = "test"
			xmlurl = "test"

			class Attrs(xsc.Namespace.Attrs):
				class a(xsc.TextAttr, xsc.NamespaceAttrMixIn): xmlname = "A"
				class A(xsc.TextAttr, xsc.NamespaceAttrMixIn): xmlname = "a"
			class Test(xsc.Element):
				class Attrs(xsc.Element.Attrs):
					class a(xsc.TextAttr): xmlname = "A"
					class A(xsc.TextAttr): xmlname = "a"

		node = xmlns.Test(
			{
				(xmlns, "a"): "a2",
				(xmlns, "A"): "A2",
			},
			a="a",
			A="A"
		)
		for (name, value) in (
				("a", "a"),
				("A", "A"),
				((xmlns, "a"), "a2"),
				((xmlns, "A"), "A2")
			):
			self.assertEqual(unicode(node[name]), value)
			self.assertEqual(unicode(node.attrs[name]), value)
			self.assertEqual(unicode(node.attrs.get(name, xml=False)), value)
			if isinstance(name, tuple):
				name = (name[0], name[1].swapcase())
			else:
				name = name.swapcase()
			self.assertEqual(unicode(node.attrs.get(name, xml=True)), value)

	def mappedmapper(self, node, converter):
		if isinstance(node, xsc.Text):
			node = node.replace("gurk", "hurz")
		return node

	def test_conv(self):
		node = self.createfrag()
		node.conv()
		node.conv(converters.Converter())
		node.mapped(self.mappedmapper, converters.Converter())

	def test_repr(self):
		for node in self.allnodes():
			repr(node)
			for class_ in presenters.__dict__.itervalues():
				if isinstance(class_, type) and issubclass(class_, presenters.Presenter):
					node.repr(class_())
			for showLocation in (False, True):
				for showPath in (False, True):
					node.repr(presenters.TreePresenter(showLocation=showLocation, showPath=showPath))

	def node2str(self, node):
		if isinstance(node, xsc.Node):
			if isinstance(node, xsc.Text):
				return "#"
			else:
				return node.xmlname[True]
		else:
			return ".".join(map(self.node2str, node))

	def check_traverse(self, node, filter, result, filterpath=False, respath=False, skiproot=False):
		self.assertEqual(map(self.node2str, node.walk(filter, filterpath=filterpath, walkpath=respath, skiproot=skiproot)), result)

		res = []

		# The following class wrap a walk filter and transforms it into a visit filter that calls its own visit method
		class VisitFilter:
			def __init__(self, orgfilter):
				self.orgfilter = orgfilter
			def __call__(self, node):
				orgres = self.orgfilter(node)
				res = []
				for option in orgres:
					if isinstance(option, bool):
						if option:
							res.append(self.visit)
					else:
						res.append(option)
				return res
			def visit(self, node):
				res.append(node)

		node.visit(VisitFilter(filter), filterpath=filterpath, visitpath=respath, skiproot=skiproot)
		self.assertEqual(map(self.node2str, res), result)

	def test_traversal(self):
		node = html.div(html.tr(html.th("gurk"), html.td("hurz"), id=html.b(42)), class_=html.i("hinz"))

		def filtertopdown(node):
			return (isinstance(node, xsc.Element), xsc.entercontent)
		def filterbottomup(node):
			return (xsc.entercontent, isinstance(node, xsc.Element))
		def filtertopdownattrs(node):
			return (isinstance(node, xsc.Element), xsc.enterattrs, xsc.entercontent)
		def filterbottomupattrs(node):
			return (xsc.enterattrs, xsc.entercontent, isinstance(node, xsc.Element))
		def filtertopdowntextonlyinattr(path):
			for node in path:
				if isinstance(node, xsc.Attr):
					inattr = True
					break
			else:
				inattr = False
			node = path[-1]
			if isinstance(node, xsc.Element):
				return (True, xsc.enterattrs, xsc.entercontent)
			if inattr and isinstance(node, xsc.Text):
				return (True, )
			else:
				return (xsc.entercontent, )

		def filtertopdownattrwithoutcontent(node):
			if isinstance(node, xsc.Element):
				return (True, xsc.entercontent, xsc.enterattrs)
			elif isinstance(node, (xsc.Attr, xsc.Text)):
				return (True, )
			else:
				return (xsc.entercontent, )

		self.check_traverse(node, filtertopdown, ["div", "tr", "th", "td"])
		self.check_traverse(node, filtertopdown, ["tr", "th", "td"], skiproot=True)
		self.check_traverse(node, filterbottomup, ["th", "td", "tr", "div"])
		self.check_traverse(node, filterbottomup, ["th", "td", "tr"], skiproot=True)
		self.check_traverse(node, filtertopdownattrs, ["div", "i", "tr", "b", "th", "td"])
		self.check_traverse(node, filtertopdownattrs, ["tr", "b", "th", "td"], skiproot=True)
		self.check_traverse(node, filtertopdownattrs, ["div", "div.class.i", "div.tr", "div.tr.id.b", "div.tr.th", "div.tr.td"], respath=True)
		self.check_traverse(node, filtertopdownattrs, ["div.tr", "div.tr.id.b", "div.tr.th", "div.tr.td"], respath=True, skiproot=True)
		self.check_traverse(node, filterbottomupattrs, ["div.class.i", "div.tr.id.b", "div.tr.th", "div.tr.td", "div.tr", "div"], respath=True)
		self.check_traverse(node, filterbottomupattrs, ["div.tr.id.b", "div.tr.th", "div.tr.td", "div.tr"], respath=True, skiproot=True)
		self.check_traverse(node, filtertopdowntextonlyinattr, ["div", "div.class.i", "div.class.i.#", "div.tr", "div.tr.id.b", "div.tr.id.b.#", "div.tr.th", "div.tr.td"], filterpath=True, respath=True)
		self.check_traverse(node, filtertopdowntextonlyinattr, ["div.tr", "div.tr.id.b", "div.tr.id.b.#", "div.tr.th", "div.tr.td"], filterpath=True, respath=True, skiproot=True)
		self.check_traverse(node, filtertopdownattrwithoutcontent, ["div", "div.tr", "div.tr.th", "div.tr.th.#", "div.tr.td", "div.tr.td.#", "div.tr.id", "div.class"], respath=True)
		self.check_traverse(node, filtertopdownattrwithoutcontent, ["div.tr", "div.tr.th", "div.tr.th.#", "div.tr.td", "div.tr.td.#", "div.tr.id"], respath=True, skiproot=True)

	def test_walk(self):
		node = self.createfrag()
		def filter1(node):
			return (True, xsc.enterattrs, xsc.entercontent, True)
		def filter2(path):
			return (True, xsc.enterattrs, xsc.entercontent, True)

		list(node.walk((True, xsc.entercontent, True)))
		list(node.walk((True, xsc.entercontent, True), walkpath=True))
		list(node.walk(filter1))
		list(node.walk(filter1, walkpath=True))
		list(node.walk(filter2, filterpath=True))
		list(node.walk(filter2, filterpath=True, walkpath=True))

	def test_visit(self):
		node = self.createfrag()
		def dummy1(node):
			pass
		def dummy2(path):
			pass
		def filter1(node):
			return (dummy1, xsc.enterattrs, xsc.entercontent, dummy1)
		def filter2(path):
			return (dummy1, xsc.enterattrs, xsc.entercontent, dummy1)

		node.visit((dummy1, xsc.enterattrs, xsc.entercontent, dummy1))
		node.visit((dummy2, xsc.enterattrs, xsc.entercontent, dummy2), visitpath=True)
		node.visit(filter1)
		node.visit(filter1, visitpath=True)
		node.visit(filter2, filterpath=True)
		node.visit(filter2, filterpath=True, visitpath=True)

	def test_locationeq(self):
		l1 = xsc.Location(sysID="gurk", pubID="http://gurk.com", lineNumber=42, columnNumber=666)
		l2 = xsc.Location(sysID="gurk", pubID="http://gurk.com", lineNumber=42, columnNumber=666)
		l3 = xsc.Location(sysID="hurz", pubID="http://gurk.com", lineNumber=42, columnNumber=666)
		l4 = xsc.Location(sysID="gurk", pubID="http://hurz.com", lineNumber=42, columnNumber=666)
		l5 = xsc.Location(sysID="gurk", pubID="http://gurk.com", lineNumber=43, columnNumber=666)
		l6 = xsc.Location(sysID="gurk", pubID="http://gurk.com", lineNumber=43, columnNumber=667)
		l7 = xsc.Location(sysID="gurk", pubID="http://gurk.com")
		self.assertEqual(l1, l2)
		self.assertNotEqual(l1, l3)
		self.assertNotEqual(l1, l4)
		self.assertNotEqual(l1, l5)
		self.assertNotEqual(l1, l6)
		self.assertNotEqual(l1, l7)

	def test_locationoffset(self):
		l1 = xsc.Location(sysID="gurk", pubID="http://gurk.com", lineNumber=42, columnNumber=666)
		self.assertEqual(l1, l1.offset(0))
		l2 = l1.offset(1)
		self.assertEqual(l1.getSystemId(), l2.getSystemId())
		self.assertEqual(l1.getPublicId(), l2.getPublicId())
		self.assertEqual(l1.getLineNumber()+1, l2.getLineNumber())

	def check_namespace(self, module):
		for obj in module.__dict__.values():
			if isinstance(obj, type) and issubclass(obj, xsc.Node):
				node = obj()
				if isinstance(node, xsc.Element):
					for (attrname, attrvalue) in node.attrs.alloweditems():
						if attrvalue.required:
							if attrvalue.values:
								node[attrname] = attrvalue.values[0]
							else:
								node[attrname] = "foo"
				node.conv().asBytes()

	def test_html(self):
		self.check_namespace(html)

	def test_ihtml(self):
		self.check_namespace(ihtml)

	def test_wml(self):
		self.check_namespace(wml)

	def test_css(self):
		self.check_namespace(css)

	def test_specials(self):
		self.check_namespace(css)

	def test_form(self):
		self.check_namespace(css)

	def test_meta(self):
		self.check_namespace(css)

	def test_htmlspecials(self):
		self.check_namespace(css)

	def test_cssspecials(self):
		self.check_namespace(css)

	def test_docbook(self):
		self.check_namespace(css)

	escapeInput = u"".join([unichr(i) for i in xrange(1000)] + [unichr(i) for i in xrange(sys.maxunicode-10, sys.maxunicode+1)])

	def test_helpersescapetext(self):
		escapeOutput = []
		for c in self.escapeInput:
			if c==u"&":
				escapeOutput.append(u"&amp;")
			elif c==u"<":
				escapeOutput.append(u"&lt;")
			elif c==u">":
				escapeOutput.append(u"&gt;")
			else:
				escapeOutput.append(c)
		escapeOutput = "".join(escapeOutput)
		self.assertEqual(helpers.escapetext(self.escapeInput), escapeOutput)

	def test_helpersescapeattr(self):
		escapeOutput = []
		for c in self.escapeInput:
			if c==u"&":
				escapeOutput.append(u"&amp;")
			elif c==u"<":
				escapeOutput.append(u"&lt;")
			elif c==u">":
				escapeOutput.append(u"&gt;")
			elif c==u'"':
				escapeOutput.append(u"&quot;")
			else:
				escapeOutput.append(c)
		escapeOutput = "".join(escapeOutput)
		self.assertEqual(helpers.escapeattr(self.escapeInput), escapeOutput)

	def test_helperxmlcharrefreplace(self):
		escapeOutput = []
		for c in self.escapeInput:
			try:
				c.encode("ascii")
				escapeOutput.append(c)
			except UnicodeError:
				escapeOutput.append(u"&#%d;" % ord(c))
		escapeOutput = u"".join(escapeOutput)
		self.assertEqual(helpers.xmlcharrefreplace(self.escapeInput, "ascii"), escapeOutput)

	def test_helpercssescapereplace(self):
		escapeOutput = []
		for c in self.escapeInput:
			try:
				c.encode("ascii")
				escapeOutput.append(c)
			except UnicodeError:
				escapeOutput.append((u"\\%x" % ord(c)).upper())
		escapeOutput = u"".join(escapeOutput)
		self.assertEqual(helpers.cssescapereplace(self.escapeInput, "ascii"), escapeOutput)

	def test_attrsclone(self):
		class newa(html.a):
			def convert(self, converter):
				attrs = self.attrs.clone()
				attrs["href"].insert(0, "foo")
				e = html.a(self.content, attrs)
				return e.convert(converter)
		e = newa("gurk", href="hurz")
		e = e.conv().conv()
		self.assertEqual(unicode(e["href"]), "foohurz")
		self.assertEqual(str(e["href"]), "foohurz")

	def test_csspublish(self):
		e = css.css(
			css.atimport("http://www.gurk.org/gurk.css"),
			css.atimport("http://www.gurk.org/print.css", media="print"),
			css.atimport("http://www.gurk.org/screen.css", media="screen"),
			css.rule(
				css.sel("body"),
				css.font_family("Verdana, sans-serif"),
				css.font_size("10pt"),
				css.background_color("#000"),
				css.color("#fff")
			),
			css.atmedia(
				css.rule(
					css.sel("div, p"),
					css.font_family("Verdana, sans-serif"),
					css.font_size("10pt"),
					css.background_color("#000"),
					css.color("#fff")
				),
				media="print"
			)
		)
		e.asBytes()

	def test_namespace(self):
		self.assertEqual(xsc.amp.xmlname, (u"amp", u"amp"))
		self.assert_(xsc.amp.xmlns is None)
		self.assertEqual(xsc.amp.xmlprefix(), None)

		self.assertEqual(html.uuml.xmlname, (u"uuml", u"uuml"))
		self.assert_(html.uuml.xmlns is html)
		self.assertEqual(html.uuml.xmlprefix(), "html")

		self.assertEqual(html.a.Attrs.class_.xmlname, (u"class_", u"class"))
		self.assert_(html.a.Attrs.class_.xmlns is None)

		self.assertEqual(xml.Attrs.lang.xmlname, (u"lang", u"lang"))
		self.assert_(xml.Attrs.lang.xmlns is xml)
		self.assertEqual(xml.Attrs.lang.xmlprefix(), "xml")

	def test_attributes(self):
		node = html.h1("gurk", {(xml, "lang"): "de"}, lang="de")
		self.assert_(node.attrs.has("lang"))
		self.assert_(node.attrs.has((xml, "lang")))

	def check_attributekeysvaluesitems(self, node, xml, attrname, attrvalue):
		self.assertEquals(node.attrs.allowedkeys(xml=xml), [attrname])
		iter = node.attrs.iterallowedkeys(xml=xml)
		self.assertEquals(iter.next(), attrname)
		self.assertRaises(StopIteration, iter.next)

		self.assertEquals(node.attrs.allowedvalues(), [node.Attrs.attr_])
		iter = node.attrs.iterallowedvalues()
		self.assertEquals(iter.next(), node.Attrs.attr_)
		self.assertRaises(StopIteration, iter.next)

		self.assertEquals(node.attrs.alloweditems(xml=xml), [(attrname, node.Attrs.attr_)])
		iter = node.attrs.iteralloweditems(xml=xml)
		self.assertEquals(iter.next(), (attrname, node.Attrs.attr_))
		self.assertRaises(StopIteration, iter.next)

		if attrvalue:
			self.assertEquals(node.attrs.keys(xml=xml), [attrname])
			iter = node.attrs.iterkeys(xml=xml)
			self.assertEquals(iter.next(), attrname)
			self.assertRaises(StopIteration, iter.next)
		else:
			self.assertEquals(node.attrs.keys(xml=xml), [])
			iter = node.attrs.iterkeys(xml=xml)
			self.assertRaises(StopIteration, iter.next)

		if attrvalue:
			res = node.attrs.values()
			self.assertEquals(len(res), 1)
			self.assertEquals(res[0].__class__, node.Attrs.attr_)
			self.assertEquals(unicode(res[0]), attrvalue)
			iter = node.attrs.itervalues()
			res = iter.next()
			self.assertEquals(res.__class__, node.Attrs.attr_)
			self.assertEquals(unicode(res), attrvalue)
			self.assertRaises(StopIteration, iter.next)
		else:
			res = node.attrs.values()
			self.assertEquals(len(res), 0)
			iter = node.attrs.itervalues()
			self.assertRaises(StopIteration, iter.next)

		if attrvalue:
			res = node.attrs.items(xml=xml)
			self.assertEquals(len(res), 1)
			self.assertEquals(res[0][0], attrname)
			self.assertEquals(res[0][1].__class__, node.Attrs.attr_)
			self.assertEquals(unicode(res[0][1]), attrvalue)
			iter = node.attrs.iteritems(xml=xml)
			res = iter.next()
			self.assertEquals(res[0], attrname)
			self.assertEquals(res[1].__class__, node.Attrs.attr_)
			self.assertEquals(unicode(res[1]), attrvalue)
			self.assertRaises(StopIteration, iter.next)
		else:
			res = node.attrs.items(xml=xml)
			self.assertEquals(len(res), 0)
			iter = node.attrs.iteritems(xml=xml)
			self.assertRaises(StopIteration, iter.next)

	def test_attributekeysvaluesitems(self):
		class Test1(xsc.Element):
			class Attrs(xsc.Element.Attrs):
				class attr_(xsc.TextAttr):
					xmlname = "attr"
					default = 42
		class Test2(xsc.Element):
			class Attrs(xsc.Element.Attrs):
				class attr_(xsc.TextAttr):
					xmlname = "attr"

		for (xml, attrname) in ((False, u"attr_"), (True, u"attr")):
			self.check_attributekeysvaluesitems(Test1(), xml, attrname, u"42")
			self.check_attributekeysvaluesitems(Test1(attr_=17), xml, attrname, u"17")
			self.check_attributekeysvaluesitems(Test1(attr_=None), xml, attrname, None)

			self.check_attributekeysvaluesitems(Test2(), xml, attrname, None)
			self.check_attributekeysvaluesitems(Test2(attr_=17), xml, attrname, u"17")
			self.check_attributekeysvaluesitems(Test2(attr_=None), xml, attrname, None)

	def test_attributeswithout(self):
		# Use a sub namespace of xml to test the issubclass checks
		class xml2(xml):
			class Attrs(xml.Attrs):
				class lang(xml.Attrs.lang):
					default = 42

		node = html.h1("gurk",
			{(xml2, "space"): 1, (xml2, "lang"): "de", (xml2, "base"): "http://www.livinglogic.de/"},
			lang="de",
			style="color: #fff",
			align="right",
			title="gurk",
			class_="important",
			id=42,
			dir="ltr"
		)
		keys = node.attrs.keys()
		keys.sort()
		keys.remove("lang")

		keys1 = node.attrs.without(["lang"]).keys()
		keys1.sort()
		self.assertEqual(keys, keys1)

		keys.remove((xml2, "space"))
		keys2 = node.attrs.without(["lang", (xml, "space")]).keys()
		keys2.sort()
		self.assertEqual(keys, keys2)

		keys.remove((xml2, "lang"))
		keys.remove((xml2, "base"))
		keys3 = node.attrs.without(["lang"], [xml]).keys()
		keys3.sort()
		self.assertEqual(keys, keys3)

		# Check that non existing attrs are handled correctly
		keys4 = node.attrs.without(["lang", "src"], keepglobals=False).keys()
		keys4.sort()
		self.assertEqual(keys, keys4)

	def test_attributeswith(self):
		# Use a sub namespace of xml to test the issubclass checks
		class xml2(xml):
			class Attrs(xml.Attrs):
				class lang(xml.Attrs.lang):
					default = 42

		node = html.h1("gurk",
			{(xml2, "space"): 1, (xml2, "lang"): "de"},
			lang="de",
			align="right"
		)
		keys = node.attrs.keys()
		keys.sort()
		keys.remove("lang")

		self.assertEquals(node.attrs.with([u"lang"]).keys(), [u"lang"])

		keys1 = node.attrs.with([u"lang", u"align"]).keys()
		keys1.sort()
		self.assertEqual(keys1, [u"align", u"lang"])

		keys = [u"lang", (xml2, u"lang")]
		keys.sort()
		keys2 = node.attrs.with(keys).keys()
		keys2.sort()
		self.assertEqual(keys2, keys)

		keys = [u"lang", (xml2, u"lang"), (xml2, u"space")]
		keys.sort()
		keys3 = node.attrs.with([u"lang"], [xml]).keys()
		keys3.sort()
		self.assertEqual(keys3, keys)

	def test_defaultattributes(self):
		class Test(xsc.Element):
			class Attrs(xsc.Element.Attrs):
				class withdef(xsc.TextAttr):
					default = 42
				class withoutdef(xsc.TextAttr):
					pass
		node = Test()
		self.assert_(node.attrs.has("withdef"))
		self.assert_(not node.attrs.has("withoutdef"))
		self.assertRaises(errors.IllegalAttrError, node.attrs.has, "illegal")
		node = Test(withdef=None)
		self.assert_(not node.attrs.has("withdef"))

	def check_listiter(self, listexp, *lists):
		for l in lists:
			count = 0
			for item in l:
				self.assert_(item in listexp)
				count += 1
			self.assertEqual(count, len(listexp))

	def test_attributedictmethods(self):
		class Test(xsc.Element):
			class Attrs(xsc.Element.Attrs):
				class withdef(xsc.TextAttr):
					default = 42
				class withoutdef(xsc.TextAttr):
					pass
				class another(xsc.URLAttr):
					pass

		node = Test(withoutdef=42)

		self.check_listiter(
			[ "withdef", "withoutdef" ],
			node.attrs.keys(),
			node.attrs.iterkeys()
		)
		self.check_listiter(
			[ Test.Attrs.withdef(42), Test.Attrs.withoutdef(42)],
			node.attrs.values(),
			node.attrs.itervalues()
		)
		self.check_listiter(
			[ ("withdef", Test.Attrs.withdef(42)), ("withoutdef", Test.Attrs.withoutdef(42)) ],
			node.attrs.items(),
			node.attrs.iteritems()
		)

		self.check_listiter(
			[ "another", "withdef", "withoutdef" ],
			node.attrs.allowedkeys(),
			node.attrs.iterallowedkeys()
		)
		self.check_listiter(
			[ Test.Attrs.another, Test.Attrs.withdef, Test.Attrs.withoutdef ],
			node.attrs.allowedvalues(),
			node.attrs.iterallowedvalues()
		)
		self.check_listiter(
			[ ("another", Test.Attrs.another), ("withdef", Test.Attrs.withdef), ("withoutdef", Test.Attrs.withoutdef) ],
			node.attrs.alloweditems(),
			node.attrs.iteralloweditems()
		)

	def test_fragattrdefault(self):
		class testelem(xsc.Element):
			class Attrs(xsc.Element.Attrs):
				class testattr(xsc.TextAttr):
					default = 42

		node = testelem()
		self.assertEquals(unicode(node["testattr"]), "42")
		self.assertEquals(unicode(node.conv()["testattr"]), "42")

		node["testattr"].clear()
		self.assert_(not node.attrs.has("testattr"))
		self.assert_(not node.conv().attrs.has("testattr"))

		node = testelem(testattr=23)
		self.assertEquals(unicode(node["testattr"]), "23")
		self.assertEquals(unicode(node.conv()["testattr"]), "23")

		del node["testattr"]
		self.assertEquals(unicode(node["testattr"]), "42")
		self.assertEquals(unicode(node.conv()["testattr"]), "42")

		node["testattr"] = None
		self.assert_(not node.attrs.has("testattr"))
		self.assert_(not node.conv().attrs.has("testattr"))

		node = testelem(testattr=None)
		self.assert_(not node.attrs.has("testattr"))
		self.assert_(not node.conv().attrs.has("testattr"))

	def test_checkisallowed(self):
		class testelem(xsc.Element):
			class Attrs(xsc.Element.Attrs):
				class testattr(xsc.TextAttr):
					pass

		class testelem2(testelem):
			pass

		class testelem3(testelem2):
			class Attrs(testelem2.Attrs):
				class testattr3(xsc.TextAttr):
					pass

		class testelem4(testelem3):
			class Attrs(testelem3.Attrs):
				testattr = None

		node = testelem()
		self.assertEquals(node.attrs.isallowed("testattr"), True)
		self.assertEquals(node.attrs.isallowed("notestattr"), False)

		node = testelem2()
		self.assertEquals(node.attrs.isallowed("testattr"), True)
		self.assertEquals(node.attrs.isallowed("notestattr"), False)

		node = testelem3()
		self.assertEquals(node.attrs.isallowed("testattr"), True)
		self.assertEquals(node.attrs.isallowed("testattr3"), True)

		node = testelem4()
		self.assertEquals(node.attrs.isallowed("testattr"), False)
		self.assertEquals(node.attrs.isallowed("testattr3"), True)

	def test_withsep(self):
		for class_ in (xsc.Frag, html.div):
			node = class_(1,2,3)
			self.assertEquals(unicode(node.withsep(",")), u"1,2,3")
			node = class_(1)
			self.assertEquals(unicode(node.withsep(",")), u"1")
			node = class_()
			self.assertEquals(unicode(node.withsep(",")), u"")

	def test_autoinherit(self):
		class NS1(xsc.Namespace):
			xmlname = "test"
			xmlurl = "test"
			class foo(xsc.Element):
				empty = True
				def convert(self, converter):
					e = self.xmlns.bar()
					return e.convert(converter)
			class bar(xsc.Entity):
				def convert(self, converter):
					return xsc.Text(17)

		class NS2(NS1):
			xmlname = "test"
			class bar(xsc.Entity):
				def convert(self, converter):
					return xsc.Text(23)

		self.assertEquals(unicode(NS1.foo().conv()), u"17")
		self.assertEquals(unicode(NS2.foo().conv()), u"23")

	def check_nskeysvaluesitems(self, ns, method, resname, resclass):
		self.assertEquals(getattr(ns, method + "keys")(xml=False), [resname])
		self.assertEquals(getattr(ns, method + "keys")(xml=True), [resname[:-1]])

		self.assertEquals(getattr(ns, method + "values")(), [resclass])

		self.assertEquals(getattr(ns, method + "items")(xml=False), [(resname, resclass)])
		self.assertEquals(getattr(ns, method + "items")(xml=True), [(resname[:-1], resclass)])

	def test_nskeysvaluesitems(self):
		class NS(xsc.Namespace):
			xmlname = "test"
			class el_(xsc.Element):
				xmlname = "el"
			class en_(xsc.Entity):
				xmlname = "en"
			class pi_(xsc.ProcInst):
				xmlname = "pi"
			class cr_(xsc.CharRef):
				xmlname = "cr"
				codepoint = 0x4242

		self.check_nskeysvaluesitems(NS, "element", "el_", NS.el_)

		keys = NS.entitykeys(xml=False)
		self.assertEqual(len(keys), 2)
		self.assert_("en_" in keys)
		self.assert_("cr_" in keys)
		keys = NS.entitykeys(xml=True)
		self.assertEqual(len(keys), 2)
		self.assert_("en" in keys)
		self.assert_("cr" in keys)

		values = NS.entityvalues()
		self.assertEqual(len(values), 2)
		self.assert_(NS.en_ in values)
		self.assert_(NS.cr_ in values)

		items = NS.entityitems(xml=False)
		self.assertEqual(len(items), 2)
		self.assert_(("en_", NS.en_) in items)
		self.assert_(("cr_", NS.cr_) in items)
		items = NS.entityitems(xml=True)
		self.assertEqual(len(items), 2)
		self.assert_(("en", NS.en_) in items)
		self.assert_(("cr", NS.cr_) in items)

		self.check_nskeysvaluesitems(NS, "procinst", "pi_", NS.pi_)

		self.check_nskeysvaluesitems(NS, "charref", "cr_", NS.cr_)

	def test_allowedattr(self):
		self.assertEquals(html.a.Attrs.allowedattr("href"), html.a.Attrs.href)
		self.assertRaises(errors.IllegalAttrError, html.a.Attrs.allowedattr, "gurk")
		self.assertEquals(html.a.Attrs.allowedattr((xml, "lang")), xml.Attrs.lang)

	def test_plaintableattrs(self):
		e = htmlspecials.plaintable(border=3)
		self.assert_(isinstance(e["border"], html.table.Attrs.border))
		self.assert_(isinstance(e["cellpadding"], html.table.Attrs.cellpadding))
		e = e.conv()
		self.assert_(isinstance(e["border"], html.table.Attrs.border))
		self.assert_(isinstance(e["cellpadding"], html.table.Attrs.cellpadding))

	def test_attrupdate(self):
		node = html.a(href="gurk", class_="hurz")
		node.attrs.update({"href": "gurk2", "id": 42})
		self.assertEquals(unicode(node["href"]), u"gurk2")
		self.assertEquals(unicode(node["id"]), u"42")

		node = html.a(href="gurk", class_="hurz")
		node.attrs.updatenew({"href": "gurk2", "id": 42})
		self.assertEquals(unicode(node["href"]), u"gurk")
		self.assertEquals(unicode(node["id"]), u"42")

		node = html.a(href="gurk", class_="hurz")
		node.attrs.updateexisting({"href": "gurk2", "id": 42})
		self.assertEquals(unicode(node["href"]), u"gurk2")
		self.assertEquals(node.attrs.has("id"), False)

	def test_classrepr(self):
		repr(xsc.Base)
		repr(xsc.Node)
		repr(xsc.Element)
		repr(xsc.ProcInst)
		repr(xsc.Entity)
		repr(xsc.CharRef)
		repr(xsc.Element.Attrs)
		repr(xml.Attrs)
		repr(xml.Attrs.lang)

	def test_itemslice(self):
		for cls in (xsc.Frag, html.div):
			# __get(item|slice)__
			e = cls(range(6))
			self.assertEqual(e[2], xsc.Text(2))
			self.assertEqual(e[-1], xsc.Text(5))
			self.assertEqual(e[:], e)
			self.assertEqual(e[:2], cls(0, 1))
			self.assertEqual(e[-2:], cls(4, 5))
			self.assertEqual(e[::2], cls(0, 2, 4))
			self.assertEqual(e[1::2], cls(1, 3, 5))
			self.assertEqual(e[::-1], cls(range(5, -1, -1)))
			e[1] = 10
			self.assertEqual(e, cls(0, 10, 2, 3, 4, 5))
			e[1] = None
			self.assertEqual(e, cls(0, 2, 3, 4, 5))
			e[1] = ()
			self.assertEqual(e, cls(0, 3, 4, 5))

			# __set(item|slice)__
			e = cls(range(6))
			e[-1] = None
			self.assertEqual(e, cls(0, 1, 2, 3, 4))

			e = cls(range(6))
			e[1:5] = (100, 200)
			self.assertEqual(e, cls(0, 100, 200, 5))

			e = cls(range(6))
			e[:] = (100, 200)
			self.assertEqual(e, cls(100, 200))

			e = cls(range(6))
			e[::2] = (100, 120, 140)
			self.assertEqual(e, cls(100, 1, 120, 3, 140, 5))

			e = cls(range(6))
			e[1::2] = (110, 130, 150)
			self.assertEqual(e, cls(0, 110, 2, 130, 4, 150))

			e = cls(range(6))
			e[::-1] = range(6)
			self.assertEqual(e, cls(range(5, -1, -1)))

			# __del(item|slice)__
			e = cls(range(6))
			del e[0]
			self.assertEqual(e, cls(1, 2, 3, 4, 5))
			del e[-1]
			self.assertEqual(e, cls(1, 2, 3, 4))

			e = cls(range(6))
			del e[1:5]
			self.assertEqual(e, cls(0, 5))

			e = cls(range(6))
			del e[2:]
			self.assertEqual(e, cls(0, 1))

			e = cls(range(6))
			del e[-2:]
			self.assertEqual(e, cls(0, 1, 2, 3))

			e = cls(range(6))
			del e[:2]
			self.assertEqual(e, cls(2, 3, 4, 5))

			e = cls(range(6))
			del e[:-2]
			self.assertEqual(e, cls(4, 5))

			e = cls(range(6))
			del e[:]
			self.assertEqual(e, cls())

			e = cls(range(6))
			del e[::2]
			self.assertEqual(e, cls(1, 3, 5))

			e = cls(range(6))
			del e[1::2]
			self.assertEqual(e, cls(0, 2, 4))

		e = html.div(range(6), id=42)
		self.assertEqual(e[2], xsc.Text(2))
		self.assertEqual(e[-1], xsc.Text(5))
		self.assertEqual(e[:], e)
		self.assertEqual(e[:2], cls(0, 1, id=42))
		self.assertEqual(e[-2:], cls(4, 5, id=42))
		self.assertEqual(e[::2], cls(0, 2, 4, id=42))
		self.assertEqual(e[1::2], cls(1, 3, 5, id=42))
		self.assertEqual(e[::-1], cls(range(5, -1, -1), id=42))

	def test_clone(self):
		for cls in (xsc.Frag, html.div):
			e = html.div(1)

			src = cls(1, e, e)

			dst = src.clone()
			self.assert_(src is not dst)
			self.assert_(src[0] is dst[0])
			self.assert_(src[1] is not dst[1])
			self.assert_(dst[1] is not dst[2])

			e.append(e) # create a cycle

			dst = src.copy()
			self.assert_(src is not dst)
			self.assert_(src[0] is dst[0])
			self.assert_(src[1] is dst[1])
			self.assert_(dst[1] is dst[2])

			dst = src.deepcopy()
			self.assert_(src is not dst)
			self.assert_(src[0] is dst[0])
			self.assert_(src[1] is not dst[1])
			self.assert_(dst[1] is dst[2])

		e = html.div(id=(17, html.div(23), 42))
		for src in (e, e.attrs):
			dst = src.clone()
			self.assert_(src["id"] is not dst["id"])
			self.assert_(src["id"][0] is dst["id"][0])
			self.assert_(src["id"][1] is not dst["id"][1])

		e["id"][1] = e # create a cycle
		e["id"][2] = e # create a cycle
		for src in (e, e.attrs):
			dst = src.copy()
			self.assert_(src["id"] is dst["id"])
			self.assert_(src["id"][0] is dst["id"][0])
			self.assert_(src["id"][1] is dst["id"][1])
			self.assert_(dst["id"][1] is dst["id"][2])
			dst = src.deepcopy()
			self.assert_(src["id"] is not dst["id"])
			self.assert_(src["id"][0] is dst["id"][0])
			self.assert_(src["id"][1] is not dst["id"][1])
			self.assert_(dst["id"][1] is dst["id"][2])

	def check_sortreverse(self, method):
		for class_ in (xsc.Frag, html.div):
			node = class_(3, 2, 1)
			node2 = getattr(node, method)()
			self.assertEqual(node, class_(3, 2, 1))
			self.assertEqual(node2, class_(1, 2, 3))

	def test_sorted(self):
		self.check_sortreverse("sorted")

	def test_reversed(self):
		self.check_sortreverse("reversed")

class PublishTest(unittest.TestCase):
	def test_publishelement(self):
		node = html.html()

		prefixes = xsc.Prefixes()
		prefixes.addPrefixMapping("h", html)

		self.assertEquals(node.asBytes(), "<html></html>")
		self.assertEquals(node.asBytes(prefixes=prefixes, elementmode=1), "<h:html></h:html>")
		self.assertEquals(node.asBytes(prefixes=prefixes, elementmode=2), """<h:html xmlns:h="http://www.w3.org/1999/xhtml"></h:html>""")

		prefixes = xsc.Prefixes()
		prefixes.addPrefixMapping(None, html)

		self.assertEquals(node.asBytes(prefixes=prefixes, elementmode=2), """<html xmlns="http://www.w3.org/1999/xhtml"></html>""")

	def test_publishentity(self):
		node = abbr.xml()

		prefixes = xsc.Prefixes()
		prefixes.addPrefixMapping("a", abbr)
		prefixes.addPrefixMapping("s", specials)

		self.assertEquals(node.asBytes(), "&xml;")
		self.assertEquals(node.asBytes(prefixes=prefixes, entitymode=1), "&a:xml;")
		self.assertEquals(node.asBytes(prefixes=prefixes, entitymode=2), """<wrap entityns:a="http://xmlns.livinglogic.de/xist/ns/abbr">&a:xml;</wrap>""")
		self.assertEquals(node.asBytes(prefixes=prefixes, elementmode=2, entitymode=2), """<s:wrap entityns:a="http://xmlns.livinglogic.de/xist/ns/abbr" xmlns:s="http://xmlns.livinglogic.de/xist/ns/specials">&a:xml;</s:wrap>""")

		prefixes = xsc.Prefixes()
		prefixes.addPrefixMapping(None, abbr)
		prefixes.addPrefixMapping("s", specials)

		self.assertEquals(node.asBytes(prefixes=prefixes, entitymode=2), """<wrap entityns="http://xmlns.livinglogic.de/xist/ns/abbr">&xml;</wrap>""")
		self.assertEquals(node.asBytes(prefixes=prefixes, elementmode=2, entitymode=2), """<s:wrap entityns="http://xmlns.livinglogic.de/xist/ns/abbr" xmlns:s="http://xmlns.livinglogic.de/xist/ns/specials">&xml;</s:wrap>""")

	def test_publishprocinst(self):
		node = php.php("x")

		prefixes = xsc.Prefixes()
		prefixes.addPrefixMapping("p", php)
		prefixes.addPrefixMapping("s", specials)

		self.assertEquals(node.asBytes(), "<?php x?>")
		self.assertEquals(node.asBytes(prefixes=prefixes, procinstmode=1), "<?p:php x?>")
		self.assertEquals(node.asBytes(prefixes=prefixes, procinstmode=2), """<wrap procinstns:p="http://www.php.net/"><?p:php x?></wrap>""")
		# FIXME this depends on dict iteration order
		self.assertEquals(node.asBytes(prefixes=prefixes, elementmode=2, procinstmode=2), """<s:wrap procinstns:p="http://www.php.net/" xmlns:s="http://xmlns.livinglogic.de/xist/ns/specials"><?p:php x?></s:wrap>""")

		prefixes = xsc.Prefixes()
		prefixes.addPrefixMapping(None, php)
		prefixes.addPrefixMapping("s", specials)

		self.assertEquals(node.asBytes(prefixes=prefixes, procinstmode=2), """<wrap procinstns="http://www.php.net/"><?php x?></wrap>""")
		# FIXME this depends on dict iteration order
		self.assertEquals(node.asBytes(prefixes=prefixes, elementmode=2, procinstmode=2), """<s:wrap procinstns="http://www.php.net/" xmlns:s="http://xmlns.livinglogic.de/xist/ns/specials"><?php x?></s:wrap>""")

	def test_publishboolattr(self):
		node = html.td("?", nowrap=None)
		self.assertEquals(node.asBytes(xhtml=0), """<td>?</td>""")
		node = html.td("?", nowrap=True)
		self.assertEquals(node.asBytes(xhtml=0), """<td nowrap>?</td>""")
		self.assertEquals(node.asBytes(xhtml=1), """<td nowrap="nowrap">?</td>""")
		self.assertEquals(node.asBytes(xhtml=2), """<td nowrap="nowrap">?</td>""")

	def test_publishurlattr(self):
		node = html.link(href=None)
		self.assertEquals(node.asBytes(xhtml=1), """<link />""")
		node = html.link(href="root:gurk.html")
		self.assertEquals(node.asBytes(xhtml=1), """<link href="root:gurk.html" />""")
		self.assertEquals(node.asBytes(xhtml=1, base="root:gurk.html"), """<link href="" />""")
		self.assertEquals(node.asBytes(xhtml=1, base="root:hurz.html"), """<link href="gurk.html" />""")

	def test_publishstyleattr(self):
		node = html.div(style=None)
		self.assertEquals(node.asBytes(xhtml=1), """<div></div>""")
		node = html.div(style="background-image: url(root:gurk.html)")
		self.assertEquals(node.asBytes(xhtml=1), """<div style="background-image: url(root:gurk.html)"></div>""")
		self.assertEquals(node.asBytes(xhtml=1, base="root:gurk.html"), """<div style="background-image: url()"></div>""")
		self.assertEquals(node.asBytes(xhtml=1, base="root:hurz.html"), """<div style="background-image: url(gurk.html)"></div>""")

	def test_publishempty(self):
		node = xsc.Frag(html.br(), html.div())
		self.assertEquals(node.asBytes(xhtml=0), """<br><div></div>""")
		self.assertEquals(node.asBytes(xhtml=1), """<br /><div></div>""")
		self.assertEquals(node.asBytes(xhtml=2), """<br/><div/>""")

	def test_publishescaped(self):
		s = u"""<&'"\xff>"""
		node = xsc.Text(s)
		self.assertEquals(node.asBytes(encoding="ascii"), """&lt;&amp;'"&#255;&gt;""")
		node = html.span(class_=s)
		self.assertEquals(node.asBytes(encoding="ascii", xhtml=2), """<span class="&lt;&amp;'&quot;&#255;&gt;"/>""")

	def createns(self):
		class xmlns(xsc.Namespace):
			xmlname = "gurk"
			xmlurl = "http://www.gurk.com/"
			class foo(xsc.Element):
				pass
			class bar(xsc.Element):
				pass
		return xmlns

	def test_nsupdate(self):
		class ns1:
			class foo(xsc.Element):
				pass
			class bar(xsc.Element):
				pass
			class foo2(xsc.Element):
				pass
			class bar2(xsc.Element):
				pass
		class ns2:
			class foo(xsc.Element):
				pass
			class bar(xsc.Element):
				pass
			class foo2(xsc.Element):
				pass
			class bar2(xsc.Element):
				pass
		a = [ {"foo": ns.foo, "bar": ns.bar, "foo2": ns.foo2, "bar2": ns.bar2} for ns in (ns1, ns2) ]

		ns = self.createns()
		ns.update(*a)
		self.assertEquals(ns.element("foo"), ns2.foo)
		self.assertEquals(ns.element("bar"), ns2.bar)
		self.assertEquals(ns.element("foo2"), ns2.foo2)
		self.assertEquals(ns.element("bar2"), ns2.bar2)

		ns = self.createns()
		ns.updatenew(*a)
		self.assertEquals(ns.element("foo"), ns.foo)
		self.assertEquals(ns.element("bar"), ns.bar)
		self.assertEquals(ns.element("foo2"), ns2.foo2)
		self.assertEquals(ns.element("bar2"), ns2.bar2)

		ns = self.createns()
		ns.updateexisting(*a)
		self.assertEquals(ns.element("foo"), ns2.foo)
		self.assertEquals(ns.element("bar"), ns2.bar)
		self.assertRaises(errors.IllegalElementError, ns.element, "foo2")
		self.assertRaises(errors.IllegalElementError, ns.element, "bar2")

class ParseTest(unittest.TestCase):
	def test_parselocationsgmlop(self):
		node = parsers.parseString("<z>gurk&amp;hurz&#42;hinz&#x666;hunz</z>", parser=parsers.SGMLOPParser())
		self.assertEqual(len(node), 1)
		self.assertEqual(len(node[0]), 1)
		self.assertEqual(node[0][0].startloc.getSystemId(), "STRING")
		self.assertEqual(node[0][0].startloc.getLineNumber(), 1)

	def test_parselocationexpat(self):
		node = parsers.parseString("<z>gurk&amp;hurz&#42;hinz&#x666;hunz</z>", parser=parsers.ExpatParser())
		self.assertEqual(len(node), 1)
		self.assertEqual(len(node[0]), 1)
		self.assertEqual(node[0][0].startloc.getSystemId(), "STRING")
		self.assertEqual(node[0][0].startloc.getLineNumber(), 1)
		self.assertEqual(node[0][0].startloc.getColumnNumber(), 3)

	def test_nsparse(self):
		xml = """
			<x:a>
				<x:a xmlns:x='http://www.w3.org/1999/xhtml'>
					<x:a xmlns:x='http://www.nttdocomo.co.jp/imode'>gurk</x:a>
				</x:a>
			</x:a>
		"""
		check = ihtml.a(
			html.a(
				ihtml.a(
					"gurk"
				)
			)
		)
		prefixes = xsc.Prefixes().addElementPrefixMapping("x", ihtml)
		node = parsers.parseString(xml, prefixes=prefixes)
		node = node.findfirst(xsc.FindType(xsc.Element)).compact() # get rid of the Frag and whitespace
		self.assertEquals(node, check)

	def test_parseurls(self):
		prefixes = xsc.Prefixes()
		prefixes.addElementPrefixMapping(None, html)
		node = parsers.parseString('<a href="4.html" style="background-image: url(3.gif);"/>', base="root:1/2.html", prefixes=prefixes)
		self.assertEqual(str(node[0]["style"]), "background-image: url(root:1/3.gif);")
		self.assertEqual(node[0]["style"].urls(), [url.URL("root:1/3.gif")])
		self.assertEqual(str(node[0]["href"]), "root:1/4.html")
		self.assertEqual(node[0]["href"].forInput(root="gurk/hurz.html"), url.URL("gurk/1/4.html"))

	def test_parserequiredattrs(self):
		class xmlns(xsc.Namespace):
			class Test(xsc.Element):
				class Attrs(xsc.Element.Attrs):
					class required(xsc.TextAttr): required = True

		prefixes = xsc.Prefixes()
		prefixes.addElementPrefixMapping(None, xmlns)
		node = parsers.parseString('<Test required="foo"/>', prefixes=prefixes)
		self.assertEqual(str(node[0]["required"]), "foo")

		warnings.filterwarnings("error", category=errors.RequiredAttrMissingWarning)
		try:
			node = parsers.parseString('<Test/>', prefixes=prefixes)
		except saxlib.SAXParseException, exc:
			self.assert_(isinstance(exc.getException(), errors.RequiredAttrMissingWarning))
			pass
		else:
			self.fail()

	def test_parsevalueattrs(self):
		class xmlns(xsc.Namespace):
			class Test(xsc.Element):
				class Attrs(xsc.Element.Attrs):
					class withvalues(xsc.TextAttr): values = ("foo", "bar")

		prefixes = xsc.Prefixes()
		prefixes.addElementPrefixMapping(None, xmlns)

		warnings.filterwarnings("error", category=errors.IllegalAttrValueWarning)
		node = parsers.parseString('<Test withvalues="bar"/>', prefixes=prefixes)
		self.assertEqual(str(node[0]["withvalues"]), "bar")
		try:
			node = parsers.parseString('<Test withvalues="baz"/>', prefixes=prefixes)
		except saxlib.SAXParseException, exc:
			self.assert_(isinstance(exc.getException(), errors.IllegalAttrValueWarning))
			pass
		else:
			self.fail()

class DTD2XSCTest(unittest.TestCase):

	def dtd2ns(self, s, xmlname, xmlurl=None, shareattrs=None):
		from xml.parsers.xmlproc import dtdparser

		dtd = dtdparser.load_dtd_string(s)
		node = xndl.fromdtd(dtd, xmlname=xmlname, xmlurl=xmlurl)

		data = node.asdata()

		if shareattrs is not None:
			data.shareattrs(shareattrs)

		mod = {"__name__": xmlname}
		encoding = "iso-8859-1"
		code = data.aspy(encoding=encoding, asmod=False).encode(encoding)
		exec code in mod

		return mod["xmlns"]

	def test_convert(self):
		dtdstring = """<?xml version='1.0' encoding='us-ascii'?>
		<!ELEMENT foo (bar+)>
		<!ATTLIST foo
			id    ID    #IMPLIED
			xmlns CDATA #FIXED "http://xmlns.foo.com/foo"
		>
		<!ELEMENT bar EMPTY>
		<!ATTLIST bar
			bar1 CDATA               #REQUIRED
			bar2 (bar2)              #IMPLIED
			bar3 (bar3a|bar3b|bar3c) #IMPLIED
			bar-4 (bar-4a|bar-4b)    #IMPLIED
			bar_4 (bar_4a|bar_4b)    #IMPLIED
			bar_42 (bar_42a|bar_42b) #IMPLIED
			class CDATA              #IMPLIED
		>
		"""
		ns = self.dtd2ns(dtdstring, "foo")

		self.assert_(issubclass(ns, xsc.Namespace))
		self.assertEqual(ns.xmlname, ("xmlns", "foo"))
		self.assertEqual(ns.xmlurl, "http://xmlns.foo.com/foo")
		self.assertEqual(ns.foo.empty, False)
		self.assert_(issubclass(ns.foo.Attrs.id, xsc.IDAttr))
		self.assert_("xmlns" not in ns.foo.Attrs)
		self.assertEqual(ns.bar.empty, True)

		self.assert_(issubclass(ns.bar.Attrs.bar1, xsc.TextAttr))
		self.assertEqual(ns.bar.Attrs.bar1.required, True)

		self.assert_(issubclass(ns.bar.Attrs.bar2, xsc.BoolAttr))
		self.assertEqual(ns.bar.Attrs.bar2.required, False)

		self.assert_(issubclass(ns.bar.Attrs.bar3, xsc.TextAttr))
		self.assertEqual(ns.bar.Attrs.bar3.required, False)
		self.assertEqual(ns.bar.Attrs.bar3.values, ("bar3a", "bar3b", "bar3c"))

		# Attributes are alphabetically sorted
		self.assert_(issubclass(ns.bar.Attrs.bar_4, xsc.TextAttr))
		self.assertEqual(ns.bar.Attrs.bar_4.xmlname, ("bar_4", "bar-4"))
		self.assertEqual(ns.bar.Attrs.bar_4.values, ("bar-4a", "bar-4b"))

		self.assert_(issubclass(ns.bar.Attrs.bar_42, xsc.TextAttr))
		self.assertEqual(ns.bar.Attrs.bar_42.xmlname, ("bar_42", "bar_4"))
		self.assertEqual(ns.bar.Attrs.bar_42.values, ("bar_4a", "bar_4b"))

		self.assert_(issubclass(ns.bar.Attrs.bar_422, xsc.TextAttr))
		self.assertEqual(ns.bar.Attrs.bar_422.xmlname, ("bar_422", "bar_42"))
		self.assertEqual(ns.bar.Attrs.bar_422.values, ("bar_42a", "bar_42b"))

	def test_keyword(self):
		dtdstring = """<?xml version='1.0' encoding='us-ascii'?>
		<!ELEMENT foo EMPTY>
		<!ATTLIST foo
			class CDATA              #IMPLIED
		>
		"""
		ns = self.dtd2ns(dtdstring, "foo")
		self.assert_(issubclass(ns.foo.Attrs.class_, xsc.TextAttr))
		self.assertEqual(ns.foo.Attrs.class_.xmlname, ("class_", "class"))

	def test_shareattrsnone(self):
		dtdstring = """<?xml version='1.0' encoding='us-ascii'?>
		<!ELEMENT foo (bar)>
		<!ATTLIST foo
			baz CDATA              #IMPLIED
		>
		<!ELEMENT bar EMPTY>
		<!ATTLIST bar
			baz CDATA              #IMPLIED
		>
		"""
		ns = self.dtd2ns(dtdstring, "foo", shareattrs=None)
		self.assert_(not hasattr(ns, "baz"))

	def test_shareattrsdupes(self):
		dtdstring = """<?xml version='1.0' encoding='us-ascii'?>
		<!ELEMENT foo (bar)>
		<!ATTLIST foo
			baz  CDATA             #IMPLIED
			baz2 CDATA             #IMPLIED
		>
		<!ELEMENT bar EMPTY>
		<!ATTLIST bar
			baz  CDATA             #IMPLIED
			baz2 CDATA             #REQUIRED
		>
		"""
		ns = self.dtd2ns(dtdstring, "foo", shareattrs=False)
		self.assert_(issubclass(ns.foo.Attrs.baz, ns.baz.baz))
		self.assert_(issubclass(ns.bar.Attrs.baz, ns.baz.baz))
		self.assert_(not hasattr(ns, "baz2"))
		self.assert_(not ns.foo.Attrs.baz2.required)
		self.assert_(ns.bar.Attrs.baz2.required)

	def test_shareattrsall(self):
		dtdstring = """<?xml version='1.0' encoding='us-ascii'?>
		<!ELEMENT foo (bar)>
		<!ATTLIST foo
			baz  CDATA             #IMPLIED
			bazz CDATA             #IMPLIED
		>
		<!ELEMENT bar EMPTY>
		<!ATTLIST bar
			baz  CDATA             #IMPLIED
			bazz CDATA             #REQUIRED
		>
		"""
		ns = self.dtd2ns(dtdstring, "foo", shareattrs=True)
		self.assert_(issubclass(ns.foo.Attrs.baz, ns.baz.baz))
		self.assert_(issubclass(ns.bar.Attrs.baz, ns.baz.baz))

		self.assertNotEqual(ns.foo.Attrs.bazz.__bases__[0], xsc.TextAttr)
		self.assertNotEqual(ns.bar.Attrs.bazz.__bases__[0], xsc.TextAttr)
		self.assertNotEqual(ns.foo.Attrs.bazz.__bases__, ns.bar.Attrs.bazz.__bases__)

		self.assert_(not ns.foo.Attrs.bazz.required)
		self.assert_(ns.bar.Attrs.bazz.required)

class TLD2XSCTest(unittest.TestCase):

	def test_convert(self):
		pass

def test_main():
	unittest.main()

if __name__ == "__main__":
	test_main()
