#! /usr/bin/python

import os
import string
import types

# for file size checking
import stat

# for image size checking
import Image

# for parsing XML files
from xmllib import *

###
### exceptions
###

class EHSCException:
	"base class for all HSC exceptions"

	def __str__(self):
		return "Something wonderful has happened"

class EHSCEmptyElementWithContent(EHSCException):
	"this element is specified to be empty, but has content"

	def __init__(self,element):
		self.element = element

	def __str__(self):
		return "the element '" + self.element.__class__.__name__ + "' is specified to be empty, but has content"

class EHSCIllegalAttribute(EHSCException):
	"this element has an attribute that is not allowed"

	def __init__(self,element,attr):
		self.element = element
		self.attr = attr

	def __str__(self):
		return "the element '" + self.element.__class__.__name__ + "' has an attribute ('" + self.attr + "') that is not allowed here. The only allowed attributes are: " + str(self.element.permitted_attrs)

class EHSCImageSizeFormat(EHSCException):
	"Can't format or evaluate image size attribute"

	def __init__(self,element,attr):
		self.element = element
		self.attr = attr

	def __str__(self):
		return "the value '" + str(self.element[self.attr]) + "' for the image size attribute '" + self.attr + "' of the element '" + self.element.__class__.__name__ + "' can't be formatted or evaluated"

class EHSCFileNotFound(EHSCException):
	"Can't open image for getting image size"

	def __init__(self,url):
		self.url = url

	def __str__(self):
		return "the image file '" + self.url + "' can't be opened"

###
###
###

class XSCNode:
	"base class for nodes in the document tree. Derived class must implement AsString() und AsHTML()"

	def __add__(self,other):
		return [self] + other

	def __radd__(self,other):
		return other + [self]

class XSCComment(XSCNode):
	"comments"

	def __init__(self,content = ""):
		self.content = content

	def AsHTML(self,xsc,mode = None):
		return XSCComment(self.content)

	def AsString(self,xsc):
		return "<!--" + self.content + "-->"

class XSCDocType(XSCNode):
	"document type"

	def __init__(self,data = ""):
		self.data = data

	def AsHTML(self,xsc,mode = None):
		return XSCDocType(self.data)

	def AsString(self,xsc):
		return "<!DOCTYPE " + self.data + ">"

class XSCElement(XSCNode):
	"XML elements"

	close = 0
	permitted_attrs = []

	def __init__(self,content = [],attrs = {},**restattrs):
		self.content = content
		self.attrs = {}

		# make a deep copy here
		for i in attrs.keys():
			self.attrs[i] = attrs[i]
		for i in restattrs.keys():
			self.attrs[i] = restattrs[i]

	def append(self,item):
		self.content.append(item)

	def CheckAttrs(self):
		"checks that only attributes that are allow are used (raises an exception otherwise)"

		for attr in self.attrs.keys():
			if attr not in self.permitted_attrs:
				raise EHSCIllegalAttribute(self,attr)

	def AsHTML(self,xsc,mode = None):
		self.CheckAttrs()

		e = self
		e.content = xsc.AsHTML(self.content,mode)
		e.attrs   = xsc.AsHTML(self.attrs,mode)

		return e

	def AsString(self,xsc):
		"returns this element as a string. For the content and the attributes the global function AsString() is called recursively"

		v = []
		v.append("<")
		v.append(string.lower(self.__class__.__name__))
		if len(self.attrs.keys()):
			v.append(" ")
			v.append(xsc.AsString(self.attrs))
		s = xsc.AsString(self.content)
		if self.close:
			v.append(">")
			v.append(s)
			v.append("</")
			v.append(string.lower(self.__class__.__name__)) # name must be a string without any nasty characters
			v.append(">")
		else:
			if len(s):
				raise EHSCEmptyElementWithContent(self)
			v.append("/>")

		return string.joinfields(v,"")

	def __getitem__(self,index):
		return self.attrs[index]

	def __setitem__(self,index,value):
		self.attrs[index] = value

	def __delitem__(self,index):
		del self.attrs[index]

	def has_attr(self,attr):
		return self.attrs.has_key(attr)

handlers = {} # dictionary that links element names to classes

###
###
###

