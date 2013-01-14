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

from flask import request, session, g, redirect, url_for


@app.route('/admin/media/',                         methods=['DELETE'])
@app.route('/admin/media/<media_id>',               methods=['DELETE'])
@app.route('/admin/media/<media_id>/<int:version>', methods=['DELETE'])
@app.route('/admin/media/<media_id>/<lang>',        methods=['DELETE'])
def admin_media_delete(media_id=None, version=None, lang=None):
	'''This method provides you with the functionality to delete media objects.
	Only administrators are allowed to delete data.

	Keyword arguments:
	media_id -- UUID of a specific media object.
	version  -- Specific version of the media
	lang     -- Language filter for the mediaobjects.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return e, 401
	
	query_condition = ''

	# Request data
	db = get_db()
	cur = db.cursor()

	query = '''delete from lf_media '''
	if media_id:
		# abort with 400 Bad Request if media_id is not a valid uuid or thread it
		# as language code if language argument does not exist
		if is_uuid(media_id):
			query_condition += 'where id = uuid2bin("%s") ' % media_id
		else:
			if lang or (version != None):
				return 'Invalid media_id', 400
			else:
				lang = media_id

	# Check for version
	if version != None:
		query_condition += 'and version = %s ' % int(version)
		
	# Check for language argument
	elif lang:
		for c in lang:
			if c not in lang_chars:
				return 'Invalid language', 400
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				'language = "%s" ' % lang
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if not affected_rows:
		return '', 410

	return '', 204



@app.route('/admin/series/',                          methods=['DELETE'])
@app.route('/admin/series/<series_id>',               methods=['DELETE'])
@app.route('/admin/series/<series_id>/<int:version>', methods=['DELETE'])
@app.route('/admin/series/<series_id>/<lang>',        methods=['DELETE'])
def admin_series_delete(series_id=None, version=None, lang=None):
	'''This method provides you with the functionality to delete series.
	Only administrators are allowed to delete data.

	Keyword arguments:
	series_id -- UUID of a specific series.
	version   -- Specific version of the series.
	lang      -- Language filter for the series.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return e, 401
	
	query_condition = ''

	# Request data
	db = get_db()
	cur = db.cursor()

	query = '''delete from lf_series '''
	if series_id:
		# abort with 400 Bad Request if series_id is not a valid uuid or thread it
		# as language code if language argument does not exist
		if is_uuid(series_id):
			query_condition += 'where id = uuid2bin("%s") ' % series_id
		else:
			if lang or (version != None):
				return 'Invalid series_id', 400
			else:
				lang = series_id

	# Check for version
	if version != None:
		query_condition += 'and version = %s ' % int(version)
		
	# Check for language argument
	elif lang:
		for c in lang:
			if c not in lang_chars:
				return 'Invalid language', 400
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				'language = "%s" ' % lang
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if not affected_rows:
		return '', 410
	
	return '', 204



@app.route('/admin/server/',                     methods=['DELETE'])
@app.route('/admin/server/<server_id>',          methods=['DELETE'])
@app.route('/admin/server/<server_id>/<format>', methods=['DELETE'])
def admin_server_delete(server_id=None, format=None):
	'''This method provides you with the functionality to delete server.
	Only administrators are allowed to delete data.

	Keyword arguments:
	server_id -- Id of a specific server.
	format    -- Format for a specific URI pattern.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401
	
	# Request data
	db = get_db()
	cur = db.cursor()

	query = '''delete from lf_server '''
	if server_id:
		# Abort with 400 Bad Request if id may be harmful (SQL injection):
		for c in server_id:
			if not c in servername_chars:
				return 'Invalid server_id', 400
		query += 'where id = "%s" ' % server_id

		# Check for format
		if format:
			# Check for harmful (SQL injection) characters in 
			# format (delimeter, quotation marks
			for c in ';"\'`':
				print(c)
				if c in format:
					return 'Invalid format', 400
			query += 'and format = "%s" ' % format

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if not affected_rows:
		return '', 410

	return '', 204



@app.route('/admin/subject/',                        methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>',        methods=['DELETE'])
@app.route('/admin/subject/<lang>',                  methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>/<lang>', methods=['DELETE'])
def admin_subject_delete(subject_id=None, lang=None):
	'''This method provides you with the functionality to delete subjects.
	Only administrators are allowed to delete data.

	Keyword arguments:
	subject_id -- UUID of a specific series.
	lang       -- Language filter for the subjects.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return e, 401
	
	query_condition = ''

	# Request data
	db = get_db()
	cur = db.cursor()

	query = '''delete from lf_subject '''
	if subject_id != None:
		# abort with 400 Bad Request if subject_id is not a valid uuid or thread it
		# as language code if language argument does not exist
		try:
			query_condition += 'where id = %s ' % int(subject_id)
		except ValueError:
			return 'Invalid subject_id', 400

	# Check for language argument
	if lang:
		for c in lang:
			if c not in lang_chars:
				return 'Invalid language', 400
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				'language = "%s" ' % lang
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409
	db.commit()

	if not affected_rows:
		return '', 410

	return '', 204



