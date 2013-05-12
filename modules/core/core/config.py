#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
	core.config
	~~~~~~~~~~~~~

	This is the main module configuration.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
'''

# Dubug ################################
DEBUG = True
'''THis will enable the debug mode. If enabled, the webservice will print
requests, SQL queries, etc. to stdout and will also return a stack trace via
HTTP. Make shure to disable this option in production.'''

# Database #############################
DATABASE_HOST   = 'localhost'
'''Database server configuration'''

DATABASE_USER   = 'root'
'''Database user configuration'''

DATABASE_NAME   = 'lernfunk3'
'''Database name configuration'''

DATABASE_PASSWD = ''
'''Database password configuration'''

DATABASE_PORT   = 3306
'''Database access port configuration'''

MEMCACHED_HOST  = 'localhost'

# Session ##############################
SECRET_KEY = 'development key'
'''Secret key to use for signing sessions.
Choose a good one (urandom)
'''

# Limits ###############################
PUT_LIMIT = 50000
'''Maximum amount of data to accept for PUT requests. If this limit is exceeded
a 400 Bad Request is returned.
'''

POST_LIMIT = 50000
'''Maximum amount of data to accept for POST requests. If this limit is
exceeded a 400 Bad Request is returned.
'''

########################################
DEFAULT_LANGUAGE = 'de'
'''Default language which will be used for suggestions.'''
