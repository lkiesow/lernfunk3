# -*- coding: utf-8 -*-
"""
	xmp.update_data
	~~~~~~~~~~~~~~~


	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD, see LICENSE for more details.
"""
# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import urllib
import urllib2
from base64 import urlsafe_b64encode, b64encode
from xml.dom.minidom import parseString

import config
import re
import libxmp
from libxmp.consts import XMP_NS_DC
import logging

def get_dc_array( xmp, dc_prop, name ):
	if dc_prop is None:
		dc_prop = []
	if xmp.does_property_exist(XMP_NS_DC, name):
		dc_prop[name] = []
		for i in range(xmp.count_array_items( XMP_NS_DC, name )):
			dc_prop[name].append( xmp.get_array_item( XMP_NS_DC, name, i+1 ).keys()[0] )
		return dc_prop[name]


def get_dc_prop( xmp, dc_prop, name ):
	if xmp.does_property_exist(XMP_NS_DC, name):
		dc_prop[name] = xmp.get_property(XMP_NS_DC, name)
		return dc_prop[name]


def get_dc_lang_prop( xmp, dc_prop, name, lang_generic=None, lang_specific=None ):
	if xmp.does_property_exist(XMP_NS_DC, name):
		dc_prop[name] = xmp.get_localized_text( XMP_NS_DC, name, 
				lang_generic, lang_specific)
		return dc_prop[name]


def get_dc_data(xmpstr):
	xmp = libxmp.core.XMPMeta( xmp_str=xmpstr )

	lang_filter = re.compile(config.LANGUAGES)
	languages = get_dc_array( xmp, None, 'language' ) \
			if config.LANGUAGE_SUPPORT \
			else None
	if config.LANGUAGE_TRY_DEFAULT and not languages:
		languages = [config.LANGUAGE_DEFAULT]
	
	dcdata = []
	if languages:
		for lang in languages:
			if not lang_filter.match(lang):
				continue
			dc_prop = {}
			dc_prop['language'] = lang

			lang_generic  = lang.split('-',1)[0]
			lang_specific = lang

			get_dc_array(     xmp, dc_prop, 'contributor' )
			get_dc_prop(      xmp, dc_prop, 'coverage' )
			get_dc_array(     xmp, dc_prop, 'creator' )
			get_dc_array(     xmp, dc_prop, 'date' )
			get_dc_lang_prop( xmp, dc_prop, 'decsription', lang_generic, lang_specific )
			get_dc_prop(      xmp, dc_prop, 'format' )
			get_dc_prop(      xmp, dc_prop, 'identifier' )
			get_dc_array(     xmp, dc_prop, 'language' )
			get_dc_array(     xmp, dc_prop, 'publisher' )
			get_dc_array(     xmp, dc_prop, 'relation' )
			get_dc_lang_prop( xmp, dc_prop, 'rights', lang_generic, lang_specific )
			get_dc_array(     xmp, dc_prop, 'source' )
			get_dc_prop(      xmp, dc_prop, 'subject' )
			get_dc_lang_prop( xmp, dc_prop, 'title', lang_generic, lang_specific )
			get_dc_array(     xmp, dc_prop, 'type' )

			dcdata.append( dc_prop )
	else:
		dc_prop = {}
		dc_prop['language'] = config.LANGUAGE_DEFAULT

		get_dc_array( xmp, dc_prop, 'contributor' )
		get_dc_prop(  xmp, dc_prop, 'coverage' )
		get_dc_array( xmp, dc_prop, 'creator' )
		get_dc_array( xmp, dc_prop, 'date' )
		get_dc_prop(  xmp, dc_prop, 'decsription')
		get_dc_prop(  xmp, dc_prop, 'format' )
		get_dc_prop(  xmp, dc_prop, 'identifier' )
		get_dc_array( xmp, dc_prop, 'language' )
		get_dc_array( xmp, dc_prop, 'publisher' )
		get_dc_array( xmp, dc_prop, 'relation' )
		get_dc_prop(  xmp, dc_prop, 'rights')
		get_dc_array( xmp, dc_prop, 'source' )
		get_dc_prop(  xmp, dc_prop, 'subject' )
		get_dc_prop(  xmp, dc_prop, 'title')
		get_dc_array( xmp, dc_prop, 'type' )

		dcdata.append( dc_prop )

	return dcdata


