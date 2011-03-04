#!/usr/local/bin/python
# -*- coding: utf-8 -*-


## Copyright 2009-2010 by LivingLogic AG, Bayreuth/Germany.
## Copyright 2009-2010 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/__init__.py for the license


"""
``uls`` is a script that lists directory contents. It is an URL-enabled version
of the ``ls`` system command. Via :mod:`ll.url` and :mod:`ll.orasql` ``uls``
supports ``ssh`` and ``oracle`` URLs too.


Options
-------

``uls`` supports the following options:

	``urls``
		Zero or more URLs. If no URL is given the current directory is listed.

	``-c``, ``--color`` : ``yes``, ``no`` or ``auto``
		Should the ouput be colored. If ``auto`` is specified (the default) then
		the output is colored if stdout is a terminal.

	``-1``, ``--one`` : ``false``, ``no``, ``0``, ``true``, ``yes`` or ``1``
		Force output to be one URL per line. The default is to output URLs in
		multiple columns (as many as fit on the screen)

	``-l``, ``--long`` : ``false``, ``no``, ``0``, ``true``, ``yes`` or ``1``
		Ouput in long format: One URL per line containing the following information:
		file mode, owner name, group name, number of bytes in the file,
		number of links, URL

	``-s``, ``--human-readable-sizes`` : ``false``, ``no``, ``0``, ``true``, ``yes`` or ``1``
		Output the file size in human readable form (e.g. ``42M`` for 42 megabytes)

	``-r``, ``--recursive`` : ``false``, ``no``, ``0``, ``true``, ``yes`` or ``1``
		List directory recursively

	``-w``, ``--spacing`` : integer
		The number of spaces between columns (only relevant when neither ``--long``
		nor ``--one`` is specified)

	``-P``, ``--padchar`` : character
		The character using for padding output in multicolumn or long format.

	``-S``, ``--sepchar`` : character
		The characters used for separating columns in long format

	``-i``, ``--include`` : regular expression
		Only URLs matching the regular expression will be output.

	``-e``, ``--expression`` : regular expression
		URLs matching the regular expression will be not be output.

	``-a``, ``--all`` :  ``false``, ``no``, ``0``, ``true``, ``yes`` or ``1``
		Output files whose name starts with a dot?
"""


import sys, re, argparse, contextlib, datetime, pwd, grp, stat, curses

from ll import misc, url

try:
	import astyle
except ImportError:
	from ll import astyle

try:
	from ll import orasql # Activate oracle URLs
except ImportError:
	pass


__docformat__ = "reStructuredText"


style_file = astyle.Style.fromstr("white:black")
style_dir = astyle.Style.fromstr("yellow:black")
style_pad = astyle.Style.fromstr("black:black:bold")
style_sizeunit = astyle.Style.fromstr("cyan:black")


