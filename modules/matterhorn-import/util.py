# -*- coding: utf-8 -*-
"""
	Lernfunk3::Matterhorn-Import::Util
	~~~~~~~~~~~~~~~

    :copyright: (c) 2013 by Lars Kiesow
    :license: FreeBSD and LGPL, see LICENSE for more details.
"""
import uuid


def xml_get_data(node, name, raiseError=False, namespace='*', type=None,
		array='never'):
	'''Get text from first selected elements. 
	Return None if there is no text.

	Keyword arguments:
	node        -- Node to use as root
	name        -- Name of the node which contains the text
	raiseError  -- If an error should be raised if element does not exist
	namespace   -- Namespace to use
	type        -- Type conversion of the data
	array       -- One of 'always', 'allowed', 'never' (default)
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
		result = is_true(type)
	elif type:
		result = type(result)
	return result


def is_true( val ):
	'''Check if a string is some kind of representation for True.

	Keyword arguments:
	val -- Value to check
	'''
	if isinstance(val, basestring):
		return val.lower() in ('1', 'yes', 'true')
	return val
