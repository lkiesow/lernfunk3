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
import uuid

from flask import request, g, jsonify


@app.route('/admin/media/',                              methods=['GET'])
@app.route('/admin/media/<uuid:media_id>',               methods=['GET'])
@app.route('/admin/media/<uuid:media_id>/<int:version>', methods=['GET'])
@app.route('/admin/media/<lang:lang>',                   methods=['GET'])
@app.route('/admin/media/<uuid:media_id>/<lang:lang>',   methods=['GET'])
def admin_media(media_id=None, version=None, lang=None):
	'''This method provides live access to the last published state of all
	mediaobjects in the Lernfunk database. Use HTTP Basic authentication to get
	access. If you don't then you will be ranked as “public” user and will only
	see what is public available.

	Keyword arguments:
	media_id -- UUID of a specific media object.
	lang     -- Language filter for the mediaobjects.

	GET parameter:
	with_series      -- Also return the series (default: enabled)
	with_contributor -- Also return the contributors (default: enabled)
	with_creator     -- Also return the creators (default: enabled)
	with_publisher   -- Also return the publishers (default: enabled)
	with_file        -- Also return all files (default: disabled)
	with_subject     -- Also return all subjects (default: enabled)
	with_read_access -- Also return media without write access (default: disabled)
	only_latest      -- Return only latest version (default: disabled)
	only_published   -- Return only published version (default: disabled)
	limit            -- Maximum amount of results to return (default: 10)
	offset           -- Offset of results to return (default: 0)
	'''

	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401
	
	if app.debug:
		print('### User #######################')
		print(user)
		print('################################')


	# Check flags for additional data
	with_series      = is_true(request.args.get('with_series',      '1'))
	with_contributor = is_true(request.args.get('with_contributor', '1'))
	with_creator     = is_true(request.args.get('with_creator',     '1'))
	with_publisher   = is_true(request.args.get('with_publisher',   '1'))
	with_file        = is_true(request.args.get('with_file',        '0'))
	with_subject     = is_true(request.args.get('with_subject',     '1'))
	with_read_access = is_true(request.args.get('with_read_access', '0'))
	only_latest      = is_true(request.args.get('only_latest',      '0'))
	only_published   = is_true(request.args.get('only_published',   '0'))
	limit            = to_int( request.args.get('limit',  '10'), 10)
	offset           = to_int( request.args.get('offset',  '0'),  0)


	query_condition = ''
	# Admins and editors can see everything. So there is no need for conditions.
	if not ( user.is_admin() or user.is_editor() ):
		# Add user as conditions
		query_condition = '''left outer join lf_access a on a.media_id = m.id 
			where ( a.user_id = %s ''' % user.id
		# Add groups as condition (if necessary)
		if not len(user.groups):
			query_condition += ') '
		elif len(user.groups) == 1:
			query_condition += 'or a.group_id = %s ) ' % user.groups.keys()[0]
		else:
			grouplist = '(' + ','.join([str(id) for id in user.groups.keys()]) + ')'
			query_condition += ' a.group_id in %s ) ' % grouplist
		# Add access condition
		if with_read_access:
			query_condition += 'and read_access '
		else:
			query_condition += 'and write_access '

	# Request data
	db = get_db()
	cur = db.cursor()
	table = 'lf_media'
	if only_latest and only_published:
		table = 'lf_latest_published_media'
	elif only_latest:
		table = 'lf_latest_media'
	elif only_published:
		table = 'lf_published_media'

	query = '''select m.id, m.version, m.parent_version, m.language,
			m.title, m.description, m.owner, m.editor, m.timestamp_edit,
			m.timestamp_created, m.published, m.source, m.visible,
			m.source_system, m.source_key, m.rights, m.type, m.coverage,
			m.relation from %s m ''' % table
	count_query = '''select count(m.id) from %s m ''' % table
	if media_id:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				"m.id = x'%s' " % media_id.hex

	# Check for language argument
	if lang:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				'm.language = "%s" ' % lang
	query += query_condition
	count_query += query_condition

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# For each media we get
	for id, version, parent_version, language, title, description, owner, \
			editor, timestamp_edit, timestamp_created, published, source, \
			visible, source_system, source_key, rights, type, coverage, \
			relation in cur.fetchall():
		media_uuid = uuid.UUID(bytes=id)
		media = {}
		# Add default elements
		media["dc:identifier"]     = str(media_uuid)
		media["lf:version"]        = version
		media["lf:parent_version"] = parent_version
		media["dc:language"]       = language
		media["dc:title"]          = title
		media["dc:description"]    = description
		media["lf:owner"]          = owner
		media["lf:editor"]         = editor
		media["dc:date"]           = str(timestamp_created)
		media["lf:last_edit"]      = str(timestamp_edit)
		media["lf:published"]      = published
		media["dc:source"]         = source
		media["lf:visible"]        = visible
		media["lf:source_system"]  = source_system
		media["lf:source_key"]     = source_key
		media["dc:rights"]         = rights
		media["dc:type"]           = type

		# Get series
		if with_series:
			cur.execute( '''select bin2uuid(ms.series_id) from lf_media_series ms
				inner join lf_latest_published_series s
				on ms.series_id = s.id and ms.series_version = s.version
				where ms.media_id = x'%s' and visible ''' % media_uuid.hex )
			series = []
			for (series_id,) in cur.fetchall():
				series.append( series_id )
			media["lf:series_id"] = series

		# Get contributor (user)
		if with_contributor:
			cur.execute( '''select user_id from lf_media_contributor
				where media_id = x'%s' ''' % media_uuid.hex )
			contributor = []
			for (user_id,) in cur.fetchall():
				contributor.append( user_id )
			media["lf:contributor"] = contributor

		# Get creator (user)
		if with_creator:
			cur.execute( '''select user_id from lf_media_creator
				where media_id = x'%s' ''' % media_uuid.hex )
			creator = []
			for (user_id,) in cur.fetchall():
				creator.append( user_id )
			media["lf:creator"] = creator

		# Get publisher (organization)
		if with_publisher:
			cur.execute( '''select organization_id from lf_media_publisher
				where media_id = x'%s' ''' % media_uuid.hex )
			organization = []
			for (organization_id,) in cur.fetchall():
				organization.append( organization_id )
			media["lf:publisher"] = organization

		# Get files
		if with_file:
			cur.execute( '''select bin2uuid(id), format, uri,
				source, source_key, source_system from lf_prepared_file
				where media_id = x'%s' ''' % media_uuid.hex )
			files = []
			for id, format, uri, src, src_key, src_sys in cur.fetchall():
				f = {}
				f["dc:identifier"]    = id
				f["dc:format"]        = format
				f["lf:uri"]           = uri
				f["lf:source"]        = src
				f["lf:source_key"]    = src_key
				f["lf:source_system"] = src_sys
				files.append( f )
			media["lf:file"] = files

		# Get subjects
		if with_subject:
			cur.execute( '''select s.name from lf_media_subject ms 
					join lf_subject s on s.id = ms.subject_id 
					where s.language = "%s" 
					and ms.media_id = x'%s' ''' % (language, media_uuid.hex) )
			subject = []
			for (subject_name,) in cur.fetchall():
				subject.append( subject_name )
			media["dc:subject"] = subject

		result.append( media )

	result = {'lf:media' : result}
	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)



