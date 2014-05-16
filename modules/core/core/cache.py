# -*- coding: utf-8 -*-
'''
	core.cache
	~~~~~~~~~~

	This module contains methods to handle cached database access.

	:copyright: (c) 2012 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
'''

from core.db   import get_db
from core      import app
from flask     import _app_ctx_stack
try:
	import pylibmc
except ImportError:
	import memcache


def get_mc():
	'''Returns a Memcached client. If there is none for the current application
	context it will create a new.
	'''
	top = _app_ctx_stack.top
	if not hasattr(top, 'memcached_cli'):
		try:
			top.memcached_cli = pylibmc.Client(
					[app.config['MEMCACHED_HOST']],
					binary = True,
					behaviors = {'tcp_nodelay': True, 'ketama': True})
		except NameError:
			top.memcached_cli = memcache.Client(
					[app.config['MEMCACHED_HOST']], debug=0)
	return top.memcached_cli


def execute_cached_query( key, cursor, query, query_args=None, time=600 ):
	'''Execute a MySQL query and cache it or retrive it from cache if it is
	already cached.

	:param key: Unique key to use for this request.
	:param cursor: Database cursor to execute query if necessary.
	:param query: Query to execute.
	:param query_args: Arguments to pass to the execute method.
	:param time: Time to cache the query.

	Example::

		>>> cur = get_db().cursor()
		>>> execute_cached_query( 'person_5', cur,
				'select username from lf_user where id=5 ' )
		('jdoe')

	'''
	mc = get_mc()
	key = 'lf3_core_' + key
	result = mc.get(key)
	if result is None:
		if query_args:
			cursor.execute(query, query_args)
		else:
			cursor.execute(query)
		result = cursor.fetchall()
		mc.set(key, result, time)
	return result
