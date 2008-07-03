:mod:`ll.ul4c` provides templating for XML/HTML as well as any other text-based
format. A template defines placeholders for data output and basic logic (like
loops and conditional blocks), that define how the final rendered output will
look.

:mod:`ll.ul4c` compiles a template to a bytecode format, which makes it possible
to implement renderers for these templates in multiple programming languages.


Embedding
=========

In the template source any text surrounded by ``<?`` and ``?>`` is a "template
tag". The first word inside the tag is the tag type. It defines what the tag
does. For example ``<?print foo?>`` is a print tag (it prints the value of the
variable ``foo``). A complete example template looks like this::

	<?if data?>
	<ul>
	<?for item in data?>
	<li><?print xmlescape(item)?></li>
	<?end for?>
	</ul>
	<?end if?>

(For text formats where the delimiters ``<?`` and ``?>`` collide with elements
that are used often or where using these delimiters is inconvenient it's
possible to specify a different delimiter pair when compiling the template.)

A complete Python program that compiles a template and renders it might look
like this::

	from ll import ul4c

	code = u'''<?if data?>
	<ul>
	<?for item in data?>
	<li><?print xmlescape(item)?></li>
	<?end for?>
	</ul>
	<?end if?>'''

	tmpl = ul4c.compile(code)

	print tmpl.renders([u"Python", u"Java", u"PHP"])

The method :meth:`Template.renders` gets passed the data object (which is
available in the template code under the name ``data``) and returns the rendered
string.


Data objects
============

The template requires a data object for rendering the final output.
What :mod:`ll.ul4c` supports in this data object is very similar to what JSON_
supports.

	.. _JSON: http://www.json.org/

Supported types are:

	*	strings
	*	integers
	*	floats
	*	date objects
	*	The "null" value (``None``)
	*	boolean values (``True`` and ``False``)
	*	lists
	*	dictionaries

Note that depending on the implementation language of the renderer additional
types might be supported, e.g. a Python renderer will probably support tuples
and lists and anything supporting :meth:`__getitem__` (or :meth:`__iter__` when
the list is used in a loop) for lists, Java might support anything implementing
the ``List`` interface (or the ``Collection`` interface if the list is used in a
loop).

The data object itself will be available inside the template code under the name
``data``.

Constants of these types can be created for all types except lists and
dictionaries. Most constants look similar to the related Python constant.


The "null" constant
-------------------

The "null" constant can be referred to via ``None``.


Boolean constants
-----------------

The boolean constants can be referred to via ``True`` and ``False``.


Integer constants
-----------------

Integer constants can be written in decimal, hexadecimal, octal and binary:
``42``, ``0x2a``, ``0o52`` and ``0b101010`` all refer to the integer value 42.


Float constants
---------------

Float constants must contain a decimal point or an exponential specifier,
e.g. ``42.``, ``4e23``.


String constants
----------------

Strings are delimited with single or double quotes and support all escape
sequences that Python supports (except ``\N{}``). Strings constants are always
unicode objects, so ``\uXXXX`` escaping is possible. Examples:

	* ``"abc"`` and ``'abc'``;

	*	``"'"`` and ``'\''`` are single quotes;

	*	``'"'`` and ``"\""`` are double quotes;

	*	``"\n"`` is a line feed and ``"\t"`` is a tab;

	*	``"\x61"`` and ``"\u0061"`` are lowercase "a"s;


Date constants
--------------

Creating date constants
 



Template code
=============

The template code tries to mimic Python syntax as far as possible, but is
limited to what is required for templates and does not allow executing arbitrary
Python statements.

:mod:`ll.ul4c` supports the following tag types:


``print``
---------

The ``print`` tag outputs the value of a variable or any other expression. If
the expression doesn't evaluate to a string it will be converted to a string
first. The format of the string depends on the renderer, but should follow
Python's ``unicode()`` output as much as possible (except that for ``None`` no
output may be produced)::

	<h1><?print person.lastname?>, <?print person.firstname?></h1>


