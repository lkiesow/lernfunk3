# -*- coding: utf-8 -*-
"""
	xmp.get_data
	~~~~~~~~~~~~


	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from base64 import urlsafe_b64encode

from matterhornsearch import app


def get_request_data(username=None, password=None):

	path = app.config['LERNFUNK_CORE_PATH'] \
			if app.config['LERNFUNK_CORE_PATH'].endswith('/') \
			else app.config['LERNFUNK_CORE_PATH'] + '/'
	url = '%s://%s:%i%s' % (
			app.config['LERNFUNK_CORE_PROTOCOL'],
			app.config['LERNFUNK_CORE_HOST'],
			app.config['LERNFUNK_CORE_PORT'],
			path )
	auth = ('Authorization', 'Basic ' + urlsafe_b64encode("%s:%s" % \
			( username, password ))) \
			if username and password \
			else None

	return url, auth


def is_true( val ):
	'''Check if a string is some kind of representation for True.

	Keyword arguments:
	val -- Value to check
	'''
	if isinstance(val, basestring):
		return val.lower() in ('1', 'yes', 'true')
	return val


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
