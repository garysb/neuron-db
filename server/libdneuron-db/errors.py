# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 nowrap:
RESERVED = [
	'get',
	'set',
	'add',
	'remove',
	'quit',
	'defined',
	'errors',
	'help',
	'start',
	'undo',
	'commit',
	'as'
]

ERRORS = {
	0x00: 'Unknown error: Please report this to us with the query you entered. As a workaround, try change your query',
	0x01: 'The error variable can only be True or False: errors [True|False|true|false|T|F|t|f|1|0]',
	0x10: 'First value needs to be an action: [get|add|remove|set|define]',
	0x11: 'Second value needs to be a type: [meta|mime|data|size|creates|modified|links]',
	0x12: 'Third value can only be used if second value is links type: [meta|mime|data|size|creates|modified|links]',
	0x13: 'Compound queries must end in a valid type: [meta|mime|data|size|creates|modified|links]',
	0x14: 'Unable to merge compound queries link results: Please report this for us. As a workaround reduce compounds',
	0x20: 'Unmatched bracket found: Check your syntax',
	0x50: 'Definition error: Please report this to us with the query you entered. As a workaround, try change your query',
	0x51: 'Definition error. Definitions must be inclosed in square brackets: define [\'variable\',\'variable\']',
	0x52: 'Definition error: Variable names must be inclosed in single quotes: define [\'variable\',\'variable\']',
	0x53: 'Definition error: You cannot use one of these reserved words: %s' % RESERVED,
	0x54: 'Definition error: Variables may only use numbers and letters: [0-9A-Za-z]'
}

class ParseError(Exception):
	pass

