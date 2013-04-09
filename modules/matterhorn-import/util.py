# -*- coding: utf-8 -*-
"""
	Lernfunk3: Matterhorn Import Service Utils
	==========================================

	:copyright: 2013 by Lars Kiesow

	:license: FreeBSD and LGPL, see LICENSE for more details.
"""
import uuid


def xml_get_data(node, name, raiseError=False, namespace='*', type=None,
		array='never'):
	'''Get text from first selected elements. Return None if there is no text.

	:param node:       Node to use as root
	:param name:       Name of the node which contains the text
	:param raiseError: If an error should be raised if element does not exist
	:param namespace:  Namespace to use
	:param type:       Type conversion of the data
	:param array:      One of 'always', 'allowed', 'never' (default)

	:returns: Value of first element or None
	'''

	# Autodetect namespace:
	#  lf: -> XML_NS_LF
	#  dc: -> XML_NS_DC
	if not namespace:
		if name.startsWith('lf:'):
			namespace = XML_NS_LF
			name = name.split(':',1)[1]
		elif name.startsWith('dc:'):
			namespace = XML_NS_DC
			name = name.split(':',1)[1]

	
	# Get data
	result = None
	try:
		if namespace:
			result = [ x.childNodes[0].data \
					for x in node.getElementsByTagNameNS(namespace, name) ]
		else:
			result = [ x.childNodes[0].data \
					for x in node.getElementsByTagName(name) ]
	except IndexError as e:
		if raiseError:
			raise e
	
	if array == 'never':
		if result == []:
			result = None
		elif len(result) != 1:
			raise ValueError('data != one element')
		else:
			result = result[0]
	elif array == 'allowed':
		if result == []:
			result = None
		elif len(result) == 1:
			result = result[0]
	elif array != 'always':
		raise ArgumentError('Invalid value for array parameter')

	# Special handling of bools:
	if type == bool:
		result = [ is_true(x) for x in result ] \
				if isinstance(result, list) else is_true(result)
	elif type:
		result = [ type(x) for x in result ] \
				if isinstance(result, list) else type(result)
	return result


def is_true( val ):
	'''Check if a string is some kind of representation for True.

	:param val: Value to check

	:returns: True or False

	Example::

		>>> is_true( 'yes' )
		True
		>>> is_true( 'YeS' )
		true
		>>> is_true( 'no' )
		False
		>>> is_true( 'true' )
		True
		>>> is_true( 1 )
		True
		>>> is_true( 0 )
		False
	'''
	if isinstance(val, basestring):
		return val.lower() in ('1', 'yes', 'true')
	return val


def split_vals( vals, delim, stripchars=' ' ):
	'''This function will split every value of a list *vals* using the character
	from *delim* als delimeter, strip the new values using *stripchars* and
	return all values in a new, one dimensional list.

	:param vals:       List of string values to split
	:param delim:      Delimeter to use for splitting the strings
	:param stripchars: Character to strip from the new values

	:returns: List of split values

	Example::
		
		>>> x = ['val;val2', 'val3; val4, val5']
		>>> split_vals( x, ';,' )
		['val', 'val2', 'val3', 'val4', 'val5']

	'''
	for d in delim:
		new = []
		for v in vals:
			for n in v.split(d):
				n = n.strip(stripchars)
				if n:
					new.append(n)
		vals = new
	return vals
