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

from hashlib   import sha512
from core.db   import get_db
from core.util import username_chars


class User:
	'''This class is intended for user data storage'''
	id=None
	name=None
	groups={}
	vcard_uri=None
	admin=False
	editor=False

	def __init__(self, id=None, name=None, groups={}, vcard_uri=None, 
			admin=False, editor=False):
		self.id        = id
		self.name      = name
		self.groups    = groups
		self.vcard_uri = vcard_uri
		self.admin     = admin
		self.editor    = editor

	def __str__(self):
		return '(id=%s, name="%s", groups=%s, vcard_uri="%s")' \
				% ( self.id, self.name, self.groups, self.vcard_uri )

	def __repr__(self):
		return self.__str__()



def get_authorization( auth ):
	'''Return an empty DOM tree for results
	'''
	username = None
	Password = None

	if not auth:
		# We got no login data.
		# Assign the name »public« to the user which will also put hin into the
		# »public« group
		username = 'public'
	else:
		username = auth.username
		password = auth.password
		
	# Check if the username might be valid as protection 
	# against SQL injection
	for c in username:
		if not c in username_chars:
			raise KeyError( 'Bad username in header.' )

	query = '''select id, salt, passwd, vcard_uri 
			from lf_user where name = "%s"''' % username

	# Get userdata from database
	db = get_db()
	cur = db.cursor()
	cur.execute( query )
	dbdata = cur.fetchone()

	if not dbdata:
		# User does not exist. Return error
		raise KeyError( 'User does not exist.' )

	id, salt, passwd, vcard_uri = dbdata
	send_passwdhash = sha512( password + str(salt) ).digest() \
			if passwd else None
	
	if passwd != send_passwdhash:
		# Password is invalid. Return error
		raise KeyError( 'Invalid password.' )

	# At this point we are shure that we got a valid user with a valid password.
	# So lets get the userdata.
	# First set, what we already know:
	user = User( id=id, name=username, vcard_uri=vcard_uri )
	
	# Then get additional data:
	query = '''select g.id, g.name from lf_user_group ug 
			left outer join lf_group g on ug.group_id = g.id 
			where ug.user_id = %s ''' % id
	cur.execute(query)
	for id, name in cur.fetchall():
		user.groups[id] = name

	# Return user information
	return user
