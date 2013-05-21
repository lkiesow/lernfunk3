# -*- coding: utf-8 -*-
"""
	feedgenerator.storage
	~~~~~~~~~~~~~~~~~~~~~

	Handles all redis storage related things for the Lernfunk feedgenerator.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""

from flask import _app_ctx_stack
import redis

from feedgenerator import app

REDIS_NS = 'lf_feedgen_'

def get_redis():
	'''Opens a new database connection if there is none yet for the
	current application context.
	'''
	top = _app_ctx_stack.top
	if not hasattr(top, 'r_server'):
		r_server = redis.Redis(
				host	   = app.config['DATABASE_HOST'],
				port	   = app.config['DATABASE_PORT'],
				db	      = app.config['DATABASE_DB'],
				password = app.config['DATABASE_PASSWD'] )
		if not top is None:
			top.r_server = r_server
		return r_server

	return top.r_server


def db_flushall():
	'''This method will remove all keys in the feedgenerator namespace from the
	connected redis database, forcing the webservice to rebuild the storage.
	'''
	r_server = get_redis()
	keys = r_server.keys('%s*' % REDIS_NS)
	return r_server.delete(*keys)


def db_save(copy_to=None):
	'''Tell the Redis server to save its data to disk, blocking until the save
	is complete. The data will be written to the directory defined in the redis
	configuration file. If copy_to is set the file will be copied to the
	specified location.

	:param copy_to: Copy the database dump to this location.
	'''
	r_server = get_redis()
	result = r_server.save()
	if result and copy_to:
		dir = r_server.config_get('dir').get('dir')
		dbfilename = r_server.config_get('dbfilename').get('dbfilename')
		if not dir or not dbfilename:
			return False
		import shutil
		if not dir.endswith('/'):
			dir += '/'
		shutil.copy(dir + dbfilename, copy_to)
	return result