class XSC(XMLParser):
	"Reads a XML file and constructs an XSC tree from it."


	def __init__(self,filename = None):
		XMLParser.__init__(self)
		self.filename = filename
		if filename != None:
			self.nesting = [ [] ] # our nodes do not have a parent link, therefore we have to store the active path through the tree in a stack (which we call nesting, because stack is already used by the base class
			self.feed(open(filename).read())
			self.close()
			self.root = self.nesting[0]
		else:
			self.root = None

	def processingInstruction (self,target, remainder):
		pass

	def unknown_starttag(self,name,attrs = {}):
		e = handlers[name]([],attrs)
		self.nesting[-1].append(e) # add the new element to the content of the innermost element (or to the array)
		self.nesting.append(e) # push new innermost element onto the stack
		
	def unknown_endtag(self,name):
		self.nesting[-1:] = [] # pop the innermost element off the stack

	def handle_data(self,data):
		self.nesting[-1].append(data) # add the new string to the content of the innermost element

	def handle_comment(self,comment):
		self.nesting[-1].append(XSCComment(comment))

	def AsHTML(self,value = None,mode = None):
		"transforms a value into its HTML equivalent: this means that HSC nodes get expanded to their equivalent HTML subtree. Scalar types are returned as is. Lists, tuples and dictionaries are treated recurcively"

		if value == None:
			xsc = XSC()
			xsc.root = self.AsHTML(self.root,mode)
			return xsc
		if type(value) in [ types.StringType,types.NoneType,types.IntType,types.LongType,types.FloatType ]:
			return value
		elif type(value) in [ types.ListType,types.TupleType ]:
			v = []
			for i in value:
				v.append(self.AsHTML(i,mode))
			return v
		elif type(value) == types.DictType:
			v = {}
			for i in value.keys():
				v[i] = self.AsHTML(value[i],mode)
			return v
		else:
			return value.AsHTML(self,mode)

	def AsString(self,value = None):
		"transforms a value into a string: string are returned with 'nasty' characters replaced with entities, XSC and HTML nodes are output as one would expect. Lists, tuples and dictionaries are treated recursively"

		if value == None:
			return self.AsString(self.root)
		if type(value) == types.StringType:
			v = []
			for i in value:
				if i == '<':
					v.append('&lt;')
				elif i == '>':
					v.append('&gt;')
				elif i == '&':
					v.append('&amp;')
				elif i == '"':
					v.append('&quot')
				elif ord(i)>=128:
					v.append('&#' + str(ord(i)) + ';')
				else:
					v.append(i)
			return string.joinfields(v,"")
		elif type(value) in [ types.NoneType,types.IntType,types.LongType,types.FloatType ] :
			return str(value)
		elif type(value) in [ types.ListType,types.TupleType ]:
			v = []
			for i in value:
				v.append(self.AsString(i))
			return string.joinfields(v,"")
		elif type(value) == types.DictType:
			v = []
			for i in value.keys():
				if len(v):
					v.append(" ")
				v.append(i) # keys must be strings without any nasty characters
				s = self.AsString(value[i])
				if len(s):
					v.append('="') # we can use double quotes here, because all double quotes will be replaced with the entity in the string
					v.append(s)
					v.append('"')
			return string.joinfields(v,"")
		else:
			return value.AsString(self)

	def __str__(self):
		return self.AsHTML().AsString()

	def ExpandedURL(self,url):
		"expands URLs"

		return url

	def ImageSize(self,url):
		"returns the size of an image as a tuple"

		try:
			img = Image.open(url)
			return img.size
		except:
			raise EHSCFileNotFound(url)

	def FileSize(self,url):
		"returns the size of a file in bytes"

		return os.stat(url)[stat.ST_SIZE]

	def ExpandLinkAttribute(self,element,attr):
		"expands the url that is the value of attr"

		if element.has_attr(attr):
			element[attr] = self.ExpandedURL(element[attr])

	def AddImageSizeAttributes(self,element,imgattr,widthattr = "width",heightattr = "height"):
		"add width and height attributes to the element for the image that can be found in the attributes imgattr. if the attribute is already there it is taken as a formating template with the size passed in as a dictionary with the keys 'width' and 'height', i.e. you could make your image twice as wide with width='%(width)d*2'"

		if element.has_attr(imgattr):
			self.ExpandLinkAttribute(element,imgattr)
			size = self.ImageSize(element[imgattr])
			sizedict = { "width": size[0], "height": size[1] }
			if element.has_attr(widthattr):
				try:
					element[widthattr] = eval(str(element[widthattr]) % sizedict)
				except:
					raise EHSCImageSizeFormat(element,widthattr)
			else:
				element[widthattr] = size[0]
			if element.has_attr(heightattr):
				try:
					element[heightattr] = eval(str(element[heightattr]) % sizedict)
				except:
					raise EHSCImageSizeFormat(element,heightattr)
			else:
				element[heightattr] = size[1]

