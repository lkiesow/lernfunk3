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


def request_series(username=None, password=None):
	'''Request media with a given identifier from the lf core server.
	'''
	# Prepare request data
	url, auth = get_request_data(username, password)

	req  = urllib2.Request('%sview/series/?with_name=1' % url)
	# offset, limit
	if auth:
		req.add_header(*auth)
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()

	return media['result']['lf:series']


def prepare_series(dom, lf_series):
	'''Include elements from a given dataset (result from a lf:core webservice
	request) into a given XMP structure.
	'''
	res = dom.createElement('result')
	res.setAttribute('org', 'mh_default_org')
	res.setAttribute('id', lf_series['dc:identifier'])

	x = dom.createElement('mediaType')
	x.appendChild( dom.createTextNode('series') )
	res.appendChild(x)

	if lf_series.get('dc:date'):
		x = dom.createElement('dcDate')
		x.appendChild( dom.createTextNode(lf_series['dc:date']) )
		res.appendChild(x)
		x = dom.createElement('modified')
		x.appendChild( dom.createTextNode(lf_series['dc:date']) )
		res.appendChild(x)

	if lf_series.get('dc:description'):
		x = dom.createElement('dcDescription')
		x.appendChild( dom.createTextNode(lf_series['dc:description']) )
		res.appendChild(x)

	if lf_series.get('dc:language'):
		x = dom.createElement('dcLanguage')
		x.appendChild( dom.createTextNode(lf_series['dc:language']) )
		res.appendChild(x)

	if lf_series.get('dc:source'):
		x = dom.createElement('dcSource')
		x.appendChild( dom.createTextNode(lf_series['dc:source']) )
		res.appendChild(x)

	if lf_series.get('dc:title'):
		x = dom.createElement('dcTitle')
		x.appendChild( dom.createTextNode(lf_series['dc:title']) )
		res.appendChild(x)

	for subj in lf_series.get('dc:subject') or []:
		x = dom.createElement('dcSubject')
		x.appendChild( dom.createTextNode(subj) )
		res.appendChild(x)

	for creator in lf_series.get('lf:creator').values() or []:
		x = dom.createElement('dcCreator')
		x.appendChild( dom.createTextNode(creator) )
		res.appendChild(x)

	return res


def get_series():
	series = request_series('lkiesow','test')
	dom = parseString(
			'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
			+ '''<search-results 
				xmlns="http://search.opencastproject.org" 
				xmlns:ns2="http://mediapackage.opencastproject.org">''' \
			+ '</search-results>')

	searchResult = dom.childNodes[0]
	searchResult.setAttribute('total', str(len(series)))
	searchResult.setAttribute('limit', '0')
	searchResult.setAttribute('offset','0')
	searchResult.setAttribute('searchTime','1')

	q = dom.createElement('query')
	q.appendChild( dom.createTextNode('*:* AND oc_organization:mh_default_org AND (oc_acl_read:ROLE_ANONYMOUS) AND -oc_mediatype:AudioVisual AND -oc_deleted:[* TO *]') )
	searchResult.appendChild(q)
	for s in series or []:
		searchResult.appendChild( prepare_series(dom, s) )
	
	return searchResult.toxml()
		


def get_serach_result(type, id, user=None, password=None):
	'''Get/Generate an XMP structure for a specified object from the Lernfunk db.
	'''
	# Get necessary data
	lf_data = request_lf_data(type, id, user, password)
	xmp     = load_xmp(type, id)

	# Enrich XMP
	include_lf_dc(lf_data, xmp)

	# Generate string
	return xmp.serialize_to_str( 
		padding=0,
		omit_packet_wrapper=True,
		use_compact_format=True)


if __name__ == '__main__':
	print get_series()
	#print get_xmp('media', 'e8ad5959-9d26-11e2-a381-047d7b0f869a', 'lkiesow', 'test')
