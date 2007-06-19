#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

## Copyright 1999-2007 by LivingLogic AG, Bayreuth/Germany.
## Copyright 1999-2007 by Walter D�rwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license


'''
<par>This module is an &xist; namespace. It provides a simple template language
based on processing instructions embedded in &xml; or plain text.</par>

<par>The following example is a simple <z>Hello, World</z> type template:</par>

<prog><![CDATA[
from ll.xist.ns import detox

template = """
<?def helloworld(n=10)?>
	<?for i in xrange(n)?>
		Hello, World!
	<?endfor?>
<?enddef?>
"""

module = detox.xml2mod(template)

print "".join(module.helloworld())
]]></prog>
'''


__version__ = "$Revision$".split()[1]
# $Source$


import sys, os, datetime, types

from ll.xist import xsc


class expr(xsc.ProcInst):
	"""
	Embed the value of the expression
	"""


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
	"""
	<par>Starts an if block. An if block can contain zero or more
	<pyref class="elif_"><class>elif_</class></pyref> blocks, followed by zero
	or one <pyref class="else_"><class>else_</class></pyref> block and must
	be closed with an <pyref class="endif"><class>endif</class></pyref> PI.</par>

	<par>For example:</par>

	<prog><![CDATA[
	<?code import random?>
	<?code n = random.choice("123?")?>
	<?if n == "1"?>
		One
	<?elif n == "2"?>
		Two
	<?elif n == "3"?>
		Three
	<?else?>
		Something else
	<?endif?>
	]]></prog>
	"""
	xmlname = "if"


class elif_(xsc.ProcInst):
	"""
	Starts an elif block.
	"""
	xmlname = "elif"


class else_(xsc.ProcInst):
	"""
	Starts an else block.
	"""
	xmlname = "else"


class def_(xsc.ProcInst):
	"""
	<par>Start a function (or method) definition. A function definition must be
	closed with an <pyref class="enddef"><class>enddef</class></pyref> PI.</par>

	<par>Example:</par>

	<prog><![CDATA[
	<?def persontable(persons)?>
		<table>
			<tr>
				<th>first name</th>
				<th>last name</th>
			</tr>
			<?for person in persons?>
				<tr>
					<td><?textexpr person.firstname?></td>
					<td><?textexpr person.lastname?></td>
				</tr>
			<?endfor?>
		</table>
	<?enddef?>
	]]></prog>

	<par>If the generated function contains output (i.e. if there is text content
	or <pyref class="expr"><class>expr</class></pyref>,
	<pyref class="textexpr"><class>textexpr</class></pyref> or
	<pyref class="attrexpr"><class>attrexpr</class></pyref> PIs before the matching
	<pyref class="enddef"><class>enddef</class></pyref>) the generated function
	will be a generator function.</par>

	<par>Output outside of a function definition will be ignored.</par>
	"""
	xmlname = "def"


class class_(xsc.ProcInst):
	"""
	<par>Start a class definition. A class definition must be closed with an
	<pyref class="endclass"><class>endclass</class></pyref> PI.</par>

	<par>Example:</par>
	<prog><![CDATA[
	<?class mylist(list)?>
		<?def output(self)?>
			<ul>
				<?for item in self?>
					<li><?textexpr item?></li>
				<?endfor?>
			</ul>
		<?enddef?>
	<?endclass?>
	]]></prog>
	"""
	xmlname = "class"


class for_(xsc.ProcInst):
	"""
	<par>Start a <lit>for</lit> loop. A for loop must be closed with an
	<pyref class="endfor"><class>endfor</class></pyref> PI.</par>

	<par>For example:</par>
	<prog><![CDATA[
	<ul>
		<?for i in xrange(10)?>
			<li><?expr str(i)?></li>
		<?endfor?>
	</ul>
	]]></prog>
	"""
	xmlname = "for"


class while_(xsc.ProcInst):
	"""
	<par>Start a <lit>while</lit> loop. A while loop must be closed with an
	<pyref class="endwhile"><class>endwhile</class></pyref> PI.</par>

	<par>For example:</par>
	<prog><![CDATA[
	<?code i = 0?>
	<ul>
		<?while True?>
			<li><?expr str(i)?><?code i += 1?></li>
			<?code if i > 10: break?>
		<?endwhile?>
	</ul>
	]]></prog>
	"""
	xmlname = "while"


class end(xsc.ProcInst):
	"""
	<par>Ends a <pyref class="while_">while</pyref> or
	<pyref class="for_">for</pyref> loop or a
	<pyref class="if_">if</pyref>, <pyref class="def_">def</pyref> or
	<pyref class="class_">class</pyref> block.
	</par>
	"""


# The name of al available processing instructions
targets = set(value.xmlname for value in vars().itervalues() if isinstance(value, type) and issubclass(value, xsc.ProcInst))


