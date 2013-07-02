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


def update_media( media_id, dc_data ):


	# TODO: 
	# - check if m['id'] is UUID.
	# - Check if media with UUID does exist.
	# - Query creator
	# - Query contributor

	# Import new user or get the ids of existing user
	if 
	creators      = self.request_people( m['creator'] )
	contributors  = self.request_people( m['contributor'] )

	creators     += self.config['defaults']['creator']
	contributors += self.config['defaults']['contributor']

	# Build mediaobject dataset
	media={
			"lf:media": [
				{
					"lf:source_key": m['id'],
					"dc:type": "Image",
					"dc:title": m['title'],
					"dc:language": (m['language'] or self.config['defaults']['language']),
					"lf:visible": self.config['defaults']['visibility'],
					"dc:source": None, # Put the mediapackage URL
					"lf:published": self.config['defaults']['published'],
					"dc:date": m['created'],
					"dc:description": m['description'],
					"dc:rights": m['license'],
					"lf:source_system": source_system,

					"dc:subject": m['subject'],
					"dc:publisher": self.config['defaults']['publisher'],
					"lf:creator": creators,
					"lf:contributor": contributors
					}
				]
			}

	media = json.dumps(media, separators=(',',':'))
	# POST media to Lernfunk Core Webservice
	req  = urllib2.Request('%sadmin/media/' % self.config['lf-url'])
	req.add_data(media)
	req.add_header('Cookie',       self.session)
	req.add_header('Content-Type', 'application/json')
	req.add_header('Accept',       'application/xml')
	u = urllib2.urlopen(req)
	newmedia = parseString(u.read())
	u.close()

	newmedia = newmedia.getElementsByTagNameNS('*', 'result')[0]
	resultcount = int(newmedia.getAttribute('resultcount'))
	if resultcount != 1:
		logging.error( ('Something went seriously wrong. ' \
				+ 'The Lernfunk Core Webservice reports, that %i media were ' \
				+ 'created. Should be 1. Aborting import of media "%s".') % \
				(resultcount, m['id'] ))
		return False

	mediaid  = xml_get_data(newmedia, 'id', type=uuid.UUID)

	logging.info('Created new media with (lf:%s)' % str(mediaid) )

	files = []
	for track in mp.getElementsByTagNameNS('*', 'track'):
		t = {'source_system' : source_system}
		t['mimetype'] = xml_get_data(track, 'mimetype')
		t['type']     = track.getAttribute('type')
		t['id']       = track.getAttribute('ref').lstrip('track').lstrip(':')
		t['tags']     = xml_get_data(track, 'tag', array='always')
		t['url']      = xml_get_data(track, 'url')

		for r in self.config['trackrules']:
			# Check rules defined in configuration. If a rule does not apply jump
			# straight to the next set of rules.
			if not self.check_rules( r, t ):
				continue

			if r['lf-type']:
				t['type'] = r['lf-type']
			if r['lf-server-id']:
				t['url'] = None
			t['format']    = r['lf-format'] or t['mimetype']
			t['quality']   = r['lf-quality']
			t['server-id'] = r['lf-server-id']
			t['source']    = r['lf-source']

			# Build request
			#  omitting: "dc:identifier": "..."
			f = {
				"dc:format":        t['format'],
				"lf:media_id":      str(mediaid),
				"lf:quality":       t['quality'],
				"lf:source":        t['source'],
				"lf:source_key":    t['id'],
				"lf:source_system": source_system,
				"lf:type":          t['type'],
				"lf:uri":           t['url'],
				"lf:server_id":     t['server-id']
			}
			files.append(f)

	for attachment in mp.getElementsByTagNameNS('*', 'attachment'):
		a = {'source_system' : source_system}
		a['mimetype'] = xml_get_data(attachment, 'mimetype')
		a['type']     = attachment.getAttribute('type')
		a['id']       = attachment.getAttribute('ref').lstrip('attachment').lstrip(':')
		a['tags']     = xml_get_data(attachment, 'tag', array='always')
		a['url']      = xml_get_data(attachment, 'url')

		for r in self.config['attachmentrules']:
			# Check rules defined in configuration. If a rule does not apply jump
			# straight to the next set of rules.
			if not self.check_rules( r, a ):
				continue

			if r['lf-type']:
				a['type'] = r['lf-type']
			if r['lf-server-id']:
				a['url'] = None
			a['format']    = r['lf-format'] or a['mimetype']
			a['quality']   = r['lf-quality']
			a['server-id'] = r['lf-server-id']
			a['source']    = r['lf-source']

			# Build request
			#  omitting: "dc:identifier": "..."
			f = {
				"dc:format":        a['format'],
				"lf:media_id":      str(mediaid),
				"lf:quality":       a['quality'],
				"lf:source":        a['source'],
				"lf:source_key":    a['id'],
				"lf:source_system": source_system,
				"lf:type":          a['type'],
				"lf:uri":           a['url'],
				"lf:server_id":     a['server-id']
			}
			files.append(f)


	# POST files to Lernfunk Core Webservice
	if files:
		files = {'lf:file':files}
		files = json.dumps(files, separators=(',',':'))

		req  = urllib2.Request('%sadmin/file/' % self.config['lf-url'])
		req.add_data(files)
		req.add_header('Cookie',       self.session)
		req.add_header('Content-Type', 'application/json')
		req.add_header('Accept',       'application/xml')
		try:
			u = urllib2.urlopen(req)
			u.close()
		except urllib2.HTTPError as e:
			addinfo = '409 probably means that the requested lf_server does not exist.' \
					if e.getcode() == 409 else ''
			logging.error('Importing files failed: "%s". Aborting import of media "%s". %s' % \
					(str(e), m['id'], addinfo ))
			return False

	logging.info('Successfully added files to media (lf:%s)' % str(mediaid) )


	# If we have no series we are finished here
	if not s.get('id'):
		return True

	# Check if series with source_key exists
	u = urllib2.urlopen( self.build_search_request( 
			op='eq:source_key', 
			val=s['id'], 
			endpoint='admin/series/' ) )
	sdata = parseString(u.read()).getElementsByTagNameNS('*', 'result')[0]
	u.close()

	if int(sdata.getAttribute('resultcount')) > 0:
		seriesid = xml_get_data(sdata, 'identifier', type=uuid.UUID, array='always')[0]
		series_media = { "lf:series_media": [ {
				"lf:series_id": str(seriesid),
				'lf:media_id':  [ str(mediaid) ]
			} ] }
		series_media = json.dumps(series_media, separators=(',',':'))
		print( series_media )

		# POST series media connection to Lernfunk Core Webservice
		req = urllib2.Request('%sadmin/series/media/' % self.config['lf-url'])
		req.add_data(series_media)
		req.add_header('Cookie',       self.session)
		req.add_header('Content-Type', 'application/json')
		req.add_header('Accept',       'application/xml')
		try:
			u = urllib2.urlopen(req)
			u.close()
			logging.info( 'Successfully media (lf:%s) to series (lf:%s)' % \
					(str(seriesid), str(mediaid) ))
		except urllib2.HTTPError as e:
			logging.error('Connecting media to series failed: "%s".' % str(e))
			return False

	else:
		series_creators     = self.request_people( s['creator'] )
		series_contributors = self.request_people( s['contributor'] )

		series = { "lf:series": [ {
				"lf:source_key":    s['id'],
				"dc:title":         s['title'],
				"dc:language":      s['language'] or self.config['defaults']['language'],
				"lf:published":     self.config['defaults']['published'],
				"lf:source_system": source_system,
				"lf:visible":       self.config['defaults']['visibility'],
				"dc:description":   s['description'],

				"dc:publisher":     self.config['defaults']['publisher'],
				"lf:creator":       series_creators,
				"dc:subject":       s['subject'],

				'lf:media_id':      [ str(mediaid) ]
			} ] }
		series = json.dumps(series, separators=(',',':'))

		# POST series to Lernfunk Core Webservice
		req = urllib2.Request('%sadmin/series/' % self.config['lf-url'])
		req.add_data(series)
		req.add_header('Cookie',       self.session)
		req.add_header('Content-Type', 'application/json')
		req.add_header('Accept',       'application/xml')
		try:
			u = urllib2.urlopen(req)
			newseries = parseString(u.read()).getElementsByTagNameNS('*', 'result')[0]
			u.close()
			resultcount = int(newseries.getAttribute('resultcount'))
			if resultcount != 1:
				logging.error( ('Something went seriously wrong. ' \
						+ 'The Lernfunk Core Webservice reports, that %i series were ' \
						+ 'created. Should be 1. Creation of series "%s" failed.') % \
						(resultcount, s['id'] ))
				return False

			seriesid = xml_get_data(newseries, 'id', type=uuid.UUID)
			logging.info( ('Successfully imported series (lf:%s) and connected media (lf:%s)') % \
					(str(seriesid), str(mediaid) ))
		except urllib2.HTTPError as e:
			logging.error( ('Importing series failed: "%s". Part of media import (%s).') % \
					(str(e), m['id'] ))
			return False

	self.logout()


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
