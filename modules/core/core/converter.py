# -*- coding: utf-8 -*-
'''
	core.converter
	~~~~~~~~~~~~~~

	This module contains special converter for URL routing.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
'''

from werkzeug.routing import BaseConverter, ValidationError
from core.util import username_regex_str, lang_regex_str
from uuid import UUID

class UUIDConverter(BaseConverter):
	'''This converter accepts version 4 UUIDs. They can have either their normal
	form xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx or can be a hexadecimal string
	without the “-” character.

	Example::

		Rule('/object/<uuid:id>')

		>> http://.../object/0d1a2dff-a062-4c39-a776-96034bc44ff0

	:param url_map: the :class:`Map`.
	'''

	def __init__(self, url_map):
		super(UUIDConverter, self).__init__(url_map)
		# UUID may be either 
		# 0d1a2dff-a062-4c39-a776-96034bc44ff0 or
		# 0d1a2dffa0624c39a77696034bc44ff0
		p = '[a-fA-F0-9]{%i}'
		self.regex = '(?:%s-%s-%s-%s-%s|%s)' % \
				( p%8, p%4, p%4, p%4, p%12, p%32 )


	def to_python(self, value):
		'''Convert UUID string or hex to UUID object.
		
		:param value: The UUID as string
		'''
		try:
			return UUID(value)
		except:
			raise ValidationError()


	def to_url(self, value):
		'''Return string representation of UUID object.
		
		:param value: UUID to convert
		'''
		return str(value)



class UsernameConverter(BaseConverter):
	'''This converter accepts lernfunk usernames which are strings containing
	only alphanumerical characters and no whitespaces.

	Example::

		>> http://.../user/johndoe

	'''

	def __init__(self, url_map):
		super(UsernameConverter, self).__init__(url_map)
		self.regex = username_regex_str



class LanguageConverter(BaseConverter):
	'''This converter accepts IETF language tags. Tags are weakly validated,
	meaning that the form is checked (no special characters, ...) but not if
	there really is such a language tag.

	Example::

		>> http://.../lang/en-UK

	'''

	def __init__(self, url_map):
		super(LanguageConverter, self).__init__(url_map)
		self.regex = lang_regex_str