``for``
-------

The ``for`` tag can be used to loop over the items in a list, the characters in
a string or the keys in a dictionary. The end of the loop body must be marked
with an ``<?end for?>`` tag::

	<ul>
	<?for person in data.persons?>
	<li><?print person.lastname?>, <?person.firstname?></li>
	<?end for?>
	</ul>

In ``for`` loops tuple unpacking is supported for tuples of length 1 and 2, so
you can do the following::

	<?for (key, value) in data.items?>

if ``items`` is an iterable containing lists with two elements.


``if``
------

The ``if`` tag can be used to output a part of the template only when a
condition is true. The end of the ``if`` block must be marked with an
``<?end if?>`` tag. The truth value of an object is the same as in Python:

	*	``None`` is false.
	*	The integer ``0`` and the float value ``0.0`` are false.
	*	Empty strings, lists and dictionaries are false.
	*	``False`` is false.
	*	Anything else is true.

For example we can output the person list only if there are any persons::

	<?if data.persons?>
	<ul>
	<?for person in data.persons?>
	<li><?print person.lastname?>, <?person.firstname?></li>
	<?end for?>
	</ul>
	<?end if?>

``elif`` and ``else`` are supported too::

	<?if data.persons?>
	<ul>
	<?for person in data.persons?>
	<li><?print person.lastname?>, <?person.firstname?></li>
	<?end for?>
	</ul>
	<?else?>
	<p>No persons found!</p>
	<?end if?>

or::

	<?if len(data.persons)==0?>
	No persons found!
	<?elif len(data.persons)==1?>
	One person found!
	<?else?>
	<?print len(data.persons)?> persons found!
	<?end if?>


``code``
--------

The ``code`` tag can be used to define or modify variables. Apart from the
assigment operator ``=``, the following augmented assignment operators are
supported:

	*	``+=`` (adds a value to the variable)
	*	``-=`` (subtracts a value from the variable)
	*	``*=`` (multiplies the variable by a value)
	*	``/=`` (divides the variable by a value)
	*	``//=`` (divides the variable by a value, rounding down to the next
		smallest integer)
	*	``&=`` (Does a modulo operation and replaces the variable value with the
		result)

For example the following template will output ``40``::

	<?code x = 17?>
	<?code x += 23?>
	<?print x?>


``render``
----------

The render tag allows one template to call other templates. The following Python
code demonstrates this::

	from ll import ul4c

	# Template 1
	source1 = u"""\
	<?if data?>\
	<ul>
	<?for item in data?><?render itemtmpl(item)?><?end for?>\
	</ul>
	<?end if?>\
	"""

	tmpl1 = ul4c.compile(source1)

	# Template 2
	source2 = u"<li><?print xmlescape(data)?></li>\n"

	tmpl2 = ul4c.compile(source2)

	# Data object for the outer template
	data = [u"Python", u"Java", u"PHP"]

	# Dictionary of subtemplates for the outer template
	templates = dict(itemtmpl=tmpl2)

	print tmpl1.renders(data, templates)

This will output::

	<ul>
	<li>Python</li>
	<li>Java</li>
	<li>PHP</li>
	</ul>

I.e. a dictionary of templates can be passed to the :meth:`renders` method as
a additional argument. The keys in this dictionary are the names of the
templates, which can be used in the ``<?render?>`` tag.
``<?render itemtmpl(item)?>`` renders the ``itemtmpl`` template and passed the
``item`` variable as the data object. All templates available in the outer
template will be available in the inner template too.


Expressions
-----------

:mod:`ll.ul4c` supports many of the operators supported by Python. Getitem style
element access is available, i.e. in the expression ``a[b]`` the following type
combinations are supported:

	*	string, integer: Returns the ``b``\th character from the string ``a``.
		Note that negative ``b`` values are supported and are relative to the end,
		so ``a[-1]`` is the last character.

	*	list, integer: Returns the ``b``\th list entry of the list ``a``. Negative
		``b`` values are supported too.

	*	dict, string: Return the value from the dictionary ``a`` corresponding to
		the key ``b``. (Note that some implementations might support keys other
		than strings too.)

