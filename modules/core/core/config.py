#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Make shure to disable this in production
DEBUG = True

# Database access configuration
DATABASE_HOST   = 'localhost'
DATABASE_USER   = 'root'
DATABASE_NAME   = 'lernfunk3'
DATABASE_PASSWD = ''
DATABASE_PORT   = 3306

# Secret key to use for signing sessions.
# Choose a good one (urandom)
SECRET_KEY = 'development key'

# Maximum amount of data to accept for POST/PUT requests. If this limit is
# exceeded a 400 Bad Request is returned.
PUT_LIMIT = 50000
POST_LIMIT = 50000

# Default language which will be used for suggestions.
DEFAULT_LANGUAGE = 'de'
