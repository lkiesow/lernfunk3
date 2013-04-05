#!/bin/env python
# -*- coding: utf-8 -*-
'''
	Lernfunk3: Matterhorn Import Service
	====================================

	:copyright: 2013, Lars Kiesow <lkiesow@uos.de>

	:license: FreeBSD and LGPL, see LICENSE for more details.
'''

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import json
import uuid
import urllib
import urllib2
from xml.dom.minidom import parseString
from pprint import pprint
from util import xml_get_data, split_vals
from base64 import urlsafe_b64encode, b64encode
from flask import jsonify
import logging
# http://docs.python.org/2/howto/logging.html
logging.basicConfig(filename='example.log',level=logging.DEBUG)


def load_config( configfile='config.json' ):
	'''This method loads the configuration file and normalizes all entries.
	This means that empty entries will be set to None values or entry lists.
	This way the configuration is easier to handle afterwards.

	:returns: Normalized configuration dictionary
	'''
	f = open( configfile, 'r')
	config = json.load(f)
	f.close()

	# Check/normalize config
	for key in ['creator', 'contributor', 'subject']:
		if not key in config['delimeter'].keys():
			config['delimeter'][key] = None
	for entry in config['trackrules'] + config['metadatarules'] \
			+ config['attachmentrules']:
		for key in ['name','comment']:
			if not key in entry.keys():
				entry[key] = ''
		for key in ['mimetype', '-mimetype', 'extension', '-extension', \
				'protocol', '-protocol', 'source_system', '-source_system', \
				'lf-quality', 'lf-server-id', 'lf-type', 'lf-format', \
				'lf-source', 'type', '-type']:
			if not key in entry.keys():
				entry[key] = None
		for key in ['tags', '-tags']:
			if not key in entry.keys():
				entry[key] = []

	# Defaults
	if not 'defaults' in config.keys():
		config['defaults'] = {}
	for key in ['publisher', 'contributor', 'creator']:
		if not key in config['defaults']:
			config['defaults'][key] = []
	for key in ['visibility', 'published']:
		if not key in config['defaults']:
			config['defaults'][key] = 1
		config['defaults']['language'] = config['defaults'].get('language') or ''

	# Make shure URL ends with /
	config['lf-url'] = config['lf-url'].rstrip('/') + '/'

	# Create a HTTP Basic Auth header from credentials
	config['auth'] = 'Basic ' + urlsafe_b64encode("%s:%s" % \
			( config['username'], config['password'] ))

	return config


