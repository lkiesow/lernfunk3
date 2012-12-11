# -*- coding: utf-8 -*-
"""
	Lernfunk3::Core
	~~~~~~~~~~~~~~~

	This module provides read and write access to the central Lernfunk database.

    :copyright: (c) 2012 by Lars Kiesow
    :license: FreeBSD and LGPL, see LICENSE for more details.
"""

import MySQLdb
from xml.dom.minidom import parseString
from flask import Flask, request, session, g, redirect, url_for, abort, \
		render_template, flash, _app_ctx_stack, make_response
from string import hexdigits

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# create our little application :)
app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	top = _app_ctx_stack.top
	if not hasattr(top, 'mysql_db'):
		top.mysql_db = MySQLdb.connect(
			host    = app.config['DATABASE_HOST'],
			user    = app.config['DATABASE_USER'],
			passwd  = app.config['DATABASE_PASSWD'],
			db      = app.config['DATABASE_NAME'],
			port    = int(app.config['DATABASE_PORT']),
			charset = 'utf8' )
	return top.mysql_db


@app.teardown_appcontext
def close_db_connection(exception):
	"""Closes the database again at the end of the request."""
	top = _app_ctx_stack.top
	if hasattr(top, 'mysql_db'):
		top.mysql_db.close()


def xml_add_elem( dom, parent, name, val ):
	if val:
		elem = dom.createElement(name)
		elem.appendChild( dom.createTextNode(str(val)) )
		parent.appendChild( elem )
		return elem
	return None


def is_uuid(s):
	if len(s) != 36:
		return False
	return \
			s[ 0] in hexdigits and \
			s[ 1] in hexdigits and \
			s[ 2] in hexdigits and \
			s[ 3] in hexdigits and \
			s[ 4] in hexdigits and \
			s[ 5] in hexdigits and \
			s[ 6] in hexdigits and \
			s[ 7] in hexdigits and \
			s[ 8] == '-' and \
			s[9] in hexdigits and \
			s[10] in hexdigits and \
			s[11] in hexdigits and \
			s[12] in hexdigits and \
			s[13] == '-' and \
			s[14] in hexdigits and \
			s[15] in hexdigits and \
			s[16] in hexdigits and \
			s[17] in hexdigits and \
			s[18] == '-' and \
			s[19] in hexdigits and \
			s[20] in hexdigits and \
			s[21] in hexdigits and \
			s[22] in hexdigits and \
			s[23] == '-' and \
			s[24] in hexdigits and \
			s[25] in hexdigits and \
			s[26] in hexdigits and \
			s[27] in hexdigits and \
			s[28] in hexdigits and \
			s[29] in hexdigits and \
			s[30] in hexdigits and \
			s[31] in hexdigits and \
			s[32] in hexdigits and \
			s[33] in hexdigits and \
			s[34] in hexdigits and \
			s[35] in hexdigits


def is_true( val ):
	return val.lower() in ['1', 'yes', 'true']


