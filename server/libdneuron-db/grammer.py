# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 nowrap:
import string
from libneuron-db.manager import manager
from libneuron-db import loggers
from libneuron-db import errors

class grammer_controller:
	def __init__(self, _definitions=False):
		self._transactions									= {}
		self._actions										= ['get', 'add', 'remove', 'set', 'define']
		self._types											= ['meta','mime','data','size', 'created', 'modified']
		self._definitions									= _definitions
		self._as											= False

	def run(self, string):
		""" Process a string and execute the resultant commands within the
			system. Then return the results to the calling method.
		"""
		self._values										= []
		self._as											= False

		# Sanitise the string we recieve to ensure we are safe from malisc
		string												= self.__sanitise(string)
		subqueries											= self.__denest(string)
		self._values										= self.__split(string)

		# Make sure our first value is a command
		if not self._values[0].strip() in self._actions:
			raise errors.ParseError(0x10)
		else:
			self._action									= self._values[0].strip()

		try:
			# Check if we have an 'as' command at the end. If so, add the value.
			if self._values[-2] == 'as':
				# Check if the last value is surounded by single quotes
				if self._values[-1][0] != '\'' and self._values[-1][-1] != '\'':
					raise errors.ParseError(0x52)
				# Set our 'as' variable.
				self._as									= self._values[-1][1:-1]
		except:
			raise errors.ParseError(0x50)

		# Check if we have a type, if not, just get the data
		self._type											= self._values[1].strip()

		# Check if we are trying to get the list of defined values
		if self._action == 'get' and self._type == 'defined':
			return self._definitions

		# Parse simple action with no type
		if self._type[0] == '[':
			parser											= parse_grammer(self._definitions)
			self._data										= parser.parse(self._type)

			# Check if we need to return a list of definitions
			try:
				def_list									= []
				for i in self._data[0]:
					def_list.append(self._definitions[i])
				return def_list
			except:
				pass

			results											= fetch_results([self._action], self._data)
			if self._as:
				self._definitions[self._as]					= results.get_results()
				return self._definitions[self._as]
			else:
				return results.get_results()
		# Parse normal action (The next value must be [])
		elif self._type in self._types:
			self._data										= self._values[2].strip()
			if self._data[0] != '[':
				raise errors.ParseError(0x12)
			else:
				parser										= parse_grammer(self._definitions)
				self._data									= parser.parse(self._data)
				results										= fetch_results([self._action,self._type], self._data)
				if self._as:
					self._definitions[self._as]				= results.get_results()
					return self._definitions[self._as]
				else:
					return results.get_results()
		# Last test, if _type isnt links, we have an error
		elif self._type == 'links':
			# Simply get the nodes links
			self._data										= self._values[2].strip()
			if self._data[0] == '[':
				parser										= parse_grammer(self._definitions)
				self._data									= parser.parse(self._data)
				results										= fetch_results([self._action,self._type], self._data)
				if self._as:
					self._definitions[self._as]				= results.get_results()
					return self._definitions[self._as]
				else:
					return results.get_results()
			else:
				# Get the data values index (values start with square brackets)
				parser										= parse_grammer(self._definitions)
				data_map									= map(lambda x: x[0]=='[', self._values)
				data_index									= data_map.index(True,1)
				action_index								= 1
				results										= False
				while self._type == 'links':
					# Control the action counter and value
					action_index							+= 1
					self._type								= self._values[action_index]
					# Control the data loop counter and data values
					try:
						if self._values[data_index][0] == '[':
							data							= self._values[data_index]
							data_index						+= 1
						else:
							data							= False
					except:
						data								= False

					# Sanatise the data to use for the query
					self._data								= parser.parse(self.__mergedata(data, results))
					results									= fetch_results(['get','links'], self._data)
					results									= results.get_results()

				# If the final result was links, return them
				if self._type[0] == '[': return self._data

				# At this point, we should have all the ids we need to act on
				try:
					data									= self._values[data_index]
				except:
					data									= False

				self._data									= parser.parse(self.__mergedata(data, results))
				results										= fetch_results([self._action,self._type], self._data)
				if self._as:
					self._definitions[self._as]				= results.get_results()
					return self._definitions[self._as]
				else:
					return results.get_results()
		else:
			raise errors.ParseError(0x11)

	def __sanitise(self, command):
		""" Sanitise the string from any wrong doing. """
		return string.strip(command)

	def __denest(self, expr):
		""" Run through the data string and find any nested queries. If we find
			some, we execute them and replace the queries with the results.
		"""
		n													= len(expr)
		components											= []
		nested												= 0
		bopen												= '('
		bclose												= ')'

		# While we still have characters to parse
		while len(expr) > 0:
			# Setup our loop variables
			n												= len(expr)
			# Start looking for an opening bracket
			target											= bopen
			if expr[0] == target: target					= bclose
			i												= self.__find(expr, target, bopen, bclose)
			if target == bclose:i							+= 1
			if expr[0] == bopen:components.append(expr[:i])
			else:components.extend(expr[:i].split())
			expr											= expr[i:]
		return components

	def __split(self, expr):
		""" Splits expr in a sequence of alternating non-bracketed and bracketed expressions """
		n													= len(expr)
		components											= []
		nested												= 0
		bopen												= '['
		bclose												= ']'

		# While we still have characters to parse
		while len(expr) > 0:
			# Setup our loop variables
			n												= len(expr)
			# Start looking for an opening bracket
			target											= bopen
			if expr[0] == target: target					= bclose
			i												= self.__find(expr, target, bopen, bclose)
			if target == bclose: i							+= 1
			if expr[0] == bopen:components.append(expr[:i])
			else:components.extend(expr[:i].split())
			expr											= expr[i:]
		return components

	def __find(self, s, target, bopen='[', bclose=']'):
		""" Version to find which returns len( s ) if target is not found"""
		nest												= 0
		index												= 0
		if target == bopen:
			result											= s.find(target)
			if result == -1:result							= len(s)
			return result
		while True:
			if s[index] == bopen:
				nest										+= 1
			elif s[index] == bclose:
				nest										-= 1
				if nest == 0: return index
			index											+= 1

	def __mergedata(self,data,results):
		if not results:
			return data
		else:
			if not data:
				return `results[0].keys()`
			else:
				# Merge the result ids with the next datas query
				_data										= '['
				for i in results[0].keys():
					_data									+= '%s:%s,' % (i, data)
				# Replace last comma with closing bracket
				_data										= _data[0:-1]+']'
				return _data

