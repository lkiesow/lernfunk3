# -*- coding: utf-8 -*-
"""
	feedgenerator.rest
	~~~~~~~~~~~~~~~~~~

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
from flask import Flask, request, Response
import urllib2
from base64 import urlsafe_b64encode
from xml.dom.minidom import parseString
import re

from matterhornsearch import app
from matterhornsearch.util import is_true, to_int, get_request_data
from matterhornsearch.series import request_series, prepare_series_xml
from matterhornsearch.media import request_media, prepare_media_xml


@app.route('/search/series.<any(xml, json):format>')
def series(format):
	'''Search for series matching the query parameters.
	
	:param format: The output format (json or xml) of the response body.

	GET parameter:

		==============  ===========================================  ========
		Parameter       Description                                  Default
		==============  ===========================================  ========
		id              Specify an object by its id                         
		q               Free-text search query                              
		series          Include series information in the results    true
		episode         Include episode information n the results    false
		limit           Maximum amount of results to return          10
		offset          Offset of results to return                  0
		==============  ===========================================  ========
	'''

	if format == 'json':
		return 'JSON not yet implemented.', 501

	# TODO: Replicate Spring Form auth
	user, passwd = None, None
	if request.authorization:
		user   = request.authorization.username
		passwd = request.authorization.password

	cookie = request.cookies.get('JSESSIONID')

	# Get request arguments:
	id      = request.args.get('id')
	q       = request.args.get('q')
	series  = is_true(request.args.get('series', True))
	episode = is_true(request.args.get('episode', False))
	limit   = to_int(request.args.get('limit',  '10'), 10)
	offset  = to_int(request.args.get('offset',  '0'),  0)
	
	if q:
		q = 'in:description:base64:%(q)s;in:title:base64:%(q)s' % \
				{ 'q' : urlsafe_b64encode(q) }

	try:
		result = search_xml(series, episode, id, None, q, limit, offset, user,
				passwd, cookie)
	except urllib2.HTTPError as e:
		if e.code == 404:
			app.logger.warn('Request to /%s/%s: 404 NOT FOUND' % (type, id))
			return 'Resource not found', 404
		if e.code == 401:
			app.logger.warn('Request to /%s/%s: 401 UNAUTHORIZED' % (type, id))
			return 'Unauthorized access (wrong credentials?)', 401
		raise e
	app.logger.info('Request to %s: OK' % request.path)

	return Response(result, mimetype='application/xml')


@app.route('/search/episode.<any(xml, json):format>')
def media(format):
	'''Search for episodes (media) matching the query parameters.
	
	:param format: The output format (json or xml) of the response body.

	GET parameter:

		==============  ===========================================  ========
		Parameter       Description                                  Default
		==============  ===========================================  ========
		id              Specify an object by its id                  enabled
		q               Free-text search query                       enabled
		sid             Only return the publishers                   enabled
		limit           Maximum amount of results to return          10
		offset          Offset of results to return                  0
		==============  ===========================================  ========
	'''

	if format == 'json':
		return 'JSON not yet implemented.', 501

	# TODO: Replicate Spring Form auth
	user, passwd = None, None
	if request.authorization:
		user   = request.authorization.username
		passwd = request.authorization.password

	cookie = request.cookies.get('JSESSIONID')

	# Get request arguments:
	id      = request.args.get('id')
	sid     = request.args.get('sid')
	q       = request.args.get('q')
	limit   = to_int(request.args.get('limit',  '10'), 10)
	offset  = to_int(request.args.get('offset',  '0'),  0)
	
	if q:
		q = 'in:description:base64:%(q)s;in:title:base64:%(q)s' % \
				{ 'q' : urlsafe_b64encode(q) }

	try:
		result = search_xml(False,True,id,sid,q,limit,offset,user,passwd,cookie)
	except urllib2.HTTPError as e:
		if e.code == 404:
			app.logger.warn('Request to /%s/%s: 404 NOT FOUND' % (type, id))
			return 'Resource not found', 404
		if e.code == 401:
			app.logger.warn('Request to /%s/%s: 401 UNAUTHORIZED' % (type, id))
			return 'Unauthorized access (wrong credentials?)', 401
		raise e
	app.logger.info('Request to %s: OK' % request.path)

	return Response(result, mimetype='application/xml')


def search_xml(series, episode, id, sid, q, limit, offset, user, passwd, cookie):
	'''Handle search requests with all kinds of filtering. The return value is
	an XML string representing a Opencast Matterhorn search result.

	:param series:  Indicates if series are requested.
	:param episode: Indicates if episodes are requested.
	:param id:      The id to search for.
	:param sid:     The id of the series the episode should belong to.
	:param q:       A Lernfunk search query.
	:param limit:   The maximum amount of objects to return.
	:param offset:  The offset for the first of the returned objects.
	:param user:    The username used for authetication with the core service.
	:param passwd:  The password used for authetication with the core service.
	:param cookie:  Cookie used for authentication.
	'''

	dom = parseString(
			'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
			+ '''<search-results 
				xmlns="http://search.opencastproject.org" 
				xmlns:m="http://mediapackage.opencastproject.org">''' \
			+ '</search-results>')

	series_data   = []
	episode_data  = []
	series_count  = 0
	episode_count = 0
	if series:
		series_data, series_count = request_series(username=user,
				password=passwd, id=id,limit=limit, offset=offset, q=q,
				cookie=cookie)
	if episode:
		episode_data, episode_count = request_media(username=user,
				password=passwd, id=id, sid=sid, limit=limit, offset=offset, q=q,
				cookie=cookie)

	searchResult = dom.childNodes[0]
	searchResult.setAttribute('total', str(series_count + episode_count))
	searchResult.setAttribute('limit', str(limit))
	searchResult.setAttribute('offset',str(offset))
	searchResult.setAttribute('searchTime','0')

	q = dom.createElement('query')
	q.appendChild( dom.createTextNode('*:* AND oc_organization:mh_default_org AND (oc_acl_read:ROLE_ANONYMOUS) AND -oc_mediatype:AudioVisual') )
	searchResult.appendChild(q)
	for s in series_data or []:
		searchResult.appendChild( prepare_series_xml(dom, s) )
	for e in episode_data or []:
		searchResult.appendChild( prepare_media_xml(dom, e) )
	
	return searchResult.toxml()


@app.route('/j_spring_security_check', methods=['POST'])
def j_spring_security_check():

	#j_username = request.args.get('j_username')
	#j_password = request.args.get('j_password')
	j_username = request.form.get('j_username')
	j_password = request.form.get('j_password')

	try:
		url, auth = get_request_data(j_username, j_password)
		url = '%slogin' % url
		req  = urllib2.Request(url)
		if auth:
			req.add_header(*auth)
		u = urllib2.urlopen(req)
		cookie = u.headers.get('Set-Cookie')
		u.close()
	except urllib2.HTTPError as e:
		if e.code == 404:
			app.logger.warn('Request to /%s/%s: 404 NOT FOUND' % (type, id))
			return 'Resource not found', 404
		if e.code == 401:
			app.logger.warn('Request to /%s/%s: 401 UNAUTHORIZED' % (type, id))
			return 'Unauthorized access (wrong credentials?)', 401
		raise e
	app.logger.info('Request to %s: OK' % request.path)

	cookie = re.sub('^session=', 'JSESSIONID=', cookie)
	response = Response('ok')
	response.headers['Set-Cookie'] = cookie
	return response