@app.route('/view/media/')
@app.route('/view/media/<media_id>')
@app.route('/view/media/<media_id>/<lang>')
def list_media(media_id=None, lang=None):

	# Check flags for additional data
	with_series      = is_true(request.args.get('with_series',      '1'))
	with_contributor = is_true(request.args.get('with_contributor', '1'))
	with_creator     = is_true(request.args.get('with_creator',     '1'))
	with_publisher   = is_true(request.args.get('with_publisher',   '1'))
	with_file        = is_true(request.args.get('with_file',        '0'))
	with_subject     = is_true(request.args.get('with_subject',     '1'))

	# Request data
	db = get_db()
	cur = db.cursor()
	query = '''select bin2uuid(id), version, parent_version, language,
			title, description, owner, editor, timestamp_edit, timestamp_created,
			published, source, visible, source_system, source_key, rights, type,
			coverage, relation from lf_published_media '''
	if media_id:
		# abort with 400 Bad Request if media_id is not a valid uuid or thread it
		# as language code if language argument does not exist
		if is_uuid(media_id):
			query += 'where id = uuid2bin("%s") ' % media_id
		else:
			if lang:
				abort(400)
			else:
				lang = media_id

	# Check for language argument
	if lang:
		for c in lang:
			if c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_':
				abort(400)
		query += ( 'and language = "%s" ' \
				if 'where id' in query \
				else 'where language = "%s" ' ) % lang
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	cur.execute( query )
	# For each media we get
	for id, version, parent_version, language, title, description, owner, \
			editor, timestamp_edit, timestamp_created, published, source, \
			visible, source_system, source_key, rights, type, coverage, \
			relation in cur.fetchall():
		m = dom.createElement("lf:media")
		# Add default elements
		xml_add_elem( dom, m, "dc:identifier",     id )
		xml_add_elem( dom, m, "lf:version",        version )
		xml_add_elem( dom, m, "lf:parent_version", parent_version )
		xml_add_elem( dom, m, "dc:language",       language )
		xml_add_elem( dom, m, "dc:title",          title )
		xml_add_elem( dom, m, "dc:description",    description )
		xml_add_elem( dom, m, "lf:owner",          owner )
		xml_add_elem( dom, m, "lf:editor",         editor )
		xml_add_elem( dom, m, "dc:date",           timestamp_created )
		xml_add_elem( dom, m, "lf:last_edit",      timestamp_edit )
		xml_add_elem( dom, m, "lf:published",      published )
		xml_add_elem( dom, m, "dc:source",         source )
		xml_add_elem( dom, m, "lf:visible",        visible )
		xml_add_elem( dom, m, "lf:source_system",  source_system )
		xml_add_elem( dom, m, "lf:source_key",     source_key )
		xml_add_elem( dom, m, "dc:rights",         rights )
		xml_add_elem( dom, m, "dc:type",           type )

		# Get series
		if with_series:
			cur.execute( '''select bin2uuid(series_id) from lf_media_series 
				where media_id = uuid2bin("%s")''' % id )
			for (series_id,) in cur.fetchall():
				xml_add_elem( dom, m, "lf:series_id", series_id )

		# Get contributor (user)
		if with_contributor:
			cur.execute( '''select user_id from lf_media_contributor
				where media_id = uuid2bin("%s")''' % id )
			for (user_id,) in cur.fetchall():
				xml_add_elem( dom, m, "lf:contributor", user_id )

		# Get creator (user)
		if with_creator:
			cur.execute( '''select user_id from lf_media_creator
				where media_id = uuid2bin("%s")''' % id )
			for (user_id,) in cur.fetchall():
				xml_add_elem( dom, m, "lf:creator", user_id )

		# Get publisher (organization)
		if with_publisher:
			cur.execute( '''select organization_id from lf_media_publisher
				where media_id = uuid2bin("%s")''' % id )
			for (organization_id,) in cur.fetchall():
				xml_add_elem( dom, m, "lf:publisher", organization_id )

		# Get files
		if with_file:
			cur.execute( '''select bin2uuid(id), format, uri,
				source, source_key, source_system from lf_prepared_file
				where media_id = uuid2bin("%s")''' % id )
			for id, format, uri, src, src_key, src_sys in cur.fetchall():
				f = dom.createElement("lf:file")
				xml_add_elem( dom, f, "dc:identifier",    id )
				xml_add_elem( dom, f, "dc:format",        format )
				xml_add_elem( dom, f, "lf:uri",           uri )
				xml_add_elem( dom, f, "lf:source",        src )
				xml_add_elem( dom, f, "lf:source_key",    src_key )
				xml_add_elem( dom, f, "lf:source_system", src_sys )
				m.appendChild(f)

		# Get subjects
		if with_subject:
			cur.execute( '''select s.name from lf_media_subject ms 
					join lf_subject s on s.id = ms.subject_id 
					where s.language = "%s" 
					and ms.media_id = uuid2bin("%s") ''' % (language, id) )
			for (subject,) in cur.fetchall():
				xml_add_elem( dom, m, "dc:subject", subject )


		dom.childNodes[0].appendChild(m)

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/view/series/')
@app.route('/view/series/<series_id>')
@app.route('/view/series/<series_id>/<lang>')
def list_series(series_id=None, lang=None):

	# Check flags for additional data
	with_media       = is_true(request.args.get('with_media',       '1'))
	with_creator     = is_true(request.args.get('with_creator',     '1'))
	with_publisher   = is_true(request.args.get('with_publisher',   '1'))
	with_subject     = is_true(request.args.get('with_subject',     '1'))

	db = get_db()
	cur = db.cursor()
	query = '''select bin2uuid(id), version, parent_version, title,
			language, description, source, timestamp_edit, timestamp_created,
			published, owner, editor, visible, source_key, source_system 
			from lf_published_series '''
	if series_id:
		# abort with 400 Bad Request if series_id is not a valid uuid or thread it
		# as language code if language argument does not exist
		if is_uuid(series_id):
			query += 'where id = uuid2bin("%s") ' % series_id
		else:
			if lang:
				abort(400)
			else:
				lang = series_id

	# Check for language argument
	if lang:
		for c in lang:
			if c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_':
				abort(400)
		query += ( 'and language = "%s" ' \
				if 'where id' in query \
				else 'where language = "%s" ' ) % lang
	cur.execute( query )
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	# For each media we get
	for id, version, parent_version, title, language, description, source, \
			timestamp_edit, timestamp_created, published, owner, editor, \
			visible, source_key, source_system in cur.fetchall():
		s = dom.createElement('lf:series')
		xml_add_elem( dom, s, "dc:identifier",     id )
		xml_add_elem( dom, s, "lf:version",        version )
		xml_add_elem( dom, s, "lf:parent_version", parent_version )
		xml_add_elem( dom, s, "dc:title",          title )
		xml_add_elem( dom, s, "dc:language",       language )
		xml_add_elem( dom, s, "dc:description",    description )
		xml_add_elem( dom, s, "dc:source",         source )
		xml_add_elem( dom, s, "lf:last_edit",      timestamp_edit )
		xml_add_elem( dom, s, "dc:date",           timestamp_created )
		xml_add_elem( dom, s, "lf:published",      published )
		xml_add_elem( dom, s, "lf:owner",          owner )
		xml_add_elem( dom, s, "lf:editor",         editor )
		xml_add_elem( dom, s, "lf:visible",        visible )
		xml_add_elem( dom, s, "lf:source_key",     source_key )
		xml_add_elem( dom, s, "lf:source_system",  source_system )
		dom.childNodes[0].appendChild(s)

		# Get media
		if with_media:
			cur.execute( '''select bin2uuid(media_id) from lf_media_series 
				where series_id = uuid2bin("%s")''' % id )
			for (media_id,) in cur.fetchall():
				xml_add_elem( dom, s, "lf:media_id", media_id )

		# Get creator (user)
		if with_creator:
			cur.execute( '''select user_id from lf_series_creator
				where series_id = uuid2bin("%s")''' % id )
			for (user_id,) in cur.fetchall():
				xml_add_elem( dom, s, "lf:creator", user_id )

		# Get publisher (organization)
		if with_publisher:
			cur.execute( '''select organization_id from lf_series_publisher
				where series_id = uuid2bin("%s")''' % id )
			for (organization_id,) in cur.fetchall():
				xml_add_elem( dom, s, "lf:publisher", organization_id )

		# Get subjects
		if with_subject:
			cur.execute( '''select s.name from lf_series_subject ms 
					join lf_subject s on s.id = ms.subject_id 
					where s.language = "%s" 
					and ms.series_id = uuid2bin("%s") ''' % (language, id) )
			for (subject,) in cur.fetchall():
				xml_add_elem( dom, s, "dc:subject", subject )

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/view/subject/')
@app.route('/view/subject/<subject_id>')
@app.route('/view/subject/<subject_id>/<lang>')
def list_subject(subject_id=None, lang=None):

	db = get_db()
	cur = db.cursor()
	query = '''select id, name, language from lf_subject '''
	if subject_id:
		# abort with 400 Bad Request if subject_id is not valid or thread it
		# as language code if language argument does not exist
		try:
			query += 'where id = %s ' % int(subject_id)
		except ValueError:
			# subject_id is not valid
			if lang:
				abort(400)
			else:
				lang = subject_id

	# Check for language argument
	if lang:
		for c in lang:
			if c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_':
				abort(400)
		query += ( 'and language = "%s" ' \
				if 'where id' in query \
				else 'where language = "%s" ' ) % lang
	cur.execute( query )
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	# For each media we get
	for id, name, language in cur.fetchall():
		s = dom.createElement('lf:subject')
		xml_add_elem( dom, s, "lf:id",       id )
		xml_add_elem( dom, s, "lf:name",     name )
		xml_add_elem( dom, s, "dc:language", language )
		dom.childNodes[0].appendChild(s)

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/view/file/')
@app.route('/view/file/<file_id>')
def list_file(file_id=None):
	db = get_db()
	cur = db.cursor()
	query = '''select bin2uuid(id), format, uri, bin2uuid(media_id),
				source, source_key, source_system from lf_prepared_file '''
	if file_id:
		# abort with 400 Bad Request if file_id is not valid
		if is_uuid(file_id):
			query += 'where id = uuid2bin("%s") ' % file_id
		else:
			abort(400)

	cur.execute( query )
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	# For each file we get
	for id, format, uri, media_id, src, src_key, src_sys in cur.fetchall():
		f = dom.createElement("lf:file")
		xml_add_elem( dom, f, "dc:identifier",    id )
		xml_add_elem( dom, f, "dc:format",        format )
		xml_add_elem( dom, f, "lf:uri",           uri )
		xml_add_elem( dom, f, "lf:media_id",      media_id )
		xml_add_elem( dom, f, "lf:source",        src )
		xml_add_elem( dom, f, "lf:source_key",    src_key )
		xml_add_elem( dom, f, "lf:source_system", src_sys )
		dom.childNodes[0].appendChild(f)

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/view/organization/')
@app.route('/view/organization/<organization_id>')
def list_organization(organization_id=None):
	db = get_db()
	cur = db.cursor()
	query = '''select id, name, vcard_uri, parent_organization 
			from lf_organization '''
	if organization_id:
		# abort with 400 Bad Request if file_id is not valid
		try:
			query += 'where id = %s ' % int(organization_id)
		except ValueError:
			abort(400)

	cur.execute( query )
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	# For each file we get
	for id, name, vcard_uri, parent_organization in cur.fetchall():
		o = dom.createElement("lf:organization")
		xml_add_elem( dom, o, "dc:identifier",             id )
		xml_add_elem( dom, o, "lf:name",                   name )
		xml_add_elem( dom, o, "lf:parent_organization_id", parent_organization )
		xml_add_elem( dom, o, "lf:vcard_uri",              vcard_uri )
		dom.childNodes[0].appendChild(o)

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/view/group/')
@app.route('/view/group/<group_id>')
def list_group(group_id=None):
	db = get_db()
	cur = db.cursor()
	query = '''select id, name from lf_group '''
	if group_id:
		# abort with 400 Bad Request if id is not valid
		try:
			query += 'where id = %s ' % int(group_id)
		except ValueError:
			abort(400)

	cur.execute( query )
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	# For each file we get
	for id, name in cur.fetchall():
		g = dom.createElement("lf:group")
		xml_add_elem( dom, g, "dc:identifier", id )
		xml_add_elem( dom, g, "lf:name",       name )
		dom.childNodes[0].appendChild(g)

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/view/user/')
@app.route('/view/user/<user_id>')
def list_user(user_id=None):
	db = get_db()
	cur = db.cursor()
	query = '''select id, name, vcard_uri from lf_user '''
	if user_id:
		# abort with 400 Bad Request if id is not valid
		try:
			query += 'where id = %s ' % int(user_id)
		except ValueError:
			abort(400)

	cur.execute( query )
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	# For each file we get
	for id, name, vcard_uri in cur.fetchall():
		u = dom.createElement("lf:user")
		xml_add_elem( dom, u, "dc:identifier", id )
		xml_add_elem( dom, u, "lf:name",       name )
		xml_add_elem( dom, u, "lf:vcard_uri",  vcard_uri )
		dom.childNodes[0].appendChild(u)

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	db.execute('insert into entries (title, text) values (?, ?)',
			[request.form['title'], request.form['text']])
	db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)


@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))


if __name__ == '__main__':
	app.run()
