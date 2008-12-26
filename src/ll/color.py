# -*- coding: utf-8 -*-

## Copyright 2004-2008 by LivingLogic AG, Bayreuth/Germany.
## Copyright 2004-2008 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/__init__.py for the license


from __future__ import division

"""
:mod:`ll.color` provides classes and functions for handling RGB colors.
"""


import colorsys

from ll import misc


__docformat__ = "reStructuredText"


class Color(tuple):
	"""
	A :class:`Color` object represents a color with red, green and blue
	components.
	"""
	def __new__(cls, r=0x0, g=0x0, b=0x0, a=0xff):
		"""
		Create a :class:`Color` with the 8 bit red, green, blue and alpha
		components :var:`r`, :var:`g`, :var:`b` and :var:`a`. Values will be
		clipped to the range [0; 255].
		"""
		return tuple.__new__(cls, (max(0, min(int(r), 255)), max(0, min(int(g), 255)), max(0, min(int(b), 255)), max(0, min(int(a), 255))))

	@classmethod
	def fromcss(cls, s):
		"""
		Create a :class:`Color` object from the CSS__ color string :var:`s`.
		All formats from CSS2 are supported (i.e. ``'#xxx'``, ``'#xxxxxx'``,
		``rgb(r, g, b)``, ``rgb(r%, g%, b%)``, ``rgba(r, g, b, a)``,
		``rgba(r%, g%, b%, a)``  and color names like ``'red'``).

		__ http://www.w3.org/TR/css3-color/#colorunits
		"""
		if s.startswith("#"):
			if len(s) == 4:
				return cls(17*int(s[1], 16), 17*int(s[2], 16), 17*int(s[3], 16))
			elif len(s) == 7:
				return cls(int(s[1:3], 16), int(s[3:5], 16), int(s[5:], 16))
		elif s.startswith("rgb(") and s.endswith(")"):
			channels = []
			for x in s[4:-1].split(","):
				x = x.strip()
				if x.endswith("%"):
					v = float(x[:-1])*0xff/100
				else:
					v = int(x)
				channels.append(v)
			return cls(*channels)
		elif s.startswith("rgba(") and s.endswith(")"):
			channels = []
			for x in s[5:-1].split(","):
				x = x.strip()
				if len(channels) == 3: # alpha value
					v = float(x)*0xff
				elif x.endswith("%"):
					v = float(x[:-1])*0xff/100
				else:
					v = int(x)
				channels.append(v)
			return cls(*channels)
		elif s in csscolors:
			return csscolors[s]
		raise ValueError("can't interpret %s as css value" % s)

	@classmethod
	def fromrgb(cls, r, g, b, a=1.0):
		"""
		Create a :class:`Color` object from the red, green, blue and alpha values
		:var:`r`, :var:`g`, :var:`b` and :var:`a`. All values will be clipped
		to the range [0; 1].
		"""
		return cls(255*r, 255*g, 255*b, 255*a)

	@classmethod
	def fromhsv(cls, h, s, v, a=1.0):
		"""
		Create a :class:`Color` object from the hue, saturation and value values
		:var:`h`, :var:`s` and :var:`v` and the alpha value :var:`a`. The hue
		value will be used modulo 1.0, saturation, value and alpha will be clipped
		to the range [0; 1].
		"""
		rgb = colorsys.hsv_to_rgb(h % 1.0, max(0., min(s, 1.)), max(0., min(v, 1.)))
		return cls.fromrgb(*(rgb + (a,)))

	@classmethod
	def fromhls(cls, h, l, s, a=1.0):
		"""
		Create a :class:`Color` object from the hue, luminance and saturation
		values :var:`h`, :var:`l` and :var:`s` and the alpha value :var:`a`.
		The hue value will be used modulo 1.0, luminance, saturation and alpha
		will be clipped to the range [0; 1].
		"""
		rgb = colorsys.hls_to_rgb(h % 1.0, max(0., min(l, 1.)), max(0., min(s, 1.)))
		return cls.fromrgb(*(rgb + (a,)))

	def __repr__(self):
		if self[3] != 0xff:
			return "Color(0x%02x, 0x%02x, 0x%02x, 0x%02x)" % self
		else:
			return "Color(0x%02x, 0x%02x, 0x%02x)" % self[:3]

	def __str__(self):
		"""
		:var:`self` formatted as a CSS color string.
		"""
		if self[3] != 0xff:
			return "rgba(%d,%d,%d,%.3f)" % (self[0], self[1], self[2], self[3]/255.)
		else:
			s = "#%02x%02x%02x" % (self[0], self[1], self[2])
			if s[1]==s[2] and s[3]==s[4] and s[5]==s[6]:
				s = "#%s%s%s" % (s[1], s[3], s[5])
		return s

	def r(self):
		"""
		The red value as an int between 0 and 255.
		"""
		return self[0]

	def g(self):
		"""
		The green value as an int between 0 and 255.
		"""
		return self[1]

	def b(self):
		"""
		The blue value as an int between 0 and 255.
		"""
		return self[2]

	def a(self):
		"""
		The alpha value as an int between 0 and 255.
		"""
		return self[3]

	def rgb(self):
		"""
		The red, green and blue value as a float tuple with values between
		0.0 and 1.0.
		"""
		return (self[0]/255., self[1]/255., self[2]/255.)

	def rgba(self):
		"""
		The red, green, blue and alpha value as a float tuple with values between
		0.0 and 1.0.
		"""
		return (self[0]/255., self[1]/255., self[2]/255., self[3]/255.)

	def hsv(self):
		"""
		:var:`self` as a HSV ("hue, saturation, value") triple.
		All three values are between 0.0 and 1.0.
		"""
		return colorsys.rgb_to_hsv(self[0]/255., self[1]/255., self[2]/255.)

	def hsva(self):
		"""
		:var:`self` as a HSV+alpha ("hue, saturation, value, alpha") tuple.
		All four values are between 0.0 and 1.0.
		"""
		return self.hsv() + (self[3]/255.,)

	def hls(self):
		"""
		:var:`self` as a HLS ("hue, luminance, saturation") triple. All three
		values are between 0.0 and 1.0.
		"""
		return colorsys.rgb_to_hls(self[0]/255., self[1]/255., self[2]/255.)

	def hlsa(self):
		"""
		:var:`self` as a HLS+alpha ("hue, luminance, saturation, alpha") tuple.
		All four values are between 0.0 and 1.0.
		"""
		return self.hls() + (self[3]/255.,)

	@property
	def lum(self):
		"""
		The luminance value from the :prop:`hls` property.
		"""
		return colorsys.rgb_to_hls(self[0]/255., self[1]/255., self[2]/255.)[1]

	def combine(self, r=None, g=None, b=None, a=None):
		"""
		Return a copy of :var:`self` with some of the values replaced by the
		arguments.
		"""
		channels = list(self)
		if r is not None:
			channels[0] = r
		if g is not None:
			channels[1] = g
		if b is not None:
			channels[2] = b
		if a is not None:
			channels[3] = a
		return self.__class__(*channels)

	def withlum(self, lum):
		(h, l, s, a) = self.hlsa()
		return self.fromhls(h, max(0., min(lum, 1.)), s, a)

	def abslum(self, f):
		"""
		Return a copy of :var:`self` with :var:`f` added to the luminocity.
		"""
		(h, l, s, a) = self.hlsa()
		return self.fromhlsa(h, l+f, s, a)

	def rellum(self, f):
		"""
		Return a copy of :var:`self` where the luminocity has been modified:
		If :var:`f` if positive the luminocity will be increased, with ``f==1``
		giving a luminocity of 1. If :var:`f` is negative, the luminocity will be
		decreased with ``f==-1`` giving a luminocity of 0. ``f==0`` will leave
		the luminocity unchanged.
		"""
		(h, l, s, a) = self.hlsa
		if f > 0:
			l += (1-l)*f
		elif f < 0:
			l += l*f
		return self.fromhlsa(h, l, s, a)

	def __add__(self, other):
		return self.__class__(0.5*(self[0]+other[0]), 0.5*(self[1]+other[1]), 0.5*(self[2]+other[2]), 255-(255-self[3])*(255-other[3])/255.)

	def __mul__(self, factor):
		return self.__class__(factor*self[0], factor*self[1], factor*self[2], self[3])

	def __rmul__(self, factor):
		return self.__class__(factor*self[0], factor*self[1], factor*self[2], self[3])

	def __div__(self, factor):
		return self.__class__(self[0]/factor, self[1]/factor, self[2]/factor, self[3])

	def __mod__(self, other):
		"""
		Blends :var:`self` with the background color :var:`other` according to the
		`SVG specification`__

		__ http://www.w3.org/TR/2003/REC-SVG11-20030114/masking.html#SimpleAlphaBlending
		"""
		sa = self[3]/255.
		rsa = 1.-sa
		return self.__class__(self[0]*sa+rsa*other[0], self[1]*sa+rsa*other[1], self[2]*sa+rsa*other[2], 255-rsa*(255-other[3]))


