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
	'''Try to load the css style sheet from the style.css template. The style
	will be stored in redis storage for further use.

	:returns: CSS stylesheet
	'''
	try:
		s = render_template('style.css')
	except TemplateNotFound:
		s = ''
	get_redis().set('%sstyle' % REDIS_NS, s)
	return s


def load_html():
	'''Load the HTML template from feeds.html and generate the HTML page which
	will be stored in the redis storage for further use.

	:returns: HTML page
	'''
	feeds = request_series()
	html  = render_template('feeds.html', feeds=feeds,
			title=app.config['FEED_HTML_TITLE'])
	get_redis().set('%shtml' % REDIS_NS, html)
	return html


def request_series():
	'''Request list of public available series from the lernfunk core
	webservice and return a list of tuples containing the identifier and title
	for each series.

	:returns: List of series

	Example::

		>>> request_series()
		[('7d13e687-da94-4847-87a1-186f1867a7d3','Series 1'),
				('23841592-98ba-4a96-9684-adf6aa844643','Series 2')]

	'''
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
