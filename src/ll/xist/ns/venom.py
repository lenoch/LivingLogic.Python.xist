#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

## Copyright 1999-2006 by LivingLogic AG, Bayreuth/Germany.
## Copyright 1999-2006 by Walter D�rwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license


'''
<par>This module is an &xist; namespace. It provides a simple template language
based on processing intructions embedded in &xml; or plain text.</par>

<par>An example that generates an &html; table containing the result
of a search for names in a <lit>person</lit> table might look
like this:</par>

<example>
<prog>
from ll.xist import xsc
from ll.xist.ns import html, htmlspecials
from ll import toxic

class search(xsc.Element):
	def convert(self, converter):
		e = xsc.Frag(
			toxic.args("search varchar2"),
			toxic.vars("i integer;"),
			toxic.type("varchar2(32000);"),
			htmlspecials.plaintable(
				toxic.code("""
					i := 1;
					for row in (select name from person where name like search) loop
						"""),
						html.tr(
							html.th(toxic.expr("i"), align="right"),
							html.td(toxic.expr("xmlescape(row.name)"))
						),
						toxic.code("""
						i := i+1;
					end loop;
				""")
			)
		)
		return e.convert(converter)

print toxic.xml2ora(search().conv().asBytes("us-ascii"), "us-ascii")
</prog>
</example>

<par>Running this script will give the following output
(the indentation will be different though):</par>

<prog>
(
	search varchar2
)
return varchar2
as
	c_out varchar2(32000);
	i integer;
begin
	c_out := c_out || '&lt;table cellpadding="0" border="0" cellspacing="0"&gt;';
	i := 1;
	for row in (select name from person where name like search) loop
		c_out := c_out || '&lt;tr&gt;&lt;th align="right"&gt;';
		c_out := c_out || i;
		c_out := c_out || '&lt;/th&gt;&lt;td&gt;';
		c_out := c_out || xmlescape(row.name);
		c_out := c_out || '&lt;/td&gt;&lt;/tr&gt;';
		i := i+1;
	end loop;
	c_out := c_out || '&lt;/table&gt;';
	return c_out;
end;
</prog>

<par>Instead of generating the &xml; from a single &xist; element,
it's of course also possible to use an &xml; file. One that generates
the same function as the one above looks like this:</par>

<example>
<prog>
&lt;?args
	search varchar2
?&gt;
&lt;?vars
	i integer;
?&gt;
&lt;plaintable class="search"&gt;
	&lt;?code
		i := 1;
		for row in (select name from person where name like search) loop
			?&gt;
			&lt;tr&gt;
				&lt;th align="right"&gt;&lt;?expr i?&gt;&lt;/th&gt;
				&lt;td&gt;&lt;?expr xmlescape(row.name)?&gt;&lt;/td&gt;
			&lt;/tr&gt;
			&lt;?code
			i := i + 1;
		end loop;
	?&gt;
&lt;/plaintable&gt;
</prog>
</example>

<par>When we save the file above as <filename>search.sqlxsc</filename> then
parsing the file, transforming it and printing the function body
works like this:</par>

<example>
<prog>
from ll.xist import parsers
from ll.xist.ns import html, htmlspecials
from ll import toxic

node = parsers.parseFile("search.sqlxsc")
node = node.conv()
print toxic.xml2ora(node.asString("us-ascii"), "us-ascii")
</prog>
</example>
'''


__version__ = "$Revision$".split()[1]
# $Source$


import datetime, new

from ll.xist import xsc


try:
	any
except NameError:
	def any(iter):
		for item in iter:
			if item:
				return True
		return False


class expr(xsc.ProcInst):
	"""
	Embed the value of the expression 
	"""
	pass


class textexpr(xsc.ProcInst):
	pass


class attrexpr(xsc.ProcInst):
	pass


class code(xsc.ProcInst):
	"""
	<par>Embed the PI data literally in the generated code.</par>

	<par>For example <lit>&lt;?code foo = 42?&gt;</lit> will put the
	statement <lit>foo = 42</lit> into the generated Python source.</par>
	"""