###
### CSS color constants (see http://www.w3.org/TR/css3-color/#html4)
###

maroon = Color(0x80, 0x00, 0x00)
red = Color(0xff, 0x00, 0x00)
orange = Color(0xff, 0xa5, 0x00)
yellow = Color(0xff, 0xff, 0x00)
olive = Color(0x80, 0x80, 0x00)
purple = Color(0x80, 0x00, 0x80)
fuchsia = Color(0xff, 0x00, 0xff)
white = Color(0xff, 0xff, 0xff)
lime = Color(0x00, 0xff, 0x00)
green = Color(0x00, 0x80, 0x00)
navy = Color(0x00, 0x00, 0x80)
blue = Color(0x00, 0x00, 0xff)
aqua = Color(0x00, 0xff, 0xff)
teal = Color(0x00, 0x80, 0x80)
black = Color(0x00, 0x00, 0x00)
silver = Color(0xc0, 0xc0, 0xc0)
gray = Color(0x80, 0x80, 0x80)

# aliases
magenta = purple
cyan = aqua

transparent = Color(0, 0, 0, 0)


csscolors = {
	"maroon": maroon,
	"red": red,
	"orange": orange,
	"yellow": yellow,
	"olive": olive,
	"purple": purple,
	"fuchsia": fuchsia,
	"white": white,
	"lime": lime,
	"green": green,
	"navy": navy,
	"blue": blue,
	"aqua": aqua,
	"teal": teal,
	"black": black,
	"silver": silver,
	"gray": gray,
	"magenta": magenta,
	"cyan": cyan,
}


