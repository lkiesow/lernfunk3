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


def request_series(username=None, password=None, id=None, limit=None,
		offset=None, q=None, cookie=None):
	'''Request series from the lf core server.

	:param id:       The id to search for.
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
	if id:
		url = '%sview/series/%s/?with_name=1' % (url,id)
	else:
		url = '%sview/series/?with_name=1' % url
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
		series = json.loads(u.read())
	finally:
		u.close()

	return series['result']['lf:series'], series['resultcount']



def prepare_series_xml(dom, lf_series):
	'''This method will build an XML structure matching a Opencast Matterhorn
	search result from a given set of series data returned from the Lernfunk
	core service.

	:param dom:      The DOM tree the elements should be appended to.
	:param lf_media: The series data to build the result from.
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

	for creator in lf_series.get('lf:creator') or []:
		x = dom.createElement('dcCreator')
		x.appendChild( dom.createTextNode(creator) )
		res.appendChild(x)

	for contributor in lf_series.get('lf:contributor') or []:
		x = dom.createElement('dcContributor')
		x.appendChild( dom.createTextNode(contributor) )
		res.appendChild(x)

	return res
