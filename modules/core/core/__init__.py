# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core
	~~~~~~~~~~~~~~~

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

# set the secret key.  keep this really secret:
app.secret_key = '\xbe\xfd\xef\x99\x9bl.:4\xb1\xc0!\xe7:D \x9en\x88tu\xd0\xde\xaa'

# import submodules
import core.view
import core.db
import core.login
import core.admin.get