@app.route('/admin/series/',                             methods=['GET'])
@app.route('/admin/series/<uuid:series_id>',             methods=['GET'])
@app.route('/admin/series/<lang:lang>',                  methods=['GET'])
@app.route('/admin/series/<uuid:series_id>/<lang:lang>', methods=['GET'])
def admin_series(series_id=None, lang=None):
	'''This method provides access to the latest published state of all series
	in the Lernfunk database. Use HTTP Basic authentication to get access to
	more series. If you don't do that you will be ranked as “public” user.

	Keyword arguments:
	series_id -- UUID of a specific series.
	lang      -- Language filter for the series.

	GET parameter:
	with_media       -- Also return the media (default: enabled)
	with_creator     -- Also return the creators (default: enabled)
	with_publisher   -- Also return the publishers (default: enabled)
	with_subject     -- Also return all subjects (default: enabled)
	with_read_access -- Also return series without write access (default: disabled)
	only_latest      -- Return only latest version (default: disabled)
	only_published   -- Return only published version (default: disabled)
	limit            -- Maximum amount of results to return (default: 10)
	offset           -- Offset of results to return (default: 0)
	'''

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401
	if not user:
		return '', 403
	
	if app.debug:
		print('### User #######################')
		print(user)
		print('################################')


	# Check flags for additional data
	with_media       = is_true(request.args.get('with_media',       '1'))
	with_creator     = is_true(request.args.get('with_creator',     '1'))
	with_publisher   = is_true(request.args.get('with_publisher',   '1'))
	with_subject     = is_true(request.args.get('with_subject',     '1'))
	with_read_access = is_true(request.args.get('with_read_access', '0'))
	only_latest      = is_true(request.args.get('only_latest',      '0'))
	only_published   = is_true(request.args.get('only_published',   '0'))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)


	query_condition = ''
	# Admins and editors can see everything. So there is no need for conditions.
	if not ( user.is_admin() or user.is_editor() ):
		# Add user as conditions
		query_condition = '''left outer join lf_access a on a.series_id = s.id 
			where ( a.user_id = %s ''' % user.id
		# Add groups as condition (if necessary)
		if not len(user.groups):
			query_condition += ') '
		elif len(user.groups) == 1:
			query_condition += 'or a.group_id = %s ) ' % user.groups.keys()[0]
		else:
			grouplist = '(' + ','.join([str(id) for id in user.groups.keys()]) + ')'
			query_condition += ' a.group_id in %s ) ' % grouplist
		# Add access condition
		if with_read_access:
			query_condition += 'and read_access '
		else:
			query_condition += 'and write_access '

	# Request data
	db = get_db()
	cur = db.cursor()
	table = 'lf_series'
	if only_latest and only_published:
		table = 'lf_latest_published_series'
	elif only_latest:
		table = 'lf_latest_series'
	elif only_published:
		table = 'lf_published_series'
	query = '''select s.id, s.version, s.parent_version, s.title,
			s.language, s.description, s.source, s.timestamp_edit,
			s.timestamp_created, s.published, s.owner, s.editor, s.visible,
			s.source_key, s.source_system 
			from %s s ''' % table
	count_query = '''select count(s.id) from %s s ''' % table
	if series_id:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				"s.id = x'%s' " % series_id.hex

	# Check for language argument
	if lang:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				's.language = "%s" ' % lang
	query += query_condition
	count_query += query_condition

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# For each media we get
	for id, version, parent_version, title, language, description, source, \
			timestamp_edit, timestamp_created, published, owner, editor, \
			visible, source_key, source_system in cur.fetchall():
		series_uuid = uuid.UUID(bytes=id)
		series = {}
		series["dc:identifier"]     = str(series_uuid)
		series["lf:version"]        = version
		series["lf:parent_version"] = parent_version
		series["dc:title"]          = title
		series["dc:language"]       = language
		series["dc:description"]    = description
		series["dc:source"]         = source
		series["lf:last_edit"]      = str(timestamp_edit)
		series["dc:date"]           = str(timestamp_created)
		series["lf:published"]      = published
		series["lf:owner"]          = owner
		series["lf:editor"]         = editor
		series["lf:visible"]        = visible
		series["lf:source_key"]     = source_key
		series["lf:source_system"]  = source_system

		# Get media
		if with_media:
			cur.execute( '''select bin2uuid(media_id) from lf_media_series 
				where series_id = x'%s'
				and series_version = %s''' % ( series_uuid.hex, version ) )
			media = []
			for (media_id,) in cur.fetchall():
				media.append( media_id )
			series['lf:media_id'] = media

		# Get creator (user)
		if with_creator:
			creator = []
			cur.execute( '''select user_id from lf_series_creator
				where series_id = x'%s' ''' % series_uuid.hex )
			for (user_id,) in cur.fetchall():
				creator.append( user_id )
			series['lf:creator'] = creator

		# Get publisher (organization)
		if with_publisher:
			cur.execute( '''select organization_id from lf_series_publisher
				where series_id = x'%s' ''' % series_uuid.hex )
			publisher = []
			for (organization_id,) in cur.fetchall():
				publisher.append( organization_id )
			series["lf:publisher"] = publisher

		# Get subjects
		if with_subject:
			cur.execute( '''select s.name from lf_series_subject ms 
					join lf_subject s on s.id = ms.subject_id 
					where s.language = "%s" 
					and ms.series_id = x'%s' ''' % (language, series_uuid.hex) )
			subject = []
			for (subject_name,) in cur.fetchall():
				subject.append( subject_name )
			series["dc:subject"] = subject
		result.append( series )

	result = { 'lf:series' : result }
	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)



