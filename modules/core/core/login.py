# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core::Login
	~~~~~~~~~~~~~~~~~~~~~~

	Login contains the login and logout mechanism for session based logins.

    :copyright: (c) 2012 by Lars Kiesow

    :license: FreeBSD and LGPL, see LICENSE for more details.
"""

from core import app
from core.authenticate import get_authorization
from werkzeug.datastructures import Authorization
from flask import session, redirect, url_for, request


@app.route('/login', methods=['GET', 'POST'])
def login():
	'''This method can be used to log into the lernfunk core webservice. Using
	this mechanism you will get a session id to use for further authentication.

	Authentication can be done either by using HTTP Basic authentication or by
	form based authentication using the fields *username* and *password*.

	As request type both GET and POST are accepted.

	Example::
		
		curl -u user:passwd 'http://example.com/login'
		curl --data username=john&password=secret 'http://example.com/login'

	'''

	auth = None
	if request.method == 'POST':
		auth = Authorization('basic', {
			'username' : request.form['username'],
			'password' : request.form['password'] } )
	else:
		auth = request.authorization
	try:
		user = get_authorization( auth )
	except KeyError as e:
		return e.message, 401
		
	if user.name == 'public':
		return 'Incorrect user or password.', 401

	session['username']   = user.name
	session['password'] = user.password_hash_b64()
	return '', 204


@app.route('/logout')
def logout():
	'''Remove username and hashec password from session if it's there.
	'''
	session.pop('username', None)
	session.pop('password', None)
	return '', 204
