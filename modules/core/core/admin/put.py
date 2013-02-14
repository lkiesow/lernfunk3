# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core::Admin
	~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.

	** Admin contains the administrative REST endpoint for the Lernfunk
	** database. It will let you retrieve, modify and edit all data.

    :copyright: (c) 2012 by Lars Kiesow
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

from flask import request, session, g, redirect, url_for, jsonify


_formdata = ['application/x-www-form-urlencoded', 'multipart/form-data']


@app.route('/admin/media/', methods=['PUT'])
def admin_media_put():
	'''This method provides you with the functionality to set media. It
	will create a new dataset or replace an old one if one with the given
	identifier/format already exists.
	Only administrators are allowed to add/modify server data.

	The data can either be JSON or XML. 
	JSON example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
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
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	XML example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	<?xml version="1.0" ?>
	<data xmlns:dc="http://purl.org/dc/elements/1.1/" 
			xmlns:lf="http://lernfunk.de/terms">
		<!-- TODO -->
	</data>
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

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
					return 'You are not allowed to create new mediao', 403

				m['coverage']       = xml_get_text(media, 'dc:coverage')
				m['description']    = xml_get_text(media, 'dc:description')
				m['language']       = xml_get_text(media, 'dc:language', True)
				m['owner']          = xml_get_text(media, 'lf:owner')
				m['parent_version'] = xml_get_text(media, 'lf:parent_version')
				m['published']      = 1 if xml_get_text(media, 'lf:published', True) else 0
				m['relation']       = xml_get_text(media, 'dc:relation')
				m['rights']         = xml_get_text(media, 'dc:rights')
				m['source']         = xml_get_text(media, 'source')
				m['source_key']     = xml_get_text(media, 'lf:source_key')
				m['source_system']  = xml_get_text(media, 'lf:source_system')
				m['title']          = xml_get_text(media, 'dc:title')
				m['type']           = xml_get_text(media, 'dc:type')
				m['visible']        = xml_get_text(media, 'lf:visible', True)
				m['date']           = xml_get_text(media, 'dc:date', True)
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
					return 'You are not allowed to create new mediao', 403

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

				# Maybe will implement this later. May be convinient:
				'''
				# Additional relations:
				m['subject']        = media.get('dc:subject')
				m['publisher']      = media.get('dc:publisher')
				m['series']         = media.get('lf:series_id')
				m['creator']        = media.get('lf:creator')
				m['contributor']    = media.get('lf:contributor')
				'''

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
					values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
					%s, %s, %s) ''', 
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
				# We could also add relations here. That would be a nice feature.
				# So maybe I'll implement it later.
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
					values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
					%s, %s, %s) ''', 
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
				# We could also add relations here. That would be a nice feature.
				# So maybe I'll implement it later.
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



#@app.route('/admin/media/',                              methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>',               methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:version>', methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<lang:lang>',   methods=['DELETE'])
#@app.route('/admin/media/<lang:lang>',                   methods=['DELETE'])
#def admin_media_delete(media_id=None, version=None, lang=None):
#	'''This method provides you with the functionality to delete media objects.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	media_id -- UUID of a specific media object.
#	version  -- Specific version of the media
#	lang     -- Language filter for the mediaobjects.
#	'''
#
#	# Check authentication. 
#	# _Only_ admins are allowed to delete data. Other users may be able 
#	# to hide data but they can never delete data.
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return e, 401
#	
#	query_condition = ''
#
#	# Request data
#	db = get_db()
#	cur = db.cursor()
#
#	query = '''delete from lf_media '''
#	if media_id:
#		query_condition += "where id = x'%s' " % media_id.hex
#
#		# Check for version
#		if version is not None:
#			query_condition += 'and version = %i ' % int(version)
#		
#	# Check for language argument
#	elif lang:
#		query_condition += ( 'and ' if query_condition else 'where ' ) + \
#				'language = "%s" ' % lang
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409
#	db.commit()
#
#	if not affected_rows:
#		return '', 410
#
#	return '', 204
#
#
#
#@app.route('/admin/series/',                               methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>',               methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:version>', methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<lang:lang>',   methods=['DELETE'])
#@app.route('/admin/series/<lang:lang>',                    methods=['DELETE'])
#def admin_series_delete(series_id=None, version=None, lang=None):
#	'''This method provides you with the functionality to delete series.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	series_id -- UUID of a specific series.
#	version   -- Specific version of the series.
#	lang      -- Language filter for the series.
#	'''
#
#	# Check authentication. 
#	# _Only_ admins are allowed to delete data. Other users may be able 
#	# to hide data but they can never delete data.
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return e, 401
#	
#	query_condition = ''
#
#	# Request data
#	db = get_db()
#	cur = db.cursor()
#
#	query = '''delete from lf_series '''
#	if series_id:
#		query_condition += "where id = x'%s' " % series_id.hex
#		# Check for version
#		if version != None:
#			query_condition += 'and version = %i ' % int(version)
#		
#	# Check for language argument
#	if lang:
#		query_condition += ( 'and ' if query_condition else 'where ' ) + \
#				'language = "%s" ' % lang
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409
#	db.commit()
#
#	if not affected_rows:
#		return '', 410
#	
#	return '', 204



