# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core::Converte
	~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.
	
	** Converter contains special converter for URL routing.

    :copyright: (c) 2013 by Lars Kiesow
    :license: FreeBSD and LGPL, see LICENSE for more details.
"""

from werkzeug.routing import Rule, Map, BaseConverter, ValidationError
from core.util import username_regex_str, lang_regex_str

class UUIDConverter(BaseConverter):

	def __init__(self, url_map):
		super(UUIDConverter, self).__init__(url_map)
		p = '[a-fA-F0-9]{%i}'
		self.regex = '(?:%s-%s-%s-%s-%s)' % ( p%8, p%4, p%4, p%4, p%12 )



class UsernameConverter(BaseConverter):

	def __init__(self, url_map):
		super(UIntConverter, self).__init__(url_map)
		self.regex = username_regex_str



class LanguageConverter(BaseConverter):

	def __init__(self, url_map):
		super(UIntConverter, self).__init__(url_map)
		self.regex = lang_regex_str
