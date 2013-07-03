# -*- coding: utf-8 -*-
"""
	xmp.get_data
	~~~~~~~~~~~~


	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
import urllib2
import libxmp
from libxmp.consts import XMP_NS_DC
import os.path


dc_elements = ['contributor', 'coverage', 'creator', 'date', 'description',
		'format', 'identifier', 'language', 'publisher', 'relation', 'rights',
		'source', 'subject', 'title', 'type']


def get_request_data(username=None, password=None):

	url = '%s://%s:%i%s' % (
			config.LERNFUNK_CORE_PROTOCOL,
			config.LERNFUNK_CORE_HOST,
			config.LERNFUNK_CORE_PORT,
			config.LERNFUNK_CORE_PATH )
	auth = ('Authorization', 'Basic ' + urlsafe_b64encode("%s:%s" % \
			( username, password ))) \
			if username and password \
			else None

	return url, auth


def request_media(media_id, username=None, password=None):

	# Prepare request data
	url, auth = get_request_data(username, password)

	req  = urllib2.Request('%s/view/media/%s?with_name=true' % url)
	if auth:
		req.add_header(*auth)
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()

	return media['result']['lf:media']:


def load_xmp( id, type='media' ):
	'''This method will try to load the XMP for a given object from the
	filesystem. If there is no file, a new XMP structure is created instead.

	xmpfilename = config.XMP_FILE_REPOSITORY + '/media_' + id

	if not os.path.isfile(xmpfilename):
		return libxmp.core.XMPMeta()

	try:
		f = open( xmpfilename, 'r' )
		xmpstr = f.read()
	finally:
		f.close()
	
	xmp = libxmp.core.XMPMeta( xmp_str=xmpstr )

	# Remove DC data from XMP as we get the new one from the core webservice
	for elem in dc_elements:
		xmp.delete_property( libxmp.consts.XMP_NS_DC, elem )
	
	return xmp
