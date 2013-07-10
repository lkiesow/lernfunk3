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
#from xmp import app
from flask import Flask
app = Flask(__name__)
app.config.from_pyfile('config.py')


dc_elements = ['contributor', 'coverage', 'creator', 'date', 'description',
		'format', 'identifier', 'language', 'publisher', 'relation', 'rights',
		'source', 'subject', 'title', 'type']


def get_request_data(username=None, password=None):

	path = app.config['LERNFUNK_CORE_PATH'] \
			if app.config['LERNFUNK_CORE_PATH'].endswith('/') \
			else app.config['LERNFUNK_CORE_PATH'] + '/'
	url = '%s://%s:%i%s' % (
			app.config['LERNFUNK_CORE_PROTOCOL'],
			app.config['LERNFUNK_CORE_HOST'],
			app.config['LERNFUNK_CORE_PORT'],
			path )
	auth = ('Authorization', 'Basic ' + urlsafe_b64encode("%s:%s" % \
			( username, password ))) \
			if username and password \
			else None

	return url, auth


def request_media(username=None, password=None):
	'''Request media with a given identifier from the lf core server.
	'''
	# Prepare request data
	url, auth = get_request_data(username, password)

	req  = urllib2.Request('%sview/media/?with_name=1&with_file=1' % url)
	# offset, limit
	if auth:
		req.add_header(*auth)
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()

	return media['result']['lf:media']


def prepare_media(dom, lf_media):
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

	c = dom.createElement('m:creators')
	mp.appendChild(c)
	for creator in lf_media.get('lf:creator').values() or []:
		x = dom.createElement('dcCreator')
		x.appendChild( dom.createTextNode(creator) )
		res.appendChild(x)
		x = dom.createElement('m:creator')
		x.appendChild( dom.createTextNode(creator) )
		c.appendChild(x)

	c = dom.createElement('m:contributors')
	mp.appendChild(c)
	for contrib in lf_media.get('lf:contributor').values() or []:
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
		if f['dc:format'].startswith('video/'):
			t = dom.createElement('m:track')
			t.setAttribute('ref', 'track:track-%s' % f['dc:identifier'])
			t.setAttribute('id', f['dc:identifier'])
			# t.setAttribute('type', 'presenter/source')
			m.appendChild(t)

			if f.get('dc:format'):
				x = dom.createElement('m:mimetype')
				x.appendChild( dom.createTextNode(f['dc:format']) )
				t.appendChild(x)

			if f.get('lf:uri'):
				x = dom.createElement('m:url')
				x.appendChild( dom.createTextNode(f['lf:uri']) )
				t.appendChild(x)

          # <ns2:tags><ns2:tag>engage</ns2:tag></ns2:tags>
          # <ns2:duration>15750</ns2:duration>
		


	return res


def get_media():
	media = request_media('lkiesow','test')
	dom = parseString(
			'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
			+ '''<search-results 
				xmlns="http://search.opencastproject.org" 
				xmlns:m="http://mediapackage.opencastproject.org">''' \
			+ '</search-results>')

	searchResult = dom.childNodes[0]
	searchResult.setAttribute('total', str(len(media)))
	searchResult.setAttribute('limit', '0')
	searchResult.setAttribute('offset','0')
	searchResult.setAttribute('searchTime','1')

	q = dom.createElement('query')
	q.appendChild( dom.createTextNode('*:* AND oc_organization:mh_default_org AND (oc_acl_read:ROLE_ANONYMOUS) AND -oc_mediatype:AudioVisual AND -oc_deleted:[* TO *]') )
	searchResult.appendChild(q)
	for m in media or []:
		searchResult.appendChild( prepare_media(dom, m) )
	
	return searchResult.toxml()


if __name__ == '__main__':
	print get_media()
	#print get_xmp('media', 'e8ad5959-9d26-11e2-a381-047d7b0f869a', 'lkiesow', 'test')
