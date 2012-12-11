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
	with_files       = is_true(request.args.get('with_files',       '0'))

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
		m = dom.createElement("media")
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
				xml_add_elem( dom, m, "lf:series", series_id )

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
		if with_files:
			pass # TODO #########################################################################

		dom.childNodes[0].appendChild(m)

	response = make_response(dom.toxml())
	response.mimetype = 'application/xml'
	return response


@app.route('/view/series/')
@app.route('/view/series/<series_id>')
@app.route('/view/series/<series_id>/<lang>')
def list_series(series_id=None, lang=None):
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
	print(query)
	cur.execute( query )
	dom = parseString('''<result 
			xmlns:dc="http://purl.org/dc/elements/1.1/"
			xmlns:lf="http://lernfunk.de/terms"></result>''')

	# For each media we get
	for id, version, parent_version, title, language, description, source, \
			timestamp_edit, timestamp_created, published, owner, editor, \
			visible, source_key, source_system in cur.fetchall():
		s = dom.createElement('series')
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
		dom.childNodes[0].appendChild(m)

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
