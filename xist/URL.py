#! /usr/bin/env python

"""URL class.

This module contains only one useful variable: the URL class
"""

__version__ = "$Revision$"[11:-2]
# $Source$

import string
import types
import urlparse
import urllib

class URL:
	"""
	This class represents XSC URLs.
	Every instance has the following instance variables:
	scheme -- The scheme (e.g. "http" or "ftp"); there a two special schemes: "server" for server relative URLs and "project" for project relative URLs
	server -- The server name
	port -- The port number
	path -- The path to the file as a list of strings
	file -- The filename without extension
	ext -- The file extension
	parameters -- The parametes
	query -- The query
	fragment -- The fragment
	These variables form a URL in the following way
	<scheme>://<server>:<port>/<path>/<file>.<ext>;<params>?<query>#<fragment>
	"""
	def __init__(self,url = None,scheme = None,server = None,port = None,path = None,file = None,ext = None,parameters = None,query = None,fragment = None):
		# initialize the defaults
		self.scheme = None
		self.server = None
		self.port = None
		self.path = []
		self.file = None
		self.ext = None
		self.parameters = None
		self.query = None
		self.fragment = None
		if url is None:
			pass
		elif type(url) == types.StringType:
			self.__fromString(url)
		elif type(url) == types.InstanceType and isinstance(url,URL):
			self.scheme     = url.scheme
			self.server     = url.server
			self.port       = url.port
			self.path       = url.path[:]
			self.file       = url.file
			self.ext        = url.ext
			self.parameters = url.parameters
			self.query      = url.query
			self.fragment   = url.fragment
		else:
			raise ValueError("URL argument must be either a string or an URL")

		if scheme is not None:
			self.scheme = scheme
		if server is not None:
			self.server = server
		if port is not None:
			self.port = port
		if path is not None:
			self.path = path[:]
		if ext is not None:
			self.ext = ext
		if file is not None:
			self.file = file
		if parameters is not None:
			self.parameters = parameters
		if query is not None:
			self.query = query
		if fragment is not None:
			self.fragment = fragment

		self.__optimize()

	def __fromString(self,url):
		if url == ":":
			self.scheme = "project"
		else:
			(self.scheme,self.server,self.path,self.parameters,self.query,self.fragment) = urlparse.urlparse(url)
			if self.scheme == "": # do we have a local file?
				if len(self.path):
					if self.path[0] == "/": # this is a server relative URL
						self.path = self.path[1:] # drop the empty string in front of the first "/" ...
						self.scheme = "server" # ... and use a special scheme for that
					elif self.path[0] == ":": # project relative, i.e. relative to the current directory
						self.path = self.path[1:] # drop of the ":" ...
						self.scheme = "project" # special scheme name
			elif self.scheme == "http":
				if len(self.path):
					self.path = self.path[1:] # if we had a http, the path from urlparse started with "/" too
			pos = string.rfind(self.server,":")
			if pos != -1:
				self.port = string.atoi(self.server[pos+1:])
				self.server = self.server[:pos]
			self.path = string.split(self.path,"/")
			self.file = self.path[-1]
			self.path = self.path[:-1]

			if self.scheme in [ "ftp" , "http" , "https" , "server", "project" , "" ]:
				pos = string.rfind(self.file,".")
				if pos != -1:
					self.ext = self.file[pos+1:]
					self.file = self.file[:pos]

			self.scheme = self.scheme or None
			self.server = self.server or None
			self.file = self.file or None
			self.parameters = self.parameters or None
			self.query = self.query or None
			self.fragment = self.fragment or None

	def __repr__(self):
		v = []
		if self.scheme:
			v.append("scheme=" + repr(self.scheme))
		if self.server:
			v.append("server=" + repr(self.server))
		if self.port:
			v.append("port=" + repr(self.port))
		if self.path:
			v.append("path=" + repr(self.path))
		if self.file:
			v.append("file=" + repr(self.file))
		if self.ext:
			v.append("ext=" + repr(self.ext))
		if self.parameters:
			v.append("parameters=" + repr(self.parameters))
		if self.query:
			v.append("query=" + repr(self.query))
		if self.fragment:
			v.append("fragment=" + repr(self.fragment))
		return "URL(" + string.join(v,", ") + ")"

	def __str__(self):
		scheme = self.scheme or ""

		server = self.server or ""
		if self.port:
			server = server + ":" + str(self.port)

		path = self.path[:]

		file = self.file or ""
		if self.ext:
			file = file + "." + self.ext
		path.append(file)

		if scheme == "project":
			scheme = "" # remove our own private scheme name
		elif scheme == "server":
			scheme = "" # remove our own private scheme name
			path[:0] = [ "" ] # make sure that there's a "/" at the start

		return urlparse.urlunparse((scheme,server,string.join(path,"/"),self.parameters or "",self.query or "",self.fragment or ""))

	def __join(self,other):
		if not other.scheme:
			self.path.extend(other.path)
			self.file       = other.file
			self.ext        = other.ext
			self.parameters = other.parameters
			self.query      = other.query
			self.fragment   = other.fragment
		elif other.scheme == "project" or other.scheme == "server":
			if self.scheme == "project": # if we were project relative, and the other one was server relative ...
				self.scheme = other.scheme # ... then now we're server relative too
			self.path       = other.path[:]
			self.file       = other.file
			self.ext        = other.ext
			self.parameters = other.parameters
			self.query      = other.query
			self.fragment   = other.fragment
		else: # URL to be joined is absolute, so we return the second URL
			return other
		self.__optimize()
		return self

	def __add__(self,other):
		"""
		joins two URLs together. When the second URL is
		absolute (i.e. contains a scheme other that "server",
		"project" or "", you'll get a copy of the second URL.
		"""
		return self.clone().__join(URL(other))

	def __radd__(self,other):
		return URL(other).__join(self.clone())

	__radd__.__doc__ = __add__.__doc__

	def clone(self):
		"""
		returns an identical clone of this URL.
		"""
		return URL(scheme = self.scheme,server = self.server,port = self.port,path = self.path,file = self.file,ext = self.ext,parameters = self.parameters,query = self.query,fragment = self.fragment)

	def isRemote(self):
		if self.scheme == "project":
			return 0
		elif self.scheme == "":
			return 0
		elif self.scheme == "server" and self.server == "localhost":
			return 0
		else:
			return 1

	def relativeTo(self,other):
		"""
		returns this URL relative to another.

		note that remote URLs won't be modified in any way,
		because although the file you've read might have been
		remote, the parsed XSC file that you output, probably
		isn't.
		"""
		new = other + self
		if (not new.scheme) or new.scheme == "project":
			otherpath = other.path[:]
			while len(otherpath) and len(new.path) and otherpath[0]==new.path[0]: # throw away identical directories in both paths (we don't have to go up from file and down to path for these identical directories)
				del otherpath[0]
				del new.path[0]
			new.path[:0] = [".."]*len(otherpath) # now for the rest of the path we have to go up from file and down to path (the directories for this are still in path)
			new.scheme = None
		return new

	def __cmp__(self,other):
		return cmp(self.scheme,other.scheme) or cmp(self.server,other.server) or cmp(self.port,other.port) or cmp(self.path,other.path) or cmp(self.file,other.file) or cmp(self.ext,other.ext) or cmp(self.parameters,other.parameters) or cmp(self.query,other.query) or cmp(self.fragment,other.fragment)

	def __optimize(self):
		"""
		optimize the path by removing combinations of down/up
		"""
		while 1:
			for i in xrange(len(self.path)):
				if self.path[i]==".." and i>0 and self.path[i-1]!="..": # found a down/up
					del self.path[i-1:i+1] # remove it
					break # restart the search
			else: # no down/up found
				break

	def read(self):
		return urllib.urlopen(str(self)).read()
