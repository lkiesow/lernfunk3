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
	for uid, name in s['lf:creator'].iteritems():
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
