# -*- coding: utf-8 -*-
'''
	core.user
	~~~~~~~~~

	This module contains classes and methods to handle users.

	:copyright: (c) 2012 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
'''

from core.db    import get_db
from core.cache import get_mc
from hashlib    import sha512
from base64     import b64decode, b64encode

#******************************************************************************#
#**  Begin of user class definition                                          **#
#******************************************************************************#

class User:
	'''This class is intended for user data storage.
	
	:param id:            Identifier of the user
	:param name:          Username of the user
	:param groups:        List of groups the user is a member of
	:param vcard_uri:     URI of a vcard file containing more user information
	:param realname:      Real name of the user
	:param email:         Email address of the user
	:param access:        Access level of the private data
	:param password_hash: Hashed version of the users password

	Example::
		
		User( 1, 'jdoe', {1:'user'}, None, 'John Doe', 'john@example.com', ... )

	'''
	id=None
	'''Identifier of the user'''

	name=None
	'''Username of the user'''

	groups={}
	'''List of groups the user is a member of'''

	vcard_uri=None
	'''URI of a vcard file containing more user information'''

	realname=None
	'''Real name of the user'''

	email=None
	'''Email address of the user'''

	access=4
	'''Access level of the private data'''

	password_hash=None
	'''Hashed version of the users password'''


	def __init__(self, id=None, name=None, groups={}, vcard_uri=None, 
			realname=None, email=None, access=4, password_hash=''):
		'''Set initial values of user object.'''
		self.id            = id
		self.name          = name
		self.groups        = groups
		self.vcard_uri     = vcard_uri
		self.realname      = realname
		self.email         = email
		self.access        = access
		self.password_hash = password_hash


	def is_admin(self):
		'''Check if user has the status of an administrator.
		
		:returns: True if user is admin False otherwise
		'''
		return self.name == 'admin' or 'admin' in self.groups.values()


	def is_editor(self):
		'''Check if user has the status of an editor.
		
		:returns: True if user is editor False otherwise
		'''
		return self.is_admin() or 'editor' in self.groups.values()

	
	def password_hash_b64(self):
		'''Return the hased password (+salt) as base64 encoded string.
		
		:returns: Hashed password
		'''
		return b64encode( self.password_hash ) \
				if self.password_hash \
				else None

	def __str__(self):
		'''Return string, describing the user object (same as __repr__).'''
		return '(id=%s, name="%s", groups=%s, vcard_uri="%s", realname="%s", ' \
				'email="%s", access="%s", is_admin=%s, is_editor=%s, ' \
				'password_hash="%s")' \
				% ( self.id, self.name, self.groups, self.vcard_uri, self.realname,
						self.email, self.access, self.is_admin(), self.is_editor(), 
						self.password_hash_b64() )


	def __repr__(self):
		'''Return representation of user object.'''
		return self.__str__()

#******************************************************************************#
#**  End of user class definition                                            **#
#******************************************************************************#


def user_by_id(uid, time=600):
	'''Get the data of the user with the id `uid` from cache or database.

	:param uid: Id of the user.
	:param time: Time in seconds to cache the data (default: 10min).
	'''
	mc = get_mc()
	key = 'lf3_core_uid_' + str(int(uid))
	user = mc.get(key)
	if user is None:
		cursor = get_db().cursor()
		cursor.execute('''select id, name, salt, passwd, vcard_uri, realname, email, access
			from lf_user where id = %i ''' % int(uid) )
		try:
			id, name, salt, passwd, vcard_uri, realname, email, access = cursor.fetchone()
		except:
			return None
		user = User(id=id, name=name, password_hash=passwd, vcard_uri=vcard_uri,
				realname=realname, email=email, access=access)
		mc.set(key, user, time)
	return user


def user_by_username(uname, time=60):
	'''Get the data of the user with the name `username` from cache or database.

	:param uid: Username to search for.
	:param time: Time in seconds to cache the data (default: 1min).
	'''
	mc = get_mc()
	key = 'lf3_core_uname_' + uname
	user = mc.get(key)
	if user is None:
		cursor = get_db().cursor()
		cursor.execute('''select id, name, salt, passwd, vcard_uri, realname, email, access
			from lf_user where name = %s ''', uname )
		try:
			id, name, salt, passwd, vcard_uri, realname, email, access = cursor.fetchone()
		except:
			return None
		user = User(id=id, name=name, password_hash=passwd, vcard_uri=vcard_uri,
				realname=realname, email=email, access=access)
		mc.set(key, user, time)
	return user