@app.route('/admin/subject/')
@app.route('/admin/subject/<int:subject_id>')
@app.route('/admin/subject/<lang:lang>')
@app.route('/admin/subject/<int:subject_id>/<lang:lang>')
def admin_subject(subject_id=None, lang=None):
	'''This method provides access to all subject in the Lernfunk database.
	
	KeyError argument:
	subject_id -- Id of a specific subject.
	lang       -- Language filter for the subjects.

	GET parameter:
	with_read_access -- Also return series without write access (default: disabled)
	limit            -- Maximum amount of results to return (default: 10)
	offset           -- Offset for results to return (default: 0)
	'''
	with_read_access = is_true(request.args.get('with_read_access', '0'))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401
	# Only user with write access are permittet.
	# But only editors have write access.
	if not user.is_editor() and not with_read_access:
		# Return empty result.
		if request.accept_mimetypes.best_match(
				['application/xml', 'application/json']) == 'application/json':
			return jsonify(result={}, resultcount=0)
		return xmlify(result={}, resultcount=0)

	db = get_db()
	cur = db.cursor()
	query = '''select id, name, language from lf_subject '''
	count_query = '''select count(id) from lf_subject '''
	query_condition = ''
	if subject_id is not None:
		query_condition += 'where id = %s ' % int(subject_id)

	# Check for language argument
	if lang:
		query_condition += ( 'and language = "%s" ' \
				if query_condition \
				else 'where language = "%s" ' ) % lang
	query += query_condition
	count_query += query_condition
	

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# For each media we get
	for id, name, language in cur.fetchall():
		subject = {}
		subject["lf:id"]       = id
		subject["lf:name"]     = name
		subject["dc:language"] = language
		result.append( subject )

	result = { 'lf:subject' : result }
	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)



