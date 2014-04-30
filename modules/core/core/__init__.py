# -*- coding: utf-8 -*-
"""
	core
	~~~~

	This module provides read and write access to the central Lernfunk database.

	:copyright: (c) 2012 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
"""

from flask import Flask

class ReverseProxied(object):
	'''Wrap the application in this middleware and configure the
	front-end server to add these headers to let you quietly bind
	this to a URL other than / and to an HTTP scheme that is
	different than what is used locally.

	In nginx:
	location /myprefix {
		proxy_pass http://192.168.0.1:5001;
		proxy_set_header Host $host;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Scheme $scheme;
		proxy_set_header X-Script-Name /myprefix;
		}

	:param app: the WSGI application
	'''
	def __init__(self, app):
		self.app = app

	def __call__(self, environ, start_response):
		script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
		if script_name:
			environ['SCRIPT_NAME'] = script_name
			path_info = environ['PATH_INFO']
			if path_info.startswith(script_name):
				environ['PATH_INFO'] = path_info[len(script_name):]

		scheme = environ.get('HTTP_X_SCHEME', '')
		if scheme:
			environ['wsgi.url_scheme'] = scheme
		return self.app(environ, start_response)

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# create our little application :)
app = Flask(__name__)
app.config.from_pyfile('config.py')
app.wsgi_app = ReverseProxied(app.wsgi_app)

# Import custom converter
import core.converter
app.url_map.converters['uuid'] = core.converter.UUIDConverter
app.url_map.converters['lang'] = core.converter.LanguageConverter
app.url_map.converters['user'] = core.converter.UsernameConverter

# set the secret key.
# You should really keep this secret:
app.secret_key = '\xbe\xfd\xef\x99\x9bl.:4\xb1\xc0!\xe7:D \x9en\x88tu\xd0\xde\xaa'

# import submodules
import core.archive
import core.admin.delete
import core.admin.get
import core.admin.post
import core.admin.put
import core.cache
import core.db
import core.login
import core.user
import core.view
