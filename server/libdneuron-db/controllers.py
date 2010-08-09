#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 nowrap:
import os
import sys
import threading
import socket
import string
import time
import random
import ConfigParser
from libneuron-db import loggers
from libneuron-db import grammer
from libneuron-db import errors

__all__														= ['run_controller', 'handle_connection']
protocol_version											= '1.01'
module_list													= []

class run_controller(threading.Thread):
	""" The create_listerner class/thread creates a socket server to handle our
		connections from a client system. The sockets interact with the other
		threads to execute commands on the system. To do this, it calls the
		global method list defined within our daemon to decide which thread has
		the method we are trying to call.
	"""
	dismiss													= threading.Event()

	def __init__(self):
		""" Load the threading initiator, then setup some port information for
			the network server. By default, we listen on port 3307 for our
			socket connections.
		"""
		threading.Thread.__init__(self,None)
		run_controller.dismiss.set()

		# Parse our configuration options
		config												= ConfigParser.ConfigParser()
		config.read(['neuron-db.conf', os.path.expanduser('~/.neuron-db.conf')])

		# Socket server setup
		try:
			# Fetch the port we need to listen on
			if config.has_option('global', 'port'):
				self.port									= int(config.get('global','port'))
			else:
				self.port									= 3307

			# Fetch the hostname to bind to
			if config.has_option('global', 'host'):
				self.bind_addr								= config.get('global','host')
			else:
				self.bind_addr								= 'localhost'

			# Socket server setup
			self.listen										= 5
			self.timeout									= 1
		except:
			loggers.log_queue.put({'type':'error','source':'control','message':'Error starting server'})
			print 'Error starting controller system'
			sys.exit(1)

	def run(self):
		""" The run method is called when we start the thread. We first bind
			the server to socket 3307, then we wait for a connection from a
			client and create a new thread to handle the connection.
		"""
		# Bind the server to our socket
		server_socket										= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind((self.bind_addr, self.port))
		server_socket.listen(self.listen)
		server_socket.settimeout(self.timeout)
		loggers.log_queue.put({'type':'notice','source':'control','message':'Controller started'})
		# Wait for a connection to be established
		while run_controller.dismiss.isSet():
			try:
				# Wait for a connection from a client
				client_socket, address						= server_socket.accept()
				handle_connection(client_socket, address, self.bind_addr)
				loggers.log_queue.put({'type':'notice','source':'control','message':'Socket control started from '+address[0]})
			except socket.timeout:
				pass

class handle_connection(threading.Thread):
	""" For  each client connection, we create a thread to handle any commands.
		Note that the client socket is closed internally.
	"""
	def __init__(self, client_socket, address, bind_addr):
		threading.Thread.__init__(self, None)
		self.client_socket									= client_socket
		self.address										= address
		self.bind_addr										= bind_addr
		self._errors										= True
		self._definitions									= {}
		self._grammer										= grammer.grammer_controller(self._definitions)
		self.start()

	def run(self):
		self.send(self.set_welcome())
		while True:
			try:
				data										= string.strip(self.read())
				# Check for any commands for this module. If we dont find a command
				# here, check if it is destined for a different module.
				if data == 'quit': break
				elif data[0:4] == 'help': self.send(self.display_help(data)); continue
				elif data[0:6] == 'errors': self.send(self.set_error(data[7:])+'\n'); continue
				elif not data: continue
				else: self.send(`self._fetch_results(data)`+'\n'); continue
			except errors.ParseError, e:
				if self._errors == True:
					self.send('0x%X: %s\n' % (e.args[0], errors.ERRORS[e.args[0]]))
				else:
					self.send('0x%X\n' % e.args[0])
				continue
			except:
				if self._errors == True:
					self.send('0x00: %s\n' % (errors.ERRORS[0]))
				else:
					self.send('0x00\n')
				continue

		self.client_socket.shutdown(2)
		self.client_socket.close()
		loggers.log_queue.put({'type':'notice','source':'control','message':'Socket control quit from '+self.address[0]})

	def send(self, data):
		""" When we send data to the client, we need to first calculate the size of the information
			we want to send. We then tack this into the first 32 bytes of information.
			
			The client must check this value to ensure that they fetch all the information from the
			servers buffer.
		"""
		data_length											= int(data.__len__())#+32
		self.client_socket.send("%032d%s" % (data_length, data))

	def read(self):
		""" Read information from the socket.
			Start by reading the first 32 bytes to get the message length. Once
			we have the length, we loop through the socket reads to fetch all
			the information and pushing it onto our output stack.
		"""

		# Fetch the packet size from the first 32 bytes of data.
		data_length											= int(self.client_socket.recv(32))
		output												= ''

		# Loop through sockets reads until we have all the data.
		while data_length >= 1:
			data											= self.client_socket.recv(8192)
			data_length										= data_length - int(data.__len__())
			output											= output + data

		# return the data to the calling method
		return output

	def set_welcome(self):
		""" When a client creates a connection, we send a initiator string. The
			string contains the server version, time, and server type to help
			the client handle the connection.
		"""
		welcome												= '220 %s neuron-db server %s; %s\n' % (self.bind_addr,protocol_version,time.asctime())
		return welcome

	def set_error(self, value=False):
		""" Toggle the type of error reporting we want. The value should be a
			boolean value. If no value is entered, it returns the state of the
			error reporting.
		"""
		value												= value.strip()
		if len(value) == 0:
			return '[error:%s]' % self._errors
		neg													= ['False','false','0','f','F']
		pos													= ['True','true','1','t','T']
		if value in neg:
			self._errors									= False
			return '[error:False]'
		elif value in pos:
			self._errors									= True
			return '[error:True]'
		else:
			raise errors.ParseError(0x01)

	def _fetch_results(self, data):
		""" Run the query, and check for any information we need to store from
			the grammer controller. Local data is returned within braces, and
			user data to be returned is stored within square brackets.
		"""
		results												= self._grammer.run(data)
		return results

	def display_help(self, data):
		""" Display any help for the control system plus a list of other mods
			that we can call for help using 'help mod'.
		"""
		# Check if we need to return external help information
		help_cmd											= data.split(' ')
		# Display the controllers help. Once we show internal commands, we look
		# for any modules we have loaded and display the list to the user.
		if not len(help_cmd) >= 2:
			msg												= 'neuron-db\n'
			msg												+= '-' * 80 + '\n'
			msg												+= 'help'+'\t' * 4 + 'Display this page\n'
			msg												+= 'help [module]'+'\t'*3+'Display help for a module\n'
			msg												+= 'quit'+'\t'*4+'Quit the control console\n'
			msg												+= 'errors [True|False]'+'\t'*2+'View/Set errors.\n'
			msg												+= 'shutdown'+'\t'*3+'Shutdown the system\n'
			msg												+= '\nMODULES\n'+'-' * 80 + '\n'

			# Loop through the module list and display the module names
			for i in module_list:
				msg											+= i['name']+'\t'*4+i['description']+'\n'
			return msg
		else:
			# Display help for a perticular module
			help_thread										= string.strip(help_cmd[1])
			for i in module_list:
				if i['name'] == help_thread:
					return i['help']
		return 'Sorry, no help available\n'

if __name__ == '__main__':
	# Run some unit tests to check we have a working socket server
	listener												= run_controller()
	listener.start()
	listener.join()

