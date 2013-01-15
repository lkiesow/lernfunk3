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


@app.route('/admin/media/',                              methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>',               methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:version>', methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<lang:lang>',   methods=['DELETE'])
@app.route('/admin/media/<lang:lang>',                   methods=['DELETE'])
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
			return 'Invalid media_id', 400

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



@app.route('/admin/series/',                               methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>',               methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/<int:version>', methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/<lang:lang>',   methods=['DELETE'])
@app.route('/admin/series/<lang:lang>',                    methods=['DELETE'])
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
			return 'Invalid series_id', 400

		# Check for version
		if version != None:
			query_condition += 'and version = %s ' % int(version)
		
	# Check for language argument
	if lang:
		if not lang_regex.match(lang):
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



@app.route('/admin/access/media/<uuid:media_id>/',                       methods=['DELETE'])
@app.route('/admin/access/media/<uuid:media_id>/user/',                  methods=['DELETE'])
@app.route('/admin/access/media/<uuid:media_id>/user/<int:user_id>',     methods=['DELETE'])
@app.route('/admin/access/media/<uuid:media_id>/group/',                 methods=['DELETE'])
@app.route('/admin/access/media/<uuid:media_id>/group/<int:group_id>',   methods=['DELETE'])
@app.route('/admin/access/series/<uuid:series_id>/',                     methods=['DELETE'])
@app.route('/admin/access/series/<uuid:series_id>/user/',                methods=['DELETE'])
@app.route('/admin/access/series/<uuid:series_id>/user/<int:user_id>',   methods=['DELETE'])
@app.route('/admin/access/series/<uuid:series_id>/group/',               methods=['DELETE'])
@app.route('/admin/access/series/<uuid:series_id>/group/<int:group_id>', methods=['DELETE'])
@app.route('/admin/access/user/<int:user_id>/',                          methods=['DELETE'])
@app.route('/admin/access/user/<int:user_id>/media/',                    methods=['DELETE'])
@app.route('/admin/access/user/<int:user_id>/media/<uuid:media_id>',     methods=['DELETE'])
@app.route('/admin/access/user/<int:user_id>/series/',                   methods=['DELETE'])
@app.route('/admin/access/user/<int:user_id>/series/<uuid:series_id>',   methods=['DELETE'])
@app.route('/admin/access/group/<int:group_id>/',                        methods=['DELETE'])
@app.route('/admin/access/group/<int:group_id>/media/',                  methods=['DELETE'])
@app.route('/admin/access/group/<int:group_id>/media/<uuid:media_id>',   methods=['DELETE'])
@app.route('/admin/access/group/<int:group_id>/series/',                 methods=['DELETE'])
@app.route('/admin/access/group/<int:group_id>/series/<uuid:series_id>', methods=['DELETE'])
def admin_access_delete(media_id=None, series_id=None, user_id=None, group_id=None):
	'''This method provides the functionality to delete access rights.
	Only administrators are allowed to delete data.

	Keyword arguments:
	group_id  -- Identifier of a specific group.
	media_id  -- Identifier of a specific mediaobject.
	series_id -- Identifier of a specific series.
	user_id   -- Identifier of a specific user.
	'''

	user_access   = '/user/'   in request.path
	group_access  = '/group/'  in request.path
	media_access  = '/media/'  in request.path
	series_access = '/series/' in request.path

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401
	
	# Request data
	db = get_db()
	cur = db.cursor()

	query = '''delete from lf_access '''

	query_condition = ''

	if user_access:
		if user_id != None:
			query_condition += 'where user_id = %i ' % int(user_id)
		else:
			query_condition += 'where not isnull(user_id) '
	if group_access:
		query_condition += 'and ' if query_condition else 'where '
		if group_id != None:
			query_condition += 'group_id = %i ' % int(group_id)
		else:
			query_condition += 'not isnull(group_id) '
	if media_access:
		query_condition += 'and ' if query_condition else 'where '
		if is_uuid(media_id):
			query_condition += 'media_id = uuid2bin("%s") ' % media_id
		else:
			query_condition += 'not isnull(media_id) '
	if series_access:
		query_condition += 'and ' if query_condition else 'where '
		if is_uuid(series_id):
			query_condition += 'series_id = uuid2bin("%s") ' % series_id
		else:
			query_condition += 'not isnull(series_id) '
	
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
		return str(e), 409 # Constraint failure -> 409 CONFLICT
	db.commit()

	if not affected_rows:
		return '', 410 # No data was deleted -> 410 GONE

	return '', 204 # Data deleted -> 204 NO CONTENT



@app.route('/admin/media/<uuid:media_id>/contributor/',                            methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:version>/contributor/',              methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/contributor/<int:user_id>',               methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:version>/contributor/<int:user_id>', methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/contributor/',                               methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/contributor/<uuid:media_id>/<int:version>',  methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/contributor/<uuid:media_id>/',               methods=['DELETE'])
def admin_media_contributor_delete(media_id=None, user_id=None, version=None):
	'''This method provides the functionality to delete contributor.
	Only administrators are allowed to delete data.

	Keyword arguments:
	media_id -- Identifies a specific mediaobject.
	version  -- Identifies a specific version of the mediaobject.
	user_id  -- Identifies a specific user.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_media_contributor '''

	query_condition = ''
	if is_uuid(media_id):
		query_condition += 'where media_id = uuid2bin("%s") ' % media_id
		if version is not None:
			query_condition += 'and media_version = %i ' % int(version)
	
	if user_id is not None:
		query_condition += ( 'and ' if query_condition else 'where ' ) \
				+ 'user_id = %i ' % int(user_id)
	
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# DB connection
	db = get_db()
	cur = db.cursor()

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



@app.route('/admin/media/<uuid:media_id>/creator/',                            methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:version>/creator/',              methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/creator/<int:user_id>',               methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:version>/creator/<int:user_id>', methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/creator/',                               methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/creator/<uuid:media_id>',                methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/creator/<uuid:media_id>/<int:version>',  methods=['DELETE'])
def admin_media_creator_delete(media_id=None, user_id=None, version=None):
	'''This method provides the functionality to delete creators.
	Only administrators are allowed to delete data.

	Keyword arguments:
	media_id -- Identifies a specific mediaobject.
	user_id  -- Identifies a specific user.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_media_creator '''

	query_condition = ''
	if is_uuid(media_id):
		query_condition += 'where media_id = uuid2bin("%s") ' % media_id
		if version is not None:
			query_condition += 'and media_version = %i ' % version
	
	if user_id is not None:
		query_condition += ( 'and ' if query_condition else 'where ' ) \
				+ 'user_id = %i ' % int(user_id)
	
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# DB connection
	db = get_db()
	cur = db.cursor()

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



@app.route('/admin/media/<uuid:media_id>/publisher/',                                  methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:version>/publisher/',                    methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/publisher/<int:org_id>',                      methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:version>/publisher/<int:org_id>',        methods=['DELETE'])
@app.route('/admin/organization/<int:org_id>/publisher/',                              methods=['DELETE'])
@app.route('/admin/organization/<int:org_id>/publisher/<uuid:media_id>/',              methods=['DELETE'])
@app.route('/admin/organization/<int:org_id>/publisher/<uuid:media_id>/<int:version>', methods=['DELETE'])
def admin_media_publisher_delete(media_id=None, org_id=None, version=None):
	'''This method provides the functionality to delete contributor.
	Only administrators are allowed to delete data.

	Keyword arguments:
	media_id -- Identifies a specific mediaobject.
	version  -- Identifies a specific version of a mediaobject.
	org_id   -- Identifies a specific organization.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_media_publisher '''

	query_condition = ''
	if is_uuid(media_id):
		query_condition += 'where media_id = uuid2bin("%s") ' % media_id
		if version is not None:
			query_condition += 'and media_version = %i ' % int(version)
	
	if org_id is not None:
		query_condition += ( 'and ' if query_condition else 'where ' ) \
				+ 'organization_id = %i ' % int(org_id)
	
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# DB connection
	db = get_db()
	cur = db.cursor()

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



@app.route('/admin/media/<uuid:media_id>/subject/',                         methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/subject/<int:subject_id>',         methods=['DELETE'])
@app.route('/admin/organization/<int:subject_id>/subject/',                 methods=['DELETE'])
@app.route('/admin/organization/<int:subject_id>/subject/<uuid:media_id>',  methods=['DELETE'])
def admin_media_subject_delete(media_id=None, subject_id=None):
	'''This method provides the functionality to delete subjects.
	Only administrators are allowed to delete data.

	Keyword arguments:
	media_id   -- Identifies a specific mediaobject.
	subject_id -- Identifies a specific subject.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_media_subject '''

	query_condition = ''
	if is_uuid(media_id):
		query_condition += 'where media_id = uuid2bin("%s") ' % media_id
	
	if subject_id is not None:
		query_condition += ( 'and ' if query_condition else 'where ' ) \
				+ 'subject_id = %i ' % int(subject_id)
	
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# DB connection
	db = get_db()
	cur = db.cursor()

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



@app.route('/admin/media/<uuid:media_id>' \
		'/series/',                                                  methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:media_version>' \
		'/series/',                                                  methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>' \
		'/series/<uuid:series_id>',                                  methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:media_version>' \
		'/series/<uuid:series_id>',                                  methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>' \
		'/series/<uuid:series_id>/<int:series_version>',             methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/<int:media_version>' \
		'/series/<uuid:series_id>/<int:series_version>',             methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>' \
		'/media/',                                                   methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
		'/media/',                                                   methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>' \
		'/media/<uuid:media_id>',                                    methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
		'/media/<uuid:media_id>',                                    methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>' \
		'/media/<uuid:media_id>/<int:media_version>',                methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
		'/media/<uuid:media_id>/<int:media_version>',                methods=['DELETE'])
def admin_media_series_delete(media_id=None, series_id=None, media_version=None, series_version=None):
	'''This method provides the functionality to delete media from series.
	Only administrators are allowed to delete data.

	Keyword arguments:
	media_id       -- Identifies a specific mediaobject.
	series_id      -- Identifies a specific series.
	media_version  -- Identifies a specific version of a mediaobject.
	series_version -- Identifies a specific version of a series.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_media_series '''

	query_condition = ''
	if is_uuid(media_id):
		query_condition += 'where media_id = uuid2bin("%s") ' % media_id
		if media_version is not None:
			query_condition += 'and media_version = %i ' % int(media_version)
	
	if is_uuid(series_id):
		query_condition += ( 'and ' if query_condition else 'where ' ) \
				+ 'series_id = uuid2bin("%s") ' % series_id
		if series_version is not None:
			query_condition += 'and series_version = %i ' % int(series_version)
	
	query += query_condition

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# DB connection
	db = get_db()
	cur = db.cursor()

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