def main(args=None):
	uids = {}
	gids = {}
	modedata = (
		(stat.S_IRUSR, "-r"),
		(stat.S_IWUSR, "-w"),
		(stat.S_IXUSR, "-x"),
		(stat.S_IRGRP, "-r"),
		(stat.S_IWGRP, "-w"),
		(stat.S_IXGRP, "-x"),
		(stat.S_IROTH, "-r"),
		(stat.S_IWOTH, "-w"),
		(stat.S_IXOTH, "-x"),
	)
	curses.setupterm()
	width = curses.tigetnum('cols')

	def rpad(s, l):
		meas = str(s)
		if not isinstance(s, (basestring, astyle.Text)):
			s = str(s)
		if len(meas) < l:
			return astyle.style_default(s, style_pad(args.padchar*(l-len(meas))))
		return s

	def lpad(s, l):
		meas = str(s)
		if not isinstance(s, (basestring, astyle.Text)):
			s = str(s)
		if len(meas) < l:
			return astyle.style_default(style_pad(args.padchar*(l-len(meas))), s)
		return s

	def match(url):
		strurl = str(url)
		if args.include is not None and args.include.search(strurl) is None:
			return False
		if args.exclude is not None and args.exclude.search(strurl) is not None:
			return False
		if not args.all and url.file.startswith("."):
			return False
		return True

	def findcolcount(urls):
		def width4cols(numcols):
			cols = [0]*numcols
			rows = (len(urls)+numcols-1)//numcols
			for (i, (u, su)) in enumerate(urls):
				cols[i//rows] = max(cols[i//rows], len(su))
			return (sum(cols) + (numcols-1)*args.spacing, rows, cols)

		numcols = len(urls)
		if numcols:
			while True:
				(s, rows, cols) = width4cols(numcols)
				if s <= width or numcols == 1:
					return (rows, cols)
				numcols -= 1
		else:
			return (0, 0)

	def printone(url):
		if args.long:
			sep = style_pad(args.sepchar)
			stat = url.stat()
			owner = url.owner()
			group = url.group()
			mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
			mode = "".join([text[bool(stat.st_mode&bit)] for (bit, text) in modedata])
			size = stat.st_size
			if args.human:
				s = "BKMGTP"
				for c in s:
					if size < 2048:
						if c == "B":
							size = str(int(size))
						else:
							size = astyle.style_default(str(int(size)), style_sizeunit(c))
						break
					size /= 1024.
			stdout.write(mode, sep, rpad(owner, 8), sep, rpad(group, 8), sep, lpad(size, 5 if args.human else 12), sep, lpad(stat.st_nlink, 3), sep, mtime, sep)
		if url.isdir():
			stdout.writeln(style_dir(str(url)))
		else:
			stdout.writeln(style_file(str(url)))

	def printblock(url, urls):
		if url is not None:
			stdout.writeln(style_dir(str(url)), ":")
		(rows, cols) = findcolcount(urls)
		for i in xrange(rows):
			for (j, w) in enumerate(cols):
				index = i+j*rows
				try:
					(u, su) = urls[index]
				except IndexError:
					pass
				else:
					if u.isdir():
						su = style_dir(su)
					else:
						su = style_file(su)
					if index + rows < len(urls):
						su = rpad(su, w+args.spacing)
					stdout.write(su)
			stdout.writeln()

	def printall(base, url):
		if url.isdir():
			if url.path.segments[-1]:
				url.path.segments.append("")
			if not args.long and not args.one:
				if args.recursive:
					urls = [(url/child, str(child)) for child in url.files() if match(url/child)]
					if urls:
						printblock(url, urls)
					for child in url.dirs():
						printall(base, url/child)
				else:
					urls = [(url/child, str(child)) for child in url.listdir() if match(url/child)]
					printblock(None, urls)
			else:
				for child in url.listdir():
					child = url/child
					if match(child):
						if not args.recursive or child.isdir(): # For files the print call is done by the recursive call to ``printall``
							printone(child)
					if args.recursive:
						printall(base, child)
		else:
			if match(url):
				printone(url)

	p = argparse.ArgumentParser(description="List the content of one or more URLs")
	p.add_argument("urls", metavar="url", help="URLs to be listed (default: current dir)", nargs="*", default=[url.Dir("./", scheme=None)], type=url.URL)
	p.add_argument("-c", "--color", dest="color", help="Color output (default: %(default)s)", default="auto", choices=("yes", "no", "auto"))
	p.add_argument("-1", "--one", dest="one", help="One entry per line? (default: %(default)s)", action=misc.FlagAction, default=False)
	p.add_argument("-l", "--long", dest="long", help="Long format? (default: %(default)s)", action=misc.FlagAction, default=False)
	p.add_argument("-s", "--human-readable-sizes", dest="human", help="Human readable file sizes? (default: %(default)s)", action=misc.FlagAction, default=False)
	p.add_argument("-r", "--recursive", dest="recursive", help="Recursive listing? (default: %(default)s)", action=misc.FlagAction, default=False)
	p.add_argument("-w", "--spacing", dest="spacing", metavar="N", help="Number of spaces between columns (default: %(default)s)", type=int, default=3)
	p.add_argument("-P", "--padchar", dest="padchar", metavar="CHAR", help="Character used for padding columns (default: %(default)s)", default=" ")
	p.add_argument("-S", "--sepchar", dest="sepchar", metavar="CHARS", help="Characters used for separating columns in long format (default: %(default)s)", default="  ")
	p.add_argument("-i", "--include", dest="include", metavar="PATTERN", help="Include only URLs matching PATTERN (default: %(default)s)", type=re.compile)
	p.add_argument("-e", "--exclude", dest="exclude", metavar="PATTERN", help="Exclude URLs matching PATTERN (default: %(default)s)", type=re.compile)
	p.add_argument("-a", "--all", dest="all", help="Include dot files? (default: %(default)s)", action=misc.FlagAction, default=False)

	args = p.parse_args(args)

	if args.color == "yes":
		color = True
	elif args.color == "no":
		color = False
	else:
		color = None
	stdout = astyle.Stream(sys.stdout, color)
	stderr = astyle.Stream(sys.stderr, color)

	with url.Context():
		for u in args.urls:
			printall(u, u)


if __name__ == "__main__":
	sys.exit(main())
