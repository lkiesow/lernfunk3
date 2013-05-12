# -*- coding: utf-8 -*-
"""
	core
	~~~~

	This module provides read and write access to the central Lernfunk database.

	:copyright: (c) 2012 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
"""

from flask import Flask

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# create our little application :)
app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# Import custom converter
import core.converter
app.url_map.converters['uuid'] = core.converter.UUIDConverter
app.url_map.converters['lang'] = core.converter.LanguageConverter
app.url_map.converters['user'] = core.converter.UsernameConverter

# set the secret key.
# You should really keep this secret:
app.secret_key = '\xbe\xfd\xef\x99\x9bl.:4\xb1\xc0!\xe7:D \x9en\x88tu\xd0\xde\xaa'

# import submodules
import core.admin.delete
import core.admin.get
import core.admin.post
import core.admin.put
import core.cache
import core.db
import core.login
import core.user
import core.view
