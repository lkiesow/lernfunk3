# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core::Authenticate
	~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.
	
	** Authenticate contains methods for authentication and authorization
	** handling.

    :copyright: (c) 2012 by Lars Kiesow
    :license: FreeBSD and LGPL, see LICENSE for more details.
"""

from hashlib import sha512


def check_credentials( username, password ):
	'''Return an empty DOM tree for results
	'''
	hashlib.sha512('123').digest()
	return parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')
