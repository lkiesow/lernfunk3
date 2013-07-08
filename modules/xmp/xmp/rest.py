# -*- coding: utf-8 -*-
"""
	feedgenerator.rest
	~~~~~~~~~~~~~~~~~~

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
from flask import Flask, request, Response
import urllib2

from xmp     import app
from xmp.get import get_xmp


@app.route('/<any(media, series):type>/<id>')
def xmpgen(type, id):
	'''Return an XMP structure for a series or media specified by its id.
	
	:param type: Specifies if media or series are requested.
	:param id:   The id of the resource.
	'''

	user, passwd = None, None
	if request.authorization:
		user   = request.authorization.username
		passwd = request.authorization.password

	try:
		xmpstr = get_xmp(type, id, user, passwd)
	except urllib2.HTTPError as e:
		if e.code == 404:
			app.logger.warn('Request to /%s/%s: 404 NOT FOUND' % (type, id))
			return 'Resource not found', 404
		if e.code == 401:
			app.logger.warn('Request to /%s/%s: 401 UNAUTHORIZED' % (type, id))
			return 'Unauthorized access (wrong credentials?)', 401
		raise e
	app.logger.info('Request to /%s/%s: OK' % (type, id))

	return Response(xmpstr, mimetype='application/rdf+xml')
