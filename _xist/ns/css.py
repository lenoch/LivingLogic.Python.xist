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
<doc:par>An &xist; module that contains elements that can be used to generate
CSS files.</doc:par>
"""

__version__ = tuple(map(int, "$Revision$"[11:-2].split(".")))
# $Source$

from xist import xsc, helpers

class css(xsc.Element):
	"""
	The root element
	"""
	empty = 0

	def publish(self, publisher):
		publisher.pushTextFilter(helpers.escapeCSS)
		# publish the imports first
		imports = self.find(type=import_)
		for i in imports:
			publisher.publish(u"\n")
			i.publish(publisher)
		# FIXME: publish global and media specific rules in their given order
		rules = self.find(type=rule)
		for r in rules:
			publisher.publish(u"\n")
			r.publish(publisher)
		publisher.popTextFilter()

class import_(xsc.Element):
	"""
	<doc:par>A CSS import rule.</doc:par>
	"""
	empty = 0
	name = "import"

	def publish(self, publisher):
		publisher.publish(u'@import url("')
		self.content.publish(publisher)
		publisher.publish(u'");')

class charset(xsc.Element):
	"""
	<doc:par>The character set of the stylesheet. Will be set automatically
	on publishing.</doc:par>
	"""
	empty = 1
	
	def publish(self, publisher):
		publisher.publish(u'@charset "')
		publisher.publish(unicode(publisher.encoding))
		publisher.publish(u'";')

class rule(xsc.Element):
	"""
	<doc:par>One CSS rule (with potentially multiple <pyref class="sel">selectors</pyref>).</doc:par>
	"""
	empty = 0

	def publish(self, publisher):
		sels = self.find(type=sel)
		props = self.find(type=prop, subtype=1)

		for i in xrange(len(sels)):
			if i != 0:
				publisher.publish(u", ")
			sels[i].publish(publisher)
		publisher.publish(u" { ")
		for i in xrange(len(props)):
			if i != 0:
				publisher.publish(u" ")
			props[i].publish(publisher)
		publisher.publish(u" }")

class sel(xsc.Element):
	"""
	<doc:par>A CSS selector.</doc:par>
	"""
	empty = 0

	def publish(self, publisher):
		self.content.publish(publisher)

class prop(xsc.Element):
	"""
	<doc:par>A CSS property.</doc:par>
	"""
	empty = 0
	attrHandlers = {"important": xsc.BoolAttr}

	def publish(self, publisher):
		publisher.publish(u"%s: " % self.name())
		self.content.publish(publisher)
		if self.hasAttr("important"):
			publisher.publish(u" !important")
		publisher.publish(u";")

class margin_top(prop):
	"""Set the top margin of a box."""
	name = "margin-top"

class margin_right(prop):
	"""Set the right margin of a box."""
	name = "margin-right"

class margin_bottom(prop):
	"""Set the bottom margin of a box."""
	name = "margin-bottom"

class margin_left(prop):
	"""Set the left margin of a box."""
	name = "margin-left"

class margin(prop):
	"""
	The <class>margin</class> property is a shorthand property for setting 
	<class>margin_top</class>, <class>margin_right</class>, <class>margin_bottom</class>,
	and <class>margin_left</class> at the same place in the style sheet.
	"""
class padding_top(prop):
	"""Set the top padding of a box."""
	name = "padding-top"

class padding_right(prop):
	"""Set the right padding of a box."""
	name = "padding-right"

class padding_bottom(prop):
	"""Set the bottom padding of a box."""
	name = "padding-bottom"

class padding_left(prop):
	"""Set the left padding of a box."""
	name = "padding-left"

class padding(prop):
	"""
	The <class>padding</class> property is a shorthand property for setting 
	<class>padding_top</class>, <class>padding_right</class>, <class>padding_bottom</class>,
	and <class>padding_left</class> at the same place in the style sheet.
	"""

class border_top_width(prop):
	"""Set the top border width of a box."""
	name = "border-top-width"

class border_right_width(prop):
	"""Set the right border width of a box."""
	name = "border-right-width"

class border_bottom_width(prop):
	"""Set the bottom border width of a box."""
	name = "border-bottom-width"

class border_left_width(prop):
	"""Set the left border width of a box."""
	name = "border-left-width"

class border_width(prop):
	"""
	The <class>border_width</class> property is a shorthand property for setting 
	<class>border__top_width</class>, <class>border_right_width</class>, 
	<class>border_bottom_width</class>, and <class>border_left_width</class> at the same place 
	in the style sheet.
	"""
	name = "border-width"

class border_top_color(prop):
	"""Set the top border color of a box."""
	name = "border-top-color"

class border_right_color(prop):
	"""Set the right border color of a box."""
	name = "border-right-color"

class border_bottom_color(prop):
	"""Set the bottom border color of a box."""
	name = "border-bottom-color"

class border_left_color(prop):
	"""Set the left border color of a box."""
	name = "border-left-color"

class border_color(prop):
	"""
	The <class>border_color</class> property is a shorthand property for setting 
	<class>border__top_color</class>, <class>border_right_color</class>, 
	<class>border_bottom_color</class>, and <class>border_left_color</class> at the same place 
	in the style sheet.
	"""
	name = "border-color"

class border_top_style(prop):
	"""Set the top border style of a box."""
	name = "border-top-style"

class border_right_style(prop):
	"""Set the right border style of a box."""
	name = "border-right-style"

class border_bottom_style(prop):
	"""Set the bottom border style of a box."""
	name = "border-bottom-style"

class border_left_style(prop):
	"""Set the left border style of a box."""
	name = "border-left-style"

class border_style(prop):
	"""
	The <class>border_style</class> property is a shorthand property for setting 
	<class>border__top_style</class>, <class>border_right_style</class>, 
	<class>border_bottom_style</class>, and <class>border_left_style</class> at the same place 
	in the style sheet.
	"""
	name = "border-style"

class border_top(prop):
	"""Set the top border of a box."""
	name = "border-top"

class border_right(prop):
	"""Set the right border of a box."""
	name = "border-right"

class border_bottom(prop):
	"""Set the bottom border of a box."""
	name = "border-bottom"

class border_left(prop):
	"""Set the left border of a box."""
	name = "border-left"

class border(prop):
	"""
	The <class>border</class> property is a shorthand property for setting 
	<class>border__top</class>, <class>border_right</class>, 
	<class>border_bottom</class>, and <class>border_left</class> at the same place 
	in the style sheet.
	"""

class display(prop):
	"""
	<doc:par>Sets the display type of a box. The values of this property
	have the following meanings:</doc:par>
	<doc:ulist>
	<doc:item><lit>block</lit>: This value causes an element to generate a principal block box.</doc:item> 
	<doc:item>lit>inline</lit>: This value causes an element to generate one or more inline boxes.</doc:item> 
	<doc:item><lit>list-item</lit>: This value causes an element (e.g., <pyref module="xist.ns.html" class="li"><class>li</class></pyref>
	in <pyref module="xist.ns.html">&html;</pyref>) to generate a principal block box and a 
	list-item inline box.</doc:Item>
	<doc:item><lit>marker</lit>: This value declares generated content before or after a box 
	to be a marker. This value should only be used with <lit>:before</lit> and
	<lit>:after</lit> pseudo-elements attached to block-level elements. In other cases,
	this value is interpreted as <lit>inline</lit>.</doc:item>
	<doc:item><lit>none</lit>: This value causes an element to generate no boxes 
	in the formatting structure (i.e., the element has no effect on layout). Descendant elements 
	do not generate any boxes either; this behavior cannot be overridden by setting the 
	<class>display</class> property on the descendants. Please note that a display of 
	<lit>none</lit> does not create an invisible box; it creates no box at all. CSS includes 
	mechanisms that enable an element to generate boxes in the formatting structure that 
	affect formatting but are not visible themselves.</doc:item>
	<doc:item><lit>run-in</lit> and <lit>compact</lit>: These values create either block 
	or inline boxes, depending on context. Properties apply to run-in and compact boxes based 
	on their final status (inline-level or block-level). For example, the 
	<pyref class="white_space"><class>white_space</class></pyref> property only applies if the box 
	becomes a block box.</doc:item> 
	<doc:item><lit>table</lit>, <lit>inline-table</lit>, <lit>table-row-group</lit>,
	<lit>table-column</lit>, <lit>table-column-group</lit>, <lit>table-header-group</lit>,
	<lit>table-footer-group</lit>, <lit>table-row</lit>, <lit>table-cell</lit>, and <lit>table-caption</lit>: 
	These values cause an element to behave like a table element.</doc:item>
	</doc:ulist>
	"""

class position(prop):
	"""
	<doc:par>The <class>position</class> and <pyref class="float"><class>float</class></pyref> properties 
	determine which of the CSS2 positioning algorithms is used to calculate the 
	position of a box. The values of this property have the following meanings:</doc:par>
	<doc:ulist>
	<doc:item><lit>static</lit>: The box is a normal box, laid out according to the normal flow. 
	The <pyref class="left"><class>left</class></pyref> and <pyref class="top"><class>top</class></pyref>
	properties do not apply.</doc:item> 
	<doc:item><lit>relative</lit>: The box's position is calculated according to the normal flow
	(this is called the position in normal flow). Then the box is offset relative to its normal 
	position. When a box <lit><replaceable>B</replaceable></lit> is relatively positioned, 
	the position of the following box is calculated as though <lit><replaceable>B</replaceable></lit>
	were not offset.</doc:item>
	<doc:item><lit>absolute</lit>: The box's position (and possibly size) is specified with the 
	<pyref class="left"><class>left</class></pyref>, <pyref class="right"><class>right</class></pyref>,
	<pyref class="top"><class>top</class></pyref>, and <pyref class="bottom"><class>bottom</class></pyref>
	properties. These properties specify offsets with respect to the box's containing block.
	Absolutely positioned boxes are taken out of the normal flow. This means they have no impact
	on the layout of later siblings. Also, though absolutely positioned boxes have margins,
	they do not collapse with any other margins.</doc:item>
	<doc:item><lit>fixed</lit>: The box's position is calculated according to the 
	<lit>absolute</lit> model, but in addition, the box is fixed with respect to some reference.
	In the case of continuous media, the box is fixed with respect to the viewport
	(and doesn't move when scrolled). In the case of paged media, the box is fixed with respect
	to the page, even if that page is seen through a viewport (in the case of a print-preview,
	for example).</doc:item>
	</doc:ulist>
	"""

class top(prop):
	"""
	This property specifies how far a box's top content edge
	is offset below the top edge of the box's containing block.
	"""

class right(prop):
	"""
	This property specifies how far a box's right content edge
	is offset to the left of the right edge of the box's containing block.
	"""

class bottom(prop):
	"""
	This property specifies how far a box's bottom content edge
	is offset above the bottom of the box's containing block.
	"""

class left(prop):
	"""
	This property specifies how far a box's left content edge
	is offset to the right of the left edge of the box's
	containing block. 
	"""

class float(prop):
	"""
	<doc:par>This property specifies whether a box should float to the
	left, right, or not at all. It may be set for elements that
	generate boxes that are not absolutely positioned. The values
	of this property have the following meanings:</doc:par>
	<doc:ulist>
	<doc:item><lit>left</lit>: The element generates a block box that is 
	floated to the left. Content flows on the right side of the box, 
	starting at the top (subject to the <pyref class="clear"><class>clear</class></pyref>
	property). The <pyref class="display"><class>display</class></pyref> is ignored, 
	unless it has the value <lit>none</lit>.</doc:item> 
	<doc:item><lit>right</lit>: Same as <lit>left</lit>, but content flows on the 
	left side of the box, starting at the top.</doc:item> 
	<doc:item><lit>none</lit>: The box is not floated.</doc:item>
	</doc:ulist>
	"""

class clear(prop):
	"""
	<doc:par>This property indicates which sides of an element's box(es) may <em>not</em>
	be adjacent to an earlier floating box. (It may be that the element itself has floating 
	descendants; the <class>clear</class> property has no effect on those.)</doc:par>
	
	<doc:par>This property may only be specified for block-level elements (including floats).
	For compact and run-in boxes, this property applies to the final block box to which the
	compact or run-in box belongs.</doc:par>
	
	<doc:par>Values have the following meanings when applied to non-floating block boxes:</doc:par>
	
	<doc:ulist>
	<doc:item><lit>left</lit>: The top margin of the generated box is increased enough
	that the top border edge is below the bottom outer edge of any left-floating boxes
	that resulted from elements earlier in the source document.</doc:item> 
	<doc:item><lit>right</lit> The top margin of the generated box is increased enough
	that the top border edge is below the bottom outer edge of any right-floating boxes
	that resulted from elements earlier in the source document.</doc:item>
	<doc:item><lit>both</lit>: The generated box is moved below all floating boxes of 
	earlier elements in the source document.</doc:item>
	<doc:item><lit>none</lit>: No constraint on the box's position with respect to floats.</doc:item>
	</doc:ulist>

	<doc:par>When the property is set on floating elements, it results in a modification 
	of the rules for positioning the float. An extra constraint is added: 
	The top outer edge of the float must be below the bottom outer edge of all earlier 
	left-floating boxes (in the case of <markup>&lt;clear&gt;left&lt;clear&gt;</markup>),
	or all earlier right-floating boxes (in the case of <markup>&lt;clear&gt;right&lt;clear&gt;</markup>),
	or both (<markup>&lt;clear&gt;both&lt;clear&gt;</markup>).</doc:par>
	"""

class z_index(prop):
	"""
	<doc:par>For a positioned box, the <class>z_index</class>
	property specifies:</doc:par>
	
	<doc:olist>
	<doc:item>The stack level of the box in the current stacking context.</doc:item>
	<doc:item>Whether the box establishes a local stacking context.</doc:item>
	</doc:olist>
	
	<doc:par>Values have the following meanings:</doc:par>
	
	<doc:ulist>
	<doc:item><lit><replaceable>integer</replaceable></lit>: This integer is the stack level 
	of the generated box in the current stacking context. The box also establishes a 
	local stacking context in which its stack level is <lit>0</lit>.</doc:item>
	<doc:item><lit>auto</lit>: The stack level of the generated box in the current stacking context 
	is the same as its parent's box. The box does not establish a new local stacking context.</doc:item>
	</doc:ulist>
	"""
	name = "z-index"

class direction(prop):
	"""
	<doc:par>This property specifies the base writing direction of blocks 
	and the direction of embeddings and overrides
	(see <pyref class="unicode_bidi"><class>unicode_bidi</class></pyref>)
	for the Unicode bidirectional algorithm. In addition, it specifies the direction
	of table column layout, the direction of horizontal overflow, and the position
	of an incomplete last line in a block in case of <markup>&lt;text_align&gt;justify&lt;/text_align&gt;</markup>.</doc:par> 
	
	<doc:par>Values for this property have the following meanings:</doc:par>
	
	<doc:ulist>
	<doc:item><lit>ltr</lit>: Left-to-right direction.</doc:item> 

	<doc:item><lit>rtl</lit>: Right-to-left direction.</doc:item>
	</doc:ulist>
	
	<doc:par>For the <class>direction</class> property to have any
	effect on inline-level elements, the <pyref class="unicode_bidi"><class>unicode_bidi</class></pyref>
	property's value must be <lit>embed</lit> or <lit>override</lit>.</doc:par>
	"""

class unicode_bidi(prop):
	"""
	<doc:par>Values for this property have the following meanings:</doc:par>

	<doc:ulist>
	<doc:item><lit>normal</lit>: The element does not open an additional level 
	of embedding with respect to the bidirectional algorithm. For inline-level elements,
	implicit reordering works across element boundaries.</doc:item>
	<doc:item><lit>embed</lit>: If the element is inline-level, this value opens 
	an additional level of embedding with respect to the bidirectional algorithm. 
	The direction of this embedding level is given by the
	<pyref class="direction><class>direction</class></pyref> property. Inside the element,
	reordering is done implicitly. This corresponds to adding a LRE (U+202A; for 
	<markup>&lt;direction&lt;/gt;ltr&lt;/direction&lt;/gt;</markup>) or RLE
	(U+202B; for <markup>&lt;direction&lt;/gt;rtl&lt;/direction&lt;/gt;</markup>)
	at the start of the element and a PDF (U+202C) at the end of the element.</doc:item>
	<doc:item><lit>bidi-override</lit>: If the element is inline-level or a block-level
	element that contains only inline-level elements, this creates an override.
	This means that inside the element, reordering is strictly in sequence according
	to the <pyref class="direction"><class>direction</class></pyref> property; the implicit part
	of the bidirectional algorithm is ignored. This corresponds to adding a LRO (U+202D; for
	<markup>&lt;direction&lt;/gt;ltr&lt;/direction&lt;/gt;</markup>) or RLO
	(U+202E; for <markup>&lt;direction&lt;/gt;rtl&lt;/direction&lt;/gt;</markup>) at the start
	of the element and a PDF (U+202C) at the end of the element.</doc:item>
	</doc:ulist>

	<doc:par>The final order of characters in each block-level element is the same
	as if the bidi control codes had been added as described above, markup had been
	stripped, and the resulting character sequence had been passed to an implementation
	of the Unicode bidirectional algorithm for plain text that produced the same line-breaks
	as the styled text. In this process, non-textual entities such as images are treated as
	neutral characters, unless their <class>unicode_bidi</class> property has a value other
	than <lit>normal</lit>, in which case they are treated as strong characters in the
	<pyref class="direction><class>direction</class></pyref> specified for the element.</doc:par> 

	<doc:par>Please note that in order to be able to flow inline boxes in a uniform direction
	(either entirely left-to-right or entirely right-to-left), more inline boxes
	(including anonymous inline boxes) may have to be created, and some inline boxes may
	have to be split up and reordered before flowing.</doc:par>

	<doc:par>Because the Unicode algorithm has a limit of 15 levels of embedding,
	care should be taken not to use <class>unicode_bidi</class> with a value other
	than <lit>normal</lit> unless appropriate. In particular, a value of <lit>inherit</lit>
	should be used with extreme caution. However, for elements that are, in general,
	intended to be displayed as blocks, a setting of
	<markup>&lt;unicode_bidi&lt;/gt;embed&lt;/unicode_bidi&lt;/gt;</markup> is preferred
	to keep the element together in case display is changed to inline.</doc:par>
	"""
	name = "unicode-bidi"

class width(prop):
	"""
	<doc:par>This property specifies the content width of boxes generated by block-level 
	and replaced elements.</doc:par>

	<doc:par>This property does not apply to non-replaced inline-level elements.
	The width of a non-replaced inline element's boxes is that of the rendered content
	within them (before any relative offset of children). Recall that inline boxes flow
	into line boxes. The width of line boxes is given by the their containing block,
	but may be shorted by the presence of floats.</doc:par> 
	
	<doc:par>The width of a replaced element's box is intrinsic and may be scaled by the user agent
	if the value of this property is different than <lit>auto</lit>.</doc:par>
	"""

class min_width(prop):
	"""
	<doc:par>This property allow the authors to constrain box widths to a certain range.</doc:par>
	"""
	name = "min-width"

class max_width(prop):
	"""
	<doc:par>This property allow the authors to constrain box widths to a certain range.</doc:par>
	"""
	name = "max-width"

class height(prop):
	"""
	<doc:par>This property specifies the content height of boxes generated by block-level 
	and replaced elements.</doc.par> 

	<doc:par>This property does not apply to non-replaced inline-level elements.
	The height of a non-replaced inline element's boxes is given by the element's
	(possibly inherited) <pyref class="line_height"><class>line_height</class></pyref> value.</doc:par> 
	"""

class min_height(prop):
	"""
	<doc:par>This property allow the authors to constrain box heights to a certain range.</doc:par>
	"""
	name = "min-height"

class max_height(prop):
	"""
	<doc:par>This property allow the authors to constrain box heights to a certain range.</doc:par>
	"""
	name = "max-height"

class line_height(prop):
	"""
	<doc:par>If the property is set on a block-level element whose content
	is composed of inline-level elements, it specifies the minimal height
	of each generated inline box.</doc:par> 

	<doc:par>If the property is set on an inline-level element, it specifies
	the exact height of each box generated by the element. (Except for inline
	replaced elements, where the height of the box is given by the
	<pyref class="height"><class>height</class></pyref> property.)</doc:par>
	"""
	name = "line-height"

class vertical_align(prop):
	"""
	<doc:par>This property affects the vertical positioning inside a line box of the boxes
	generated by an inline-level element. The following values only have meaning with
	respect to a parent inline-level element, or to a parent block-level element,
	if that element generates anonymous inline boxes; they have no effect if no
	such parent exists.</doc:par>

	<doc:ulist>
	<doc:item><lit>baseline</lit>: Align the baseline of the box with the baseline of the parent box.
	If the box doesn't have a baseline, align the bottom of the box with the parent's baseline.</doc:item> 
	<doc:item><lit>middle</lit>: Align the vertical midpoint of the box with the baseline
	of the parent box plus half the x-height of the parent.</doc:item>
	<doc:item><lit>sub</lit>: Lower the baseline of the box to the proper position
	for subscripts of the parent's box. (This value has no effect on the font size
	of the element's text.)</doc:item>
	<doc:item><lit>super</lit>: Raise the baseline of the box to the proper position
	for superscripts of the parent's box. (This value has no effect on the font size
	of the element's text.)</doc:item>
	<doc:item><lit>text-top</lit>: Align the top of the box with the top of the parent
	element's font.</doc:item> 
	<doc:item><lit>text-bottom</lit>: Align the bottom of the box with the bottom of the
	parent element's font.</doc:item>
	<doc:item><lit><replaceable>percentage</replaceable></lit>: Raise (positive value)
	or lower (negative value) the box by this distance (a percentage of the
	<pyref class="line_height"><class>line_height</class></pyref> value). The value <lit>0%</lit>
	means the same as <lit>baseline</lit>.</doc:item> 
	<doc:item><lit><replaceable>length</replaceable></lit>: Raise (positive value)
	or lower (negative value) the box by this distance. The value <lit>0cm</lit>
	means the same as <lit>baseline</lit>.</doc:item>
	</doc:ulist>

	<doc:par>The remaining values refer to the line box in which the generated box appears:</doc:par>
	
	<doc:ulist>
	<doc:item><lit>top</lit>: Align the top of the box with the top of the line box.</doc:item> 
	<doc:item><lit>bottom</lit>: Align the bottom of the box with the bottom of the line box.</doc:item> 
	</doc:ulist>
	"""
	name = "vertical-align"

class overflow(prop):
	"""
	<doc:par>This property specifies whether the content of a block-level element is clipped
	when it overflows the element's box (which is acting as a containing block for the content).
	Values have the following meanings:</doc:par>
	
	<doc:ulist>
	<doc:Item><lit>visible</lit>: This value indicates that content is not clipped, i.e.,
	it may be rendered outside the block box.</doc:item>
	<doc:item><lit>hidden</lit>: This value indicates that the content is clipped
	and that no scrolling mechanism should be provided to view the content outside
	the clipping region; users will not have access to clipped content. The size and shape
	of the clipping region is specified by the <pyref class="clip"><class>clip</class></pyref> property.</doc:item> 
	<doc:item><lit>scroll</lit>: This value indicates that the content is clipped and
	that if the user agent uses scrolling mechanism that is visible on the screen
	(such as a scroll bar or a panner), that mechanism should be displayed for a box
	whether or not any of its content is clipped. This avoids any problem with scrollbars
	appearing and disappearing in a dynamic environment. When this value is specified
	and the target medium is <lit>print</lit> or <lit>projection</lit>, overflowing
	content should be printed. </doc:item>
	<doc:item><lit>auto</lit>: The behavior of the <lit>auto</lit> value is user
	agent-dependent, but should cause a scrolling mechanism to be provided
	for overflowing boxes.</doc:item>
	</doc:ulist>
	<doc:par>Even if <class>overflow</class> is set to <lit>visible</lit>, content may be clipped
	to a UA's document window by the native operating environment.</doc:par> 
	"""

class clip(prop):
	"""
	<doc:par>The <class>clip</class> property applies to elements that have a
	<pyref class="overflow"><class>overflow</class></pyref> property with a value
	other than <lit>visible</lit>. Values have the following meanings:</doc:par>

	<doc:ulist>
	<doc:item><lit>auto</lit>: The clipping region has the same size and
	location as the element's box(es).</doc:item>
	<doc:item><doc:par><lit><replaceable>shape</replaceable></lit>: In CSS2, the only valid
	<lit><replaceable>shape</replaceable></lit> value is: rect
	(<lit><replaceable>top</replaceable> <replaceable>right</replaceable> <replaceable>bottom</replaceable> <replaceable>left</replaceable></lit>)
	where <lit><replaceable>top</replaceable></lit>, <lit><replaceable>bottom</replaceable></lit>,
	<lit><replaceable>right</replaceable></lit>, and <lit><replaceable>left</replaceable></lit>
	specify offsets from the respective sides of the box.</doc:par>

	<doc:par><lit><replaceable>top</replaceable></lit>, <lit><replaceable>right</replaceable></lit>,
	<lit><replaceable>bottom</replaceable></lit>, and <lit><replaceable>left</replaceable></lit>
	may either have a <lit><replaceable>length</replaceable></lit> value or <lit>auto</lit>.
	Negative lengths are permitted. The value <lit>auto</lit> means that a given edge of
	the clipping region will be the same as the edge of the element's generated box
	(i.e., <lit>auto</lit> means the same as <lit>0</lit>.)</doc:par>

	<doc:par>When coordinates are rounded to pixel coordinates, care should be taken that
	no pixels remain visible when <lit><replaceable>left</replaceable> + <replaceable>right</replaceable></lit>
	is equal to the element's width (or <lit><replaceable>top</replaceable> + <replaceable>bottom</replaceable></lit>
	equals the element's height), and conversely that no pixels remain hidden when these values are 0.</doc:par>
	</doc:item>
	/doc:list>

	<doc:par>The element's ancestors may also have clipping regions (in case their
	<pyref class="overflow"><class>overflow</class></pyref> property is not <lit>visible</lit>);
	what is rendered is the intersection of the various clipping regions.</doc:par> 

	<doc:par>If the clipping region exceeds the bounds of the UA's document window,
	content may be clipped to that window by the native operating environment.</doc:par> 
	"""

class visibility(prop):
	"""
	<doc:par>The <class>visibility</class> property specifies whether the boxes generated
	by an element are rendered. Invisible boxes still affect layout (set the
	<pyref class="display"><class>display</class></pyref> property to <lit>none</lit> to
	suppress box generation altogether). Values have the following meanings:</doc:par>

	<doc:ulist>
	<doc:item><lit>visible</lit>: The generated box is visible.</doc:item> 
	<doc:item><lit>hidden</lit>: The generated box is invisible (fully transparent),
	but still affects layout.</doc:item> 
	<doc:item><lit>collapse</lit>: Used for dynamic row and column effects in tables.
	If used on elements other than rows or columns, <lit>collapse</lit> has the same
	meaning as <lit>hidden</lit>.</doc:par>

	<doc:par>This property may be used in conjunction with scripts to create dynamic effects.</doc:par>
	"""

class content(prop):
	"""
	<doc:par>This property is used with the <lit>:before</lit> and <lit>:after</lit>
	pseudo-elements to generate content in a document.</doc:par> 
	"""

class quotes(prop):
	"""
	<doc:par>This property specifies quotation marks for any number of embedded quotations.</doc:par> 
	"""

class counter_reset(prop):
	"""
	"""
	name = "counter-reset"

class counter_increment(prop):
	"""
	"""
	name = "counter-increment"

class marker_offset(prop):
	"""
	"""
	name = "marker-offset"

class list_style_type(prop):
	"""
	"""
	name = "list-style-type"

class list_style_image(prop):
	"""
	"""
	name = "list-style-image"

class list_style_position(prop):
	"""
	"""
	name = "list-style-position"

class list_style(prop):
	"""
	"""
	name = "list-style"

class size(prop):
	"""
	"""

class marks(prop):
	"""
	"""

class page_break_before(prop):
	"""
	"""
	name = "page-break-before"

class page_break_after(prop):
	"""
	"""
	name = "page-break-after"

class page_break_inside(prop):
	"""
	"""
	name = "page-break-inside"

class page(prop):
	"""
	"""

class orphans(prop):
	"""
	"""

class widows(prop):
	"""
	"""

class color(prop):
	"""
	"""

class background_color(prop):
	"""
	"""
	name = "background-color"

class background_image(prop):
	"""
	"""
	name = "background-image"

class background_repeat(prop):
	"""
	"""
	name = "background-repeat"

class background_attachment(prop):
	"""
	"""
	name = "background-attachment"

class background_position(prop):
	"""
	"""
	name = "background-position"

class background(prop):
	"""
	"""

class font_family(prop):
	"""
	"""
	name = "font-family"

class font_style(prop):
	"""
	"""
	name = "font-style"

class font_variant(prop):
	"""
	"""
	name = "font-variant"

class font_weight(prop):
	"""
	"""
	name = "font-weight"

class font_stretch(prop):
	"""
	"""
	name = "font-stretch"

class font_size(prop):
	"""
	"""
	name = "font-size"

class font_size_adjust(prop):
	"""
	"""
	name = "font-size-adjust"

class font(prop):
	"""
	"""

class text_indent(prop):
	"""
	"""
	name = "text-indent"

class text_align(prop):
	"""
	"""
	name = "text-align"

class text_decoration(prop):
	"""
	"""
	name = "text-decoration"

class text_shadow(prop):
	"""
	"""
	name = "text-shadow"

class letter_spacing(prop):
	"""
	"""
	name = "letter-spacing"

class word_spacing(prop):
	"""
	"""
	name = "word-spacing"

class text_transform(prop):
	"""
	"""
	name = "text-transform"

class white_space(prop):
	"""
	"""
	name = "white-space"

class caption_side(prop):
	"""
	"""
	name = "caption-side"

class table_layout(prop):
	"""
	"""
	name = "table-layout"

class border_collapse(prop):
	"""
	"""
	name = "border-collapse"

class border_spacing(prop):
	"""
	"""
	name = "border-spacing"

class empty_cells(prop):
	"""
	"""
	name = "empty-cells"

class speak_header(prop):
	"""
	"""
	name = "speak-header"

class cursor(prop):
	"""
	"""

class outline(prop):
	"""
	"""

class outline_width(prop):
	"""
	"""
	name = "outline-width"

class outline_style(prop):
	"""
	"""
	name = "outline-style"

class outline_color(prop):
	"""
	"""
	name = "outline-color"

class volume(prop):
	"""
	"""

class speak(prop):
	"""
	"""

class pause_before(prop):
	"""
	"""
	name = "pause-before"

class pause_after(prop):
	"""
	"""
	name = "pause-after"

class pause(prop):
	"""
	"""

class cue_before(prop):
	"""
	"""
	name = "cue-before"

class cue_after(prop):
	"""
	"""
	name = "cue-after"

class cue(prop):
	"""
	"""
	name = "cue"

class play_during(prop):
	"""
	"""
	name = "play-during"

class azimuth(prop):
	"""
	"""

class elevation(prop):
	"""
	"""

class speech_rate(prop):
	"""
	"""
	name = "speech-rate"

class voice_family(prop):
	"""
	"""
	name = "voice-family"

class pitch(prop):
	"""
	"""

class pitch_range(prop):
	"""
	"""
	name = "pitch-range"

class stress(prop):
	"""
	"""

class richness(prop):
	"""
	"""

class speak_punctuation(prop):
	"""
	"""
	name = "speak-punctuation"

class speak_numeral(prop):
	"""
	"""
	name = "speak-numeral"

# register all the classes we've defined so far
namespace = xsc.Namespace("css", "http://www.w3.org/TR/REC-CSS2", vars())
