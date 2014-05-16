# -*- coding: utf-8 -*-
"""
	feedgenerator.rest
	~~~~~~~~~~~~~~~~~~

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
from flask import Flask, request, Response
import redis
import time
from threading import Thread

from feedgenerator           import app
from feedgenerator.generator import *
from feedgenerator.storage   import *
from feedgenerator.info      import *


@app.route('/<any(rss, atom, podcast):feedtype>/<id>')
@app.route('/<any(rss, atom, podcast):feedtype>/<id>/<lang>')
def feed(feedtype, id, lang=None):
	'''Return a feed for a given series (id).
	
	:param feedtype: Type of feed to return. Supported types are rss, atom and
		podcast.
	:param lang: Language filter for the request.
	'''

	UPDATE_NONE  = 0
	UPDATE_ASYNC = 1
	UPDATE_SYNC  = 2

	update = UPDATE_NONE

	last_update = get_redis().get('%slast_update_%s_%s' % (REDIS_NS, id, lang))
	if last_update is None:
		update = UPDATE_SYNC
	elif int(time.time()) - int(last_update) > \
			timestr_to_secs(app.config['FEED_UPDATE_TIME_SYNC']):
		update = UPDATE_SYNC
	elif int(time.time()) - int(last_update) > \
			timestr_to_secs(app.config['FEED_UPDATE_TIME']):
		update = UPDATE_ASYNC

	feed = None
	if update != UPDATE_SYNC:
		feed = get_redis().get('%s%s_%s_%s' % (REDIS_NS, feedtype, id, lang))
	if not feed:
		update = UPDATE_SYNC
	
	if update == UPDATE_ASYNC:
		Thread(target=build_feed, args=(id, lang, request.url)).start()
	elif update == UPDATE_SYNC:
		try:
			feed = build_feed(id, lang, request.url, feedtype)
		except urllib2.HTTPError as e:
			if e.code == 404:
				return 'Series with id="%s" does not exist.' % id, 404
			else:
				raise
	return Response(feed, mimetype=('application/atom+xml' if feedtype == 'atom' \
			else 'application/rss+xml'))


@app.route('/')
def html():
	'''Display information page listing all available feeds.
	'''
	last_update = int(time.time()) \
			- int(get_redis().get('%slast_update_html' % REDIS_NS) or 0)

	# Synchronous update:
	if last_update > timestr_to_secs(app.config['INFO_UPDATE_TIME_SYNC']):
		return load_html()
	# Asynchronous update:
	elif last_update > timestr_to_secs(app.config['INFO_UPDATE_TIME']):
		Thread(target=load_html).start()
	# No update:
	return get_redis().get('%shtml' % REDIS_NS) \
			or load_html()


@app.route('/style.css')
def style():
	'''Return CSS stylesheet for information page'''
	return Response(
			get_redis().get('%sstyle' % REDIS_NS) or load_style(),
			mimetype='text/css' )


def timestr_to_secs(timestr):
	timeparts = timestr.split(':')
	if len(timeparts) > 3:
		raise ValueError('Invalid time string "%s"' % timestr)
	timeparts = [ int(x) for x in timeparts ]
	timeparts.reverse()
	timeparts += [0,0,0] # make sure we have three elements
	seconds = timeparts[0] + 60*timeparts[1] + 3600*timeparts[2]
	return seconds
