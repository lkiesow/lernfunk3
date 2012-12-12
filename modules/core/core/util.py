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
from string import hexdigits
from xml.dom.minidom import parseString


def result_dom():
	'''Return an empty DOM tree for results
	'''
	return parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')


def xml_add_elem( dom, parent, name, val ):
	'''Insert a new element with text node into a DOM tree if the value exists.
	
	Keyword arguments:
	dom    -- DOM tree
	parent -- Parent element of the one to create
	name   -- Name of the element
	val    -- Text value of the element
	'''
	if val:
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
	if len(s) != 36:
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
