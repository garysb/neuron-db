# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 nowrap:
import os
import ConfigParser
from libneuron-db import loggers

# Parse our configuration options
config									= ConfigParser.ConfigParser()
config.read(['neuron-db.conf', os.path.expanduser('~/.neuron-db.conf')])
try:
	# Fetch the data directory to work on
	if config.has_option('global', 'data'):
		data_dir						= int(config.get('global','data'))
	else:
		data_dir						= 'data'
except:
	data_dir							= 'data'

loggers.log_queue.put({'type':'notice','source':'engine','message':'File storage engine loaded'})

def _add(node_id, node_data):
	""" Add the node data to the storage engine. The file storage engine simply
		creates a seperate file for each node. This isnt a very good way of
		doing it, but it is simple to trace and implement.
	"""
	try:
		_file							= open('%s/%s.dat' % (data_dir, node_id), 'ab')
		_file.write(node_data)
		_file.flush()
		_file.close()
		return True
	except:
		return False

def _set(node_id, node_data):
	""" Add the node data to the storage engine. The file storage engine simply
		creates a seperate file for each node. This isnt a very good way of
		doing it, but it is simple to trace and implement.
	"""
	try:
		_file							= open('%s/%s.dat' % (data_dir, node_id), 'wb')
		_file.write(node_data)
		_file.flush()
		_file.close()
		return True
	except:
		return False

def _remove(node_id):
	""" Remove a node from the system. Within the file storage engine, we only
		remove the file containing the data. And return true if successfull.
	"""
	try:
		os.unlink('%s/%s.dat' % (data_dir, node_id))
		return True
	except:
		return False

def _get(node_id):
	""" Fetch the data content of a node. In the file storage engine we simply
		return the content of the dat file for the node.
	"""
	try:
		_file							= open('%s/%s.dat' % (data_dir, node_id), 'rb')
		_data							= _file.read()
		return _data
	except:
		return False

