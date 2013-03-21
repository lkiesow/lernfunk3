# -*- coding: utf-8 -*-
'''
	Lernfunk3::Core::db
	~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.
	
	** Db contains database handline

    :copyright: (c) 2012 by Lars Kiesow
    :license: FreeBSD and LGPL, see LICENSE for more details.
'''

from core import app
import MySQLdb
from flask import _app_ctx_stack, abort


def get_db():
	'''Returns a database connection. If there is none open for the current
	application context it will create a new connection.
	'''
	top = _app_ctx_stack.top
	if not hasattr(top, 'mysql_db'):
		try:
			top.mysql_db = MySQLdb.connect(
				host    = app.config['DATABASE_HOST'],
				user    = app.config['DATABASE_USER'],
				passwd  = app.config['DATABASE_PASSWD'],
				db      = app.config['DATABASE_NAME'],
				port    = int(app.config['DATABASE_PORT']),
				charset = 'utf8' )
		except MySQLdb.OperationalError as e:
			abort(500, str(e))
	return top.mysql_db


@app.teardown_appcontext
def close_db_connection(exception):
	'''Closes the database again at the end of the request.
	'''
	top = _app_ctx_stack.top
	if hasattr(top, 'mysql_db'):
		top.mysql_db.close()
