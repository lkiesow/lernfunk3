# -*- coding: utf-8 -*-
"""
	feedgenerator.info
	~~~~~~~~~~~~~~~~~~

	Generate information pages about available feeds.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
from flask import render_template
from jinja2 import TemplateNotFound
import urllib2
import json

from feedgenerator import app
from feedgenerator.storage import *


def load_style():
	try:
		s = render_template('style.css')
	except TemplateNotFound:
		s = ''
	get_redis().set('%sstyle' % REDIS_NS, s)
	return s


def load_html():
	feeds = request_series()
	html = render_template('feeds.html', feeds=feeds, 
			title=app.config['FEED_HTML_TITLE'])
	get_redis().set('%shtml' % REDIS_NS, html)
	return html


def request_series():
	req  = urllib2.Request('%s://%s:%i%sview/series/?with_nothing=true' % (
		app.config['LERNFUNK_CORE_PROTOCOL'],
		app.config['LERNFUNK_CORE_HOST'],
		app.config['LERNFUNK_CORE_PORT'],
		app.config['LERNFUNK_CORE_PATH']))
	req.add_header('Accept', 'application/json')
	try:
		u = urllib2.urlopen(req)
		series = json.loads(u.read())
	finally:
		u.close()
	return [ (s['dc:identifier'], s['dc:title']) \
			for s in series['result'].get('lf:series') ]
