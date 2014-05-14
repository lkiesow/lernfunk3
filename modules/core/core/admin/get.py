# -*- coding: utf-8 -*-
"""
	core.admin.get
	~~~~~~~~~~~~~~

	This module provides administrative read access to the central Lernfunk
	database.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
"""

from core import app
from core.util import *
from core.db import get_db
from core.authenticate import get_authorization
import uuid
import json

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

	:param media_id: UUID of a specific media object.
	:param lang:     Language filter for the mediaobjects.

	GET parameter:

		================  ===========================================  ========
		Parameter         Description                                  Default
		================  ===========================================  ========
		with_series       Also return the series                       enabled
		with_file         Also return all files                        disabled
		with_subject      Also return all subjects                     enabled
		with_read_access  Also media without write access              disabled
		only_latest       Return only latest version                   disabled
		only_published    Return only published version                disabled
		limit             Maximum amount of results to return          10
		offset            Offset of results to return                  0
		with_nothing      Disable all ``with_...`` options by default
		order             Order results by field (ascending)
		rorder            Order results by field (descending)
		q                 Search/filter query
		================  ===========================================  ========

	Search arguments:

		=============  ====  =================
		Key            Type  Database Field
		=============  ====  =================
		identifier     uuid  id
		version        int   version
		description    str   description
		title          str   title
		source         str   source
		source_key     str   source_key
		source_system  str   source_system
		date           time  timestamp_created
		last_edit      time  timestamp_edit
		lang           lang  language
		creator        str   creator
		contributor    str   contributor
		publisher      str   publisher
		=============  ====  =================
	
	Search example::

		...?q=eq:source_key:721e6fcd-8667-11e2-a172-047d7b0f869a
		.../q=gt:version:5
	
	Order options:

		* id
		* language
		* title
		* timestamp_edit
		* timestamp_created
		* source_key

	Order example:

		...?order=id

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
	default          = '0' if is_true(request.args.get('with_nothing', '0')) else '1'
	with_series      = is_true(request.args.get('with_series',      default))
	with_file        = is_true(request.args.get('with_file',        '0'))
	with_subject     = is_true(request.args.get('with_subject',     default))
	with_read_access = is_true(request.args.get('with_read_access', '0'))
	only_latest      = is_true(request.args.get('only_latest',      '0'))
	only_published   = is_true(request.args.get('only_published',   '0'))
	limit            = to_int( request.args.get('limit',  '10'), 10)
	offset           = to_int( request.args.get('offset',  '0'),  0)
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)
	search           = request.args.get('q', None)


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
			m.relation, m.creator, m.contributor, m.publisher
			from %s m ''' % table
	count_query = '''select count(m.id) from %s m ''' % table
	if media_id:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				"m.id = x'%s' " % media_id.hex

	# Check for language argument
	if lang:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				'm.language = "%s" ' % lang

	if search:
		try:
			allowed = {
					'identifier'    : ('uuid','m.id'),
					'version'       : ('int','m.version'),
					'description'   : ('str','m.description'),
					'title'         : ('str','m.title'),
					'source'        : ('str','m.source'),
					'source_key'    : ('str','m.source_key'),
					'source_system' : ('str','m.source_system'),
					'date'          : ('time','m.timestamp_created'),
					'last_edit'     : ('time','m.timestamp_edit'),
					'lang'          : ('lang','m.language'),
					'creator'       : ('str','m.creator'),
					'contributor'   : ('str','m.contributor'),
					'publisher'     : ('str','m.publisher')}
			query_condition += ( 'and ' if query_condition else 'where ' ) + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400

	query += query_condition
	count_query += query_condition

	# Sort by column
	order_opts = ['id', 'language', 'title', 'timestamp_edit', 
			'timestamp_created', 'source_key']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder

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
			relation, creator, contributor, publisher in cur.fetchall():
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
		media["dc:creator"]        = try_parse_json(creator)
		media["dc:contributor"]    = try_parse_json(contributor)
		media["dc:publisher"]      = try_parse_json(publisher)

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

		# Get files
		if with_file:
			cur.execute( '''select bin2uuid(id), format, uri,
				source, source_key, source_system, flavor, tags from lf_file
				where media_id = x'%s' ''' % media_uuid.hex )
			files = []
			for id, format, uri, src, src_key, src_sys, flavor, tags in cur.fetchall():
				try:
					tags = json.loads(tags)
				except (ValueError, TypeError):
					tags = None
				f = {}
				f["dc:identifier"]    = id
				f["dc:format"]        = format
				f["lf:uri"]           = uri
				f["lf:source"]        = src
				f["lf:source_key"]    = src_key
				f["lf:source_system"] = src_sys
				f["lf:flavor"]        = flavor
				f["lf:tags"]          = tags
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

	:param series_id: UUID of a specific series.
	:param lang:      Language filter for the series.

	GET parameter:

		================  ===========================================  =========
		Parameter         Description                                  Default
		================  ===========================================  =========
		with_media        Also return the media                        enabled
		with_subject      Also return all subjects                     enabled
		with_read_access  Also series without write access             disabled
		only_latest       Return only latest version                   disabled
		only_published    Return only published version                disabled
		limit             Maximum amount of results to return          10
		offset            Offset of results to return                  0
		with_nothing      Disable all ``with_...`` options by default
		order             Order results by field (ascending)
		rorder            Order results by field (descending)
		q                 Search/filter query
		================  ===========================================  =========

	Search arguments:

		=============  ====  =================
		Key            Type  Database Field
		=============  ====  =================
		identifier     uuid  id
		version        int   version
		description    str   description
		title          str   title
		source         str   source
		source_key     str   source_key
		source_system  str   source_system
		date           time  timestamp_created
		last_edit      time  timestamp_edit
		lang           lang  language
		creator        str   creator
		contributor    str   contributor
		publisher      str   publisher
		=============  ====  =================

	Search example::

		...?q=eq:source_key:721e6fcd-8667-11e2-a172-047d7b0f869a
		.../q=gt:version:5

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
	default          = '0' if is_true(request.args.get('with_nothing', '0')) else '1'
	with_media       = is_true(request.args.get('with_media',       default))
	with_subject     = is_true(request.args.get('with_subject',     default))
	with_read_access = is_true(request.args.get('with_read_access', '0'))
	only_latest      = is_true(request.args.get('only_latest',      '0'))
	only_published   = is_true(request.args.get('only_published',   '0'))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)
	search           = request.args.get('q', None)


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
			s.source_key, s.source_system, s.creator, s.contributor, s.publisher 
			from %s s ''' % table
	count_query = '''select count(s.id) from %s s ''' % table
	if series_id:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				"s.id = x'%s' " % series_id.hex

	# Check for language argument
	if lang:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				's.language = "%s" ' % lang

	if search:
		try:
			allowed = {
					'identifier'    : ('uuid','s.id'),
					'version'       : ('int','s.version'),
					'description'   : ('str','s.description'),
					'title'         : ('str','s.title'),
					'source'        : ('str','s.source'),
					'source_key'    : ('str','s.source_key'),
					'source_system' : ('str','s.source_system'),
					'date'          : ('time','s.timestamp_created'),
					'last_edit'     : ('time','s.timestamp_edit'),
					'lang'          : ('lang','s.language'),
					'creator'       : ('str','s.creator'),
					'contributor'   : ('str','s.contributor'),
					'publisher'     : ('str','s.publisher')}
			query_condition += ( 'and ' if query_condition else 'where ' ) + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400

	query += query_condition
	count_query += query_condition

	# Sort by column
	order_opts = ['id', 'language', 'title', 'timestamp_edit', 
			'timestamp_created', 'source_key']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder

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
			visible, source_key, source_system, creator, contributor, \
			publisher in cur.fetchall():
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
		series["dc:creator"]        = try_parse_json(creator)
		series["dc:contributor"]    = try_parse_json(contributor)
		series["dc:publisher"]      = try_parse_json(publisher)

		# Get media
		if with_media:
			cur.execute( '''select bin2uuid(media_id) from lf_media_series 
				where series_id = x'%s'
				and series_version = %s''' % ( series_uuid.hex, version ) )
			media = []
			for (media_id,) in cur.fetchall():
				media.append( media_id )
			series['lf:media_id'] = media

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
	
	:param subject_id: Id of a specific subject.
	:param lang:       Language filter for the subjects.

	GET parameter:

		================  =======================================  ========
		Parameter         Description                              Default
		================  =======================================  ========
		with_read_access  Also return series without write access  disabled
		limit             Maximum amount of results to return      10
		offset            Offset for results to return             0
		order             Order results by field (ascending)
		rorder            Order results by field (descending)
		q                 Search/filter query
		================  =======================================  ========

	Search arguments:

		====  ====  ========
		id    int   id
		name  str   name
		lang  lang  language
		====  ====  ========

	Search example::

		...?q=eq:id:5

	'''
	with_read_access = is_true(request.args.get('with_read_access', '0'))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)
	search           = request.args.get('q', None)

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
	
	if search:
		try:
			allowed = {
					'id'        : ('int','id'),
					'name'      : ('str','name'),
					'lang'      : ('lang','language')}
			query_condition += ('and ' if query_condition else 'where ') + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400
	query += query_condition
	count_query += query_condition

	# Sort by column
	order_opts = ['id', 'language', 'name']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder
	

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
	belong to. This basically means that if you can access the media, you can
	access the files assigned to the media.

	:param file_id: UUID of a specific file.

	GET parameter:

		=================  =======================================  ========
		Parameter          Description                              Default
		=================  =======================================  ========
		wsith_read_access  Also return series without write access  disabled
		limit              Maximum amount of results to return       10
		offset             Offset of results to return               0
		order              Order results by field (ascending)
		rorder             Order results by field (descending)
		q                  Search/filter query
		=================  =======================================  ========

	Search arguments:

		=============  ====  =============
		Argument       Type  Db field
		=============  ====  =============
		identifier     uuid  id
		media_id       uuid  media_id
		format         str   format
		type           str   type
		quality        str   quality
		uri            str   uri
		source         str   source
		source_key     str   source_key
		source_system  str   source_system
		=============  ====  =============

	Search example::

		...?q=eq:media_id:721DC300-8667-11E2-A172-047D7B0F869A

	Order options:
	
		* id
		* format
		* uri
		* media_id
		* source_key

	Order example::

		...?order=id

	'''

	with_read_access = is_true(request.args.get('with_read_access', '0'))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)
	search           = request.args.get('q', None)

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
	query = '''select f.id, f.format, f.type, f.quality, f.uri, bin2uuid(f.media_id),
				f.source, f.source_key, f.source_system, f.flavor, f.tags 
				from lf_file f '''
	count_query = '''select count(f.id) from lf_file f '''
	if file_id:
		query += "where f.id = x'%s' " % file_id.hex
	
	if search:
		try:
			allowed = {
					'identifier'    : ('uuid','f.id'),
					'media_id'      : ('uuid','f.media_id'),
					'format'        : ('str','f.format'),
					'type'          : ('str','f.type'),
					'quality'       : ('str','f.quality'),
					'uri'           : ('str','f.uri'),
					'source'        : ('str','f.source'),
					'source_key'    : ('str','f.source_key'),
					'source_system' : ('str','f.source_system'),
					'flavor'        : ('str','f.flavor'),
					'tags'          : ('str','f.tags')}
			query_condition += ('and ' if query_condition else 'where ') + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400
	query += query_condition
	count_query += query_condition

	# Sort by column
	order_opts = ['id', 'format', 'uri', 'media_id', 'source_key']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder

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
	for id, format, type, quality, uri, media_id, src, src_key, src_sys, \
			flavor, tags in cur.fetchall():
		try:
			tags = json.loads(tags)
		except (ValueError, TypeError):
			tags = None
		file_uuid = uuid.UUID(bytes=id)
		file = {}
		file["dc:identifier"]    = str(file_uuid)
		file["dc:format"]        = format
		file["lf:type"]          = type
		file["lf:quality"]       = quality
		file["lf:uri"]           = uri
		file["lf:media_id"]      = media_id
		file["lf:source"]        = src
		file["lf:source_key"]    = src_key
		file["lf:source_system"] = src_sys
		file["lf:flavor"]        = flavor
		file["lf:tags"]          = tags
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

	:param organization_id: Id of a specific organization.

	GET parameter:

		================  =======================================  ========
		Parameter         Description                              Defaul
		================  =======================================  ========
		with_read_access  Also return series without write access  disabled
		limit             Maximum amount of results to return      10
		offset            Offset of results to return              0
		order             Order results by field (ascending)
		rorder            Order results by field (descending)
		q                 Search/filter query
		================  =======================================  ========

	Search arguments:

		========  ====  ========
		Argument  Type  Db field
		========  ====  ========
		id        int   id
		name      str   name
		========  ====  ========

	Search example::

		...?q=eq:id:5

	Order options:

		* id
		* name
	
	Order example::

		...?order=id

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
	query_condition = ''
	if organization_id != None:
		# abort with 400 Bad Request if organization_id is not valid
		try:
			query_condition += 'where id = %s ' % int(organization_id)
		except ValueError:
			return 'Invalid organization_id', 400
	
	if search:
		try:
			allowed = {
					'id'   : ('int','id'),
					'name' : ('str','name')}
			query_condition += ('and ' if query_condition else 'where ') + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400

	query += query_condition
	count_query += query_condition

	# Sort by column
	order_opts = ['id', 'name']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder

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
		org['lf:vcard_uri']              = vcard_uri
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

	:param group_id: Id of a specific group

	GET parameter:
	
		=========  ===================================  =====
		Parameter  Description	Default
		=========  ===================================  =====
		limit      Maximum amount of results to return  10
		offset     Offset of results to return          0
		order      Order results by field (ascending)
		rorder     Order results by field (descending)
		q          Search/filter query
		=========  ===================================  =====

	Search arguments:

		========  ====  ========
		Argument  Type  Db field
		========  ====  ========
		id        int   id
		name      str   name
		========  ====  ========

	Search example::

		...?q=eq:id:5

	Order options:

		* id
		* name
	
	Order example::

		...?order=id

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
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)
	search           = request.args.get('q', None)

	db = get_db()
	cur = db.cursor()
	query = '''select id, name from lf_group '''
	count_query = 'select count(id) from lf_group '
	query_condition = ''
	if group_id != None:
		# abort with 400 Bad Request if id is not valid
		try:
			query_condition += 'where id = %s ' % int(group_id)
		except ValueError:
			return 'Invalid group_id', 400
	
	if search:
		try:
			allowed = {
					'id'   : ('int','id'),
					'name' : ('str','name')}
			query_condition += ('and ' if query_condition else 'where ') + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400

	query += query_condition
	count_query += query_condition

	# Sort by column
	order_opts = ['id', 'name']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder

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

	:param user_id: Id of a specific user.

	GET parameter:

		=========  ===================================  =======
		Parameter  Description                          Default
		=========  ===================================  =======
		limit      Maximum amount of results to return  10
		offset     Offset of results to return          0
		order      Order results by field (ascending)
		rorder     Order results by field (descending)
		q          Search/filter query
		=========  ===================================  =======

	Search arguments:

		========  ====  ========
		Argument  Type  Db field
		========  ====  ========
		id        int   id
		name      str   name
		realname  str   realname
		email     str   email
		========  ====  ========

	Search example:

		...?q=eq:id:5

	Order options:

		* id
		* name
		* realname
		* access

	Order example:

		...?order=id

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
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)
	search           = request.args.get('q', None)
	
	if search:
		try:
			allowed = {
					'id'       : ('int','u.id'),
					'realname' : ('str','u.realname'),
					'email'    : ('str','u.email'),
					'name'     : ('str','u.name')}
			query_condition += ('and ' if query_condition else 'where ') + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400

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

	# Sort by column
	order_opts = ['id', 'name', 'realname', 'access']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder

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