class parse_grammer:
	""" The grammer parser parses any information we recieved from a client
		that isnt in our list of commands. This may be called multiple times
		for each query if the grammer controller finds nested queries within
		the clients query. We always return a list as our results of the query.
	"""
	def __init__(self, _definitions):
		self._string										= ''
		self._index											= -1
		self._values										= []
		self._definitions									= _definitions

	def parse(self,_string):
		""" The main parsing method. This controls parsing the string given to
			it by the calling method. Once the end of the string is found, we
			return the results to the method as a list.
		"""
		# Force our variables to be reset
		self._string										= _string
		self._values										= []
		self._index											= -1

		# Process string until StopIteration exception is raised
		try:
			while True:
				# Remove unwanted whitespace
				self._strip()
				# Fetch the next char and decide what to do
				peek										= self._peek()
				if not peek:
					raise StopIteration
				elif peek == '[':
					# We have started a new list, parse it
					self._values.append(self._readList())
				elif peek.isalpha():
					# FIXME: The action and values for it should be stored as string
					self._readAction()
				elif peek.isdigit():
					pass
				elif peek == ',':
					# Next value
					self._next()
					pass
				else:
					raise errors.ParseError(0x00)
		except StopIteration:
			return self._values

	def _peek(self):
		""" Check the next character in the string without modifying the index.
		"""
		i													= self._index + 1
		if i < len(self._string):
			return self._string[i]
		else:
			return None

	def _next(self):
		""" Get the next character in the string and increase the index to the
			new character in the string.
		"""
		self._index											+= 1
		if self._index < len(self._string):
			return self._string[self._index]
		else:
			raise StopIteration

	def _all(self):
		""" Resturn the entire string to the calling method. """
		return self._string

	def _strip(self):
		""" Recursivly remove any white space characters in the front of our
			string and increase the index.
		"""
		p													= self._peek()
		while p is not None and p in string.whitespace:
			self._next()
			p												= self._peek()

	def _readAction(self):
		""" alpha """
		_action												= ''
		c													= self._peek()

		while c.isalpha():
			_action											+= self._next()
			c												= self._peek()

		if _action in self._commands:
			self._actions.append(_action)
		elif _action in self._references:
			self._actions.append(_action)
		else:
			raise errors.ParseError(0x00)

	def _readList(self):
		""" [] """
		_buffer												= []
		self._next()

		while True:
			self._strip()
			try:
				p											= self._peek()
				if not p:
					raise StopIteration
				elif p == ',':
					# Start next value
					self._next()
					continue
				elif p == '\'':
					# Start reading a string
					_buffer.append(self._readString())
				elif p == '[':
					# Start reading a nested list
					_buffer.append(self._readList())
				elif p == ']':
					# Close this list and return it
					self._next()
					return _buffer
				elif p.isdigit():
					# Could be a link or a node. If the number ends with a :,
					# we are looking at a link, so send it to the link parser
					if self._isLink():
						_buffer								= self._readLink()
					else:
						_node_id							= ''
						while p.isdigit():
							_node_id						+= self._next()
							p								= self._peek()
						_buffer.append(_node_id)
				else:
					# Unrecognised value, raise parse error
					raise errors.ParseError(0x00)
			except StopIteration:
				return _buffer
		return _buffer

	def _readString(self, _comma='\''):
		""" ['"]string['"] """
		_buffer												= ''
		self._next()

		while True:
			try:
				p											= self._peek()
				if not p == _comma:
					_buffer									+= self._next()
					p										= self._peek()
				else:
					self._next()
					break
			except StopIteration:
				return _buffer
		return _buffer

	def _isLink(self):
		p													= self._index+1
		c													= self._string[p]

		while c.isdigit():
			p												+= 1
			c												= self._string[p]

		if c == ':':
			return True
		else:
			return False

	def _readLink(self):
		""" 0000:['string','string','string'],1111:['string','string','string']
			return {0000: ['string','string','string']}
		"""
		_values												= {}
		_node_id											= ''
		# Loop through the data always starting with numbers
		while True:
			# Get the node id
			p												= self._peek()
			while p.isdigit():
				_node_id									+= self._next()
				p											= self._peek()
			# Make sure we have a : after the node id
			if p == ':':
				self._next()
			else:
				# FIXME: Raise invalid link
				raise errors.ParseError(0x00)
			# Parse the list of link types
			_link_values									= self._readList()
			# Add the dictionary entry
			_values[_node_id]								= _link_values

			# Decide if we have another link, or the end
			p												= self._peek()
			if p == ',':
				_node_id									= ''
				self._next()
				continue
			elif p == ']':
				return _values

