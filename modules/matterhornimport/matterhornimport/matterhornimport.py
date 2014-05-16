#!/bin/env python
# -*- coding: utf-8 -*-
'''
	matterhornimport.matterhornimport
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
import os
from util import xml_get_data, split_vals
from base64 import urlsafe_b64encode, b64encode
from flask import jsonify
import logging

# Defaultconfigfile
__dir__     = os.path.dirname(__file__)
__cfgfile__ = os.path.join(__dir__,'config.json')
__logfile__ = os.path.join(__dir__,'matterhorn-import.log')

# webservice stuff
from flask import Flask, request, _app_ctx_stack
app = Flask(__name__)


def load_config( configfile=__cfgfile__ ):
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
		try:
			self.login()
		except urllib2.URLError as e:
			logging.error('Faild to login: %s' % str(e) )
			return False

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
				self.config['delimeter']['subject'] or [] )
		m['creator']     = split_vals( m['creator'],
				self.config['delimeter']['creator'] or [] )
		m['contributor'] = split_vals( m['contributor'],
				self.config['delimeter']['contributor'] or [] )

		# Get additional metadata
		for cat in mp.getElementsByTagNameNS('*', 'catalog'):
			t = {'source_system' : source_system}
			t['mimetype'] = xml_get_data(cat, 'mimetype')
			t['type']     = cat.getAttribute('type')
			t['id']       = cat.getAttribute('ref').lstrip('catalog').lstrip(':')
			t['tags']     = xml_get_data(cat, 'tag', array='always')
			t['url']      = xml_get_data(cat, 'url')

			for r in self.config['metadatarules']:
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
								self.config['delimeter']['subject'] or [] )
						s['creator']     = split_vals( s['creator'],
								self.config['delimeter']['creator'] or [] )
						s['contributor'] = split_vals( s['contributor'],
								self.config['delimeter']['contributor'] or [] )
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
		creators      = m['creator']
		contributors  = m['contributor']

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
						"dc:date": (m.get('created') or m.get('start')),
						"dc:description": m.get('description'),
						"dc:rights": m.get('license'),
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
			t['flavor']   = t['type']

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
					"lf:server_id":     t['server-id'],
					"lf:flavor":        t['flavor'],
					"lf:tags":          t['tags']
				}
				files.append(f)

		for attachment in mp.getElementsByTagNameNS('*', 'attachment'):
			a = {'source_system' : source_system}
			a['mimetype'] = xml_get_data(attachment, 'mimetype')
			a['type']     = attachment.getAttribute('type')
			a['id']       = attachment.getAttribute('ref').lstrip('attachment').lstrip(':')
			a['tags']     = xml_get_data(attachment, 'tag', array='always')
			a['url']      = xml_get_data(attachment, 'url')
			a['flavor']   = a['type']

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
					"lf:server_id":     a['server-id'],
					"lf:flavor":        a['flavor'],
					"lf:tags":          a['tags']
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
				import time
				time.sleep(0.2)
				u = urllib2.urlopen(req)
				u.close()
			except urllib2.HTTPError as e:
				addinfo = '409 probably means that the requested lf_server does not exist.' \
						if e.getcode() == 409 else ''
				logging.error('Importing files failed: "%s". Aborting import of media "%s". %s' % \
						(str(e), m['id'], addinfo ))

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
			series_creators     = s.get('creator')
			series_contributors = s.get('contributor')

			series = { "lf:series": [ {
					"lf:source_key":    s['id'],
					"dc:title":         s.get('title'),
					"dc:language":      s.get('language') or self.config['defaults']['language'],
					"lf:published":     self.config['defaults']['published'],
					"lf:source_system": source_system,
					"lf:visible":       self.config['defaults']['visibility'],
					"dc:description":   s.get('description'),

					"dc:publisher":     self.config['defaults']['publisher'],
					"lf:creator":       series_creators,
					"dc:subject":       s.get('subject'),

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

		return True



def service_get_config():
	'''Returns the importer configuration. If it is not alredy loaded for the
	current application context it will load it.

	:returns: A MediapackageImporter configuration
	'''
	top = _app_ctx_stack.top
	if not hasattr(top, 'importer_config'):
		try:
			top.importer_config = load_config()
			# We also want to configure the logger
			configure_logger( top.importer_config )
		except ValueError as e:
			abort(500, str(e))
	return top.importer_config



def service_get_mediapackage_importer( config ):
	'''Returns an instance of a mediapackage importer. If there is none for the
	current application context a new one will be created.

	:param config: A valid MediapackageImporter configuration
	:returns: An instance of MediapackageImporter
	'''
	top = _app_ctx_stack.top
	if not hasattr(top, 'importer_instance'):
		try:
			top.importer_instance = MediapackageImporter( config )
		except ValueError as e:
			abort(500, str(e))
	return top.importer_instance



@app.route('/', methods=['PUT','POST'])
def service():
	'''This method will accept a mediapackage per HTTP POST or PUT request and
	uses it for import.

	The data should be delivered as multipart/form-data and have to include the
	following fields:

		=============  ==========================================
		mediapackage   An Opencast Matterhorn mediapackage as XML
		source_system  System identifier of the Matterhorn server
		=============  ==========================================
	
	'''
	mpkg = request.form.get('mediapackage')
	if not mpkg:
		return 'No mediapackage attached\n', 400

	source_system = request.form.get('source_system')
	if not source_system:
		return 'No source system defined\n', 400

	config = service_get_config()

	# Check if we want to save the mediapackages we get
	if config.get('mediapackage_archive'):
		import time
		with open('%s/%s.xml' % (config['mediapackage_archive'], time.time()), 'w') as f:
			f.write( mpkg )

	# Import media
	#importer = service_get_mediapackage_importer( config )
	importer = MediapackageImporter( config )
	if importer.import_media( mpkg, source_system ):
		return 'Mediapackage received\n', 201
	return 'Import failed. See importer logs for more details', 500



def configure_logger( config ):
	'''This method will set up the logger. For this config['loglevel'] and
	config['logfile'] are used. The fallback values in case that these keys are
	not in the configuration are INFO as loglevel and matterhorn-import.log as
	'''
	loglevel = config.get('loglevel') or 'INFO'
	loglevel = getattr(logging, loglevel.upper(), None)
	if not isinstance(loglevel, int):
		print('Error: Invalig loglevel')
		exit()
	logfile = config.get('logfile') or __logfile__
	logging.basicConfig(filename=logfile, level=loglevel)



def program( mpkgfile ):
	'''Reads a mediapackage in XML format from a file and starts the import.

	:param mpkgfile: XML mediapackage file to load
	'''
	try:
		config = load_config()
	except ValueError as e:
		print( 'Error loading config: %s' % str(e) )
		exit()

	configure_logger( config )

	# Import media
	importer = MediapackageImporter( config )

	f = open( mpkgfile, 'r' )
	mediapackage = f.read()
	f.close()

	return importer.import_media( mediapackage, 'localhost' )