@app.route('/admin/access/')
@app.route('/admin/access/media/')
@app.route('/admin/access/series/')
@app.route('/admin/access/media/<uuid:media_id>')
@app.route('/admin/access/series/<uuid:series_id>')
def admin_access(media_id=None, series_id=None):
	'''This method provides access to all defined access rights, defined in the
	Lernfunk database. You have to authenticate yourself as an administrator to
	access this data.

	:param media_id:  Show access to a specific media.
	:param series_id: Show access to a specific series.

	GET parameter:

		================  =======================================  ========
		Parameter         Description                              Default
		================  =======================================  ========
		limit             Maximum amount of results to return      10
		offset            Offset of results to return              0
		order             Order results by field (ascending)
		rorder            Order results by field (descending)
		q                 Search/filter query
		================  =======================================  ========

	Search arguments:

		=========  ====  =================
		id         uuid  id
		media_id   uuid  media_id
		series_id  uuid  series_id
		group_id   int   group_id
		user_id    int   user_id
		=========  ====  =================
	
	Search example::

		...?q=eq:media_id:721e6fcd-8667-11e2-a172-047d7b0f869a
		.../q=gt:group_id:5
	
	Order options:

		* id
		* media_id
		* series_id
		* group_id
		* user_id

	Order example:

		...?order=id

	'''

	# Check for authentication as admin.
	# Neither normal user nor editors may read access rights.
	try:
		if not get_authorization( request.authorization ).is_admin():
			return 'Authentication as admin failed', 403
	except KeyError as e:
		return str(e), 401

	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)
	search           = request.args.get('q', None)

	db = get_db()
	cur = db.cursor()
	query = '''select id, bin2uuid(media_id), bin2uuid(series_id),
		group_id, user_id, read_access, write_access
		from lf_access '''
	count_query = 'select count(id) from lf_access '
	query_condition = ''

	if media_id:
		query_condition = "where media_id = x'%s' " % media_id.hex
	elif series_id:
		query_condition = "where series_id = x'%s' " % series_id.hex
	elif 'media' in request.path:
		query_condition = 'where not isnull(media_id) '
	elif 'series' in request.path:
		query_condition = 'where not isnull(series_id) '

	if search:
		try:
			allowed = {
					'id'        : ('uuid','id'),
					'media_id'  : ('uuid','media_id'),
					'series_id' : ('uuid','series_id'),
					'group_id'  : ('int','group_id'),
					'user_id'   : ('int','user_id')}
			query_condition += ( 'and ' if query_condition else 'where ' ) + \
					'(%s) ' % search_query( search, allowed )
		except ValueError as e:
			return e.message, 400
		except TypeError:
			return 'Invalid search query', 400

	query       += query_condition
	count_query += query_condition

	# Sort by column
	order_opts = ['id', 'media_id', 'series_id', 'group_id', 'user_id']
	if order:
		if not order in order_opts:
			return 'Cannot order by %s' % order, 400
		query += 'order by %s asc ' % order
	elif rorder:
		if not rorder in order_opts:
			return 'Cannot order by %s' % rorder, 400
		query += 'order by %s desc ' % rorder

	# Add limit and offset
	query += 'limit %s, %s ' % ( offset, limit )

	# Get amount of results
	cur.execute( count_query )
	result_count = cur.fetchone()[0]

	# Get data
	cur.execute( query )
	result = []

	# For each file we get
	for id, media_id, series_id, group_id, user_id, \
			read_access, write_access in cur.fetchall():
		a = {}
		a['dc:identifier']   = id
		a['lf:media_id']     = media_id
		a['lf:series_id']    = series_id
		a['lf:group_id']     = group_id
		a['lf:user_id']      = user_id
		a['lf:read_access']  = read_access
		a['lf:write_access'] = write_access
		result.append( a )

	result = { 'lf:access' : result }

	if request.accept_mimetypes.best_match(
			['application/xml', 'application/json']) == 'application/json':
		return jsonify(result=result, resultcount=result_count)
	return xmlify(result=result, resultcount=result_count)