def update_media( media_id, dc ):

	# Prepare data we need for HTTP requests
	url = '%s://%s:%i%s' % (
			config.LERNFUNK_CORE_PROTOCOL,
			config.LERNFUNK_CORE_HOST,
			config.LERNFUNK_CORE_PORT,
			config.LERNFUNK_CORE_PATH )
	auth = 'Basic ' + urlsafe_b64encode("%s:%s" % \
			( config.LERNFUNK_CORE_USERNAME, config.LERNFUNK_CORE_PASSWORD ))

	# TODO: 
	# - check if m['id'] is UUID.
	# - Check if media with UUID does exist.
	# - Query creator
	# - Query contributor

	# Import new user or get the ids of existing user
	creators = self.request_people( dc['creator'] ) \
			if dc.get('creator') \
			else []
	contributors = self.request_people( dc['contributor'] ) \
			if dc.get('contributor') \
			else []

	# Build mediaobject dataset
	media={
			"lf:media": [
				{
					"dc:type"        : "Image",
					"dc:title"       : dc.get('title'),
					"dc:language"    : dc.get('language'),
					"dc:source"      : dc.get('source'),
					"dc:date"        : dc.get('created'),
					"dc:description" : dc.get('description'),
					"dc:rights"      : dc.get('license'),
					"dc:subject"     : dc.get('subject'),
					"dc:publisher"   : dc.get('publisher'),
					"lf:creator"     : creators,
					"lf:contributor" : contributors
					}
				]
			}

	media = json.dumps(media, separators=(',',':'))
	# POST media to Lernfunk Core Webservice
	req  = urllib2.Request('%sadmin/media/' % url)
	req.add_data(media)
	req.add_header('Cookie',        self.session)
	req.add_header('Authorization', auth)
	req.add_header('Content-Type',  'application/json')
	req.add_header('Accept',        'application/xml')
	u = urllib2.urlopen(req)
	newmedia = parseString(u.read())
	u.close()

	newmedia = newmedia.getElementsByTagNameNS('*', 'result')[0]
	resultcount = int(newmedia.getAttribute('resultcount'))
	if resultcount != 1:
		logging.error( ('Something went seriously wrong. ' \
				+ 'The Lernfunk Core Webservice reports, that %i media were ' \
				+ 'created. Should be 1.') % \
				resultcount)
		return False

	# mediaid  = xml_get_data(newmedia, 'id', type=uuid.UUID)

	# logging.info('Created new media with (lf:%s)' % str(mediaid) )



def request_people( self, names ):
	'''This method takes a list of realnames, checks if users with these name
	exists in the lernfunk system and returns their ids. If a user does not
	yet exists he will be created.

	:param names: List of realnames
	'''
	# Prepare URL and credentials
	url = '%s://%s:%i%s' % (
			config.LERNFUNK_CORE_PROTOCOL,
			config.LERNFUNK_CORE_HOST,
			config.LERNFUNK_CORE_PORT,
			config.LERNFUNK_CORE_PATH )
	auth = 'Basic ' + urlsafe_b64encode("%s:%s" % \
			( config.LERNFUNK_CORE_USERNAME, config.LERNFUNK_CORE_PASSWORD ))

	# Start requesting data
	uids = []
	for name in names:
		# First: Check if user exists:

		# Use Base64 encoding if necessary
		searchq = 'eq:realname:base64:%s' % b64encode(name) \
				if ( ',' in name or ';' in name ) \
				else 'eq:realname:%s' % name
		req = urllib2.Request('%sadmin/user/?%s' % (
			url, urllib.urlencode({'q':searchq})))
		req.add_header('Authorization', auth)
		req.add_header('Accept', 'application/xml')
		u = urllib2.urlopen(req)
		data = parseString(u.read()).getElementsByTagNameNS('*', 'result')[0]
		u.close()
		resultcount = int(data.getAttribute('resultcount'))
		if resultcount == 0:
			logging.info('No user with realname "%s". Create new.' % name)
			# Create new user
			user = {"lf:user":[{'lf:realname':name}]}
			user = json.dumps(user, separators=(',',':'))
			req  = urllib2.Request('%sadmin/user/' % url)
			req.add_data(user)
			req.add_header('Authorization', auth)
			req.add_header('Content-Type', 'application/json')
			req.add_header('Accept',       'application/xml')
			u = urllib2.urlopen(req)
			newuser = u.read()
			u.close()
			uid = xml_get_data(parseString(newuser), 'id', type=int)
			logging.info('User with realname "%s" created with uid=%i' % (name,uid))
		else:
			if resultcount > 1:
				logging.warn('Realname "%s" is ambiguous. Use first match.' % name )
			uid = xml_get_data(data, 'identifier', type=int)
		uids.append( uid )

	return uids


if __name__ == '__main__':
	with open('test.xmp', 'r') as f:
		xmpstr = f.read()
	import pprint
	pprint.pprint( get_dc_data(xmpstr) )


'''
xmp2.set_property( libxmp.consts.XMP_NS_DC, 'creator', 'Lars Kiesow')
xmp2.serialize_to_str( 
	padding=0,
	omit_packet_wrapper=True,
	use_compact_format=True)
'''
