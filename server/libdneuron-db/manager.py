# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 nowrap:
# Our main node object
import os
import sys
import copy
import bsddb
import cPickle
import ConfigParser
import engines.filestorage as engine
from libneuron-db import loggers
from libneuron-db.node import node
from libneuron-db.security import security

class node_manager:
	def __init__(self):
		""" Make sure our node file exists and that we have our root node in it
			to remove index 0 from the list. We check the config file to do it.
		"""
		# Reset our claim list
		self._claimed							= []

		# Parse our configuration options
		config									= ConfigParser.ConfigParser()
		config.read(['neuron-db.conf', os.path.expanduser('~/.neuron-db.conf')])
		try:
			# Fetch the data directory to work on
			if config.has_option('global', 'data'):
				self._data						= config.get('global','data')
			else:
				self._data						= 'data'

			# Make the directory if needed
			if not os.path.exists(self._data):
				loggers.log_queue.put({'type':'notice','source':'node','message':'Creating %s' % self._data})
				os.mkdir(self._data)

			# Open the node database
			self._nodes							= bsddb.rnopen('%s/nodes.dat' % self._data, 'c')
			# Add the root security node if we are creating the database
			if self._nodes.__len__() == 0:
				self._nodes.db.append(cPickle.dumps(security(1)))
				self._nodes.sync()
		except:
			loggers.log_queue.put({'type':'error','source':'node','message':'Error initiating node system'})
			print 'Error initiating node system.', sys.exc_info()[1]
			sys.exit(1)

	def get(self, node_id):
		""" Return a reference the the node object we want to view/modify. We
			use a try/except to see if the node exists.
		"""
		try:
			return cPickle.loads(self._nodes[int(node_id)])
		except:
			return False

	def claim(self):
		""" Claim an id to use for storage. The reason we do this is to enable
			the system to write the data and blank the variable before we store
			the node information. When we claim an id, we set it to None, and
			store the value in a claimed list.
		"""
		try:
			self._nodes.db.append(None)
			node_id								= self._nodes.__len__()
			self._claimed.append(node_id)
			self._nodes.sync()
			return node_id
		except:
			return False

	def create(self):
		""" Create a new node for our grammer parser. This simply extracts the
			node information and creates a new instance of node() to be returned.
		"""
		_id										= self.claim()
		_node									= node(_id)
		self.add(_node, _id)
		return _id

	def add(self, node_obj, node_id=False):
		""" Add a node to the node list, then update the nodes file with the
			new node data. The file update if buffered, so it might not commit
			straight away. This increases the speed of node additions.
		"""
		# Check if we have a proper node object __class__
		# FIXME: Should not be using isinstance as it will break any variations of our node class (security)
		if not isinstance(node_obj,node):
			return False

		# FIXME: Need to check for None list entries and full them first
		if node_id:
			try:
				self._nodes[node_id]			= cPickle.dumps(node_obj)
				self._nodes.sync()
				self._claimed.remove(node_id)
				return node_id
			except:
				return False
		else:
			try:
				# FIXME: We need to find a more efficient way of adding the node id.
				self._nodes.db.append(cPickle.dumps(node_obj))
				node_id							= self._nodes.__len__()
				node_obj._id					= node_id
				self._nodes[node_id]			= cPickle.dumps(node_obj)
				self._nodes.sync()
				return node_id
			except:
				return False

	def call(self, node_id, method, *args, **kwargs):
		""" Call a method within a node. This is used for tasks like updating
			nodes links list.
		"""
		try:
			# Check if we have any methods that need to act on multiple nodes.
			# If they do, we need to call seperate methods to handle these.
			if method == 'addLink':
				node_id							= int(node_id)
				alt_node_id						= int(args[0])
				# Check both nodes exist
				if not self._nodes.has_key(node_id) or not self._nodes.has_key(alt_node_id):
					return False
				# Add the link to the main node
				_node							= cPickle.loads(self._nodes[node_id])
				if _node.addLink(*args):
					# FIXME: Need to remove modified hack
					_node._modified_hack		= False
					self.update(_node)

				# Add the link to the alternate node
				alt_node						= cPickle.loads(self._nodes[int(args[0])])
				alt_node.addLink(_node._id, args[1])

				# Commit our changes
				# FIXME: Need to remove modified hack
				alt_node._modified_hack			= False
				if self.update(alt_node):
					return True
				else:
					return False

			elif method == 'remLink':
				node_id							= int(node_id)
				alt_node_id						= int(args[0])
				# Check both nodes exist
				if not self._nodes.has_key(node_id) or not self._nodes.has_key(alt_node_id):
					return False
				# Remove the link to the main node
				_node							= cPickle.loads(self._nodes[node_id])
				if _node.remLink(*args):
					# FIXME: Need to remove modified hack
					_node._modified_hack		= False
					self.update(_node)

				# Remove the link to the alternate node
				alt_node						= cPickle.loads(self._nodes[int(args[0])])
				alt_node.remLink(_node._id, args[1])

				# Commit our changes
				# FIXME: Need to remove modified hack
				alt_node._modified_hack			= False
				if self.update(alt_node):
					return True
				else:
					return False
			elif method == 'addSecurity':
				node_id							= int(node_id)
				alt_node_id						= int(args[0])
				# Check both nodes exist
				if not self._nodes.has_key(node_id) or not self._nodes.has_key(alt_node_id):
					return False
				# Add the link to the main node
				_node							= cPickle.loads(self._nodes[node_id])
				if _node.addSecurity(*args):
					# FIXME: Need to remove modified hack
					_node._modified_hack		= False
					self.update(_node)

				# Add the link to the alternate node
				alt_node						= cPickle.loads(self._nodes[int(args[0])])
				alt_node.addSecurity(_node._id, args[1])

				# Commit our changes
				# FIXME: Need to remove modified hack
				alt_node._modified_hack			= False
				if self.update(alt_node):
					return True
				else:
					return False
			elif method == 'remSecurity':
				node_id							= int(node_id)
				alt_node_id						= int(args[0])
				# Check both nodes exist
				if not self._nodes.has_key(node_id) or not self._nodes.has_key(alt_node_id):
					return False
				# Remove the link to the main node
				_node							= cPickle.loads(self._nodes[node_id])
				if _node.remSecurity(*args):
					# FIXME: Need to remove modified hack
					_node._modified_hack		= False
					self.update(_node)

				# Remove the link to the alternate node
				alt_node						= cPickle.loads(self._nodes[int(args[0])])
				alt_node.remSecurity(_node._id, args[1])

				# Commit our changes
				# FIXME: Need to remove modified hack
				alt_node._modified_hack			= False
				if self.update(alt_node):
					return True
				else:
					return False
			else:
				node_id							= int(node_id)
				# Get the node object
				_node_orig						= cPickle.loads(self._nodes[node_id])
				_node							= copy.copy(_node_orig)
				if hasattr(_node, method) and callable(getattr(_node, method)):
					# If the method modifies the data, we need to return the result of the
					# update, else we return the result from the method itself.
					result						= getattr(_node, method)(*args, **kwargs)
					# FIXME: Need to remove modified hack
					if _node._modified_hack:
						_node._modified_hack	= False
						return self.update(_node)
					if _node_orig == _node:
						return result
					else:
						_node._modified_hack	= False
						return self.update(_node)
				elif hasattr(self._client, method):
					raise TypeError(method)
				else:
					raise AttributeError(method)
		except:
			return False

	def remove(self, node_id):
		""" Remove a node from our node list. To do this, we replace the node
			with None. This should then be picked up when we add a new node and
			replaced with the next node.
		"""
		# FIXME: Make sure the node exists before trying to access it
		# FIXME: Make some kind of undelete option
		# FIXME: Do we delete links, or report links (We currently delete them)
		# FIXME: Remove data file (Do we want to remove or backup?)
		try:
			# Remove all the links within the other nodes
			_links								= self.get(node_id).getLinks()
			n_obj								= self.get(int(node_id))
			# For each link id in our links list
			for _node in _links.keys():
				# For each link type in a link
				# FIXME: Need to reevaluate this. Its slow and sloppy
				for i in range(_links[_node].__len__()):
					try:
						n_obj.remLink(_node, _links[_node][0])
					except KeyError:
						break
			self._nodes[int(node_id)]			= None
			self._nodes.sync()
			return True
		except:
			return False

	def update(self, node_obj):
		""" Update the node object in our nodes.dat file. We use the node id in
			the object itself (_id) to set the list position.
		"""
		# FIXME: Make sure the node exists before committing updates
		try:
			self._nodes[node_obj._id]			= cPickle.dumps(node_obj)
			self._nodes.sync()
			return True
		except:
			return False

	def hasNode(self, node_id):
		""" Check if a node id exists within our node list. If exists and isnt
			None, we return true, else we return false.
		"""
		try:
			if self._nodes.has_key(node_id):
				return True
			else:
				return False
		except:
			return False

	def count(self):
		""" Return the total quantity of nodes within the system """
		try:
			return self._nodes.__len__()
		except:
			return False

manager = node_manager()

