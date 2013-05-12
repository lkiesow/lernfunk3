# -*- coding: utf-8 -*-
'''
	corer.authenticate
	~~~~~~~~~~~~~~~~~~

	Authenticate contains methods for authentication and authorization handling
	as well as user handling.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
'''

from flask     import session
from core.db   import get_db
from core.user import User
from hashlib   import sha512
from core.util import username_chars


def get_authorization( auth ):
	'''Check request for valid authentication data. The data can be either a
	session previuosly started with /login or authentication data. provided for
	example by a HTTP Basic authentication.

	:param auth: The authentication data in case session based authentication is
					 *not* used. Even if a session exist, this data has higher
					 priority than the session data.

	:returns: If successfull a valid User object is returned.
	'''
	username = None
	password = None

	if not auth:
		# We got no login data.
		# Assign the name »public« to the user which will also put hin into the
		# »public« group
		if 'username' in session and 'password' in session:
			username = session['username']
			password = session['password']
			print([ username, password ])
		else:
			username = 'public'
	else:
		username = auth.username
		password = auth.password
		
	# Check if the username might be valid as protection 
	# against SQL injection
	for c in username:
		if not c in username_chars:
			raise KeyError( 'Bad username in header.' )

	query = '''select id, salt, passwd, vcard_uri, realname, email, access
			from lf_user where name = "%s"''' % username

	# Get userdata from database
	db = get_db()
	cur = db.cursor()
	cur.execute( query )
	dbdata = cur.fetchone()

	if not dbdata:
		# User does not exist. Return error
		raise KeyError( 'User does not exist.' )

	id, salt, passwd, vcard_uri, realname, email, access = dbdata
	send_passwdhash = ( sha512( password + str(salt) ).digest() \
			if auth else b64decode(password) ) \
			if passwd else None
	
	if passwd != send_passwdhash:
		# Password is invalid. Return error
		raise KeyError( 'Invalid password.' )

	# At this point we are shure that we got a valid user with a valid password.
	# So lets get the userdata.
	# First set, what we already know:
	user = User( id=id, name=username, vcard_uri=vcard_uri, groups={}, 
			realname=realname, email=email, access=access, password_hash=passwd )
	
	# Then get additional data:
	query = '''select g.id, g.name from lf_user_group ug 
			left outer join lf_group g on ug.group_id = g.id 
			where ug.user_id = %s ''' % id
	cur.execute(query)
	for id, name in cur.fetchall():
		user.groups[id] = name

	# Return user information
	return user