# FIXME: The fetch_results should extend threading to allow us to run parallel queries
class fetch_results:
	""" The fetch_results class queries the actual node system for data. We
		give it a query type as a list and a list of options to parse. When
		it gets a result from the node system, it returns it to the calling
		object. (Normall the grammer_controller).
	"""
	def __init__(self,_actions, _values):
		# Define our actions to commit and our variables to use for actions
		self._actions										= _actions
		self._values										= _values

	def get_results(self):
		# Call the relivant method, and return the result
		try:
			return getattr(self,'_%s'%self._actions[0])()
		except:
			return False

	def _get(self):
		""" Get information from nodes """
		# Check what we are supposed to be getting
		try:
			if self._actions[1] == 'meta':
				_meta										= []
				try:
					for i in self._values[0]:
						try:
							_meta.append(manager.call(i,'getMeta'))
						except IndexError:
							_meta.append(False)
					return _meta
				except:
					return False
			elif self._actions[1] == 'links':
				# Check if we have a dictionary or a list
				if isinstance(self._values[0],list):
					_links									= []
					try:
						for i in self._values[0]:
							try:
								_links.append(manager.call(i,'getLinks'))
							except IndexError:
								_links.append(False)
						return _links
					except:
						return False
				elif isinstance(self._values[0],dict):
					_links									= []
					try:
						for i in self._values[0].keys():
							try:
								_links.append(manager.call(i,'getLinks',*tuple(self._values[0][i])))
							except IndexError:
								_links.append(False)
						return _links
					except:
						return False
				else:
					return False
			elif self._actions[1] == 'data':
				_data										= []
				try:
					for i in self._values[0]:
						try:
							_data.append(manager.call(i,'getData'))
						except IndexError:
							_data.append(False)
					return _data
				except:
					return False
			elif self._actions[1] == 'mime':
				_mimes										= []
				try:
					for i in self._values[0]:
						try:
							_mimes.append(manager.call(i,'getMime'))
						except IndexError:
							_mimes.append(False)
					return _mimes
				except:
					return False
			elif self._actions[1] == 'size':
				_sizes										= []
				try:
					for i in self._values[0]:
						try:
							_sizes.append(manager.call(i,'getSize'))
						except IndexError:
							_sizes.append(False)
					return _sizes
				except:
					return False
			elif self._actions[1] == 'created':
				_creations									= []
				try:
					for i in self._values[0]:
						try:
							_creations.append(manager.call(i,'getCreated'))
						except IndexError:
							_creations.append(False)
					return _creations
				except:
					return False
			elif self._actions[1] == 'modified':
				_modifies									= []
				try:
					for i in self._values[0]:
						try:
							_modifies.append(manager.call(i,'getModified'))
						except IndexError:
							_modifies.append(False)
					return _modifies
				except:
					return False
		except:
			# Fetch node information from the node list
			_ids											= []
			for i in self._values[0]:
				try:
					_ids.append(manager.call(i,'get'))
				except:
					_ids.append(None)
			return _ids

	def _add(self):
		""" Add a node or information to a node """
		try:
			if self._actions[1] == 'meta':
				_results									= []
				try:
					for _node in self._values[0]:
						try:
							_subresults						= []
							for _meta in self._values[0][_node]:
								_subresults.append(manager.call(_node,'addMeta',_meta))
							_results.append(_subresults)
						except IndexError:
							_results.append(False)
					return _results
				except:
					return False
			elif self._actions[1] == 'links':
				_results									= []
				try:
					# For each node we want to add new links to
					for _node in self._values[0]:
						try:
							_subresults						= []
							# For each destination node
							for _dest in self._values[0][_node].keys():
								_ssubresults				= []
								# For each link type
								for _type in self._values[0][_node][_dest]:
									_ssubresults.append(manager.call(_node,'addLink',_dest,_type))
								_subresults.append(_ssubresults)
							_results.append(_subresults)
						except IndexError:
							_results.append(False)
					return _results
				except:
					return False
			elif self._actions[1] == 'data':
				_results									= []
				try:
					for _node in self._values[0].keys():
						try:
							_subresults						= []
							for _data in self._values[0][_node]:
								_subresults.append(manager.call(_node,'addData',_data))
							_results.append(_subresults)
						except IndexError:
							_results.append(False)
					return _results
				except:
					return False
			else:
				return False
		except:
			# We are adding nodes to the system, loop through the list
			_ids											= []
			for i in self._values[0]:
				_id											= manager.create()
				# Add the meta data
				try:
					for meta in i[0]:
						manager.call(_id, 'addMeta', meta)
				except:
					pass
				# Add links
				try:
					for _dest in i[1].keys():
						for _type in i[1][_dest]:
							manager.call(_id, 'addLink', _dest, _type)
				except:
					pass
				# Add Data
				result										= manager.call(_id, 'addData', i[2])
				# Commit the node
				_ids.append(_id)
			return _ids

	def _remove(self):
		""" Add a node or information to a node """
		try:
			if self._actions[1] == 'meta':
				_results									= []
				try:
					for _node in self._values[0]:
						try:
							_subresults						= []
							for _meta in self._values[0][_node]:
								_subresults.append(manager.call(_node,'remMeta',_meta))
							_results.append(_subresults)
						except IndexError:
							_results.append(False)
					return _results
				except:
					return `False`
			elif self._actions[1] == 'links':
				_results									= []
				try:
					# For each node we want to add new links to
					for _node in self._values[0]:
						try:
							_subresults						= []
							# For each destination node
							for _dest in self._values[0][_node]:
								_ssubresults				= []
								# For each link type
								for _type in self._values[0][_node][_dest]:
									_ssubresults.append(manager.call(_node,'remLink',_dest,_type))
								_subresults.append(_ssubresults)
							_results.append(_subresults)
						except IndexError:
							_results.append(False)
					return _results
				except:
					return `False`
			elif self._actions[1] == 'data':
				_ids										= []
				for i in self._values[0]:
					_ids.append(manager.call(i,'remData'))
				return _ids
		except:
			_ids											= []
			for i in self._values[0]:
				_ids.append(manager.remove(i))
			return _ids

	def _set(self):
		""" Add a node or information to a node """
		try:
			if self._actions[1] == 'meta':
				return 'SET META'
			elif self._actions[1] == 'links':
				return 'SET LINKS'
			elif self._actions[1] == 'data':
				return 'SET DATA'
			elif self._actions[1] == 'mime':
				return 'SET MIME'
		except:
			return False

