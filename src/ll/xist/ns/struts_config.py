#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

## Copyright 1999-2007 by LivingLogic AG, Bayreuth/Germany.
## Copyright 1999-2007 by Walter D�rwald
##
## All Rights Reserved
##
## See xist/__init__.py for the license


"""
<par>Namespace module for <link href="http://jakarta.apache.org/struts/">Struts</link>
configuration files: <link href="http://jakarta.apache.org/struts/dtds/struts-config_1_1.dtd">http://jakarta.apache.org/struts/dtds/struts-config_1_1.dtd</link>.</par>
"""

__version__ = "$Revision$".split()[1]
# $Source$

from ll.xist import xsc, sims
from ll.xist.ns import xml


xmlns = "http://jakarta.apache.org/struts/dtds/struts-config_1_1.dtd"


class DocType(xsc.DocType):
	def __init__(self):
		xsc.DocType.__init__(
			self,
			'struts-config PUBLIC '
			'"-//Apache Software Foundation//DTD Struts Configuration 1.1//EN" '
			'"http://jakarta.apache.org/struts/dtds/struts-config_1_1.dtd"'
		)


class ElementWithID(xsc.Element):
	class Attrs(xsc.Element.Attrs):
		class id(xsc.IDAttr): pass


class action(ElementWithID):
	xmlns = xmlns
	class Attrs(ElementWithID.Attrs):
		class attribute(xsc.TextAttr): pass
		class className(xsc.TextAttr): pass
		class forward(xsc.TextAttr): pass
		class include(xsc.TextAttr): pass
		class input(xsc.TextAttr): pass
		class name(xsc.TextAttr): pass
		class parameter(xsc.TextAttr): pass
		class path(xsc.TextAttr): required = True
		class prefix(xsc.TextAttr): pass
		class roles(xsc.TextAttr): pass
		class scope(xsc.TextAttr): values = (u"request", u"session")
		class suffix(xsc.TextAttr): pass
		class type(xsc.TextAttr): pass
		class unknown(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")
		class validate(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")


class action_mappings(ElementWithID):
	xmlns = xmlns
	xmlname = "action-mappings"
	class Attrs(ElementWithID.Attrs):
		class type(xsc.TextAttr): pass


class controller(ElementWithID):
	xmlns = xmlns
	class Attrs(ElementWithID.Attrs):
		class bufferSize(xsc.TextAttr): pass
		class className(xsc.TextAttr): pass
		class contentType(xsc.TextAttr): pass
		class debug(xsc.TextAttr): pass
		class forwardPattern(xsc.TextAttr): pass
		class inputForward(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")
		class locale(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")
		class maxFileSize(xsc.TextAttr): pass
		class memFileSize(xsc.TextAttr): pass
		class multipartClass(xsc.TextAttr): pass
		class nocache(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")
		class pagePattern(xsc.TextAttr): pass
		class processorClass(xsc.TextAttr): pass
		class tempDir(xsc.TextAttr): pass


class data_source(ElementWithID):
	xmlns = xmlns
	xmlname = "data-source"
	class Attrs(ElementWithID.Attrs):
		class className(xsc.TextAttr): pass
		class key(xsc.TextAttr): pass
		class type(xsc.TextAttr): pass


class data_sources(ElementWithID):
	xmlns = xmlns
	xmlname = "data-sources"


class description(ElementWithID):
	xmlns = xmlns
	pass


class display_name(ElementWithID):
	xmlns = xmlns
	xmlname = "display-name"


class exception(ElementWithID):
	xmlns = xmlns
	class Attrs(ElementWithID.Attrs):
		class bundle(xsc.TextAttr): pass
		class className(xsc.TextAttr): pass
		class handler(xsc.TextAttr): pass
		class key(xsc.TextAttr): required = True
		class path(xsc.TextAttr): pass
		class scope(xsc.TextAttr): pass
		class type(xsc.TextAttr): required = True


class form_bean(ElementWithID):
	xmlns = xmlns
	xmlname = "form-bean"
	class Attrs(ElementWithID.Attrs):
		class className(xsc.TextAttr): pass
		class dynamic(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")
		class name(xsc.TextAttr): required = True
		class type(xsc.TextAttr): required = True


class form_beans(ElementWithID):
	xmlns = xmlns
	xmlname = "form-beans"
	class Attrs(ElementWithID.Attrs):
		class type(xsc.TextAttr): pass


class form_property(xsc.Element):
	xmlns = xmlns
	xmlname = "form-property"
	class Attrs(xsc.Element.Attrs):
		class className(xsc.TextAttr): pass
		class initial(xsc.TextAttr): pass
		class name(xsc.TextAttr): required = True
		class size(xsc.TextAttr): pass
		class type(xsc.TextAttr): required = True


class forward(ElementWithID):
	xmlns = xmlns
	class Attrs(ElementWithID.Attrs):
		class className(xsc.TextAttr): pass
		class contextRelative(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")
		class name(xsc.TextAttr): required = True
		class path(xsc.TextAttr): required = True
		class redirect(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")


class global_exceptions(ElementWithID):
	xmlns = xmlns
	xmlname = "global-exceptions"


class global_forwards(ElementWithID):
	xmlns = xmlns
	xmlname = "global-forwards"
	class Attrs(ElementWithID.Attrs):
		class type(xsc.TextAttr): pass


class icon(ElementWithID):
	xmlns = xmlns


class large_icon(ElementWithID):
	xmlns = xmlns
	xmlname = "large-icon"


class message_resources(ElementWithID):
	xmlns = xmlns
	xmlname = "message-resources"
	class Attrs(ElementWithID.Attrs):
		class className(xsc.TextAttr): pass
		class factory(xsc.TextAttr): pass
		class key(xsc.TextAttr): pass
		class null(xsc.TextAttr): values = (u"true", u"false", u"yes", u"no")
		class parameter(xsc.TextAttr): required = True


class plug_in(ElementWithID):
	xmlns = xmlns
	xmlname = "plug-in"
	class Attrs(ElementWithID.Attrs):
		class className(xsc.TextAttr): required = True


class set_property(ElementWithID):
	xmlns = xmlns
	xmlname = "set-property"
	class Attrs(ElementWithID.Attrs):
		class property(xsc.TextAttr): required = True
		class value(xsc.TextAttr): required = True


class small_icon(ElementWithID):
	xmlns = xmlns
	xmlname = "small-icon"


class struts_config(ElementWithID):
	xmlns = xmlns
	xmlname = "struts-config"


action_mappings.model = sims.Elements(action)
data_sources.model = sims.Elements(data_source)
exception.model = \
forward.model = sims.Elements(display_name, description, set_property, icon)
global_exceptions.model = sims.Elements(exception)
action.model = sims.Elements(exception, description, forward, display_name, set_property, icon)
form_beans.model = sims.Elements(form_bean)
form_bean.model = sims.Elements(form_property, display_name, description, set_property, icon)
global_forwards.model = sims.Elements(forward)
struts_config.model = sims.Elements(global_exceptions, controller, message_resources, data_sources, plug_in, action_mappings, form_beans, global_forwards)
controller.model = \
data_source.model = \
form_property.model = \
message_resources.model = \
plug_in.model = sims.Elements(set_property)
icon.model = sims.Elements(small_icon, large_icon)
set_property.model = sims.Empty()
description.model = \
display_name.model = \
large_icon.model = \
small_icon.model = sims.NoElements()


# this is no "official" struts-config element, but nonetheless useful for generating
# the final XML output
class user_struts_config(xsc.Element):
	xmlns = xmlns
	xmlname = "user-struts-config"
	model = struts_config.model

	def convert(self, converter):
		e = xsc.Frag(
			xml.XML10(),
			u"\n",
			DocType(),
			u"\n",
			struts_config(self.content)
		)
		return e.convert(converter)
