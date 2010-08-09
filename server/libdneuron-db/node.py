# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 nowrap:
# Our main node object
import re
import time
#import types
import engines.filestorage as engine

class node:
	def __init__(self, _id):
		""" Define our object instance variables. These are stored eventially
			within a serialised string.
		"""
		self._id								= _id
		self._mime								= 'text-plain'
		self._size								= 0
		self._created							= time.gmtime()
		self._modified							= time.gmtime()
		self._modified_hack						= False
		self._meta								= []
		self._links								= {}
		self._security							= {}

	def __cmp__(self, other):
		""" Check all our content to make sure we havnt modified anything. If we
			have, we return a zero (not quiet sure why, but this is pythons default.
		"""
		# FIXME: Need to Remove modified hack
		if self._modified_hack:
			return -1
		return int(time.mktime(self._modified) - time.mktime(other._modified))

	def get(self):
		""" Fetch all the node information (excluding the data) """
		return [self._id, self._size, self._created, self._modified, self._meta, self._links, self._mime]

	def getFull(self):
		pass

	def getMime(self):
		""" Fetch the mime type for this node and return it to the calling
			method. We could do away with this and just return the _mime value
			but I prefer a wrapper for if we get more technical with the mime
			data in the future.
		"""
		return self._mime

	def getSize(self):
		""" Fetch and return the size (in bytes) of the data segment of this
			node. As with the mime type, we could just fetch the _size variable
			but we like wrapping things.
		"""
		return self._size

	def getCreated(self):
		""" Get and return the date the node was created on the system.
		"""
		return self._created

	def getModified(self):
		"""Fetch and return the date the node or its data was last modified.
		"""
		return self._modified

	def addMeta(self, meta):
		""" Add metadata to this node. We first sanitise the metadata to ensure
			we dont have any unrecognised content within it. We then append the
			metadata to the end of the _meta list.
		"""
		try:
			safe_meta							= re.escape(meta)
			# Check if the metadata already exists
			if safe_meta in self._meta:
				return True
			self._meta.append(safe_meta)
			# Update the modified date
			self._modified						= time.gmtime()
			# FIXME: Need to remove modified hack
			self._modified_hack = True
			return True
		except:
			return False

	def remMeta(self, meta):
		""" Remove metadata from this node. We need to check the data to ensure
			we dont have strange content. Then remove the content from within
			the _meta list.
		"""
		try:
			safe_meta							= re.escape(meta)
			# Check if the metadata exists in the _meta list
			if safe_meta not in self._meta:
				return True
			self._meta.remove(safe_meta)
			self._modified						= time.gmtime()
			# FIXME: Need to remove modified hack
			self._modified_hack = True
			return True
		except:
			return False

	def getMeta(self):
		""" Return a list of all metadata for this node. We dont need to do any
			sanity checks because we have no user input. We still wrap it with
			a try/except block incase we are missing our _meta list.
		"""
		try:
			return self._meta
		except:
			return False

	def hasMeta(self, meta):
		""" Check if this node a metadata that we require. If the meta we are
			looking for exists, return true, else return false.
		"""
		try:
			safe_meta							= re.escape(meta)
			if safe_meta in self._meta:
				return True
			else:
				return False
		except:
				return False

	def setData(self, data):
		""" When we set data in the node, we pass the data into our content
			handler and then store the content reference within the node. This
			helps reduce the overhead of node scanning by keeping large content
			out of the node system. This will delete any content currently in
			the node data segment.
		"""
		try:
			self._size							= len(data)
			engine._set(self._id, data)
			self._modified						= time.gmtime()
			# FIXME: Need to remove modified hack
			self._modified_hack = True
			return True
		except:
			return False

	def addData(self, data):
		""" When we add data to the node, we pass the data into our content
			handler and then store the content reference within the node. This
			helps reduce the overhead of node scanning by keeping large content
			out of the node system.
		"""
		try:
			# Set the mode type, and update the modified time
			self._size							= len(data)
			engine._add(self._id, data)
			self._modified						= time.gmtime()
			# FIXME: Need to remove modified hack
			self._modified_hack = True
			return True
		except:
			return False

	def getData(self):
		""" Fetch the data from the data engine and return it to the calling
			method. We do not store the data internally as this would have an
			impact on the speed of the nodes.
		"""
		if self._size:
			try:
				return engine._get(self._id)
			except:
				return False
		else:
			return ''

	def remData(self):
		""" Remove data from the node. This will not delete the node itself, it
			only removes the data accociated with it.
		"""
		if self._size:
			try:
				if engine._remove(self._id):
					self._size					= 0
					self._modified				= time.gmtime()
					# FIXME: Need to remove modified hack
					self._modified_hack = True
					return True
				else:
					return False
			except:
				return False
		else:
			return True

	def addLink(self, link, name):
		""" Add a link to this node. We first sanitise the link, then we
			make sure the destination exists within the system.
		"""
		try:
			link								= int(link)
			if link in self._links:
				if name not in self._links[link]:
					# Add the link to this node
					self._links[link].append(name)
					# Add the link to the destination node
					self._modified				= time.gmtime()
					# FIXME: Need to remove modified hack
					self._modified_hack = True
			else:
				self._links[link]				= [name]
				self._modified					= time.gmtime()
				# FIXME: Need to remove modified hack
				self._modified_hack = True
			return True
		except:
			return False

	def remLink(self, link, name):
		""" Remove a link from this node. We check that the link is an integer,
			we ensure the link exists. If so, we remove the link from the node
			and from the link destination node.
		"""
		try:
			link								= int(link)
			if link in self._links:
				if name in self._links[link]:
					self._links[link].remove(name)
					# Remove the link from the destination node
					if self._links[link].__len__() == 0:
						del self._links[link]
					self._modified				= time.gmtime()
					# FIXME: Need to remove modified hack
					self._modified_hack = True
			return True
		except:
			return False

	def getLinks(self, *types):
		""" This method returns a list of links within this node. We dont do
			any sanity checks because we have no user input.
		"""
		try:
			if types:
				# Check if we have any types to look for
				_results						= {}
				# Loop through each node
				for _node in self._links.keys():
					if len(filter(lambda a: a in types,self._links[_node])) == len(types):
						_results[_node]			= list(types)
				return _results
			else:
				return self._links
		except:
			return False

	def hasLink(self, link=None, name=None):
		""" Check if this node has a parent that we require. If the parent we
			are looking for exists, return true, else return false.
		"""
		try:
			# No link and no name
			if not link and not name and self._links.__len__():
				return True
			# Link and no name
			elif not name and link in self._links:
				return True
			# Name and no link
			elif name and not link:
				for i in self._links:
					if name in self._links[i]:
						return True
				return False
			# Name and link
			elif name and link:
				if link in self._links:
					if name in self._links[link]:
						return True
				return False
			else:
				return False
		except:
			return False

	def addSecurity(self, link, name):
		""" Adds a security node to the data node. The link should contain
			a valid security node and the level should be one of the defined
			security levels.
		"""
		try:
			link								= int(link)
			if link in self._security:
				if name not in self._security[link]:
					# Add the link to this node
					self._security[link].append(name)
					self._modified				= time.gmtime()
					# FIXME: Need to remove modified hack
					self._modified_hack = True
			else:
				self._seciruty[link]			= [name]
				self._modified					= time.gmtime()
				# FIXME: Need to remove modified hack
				self._modified_hack = True
			return True
		except:
			return False

	def remSecurity(self, link, name):
		""" Remove a link from this node. We check that the link is an integer,
			we ensure the link exists. If so, we remove the link from the node
			and from the link destination node.
		"""
		try:
			link								= int(link)
			if link in self._security:
				if name in self._security[link]:
					self._security[link].remove(name)
					if self._security[link].__len__() == 0:
						del self._security[link]
					self._modified				= time.gmtime()
					# FIXME: Need to remove modified hack
					self._modified_hack = True
			return True
		except:
			return False

	def getSecurity(self, *types):
		""" This method returns a list of links within this node. We dont do
			any sanity checks because we have no user input.
		"""
		try:
			if types:
				# Check if we have any types to look for
				_results						= {}
				# Loop through each node
				for _node in self._security.keys():
					if len(filter(lambda a: a in types,self._security[_node])) == len(types):
						_results[_node]			= list(types)
				return _results
			else:
				return self._security
		except:
			return False

	def hasSecurity(self, link=None, name=None):
		""" Check if this node has a parent that we require. If the parent we
			are looking for exists, return true, else return false.
		"""
		try:
			# No link and no name
			if not link and not name and self._security.__len__():
				return True
			# Link and no name
			elif not name and link in self._security:
				return True
			# Name and no link
			elif name and not link:
				for i in self._security:
					if name in self._security[i]:
						return True
				return False
			# Name and link
			elif name and link:
				if link in self._security:
					if name in self._security[link]:
						return True
				return False
			else:
				return False
		except:
			return False