@app.route('/admin/file/',          methods=['DELETE'])
@app.route('/admin/file/<file_id>', methods=['DELETE'])
def admin_file_delete(file_id=None):
	'''This method provides you with the functionality to delete file objects.
	Only administrators are allowed to delete data.

	Keyword arguments:
	file_id -- UUID of a specific file object.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return e, 401
	
	# Request data
	db = get_db()
	cur = db.cursor()

	query = '''delete from lf_file '''
	if file_id:
		if is_uuid(file_id):
			# abort with 400 Bad Request if file_id is not a valid uuid:
			query += 'where id = uuid2bin("%s") ' % file_id
		else:
			return 'Invalid file_id', 400

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409 # Constraint failure -> 409 CONFLICT
	db.commit()

	if not affected_rows:
		return '', 410 # No data was deleted -> 410 GONE

	return '', 204 # Data deleted -> 204 NO CONTENT



@app.route('/admin/organization/',                      methods=['DELETE'])
@app.route('/admin/organization/<int:organization_id>', methods=['DELETE'])
def admin_organization_delete(organization_id=None):
	'''This method provides you with the functionality to delete organizations.
	Only administrators are allowed to delete data.

	Keyword arguments:
	organization_id -- Identifier of a specific organization.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return e, 401
	
	# Request data
	db = get_db()
	cur = db.cursor()

	query = '''delete from lf_organization '''
	if organization_id != None:
		try:
			# abort with 400 Bad Request if file_id is not a valid uuid:
			query += 'where id = %s ' % int(organization_id)
		except ValueError:
			return 'Invalid file_id', 400 # 400 BAD REQUEST

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409 # Constraint failure -> 409 CONFLICT
	db.commit()

	if not affected_rows:
		return '', 410 # No data was deleted -> 410 GONE

	return '', 204 # Data deleted -> 204 NO CONTENT



@app.route('/admin/group/',               methods=['DELETE'])
@app.route('/admin/group/<int:group_id>', methods=['DELETE'])
def admin_group_delete(group_id=None):
	'''This method provides you with the functionality to delete groups.
	Only administrators are allowed to delete data.

	Keyword arguments:
	group_id -- Identifier of a specific group.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return e, 401
	
	# Request data
	db = get_db()
	cur = db.cursor()

	# admin and public are special. You cannot delete them.
	query = '''delete from lf_group 
		where name != 'admin' and name != 'public' '''
	if group_id != None:
		try:
			# abort with 400 Bad Request if id is not valid:
			query += 'and id = %s ' % int(group_id)
		except ValueError:
			return 'Invalid group_id', 400 # 400 BAD REQUEST

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409 # Constraint failure -> 409 CONFLICT
	db.commit()

	if not affected_rows:
		return '', 410 # No data was deleted -> 410 GONE

	return '', 204 # Data deleted -> 204 NO CONTENT



@app.route('/admin/user/',              methods=['DELETE'])
@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
@app.route('/admin/user/<name>',        methods=['DELETE'])
def admin_user_delete(user_id=None, name=None):
	'''This method provides you with the functionality to delete user.
	Only administrators are allowed to delete data.

	Keyword arguments:
	user_id -- Identifier of a specific user.
	name    -- Name of a specific user.
	'''

	# Check authentication. 
	# _Only_ admins are allowed to delete data. Other users may be able 
	# to hide data but they can never delete data.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return e, 401
	
	# Request data
	db = get_db()
	cur = db.cursor()

	# admin and public are special. You cannot delete them.
	query = '''delete from lf_user
		where name != 'admin' and name != 'public' '''
	if user_id != None:
		try:
			# abort with 400 Bad Request if id is not valid:
			query += 'and id = %s ' % int(user_id)
		except ValueError:
			return 'Invalid user_id', 400 # 400 BAD REQUEST
	elif name:
		for c in name:
			if c not in username_chars:
				return 'Invalid username', 400
		query += 'and name = %s ' % name


	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get data
	affected_rows = 0
	try:
		affected_rows = cur.execute( query )
	except IntegrityError as e:
		return str(e), 409 # Constraint failure -> 409 CONFLICT
	db.commit()

	if not affected_rows:
		return '', 410 # No data was deleted -> 410 GONE

	return '', 204 # Data deleted -> 204 NO CONTENT



''' ----------------------------------------------------------------------------
	End of method which effect entities. The following methods are for
	relations. Access is still only granted to administrators. Other user have
	to create a new entity version without the specific connector.
---------------------------------------------------------------------------- '''