def tokenize(string):
	"""
	Tokenize the <class>unicode</class> object <arg>string</arg> (which must
	be an &xml; string) according to the processing instructions in this namespace.
	<function>tokenize</function> will generate tuples with the first
	item being the processing instruction target name and the second being the PI
	data. <z>Text</z> content (i.e. anything other than PIs) will be returned
	as <lit>(None, <rep>data</rep>)</lit>. Unknown processing instructions
	will be returned as literal text (i.e. as <lit>(None, u"&lt;?<rep>target</rep>
	<rep>data</rep>?&gt;")</lit>).
	"""

	pos = 0
	while True:
		pos1 = string.find("<?", pos)
		if pos1<0:
			part = string[pos:]
			if part:
				yield (None, part)
			return
		pos2 = string.find("?>", pos1)
		if pos2<0:
			part = string[pos:]
			if part:
				yield (None, part)
			return
		part = string[pos:pos1]
		if part:
			yield (None, part)
		part = string[pos1+2: pos2].strip()
		parts = part.split(None, 1)
		target = parts[0]
		if len(parts) > 1:
			data = parts[1]
		else:
			data = ""
		if target not in targets:
			# return unknown PIs as text
			data = "<?%s %s?>" % (target, data)
			target = None
		yield (target, data)
		pos = pos2+2


# Used for indenting Python source code
indent = "\t"


def xml2py(source):
	stack = []
	stackoutput = [] # stack containing only True for def and False for class

	lines = [
		"# generated by %s %s on %s UTC" % (__file__, __version__, datetime.datetime.utcnow()),
		"",
		"from ll.xist.helpers import escapetext as __detox_escapetext__, escapeattr as __detox_escapeattr__",
		"",
	]

	def endscope(action):
		if not stack:
			raise SyntaxError("can't end %s scope: no active scope" % (action or "unnamed"))
		if action and action != stack[-1][0]:
			raise SyntaxError("can't end %s scope: active scope is: %s %s" % (action, stack[-1][0], stack[-1][1]))
		return stack.pop()

	for (t, s) in tokenize(source):
		if t is None:
			# ignore output outside of functions
			if stackoutput and stackoutput[-1]:
				lines.append("%syield %r" % (len(stack)*indent, s))
		elif t == "expr":
			# ignore output outside of functions
			if stackoutput and stackoutput[-1]:
				lines.append("%syield %s" % (len(stack)*indent, s))
		elif t == "textexpr":
			# ignore output outside of functions
			if stackoutput and stackoutput[-1]:
				lines.append("%syield __detox_escapetext__(%s)" % (len(stack)*indent, s))
		elif t == "attrexpr":
			# ignore output outside of functions
			if stackoutput and stackoutput[-1]:
				lines.append("%syield __detox_escapeattr__(%s)" % (len(stack)*indent, s))
		elif t == "code":
			lines.append("%s%s" % (len(stack)*indent, s))
		elif t == "def":
			lines.append("")
			lines.append("%sdef %s:" % (len(stack)*indent, s))
			stack.append((t, s))
			stackoutput.append(True)
		elif t == "class":
			lines.append("")
			lines.append("%sclass %s:" % (len(stack)*indent, s))
			stack.append((t, s))
			stackoutput.append(False)
		elif t == "for":
			lines.append("%sfor %s:" % (len(stack)*indent, s))
			stack.append((t, s))
		elif t == "while":
			lines.append("%swhile %s:" % (len(stack)*indent, s))
			stack.append((t, s))
		elif t == "if":
			lines.append("%sif %s:" % (len(stack)*indent, s))
			stack.append((t, s))
		elif t == "else":
			lines.append("%selse:" % ((len(stack)-1)*indent))
		elif t == "elif":
			lines.append("%selif %s:" % ((len(stack)-1)*indent, s))
		elif t == "end":
			scope = endscope(s)
			if scope in ("def", "class"):
				stackoutput.pop()
	if stack:
		raise SyntaxError("unclosed scopes remaining: %s" % ", ".join(scope[0] for scope in stack))
	return "\n".join(lines)


def xml2mod(source, name=None, filename="<string>", store=False, loader=None):
	name = name or "ll.xist.ns.detox.sandbox_%x" % (hash(filename) + sys.maxint + 1)
	module = types.ModuleType(name)
	module.__file__ = filename
	if loader is not None:
		module.__loader__ = loader
	if store:
		sys.modules[name] = module
	code = compile(xml2py(source), filename, "exec")
	exec code in module.__dict__
	return module


# The following stuff has been copied from Kids import hook

DETOX_EXT = ".detox"


def enable_import(suffixes=None):
	class DetoxLoader(object):
		def __init__(self, path=None):
			if path and os.path.isdir(path):
				self.path = path
			else:
				raise ImportError

		def find_module(self, fullname):
			path = os.path.join(self.path, fullname.split(".")[-1])
			for ext in [cls.DETOX_EXT] + self.suffixes:
				if os.path.exists(path + ext):
					self.filename = path + ext
					return self
			return None

		def load_module(self, fullname):
			try:
				return sys.modules[fullname]
			except KeyError:
				return xml2mod(open(self.filename, "r").read(), name=fullname, filename=self.filename, store=True, loader=self)

	DetoxLoader.suffixes = suffixes or []
	sys.path_hooks.append(DetoxLoader)
	sys.path_importer_cache.clear()
