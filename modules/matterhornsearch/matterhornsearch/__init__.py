# -*- coding: utf-8 -*-
"""
	matterhornsearch
	~~~~~~~~~~~~~~~~

	This module will act like a Opencast Matterhorn Search Service only that it
	actually gets the data from Lernfunk instead.

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

# import submodules
import matterhornsearch.rest

# Write error log to file
if not app.debug:
	import logging
	from logging.handlers import RotatingFileHandler
	file_handler = RotatingFileHandler(app.config['LOGFILE'], 
			'a', 10 * 1024 * 1024, 10)
	file_handler.setFormatter(logging.Formatter(
		'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
	app.logger.setLevel(logging.INFO)
	file_handler.setLevel(logging.INFO)
	app.logger.addHandler(file_handler)
