# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core::Converte
	~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.
	
	** Converter contains special converter for URL routing.

    :copyright: (c) 2013 by Lars Kiesow
    :license: FreeBSD and LGPL, see LICENSE for more details.
"""

from werkzeug.routing import BaseConverter, ValidationError
from core.util import username_regex_str, lang_regex_str
from uuid import UUID

class UUIDConverter(BaseConverter):

	def __init__(self, url_map):
		super(UUIDConverter, self).__init__(url_map)
		# UUID may be either 
		# 0d1a2dff-a062-4c39-a776-96034bc44ff0 or
		# 0d1a2dffa0624c39a77696034bc44ff0
		p = '[a-fA-F0-9]{%i}'
		self.regex = '(?:%s-%s-%s-%s-%s|%s)' % \
				( p%8, p%4, p%4, p%4, p%12, p%32 )


	def to_python(self, value):
		'''Convert UUID string or hex to UUID object'''
		try:
			return UUID(value)
		except:
			raise ValidationError()


	def to_url(self, value):
		'''Return string representation of UUID object'''
		return str(value)



class UsernameConverter(BaseConverter):

	def __init__(self, url_map):
		super(UsernameConverter, self).__init__(url_map)
		self.regex = username_regex_str



class LanguageConverter(BaseConverter):

	def __init__(self, url_map):
		super(LanguageConverter, self).__init__(url_map)
		self.regex = lang_regex_str
