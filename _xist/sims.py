#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

## Copyright 1999-2004 by LivingLogic AG, Bayreuth, Germany.
## Copyright 1999-2004 by Walter D�rwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license

"""
This module contains classes for a very simple validation model
"""

__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$


import warnings
from ll.xist import xsc, errors


class EmptyElementWithContentWarning(errors.Warning):
	"""
	Warning that is issued, when an element has content,
	but it shouldn't (i.e. <lit>model</lit> is <pyref class="Empty"><class>Empty</class></pyref>)
	"""

	def __init__(self, node):
		self.node = node

	def __str__(self):
		s = "element %s" % self.node._str(fullname=True, xml=False, decorate=True)
		if self.node.startloc is not None:
			s += " at %s" % self.node.startloc
		s += " has EMPTY content model, but has content"
		return s


class WrongElementWarning(errors.Warning):
	"""
	Warning that is issued, when an element contains another element
	but it shouldn't.
	"""

	def __init__(self, node, badnode, elements):
		self.node = node
		self.badnode = badnode
		self.elements = elements

	def __str__(self):
		s = "element %s" % self.node._str(fullname=True, xml=False, decorate=True)
		if self.node.startloc is not None:
			s += " at %s" % self.node.startloc
		s += " may not contain element %s" % self.badnode._str(fullname=1, xml=0, decorate=1)
		if self.badnode.startloc is not None:
			s += " at %s" % self.badnode.startloc
		return s


class ElementWarning(errors.Warning):
	"""
	Warning that is issued, when an element contains another element
	but it shouldn't contain any.
	"""

	def __init__(self, node, badnode):
		self.node = node
		self.badnode = badnode

	def __str__(self):
		s = "element %s" % self.node._str(fullname=True, xml=False, decorate=True)
		if self.node.startloc is not None:
			s += " at %s" % self.node.startloc
		s += " may not contain other elements"
		if self.badnode.startloc is not None:
			s += " (at %s)" % self.badnode.startloc
		return s


class IllegalTextWarning(errors.Warning):
	"""
	Warning that is issued, when an element contains a text node
	but it shouldn't.
	"""

	def __init__(self, node, badnode):
		self.node = node
		self.badnode = badnode

	def __str__(self):
		s = "element %s" % self.node._str(fullname=True, xml=False, decorate=True)
		if self.node.startloc is not None:
			s += " at %s" % self.node.startloc
		s += " may not contain text nodes"
		if self.badnode.startloc is not None:
			s += " (at %s)" % self.badnode.startloc
		return s


def badtext(node):
	"""
	Return whether <arg>node</arg> is a text node (i.e.
	<pyref module="ll.xist" class="Text"><class>Text</class></pyref>
	that does not consist of whitespace only.
	"""
	if isinstance(node, xsc.Text):
		if not node.isspace(): # Works even for empty text node
			return True
	return False


class Empty(object):
	"""
	This validator checks that an element has no content.
	"""
	empty = True

	def __repr__(self):
		return "Empty()"

	def checkvalid(self, node):
		"""
		check that the content of <arg>node</arg> is valid.
		"""
		if isinstance(node, xsc.Element):
			if len(node):
				warnings.warn(EmptyElementWithContentWarning(node))


class NoElements(object):
	"""
	This validator checks that an element does not have child elements
	from the same namespace.
	"""
	empty = False

	def __repr__(self):
		return "NoElements()"

	def checkvalid(self, node):
		"""
		check that the content of <arg>node</arg> is valid.
		"""
		if isinstance(node, xsc.Element):
			for child in node.content:
				if isinstance(child, xsc.Element) and node.xmlns is not None and child.xmlns is not None and issubclass(child.xmlns, node.xmlns):
					warnings.warn(ElementWarning(node, child))


class NoElementsOrText(object):
	"""
	This validator checks that an element does have neither child elements
	from the same namespace nor real (i.e. not-whitespace) text nodes.
	"""
	empty = False

	def __repr__(self):
		return "NoElementsOrText()"

	def checkvalid(self, node):
		"""
		check that the content of <arg>node</arg> is valid.
		"""
		if isinstance(node, xsc.Element):
			for child in node.content:
				if badtext(child):
					warnings.warn(IllegalTextWarning(node, child))
				elif isinstance(child, xsc.Element) and node.xmlns is not None and child.xmlns is not None and issubclass(child.xmlns, node.xmlns):
					warnings.warn(ElementWarning(node, child))


class Elements(object):
	"""
	This validator checks that an element does have neither child elements
	from any of the namespaces of those elements specified in the constructor
	except for those elements itself nor real (i.e. not-whitespace) text nodes.
	"""
	empty = False

	def __init__(self, *elements):
		"""
		Every element in <lit>elements</lit> may be in the content of the
		node to which this validator is attached. Any other element from one
		of the namespaces of those elements is invalid.
		"""
		self.elements = elements

	def __repr__(self):
		return "Elements(%s)" % ", ".join(["%s.%s" % (cls.__module__, cls.__name__) for cls in self.elements])

	def checkvalid(self, node):
		"""
		check that the content of <arg>node</arg> is valid.
		"""
		ns = None
		if isinstance(node, xsc.Element):
			for child in node.content:
				if badtext(child):
					warnings.warn(IllegalTextWarning(node, child))
				elif isinstance(child, xsc.Element) and node.xmlns is not None and not isinstance(child, self.elements):
					if ns is None:
						# FIXME: Drop the list comprehension in 2.4
						ns = tuple([el.xmlns for el in self.elements if el.xmlns is not None])
					if child.xmlns is not None and issubclass(child.xmlns, ns):
						warnings.warn(WrongElementWarning(node, child, self.elements))


class ElementsOrText(Elements):
	"""
	This validator checks that an element doesn't have child elements
	from the same namespace except those specified in the constructor.
	"""

	def __init__(self, *elements):
		"""
		Every element in <lit>elements</lit> may be in the content of the
		node to which this validator is attached. Any other element from one
		of the namespaces of those elements is invalid.
		"""
		self.elements = elements

	def __repr__(self):
		return "ElementsOrText(%s)" % ", ".join(["%s.%s" % (cls.__module__, cls.__name__) for cls in self.elements])

	def checkvalid(self, node):
		"""
		check that the content of <arg>node</arg> is valid.
		"""
		ns = None
		if isinstance(node, xsc.Element):
			for child in node.content:
				if isinstance(child, xsc.Element) and node.xmlns is not None and not isinstance(child, self.elements):
					if ns is None:
						# FIXME: Drop the list comprehension in 2.4
						ns = tuple([el.xmlns for el in self.elements if el.xmlns is not None])
					if child.xmlns is not None and issubclass(child.xmlns, ns):
						warnings.warn(WrongElementWarning(node, child, self.elements))


class Any(object):
	"""
	This validator declares any content to be valid.
	"""
	empty = False

	def __repr__(self):
		return "Any()"

	def checkvalid(self, node):
		"""
		check that the content of <arg>node</arg> is valid.
		This method does nothing as anything is valid.
		"""