@app.route('/admin/file/')
@app.route('/admin/file/<uuid:file_id>')
def admin_file(file_id=None):
	'''This method provides access to the files datasets in the Lernfunk
	database. Access rights for this are taken from the media object the files
	belong to.

	Keyword arguments:
	file_id -- UUID of a specific file.

	GET parameter:
	wsith_read_access -- Also return series without write access (default: disabled)
	limit            -- Maximum amount of results to return (default: 10)
	offset           -- Offset of results to return (default: 0)
	'''

	with_read_access = is_true(request.args.get('with_read_access', '0'))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401
	
	if app.debug:
		print('### User #######################')
		print(user)
		print('################################')

	query_condition = ''
	# Admins and editors can see everything. So there is no need for conditions.
	if not ( user.is_admin() or user.is_editor() ):
		# Add user as conditions
		query_condition = '''inner join lf_access a on a.media_id = f.media_id 
			where ( a.user_id = %s ''' % user.id
		# Add groups as condition (if necessary)
		if not len(user.groups):
			query_condition += ') '
		elif len(user.groups) == 1:
			query_condition += 'or a.group_id = %s ) ' % user.groups.keys()[0]
		else:
			grouplist = '(' + ','.join([str(id) for id in user.groups.keys()]) + ')'
			query_condition += ' a.group_id in %s ) ' % grouplist
		# Add access condition
		if with_read_access:
			query_condition += 'and read_access '
		else:
			query_condition += 'and write_access '


	# Request data
	db = get_db()
	cur = db.cursor()
	query = '''select f.id, f.format, f.uri, bin2uuid(f.media_id),
				f.source, f.source_key, f.source_system from lf_prepared_file f '''
	count_query = '''select count(f.id) from lf_prepared_file f '''
	if file_id:
		query += "where f.id = x'%s' " % file_id.hex
	query += query_condition
	count_query += query_condition

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# For each file we get
	for id, format, uri, media_id, src, src_key, src_sys in cur.fetchall():
		file_uuid = uuid.UUID(bytes=id)
		file = {}
		file["dc:identifier"]    = str(file_uuid)
		file["dc:format"]        = format
		file["lf:uri"]           = uri
		file["lf:media_id"]      = media_id
		file["lf:source"]        = src
		file["lf:source_key"]    = src_key
		file["lf:source_system"] = src_sys
		result.append( file )

	result = { 'lf:file' : result }
	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)



