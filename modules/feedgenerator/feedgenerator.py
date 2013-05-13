# -*- coding: utf-8 -*-
"""
	feedgenerator
	~~~~~~~~~~~~~

	A microblog example application written as Flask tutorial with
	Flask and sqlite3.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
from flask import Flask, request, session, g, redirect, url_for, abort, \
		render_template, flash, _app_ctx_stack, Response
from jinja2 import TemplateNotFound
import config
import redis
import urllib2
import json
import os.path
import time
from feedgen.feed import FeedGenerator

# create our little application :)
app = Flask(__name__)

REDIS_NS = 'lf_feedgen_'

def get_redis():
	'''Opens a new database connection if there is none yet for the
	current application context.
	'''
	top = _app_ctx_stack.top
	if not hasattr(top, 'r_server'):
		top.r_server = redis.Redis(
				host	 = config._DATABASE_HOST,
				port	 = config._DATABASE_PORT,
				db	   = config._DATABASE_DB,
				password = config._DATABASE_PASSWD )

	return top.r_server


@app.route('/rss/<id>')
@app.route('/rss/<id>/<lang>')
def rss(id, lang=None):
	return build_feed(id, lang)


@app.route('/atom/<id>')
def atom(id):
	return ''


@app.route('/podcast/<id>')
def podcast(id):
	return ''


@app.route('/')
def feeds():
	return get_redis().get('%shtml' % REDIS_NS) \
			or load_html()


@app.route('/style.css')
def style():
	if app.debug:
		return Response( load_style(), mimetype='text/css')
	return get_redis().get('%sstyle' % REDIS_NS) \
			or load_style()


def load_style():
	try:
		s = render_template('style.css')
	except TemplateNotFound:
		s = ''
	get_redis().set('%sstyle' % REDIS_NS, s)
	return s


def request_series():
	req  = urllib2.Request('%s://%s:%i%sview/series/?with_nothing=true' % (
		config._LERNFUNK_CORE_PROTOCOL,
		config._LERNFUNK_CORE_HOST,
		config._LERNFUNK_CORE_PORT,
		config._LERNFUNK_CORE_PATH))
	req.add_header('Accept', 'application/json')
	try:
		u = urllib2.urlopen(req)
		series = json.loads(u.read())
	finally:
		u.close()
	print str(series)
	return [ (s['dc:identifier'], s['dc:title']) \
			for s in series['result'].get('lf:series') ]


def build_feed(id, lang):
	fg = FeedGenerator()
	fg.id(request.url)
	fg.link( href=request.url, rel='self' )
	req  = urllib2.Request('%s://%s:%i%sview/series/%s?with_name=true' % (
		config._LERNFUNK_CORE_PROTOCOL,
		config._LERNFUNK_CORE_HOST,
		config._LERNFUNK_CORE_PORT,
		config._LERNFUNK_CORE_PATH,
		id))
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		series = json.loads(u.read())
	finally:
		u.close()
	print str(series)
	fg.title(series['result']['lf:series'][0]['dc:title'])

	# Get media
	req  = urllib2.Request('%s://%s:%i%sview/series/%s/media/%s?with_file=true' % (
		config._LERNFUNK_CORE_PROTOCOL,
		config._LERNFUNK_CORE_HOST,
		config._LERNFUNK_CORE_PORT,
		config._LERNFUNK_CORE_PATH,
		id,
		lang or ''))
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()
	print str(media)
	return ''


def load_html():
	feeds = request_series()
	html = render_template('feeds.html', feeds=feeds, 
			title=config._FEED_HTML_TITLE)
	get_redis().set('%shtml' % REDIS_NS, html)
	return html


def init():
	r_server = redis.Redis(
			host	 = config._DATABASE_HOST,
			port	 = config._DATABASE_PORT,
			db	   = config._DATABASE_DB,
			password = config._DATABASE_PASSWD )
	r_server.delete('%shtml' % REDIS_NS)
	r_server.delete('%sstyle' % REDIS_NS)
	return ''

if __name__ == '__main__':
	app.run(debug=True, port=5001)