class MediapackageImporter:
	'''This class will parse a Matterhorn mediapackage and send the containing
	data to a Lernfunk system. Imported values are:

	- Media (Mediapackage)
	- Series (Series)
	- Files (Tracks)
	- Files (Images)
	- User (Creator, Contributor)

	'''

	def __init__(self, config):
		self.config = config


	def check_rules(self, ruleset, data):
		'''Check if every rule of a ruleset applies to the given data. Returns False
		if a rule does not apply, True otherwise.

		:param ruleset: A normalized set of rules
		:param data:    The data to check
		'''
		if ruleset['-mimetype'] and \
				ruleset['-mimetype'] == data.get('mimetype'):
			return False
		if ruleset['-extension'] and \
				data.get('url').endwith(ruleset['-extension']):
			return False
		if ruleset['-protocol'] and \
				data.get('url').startswith(ruleset['-protocol']):
			return False
		if ruleset['-source_system'] and \
				ruleset['-source_system'] == data.get('source_system'):
			return False
		if ruleset['-type'] and \
				ruleset['-type'] == type:
			return False
		if ruleset['mimetype'] and \
				ruleset['mimetype'] != data.get('mimetype'):
			return False
		if ruleset['extension'] and \
				not data.get('url').endswith( ruleset['extension'] ):
			return False
		if ruleset['protocol'] and \
				not data.get('url').startswith( ruleset['protocol'] ):
			return False
		if ruleset['source_system'] and \
				ruleset['source_system'] != data.get('source_system'):
			return False
		if ruleset['type'] and \
				ruleset['type'] != data.get('type'):
			return False
		# Finally check the tags
		if True in [ t in data['tags'] for t in ruleset['-tags'] ]:
			return False
		if False in [ t in data['tags'] for t in ruleset['tags'] ]:
			return False
		return True


	def login( self ):
		'''This method will send a login request to the Lernfunk Core Webservice. On
		success it will return a valid session which can be used for further
		authentication.
		'''
		req = urllib2.Request('%slogin' % self.config['lf-url'])
		req.add_header('Authorization', self.config['auth'])
		u = urllib2.urlopen(req)
		self.session = u.info().get('Set-Cookie')
		u.close()
		if not self.session:
			raise urllib2.URLError('Login failed')


	def logout( self ):
		'''This method will send a logout request to the Lernfunk Core Webservice.
		'''
		req = urllib2.Request('%slogout' % self.config['lf-url'])
		req.add_header('Cookie', self.session)
		u = urllib2.urlopen(req)


	def request_people( self, names ):
		'''This method takes a list of realnames, checks if users with these name
		exists in the lernfunk system and returns their ids. If a user does not
		yet exists he will be created.

		:param names: List of realnames
		'''
		uids = []
		for name in names:
			# First: Check if user exists:

			# Use Base64 encoding if necessary
			searchq = 'eq:realname:base64:%s' % b64encode(name) \
					if ( ',' in name or ';' in name ) \
					else 'eq:realname:%s' % name
			req = urllib2.Request('%sadmin/user/?%s' % (
				self.config['lf-url'],
				urllib.urlencode({'q':searchq})))
			req.add_header('Cookie', self.session)
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
				req  = urllib2.Request('%sadmin/user/' % self.config['lf-url'])
				req.add_data(user)
				req.add_header('Cookie',       self.session)
				req.add_header('Content-Type', 'application/json')
				req.add_header('Accept',       'application/xml')
				u = urllib2.urlopen(req)
				newuser = u.read()
				u.close()
				uid = xml_get_data(parseString(newuser), 'id', type=int)
			else:
				if resultcount > 1:
					logging.warn('Realname "%s" is ambiguous. Use first match.' % name )
				uid = xml_get_data(data, 'identifier', type=int)
			uids.append( uid )

		return uids


	def post_series( self, s ):
		print '###############'
		print s
		print '###############'
		creators     = self.request_people( s['creator'] )
		contributors = self.request_people( s['contributor'] )

		series = {
				"lf:series": [
					{
						"lf:source_key": s['id'],
						"lf:editor": 3,
						"dc:identifier": "ba88024f-6adc-11e2-8b4e-047d7b0f869a", 
						"lf:owner": 3, 
						"dc:title": "testseries", 
						"dc:language": "de", 
						"lf:published": 1, 
						"dc:date": "2013-01-30 13:58:22", 
						"lf:source_system": null, 
						"lf:visible": 1, 
						"lf:last_edit": "2013-01-30 13:58:22", 
						"dc:description": "some text\u2026", 

						"dc:publisher": [ 1 ], 
						"lf:creator": [ 1 ], 
						"dc:subject": [ "Informatik" ]
						}
					]
				}
		return
		uids = []
		for name in names:
			# First: Check if user exists:

			# Use Base64 encoding if necessary
			searchq = 'eq:realname:base64:%s' % b64encode(name) \
					if ( ',' in name or ';' in name ) \
					else 'eq:realname:%s' % name
			req = urllib2.Request('%sadmin/user/?%s' % (
				self.config['lf-url'],
				urllib.urlencode({'q':searchq})))
			req.add_header('Cookie', self.session)
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
				req  = urllib2.Request('%sadmin/user/' % self.config['lf-url'])
				req.add_data(user)
				req.add_header('Cookie',       self.session)
				req.add_header('Content-Type', 'application/json')
				req.add_header('Accept',       'application/xml')
				u = urllib2.urlopen(req)
				newuser = u.read()
				u.close()
				uid = xml_get_data(parseString(newuser), 'id', type=int)
			else:
				if resultcount > 1:
					logging.warn('Realname "%s" is ambiguous. Use first match.' % name )
				uid = xml_get_data(data, 'identifier', type=int)
			uids.append( uid )

		return uids


	def build_search_request( self, op, val, endpoint, mimetype='application/xml' ):
		'''Build a search request for the Lernfunk Core Webservice.

		:param op:       Search operator for request
		:param val:      Value for search
		:param endpoint: Endpoint for request
		:param mimetype: Mimetype for result

		:returns: Search request for use with urllib2
		'''
		searchq = '%s:base64:%s' % ( op, b64encode(val) ) \
				if ( ',' in val or ';' in val ) \
				else '%s:%s' % ( op, val )
		req = urllib2.Request('%s%s?%s' % (
			self.config['lf-url'],
			endpoint,
			urllib.urlencode({'q':searchq})))
		req.add_header('Cookie', self.session)
		req.add_header('Accept', mimetype)
		return req


	def import_media( self, mp, source_system='localhost' ):
		'''This method takes a Opencast Matterhorn mediapackage as input, parses it
		and imports the tracks, metadata and attachments according to the
		configuration.

		The new datasets are send to the Lernfunk core webservice as HTTP POST
		requests.

		:param mp: String representation of a matterhorn mediapackage

		'''
		# Log into core webservice
		self.login()

		# Parse XML
		mp = parseString( mp )

		# Get metadata
		m = {}
		s = {}
		m['title']       = xml_get_data(mp, 'title')
		s['id']          = xml_get_data(mp, 'series')
		s['title']       = xml_get_data(mp, 'seriestitle')
		m['license']     = xml_get_data(mp, 'license')
		m['language']    = xml_get_data(mp, 'language')
		m['description'] = xml_get_data(mp, 'description')
		m['creator']     = xml_get_data(mp, 'creator',     array='always')
		m['contributor'] = xml_get_data(mp, 'contributor', array='always')
		m['subject']     = xml_get_data(mp, 'subject',     array='always')
		mpNode = mp.getElementsByTagNameNS('*','mediapackage')[0]
		m['id']       = mpNode.getAttribute('id')
		m['start']    = mpNode.getAttribute('start')
		m['duration'] = mpNode.getAttribute('duration')

		# Split values if necessary
		m['subject']     = split_vals( m['subject'], 
				config['delimeter']['subject'] or [] )
		m['creator']     = split_vals( m['creator'], 
				config['delimeter']['creator'] or [] )
		m['contributor'] = split_vals( m['contributor'], 
				config['delimeter']['contributor'] or [] )

		# Get additional metadata
		for cat in mp.getElementsByTagNameNS('*', 'catalog'):
			t = {'source_system' : source_system}
			t['mimetype'] = xml_get_data(cat, 'mimetype')
			t['type']     = cat.getAttribute('type')
			t['id']       = cat.getAttribute('ref').lstrip('catalog').lstrip(':')
			t['tags']     = xml_get_data(cat, 'tag', array='always')
			t['url']      = xml_get_data(cat, 'url')

			for r in config['metadatarules']:
				if not self.check_rules( r, t ):
					continue
				# Get additional metadata from server
				try:
					u = urllib2.urlopen(t['url'])
					dcdata = u.read()
					u.close()
					dcdata = parseString(dcdata)
					ns = 'http://purl.org/dc/terms/'
					if r.get('use-for') == 'media':
						m['created'] = xml_get_data(dcdata, 'created', namespace=ns)
					if r.get('use-for') == 'series':
						s['creator']     = xml_get_data(dcdata, 'creator',     namespace=ns, array='always')
						s['contributor'] = xml_get_data(dcdata, 'contributor', namespace=ns, array='always')
						s['subject']     = xml_get_data(dcdata, 'subject',     namespace=ns, array='always')
						s['license']     = xml_get_data(dcdata, 'license>',    namespace=ns)
						s['description'] = xml_get_data(dcdata, 'description', namespace=ns)
						s['description'] = xml_get_data(dcdata, 'description', namespace=ns)
						s['language']    = xml_get_data(dcdata, 'language',    namespace=ns)

						# Split values if necessary
						s['subject']     = split_vals( s['subject'], 
								config['delimeter']['subject'] or [] )
						s['creator']     = split_vals( s['creator'], 
								config['delimeter']['creator'] or [] )
						s['contributor'] = split_vals( s['contributor'], 
								config['delimeter']['contributor'] or [] )
				except urllib2.URLError:
					pass
		
		# TODO: 
		# - check if m['id'] is UUID.
		# - Check if media with UUID does exist.
		# - Query creator
		# - Query contributor

		# Check if mediapackage with source_key exists
		u = urllib2.urlopen( self.build_search_request( 
				op='eq:source_key', 
				val=m['id'], 
				endpoint='admin/media/' ) )
		mdata = parseString(u.read()).getElementsByTagNameNS('*', 'result')[0]
		u.close()

		if int(mdata.getAttribute('resultcount')):
			# There is already a existing mediaobject with the given source_key in
			# Lernfunk. Thus we abort the import
			logging.warn( ('Media with source_key="%s" already exists. ' \
					+ 'Aborting import.') % m['id'] )
			return False

		# Import new user or get the ids of existing user
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
						"dc:language": (m['language'] or config['defaults']['language']),
						"lf:visible": config['defaults']['visibility'],
						"dc:source": None, # Put the mediapackage URL
						"lf:published": config['defaults']['published'],
						"dc:date": m['created'],
						"dc:description": m['description'],
						"dc:rights": m['license'],
						"lf:source_system": source_system,

						"dc:subject": m['subject'],
						"dc:publisher": config['defaults']['publisher'],
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
		mediaid  = xml_get_data(newmedia, 'id', type=uuid.UUID)

		resultcount = int(newmedia.getAttribute('resultcount'))
		if resultcount != 1:
			logging.error( ('Something went seriously wrong. ' \
					+ 'The Lernfunk Core Webservice reports, that %i media were ' \
					+ 'created. Should be 1. Aborting import of media "%s".') % \
					(resultcount, m['id'] ))
			return False

		files = []
		for track in mp.getElementsByTagNameNS('*', 'track'):
			t = {'source_system' : source_system}
			t['mimetype'] = xml_get_data(track, 'mimetype')
			t['type']     = track.getAttribute('type')
			t['id']       = track.getAttribute('ref').lstrip('track').lstrip(':')
			t['tags']     = xml_get_data(track, 'tag', array='always')
			t['url']      = xml_get_data(track, 'url')

			for r in config['trackrules']:
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

			for r in config['attachmentrules']:
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
				logging.error( ('Importing files failed: "%s". Aborting import of media "%s".') % \
						(str(e), m['id'] ))
				return False


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

		print( mdata.toxml() )

		if int(mdata.getAttribute('resultcount')) > 0:
			print( 'Series does exist. Add media here' )

		else:
			series_creators     = self.request_people( s['creator'] )
			series_contributors = self.request_people( s['contributor'] )

			series = { "lf:series": [ {
					"lf:source_key":    s['id'],
					"dc:title":         s['title'],
					"dc:language":      s['language'] or config['defaults']['language'],
					"lf:published":     config['defaults']['published'],
					"lf:source_system": source_system,
					"lf:visible":       config['defaults']['visibility'],
					"dc:description":   s['description'],

					"dc:publisher":     config['defaults']['publisher'],
					"lf:creator":       series_creators,
					"dc:subject":       s['subject']
				} ] }
			series = json.dumps(series, separators=(',',':'))
			print( series )

		self.logout()
		
		pprint(s)



def main():
	global config
	try:
		config = load_config()
	except ValueError as e:
		logging.error( 'Error loading config: %s' % str(e) )
		exit()

	importer = MediapackageImporter( config )

	f = open( sys.argv[1], 'r' )
	mediapackage = f.read()
	f.close()

	importer.import_media( mediapackage, 'localhost' )


if __name__ == "__main__":
	main()