Slices are also supported (for list and string objects). As in Python one or
both of the indexes may be missing to start at the first or end at the last
character/item. Negative indexes are relative to the end. Indexes that are out
of bounds are simply clipped:

	*	``<?print "Hello, World!"[7:-1]?>`` prints ``World``.

	*	``<?print "Hello, World!"[:-8]?>`` prints ``Hello``.

The following binary operators are supported: ``+``, ``-``, ``*``, ``/`` (floor
division), ``//`` (truncating division) and ``&`` (modulo).

The usual boolean operators ``not``, ``and`` and ``or`` are supported. However
``and`` and ``or`` don't short-circuit (but they always return one of the
operands). For example, the following code will output the ``data.title``
object if it's true, else ``data.id`` will be output::

	<?print xmlescape(data.title or data.id)?>

The two comparison operators ``==`` and ``!=`` are supported.

Containment test via the ``in`` operator can be done, in the expression
``a in b`` the following type combinations are supported:

	*	string, string: Checks whether ``a`` is a substring of ``b``.
	*	any object, list: Checks whether the object ``a`` is in the list ``b``
		(comparison is done by value not by identity)
	*	string, dict: Checks whether the key ``a`` is in the dictionary ``b``.
		(Note that some implementations might support keys other than strings too.)

The inverted containment test (via ``not in``) is available too.

Attribute access in the template code maps the dictionary style getitem access
in the data object::

	from ll import ul4c
	tmpl = ul4c.compile("<?print data.foo?>")
	print tmpl.renders(dict(foo="bar"))

However getitem style access in the template is still possible::

	from ll import ul4c
	tmpl = ul4c.compile("<?print data['foo']?>")
	print tmpl.renders(dict(foo="bar"))


Functions
---------

:mod:`ll.ul4c` supports a number of functions.


``now``
:::::::

``now()`` returns the current date and time as a data object.


``isnone``
::::::::::

``isnone(foo)`` returns ``True`` if ``foo`` is ``None``, else ``False`` is
returned::

	data is <?if isnone(data)?>None<?else?>something else<?end if?>!


``isbool``
::::::::::

``isbool(foo)`` returns ``True`` if ``foo`` is ``True`` or ``False``, else
``False`` is returned.


``isint``
:::::::::

``isint(foo)`` returns ``True`` if ``foo`` is an integer object, else ``False``
is returned.


``isfloat``
:::::::::::

``isfloat(foo)`` returns ``True`` if ``foo`` is a float object, else ``False``
is returned.


``isstr``
:::::::::

``isstr(foo)`` returns ``True`` if ``foo`` is a string object, else ``False``
is returned.


``isdate``
::::::::::

``isdate(foo)`` returns ``True`` if ``foo`` is a date object, else ``False``
is returned.


``islist``
::::::::::

``islist(foo)`` returns ``True`` if ``foo`` is a list object, else ``False``
is returned.


``isdict``
::::::::::::

``isdict(foo)`` returns ``True`` if ``foo`` is a dictionary object, else
``False`` is returned.


``bool``
::::::::

``bool(foo)`` converts ``foo`` to an boolean. I.e. ``True`` or ``False`` is
returned according to the truth value of ``foo``.


``int``
:::::::

``int(foo)`` converts ``foo`` to an integer. ``foo`` can be a string, a float,
a boolean or an integer.


``str``
:::::::

``str(foo)`` converts ``foo`` to a string. If ``foo`` is ``None`` the result
will be the empty string. For lists and dictionaries the exact format is
undefined, but should follow Python's repr format.


``repr``
::::::::

