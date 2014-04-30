# -*- coding: utf-8 -*-
"""
	core.admin.delete
	~~~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.
	Admin contains the administrative REST endpoint for the Lernfunk database.
	It will let you retrieve, modify and edit all data.

	:copyright: 2013 by Lars Kiesow
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

	:param media_id: UUID of a specific media object.
	:param version:  Specific version of the media
	:param lang:     Language filter for the mediaobjects.
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
		query_condition += "where id = x'%s' " % media_id.hex

		# Check for version
		if version is not None:
			query_condition += 'and version = %i ' % int(version)
		
	# Check for language argument
	elif lang:
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

	:param series_id: UUID of a specific series.
	:param version:   Specific version of the series.
	:param lang:      Language filter for the series.
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
		query_condition += "where id = x'%s' " % series_id.hex
		# Check for version
		if version != None:
			query_condition += 'and version = %i ' % int(version)
		
	# Check for language argument
	if lang:
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

	:param server_id: Id of a specific server.
	:param format:    Format for a specific URI pattern.
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



@app.route('/admin/subject/',                             methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>',             methods=['DELETE'])
@app.route('/admin/subject/<lang:lang>',                  methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>/<lang:lang>', methods=['DELETE'])
def admin_subject_delete(subject_id=None, lang=None):
	'''This method provides you with the functionality to delete subjects.
	Only administrators are allowed to delete data.

	:param subject_id: UUID of a specific series.
	:param lang:       Language filter for the subjects.
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
			query_condition += 'where id = %i ' % int(subject_id)
		except ValueError:
			return 'Invalid subject_id', 400

	# Check for language argument
	if lang:
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



@app.route('/admin/file/',               methods=['DELETE'])
@app.route('/admin/file/<uuid:file_id>', methods=['DELETE'])
def admin_file_delete(file_id=None):
	'''This method provides you with the functionality to delete file objects.
	Only administrators are allowed to delete data.

	:param file_id: UUID of a specific file object.
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
		query += "where id = x'%s' " % file_id.hex

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

	:param organization_id: Identifier of a specific organization.
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

	:param group_id: Identifier of a specific group.
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
@app.route('/admin/user/<user:name>',   methods=['DELETE'])
def admin_user_delete(user_id=None, name=None):
	'''This method provides you with the functionality to delete user.
	Only administrators are allowed to delete data.

	:param user_id: Identifier of a specific user.
	:param name:    Name of a specific user.
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
			query += 'and id = %i ' % int(user_id)
		except ValueError:
			return 'Invalid user_id', 400 # 400 BAD REQUEST
	elif name:
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

	:param group_id:  Identifier of a specific group.
	:param media_id:  Identifier of a specific mediaobject.
	:param series_id: Identifier of a specific series.
	:param user_id:   Identifier of a specific user.
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
		if media_id:
			query_condition += "media_id = x'%s' " % media_id.hex
		else:
			query_condition += 'not isnull(media_id) '
	if series_access:
		query_condition += 'and ' if query_condition else 'where '
		if series_id:
			query_condition += "series_id = x'%s' " % series_id.hex
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



@app.route('/admin/media/<uuid:media_id>/subject/',                 methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>/subject/<int:subject_id>', methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>/media/',                methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>/media/<uuid:media_id>', methods=['DELETE'])
def admin_media_subject_delete(media_id=None, subject_id=None):
	'''This method provides the functionality to delete subjects.
	Only administrators are allowed to delete data.

	:param media_id:   Identifies a specific mediaobject.
	:param subject_id: Identifies a specific subject.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_media_subject '''

	query_condition = ''
	if media_id:
		query_condition += "where media_id = x'%s' " % media_id.hex
	
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
@app.route('/admin/media/<uuid:media_id>' \
		'/series/<uuid:series_id>',                                  methods=['DELETE'])
@app.route('/admin/media/<uuid:media_id>' \
		'/series/<uuid:series_id>/<int:series_version>',             methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>' \
		'/media/',                                                   methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
		'/media/',                                                   methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>' \
		'/media/<uuid:media_id>',                                    methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/<int:series_version>' \
		'/media/<uuid:media_id>',                                    methods=['DELETE'])
def admin_media_series_delete(media_id=None, series_id=None, series_version=None):
	'''This method provides the functionality to delete media from series.
	Only administrators are allowed to delete data.

	:param media_id:       Identifies a specific mediaobject.
	:param series_id:      Identifies a specific series.
	:param series_version: Identifies a specific version of a series.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_media_series '''

	query_condition = ''
	if media_id:
		query_condition += "where media_id = x'%s' " % media_id.hex
	
	if series_id:
		query_condition += ( 'and ' if query_condition else 'where ' ) \
				+ "series_id = x'%s' " % series_id.hex
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



@app.route('/admin/series/<uuid:series_id>/subject/',                 methods=['DELETE'])
@app.route('/admin/series/<uuid:series_id>/subject/<int:subject_id>', methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>/series/',                 methods=['DELETE'])
@app.route('/admin/subject/<int:subject_id>/series/<uuid:series_id>', methods=['DELETE'])
def admin_series_subject_delete(series_id=None, subject_id=None):
	'''This method provides the functionality to delete subjects.
	Only administrators are allowed to delete data.

	:param series_id:   Identifies a specific seriesobject.
	:param subject_id: Identifies a specific subject.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_series_subject '''

	query_condition = ''
	if series_id:
		query_condition += "where series_id = x'%s' " % series_id.hex
	
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



@app.route('/admin/user/<int:user_id>/group/',               methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/group/<int:group_id>', methods=['DELETE'])
@app.route('/admin/group/<int:group_id>/user/',              methods=['DELETE'])
@app.route('/admin/group/<int:group_id>/user/<int:user_id>', methods=['DELETE'])
def admin_user_group_delete(user_id=None, group_id=None):
	'''This method provides the functionality to delete user from groups.
	Only administrators are allowed to delete data.

	:param user_id:  Identifies a specific user.
	:param group_id: Identifies a specific group.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_user_group '''

	# DB connection
	db = get_db()
	cur = db.cursor()

	# We do not want to delete the connection between u:admin and g:admin as
	# well as u:public and g:public. So we have to know their ids:
	cur.execute( 'select id from lf_user where name = "admin" ' )
	user_id_a = cur.fetchone()[0]
	cur.execute( 'select id from lf_user where name = "public" ' )
	user_id_p = cur.fetchone()[0]
	cur.execute( 'select id from lf_group where name = "admin" ' )
	group_id_a = cur.fetchone()[0]
	cur.execute( 'select id from lf_group where name = "public" ' )
	group_id_p = cur.fetchone()[0]

	query += 'where (user_id != %i or group_id != %i) ' \
			'and (user_id != %i or group_id != %i) ' % \
			(user_id_a, group_id_a, user_id_p, group_id_p)

	if user_id is not None:
		query += 'and user_id = %i ' % int(user_id)
	
	if group_id is not None:
		query += 'and group_id = %i ' % int(group_id)

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



@app.route('/admin/user/<int:user_id>/organization/',                      methods=['DELETE'])
@app.route('/admin/user/<int:user_id>/organization/<int:organization_id>', methods=['DELETE'])
@app.route('/admin/organization/<int:organization_id>/user/',              methods=['DELETE'])
@app.route('/admin/organization/<int:organization_id>/user/<int:user_id>', methods=['DELETE'])
def admin_series_organization_delete(user_id=None, organization_id=None):
	'''This method provides the functionality to delete user from organizations.
	Only administrators are allowed to delete data.

	:param user_id:         Identifies a specific user.
	:param organization_id: Identifies a specific organization.
	'''

	# Check authentication. 
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Only admins are allowed to delete data', 401
	except KeyError as e:
		return str(e), 401

	query = '''delete from lf_user_organization '''
	
	query_condition = '';
	if user_id is not None:
		query_condition += 'where user_id = %i ' % int(user_id)
	
	if organization_id is not None:
		query_condition += ('and ' if query_condition else 'where ') \
				+ 'organization_id = %i ' % int(organization_id)

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
