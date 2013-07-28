# -*- coding: utf-8 -*-
"""
	xmp.get_data
	~~~~~~~~~~~~


	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import urllib2
import json
import os.path
from base64 import urlsafe_b64encode
from xml.dom.minidom import parseString

from matterhornsearch import app
from matterhornsearch.util import get_request_data


def request_media(username=None, password=None, id=None, sid=None,
		limit=None, offset=None, q=None, cookie=None):
	'''Request media from the lf core server.

	:param id:       The id to search for.
	:param sid:      The id of the series the episode should belong to.
	:param q:        A Lernfunk search query.
	:param limit:    The maximum amount of objects to return.
	:param offset:   The offset for the first of the returned objects.
	:param username: The username used for authetication with the core service.
	:param password: The password used for authetication with the core service.
	:param cookie:   Cookie used for authentication.
	'''
	# Prepare request data
	url, auth = get_request_data(username, password)

	# Build search query
	if sid:
		url = '%sview/series/%s/media/' % (url,sid)
	else:
		url = '%sview/media/' % url
	if id:
		url = '%s%s/?with_name=1&with_file=1' % (url,id)
	else:
		url = '%s?with_name=1&with_file=1&with_series=1' % url
	if limit:
		url += '&limit=%i' % limit
	if offset:
		url += '&offset=%i' % offset
	if q:
		url += '&q=%s' % q

	req  = urllib2.Request(url)
	# offset, limit
	if auth:
		req.add_header(*auth)
	elif cookie:
		req.add_header('cookie', 'session="%s"; Path=/; HttpOnly' % cookie)
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()

	return media['result']['lf:media'], media['resultcount']


def prepare_media_xml(dom, lf_media):
	'''This method will build an XML structure matching a Opencast Matterhorn
	search result from a given set of media data returned from the Lernfunk core
	service.

	:param dom:      The DOM tree the elements should be appended to.
	:param lf_media: The media data to build the result from.
	'''
	res = dom.createElement('result')
	res.setAttribute('org', 'mh_default_org')
	res.setAttribute('id', lf_media['dc:identifier'])

	x = dom.createElement('mediaType')
	x.appendChild( dom.createTextNode('AudioVisual') )
	res.appendChild(x)

	mp = dom.createElement('m:mediapackage')
	res.appendChild(mp)
	mp.setAttribute('id', lf_media['dc:identifier'])

	x = dom.createElement('mediaType')
	x.appendChild( dom.createTextNode('AudioVisual') )
	res.appendChild(x)

	if lf_media.get('dc:date'):
		x = dom.createElement('dcCreated')
		x.appendChild( dom.createTextNode(lf_media['dc:date']) )
		res.appendChild(x)
		mp.setAttribute('start', lf_media['dc:date'])
	
	if lf_media.get('lf:last_edit'):
		x = dom.createElement('modified')
		x.appendChild( dom.createTextNode(lf_media['lf:last_edit']) )
		res.appendChild(x)

	if lf_media.get('dc:description'):
		x = dom.createElement('dcDescription')
		x.appendChild( dom.createTextNode(lf_media['dc:description']) )
		res.appendChild(x)

	if lf_media.get('dc:language'):
		x = dom.createElement('dcLanguage')
		x.appendChild( dom.createTextNode(lf_media['dc:language']) )
		res.appendChild(x)

	if lf_media.get('dc:source'):
		x = dom.createElement('dcSource')
		x.appendChild( dom.createTextNode(lf_media['dc:source']) )
		res.appendChild(x)

	if lf_media.get('dc:title'):
		x = dom.createElement('dcTitle')
		x.appendChild( dom.createTextNode(lf_media['dc:title']) )
		res.appendChild(x)
		x = dom.createElement('m:title')
		x.appendChild( dom.createTextNode(lf_media['dc:title']) )
		mp.appendChild(x)

	for subj in lf_media.get('dc:subject') or []:
		x = dom.createElement('dcSubject')
		x.appendChild( dom.createTextNode(subj) )
		res.appendChild(x)
	
	for series in lf_media.get('lf:series_id') or []:
		x = dom.createElement('dcIsPartOf')
		x.appendChild( dom.createTextNode(series) )
		res.appendChild(x)

	c = dom.createElement('m:creators')
	mp.appendChild(c)
	for creator in lf_media.get('lf:creator') or []:
		x = dom.createElement('dcCreator')
		x.appendChild( dom.createTextNode(creator) )
		res.appendChild(x)
		x = dom.createElement('m:creator')
		x.appendChild( dom.createTextNode(creator) )
		c.appendChild(x)

	c = dom.createElement('m:contributors')
	mp.appendChild(c)
	for contrib in lf_media.get('lf:contributor') or []:
		x = dom.createElement('dcContributor')
		x.appendChild( dom.createTextNode(contrib) )
		res.appendChild(x)
		x = dom.createElement('m:contributor')
		x.appendChild( dom.createTextNode(contrib) )
		c.appendChild(x)

	
	# Add media:
	# - format video/* and audio/* will become media elements
	# - format image/* will become attachment
	m = dom.createElement('m:media')
	a = dom.createElement('m:attachments')
	mp.appendChild(m)
	mp.appendChild(a)
	for f in lf_media.get('lf:file') or []:
		if not f.get('dc:format'):
			continue

		# Handle videos
		if f['dc:format'].startswith('video/'):
			t = dom.createElement('m:track')
			t.setAttribute('ref', 'track:track-%s' % f['dc:identifier'])
			t.setAttribute('id', f['dc:identifier'])
			t.setAttribute('type', f['lf:flavor'])
			m.appendChild(t)

			if f.get('dc:format'):
				x = dom.createElement('m:mimetype')
				x.appendChild( dom.createTextNode(f['dc:format']) )
				t.appendChild(x)

			if f.get('lf:uri'):
				x = dom.createElement('m:url')
				x.appendChild( dom.createTextNode(f['lf:uri']) )
				t.appendChild(x)

			if f.get('lf:tags'):
				x = dom.createElement('m:tags')
				for tag in f['lf:tags']:
					y = dom.createElement('m:tag')
					y.appendChild( dom.createTextNode(tag) )
					x.appendChild(y)
				t.appendChild(x)

			# Handle images
		elif f['dc:format'].startswith('image/'):
			t = dom.createElement('m:attachment')
			t.setAttribute('ref', 'track:track-%s' % f['dc:identifier'])
			t.setAttribute('id', f['dc:identifier'])
			t.setAttribute('type', f['lf:flavor'])
			a.appendChild(t)

			if f.get('dc:format'):
				x = dom.createElement('m:mimetype')
				x.appendChild( dom.createTextNode(f['dc:format']) )
				t.appendChild(x)

			if f.get('lf:uri'):
				x = dom.createElement('m:url')
				x.appendChild( dom.createTextNode(f['lf:uri']) )
				t.appendChild(x)

			if f.get('lf:tags'):
				x = dom.createElement('m:tags')
				t.appendChild(x)
				for tag in f['lf:tags']:
					y = dom.createElement('m:tag')
					y.appendChild( dom.createTextNode(tag) )
					t.appendChild(y)

          # <ns2:duration>15750</ns2:duration>

	return res