@app.route('/admin/server/', methods=['PUT'])
def admin_server_put():
	'''This method provides you with the functionality to set server data. It
	will create a new dataset or replace an old one if one with the given
	identifier/format already exists.
	Only administrators are allowed to add/modify server data.

	The data can either be JSON or XML. 
	JSON example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
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
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	XML example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
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
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	This data should fill the whole body and the content type should be set
	accordingly (“application/json” or “application/xml”). You can however also
	send data with the mimetypes “application/x-www-form-urlencoded” or
	“multipart/form-data” (For example if you want to use HTML forms). In this
	case the data is expected to be in a field called data and the correct
	content type of the data is expected to be in the field type of the request.

	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
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
				id = server.getElementsByTagName('lf:id')[0].childNodes[0].data
				if not idcheck.match(id):
					return 'Bad identifier for server: %s' % id, 400
				fmt = server.getElementsByTagName('lf:format')[0].childNodes[0].data
				if not fmtcheck.match(fmt):
					return 'Bad format for server: %s' % fmt, 400
				uri_pattern = server.getElementsByTagName('lf:uri_pattern')[0]\
						.childNodes[0].data
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
	JSON example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
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
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	XML example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
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
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

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
	if request.content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
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
					id = int(subject.getElementsByTagName('lf:id')[0].childNodes[0].data)
				except AttributeError:
					id = None
				except ValueError:
					return 'Bad identifier for subject', 400
				lang = subject.getElementsByTagName('dc:language')[0].childNodes[0].data
				if not lang_regex_full.match(lang):
					return 'Bad language tag: %s' % lang, 400
				name = subject.getElementsByTagName('lf:name')[0].childNodes[0].data
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
	JSON example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
{
	"lf:file": [
		{
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
		}
	]
}
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	XML example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
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
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	
	IMPORTANT NOTICE:
	 | There should be either a uri or a server, not both. If both fields are
	 | set the server is simply ignored. If no uri is set the uri will be
	 | generated dynamically (have a look at the server uri_pattern for more
	 | information). If none of them is set the insert will fail.

	Optional fields are source, source_system, source_key, quality and type.

	INTERNAL NOTICE:
		The id can also be ommittet, in which case a new uuid is generated
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

	# Check content length and reject lange chunks of data 
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
					d['id'] = uuid.UUID(file.getElementsByTagName('dc:identifier')[0]\
							.childNodes[0].data).bytes
				except (AttributeError, IndexError):
					pass
				d['media_id'] = uuid.UUID(file.getElementsByTagName('lf:media_id')[0]\
						.childNodes[0].data).bytes
				d['format'] = file.getElementsByTagName('dc:format')[0].childNodes[0].data
				try:
					d['quality'] = file.getElementsByTagName('lf:quality')[0].childNodes[0].data
				except IndexError:
					pass
				try:
					d['source'] = file.getElementsByTagName('lf:source')[0].childNodes[0].data
				except IndexError:
					pass
				try:
					d['source_system'] = file.getElementsByTagName('lf:source_system')[0]\
							.childNodes[0].data
				except IndexError:
					pass
				try:
					d['source_key'] = file.getElementsByTagName('lf:source_key')[0]\
							.childNodes[0].data
				except IndexError:
					pass
				try:
					d['type'] = file.getElementsByTagName('lf:type')[0].childNodes[0].data
				except IndexError:
					pass
				try:
					d['uri'] = file.getElementsByTagName('lf:uri')[0].childNodes[0].data
				except IndexError:
					d['server_id'] = file.getElementsByTagName('lf:server_id')[0].childNodes[0].data
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
	JSON example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
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
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	XML example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	<?xml version="1.0" ?>
	<data xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:lf="http://lernfunk.de/terms">
		<lf:organization>
			<lf:name>Universität Osnabrück</lf:name>
			<dc:identifier>1</dc:identifier>
		</lf:organization>
	</data>
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

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
	if request.content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
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
				try:
					id = int(org.getElementsByTagName('dc:identifier')[0]\
							.childNodes[0].data)
				except IndexError:
					id = None
				try:
					parent_id = int(org.getElementsByTagName('lf:parent_organization_id')[0]\
							.childNodes[0].data)
				except IndexError:
					parent_id = None
				try:
					vcard_uri = org.getElementsByTagName('lf:vcard_uri')[0].childNodes[0].data
				except IndexError:
					vcard_uri = None
				name = org.getElementsByTagName('lf:name')[0].childNodes[0].data
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
	JSON example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	{
		"lf:group": [
		{
			"lf:name": "test", 
		}
		]
	}
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	XML example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	<?xml version="1.0" ?>
	<data xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:lf="http://lernfunk.de/terms">
		<lf:group>
			<lf:name>test</lf:name>
			<dc:identifier>42</dc:identifier>
		</lf:group>
	</data>
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	The id can be ommittet. In that case a new id is generated automatically.

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
	if request.content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
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
	modify their own data 

	The data can either be JSON or XML. 
	JSON example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	{
		"lf:user": [
		{
			"lf:name": "admin", 
			"lf:access": "administrators only", 
			"dc:identifier": 1, 
			"lf:realname": null, 
			"lf:email": null, 
			"lf:vcard_uri": null,
			"lf:passwd": "<secret>"
		}
		]
	}
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	XML example:
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	<?xml version="1.0" ?>
	<data xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:lf="http://lernfunk.de/terms">
		<lf:group>
			<lf:name>test</lf:name>
			<dc:identifier>42</dc:identifier>
		</lf:group>
	</data>
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

	The id can be ommittet. In that case a new id is generated automatically.

	The access data can be given either as integer or as their string
	representation. The latter is automatically converted to an integer.
	Possible values for the access field are:
		1 : 'public'
		2 : 'login required'
		3 : 'editors only'
		4 : 'administrators only'

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
	if user.name == 'public':
		return 'You cannot modify your user if you are not logged in', 401

	# Check content length and reject lange chunks of data 
	# which would block the server.
	if request.content_length > app.config['PUT_LIMIT']:
		return 'Amount of data exeeds maximum (%i bytes > %i bytes)' % \
				(request.content_length, app.config['PUT_LIMIT']), 400

	# Determine content type
	if request.content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
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
		return 'Not yet implemented', 400
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
			data = data['lf:user']
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



#@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
#@app.route('/admin/user/<user:name>',   methods=['DELETE'])
#def admin_user_delete(user_id=None, name=None):
#	'''This method provides you with the functionality to delete user.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	user_id -- Identifier of a specific user.
#	name    -- Name of a specific user.
#	'''
#
#	# Check authentication. 
#	# _Only_ admins are allowed to delete data. Other users may be able 
#	# to hide data but they can never delete data.
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return e, 401
#	
#	# Request data
#	db = get_db()
#	cur = db.cursor()
#
#	# admin and public are special. You cannot delete them.
#	query = '''delete from lf_user
#		where name != 'admin' and name != 'public' '''
#	if user_id != None:
#		try:
#			# abort with 400 Bad Request if id is not valid:
#			query += 'and id = %i ' % int(user_id)
#		except ValueError:
#			return 'Invalid user_id', 400 # 400 BAD REQUEST
#	elif name:
#		query += 'and name = %s ' % name
#
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#''' ----------------------------------------------------------------------------
#	End of method which effect entities. The following methods are for
#	relations. Access is still only granted to administrators. Other user have
#	to create a new entity version without the specific connector.
#---------------------------------------------------------------------------- '''
#
#
#
#@app.route('/admin/access/media/<uuid:media_id>/',                       methods=['DELETE'])
#@app.route('/admin/access/media/<uuid:media_id>/user/',                  methods=['DELETE'])
#@app.route('/admin/access/media/<uuid:media_id>/user/<int:user_id>',     methods=['DELETE'])
#@app.route('/admin/access/media/<uuid:media_id>/group/',                 methods=['DELETE'])
#@app.route('/admin/access/media/<uuid:media_id>/group/<int:group_id>',   methods=['DELETE'])
#@app.route('/admin/access/series/<uuid:series_id>/',                     methods=['DELETE'])
#@app.route('/admin/access/series/<uuid:series_id>/user/',                methods=['DELETE'])
#@app.route('/admin/access/series/<uuid:series_id>/user/<int:user_id>',   methods=['DELETE'])
#@app.route('/admin/access/series/<uuid:series_id>/group/',               methods=['DELETE'])
#@app.route('/admin/access/series/<uuid:series_id>/group/<int:group_id>', methods=['DELETE'])
#@app.route('/admin/access/user/<int:user_id>/',                          methods=['DELETE'])
#@app.route('/admin/access/user/<int:user_id>/media/',                    methods=['DELETE'])
#@app.route('/admin/access/user/<int:user_id>/media/<uuid:media_id>',     methods=['DELETE'])
#@app.route('/admin/access/user/<int:user_id>/series/',                   methods=['DELETE'])
#@app.route('/admin/access/user/<int:user_id>/series/<uuid:series_id>',   methods=['DELETE'])
#@app.route('/admin/access/group/<int:group_id>/',                        methods=['DELETE'])
#@app.route('/admin/access/group/<int:group_id>/media/',                  methods=['DELETE'])
#@app.route('/admin/access/group/<int:group_id>/media/<uuid:media_id>',   methods=['DELETE'])
#@app.route('/admin/access/group/<int:group_id>/series/',                 methods=['DELETE'])
#@app.route('/admin/access/group/<int:group_id>/series/<uuid:series_id>', methods=['DELETE'])
#def admin_access_delete(media_id=None, series_id=None, user_id=None, group_id=None):
#	'''This method provides the functionality to delete access rights.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	group_id  -- Identifier of a specific group.
#	media_id  -- Identifier of a specific mediaobject.
#	series_id -- Identifier of a specific series.
#	user_id   -- Identifier of a specific user.
#	'''
#
#	user_access   = '/user/'   in request.path
#	group_access  = '/group/'  in request.path
#	media_access  = '/media/'  in request.path
#	series_access = '/series/' in request.path
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#	
#	# Request data
#	db = get_db()
#	cur = db.cursor()
#
#	query = '''delete from lf_access '''
#
#	query_condition = ''
#
#	if user_access:
#		if user_id != None:
#			query_condition += 'where user_id = %i ' % int(user_id)
#		else:
#			query_condition += 'where not isnull(user_id) '
#	if group_access:
#		query_condition += 'and ' if query_condition else 'where '
#		if group_id != None:
#			query_condition += 'group_id = %i ' % int(group_id)
#		else:
#			query_condition += 'not isnull(group_id) '
#	if media_access:
#		query_condition += 'and ' if query_condition else 'where '
#		if media_id:
#			query_condition += "media_id = x'%s' " % media_id.hex
#		else:
#			query_condition += 'not isnull(media_id) '
#	if series_access:
#		query_condition += 'and ' if query_condition else 'where '
#		if series_id:
#			query_condition += "series_id = x'%s' " % series_id.hex
#		else:
#			query_condition += 'not isnull(series_id) '
#	
#	query += query_condition
#			
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/media/<uuid:media_id>/contributor/',                            methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:version>/contributor/',              methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/contributor/<int:user_id>',               methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:version>/contributor/<int:user_id>', methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/contributor/',                               methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/contributor/<uuid:media_id>/<int:version>',  methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/contributor/<uuid:media_id>/',               methods=['DELETE'])
#def admin_media_contributor_delete(media_id=None, user_id=None, version=None):
#	'''This method provides the functionality to delete contributor.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	media_id -- Identifies a specific mediaobject.
#	version  -- Identifies a specific version of the mediaobject.
#	user_id  -- Identifies a specific user.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_media_contributor '''
#
#	query_condition = ''
#	if media_id:
#		query_condition += "where media_id = x'%s' " % media_id.hex
#		if version is not None:
#			query_condition += 'and media_version = %i ' % int(version)
#	
#	if user_id is not None:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ 'user_id = %i ' % int(user_id)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/media/<uuid:media_id>/creator/',                            methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:version>/creator/',              methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/creator/<int:user_id>',               methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:version>/creator/<int:user_id>', methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/creator/',                               methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/creator/<uuid:media_id>',                methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/creator/<uuid:media_id>/<int:version>',  methods=['DELETE'])
#def admin_media_creator_delete(media_id=None, user_id=None, version=None):
#	'''This method provides the functionality to delete creators.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	media_id -- Identifies a specific mediaobject.
#	user_id  -- Identifies a specific user.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_media_creator '''
#
#	query_condition = ''
#	if media_id:
#		query_condition += "where media_id = x'%s' " % media_id.hex
#		if version is not None:
#			query_condition += 'and media_version = %i ' % version
#	
#	if user_id is not None:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ 'user_id = %i ' % int(user_id)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/media/<uuid:media_id>/publisher/',                                  methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:version>/publisher/',                    methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/publisher/<int:org_id>',                      methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:version>/publisher/<int:org_id>',        methods=['DELETE'])
#@app.route('/admin/organization/<int:org_id>/publisher/',                              methods=['DELETE'])
#@app.route('/admin/organization/<int:org_id>/publisher/<uuid:media_id>/',              methods=['DELETE'])
#@app.route('/admin/organization/<int:org_id>/publisher/<uuid:media_id>/<int:version>', methods=['DELETE'])
#def admin_media_publisher_delete(media_id=None, org_id=None, version=None):
#	'''This method provides the functionality to delete contributor.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	media_id -- Identifies a specific mediaobject.
#	version  -- Identifies a specific version of a mediaobject.
#	org_id   -- Identifies a specific organization.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_media_publisher '''
#
#	query_condition = ''
#	if media_id:
#		query_condition += "where media_id = x'%s' " % media_id.hex
#		if version is not None:
#			query_condition += 'and media_version = %i ' % int(version)
#	
#	if org_id is not None:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ 'organization_id = %i ' % int(org_id)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/media/<uuid:media_id>/subject/',                 methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/subject/<int:subject_id>', methods=['DELETE'])
#@app.route('/admin/subject/<int:subject_id>/media/',                methods=['DELETE'])
#@app.route('/admin/subject/<int:subject_id>/media/<uuid:media_id>', methods=['DELETE'])
#def admin_media_subject_delete(media_id=None, subject_id=None):
#	'''This method provides the functionality to delete subjects.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	media_id   -- Identifies a specific mediaobject.
#	subject_id -- Identifies a specific subject.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_media_subject '''
#
#	query_condition = ''
#	if media_id:
#		query_condition += "where media_id = x'%s' " % media_id.hex
#	
#	if subject_id is not None:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ 'subject_id = %i ' % int(subject_id)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/media/<uuid:media_id>' \
#		'/series/',                                                  methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:media_version>' \
#		'/series/',                                                  methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>' \
#		'/series/<uuid:series_id>',                                  methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:media_version>' \
#		'/series/<uuid:series_id>',                                  methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>' \
#		'/series/<uuid:series_id>/<int:series_version>',             methods=['DELETE'])
#@app.route('/admin/media/<uuid:media_id>/<int:media_version>' \
#		'/series/<uuid:series_id>/<int:series_version>',             methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>' \
#		'/media/',                                                   methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
#		'/media/',                                                   methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>' \
#		'/media/<uuid:media_id>',                                    methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
#		'/media/<uuid:media_id>',                                    methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>' \
#		'/media/<uuid:media_id>/<int:media_version>',                methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
#		'/media/<uuid:media_id>/<int:media_version>',                methods=['DELETE'])
#def admin_media_series_delete(media_id=None, series_id=None, media_version=None, series_version=None):
#	'''This method provides the functionality to delete media from series.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	media_id       -- Identifies a specific mediaobject.
#	series_id      -- Identifies a specific series.
#	media_version  -- Identifies a specific version of a mediaobject.
#	series_version -- Identifies a specific version of a series.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_media_series '''
#
#	query_condition = ''
#	if media_id:
#		query_condition += "where media_id = x'%s' " % media_id.hex
#		if media_version is not None:
#			query_condition += 'and media_version = %i ' % int(media_version)
#	
#	if series_id:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ "series_id = x'%s' " % series_id.hex
#		if series_version is not None:
#			query_condition += 'and series_version = %i ' % int(series_version)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/series/<uuid:series_id>/creator/',                            methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:version>/creator/',              methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/creator/<int:user_id>',               methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:version>/creator/<int:user_id>', methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/creator/',                               methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/creator/<uuid:series_id>',                methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/creator/<uuid:series_id>/<int:version>',  methods=['DELETE'])
#def admin_series_creator_delete(series_id=None, user_id=None, version=None):
#	'''This method provides the functionality to delete creators from series.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	series_id -- Identifies a specific series.
#	version   -- Identifies a specific version of a series.
#	user_id   -- Identifies a specific user.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_series_creator '''
#
#	query_condition = ''
#	if series_id:
#		query_condition += "where series_id = x'%s' " % series_id.hex
#		if version is not None:
#			query_condition += 'and series_version = %i ' % version
#	
#	if user_id is not None:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ 'user_id = %i ' % int(user_id)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/series/<uuid:series_id>/publisher/',                                 methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:version>/publisher/',                   methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/publisher/<int:org_id>',                     methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/<int:version>/publisher/<int:org_id>',       methods=['DELETE'])
#@app.route('/admin/organization/<int:org_id>/publisher/',                               methods=['DELETE'])
#@app.route('/admin/organization/<int:org_id>/publisher/<uuid:series_id>/',              methods=['DELETE'])
#@app.route('/admin/organization/<int:org_id>/publisher/<uuid:series_id>/<int:version>', methods=['DELETE'])
#def admin_series_publisher_delete(series_id=None, org_id=None, version=None):
#	'''This method provides the functionality to delete contributor.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	series_id -- Identifies a specific seriesobject.
#	version   -- Identifies a specific version of a seriesobject.
#	org_id    -- Identifies a specific organization.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_series_publisher '''
#
#	query_condition = ''
#	if series_id:
#		query_condition += "where series_id = x'%s' " % series_id.hex
#		if version is not None:
#			query_condition += 'and series_version = %i ' % int(version)
#	
#	if org_id is not None:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ 'organization_id = %i ' % int(org_id)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/series/<uuid:series_id>/subject/',                 methods=['DELETE'])
#@app.route('/admin/series/<uuid:series_id>/subject/<int:subject_id>', methods=['DELETE'])
#@app.route('/admin/subject/<int:subject_id>/series/',                 methods=['DELETE'])
#@app.route('/admin/subject/<int:subject_id>/series/<uuid:series_id>', methods=['DELETE'])
#def admin_series_subject_delete(series_id=None, subject_id=None):
#	'''This method provides the functionality to delete subjects.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	series_id   -- Identifies a specific seriesobject.
#	subject_id -- Identifies a specific subject.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_series_subject '''
#
#	query_condition = ''
#	if series_id:
#		query_condition += "where series_id = x'%s' " % series_id.hex
#	
#	if subject_id is not None:
#		query_condition += ( 'and ' if query_condition else 'where ' ) \
#				+ 'subject_id = %i ' % int(subject_id)
#	
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/user/<int:user_id>/group/',               methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/group/<int:group_id>', methods=['DELETE'])
#@app.route('/admin/group/<int:group_id>/user/',              methods=['DELETE'])
#@app.route('/admin/group/<int:group_id>/user/<int:user_id>', methods=['DELETE'])
#def admin_user_group_delete(user_id=None, group_id=None):
#	'''This method provides the functionality to delete user from groups.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	user_id  -- Identifies a specific user.
#	group_id -- Identifies a specific group.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_user_group '''
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# We do not want to delete the connection between u:admin and g:admin as
#	# well as u:public and g:public. So we have to know their ids:
#	cur.execute( 'select id from lf_user where name = "admin" ' )
#	user_id_a = cur.fetchone()[0]
#	cur.execute( 'select id from lf_user where name = "public" ' )
#	user_id_p = cur.fetchone()[0]
#	cur.execute( 'select id from lf_group where name = "admin" ' )
#	group_id_a = cur.fetchone()[0]
#	cur.execute( 'select id from lf_group where name = "public" ' )
#	group_id_p = cur.fetchone()[0]
#
#	query += 'where (user_id != %i or group_id != %i) ' \
#			'and (user_id != %i or group_id != %i) ' % \
#			(user_id_a, group_id_a, user_id_p, group_id_p)
#
#	if user_id is not None:
#		query += 'and user_id = %i ' % int(user_id)
#	
#	if group_id is not None:
#		query += 'and group_id = %i ' % int(group_id)
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
#
#
#
#@app.route('/admin/user/<int:user_id>/organization/',                      methods=['DELETE'])
#@app.route('/admin/user/<int:user_id>/organization/<int:organization_id>', methods=['DELETE'])
#@app.route('/admin/organization/<int:organization_id>/user/',              methods=['DELETE'])
#@app.route('/admin/organization/<int:organization_id>/user/<int:user_id>', methods=['DELETE'])
#def admin_series_subject_delete(user_id=None, organization_id=None):
#	'''This method provides the functionality to delete user from organizations.
#	Only administrators are allowed to delete data.
#
#	Keyword arguments:
#	user_id         -- Identifies a specific user.
#	organization_id -- Identifies a specific organization.
#	'''
#
#	# Check authentication. 
#	try:
#		if not get_authorization( request.authorization ).is_admin():
#			return 'Only admins are allowed to delete data', 401
#	except KeyError as e:
#		return str(e), 401
#
#	query = '''delete from lf_user_organization '''
#	
#	query_condition = '';
#	if user_id is not None:
#		query_condition += 'where user_id = %i ' % int(user_id)
#	
#	if organization_id is not None:
#		query_condition += ('and ' if query_condition else 'where ') \
#				+ 'organization_id = %i ' % int(organization_id)
#
#	query += query_condition
#
#	if app.debug:
#		print('### Query ######################')
#		print( query )
#		print('################################')
#
#	# DB connection
#	db = get_db()
#	cur = db.cursor()
#
#	# Get data
#	affected_rows = 0
#	try:
#		affected_rows = cur.execute( query )
#	except IntegrityError as e:
#		return str(e), 409 # Constraint failure -> 409 CONFLICT
#	db.commit()
#
#	if not affected_rows:
#		return '', 410 # No data was deleted -> 410 GONE
#
#	return '', 204 # Data deleted -> 204 NO CONTENT