class if_(xsc.ProcInst):
	xmlname = "if"


class elif_(xsc.ProcInst):
	xmlname = "elif"


class else_(xsc.ProcInst):
	xmlname = "else"


class endif(xsc.ProcInst):
	pass


class def_(xsc.ProcInst):
	xmlname = "def"


class enddef(xsc.ProcInst):
	pass


class class_(xsc.ProcInst):
	xmlname = "class"


class endclass(xsc.ProcInst):
	pass


class for_(xsc.ProcInst):
	xmlname = "for"


class endfor(xsc.ProcInst):
	pass


# Used for indenting Python source code
indent = "\t"


@classmethod
def xml2py(cls, source):
	stack = []
	lines = [
		"# generated by %s %s on %s UTC" % (__file__, __version__, datetime.datetime.utcnow()),
		"",
		"from ll.xist.helpers import escapetext as __venom_escapetext__, escapeattr as __venom_escapeattr__",
		"",
	]

	def endscope(action):
		if not stack:
			raise SyntaxError("can't end %s scope: no active scope" % action._str(fullname=True, xml=False, decorate=False))
		if not issubclass(stack[-1][0], action):
			raise SyntaxError("can't end %s scope: active scope is: %s %s" % (action._str(fullname=True, xml=False, decorate=False), stack[-1][0]._str(fullname=True, xml=False, decorate=False), stack[-1][1]))
		stack.pop(-1)

	for (t, s) in cls.tokenize(source):
		if t is unicode:
			if any(issubclass(item[0], def_) for item in stack):
				lines.append("%syield %r" % (len(stack)*cls.indent, s))
			# ignore output outside of functions
		elif issubclass(t, expr):
			if any(issubclass(item[0], def_) for item in stack):
				lines.append("%syield %s" % (len(stack)*cls.indent, s))
			# ignore output outside of functions
		elif issubclass(t, textexpr):
			if any(issubclass(item[0], def_) for item in stack):
				lines.append("%syield __venom_escapetext__(%s)" % (len(stack)*cls.indent, s))
			# ignore output outside of functions
		elif issubclass(t, attrexpr):
			if any(issubclass(item[0], def_) for item in stack):
				lines.append("%syield __venom_escapeattr__(%s)" % (len(stack)*cls.indent, s))
			# ignore output outside of functions
		elif issubclass(t, code):
			lines.append("%s%s" % (len(stack)*cls.indent, s))
		elif issubclass(t, def_):
			lines.append("%sdef %s:" % (len(stack)*cls.indent, s))
			stack.append((t, s))
		elif issubclass(t, enddef):
			endscope(def_)
		elif issubclass(t, class_):
			lines.append("%sclass %s:" % (len(stack)*cls.indent, s))
			stack.append((t, s))
		elif issubclass(t, endclass):
			endscope(class_)
		elif issubclass(t, for_):
			lines.append("%sfor %s:" % (len(stack)*cls.indent, s))
			stack.append((t, s))
		elif issubclass(t, endfor):
			endscope(for_)
		elif issubclass(t, if_):
			lines.append("%sif %s:" % (len(stack)*cls.indent, s))
			stack.append((t, s))
		elif issubclass(t, else_):
			lines.append("%selse:" % ((len(stack)-1)*cls.indent))
		elif issubclass(t, elif_):
			lines.append("%selif %s:" % ((len(stack)-1)*cls.indent, s))
		elif issubclass(t, endif):
			endscope(if_)
	return "\n".join(lines)


@classmethod
def xml2mod(cls, source, name="venom"):
	mod = new.module(name)
	exec cls.xml2py(source) in mod.__dict__
	return mod


class __ns__(xsc.Namespace):
	xmlname = "pox"
	xmlurl = "http://xmlns.livinglogic.de/xist/ns/pox"
__ns__.makemod(vars())
