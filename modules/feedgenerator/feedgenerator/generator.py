# -*- coding: utf-8 -*-
"""
	feedgenerator.generator
	~~~~~~~~~~~~~~~~~~~~~~~


	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
import urllib2
import json
import time
from feedgen.feed import FeedGenerator

from feedgenerator import app
from feedgenerator.storage import *


def build_feed(id, lang, url, return_type=None):
	'''Request the data for a given id from the lernfunk core webservice and
	construct a feed for it which is stored in the redis database.

	:param id:          Series id to request.
	:param lang:        Language to request.
	:param url:         The request URL
	:param return_type: Type of feed to return.

	:returns: Feed of requested type.

	You have to pass the request URL since it cannot be retrieved automatically
	for asynchronous updates.
	'''
	feed = None
	try:
		feed = _build_feed(id, lang, url, return_type)
	except urllib2.HTTPError as e:
		# Clean up if we get a 404: Not Found
		if e.code == 404:
			r_server = get_redis()
			r_server.delete('%slast_update_%s' % (REDIS_NS, id))
			r_server.delete('%srss_%s'         % (REDIS_NS, id))
			r_server.delete('%satom_%s'        % (REDIS_NS, id))
			r_server.delete('%spodcast_%s'     % (REDIS_NS, id))
		raise
	return feed


###
# Build a feed without handling errors
##
def _build_feed(id, lang, url, return_type=None):
	fg = None
	fg = FeedGenerator()
	fg.id(url)
	fg.link( href=url, rel='self' )
	req  = urllib2.Request('%s://%s:%i%sview/series/%s?with_name=true' % (
		app.config['LERNFUNK_CORE_PROTOCOL'],
		app.config['LERNFUNK_CORE_HOST'],
		app.config['LERNFUNK_CORE_PORT'],
		app.config['LERNFUNK_CORE_PATH'],
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
	for name in s.get('lf:creator') or ['']:
		fg.author( name=name )

	# Get media
	req  = urllib2.Request('%s://%s:%i%sview/series/%s/media/%s%s' % (
		app.config['LERNFUNK_CORE_PROTOCOL'],
		app.config['LERNFUNK_CORE_HOST'],
		app.config['LERNFUNK_CORE_PORT'],
		app.config['LERNFUNK_CORE_PATH'],
		id,
		lang or '',
		'?with_file=1&with_name=1'))
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()

	# Add media to feed
	for media in media['result']['lf:media']:
		fe = fg.add_entry()
		fe.id('%s/%s/%s' % (url, media['dc:identifier'], media['lf:version']))
		fe.title(media['dc:title'])
		for name in media.get('lf:creator') or ['']:
			fe.author( name=name )
			fg.contributor( name=name )
		for name in media.get('lf:contributor') or []:
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
	r_server.set('%slast_update_%s_%s' % (REDIS_NS, id, lang), int(time.time()))
	r_server.set('%srss_%s_%s'     % (REDIS_NS, id, lang), rssfeed)
	r_server.set('%satom_%s_%s'    % (REDIS_NS, id, lang), atomfeed)
	r_server.set('%spodcast_%s_%s' % (REDIS_NS, id, lang), podcast)

	if return_type == 'rss':
		return rssfeed
	if return_type == 'atom':
		return atomfeed
	if return_type == 'podcast':
		return podcast
