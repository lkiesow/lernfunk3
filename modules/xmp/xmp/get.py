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
import libxmp
from libxmp.consts import XMP_NS_DC
import json
import os.path
from base64 import urlsafe_b64encode
from xmp import app


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


def request_lf_data(type, id, username=None, password=None):
	'''Request media with a given identifier from the lf core server.
	'''
	# Prepare request data
	url, auth = get_request_data(username, password)

	req  = urllib2.Request('%sview/%s/%s?with_name=1' % (url,type,id))
	if auth:
		req.add_header(*auth)
	req.add_header('Accept', 'application/json')
	u = urllib2.urlopen(req)
	try:
		media = json.loads(u.read())
	finally:
		u.close()

	return media['result']['lf:' + type]


def load_xmp( type, id ):
	'''This method will try to load the XMP for a given object from the
	filesystem. If there is no file, a new XMP structure is created instead.
	'''

	xmpfilename = '%s/%s_%s.xmp' % (app.config['XMP_FILE_REPOSITORY'], type, id)

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
		xmp.delete_property( XMP_NS_DC, elem )
	
	return xmp


def include_lf_dc(lf_data, xmp):
	'''Include elements from a given dataset (result from a lf:core webservice
	request) into a given XMP structure.
	'''

	lastdata = {}

	for data in lf_data:
		lang = data.get('dc:language')
		for key in ['title', 'description', 'rights']:
			value = data.get('dc:' + key)
			if value:
				if lang:
					xmp.set_localized_text(XMP_NS_DC, key, None, lang, value.encode('utf-8'))
				else:
					xmp.set_property(XMP_NS_DC, key, value)

		for key in ['coverage', 'identifier', 'type']:
			value = data.get('dc:' + key)
			if value:
				xmp.set_property(XMP_NS_DC, key, value)

		for key in ['date', 'language', 'relation', 'source']:
			value = data.get('dc:' + key)
			if value and value != lastdata.get(key):
				lastdata[key] = value
				xmp.append_array_item(XMP_NS_DC, key, value, {'prop_array_is_alt':True})

		# Add persons
		# TODO: Add publisher (get name from core)
		for key in ['contributor', 'creator']: #, 'publisher']:
			for uid, name in (data.get('dc:' + key) or {}).iteritems():
				if name != lastdata.get(key):
					lastdata[key] = name
					xmp.append_array_item(XMP_NS_DC, key, name, {'prop_array_is_alt':True})

		# Add subjects
		for subj in data.get('dc:subject') or []:
			if lang:
				xmp.set_localized_text(XMP_NS_DC, 'subject', None, lang, subj.encode('utf-8'))
			else:
				xmp.append_array_item(XMP_NS_DC, 'subject', subj, {'prop_array_is_alt':True})

	return xmp


def get_xmp(type, id, user=None, password=None):
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
	print get_xmp('media', 'e8ad5959-9d26-11e2-a381-047d7b0f869a', 'lkiesow', 'test')
