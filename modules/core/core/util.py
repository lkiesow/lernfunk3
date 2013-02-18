# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core::Util
	~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.
	
	** Util contains general helper functions, …

    :copyright: (c) 2012 by Lars Kiesow
    :license: FreeBSD and LGPL, see LICENSE for more details.
"""

from core import app
from core.db import get_db
from string import hexdigits, letters, digits
from xml.dom.minidom import parseString
import re
from flask import request, make_response
import uuid

'''All characters allowed for language tags.'''
lang_chars = letters + digits + '-_'

'''Simple regular expression to match IETF language tags.'''
lang_regex_str  = '(?:[a-zA-Z]{2,3}([-_][a-zA-Z\d]{1,8})*)'
lang_regex      = re.compile(lang_regex_str)
lang_regex_full = re.compile('^'+lang_regex_str+'$')

'''All characters allowed for usernames.'''
username_chars = lang_chars

'''Simple regular expression to match usernames.'''
username_regex_str  = '(?:[\w-]+)'
username_regex      = re.compile(username_regex_str)
username_regex_full = re.compile('^'+username_regex_str+'$')

'''All characters allowed for server names.'''
servername_chars = username_chars + '.'

'''XML namespace definitions'''
XML_NS_DC = "http://purl.org/dc/elements/1.1/"
XML_NS_LF = "http://lernfunk.de/terms"

def result_dom( count=0 ):
	'''Return an empty DOM tree for results
	'''
	return parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"
			resultcount="%s"></result>''' % int(count) )


def xml_add_elem( dom, parent, name, val ):
	'''Insert a new element with text node into a DOM tree if the value exists.
	
	Keyword arguments:
	dom    -- DOM tree
	parent -- Parent element of the one to create
	name   -- Name of the element
	val    -- Text value of the element
	'''
	if val != None:
		elem = dom.createElement(name)
		elem.appendChild( dom.createTextNode(str(val)) )
		parent.appendChild( elem )
		return elem
	return None


def is_uuid(s):
	'''Check if a string is a valid UUID.

	Keyword arguments:
	s -- UUIS as string to check
	'''
	if not s or len(s) != 36:
		return False
	return \
			s[ 0] in hexdigits and \
			s[ 1] in hexdigits and \
			s[ 2] in hexdigits and \
			s[ 3] in hexdigits and \
			s[ 4] in hexdigits and \
			s[ 5] in hexdigits and \
			s[ 6] in hexdigits and \
			s[ 7] in hexdigits and \
			s[ 8] == '-' and \
			s[9] in hexdigits and \
			s[10] in hexdigits and \
			s[11] in hexdigits and \
			s[12] in hexdigits and \
			s[13] == '-' and \
			s[14] in hexdigits and \
			s[15] in hexdigits and \
			s[16] in hexdigits and \
			s[17] in hexdigits and \
			s[18] == '-' and \
			s[19] in hexdigits and \
			s[20] in hexdigits and \
			s[21] in hexdigits and \
			s[22] in hexdigits and \
			s[23] == '-' and \
			s[24] in hexdigits and \
			s[25] in hexdigits and \
			s[26] in hexdigits and \
			s[27] in hexdigits and \
			s[28] in hexdigits and \
			s[29] in hexdigits and \
			s[30] in hexdigits and \
			s[31] in hexdigits and \
			s[32] in hexdigits and \
			s[33] in hexdigits and \
			s[34] in hexdigits and \
			s[35] in hexdigits


def is_true( val ):
	'''Check if a string is some kind of representation for True.

	Keyword arguments:
	val -- Value to check
	'''
	return val.lower() in ['1', 'yes', 'true']


def xml_get_text(node, name, raiseError=False, namespace=None):
	'''Get text from first selected elements. 
	Return None if there is no text.

	Keyword arguments:
	node -- Selected nodes
	'''
	if not namespace:
		if name.startsWith('lf:'):
			namespace = XML_NS_LF
			name = name.split(':',1)[1]
		elif name.startsWith('dc:'):
			namespace = XML_NS_DC
			name = name.split(':',1)[1]
	if raiseError:
		if namespace:
			return node.getElementsByTagNameNS(namespace, name)[0].childNodes[0].data
		else:
			return node.getElementsByTagName(name)[0].childNodes[0].data
	try:
		if namespace:
			return node.getElementsByTagNameNS(namespace, name)[0].childNodes[0].data
		else:
			return node.getElementsByTagName(name)[0].childNodes[0].data
	except IndexError:
		return None


def to_int( s, default=0 ):
	'''Convert string to integer. If the string cannot be converted a default
	value is used.

	Keyword arguments:
	s       -- String to convert
	default -- Value to return if the string cannot be converted
	'''
	try:
		return int(s)
	except ValueError:
		return default



def search_query( query, allowed ):
	return 'or '.join([ 
		'and '.join([ search_op(allowed, *y.split(':',2)) \
				for y in x.split(',')]) \
				for x in query.split(';') ])



def search_op( allowed, op, key, val ):
	
	if not key in allowed.keys():
		raise ValueError('Illegal identifier for search argument')

	type,key = allowed[key]
	
	if type == 'uuid':
		if op == 'eq':
			return "%s = x'%s' " % (key, uuid.UUID(val).hex)
		if op == 'neq':
			return "%s != x'%s' " % (key, uuid.UUID(val).hex)

	elif type == 'int':
		if op == 'eq':
			return '%s = %i ' % (key, int(val))
		if op == 'neq':
			return '%s != %i ' % (key, int(val))
		if op == 'lt':
			return '%s < %i ' % (key, int(val))
		if op == 'gt':
			return '%s > %i ' % (key, int(val))
		if op == 'leq':
			return '%s <= %i ' % (key, int(val))
		if op == 'geq':
			return '%s >= %i ' % (key, int(val))

	elif type == 'str':
		val = get_db().escape_string(val)
		if op == 'eq':
			return '%s = "%s" ' % (key, val)
		if op == 'neq':
			return '%s != "%s" ' % (key, val)
		if op == 'in':
			return '%s like "%%%s%%" ' % (key, val)
		if op == 'startswith':
			return '%s like "%s%%" ' % (key, val)
		if op == 'endswith':
			return '%s like "%%%s" ' % (key, val)

	elif type == 'time':
		import datetime
		try:
			# Assume ISO datetime format (YYYY-MM-DD HH:MM:SS)
			datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
		except ValueError:
			import email.utils
			# Check RFC2822 datetime format instead
			# (Do not use , for separating weekday and month!)
			val = datetime.datetime.fromtimestamp(
					email.utils.mktime_tz(email.utils.parsedate_tz(val))
					).strftime("%Y-%m-%d %H:%M:%S")
		if op == 'eq':
			return '%s = "%s" ' % (key, val)
		if op == 'neq':
			return '%s != "%s" ' % (key, val)
		if op == 'lt':
			return '%s < "%s" ' % (key, val)
		if op == 'gt':
			return '%s > "%s" ' % (key, val)
		if op == 'leq':
			return '%s <= "%s" ' % (key, val)
		if op == 'geq':
			return '%s >= "%s" ' % (key, val)
	
	elif type == 'lang':
		if not lang_regex_full.match(val):
			raise ValueError('Invalid language tag')
		if op == 'eq':
			return '%s = "%s" ' % (key, val)
		if op == 'neq':
			return '%s != "%s" ' % (key, val)
		if op == 'in':
			return '%s like "%%%s%%" ' % (key, val)
		if op == 'startswith':
			return '%s like "%s%%" ' % (key, val)


	raise ValueError('Illegal search operator')

	return '-'



def __xmlify( result, dom, parent ):
	if result is None:
		raise ValueError()
	elif isinstance(result, dict):
		for k,v in result.iteritems():
			if isinstance(v, list):
				for e in v:
					elem = dom.createElement(k)
					try:
						__xmlify( e, dom=dom, parent=elem )
						parent.appendChild( elem )
					except ValueError:
						pass
			else:
				elem = dom.createElement(k)
				try:
					__xmlify( v, dom=dom, parent=elem )
					parent.appendChild( elem )
				except ValueError:
					pass
	else:
		parent.appendChild( dom.createTextNode(str(result)) )




def xmlify( result, resultcount=1 ):

	dom = result_dom( resultcount )
	parent = dom.firstChild

	__xmlify( result, dom, parent )

	# Return string representation
	if app.debug and not request.is_xhr:
		response = make_response( dom.toprettyxml() )
	else:
		response = make_response( dom.toxml() )
	response.mimetype = 'application/xml'
	return response
