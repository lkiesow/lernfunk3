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
from threading import Thread

# create our little application :)
app = Flask(__name__)

REDIS_NS = 'lf_feedgen_'

def get_redis():
	'''Opens a new database connection if there is none yet for the
	current application context.
	'''
	top = _app_ctx_stack.top
	if not hasattr(top, 'r_server'):
		r_server = redis.Redis(
				host	 = config._DATABASE_HOST,
				port	 = config._DATABASE_PORT,
				db	   = config._DATABASE_DB,
				password = config._DATABASE_PASSWD )
		if not top is None:
			top.r_server = r_server
		return r_server

	return top.r_server


def timestr_to_secs(timestr):
	timeparts = timestr.split(':')
	if len(timeparts) > 3:
		raise ValueError('Invalid time string "%s"' % timestr)
	timeparts = [ int(x) for x in timeparts ]
	timeparts.reverse()
	timeparts += [0,0,0] # make sure we have three elements
	seconds = timeparts[0] + 60*timeparts[1] + 3600*timeparts[2]
	return seconds


def db_flushall():
	r_server = get_redis()
	keys = r_server.keys('%s*' % REDIS_NS)
	return r_server.delete(*keys)


def db_save(copy_to=None):
	'''Tell the Redis server to save its data to disk, blocking until the save
	is complete. The data will be written to the directory defined in the redis
	configuration file. If copy_to is set the file will be copied to the
	specified location.

	:param copy_to: Copy the database dump to this location.
	'''
	r_server = get_redis()
	result = r_server.save()
	if result and copy_to:
		dir = r_server.config_get('dir').get('dir')
		dbfilename = r_server.config_get('dbfilename').get('dbfilename')
		if not dir or not dbfilename:
			return False
		import shutil
		if not dir.endswith('/'):
			dir += '/'
		shutil.copy(dir + dbfilename, copy_to)
	return result


@app.route('/<any(rss, atom, podcast):feedtype>/<id>')
@app.route('/<any(rss, atom, podcast):feedtype>/<id>/<lang>')
def feed(feedtype, id, lang=None):

	UPDATE_NONE  = 0
	UPDATE_ASYNC = 1
	UPDATE_SYNC  = 2

	update = UPDATE_NONE

	last_update = get_redis().get('%slast_update_%s' % (REDIS_NS, id))
	if last_update is None:
		update = UPDATE_SYNC
	elif int(time.time()) - int(last_update) > \
			timestr_to_secs(config._FEED_UPDATE_TIME_SYNC):
		update = UPDATE_SYNC
	elif int(time.time()) - int(last_update) > \
			timestr_to_secs(config._FEED_UPDATE_TIME):
		update = UPDATE_ASYNC

	feed = None
	if update != UPDATE_SYNC:
		feed = get_redis().get('%s%s_%s' % (REDIS_NS, feedtype, id))
	if not feed:
		update = UPDATE_SYNC
	
	if update == UPDATE_ASYNC:
		Thread(target=build_feed, args=(id, lang, request.url)).start()
	elif update == UPDATE_SYNC:
		feed = build_feed(id, lang, request.url, feedtype)
	return Response(feed, mimetype=('application/atom+xml' if feedtype == 'atom' \
			else 'application/rss+xml'))


@app.route('/')
def html():
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


def build_feed(id, lang, url, return_type=None):
	fg = None
	fg = FeedGenerator()
	fg.id(url)
	fg.link( href=url, rel='self' )
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
	s = series['result']['lf:series'][0]
	fg.title(s['dc:title'])
	fg.language(s['dc:language'])
	for cat in s['dc:subject']:
		fg.category( term=cat.lower(), label=cat )
	fg.description(s['dc:description'] or s['dc:title'])
	for uid, name in s['lf:creator'].iteritems():
		fg.author( name=name )

	# Get media
	req  = urllib2.Request('%s://%s:%i%sview/series/%s/media/%s%s' % (
		config._LERNFUNK_CORE_PROTOCOL,
		config._LERNFUNK_CORE_HOST,
		config._LERNFUNK_CORE_PORT,
		config._LERNFUNK_CORE_PATH,
		id,
		lang or '',
		'?with_file=1&with_name=1'))
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()
	print str(media)

	# Add media to feed
	for media in media['result']['lf:media']:
		fe = fg.add_entry()
		print media
		fe.id('%s/%s/%s' % (url, media['dc:identifier'], media['lf:version']))
		fe.title(media['dc:title'])
		for uid, name in media['lf:creator'].iteritems():
			fe.author( name=name )
			fg.contributor( name=name )
		for uid, name in media['lf:contributor'].iteritems():
			fe.contributor( name=name )
			fg.contributor( name=name )
		fe.content(media['dc:description'])
		is_av = lambda x: x.startswith('video') or x.startswith('audio')
		for file in media['lf:file']:
			fe.link( 
					href=file['lf:uri'], 
					rel=( 'enclosure' if is_av(file['dc:format']) else 'alternate' ),
					type=file['dc:format'] )
		fe.published(media['dc:date'] + ' +0')

	rssfeed  = fg.rss_str(pretty=False)
	atomfeed = fg.atom_str(pretty=False)

	# Podcast specific values
	fg.load_extension('podcast')

	podcast = fg.rss_str(pretty=False)

	r_server = get_redis()
	r_server.set('%slast_update_%s' % (REDIS_NS, id), int(time.time()))
	r_server.set('%srss_%s'     % (REDIS_NS, id), rssfeed)
	r_server.set('%satom_%s'    % (REDIS_NS, id), atomfeed)
	r_server.set('%spodcast_%s' % (REDIS_NS, id), podcast)

	if return_type == 'rss':
		return rssfeed
	if return_type == 'atom':
		return atomfeed
	if return_type == 'podcast':
		return podcast


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
