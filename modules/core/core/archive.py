# -*- coding: utf-8 -*-
"""
	core.archive
	~~~~~~~~~~~~

	Archive contains the archive REST endpoint which grants access to old
	versions of media objects and series.

	:copyright: 2013 by Lars Kiesow
	:license: FreeBSD and LGPL, see LICENSE for more details.
"""

from core import app
from core.util import *
from core.db import get_db
from core.authenticate import get_authorization
import uuid

from flask import request, session, g, redirect, url_for, abort, make_response, jsonify


@app.route('/archive/media/')
@app.route('/archive/media/<uuid:media_id>')
@app.route('/archive/media/<uuid:media_id>/<int:version>')
@app.route('/archive/media/<lang:lang>')
@app.route('/archive/media/<uuid:media_id>/<lang:lang>')
def archive_media(media_id=None, version=None, lang=None):
	'''This method provides access to old  published states of all
	mediaobjects in the Lernfunk database. Use HTTP Basic authentication to get
	access. If you don't then you will be ranked as “public” user and will only
	see what is public available.

	:param media_id: UUID of a specific media object.
	:param version:  Version of media object to get.
	:param lang:     Language filter for the mediaobjects.

	GET parameter:

		================  ===========================================  ========
		Parameter         Description                                  Default
		================  ===========================================  ========
		with_series       Also return the series                       enabled
		with_contributor  Also return the contributors                 enabled
		with_creator      Also return the creators                     enabled
		with_publisher    Also return the publishers                   enabled
		with_file         Also return all files                        disabled
		with_subject      Also return all subjects                     enabled
		limit             Maximum amount of results to return          10
		offset            Offset of results to return                  0
		with_nothing      Disable all ``with_...`` options by default
		order             Order results by field (ascending)
		rorder            Order results by field (descending)
		q                 Search/filter query
		================  ===========================================  ========

	Search arguments:

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

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		abort(401, e)
	if not user:
		abort(403)
	
	if app.debug:
		print('### User #######################')
		print(user)
		print('################################')
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
		query_condition += 'and read_access '

	# Hide invisible ones
	query_condition += 'and visible ' if query_condition else 'where visible '


	# Check flags for additional data
	default          = '0' if is_true(request.args.get('with_nothing', '0')) else '1'
	with_series      = is_true(request.args.get('with_series',      default))
	with_contributor = is_true(request.args.get('with_contributor', default))
	with_creator     = is_true(request.args.get('with_creator',     default))
	with_publisher   = is_true(request.args.get('with_publisher',   default))
	with_file        = is_true(request.args.get('with_file',        '0'))
	with_subject     = is_true(request.args.get('with_subject',     default))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)

	# Request data
	db = get_db()
	cur = db.cursor()
	query = '''select m.id, m.version, m.parent_version, m.language,
			m.title, m.description, m.owner, m.editor, m.timestamp_edit,
			m.timestamp_created, m.published, m.source, m.visible,
			m.source_system, m.source_key, m.rights, m.type, m.coverage,
			m.relation from lf_published_media m '''
	count_query = '''select count(m.id) from lf_published_media m '''
	if media_id:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				"m.id = x'%s' " % media_id.hex

	# Check for specific version
	if version != None:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				'm.version = "%s" ' % version

	# Check for language argument (if version not set)
	elif lang:
		for c in lang:
			if c not in lang_chars:
				abort(400)
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				'm.language = "%s" ' % lang
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
			media["dc:publisher"] = organization

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



@app.route('/archive/series/')
@app.route('/archive/series/<uuid:series_id>')
@app.route('/archive/series/<uuid:series_id>/<int:version>')
@app.route('/archive/series/<lang:lang>')
@app.route('/archive/series/<uuid:series_id>/<lang:lang>')
def archive_series(series_id=None, version=None, lang=None):
	'''This method provides access to the latest published state of all series
	in the Lernfunk database. Use HTTP Basic authentication to get access to
	more series. If you don't do that you will be ranked as “public” user.

	:param series_id: UUID of a specific series.
	:param version:   Version of series to get.
	:param lang:      Language filter for the series.

	GET parameter:

		==============  ===========================================  =======
		Parameter       Description                                  Default
		==============  ===========================================  =======
		with_media      Also return the media                        enabled
		with_creator    Also return the creators                     enabled
		with_publisher  Also return the publishers                   enabled
		with_subject    Also return all subjects                     enabled
		limit           Maximum amount of results to return          10
		offset          Offset of results to return                  0
		with_nothing    Disable all ``with_...`` options by default
		order           Order results by field (ascending)
		rorder          Order results by field (descending)
		q               Search/filter query
		==============  ===========================================  =======

	Search arguments:

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
		=============  ====  =================

	Search example::

		...?q=eq:source_key:721e6fcd-8667-11e2-a172-047d7b0f869a
		.../q=gt:version:5

	'''

	user = None
	try:
		user = get_authorization( request.authorization )
	except KeyError as e:
		abort(401, e)
	if not user:
		abort(403)
	
	if app.debug:
		print('### User #######################')
		print(user)
		print('################################')

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
		query_condition += 'and read_access '

	# Hide invisible ones
	query_condition += 'and visible ' if query_condition else 'where visible '

	# Check flags for additional data
	default          = '0' if is_true(request.args.get('with_nothing', '0')) else '1'
	with_media       = is_true(request.args.get('with_media',       default))
	with_creator     = is_true(request.args.get('with_creator',     default))
	with_publisher   = is_true(request.args.get('with_publisher',   default))
	with_subject     = is_true(request.args.get('with_subject',     default))
	limit            = to_int(request.args.get('limit',  '10'), 10)
	offset           = to_int(request.args.get('offset',  '0'),  0)
	order            = request.args.get( 'order', None)
	rorder           = request.args.get('rorder', None)

	db = get_db()
	cur = db.cursor()
	query = '''select s.id, s.version, s.parent_version, s.title,
			s.language, s.description, s.source, s.timestamp_edit,
			s.timestamp_created, s.published, s.owner, s.editor, s.visible,
			s.source_key, s.source_system 
			from lf_published_series s '''
	count_query = '''select count(s.id) from lf_published_series s '''
	if series_id:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				"s.id = x'%s' " % series_id.hex

	# Check for specific version
	if version != None:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				's.version = "%s" ' % version

	# Check for language argument
	elif lang:
		query_condition += ( 'and ' if query_condition else 'where ' ) + \
				's.language = "%s" ' % lang
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
			series["dc:publisher"] = publisher

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