``repr(foo)`` converts ``foo`` to a string representation that is useful for
debugging proposes. The output is a constant expression that could be used to
recreate the object (except for list and dict, where ``repr`` follows the format
of Python's :func:`repr` function).


``len``
:::::::

``len(foo)`` returns the length of a string, or the number of items in a list
or dictionary.


``enumerate``
:::::::::::::

Enumerates the items of the argument (which must be iterable, i.e. a string,
a list or dictionary). For example the following code::

	<?for (i, c) in enumerate("foo")?><?print i?>=<?print c?>;<?end for?>

prints::

	0=f;1=o;2=o
	

``xmlescape``
:::::::::::::

``xmlescape`` takes a string as an argument. It returns a new string where the
characters ``&``, ``<``, ``>``, ``'`` and ``"`` are replaced with the
appropriate XML entity references. For example::

	<?print xmlescape("<'foo' & 'bar'>")?>

prints::

	``&lt;&#39;foo&#39; &amp; ;&#39;bar&#39&gt;``

If the argument is not a string, it will be converted to a string first.


``sorted``
::::::::::

``sorted`` returns a sorted list with the items from it's argument. For example::

	<?for c in sorted('bar')?><?print c?><?end for?>

prints::

	abr

Supported arguments are iterable objects, i.e. strings, lists and dictionaries.


``chr``
:::::::

``chr(x)`` returns a one-character string with a character with the codepoint
``x``. ``x`` must be an integer.


``ord``
:::::::

The argument for ``ord`` must be a one-character string. ``ord`` returns the
codepoint of that character as an integer.


``hex``
:::::::

Return the hexadecimal representation of the integer argument (with a leading
``0x``). For example ``<?print hex(42)?>`` outputs ``0x2a``.


``oct``
:::::::

Return the octal representation of the integer argument (with a leading ``0o``).
For example ``<?print oct(42)?>`` outputs ``0o52``.


``bin``
:::::::

Return the binary representation of the integer argument (with a leading ``0b``).
For example ``<?print bin(42)?>`` outputs ``0b101010``.


``range``
::::::::::

``range`` returns an object that can be iterated and will produce consecutive
integers up to the specified argument. With two arguments the first is the start
value and the second is the stop value. With three arguments the third one is
the step size (which can be negative).


Methods
-------

Objects in :mod:`ll.ul4c` support some methods too (depending on the type of the
object).


``upper``
:::::::::

The ``upper`` method of strings returns an uppercase version of the string for
which it's called::

	<?print 'foo'.upper()?>

prints::

	FOO


``lower``
:::::::::

The ``lower`` method of strings returns an lowercase version of the string for
which it's called.


``startswith``
::::::::::::::

``x.startswith(y)`` returns ``True`` if the string ``x`` starts with the string
``y`` and ``False`` otherwise.


``endswith``
::::::::::::::

``x.endswith(y)`` returns ``True`` if the string ``x`` ends with the string
``y`` and ``False`` otherwise.


``strip``
:::::::::

The string method ``strip`` returns a copy of the string with leading and
trailing whitespace removed. If an argument ``chars`` is given and not ``None``,
characters in ``chars`` will be removed instead.


``lstrip``
::::::::::

The string method ``lstrip`` returns a copy of the string with leading
whitespace removed. If an argument ``chars`` is given and not ``None``,
characters in ``chars`` will be removed instead.


``rstrip``
::::::::::

The string method ``rstrip`` returns a copy of the string with trailing
whitespace removed. If an argument ``chars`` is given and not ``None``,
characters in ``chars`` will be removed instead.


``split``
:::::::::
The string method ``split`` splits the string into separate "words" and returns
the resulting list. Without any arguments, the string is split on whitespace
characters. With one argument the argument specifies the soprator to use. The
second optional argument specifies the maximum number of splits to do.


``rsplit``
::::::::::
The string method ``rsplit`` works like ``split``, except that splitting start
from the end (which is only relevant when the maximum number of splits is
given).


``find``
::::::::

This string method search for a substring of the object for which it's called
and returns the position of the first appearance of the substring or -1 if
the string can't be found. For example ``"foobar".find("foo")`` returns 3.
The optional second and third argument specify the start and end position for
the search.