@app.route('/admin/organization/')
@app.route('/admin/organization/<int:organization_id>')
def admin_organization(organization_id=None):
	'''This method provides access to all orginization datasets in the Lernfunk
	database.

	Keyword arguments:
	organization_id -- Id of a specific organization.

	GET parameter:
	with_read_access -- Also return series without write access (default: disabled)
	limit            -- Maximum amount of results to return (default: 10)
	offset           -- Offset of results to return (default: 0)
	'''

	with_read_access = is_true(request.args.get('with_read_access', '0'))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401
	# Only user with write access are permittet.
	# But only editors have write access.
	if not user.is_editor() and not with_read_access:
		# Return empty result.
		if request.accept_mimetypes.best_match(
				['application/xml', 'application/json']) == 'application/json':
			return jsonify(result={}, resultcount=0)
		return xmlify(result={}, resultcount=0)

	db = get_db()
	cur = db.cursor()
	query = '''select id, name, vcard_uri, parent_organization 
			from lf_organization '''
	count_query = '''select count(id) from lf_organization '''
	if organization_id:
		query += 'where id = %s ' % int(organization_id)
		count_query += 'where id = %s ' % int(organization_id)

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# For each file we get
	for id, name, vcard_uri, parent_organization in cur.fetchall():
		org = {}
		org['dc:identifier']             = id
		org['lf:name']                   = name
		org['lf:parent_organization_id'] = parent_organization
		org['vcard_uri']                 = vcard_uri
		result.append( org )

	result = { 'lf:organization' : result }

	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)



@app.route('/admin/group/')
@app.route('/admin/group/<int:group_id>')
def admin_group(group_id=None):
	'''This method provides access to all group datasets from the Lernfunk
	database. You have to authenticate yourself as an administrator to access
	these data.

	Keyword arguments:
	group_id -- Id of a specific group.

	GET parameter:
	limit  -- Maximum amount of results to return (default: 10)
	offset -- Offset of results to return (default: 0)
	'''

	# Check for authentication as admin.
	# Neither normal user nor editors have access to groups.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Authentication as admin failed', 403
	except KeyError as e:
		return str(e), 401

	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)

	db = get_db()
	cur = db.cursor()
	query = '''select id, name from lf_group '''
	count_query = 'select count(id) from lf_group '
	if group_id:
		query += 'where id = %s ' % int(group_id)
		count_query += 'where id = %s ' % int(group_id)

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# For each file we get
	for id, name in cur.fetchall():
		group = {}
		group['dc:identifier'] = id
		group['lf:name']       = name
		result.append( group )

	result = { 'lf:group' : result }

	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)


@app.route('/admin/user/')
@app.route('/admin/user/<int:user_id>')
def admin_user(user_id=None):
	'''This method provides access to the user data from the lernfunk database.
	Use HTTP Basic authentication to get access to more data.

	Keyword arguments:
	user_id -- Id of a specific user.

	GET parameter:
	limit  -- Maximum amount of results to return (default: 10)
	offset -- Offset of results to return (default: 0)
	'''

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		return str(e), 401
	
	if app.debug:
		print('### User #######################')
		print(user)
		print('################################')
	
	query_condition = ''
	if user.is_admin(): # No restriction for admin
		pass
	elif user.is_editor(): # Editor
		query_condition = 'where ( access <= 3 or id = %s ) ' % user.id
	elif user.name != 'public': # User with proper authentication
		query_condition = 'where ( access <= 2 or id = %s ) ' % user.id
	else:
		query_condition = 'where ( access = 1 or id = %s ) ' % user.id

	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)

	db = get_db()
	cur = db.cursor()
	query = '''select u.id, u.name, u.vcard_uri, u.realname, u.email, u.access 
			from lf_user u '''
	count_query = 'select count(u.id) from lf_user u '
	if user_id:
		query_condition += ('and ' if query_condition else 'where ' ) + \
				'id = %s ' % int(user_id)
	query += query_condition
	count_query += query_condition

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	if app.debug:
		print('### Query ######################')
		print( query )
		print('################################')

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# Human readable mapping for user access rights
	accessmap = {
			1 : 'public',
			2 : 'login required',
			3 : 'editors only',
			4 : 'administrators only'
			}

	# For each file we get
	for id, name, vcard_uri, realname, email, access in cur.fetchall():
		user = {}
		user['dc:identifier'] = id
		user['lf:name']       = name
		user['lf:vcard_uri']  = vcard_uri
		user['lf:realname']   = realname
		user['lf:email']      = email
		user['lf:access']     = accessmap[access]
		result.append( user )

	result = { 'lf:user' : result }
	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)