def css(value):
	return Color.fromcss(value)


def dist(c1, c2):
	"""
	Return the distance between two colors.
	"""

	d0 = c1[0]-c2[0]
	d1 = c1[1]-c2[1]
	d2 = c1[2]-c2[2]
	return d0*d0+d1*d1+d2*d2


def multiply(c1, c2):
	"""
	Multiplies the colors :var:`c1` and :var:`c2`.
	"""
	return Color(c1[0]*c2[0], c1[1]*c2[1], c1[2]*c2[2], 1.-(1.-c1[3])*(1.-c2[3]))


def screen(c1, c2):
	"""
	Does a negative multiplication of the colors :var:`c1` and :var:`c2`.
	"""
	return Color(*(1.-(1.-x)*(1.-y) for (x, y) in zip(c1, c2)))


def mix(*args):
	"""
	Calculates a weighted mix of the colors from :var:`args`. Items in
	:var:`args` are either colors or weights.
	"""
	channels = [0., 0., 0., 0.]
	weight = 1.
	sumweights = 0.
	for arg in args:
		if isinstance(arg, Color):
			sumweights += weight
			for i in xrange(3):
				channels[i] += weight*arg[i]
			channels[3] += weight*(255-arg[3])
		elif isinstance(arg, tuple):
			sumweights += arg[1]
			for i in xrange(3):
				channels[i] += arg[1]*arg[0][i]
			channels[3] += weight*(255-arg[0][3])
		else:
			weight = arg
	if not sumweights:
		raise ValueError("at least one of the weights must be >0")
	return Color(channels[0]/sumweights, channels[1]/sumweights, channels[2]/sumweights, 255-sumweights*channels[3])
