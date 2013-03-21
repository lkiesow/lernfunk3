# -*- coding: utf-8 -*-
"""
	core.admin.put
	~~~~~~~~~~~~~~~

	This module provides write access to the central Lernfunk database. It is
	the administrative REST endpoint for the Lernfunk database. It will let you
	modify and create all data.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
"""

from core import app
from core.util import *
from core.db import get_db
from core.authenticate import get_authorization
from MySQLdb import IntegrityError
from MySQLdb import Error as MySQLdbError
from xml.dom.minidom import parseString
import json
from datetime import datetime
import email.utils
from string import printable as printable_chars
import os
import hashlib

from flask import request, session, g, redirect, url_for, jsonify


_formdata = ['application/x-www-form-urlencoded', 'multipart/form-data']


@app.route('/admin/media/', methods=['PUT'])
def admin_media_put():
	'''This method provides you with the functionality to set media. It will
	create a new dataset or a new version if one with the given identifier
	already exists.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:media": [
			{
				"lf:source_key": "123456789", 
				"dc:type": "Image", 
				"dc:title": "test", 
				"dc:language": "de", 
				"lf:visible": 1, 
				"dc:source": null, 
				"dc:identifier": "ba8488d1-6adc-11e2-8b4e-047d7b0f869a", 
				"lf:published": 0, 
				"dc:date": "2013-01-30 13:58:22", 
				"dc:description": "some text\u2026", 
				"dc:rights": "cc-by", 
				"lf:owner": 3, 
				"lf:last_edit": "2013-01-30 13:58:22", 
				"lf:parent_version": null, 
				"lf:source_system": null
			}
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/" 
				xmlns:lf="http://lernfunk.de/terms">
			<!-- TODO -->
		</data>

	NOTICES:
	 * If the identifier is ommittet a new id is generated automatically. 
	 * Only administrators and editors can change the ownership of a media.
	 * You need to have write access to a series to add this edia to a series.
	 * You cannot modify a specific version. Insted a new version is created
	   automatically. If you really want to get rid of a specific version: Be
	   admin, delete the old one and create a new version. If you are no admin:
	   Create a new version based on an old one and ask someone who is admin to
	   delete this one.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	# If the user is no editor (or admin) we want to know which objects he is
	# allowed to modify. In any case, he is not allowed to add new data.
	access_to_media = []
	access_to_series = []
	if not user.is_editor():
		groups = 'or group_id in (' + ','.join( user.groups ) + ') ' \
				if user.groups else ''
		q ='''select media_id, series_id from lf_access 
				where ( user_id = %i %s) 
				and write_access ''' % ( user.id, groups )
		cur.execute( q )
		for ( media_id, series_id ) in cur.fetchall():
			if media_id:
				access_to_media.append( media_id )
			elif series_id:
				access_to_series.append( series_id )

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for media in data.getElementsByTagName( 'lf:media' ):
				m = {}
				m['id'] = uuid.UUID(xml_get_text(media, 'dc:identifier'))
				if not ( m['id'] or user.is_editor() ):
					return 'You are not allowed to create new media', 403

				m['coverage']       = xml_get_text(media, 'dc:coverage')
				m['description']    = xml_get_text(media, 'dc:description')
				m['language']       = xml_get_text(media, 'dc:language', True)
				m['owner']          = xml_get_text(media, 'lf:owner')
				m['parent_version'] = xml_get_text(media, 'lf:parent_version')
				m['published']      = 1 if xml_get_text(media,'lf:published',True) else 0
				m['relation']       = xml_get_text(media, 'dc:relation')
				m['rights']         = xml_get_text(media, 'dc:rights')
				m['source']         = xml_get_text(media, 'source')
				m['source_key']     = xml_get_text(media, 'lf:source_key')
				m['source_system']  = xml_get_text(media, 'lf:source_system')
				m['title']          = xml_get_text(media, 'dc:title')
				m['type']           = xml_get_text(media, 'dc:type')
				m['visible']        = xml_get_text(media, 'lf:visible', True)
				m['date']           = xml_get_text(media, 'dc:date', True)

				# Additional relations:
				m['subject']        = [ s.childNodes[0].data \
						for s in media.getElementsByTagNameNS(XML_NS_DC,'subject') ]
				m['publisher']      = [ int(p.childNodes[0].data) \
						for p in media.getElementsByTagNameNS(XML_NS_DC,'publisher') ]
				m['creator']        = [ int(c.childNodes[0].data) \
						for c in media.getElementsByTagNameNS(XML_NS_LF,'creator') ]
				m['contributor']    = [ int(c.childNodes[0].data) \
						for c in media.getElementsByTagNameNS(XML_NS_LF,'contributor') ]
				sqldata.append( m )
		except (AttributeError, IndexError):
			return 'Invalid server data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new server data
		try:
			data = data['lf:media']
		except KeyError:
			# Assume that there is only one server
			data = [data]
		for media in data:
			m = {}
			try:
				if media.get('dc:identifier'):
					m['id'] = uuid.UUID(media['dc:identifier'])
				elif not user.is_editor():
					return 'You are not allowed to create new media', 403

				m['coverage']       = media.get('dc:coverage')
				m['description']    = media.get('dc:description')
				m['language']       = media['dc:language']
				m['owner']          = media.get('lf:owner')
				m['parent_version'] = media.get('lf:parent_version')
				m['published']      = 1 if media['lf:published'] else 0
				m['relation']       = media.get('dc:relation')
				m['rights']         = media.get('dc:rights')
				m['source']         = media.get('source')
				m['source_key']     = media.get('lf:source_key')
				m['source_system']  = media.get('lf:source_system')
				m['title']          = media.get('dc:title')
				m['type']           = media.get('dc:type')
				m['visible']        = media['lf:visible']
				m['date']           = media['dc:date']

				# Additional relations:
				m['subject']        = media.get('dc:subject')
				m['publisher']      = media.get('dc:publisher')
				m['creator']        = media.get('lf:creator')
				m['contributor']    = media.get('lf:contributor')

				sqldata.append( m )
			except KeyError:
				return 'Invalid server data', 400

	# Check some data
	for media in sqldata:
		try:
			if not media['type'] in ['Collection','Dataset','Event','Image',
					'Interactive Resource','Service','Software','Sound','Text',
					None]:
				return 'dc:type has to be part of the DCMI Type Vocabulary ' \
						+ '[http://dublincore.org/documents/2000/07/11/'\
						+ 'dcmi-type-vocabulary/]', 400
			if not media.get('date'):
				media['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			else:
				try:
					# Assume ISO datetime format (YYYY-MM-DD HH:MM:SS)
					datetime.strptime(media['date'], '%Y-%m-%d %H:%M:%S')
				except ValueError:
					# Check RFC2822 datetime format instead
					# (Do not use , for separating weekday and month!)
					media['date'] = datetime.fromtimestamp(
							email.utils.mktime_tz(email.utils.parsedate_tz(val))
							).strftime("%Y-%m-%d %H:%M:%S")
			media['owner'] = int(media['owner'])
			# Check relations:
			if media.get('publisher'):
				media['publisher'] = [ int(pub) for pub in media['publisher'] ]
			if media.get('creator'):
				media['creator'] = [ int(creator) for creator in media['creator'] ]
			if media.get('contributor'):
				media['contributor'] = [ int(contrib) for contrib in media['contributor'] ]
		except (KeyError, ValueError):
			return 'Invalid server data', 400

	# Admins and editors are allowed to create new media and change the
	# ownership of all existing ones. Thus we do not have to check their
	# permissions on each object:
	result = []
	if user.is_editor:
		for media in sqldata:
			# If there is no id, we create a new one:
			if not media.get('id'):
				media['id'] = uuid.uuid4()
			try:
				# Get next version for this media. Since this happens in a
				# transaction the value will not change between transactions.
				cur.execute('''select max(version) from lf_media 
					where id = x'%s' ''' % media['id'].hex )
				(version,) = cur.fetchone()
				version = 0 if ( version is None ) else version + 1
				cur.execute('''insert into lf_media
					(id, version, parent_version, language, title, description,
					owner, editor, timestamp_created, published, source, visible,
					source_system, source_key, rights, type, coverage, relation) 
					values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
					( media['id'].bytes,
						version,
						media.get('parent_version'),
						media['language'],
						media.get('title'),
						media.get('description'),
						media.get('owner'),
						user.id,
						media['date'],
						media['published'],
						media.get('source'),
						media['visible'],
						media.get('source_system'),
						media.get('source_key'),
						media.get('rights'),
						media.get('type'),
						media.get('coverage'),
						media.get('relation') ) )

				# Add relations
				if media.get('published'):
					for pub in media['published']:
						cur.execute('''insert into lf_media_publisher
							(media_id, organization_id, media_version)
							values (%s, %s, %s) ''',
							( media['id'].bytes, pub, version ) )
				if media.get('creator'):
					for creator in media['creator']:
						cur.execute('''insert into lf_media_creator
							(media_id, user_id, media_version)
							values (%s, %s, %s) ''',
							( media['id'].bytes, creator, version ) )
				if media.get('contributor'):
					for contrib in media['contributor']:
						cur.execute('''insert into lf_media_contributor
							(media_id, user_id, media_version)
							values (%s, %s, %s) ''',
							( media['id'].bytes, contrib, version ) )

				if media.get('subject'):
					for subj in media['subject']:
						cur.execute('''select id from lf_subject
							where language=%s and name=%s ''',
							( media['language'], subj ) )
						id = cur.fetchone()
						if not id:
							cur.execute('''insert into lf_subject
								(language, name) values (%s, %s) ''',
								( media['language'], subj ) )
							cur.execute('''select last_insert_id() ''')
							id = cur.fetchone()
						id, = id
						cur.execute('''replace into lf_media_subject
							(subject_id, media_id) values (%s, %s) ''',
							(id, media['id'].bytes) )

			except MySQLdbError as e:
				db.rollback()
				cur.close()
				return str(e), 400
			result.append( {'id':str(media['id']), 'version':version} )

		# We will never reach this in case of a failure.
		db.commit()
		cur.close()
		result = { 'lf:created_media' : result }
		if request.accept_mimetypes.best_match(
				['application/xml', 'application/json']) == 'application/json':
			return jsonify(result=result)
		return xmlify(result=result)


	# A simple user tries to update a media object (Create a new version). We
	# have to check if he is (a) the owner of the media or (b) has write access
	# defined in lf_access.
	else:
		try:
			# Get owner
			cur.execute('''select owner from lf_latest_media 
				where id = x'%s' ''' % media['id'])
			owner = int( cur.fetchone() )
			if not ( media['id'].bytes in access_to_media or user.id == owner ):
				return 'You are not allowed to modify this media object', 403
			if owner != media['owner']:
				return 'You are not allowed to change the ownership', 403
			try:
				# Get next version for this media. Since this happens in a
				# transaction the value will not change between transactions.
				cur.execute('''select max(version) from lf_media 
					where id = x'%s' ''' % media['id'].hex )
				(version,) = cur.fetchone()
				version = 0 if ( version is None ) else version + 1
				cur.execute('''insert into lf_media
					(id, version, parent_version, language, title, description,
					owner, editor, timestamp_created, published, source, visible,
					source_system, source_key, rights, type, coverage, relation) 
					values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
					( media['id'].bytes,
						version,
						media.get('parent_version'),
						media['language'],
						media.get('title'),
						media.get('description'),
						media.get('owner'),
						user.id,
						media['date'],
						media['published'],
						media.get('source'),
						media['visible'],
						media.get('source_system'),
						media.get('source_key'),
						media.get('rights'),
						media.get('type'),
						media.get('coverage'),
						media.get('relation') ) )

				# Add relations
				if media.get('published'):
					for pub in media['published']:
						cur.execute('''insert into lf_media_publisher
							(media_id, organization_id, media_version)
							values (%s, %s, %s) ''',
							( media['id'].bytes, pub, version ) )
				if media.get('creator'):
					for creator in media['creator']:
						cur.execute('''insert into lf_media_creator
							(media_id, user_id, media_version)
							values (%s, %s, %s) ''',
							( media['id'].bytes, creator, version ) )
				if media.get('contributor'):
					for contrib in media['contributor']:
						cur.execute('''insert into lf_media_contributor
							(media_id, user_id, media_version)
							values (%s, %s, %s) ''',
							( media['id'].bytes, contrib, version ) )

				if media.get('subject'):
					for subj in media['subject']:
						cur.execute('''select id from lf_subject
							where language=%s and name=%s ''',
							( media['language'], subj ) )
						id = cur.fetchone()
						if not id:
							cur.execute('''insert into lf_subject
								(language, name) values (%s, %s) ''',
								( media['language'], subj ) )
							cur.execute('''select last_insert_id() ''')
							id = cur.fetchone()
						id, = id
						cur.execute('''replace into lf_media_subject
							(subject_id, media_id) values (%s, %s) ''',
							(id, media['id'].bytes) )
			except MySQLdbError as e:
				db.rollback()
				cur.close()
				return str(e), 400
			result.append( {'id':str(media['id']), 'version':version} )
		except KeyError:
			return 'A mere user cannot create a new media object', 403

		# We will never reach this in case of a failure.
		db.commit()
		cur.close()
		result = { 'lf:created_media' : result }
		if request.accept_mimetypes.best_match(
				['application/xml', 'application/json']) == 'application/json':
			return jsonify(result=result)
		return xmlify(result=result)
	
	return ''



@app.route('/admin/series/', methods=['PUT'])
def admin_series_put():
	'''This method provides you with the functionality to set series. It
	will create a new dataset or a new version if one with the given
	identifier already exists.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:series": [
			{
				"lf:parent_version": null, 
				"dc:source": null, 
				"lf:version": 0, 
				"lf:source_key": null, 
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
			}
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/" 
				xmlns:lf="http://lernfunk.de/terms">
			<!-- TODO -->
		</data>


	NOTICES:
	 * If the identifier is ommittet a new id is generated automatically. 
	 * Only administrators and editors can change the ownership of a series.
	 * You cannot modify a specific version. Insted a new version is created
	   automatically. If you really want to get rid of a specific version: Be
	   admin, delete the old one and create a new version. If you are no admin:
	   Create a new version based on an old one and ask someone who is admin to
	   delete the old one.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	# If the user is no editor (or admin) we want to know which objects he is
	# allowed to modify. In any case, he is not allowed to add new data.
	access_to_media = []
	access_to_series = []
	if not user.is_editor():
		groups = 'or group_id in (' + ','.join( user.groups ) + ') ' \
				if user.groups else ''
		q ='''select media_id, series_id from lf_access 
				where ( user_id = %i %s) 
				and write_access ''' % ( user.id, groups )
		cur.execute( q )
		for ( media_id, series_id ) in cur.fetchall():
			if media_id:
				access_to_media.append( media_id )
			elif series_id:
				access_to_series.append( series_id )

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for series in data.getElementsByTagName( 'lf:series' ):
				s = {}
				s['id'] = uuid.UUID(xml_get_text(series, 'dc:identifier'))
				if not ( s['id'] or user.is_editor() ):
					return 'You are not allowed to create new series', 403

				s['description']    = xml_get_text(series, 'dc:description')
				s['language']       = xml_get_text(series, 'dc:language', True)
				s['owner']          = xml_get_text(series, 'lf:owner')
				s['parent_version'] = xml_get_text(series, 'lf:parent_version')
				s['published']      = 1 \
						if xml_get_text(series, 'lf:published', True) else 0
				s['source']         = xml_get_text(series, 'source')
				s['source_key']     = xml_get_text(series, 'lf:source_key')
				s['source_system']  = xml_get_text(series, 'lf:source_system')
				s['title']          = xml_get_text(series, 'dc:title')
				s['visible']        = xml_get_text(series, 'lf:visible', True)
				s['date']           = xml_get_text(series, 'dc:date', True)

				# Additional relations:
				m['subject']        = [ s.childNodes[0].data \
						for s in series.getElementsByTagNameNS(XML_NS_DC,'subject') ]
				m['publisher']      = [ int(p.childNodes[0].data) \
						for p in series.getElementsByTagNameNS(XML_NS_DC,'publisher') ]
				m['creator']        = [ int(c.childNodes[0].data) \
						for c in series.getElementsByTagNameNS(XML_NS_LF,'creator') ]
				m['media']          = [ c.childNodes[0].data \
						for c in series.getElementsByTagNameNS(XML_NS_LF,'media_id') ]
				sqldata.append( s )
		except (AttributeError, IndexError):
			return 'Invalid series data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new server data
		try:
			data = data['lf:series']
		except KeyError:
			# Assume that there is only one server
			data = [data]
		for series in data:
			s = {}
			try:
				if series.get('dc:identifier'):
					s['id'] = uuid.UUID(series['dc:identifier'])
				elif not user.is_editor():
					return 'You are not allowed to create new serieso', 403

				s['description']    = series.get('dc:description')
				s['language']       = series['dc:language']
				s['owner']          = series.get('lf:owner')
				s['parent_version'] = series.get('lf:parent_version')
				s['published']      = 1 if series['lf:published'] else 0
				s['source']         = series.get('source')
				s['source_key']     = series.get('lf:source_key')
				s['source_system']  = series.get('lf:source_system')
				s['title']          = series.get('dc:title')
				s['visible']        = series['lf:visible']
				s['date']           = series['dc:date']

				# Additional relations:
				s['subject']        = series.get('dc:subject')
				s['publisher']      = series.get('dc:publisher')
				s['creator']        = series.get('lf:creator')
				s['media']          = series.get('lf:media_id')

				sqldata.append( m )
			except KeyError:
				return 'Invalid server data', 400

	# Check some data
	for series in sqldata:
		try:
			if not series.get('date'):
				series['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			else:
				try:
					# Assume ISO datetime format (YYYY-MM-DD HH:MM:SS)
					datetime.strptime(series['date'], '%Y-%m-%d %H:%M:%S')
				except ValueError:
					# Check RFC2822 datetime format instead
					# (Do not use , for separating weekday and month!)
					series['date'] = datetime.fromtimestamp(
							email.utils.mktime_tz(email.utils.parsedate_tz(val))
							).strftime("%Y-%m-%d %H:%M:%S")
			series['owner'] = int(series['owner'])
			# Check relations:
			if series.get('publisher'):
				series['publisher'] = [ int(pub) for pub in series['publisher'] ]
			if series.get('creator'):
				series['creator'] = [ int(creator) for creator in series['creator'] ]
			if series.get('media'):
				series['media'] = [ uuid.UUID(m) for m in series['media'] ]
		except (KeyError, ValueError):
			return 'Invalid server data', 400

	# Admins and editors are allowed to create new series and change the
	# ownership of all existing ones. Thus we do not have to check their
	# permissions on each object:
	result = []
	if user.is_editor:
		for series in sqldata:
			# If there is no id, we create a new one:
			if not series.get('id'):
				series['id'] = uuid.uuid4()
			try:
				# Get next version for this series. Since this happens in a
				# transaction the value will not change between transactions.
				cur.execute('''select max(version) from lf_series 
					where id = x'%s' ''' % series['id'].hex )
				(version,) = cur.fetchone()
				version = 0 if ( version is None ) else version + 1
				cur.execute('''insert into lf_series
					(id, version, parent_version, language, title, description,
					owner, editor, timestamp_created, published, source, visible,
					source_system, source_key) 
					values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ''',
					( series['id'].bytes,
						version,
						series.get('parent_version'),
						series['language'],
						series.get('title'),
						series.get('description'),
						series.get('owner'),
						user.id,
						series['date'],
						series['published'],
						series.get('source'),
						series['visible'],
						series.get('source_system'),
						series.get('source_key') ) )

				# Add relations
				if series.get('published'):
					for pub in series['published']:
						cur.execute('''insert into lf_series_publisher
							(series_id, organization_id, series_version)
							values (%s, %s, %s) ''',
							( series['id'].bytes, pub, version ) )
				if series.get('creator'):
					for creator in series['creator']:
						cur.execute('''insert into lf_series_creator
							(series_id, user_id, series_version)
							values (%s, %s, %s) ''',
							( series['id'].bytes, creator, version ) )

				if series.get('subject'):
					for subj in series['subject']:
						cur.execute('''select id from lf_subject
							where language=%s and name=%s ''',
							( series['language'], subj ) )
						id = cur.fetchone()
						if not id:
							cur.execute('''insert into lf_subject
								(language, name) values (%s, %s) ''',
								( series['language'], subj ) )
							cur.execute('''select last_insert_id() ''')
							id = cur.fetchone()
						id, = id
						cur.execute('''replace into lf_series_subject
							(subject_id, series_id) values (%s, %s) ''',
							(id, series['id'].bytes) )

				if series.get('media'):
					for media_id in series['media']:
						cur.execute('''insert into lf_media_series
							(series_id, media_id, series_version) values (%s,%s,%s) ''',
							(series['id'].bytes, media_id.bytes, version) )
			except MySQLdbError as e:
				db.rollback()
				cur.close()
				return str(e), 400
			result.append( {'id':str(series['id']), 'version':version} )

		# We will never reach this in case of a failure.
		db.commit()
		cur.close()
		result = { 'lf:created_series' : result }
		if request.accept_mimetypes.best_match(
				['application/xml', 'application/json']) == 'application/json':
			return jsonify(result=result)
		return xmlify(result=result)


	# If a simple user tries to update a series object (Create a new version).
	# We have to check if he is (a) the owner of the series or (b) has write
	# access defined in lf_access.
	else:
		try:
			# Get owner
			cur.execute('''select owner from lf_latest_series 
				where id = x'%s' ''' % series['id'])
			owner = int( cur.fetchone() )
			if not ( series['id'].bytes in access_to_series or user.id == owner ):
				return 'You are not allowed to modify this series object', 403
			if owner != series['owner']:
				return 'You are not allowed to change the ownership', 403
			try:
				# Get next version for this series. Since this happens in a
				# transaction the value will not change between transactions.
				cur.execute('''select max(version) from lf_series 
					where id = x'%s' ''' % series['id'].hex )
				(version,) = cur.fetchone()
				version = 0 if ( version is None ) else version + 1
				cur.execute('''insert into lf_series
					(id, version, parent_version, language, title, description,
					owner, editor, timestamp_created, published, source, visible,
					source_system, source_key) 
					values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ''',
					( series['id'].bytes,
						version,
						series.get('parent_version'),
						series['language'],
						series.get('title'),
						series.get('description'),
						series.get('owner'),
						user.id,
						series['date'],
						series['published'],
						series.get('source'),
						series['visible'],
						series.get('source_system'),
						series.get('source_key') ) )

				# Add relations
				if series.get('published'):
					for pub in series['published']:
						cur.execute('''insert into lf_series_publisher
							(series_id, organization_id, series_version)
							values (%s, %s, %s) ''',
							( series['id'].bytes, pub, version ) )
				if series.get('creator'):
					for creator in series['creator']:
						cur.execute('''insert into lf_series_creator
							(series_id, user_id, series_version)
							values (%s, %s, %s) ''',
							( series['id'].bytes, creator, version ) )

				if series.get('subject'):
					for subj in series['subject']:
						cur.execute('''select id from lf_subject
							where language=%s and name=%s ''',
							( series['language'], subj ) )
						id = cur.fetchone()
						if not id:
							cur.execute('''insert into lf_subject
								(language, name) values (%s, %s) ''',
								( series['language'], subj ) )
							cur.execute('''select last_insert_id() ''')
							id = cur.fetchone()
						id, = id
						cur.execute('''replace into lf_series_subject
							(subject_id, series_id) values (%s, %s) ''',
							(id, series['id'].bytes) )

				if series.get('media'):
					for media_id in series['media']:
						cur.execute('''insert into lf_media_series
							(series_id, media_id, series_version) values (%s,%s,%s) ''',
							(series['id'].bytes, media_id.bytes, version) )

			except MySQLdbError as e:
				db.rollback()
				cur.close()
				return str(e), 400
			result.append( {'id':str(series['id']), 'version':version} )
		except KeyError:
			return 'A mere user cannot create a new series object', 403

		# We will never reach this in case of a failure.
		db.commit()
		cur.close()
		result = { 'lf:created_series' : result }
		if request.accept_mimetypes.best_match(
				['application/xml', 'application/json']) == 'application/json':
			return jsonify(result=result)
		return xmlify(result=result)
	
	return ''



@app.route('/admin/server/', methods=['PUT'])
def admin_server_put():
	'''This method provides you with the functionality to set server data. It
	will create a new dataset or replace an old one if one with the given
	identifier/format already exists.
	Only administrators are allowed to add/modify server data.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:server": [
				{
					"lf:format": "video/mpeg", 
					"lf:id": "myserver", 
					"lf:uri_pattern": "http://myserver.com/{source_key}.mpg"
				}, 
				{ ... }
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/" 
				xmlns:lf="http://lernfunk.de/terms">
			<lf:server>
				<lf:format>video/mpeg</lf:format>
				<lf:id>myserver</lf:id>
				<lf:uri_pattern>http://myserver.com/{source_key}.mpg</lf:uri_pattern>
			</lf:server>
			...
		</data>

	** URI PATTERN **

	You can use the following placeholders in the URI pattern:
	  =================== ========================
	  {file_id}           Fill in file identifier
	  {format}            Fill in file format
	  {media_id}          Fill in media identifier
	  {source_key}        Fill in file source key
	  {media_source_key}  Fill in media source key
	  =================== ========================

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	# Only admins are allowed to modify server.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to modify server', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	# RegExp to check data with:
	idcheck  = re.compile('^[\w\-_\.:]+$')
	fmtcheck = re.compile('^[\w\-\.\/]+$')

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for server in data.getElementsByTagName( 'lf:server' ):
				id = xml_get_text(server, 'lf:id')
				if not idcheck.match(id):
					return 'Bad identifier for server: %s' % id, 400
				fmt = xml_get_text(server,'lf:format',True)
				if not fmtcheck.match(fmt):
					return 'Bad format for server: %s' % fmt, 400
				uri_pattern = xml_get_text(server,'lf:uri_pattern',True)
				sqldata.append( ( id, fmt, uri_pattern ) )
		except (AttributeError, IndexError):
			return 'Invalid server data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new server data
		try:
			data = data['lf:server']
		except KeyError:
			# Assume that there is only one server
			data = [data]
		for server in data:
			try:
				id = server['lf:id']
				if not idcheck.match(id):
					return 'Bad identifier for server: %s' % id, 400
				fmt = server['lf:format']
				if not fmtcheck.match(fmt):
					return 'Bad format for server: %s' % fmt, 400
				sqldata.append( ( id, fmt, server['lf:uri_pattern'] ) )
			except KeyError:
				return 'Invalid server data', 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	affected_rows = 0
	try:
		affected_rows = cur.executemany('''insert into lf_server 
			(id, format, uri_pattern) values (%s, %s, %s) 
			on duplicate key update uri_pattern=values(uri_pattern)''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/subject/', methods=['PUT'])
def admin_subject_put():
	'''This method provides you with the functionality to set subject data. It
	will create a new dataset or replace an old one if one with the given
	identifier already exists.
	Only administrators and editors are allowed to add/modify subject data.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:subject": [
			{
				"lf:name": "Computer Science", 
				"dc:language": "en", 
				"lf:id": 1
			}, 
			{ ... }
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:subject>
				<lf:name>Computer Science</lf:name>
				<dc:language>en</dc:language>
				<lf:id>1</lf:id>
			</lf:subject>
			...
		</data>

	The id can be ommittet. In that case a new id is generated automatically.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	# _Only_ admins and editors are allowed to create/modify subjects.
	try:
		if not get_authorization( request.authorization ).is_editor():
			return 'Only admins and editors are allowed to create/modify subjects', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	# RegExp to check data with:
	fmtcheck = re.compile('^[\w\-\.\/]+$')

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for subject in data.getElementsByTagName( 'lf:subject' ):
				try:
					id = int(xml_get_text(subject,'lf:id'))
				except TypeError:
					id = None
				except ValueError:
					return 'Bad identifier for subject', 400
				lang = xml_get_text(subject,'dc:language')
				if not lang_regex_full.match(lang):
					return 'Bad language tag: %s' % lang, 400
				name = xml_get_text(subject,'lf:name',True)
				sqldata.append( ( id, lang, name ) )
		except (AttributeError, IndexError):
			return 'Invalid subject data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new subject data
		try:
			data = data['lf:subject']
		except KeyError:
			# Assume that there is only one subject dataset
			data = [data]
		for subject in data:
			try:
				try:
					id = int(subject['lf:id'])
				except KeyError:
					id = None
				except ValueError:
					return 'Bad identifier for subject', 400
				lang = subject['dc:language']
				if not lang_regex_full.match(lang):
					return 'Bad language tag: %s' % fmt, 400
				sqldata.append( ( id, lang, subject['lf:name'] ) )
			except KeyError:
				return 'Invalid subject data', 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	affected_rows = 0
	try:
		affected_rows = cur.executemany('''insert into lf_subject
			(id, language, name) values (%s, %s, %s) 
			on duplicate key update 
			language=values(language), name=values(name) ''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/file/', methods=['PUT'])
def admin_file_put():
	'''This method provides you with the functionality to set file data. It
	will create a new dataset or replace an old one if one with the given
	identifier already exists.
	Only administrators and editors are allowed to add/modify file data.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:file": [{
				"lf:source_system": "matterhorn13@uos", 
				"lf:source_key": "ba8b331d-6adc-11e2-8b4e-047d7b0f869a", 
				"dc:identifier": "ba8b380b-6adc-11e2-8b4e-047d7b0f869a", 
				"lf:quality": "high-quality",
				"dc:format": "application/matterhorn13", 
				"lf:source": "http://video.example.com/",
				"lf:type": "vga", 
				"lf:media_id": "BA8488D1-6ADC-11E2-8B4E-047D7B0F869A", 
				"lf:uri": "http://video.example.com/watch/ba8b331d-6adc-11e2-8b4e-047d7b0f869a/"
				"lf:server_id": "exampleserver"
			}]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:file>
				<lf:source_key>bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb</lf:source_key>
				<dc:identifier>bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb</dc:identifier>
				<dc:format>video/mpeg</dc:format>
				<lf:media_id>BA8488D1-6ADC-11E2-8B4E-047D7B0F869A</lf:media_id>
				<lf:server_id>exampleserver<lf:server_id>
			</lf:file>
		</data>
	
	IMPORTANT NOTICE:
	 | There should be either a uri or a server, not both. If both fields are
	 | set the server is simply ignored. If no uri is set the uri will be
	 | generated dynamically (have a look at the server uri_pattern for more
	 | information). If none of them is set the insert will fail.

	Optional fields are source, source_system, source_key, quality and type.

	INTERNAL NOTICE:
		The id can also be omitted, in which case a new uuid is generated
		automatically. However, you wont be able to get this id by
		LAST_INSERT_ID() as it is generated by a database trigger.

	The data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	# _Only_ admins and editors are allowed to create/modify files.
	try:
		if not get_authorization( request.authorization ).is_editor():
			return 'Only admins and editors are allowed to create/modify files', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject large chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in ['application/x-www-form-urlencoded', 
			'multipart/form-data']:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	# RegExp to check data with:
	fmtcheck = re.compile('^[\w\-\.\/]+$')

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for file in data.getElementsByTagName( 'lf:file' ):
				d = {}
				try:
					d['id'] = uuid.UUID(xml_get_text(file,'dc:identifier')).bytes
				except (AttributeError, IndexError, TypeError):
					pass
				d['media_id']      = uuid.UUID(xml_get_text(file,'lf:media_id')).bytes
				d['format']        = xml_get_text(file,'dc:format',True)
				d['quality']       = xml_get_text(file,'lf:quality')
				d['source']        = xml_get_text(file,'lf:source')
				d['source_system'] = xml_get_text(file,'lf:source_system')
				d['source_key']    = xml_get_text(file,'lf:source_key')
				d['type']          = xml_get_text(file,'lf:type')
				d['uri']           = xml_get_text(file,'lf:uri')
				if not d.get('uri'):
					d['server_id'] = xml_get_text(file,'lf:server_id',True)
				sqldata.append( ( d.get('id'), d['media_id'], 
					d['format'], d.get('type'), d.get('quality'), d.get('server_id'),
					d.get('uri'), d.get('source'), d.get('source_system'), 
					d.get('source_key') ) )
		except (AttributeError, IndexError):
			return 'Invalid subject data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new subject data
		try:
			data = data['lf:file']
		except KeyError:
			# Assume that there is only one subject dataset
			data = [data]
		for file in data:
			try:
				d = {}
				try:
					d['id'] = uuid.UUID(file.get('dc:identifier')).bytes
				except TypeError:
					pass
				except ValueError:
					return 'Bad identifier', 400
				try:
					d['media_id'] = uuid.UUID(file.get('lf:media_id')).bytes
				except ValueError:
					return 'Bad media identifier', 400
				d['format'] = file['dc:format']
				d['quality'] = file.get('lf:quality')
				d['source'] = file.get('lf:source')
				d['source_key'] = file.get('lf:source_key')
				d['source_system'] = file.get('lf:source_system')
				d['type'] = file.get('lf:type')
				try:
					d['uri'] = file['lf:uri']
				except KeyError:
					d['server_id'] = file['lf:server_id']

				sqldata.append( ( d.get('id'), d['media_id'], 
					d['format'], d['type'], d['quality'], d.get('server_id'),
					d.get('uri'), d['source'], d['source_system'], 
					d['source_key'] ) )
			except KeyError:
				return 'Invalid subject data', 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	affected_rows = 0
	try:
		affected_rows = cur.executemany('''insert into lf_file
			(id, media_id, format, type, quality, server_id, uri, source,
				source_system, source_key) 
			values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
			on duplicate key update 
			media_id=values(media_id), format=values(format) , type=values(type),
			quality=values(quality), server_id=values(server_id), uri=values(uri),
			source=values(source), source_system=values(source_system),
			source_key=values(source_key)''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/organization/', methods=['PUT'])
def admin_organization_put():
	'''This method provides you with the functionality to set organizations. It
	will create a new dataset or replace an old one if one with the given
	identifier already exists.
	Only administrators and editors are allowed to add/modify subject data.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:organization": [
			{
				"lf:name": "Universit\u00e4t Osnabr\u00fcck", 
				"lf:parent_organization_id": null, 
				"vcard_uri": null, 
				"dc:identifier": 1
			}
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:organization>
				<lf:name>Universität Osnabrück</lf:name>
				<dc:identifier>1</dc:identifier>
			</lf:organization>
		</data>

	The id can be omitted. In that case a new id is generated automatically.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	# _Only_ admins and editors are allowed to create/modify subjects.
	try:
		if not get_authorization( request.authorization ).is_editor():
			return 'Only admins and editors are allowed to create/modify subjects', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject large chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	# RegExp to check data with:
	fmtcheck = re.compile('^[\w\-\.\/]+$')

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for org in data.getElementsByTagName( 'lf:organization' ):
				id = xml_get_text(org, 'dc:identifier')
				if not id is None:
					id = int(id)
				parent_id = xml_get_text(org,'lf:parent_organization_id')
				if not parent_id is None:
					parent_id = int(parent_id)
				vcard_uri = xml_get_text(org,'lf:vcard_uri')
				name = xml_get_text(org,'lf:name')
				sqldata.append( ( id, name, vcard_uri, parent_id ) )
		except (AttributeError, IndexError, ValueError):
			return 'Invalid organization data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			data = data['lf:organization']
		except KeyError:
			# Assume that there is only one dataset
			data = [data]
		for org in data:
			try:
				id = int(org['dc:identifier']) if org.get('dc:identifier') else None
				parent_id = int(org['lf:parent_organization_id']) \
						if org.get('lf:parent_organization_id') else None
				vcard_uri = org.get('lf:vcard_uri')
				name = org['lf:name']
				sqldata.append( ( id, name, vcard_uri, parent_id ) )
			except KeyError:
				return 'Invalid organization data', 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	affected_rows = 0
	try:
		affected_rows = cur.executemany('''insert into lf_organization
			(id, name, vcard_uri, parent_organization) values (%s, %s, %s, %s) 
			on duplicate key update 
			name=values(name), vcard_uri=values(vcard_uri), 
			parent_organization=values(parent_organization) ''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/group/', methods=['PUT'])
def admin_group_put():
	'''This method provides you with the functionality to set group data. It
	will create a new dataset or replace an old one if one with the given
	identifier already exists.
	Only administrators are allowed to add/modify groups.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:group": [
			{
				"lf:name": "test", 
			}
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:group>
				<lf:name>test</lf:name>
				<dc:identifier>42</dc:identifier>
			</lf:group>
		</data>

	The id can be omitted. In that case a new id is generated automatically.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to create/modify groups', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	cur.execute( '''select id, name from lf_group 
			where name in ("admin", "editor", "public") ''' )
	restricted_ids = {}
	for id, name in cur.fetchall():
		restricted_ids[id] = name

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for group in data.getElementsByTagName( 'lf:groups' ):
				try:
					id = int(group.getElementsByTagName('dc:identifier')[0]\
							.childNodes[0].data)
				except IndexError:
					id = None
				if id in restricted_ids.keys():
					return 'Cannot modify fixed group "%s"' % restricted_ids[id], 400
				name = group.getElementsByTagName('lf:name')[0].childNodes[0].data
				if name in ['admin', 'editor', 'public']:
					return 'Cannot create fixed group "%s"' % name, 400
				sqldata.append( ( id, name ) )
		except (AttributeError, IndexError, ValueError):
			return 'Invalid group data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			data = data['lf:group']
		except KeyError:
			# Assume that there is only one dataset
			data = [data]
		for group in data:
			try:
				id = int(group['dc:identifier']) if group.get('dc:identifier') else None
				if id in restricted_ids.keys():
					return 'Cannot modify fixed group "%s"' % restricted_ids[id], 400
				name = group['lf:name']
				if name in ['admin', 'editor', 'public']:
					return 'Cannot create fixed group "%s"' % name, 400
				sqldata.append( ( id, name ) )
			except KeyError:
				return 'Invalid group data', 400

	affected_rows = 0
	try:
		affected_rows = cur.executemany('''insert into lf_group
			(id, name) values (%s, %s) 
			on duplicate key update name=values(name) ''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/user/', methods=['PUT'])
def admin_user_put():
	'''This method provides you with the functionality to set user. It
	will create a new dataset or replace an old one if one with the given
	identifier already exists.
	Only administrators are allowed to add/modify any user. Other users may only
	modify their own data.

	The data can either be JSON or XML.

	JSON example::

		{
			"lf:user": [
			{
				"dc:identifier": 42,
				"lf:name": "testuser",
				"lf:access": "administrators only",
				"lf:realname": null,
				"lf:email": null,
				"lf:vcard_uri": null
			}
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:group>
				<lf:name>test</lf:name>
				<dc:identifier>42</dc:identifier>
			</lf:group>
		</data>

	The id can be omitted. In that case a new id is generated automatically.

	The access data can be given either as integer or as their string
	representation. The latter is automatically converted to an integer.
	Possible values for the access field are::

		1 : 'public'
		2 : 'login required'
		3 : 'editors only'
		4 : 'administrators only'

	IMPORTANT NOTICE (Passwords):
	 | Although a password is part of a users data it cannot be set along with
	 | the rest of the “normal” user data as it more important. If a new user is
	 | created, the password is set to NULL which means that the user cannot log
	 | into to system. A password can then be set by using /admin/user/passwd.

	IMPORTANT NOTICE (Username):
	 | Usernames are as unique as user ids attempting to insert an already
	 | existing username will fail. Furthermore the username cannot be modified
	 | afterwards to ensure that one username always identifies the same user.
	 | Thus all updates will fail if there is a username given which differes
	 | from the old one.

	IMPORTANT NOTICE (Multiple datasets):
	 | As with all the other PUT methods this method can be used to insert
	 | multiple datasets. However, it can only be used to insert multiple
	 | datasets of _one_ type. This means that if one dataset contains an
	 | username the data is inserted explicitly as new data and an omitted
	 | username will result in a failure. The same goes for passwords.

	The data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication.
	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401

	# Deny access for public users:
	if user.name == 'public':
		return 'You cannot modify your user if you are not logged in', 401

	# Check content length and reject lange chunks of data
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400
	
	set_passwd = False
	is_insert  = False

	# Human readable mapping for user access rights
	accessmap = {
			'public' : 1,
			'login required' : 2,
			'editors only' : 3,
			'administrators only' : 4,
			'1' : 1,
			'2' : 2,
			'3' : 3,
			'4' : 4
			}

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for udata in data.getElementsByTagName( 'lf:user' ):
				u = {}
				u['id']       = xml_get_text(udata, 'dc:coverage')
				if u['id']:
					u['id'] = int(u['id'])
				u['name']       = xml_get_text(udata, 'lf:name', True)
				u['access']     = accessmap[xml_get_text(udata, 'lf:access')]
				u['realname']   = xml_get_text(udata, 'lf:realname')
				u['vcard']      = xml_get_text(udata, 'lf:vcard_uri')
				u['email']      = xml_get_text(udata, 'lf:email')
				sqldata.append( u )
		except (AttributeError, IndexError, ValueError):
			return 'Invalid group data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			data = data['lf:user']
		except KeyError:
			# Assume that there is only one dataset
			data = [data]
		for udata in data:
			try:
				u = {}
				u['id']       = int(udata['dc:identifier']) \
						if udata.get('dc:identifier') else None
				u['name']     = udata['lf:name']
				u['access']   = accessmap[udata['lf:access']]
				u['realname'] = udata.get('lf:realname')
				u['vcard']    = udata.get('lf:vcard_uri')
				u['email']    = udata.get('lf:email')
				sqldata.append( u )
			except (KeyError, ValueError):
				return 'Invalid group data', 400

	# Check data
	for udata in sqldata:
		if not user.is_admin() and udata['id'] != user.id:
			return 'You have to be admin to modify another user', 400
		if udata['name'] in ['admin', 'public']:
			return 'Cannot create fixed group "%s"' % udata['name'], 400
		if not ( udata['email'] is None or '@' in udata['email'] ):
			return 'Invalid email address “%s”' % udata['email'], 400
		if not username_regex_full.match(udata['name']):
			return 'Invalid username “%s”' % udata['name'], 400

	# Request data
	db = get_db()
	cur = db.cursor()

	result = []
	try:
		# check username
		for udata in sqldata:
			# Check if id has another username:
			cur.execute('''select id from lf_user 
					where ( id = %(id)i and name != "%(name)s" ) 
					or ( name = "%(name)s" and id != %(id)i ) ''' %
					{ 'id':udata['id'], 'name':udata['name'] } )
			if cur.fetchone():
				db.rollback()
				cur.close()
				return 'You cannot change a username', 400

			cur.execute('''insert into lf_user
				(id, name, vcard_uri, realname, email, access)
				values (%s, %s, %s, %s, %s, %s)
				on duplicate key update id=LAST_INSERT_ID(id), 
					vcard_uri=values(vcard_uri), realname=values(realname),
					email=values(realname), access=values(access) ''',
					( udata['id'], udata['name'], udata['vcard'], udata['realname'],
					udata['email'], udata['access'] ) )
			
			cur.execute('''select id from lf_user where name = %s''', udata['name'])
			(id,) = cur.fetchone()
			result.append( {'id':id, 'name':udata['name']} )

	except MySQLdbError as e:
		db.rollback()
		cur.close()
		return str(e), 400

	# We will never reach this in case of a failure.
	db.commit()
	cur.close()
	result = { 'lf:created_user' : result }
	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result)
	return xmlify(result=result)



@app.route('/admin/user/passwd', methods=['PUT'])
def admin_user_passwd_put():
	'''This method provides you with the functionality to set a users password.
	A users password can only be set by himself (assuming that a password was
	already set for him and thus he can authorize himself) or by an
	administrator.
	create a new dataset or replace an old one if one with the given
	identifier already exists.
	Only administrators are allowed to add/modify any user. Other users may only
	modify their own data.

	The data can either be JSON or XML.

	JSON example::

		{
			"lf:user_password": [
			{
				"lf:user_id": 42,
				"lf:password": "SECRET_PASSWORD"
			}
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:user_password>
				<lf:user_id>42</lf:user_id>
				<lf:password>SECRET_PASSWORD</lf:password>
			</lf:group>
		</data>

	The data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication.
	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401

	# Deny access for public users:
	if user.name == 'public':
		return 'You cannot modify your password if you are not logged in', 401

	# Check content length and reject lange chunks of data
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for up in data.getElementsByTagName( 'lf:user_password' ):
				u = {}
				u['user_id']  = int(xml_get_text(up, 'lf:user_id'))
				u['password'] = xml_get_text(up, 'lf:password')
				sqldata.append( u )
		except (AttributeError, IndexError, ValueError):
			return 'Invalid data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			data = data['lf:user_password']
		except KeyError:
			# Assume that there is only one dataset
			data = [data]
		for udata in data:
			try:
				u = {}
				u['user_id']  = int(udata['lf:user_id'])
				u['password'] = udata.get('lf:password')
				sqldata.append( u )
			except (KeyError, ValueError):
				return 'Invalid password data', 400

	# Check and prepare data
	import hashlib
	h = hashlib.sha512()
	sqldata_ready = []
	for data in sqldata:
		if not user.is_admin() and data['user_id'] != user.id:
			return 'Only admins are allowed to edit other peoples accounts', 401
		# Generate salt
		salt = None
		password = None
		if not data['password'] is None:
			salt = ''
			for c in os.urandom(32):
				c = ord(c) % len(printable_chars)
				salt += printable_chars[c]
			h.update( data['password'] + salt )
			password = h.digest()
		sqldata_ready.append( ( salt, password, data['user_id'] ) )

	# Request data
	db = get_db()
	cur = db.cursor()

	affected_rows = 0
	try:
		cur.executemany('''update lf_user
				set salt=%s, passwd=%s
				where id=%s''', sqldata_ready )

	except MySQLdbError as e:
		db.rollback()
		cur.close()
		return str(e), 400

	# We will never reach this in case of a failure.
	db.commit()
	cur.close()

	if affected_rows:
		return '', 201
	return '', 200
				




''' ----------------------------------------------------------------------------
	End of method which effect entities. The following methods are for
	relations. Access is still only granted to administrators. Other user have
	to create a new entity version without the specific connector.
---------------------------------------------------------------------------- '''


@app.route('/admin/access/', methods=['PUT'])
def admin_access_put():
	'''This method provides you with the functionality to set access rights. It
	will create a new dataset or replace an old one if one with the given
	identifier already exists.
	Only administrators are allowed to add/modify access rights.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:access": [
			{
				"lf:media_id"     : "6EB7CD04-7F69-11E2-9DE9-047D7B0F869A",
				"lf:series_id"    : null,
				"lf:group_id"     : null,
				"lf:user_id"      : 1,
				"lf:read_access"  : 1,
				"lf:write_access" : 0
			}
			]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:lf="http://lernfunk.de/terms">
			<lf:access>
				…
			</lf:access>
		</data>

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to create/modify access data', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400
	
	# Request data
	db = get_db()
	cur = db.cursor()

	sqldata = []
	if type == 'application/xml':
		try:
			data = parseString(data)
			for access in data.getElementsByTagNameNS(XML_NS_LF, 'access'):
				id       = xml_get_text(access, 'dc:identifier')
				if not id is None:
					id = int(id)
				media_id = xml_get_text(access, 'lf:media_id')
				if not media_id is None:
					media_id = uuid.UUID(media_id)
				series_id = xml_get_text(access, 'lf:series_id')
				if not series_id is None:
					series_id = uuid.UUID(series_id)
				user_id  = xml_get_text(access, 'lf:user_id')
				if not user_id is None:
					user_id = int(user_id)
				group_id = xml_get_text(access, 'lf:group_id')
				if not group_id is None:
					group_id = int(group_id)
				read_access  = is_true(xml_get_text(access, 'lf:read_access' ))
				write_access = is_true(xml_get_text(access, 'lf:write_access'))

				sqldata.append( u )
		except:
			return 'Invalid group data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			data = data['lf:access']
		except KeyError:
			# Assume that there is only one dataset
			data = [data]
		for access in data:
			try:
				id = int(access['dc:identifier']) \
						if access.get('dc:identifier') else None
				media_id = uuid.UUID(access['lf:media_id']) \
						if access.get('lf:media_id') else None
				series_id = uuid.UUID(access['lf:series_id']) \
						if access.get('lf:series_id') else None
				user_id = int(access['lf:user_id']) \
						if access.get('lf:user_id') else None
				group_id = int(access['lf:group_id']) \
						if access.get('lf:group_id') else None
				read_access  = 1 if access.get('lf:read_access') else 0
				write_access = 1 if access.get('lf:write_access') else 0
				sqldata.append( ( id, media_id, series_id, user_id, group_id,
					read_access, write_access ) )
			except KeyError:
				return 'Invalid group data', 400

	affected_rows = 0
	try:
		affected_rows = cur.executemany('''insert into lf_access
			(id, media_id, series_id, group_id, user_id, read_access, write_access)
			values (%s,%s,%s,%s,%s,%s,%s) 
			on duplicate key update media_id=values(media_id),
				series_id=values(series_id), user_id=values(user_id),
				group_id=values(group_id), read_access=values(read_access),
				write_access=values(write_access) ''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/series/media/', methods=['PUT'])
def admin_series_media_put():
	'''This method provides you with the functionality to connect media and
	series. Every time the connection between series and media is changed a new
	series version is created.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:series_media": [{
			"lf:series_id": "AAAAAAAA-7F69-11E2-9DE9-047D7B0F869A",
			"lf:series_version": 2,
			"lf:media_id": [ "6EB7CD04-7F69-11E2-9DE9-047D7B0F869A" ]
			}]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:series_media>
				<lf:series_id>aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa</lf:series_id>
				<lf:series_version>1</lf:series_version>
				<lf:media_id>aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa</lf:media_id>
				<lf:media_id>bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb</lf:media_id>
			</lf:series_media>
		</data>

	IMPORTANT NOTICE: If you send JSON/XML data to set up new series media
	 | connections, the old ones will not be cloned. Thus they should be
	 | included in the new data if you want to keep them. If you simply want to
	 | add a new media object to a series, use the POST method.

	NOTICE: series_version is used to determine the parent version. It can be
	 | omittet in which case the latest version of the series is used as parent.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401

	# Deny access for public users:
	if not user or user.name == 'public':
		return 'You have to authenticate yourself to modify a series', 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400
		
	# Request data
	db = get_db()
	cur = db.cursor()
	
	# If the user is no editor (or admin) we want to know which objects he is
	# allowed to modify. In any case, he is not allowed to add new data.
	access = []
	if not user.is_editor():
		groups = 'or group_id in (' + ','.join( user.groups ) + ') ' \
				if user.groups else ''
		q ='''select series_id from lf_access 
				where ( user_id = %i %s) and series_id 
				and write_access ''' % ( user.id, groups )
		cur.execute( q )
		for (series_id,) in cur.fetchall():
			access.append( series_id )

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for ms in data.getElementsByTagNameNS(XML_NS_LF, 'series_media'):
				series_id = uuid.UUID(xml_get_text(ms,'lf:series_id'))
				series_version = xml_get_text(ms,'lf:series_version')
				media = [ uuid.UUID(id.childNodes[0].data) \
					for id in ms.getElementsByTagNameNS(XML_NS_LF, 'media_id') ]
				sqldata.append( (series_id, series_version, media) )
		except (AttributeError, IndexError, ValueError):
			return 'Invalid group data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return 'Error parsing JSON data: %s' % e.message, 400
		# Get array of new data
		try:
			for ms in data['lf:series_media']:
				series_id = uuid.UUID(ms['lf:series_id'])
				if not user.is_editor() and series_id.bytes in access:
					cur.close()
					return 'You cannot modify this series', 401
				series_version = ms.get('lf:series_version')
				media = ms['lf:media_id']
				if not isinstance(media, list):
					media = [ media ]
				media = [ uuid.UUID(id) for id in media ]
				sqldata.append( (series_id, series_version, media) )
		except (KeyError, TypeError, ValueError):
			return 'Invalid data', 400

	affected_rows = 0
	try:
		for (series_id, version, media) in sqldata:
			# First: Create new version of series
			cur.execute('''select id, version, parent_version, title, language,
				description, source, timestamp_edit, timestamp_created, published,
				owner, editor, visible, source_key, source_system from %s 
				where id = x'%s' %s''' % \
						('lf_series', series_id.hex, 'and version = %i ' % version) \
						if not version is None else \
						('lf_latest_series', series_id.hex, ''))
			( id, version, parent_version, title, language, description, source,
					timestamp_edit, timestamp_created, published, owner, editor,
					visible, source_key, source_system ) = cur.fetchone()
			cur.execute('''select max(version) from lf_series 
					where id = x'%s' ''' % series_id.hex )
			(new_version,) = cur.fetchone()
			new_version += 1
			cur.execute('''insert into lf_series (id, version, parent_version, title,
					language, description, source, timestamp_created, published, owner,
					editor, visible, source_key, source_system)
					values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ''', 
					( id, new_version, version, title, language, description,
						source, timestamp_created, published, owner, editor, visible,
						source_key, source_system ))
			
			# Second: Connect media to new series
			insertdata = []
			for media_id in media:
				insertdata.append(( series_id.bytes, media_id.bytes, new_version ))

			affected_rows += cur.executemany('''insert into lf_media_series
				(series_id, media_id, series_version) values (%s,%s,%s) ''', 
				insertdata )
	except (IntegrityError, MySQLdbError) as e:
		db.rollback()
		cur.close()
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/user/group/', methods=['PUT'])
def admin_user_group_put():
	'''This method provides you with the functionality to connect user and
	groups. Only administrators are allowed to do this.

	The data can either be JSON or XML. 
	JSON examples::

		{
			"lf:user_group": [{
				"lf:user_id" : 42,
				"lf:group_id" : 42
			}]
		}

		{
			"lf:user_group": [{
				"lf:user_id" : [ 42, 23, 123 ],
				"lf:group_id" : [ 42, 11 ]
			}]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:user_group>
				<lf:user_id>42</lf:user_id>
				<lf:group_id>42</lf:group_id>
			</lf:user_group>
		</data>

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:user_group>
				<lf:user_id>42</lf:user_id>
				<lf:user_id>23</lf:user_id>
				<lf:group_id>42</lf:group_id>
				<lf:group_id>4</lf:group_id>
				<lf:group_id>2</lf:group_id>
			</lf:user_group>
		</data>

	NOTICE: user_group can hold more than one user or group id. If more than one
	 | user or group id is specified each user will be connected to each group.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to add user to a group', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for ug in data.getElementsByTagName('lf:user_group'):
				for u in ug.getElementsByTagName('lf:user_id'):
					for g in ug.getElementsByTagName('lf:group_id'):
						sqldata.append( (
							int(u.childNodes[0].data),
							int(g.childNodes[0].data) ) )
		except (AttributeError, IndexError, ValueError):
			return 'Invalid data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			for ug in data['lf:user_group']:
				user_id = ug['lf:user_id']
				if not isinstance( user_id, list ):
					user_id = [ user_id ]
				group_id = ug['lf:group_id']
				if not isinstance( group_id, list ):
					group_id = [ group_id ]
				for u in user_id:
					for g in group_id:
						sqldata.append( (int(u), int(g)) )
		except (KeyError, ValueError):
			return 'Invalid data', 400
		
	# Request data
	db = get_db()
	cur = db.cursor()

	affected_rows = 0
	try:
		# We use INSERT IGNORE here as we do not need to update anything if the
		# pair of keys already exists.
		affected_rows = cur.executemany('''insert ignore into lf_user_group
			(user_id, group_id) values (%s,%s) ''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/user/organization/', methods=['PUT'])
def admin_user_organization_put():
	'''This method provides you with the functionality to assign user to
	organizations. Only administrators are allowed to do this.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:user_organization": [{
				"lf:user_id" : 42,
				"lf:organization_id" : 42
			}]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:user_organization>
				<lf:user_id>42</lf:user_id>
				<lf:organization_id>42</lf:organization_id>
			</lf:user_organization>
		</data>

	NOTICE: Like with user_groups you can have more than one user id or
	 | organization id in  user_organization.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to add user to a group', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for uo in data.getElementsByTagName('lf:user_organization'):
				for u in ug.getElementsByTagName('lf:user_id'):
					for o in ug.getElementsByTagName('lf:organization_id'):
						sqldata.append( (
							int(u.childNodes[0].data),
							int(o.childNodes[0].data) ) )
		except (AttributeError, IndexError, ValueError):
			return 'Invalid data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			for uo in data['lf:user_organization']:
				user_id = ug['lf:user_id']
				if not isinstance( user_id, list ):
					user_id = [ user_id ]
				org_id = ug['lf:organization_id']
				if not isinstance( org_id, list ):
					org_id = [ org_id ]
				for u in user_id:
					for o in org_id:
						sqldata.append( (int(u), int(o)) )
		except (KeyError, ValueError):
			return 'Invalid data', 400
		
	# Request data
	db = get_db()
	cur = db.cursor()

	affected_rows = 0
	try:
		# We use INSERT IGNORE here as we do not need to update anything if the
		# pair of keys already exists.
		affected_rows = cur.executemany('''insert ignore into 
			lf_user_organization (user_id, organization_id)
			values (%s,%s) ''', sqldata )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/media/subject/', methods=['PUT'])
def admin_media_subject_put():
	'''This method provides you with the functionality to assign subjects to
	media.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:media_subject": [{
				"lf:media_id"  : "aaaaaaaa-6adc-11e2-8b4e-047d7b0f8",
				"lf:subject_id": 42,
				"lf:subject"   : "Computer Science",
				"dc:language"  : "en"
			}]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:media_subject>
				<lf:media_id>aaaaaaaa-6adc-11e2-8b4e-047d7b0f8</lf:media_id>
				<lf:subject_id>42</lf:subject_id>
			</lf:media_subject>
		</data>

	IMPORTANT NOTICE: Either lf:subject_id or lf:subject can be used. Not both.
	 | If both fields are present lf:subject will be ignored. That is, because
	 | using lf:subject_id is faster and will produce less load for database and
	 | webservice.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	# Request data
	db = get_db()
	cur = db.cursor()

	# If the user is no editor (or admin) we want to know which objects he is
	# allowed to modify. In any case, he is not allowed to add new data.
	access = []
	if not user.is_editor():
		groups = 'or group_id in (' + ','.join( user.groups ) + ') ' \
				if user.groups else ''
		q = '''select media_id from lf_access 
				where ( user_id = %i %s) and media_id
				and write_access ''' % ( user.id, groups )
		cur.execute( q )
		access = [ media_id for media_id, in cur.fetchall() ]

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for ms in data.getElementsByTagName( 'lf:media_subject' ):
				media_id   = uuid.UUID(xml_get_text(ms, 'lf:media_id'))
				subject_id = xml_get_text(ms, 'lf:subject_id')
				subject    = xml_get_text(ms, 'lf:subject')
				language   = xml_get_text(ms, 'dc:language')
				sqldata.append(( media_id, subject_id, subject, language ))
		except (AttributeError, IndexError, ValueError):
			return 'Invalid group data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			sqldata = [ ( 
					uuid.UUID(ms['lf:media_id']),
					ms.get('lf:subject_id'),
					ms.get('lf:subject'),
					ms.get('dc:language')
					) for ms in data['lf:media_subject'] ]
		except (KeyError, ValueError):
			return 'Invalid data', 400
		
	# Check data and permissions
	sqldata_ready = []
	try:
		for ( media_id, subject_id, subject, lang ) in sqldata:
			if not user.is_editor() and not media_id.bytes in access:
				db.rollback()
				cur.close()
				return 'You are not allowed to modify this media', 401
			if subject_id is None:
				if subject is None:
					db.rollback()
					cur.close()
					return 'No subject data specified', 400
				if lang is None:
					db.rollback()
					cur.close()
					return 'No language for subject specified', 400
				# Get subject_id from database
				cur.execute('''select id from lf_subject
					where language=%s and name=%s ''', (lang, subject) )
				subject_id = cur.fetchone()
				if not subject_id:
					cur.execute('''insert into lf_subject
						(language, name) values (%s, %s) ''', (lang, subject))
					cur.execute('''select last_insert_id() ''')
					subject_id = cur.fetchone()
				subject_id, = subject_id
			sqldata_ready.append( (subject_id, media_id.bytes) )

		affected_rows = 0
		# We use INSERT IGNORE here as we do not need to update anything if the
		# pair of keys already exists.
		affected_rows = cur.executemany('''insert ignore into 
			lf_media_subject (subject_id, media_id)
			values (%s,%s) ''', sqldata_ready )
	except MySQLdbError as e:
		db.rollback()
		cur.close()
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200



@app.route('/admin/series/subject/', methods=['PUT'])
def admin_series_subject_put():
	'''This method allows you to assign subjects to series.

	The data can either be JSON or XML. 

	JSON example::

		{
			"lf:series_subject": [{
				"lf:series_id"  : "aaaaaaaa-6adc-11e2-8b4e-047d7b0f8",
				"lf:subject_id": 42,
				"lf:subject"   : "Computer Science",
				"dc:language"  : "en"
			}]
		}

	XML example::

		<?xml version="1.0" ?>
		<data xmlns:dc="http://purl.org/dc/elements/1.1/"
				xmlns:lf="http://lernfunk.de/terms">
			<lf:series_subject>
				<lf:series_id>aaaaaaaa-6adc-11e2-8b4e-047d7b0f8</lf:series_id>
				<lf:subject_id>42</lf:subject_id>
			</lf:series_subject>
		</data>

	IMPORTANT NOTICE: Either lf:subject_id or lf:subject can be used. Not both.
	 | If both fields are present lf:subject will be ignored. That is, because
	 | using lf:subject_id is faster and will produce less load for database and
	 | webservice. If lf:subject is used there must also be a language.

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/xml', 'application/json']:
		return 'Invalid data type: %s' % type, 400

	# Request data
	db = get_db()
	cur = db.cursor()

	# If the user is no editor (or admin) we want to know which objects the user
	# is allowed to modify. In any case, he is not allowed to add new data.
	access = []
	if not user.is_editor():
		groups = 'or group_id in (' + ','.join( user.groups ) + ') ' \
				if user.groups else ''
		q = '''select series_id from lf_access 
				where ( user_id = %i %s) and series_id
				and write_access ''' % ( user.id, groups )
		cur.execute( q )
		access = [ series_id for series_id, in cur.fetchall() ]

	sqldata = []
	if type == 'application/xml':
		data = parseString(data)
		try:
			for ms in data.getElementsByTagName( 'lf:series_subject' ):
				series_id   = uuid.UUID(xml_get_text(ms, 'lf:series_id'))
				subject_id = xml_get_text(ms, 'lf:subject_id')
				subject    = xml_get_text(ms, 'lf:subject')
				language   = xml_get_text(ms, 'dc:language')
				sqldata.append(( series_id, subject_id, subject, language ))
		except (AttributeError, IndexError, ValueError):
			return 'Invalid group data', 400
	elif type == 'application/json':
		# Parse JSON
		try:
			data = json.loads(data)
		except ValueError as e:
			return e.message, 400
		# Get array of new data
		try:
			sqldata = [ ( 
					uuid.UUID(ms['lf:series_id']),
					ms.get('lf:subject_id'),
					ms.get('lf:subject'),
					ms.get('dc:language')
					) for ms in data['lf:series_subject'] ]
		except (KeyError, ValueError):
			return 'Invalid data', 400
		
	# Check data and permissions
	sqldata_ready = []
	try:
		for ( series_id, subject_id, subject, lang ) in sqldata:
			if not user.is_editor() and not series_id.bytes in access:
				db.rollback()
				cur.close()
				return 'You are not allowed to modify this series', 401
			if subject_id is None:
				if subject is None:
					db.rollback()
					cur.close()
					return 'No subject data specified', 400
				if lang is None:
					db.rollback()
					cur.close()
					return 'No language for subject specified', 400
				# Get subject_id from database
				cur.execute('''select id from lf_subject
					where language=%s and name=%s ''', (lang, subject) )
				subject_id = cur.fetchone()
				if not subject_id:
					cur.execute('''insert into lf_subject
						(language, name) values (%s, %s) ''', (lang, subject))
					cur.execute('''select last_insert_id() ''')
					subject_id = cur.fetchone()
				subject_id, = subject_id
			sqldata_ready.append( (subject_id, series_id.bytes) )

		affected_rows = 0
		# We use INSERT IGNORE here as we do not need to update anything if the
		# pair of keys already exists.
		affected_rows = cur.executemany('''insert ignore into 
			lf_series_subject (subject_id, series_id)
			values (%s,%s) ''', sqldata_ready )
	except MySQLdbError as e:
		db.rollback()
		cur.close()
		return str(e), 409
	db.commit()

	if affected_rows:
		return '', 201
	return '', 200
