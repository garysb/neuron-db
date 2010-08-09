#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 nowrap:
import os
import threading
import socket
import string
import time
import Queue
import ConfigParser

protocol_version											= '1.01'
log_queue													= Queue.Queue()

class run_logger(threading.Thread):
	""" The create_listerner class/thread creates a socket server to handle our
		connections from a client system. The sockets interact with the other
		threads to execute commands on the system. To do this, it calls the
		global method list defined within our daemon to decide which thread has
		the method we are trying to call.
	"""
	dismiss													= threading.Event()
	client_list												= []
	client_lock												= threading.Lock()

	def __init__(self):
		threading.Thread.__init__(self,None)
		run_logger.dismiss.set()

		global log_queue
		log_queue											= Queue.Queue()

		# Parse our configuration options
		config												= ConfigParser.ConfigParser()
		config.read(['dropletdb.conf', os.path.expanduser('~/.dropletdb.conf')])
		try:
			# Fetch the port we need to listen on
			if config.has_option('logging', 'port'):
				self.port									= int(config.get('logging','port'))
			else:
				self.port									= 3308

			# Fetch the hostname to bind to
			if config.has_option('logging', 'host'):
				self.bind_addr								= config.get('logging','host')
			else:
				self.bind_addr								= 'localhost'

			# Fetch the logfile name
			if config.has_option('logging', 'logfile'):
				self.logfile								= config.get('logging','logfile')
			else:
				self.logfile								= 'dropletdb.log'

			self.listen										= 5
			self.timeout									= 0.5
		except:
			print 'Error starting logging system'

	def run(self):
		# Create out file log thread
		run_logger.client_lock.acquire()
		file_client											= handle_file_log(self.logfile)
		file_client.setName('fileThread')
		run_logger.client_list.append(file_client)
		run_logger.client_lock.release()
		file_client.start()
		log_queue.put({'type':'notice','source':'logger','message':'File log started'})
		# Bind the server to our socket
		server_socket										= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind((self.bind_addr, self.port))
		server_socket.listen(self.listen)
		server_socket.settimeout(self.timeout)
		# Wait for a connection to be established
		while run_logger.dismiss.isSet():
			try:
				msg											= log_queue.get(block=False, timeout=False)
				for client in run_logger.client_list:
					client.my_queue.put(msg)
			except Queue.Empty:
				pass

			try:
				# Wait for a connection from a client
				client_socket, address						= server_socket.accept()
				run_logger.client_lock.acquire()
				new_client									= handle_connection(client_socket, address, self.bind_addr)
				run_logger.client_list.append(new_client)
				run_logger.client_lock.release()
				new_client.start()
				log_queue.put({'type':'notice','source':'logger','message':'Socket log started from '+address[0]})
			except socket.timeout:
				pass

class handle_connection(threading.Thread):
	""" This class implements a tcp log watcher.
	"""
	def __init__(self, client_socket, address, bind_addr):
		threading.Thread.__init__(self, None)
		self.my_queue										= Queue.Queue()
		self.client_socket									= client_socket
		self.client_socket.settimeout(0.5)
		self.address										= address
		self.bind_addr										= bind_addr

	def run(self):
		#self.client_socket.setblocking(0)
		self.client_socket.send(self.set_welcome())
		while True:
			try:
				raw_msg										= self.my_queue.get(True, 0.5)
				if raw_msg:
					msg										= '[%s] [%s] [%s] %s\n' % (time.asctime(), raw_msg['source'], raw_msg['type'], raw_msg['message'])
				self.client_socket.send(msg)
			except Queue.Empty:
				try:
					raw_data								= self.client_socket.recv(4096)
				except:
					continue
				if raw_data:
					data									= string.strip(raw_data)
					if not data or data == 'quit': break
					if data == 'clients':
						self.client_socket.send(`run_logger.client_list`+'\n')
						continue
					self.client_socket.send(`list(data)`+'\n')
		self.client_socket.shutdown(2)
		self.client_socket.close()
		run_logger.client_lock.acquire()
		run_logger.client_list.remove(self)
		run_logger.client_lock.release()
		global log_queue
		log_queue.put({'type':'notice','source':'logger','message':'Socket log quit from '+self.address[0]})

	def set_welcome(self):
		welcome												= '220 %s neuron-db logs %s; %s\n' % (self.bind_addr,protocol_version,time.asctime())
		return welcome

class handle_file_log(threading.Thread):
	""" The handle_file_log object/thread generates a filesystem log that adds
		its queue messages into the filesystem.
	"""
	my_queue												= Queue.Queue()

	def __init__(self, logfile='dropletdb.log'):
		threading.Thread.__init__(self, None)
		self.logfile										= logfile

	def run(self):
		while True:
			try:
				raw_msg										= self.my_queue.get(True, 0.5)
				if raw_msg:
					msg										= '[%s] [%s] [%s] %s\n' % (time.asctime(), raw_msg['source'], raw_msg['type'], raw_msg['message'])
					log_file								= open(self.logfile,'a')
					log_file.write(msg)
					log_file.close()
			except Queue.Empty:
				pass

if __name__ == '__main__':
	# Run some unit tests to check we have a working socket server
	logger													= run_logger()
	logger.start()

	# Add some random test messages to the queue
	time.sleep(3)
	log_queue.put({'type':'notice','source':'logger','message':'Unit test 1'})
	time.sleep(0.5)
	log_queue.put({'type':'error','source':'logger','message':'Unit test 2'})
	log_queue.put({'type':'notice','source':'logger','message':'Unit test 3'})
	time.sleep(2)
	log_queue.put({'type':'warning','source':'logger','message':'Unit test 4'})
	log_queue.put({'type':'notice','source':'logger','message':'Unit test 5'})
	time.sleep(0.1)
	log_queue.put({'type':'warning','source':'logger','message':'Unit test 6'})
	time.sleep(0.1)
	log_queue.put({'type':'notice','source':'logger','message':'Unit test 7'})
	time.sleep(2)
	log_queue.put({'type':'error','source':'logger','message':'Unit test 8'})
	time.sleep(1)
	log_queue.put({'type':'notice','source':'logger','message':'Unit test 9'})
	log_queue.put({'type':'notice','source':'logger','message':'Unit test 10'})

	logger.join()

