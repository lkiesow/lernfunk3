#!/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import os
import time
import datetime
import MySQLdb
import uuid
from xml.dom.minidom import parse
from string import letters

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# List of matterhorn search services:
services = [
		'http://video2.virtuos.uos.de:8080/search/'
	]

endpoints = {
			'series' : 'series.xml?limit=999999&episodes=false&series=true',
			'episodes' : 'episode.xml?limit=999999&sid=%s'
		}

#		'http://video2.virtuos.uos.de:8080/search/series.xml' \
#				'?limit=999999&episodes=true&series=true'

__LF3DB = {
			'host'   : 'localhost',
			'db'     : 'lernfunk3',
			'user'   : 'root',
			'passwd' : '',
			'port'   : 3306
		}

__INSERT_AS = {
			'user'  : 'admin',
			'group' : 'admin'
		}


lf3db = MySQLdb.connect(
	host    = __LF3DB['host'],
	user    = __LF3DB['user'],
	passwd  = __LF3DB['passwd'],
	db      = __LF3DB['db'],
	port    = __LF3DB['port'],
	charset = 'utf8' )

cur = lf3db.cursor()


def getTextByTagName(node, tag):
	rc = []
	for nodes in node.getElementsByTagName(tag):
		for node in nodes.childNodes:
			if node.nodeType == node.TEXT_NODE:
				rc.append(node.data)
	return ''.join(rc)



def getText(nodes):
	rc = []
	for node in nodes.childNodes:
		if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
	return ''.join(rc)



def getUserId( cur, username=None, realname=None ):
	query = 'select id from lf_user '
	
	if realname:
		query += 'where realname = "%s" ' % realname
	if username:
		query += ( 'and ' if realname else 'where ' ) + \
				'name = "%s" ' % username
	cur.execute(query)
	ids = []
	for ( id, ) in cur.fetchall():
		ids.append( id )
	return ids



def addSeriesCreator(series, username=None, realname=None):
	query = '''select count(id) from lf_user 
			where realname = "%s" ''' % str(creator_realname).translate(None, '";')
	cur.execute( query )
	usercount = cur.fetchone()[0]
	if not usercount:
		usercount = 1
		# Get a unique username
		while usercount:
			query = '''select count(id) from lf_user 
					where name = "%s" ''' % creator_username
			cur.execute( query )
			usercount = cur.fetchone()[0]
			if usercount:
				creator_username += str(usercount)
		# Create new user
		query = '''insert into lf_user (name,realname) values ("%s","%s") ''' % \
				( creator_username, str(creator_realname).translate(None, '"') )
		cur.execute( query )
		lf3db.commit()
		id = getUserId( cur, username=creator_username,
				realname=str(creator_realname).translate(None, '"') )[0]
		print('User created [id=%i]' % id )
	elif usercount == 1:
		id = getUserId( cur, realname=str(creator_realname).translate(None, '"') )[0]
		print('User exists [id=%i]' % id )



def mysql_escape( s ):
	if s is None:
		return s
	return ''.join([ '\\'+c if c in '\\"' else c for c in s ])



def mysql_quote( s ):
	if s is None:
		return 'NULL'
	return '"%s"' % s



def new_series( service, result, user ):
	title            = mysql_escape(getTextByTagName(result, 'dcTitle'))
	creator_realname = mysql_escape(getTextByTagName(result, 'dcCreator'))
	creator_username = ''.join([ c if c in letters else '' \
			for c in creator_realname ]).lower()
	institute   = mysql_escape(getTextByTagName(result, 'dcContributor'))
	language    = mysql_escape(getTextByTagName(result, 'dcLanguage'))
	rights      = mysql_escape(getTextByTagName(result, 'dcLicense'))
	description = mysql_escape(getTextByTagName(result, 'dcDescription'))
	identifier  = mysql_escape(result.getAttribute('id'))

	# Return if series exists
	cur.execute('''select count(id) from lf_series 
			where source_key = %s ''' % mysql_quote(identifier) )
	if cur.fetchone()[0]:
		return
	# TODO: Add media to existing series

	# Generate new id for series
	series_id = None
	try:
		series_id = uuid.UUID(identifier)
		cur.execute('''select count(id) from lf_series
				where id = unhex("%s") ''', series_id.hex )
		if cur.fetchone()[0]:
			raise ValueError('Id already exists for a different series')
	except ValueError as e:
		print( 'series: %s' % e )
		series_id = uuid.uuid4()

	query = '''insert into lf_series 
			( id, title, language, description, published, 
				owner, editor, source_system, source_key) 
			values ( x'%s', %s, %s, %s, %s, %s, %s, %s, %s) ''' % \
				( series_id.hex, mysql_quote(title), mysql_quote(language),
						mysql_quote(description), 1, user, user, 
						'"video2.virtuos.uos.de"', mysql_quote(identifier) )
	cur.execute( query )
	lf3db.commit()

	if creator_realname:
		# Insert in lf_series_creator
		# TODO: Implement it!
		pass

	# Get media
	f = urllib2.urlopen( service + endpoints['episodes'] % series_id )
	mediaxml = parse(f)
	f.close()

	for result in mediaxml.getElementsByTagName('result'):
		# Check if result is a media object
		if getTextByTagName(result, 'mediaType') == 'AudioVisual':
			new_media( service, result, user, series_id )




def new_media( service, result, user, series_id ):
	mediapackage     = result.getElementsByTagName('mediapackage')[0]
	title            = mysql_escape(getTextByTagName(result, 'dcTitle'))
	series           = mysql_escape(getTextByTagName(result, 'dcIsPartOf'))
	creator_realname = mysql_escape(getTextByTagName(result, 'dcCreator'))
	creator_username = ''.join([ c if c in letters else '' \
			for c in creator_realname ]).lower()
	institute        = mysql_escape(getTextByTagName(result, 'dcContributor'))
	language         = mysql_escape(getTextByTagName(result, 'dcLanguage'))
	rights           = mysql_escape(getTextByTagName(result, 'dcLicense'))
	description      = mysql_escape(getTextByTagName(result, 'dcDescription'))
	identifier       = mysql_escape(result.getAttribute('id'))
	subject          = mysql_escape(getTextByTagName(result, 'dcSubject'))
	created          = mysql_escape(getTextByTagName(result, 'dcCreated'))

	# Return if series exists
	cur.execute('''select count(id) from lf_media
			where source_key = %s ''' % mysql_quote(identifier) )
	if cur.fetchone()[0]:
		return

	# Generate new id for series
	media_id = None
	try:
		media_id = uuid.UUID(identifier)
		cur.execute('''select count(id) from lf_series
				where id = unhex("%s") ''', media_id.hex )
		if cur.fetchone()[0]:
			raise ValueError('Id already exists for a different media (%s)' % identifier)
	except ValueError as e:
		print( 'media: %s (%s)' % (e, identifier) )
		media_id = uuid.uuid4()

	if creator_realname:
		# Insert in lf_series_creator
		pass

	query = '''insert into lf_media 
			( id, title, language, description, published, timestamp_created,
				owner, editor, source_system, source_key, type) 
			values ( x'%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ) ''' % \
				( media_id.hex, mysql_quote(title), mysql_quote(language),
						mysql_quote(description), 1, mysql_quote(created),
						user, user, '"matterhorn13@video2.virtuos.uos.de"', 
						mysql_quote(identifier), '"MovingImage"' )
	cur.execute( query )

	query = '''insert into lf_media_series 
			( series_id, media_id, series_version, media_version )
			values ( x'%s', x'%s', %i, %i ) ''' % \
					( series_id.hex, media_id.hex, 0, 0 )
	cur.execute( query )
	lf3db.commit()

	# Get files:
	for track in mediapackage.getElementsByTagName('track'):
		new_file( track, media_id )



def new_file( trackxml, media_id ):
	identifier = trackxml.getAttribute('ref').split(':', 1)[-1]
	type       = trackxml.getAttribute('type')

	mimetype   = getTextByTagName(trackxml, 'mimetype')
	if not mimetype in ['audio/mp3', 'video/mp4']:
		# We don't want other tracks
		return

	tags = []
	for tag in trackxml.getElementsByTagName('tag'):
		tags.append(getText(tag))
	# Check if track should be published
	if not 'publish' in tags:
		return

	acceped_qualities = ['mobile', 'high-quality', 'hd-quality']
	quality = None
	for q in acceped_qualities:
		if q in tags:
			quality = q
			break
	if not quality:
		return

	type_conversion = {
			'presentation/delivery' : 'vga',
			'presenter/delivery'    : 'dozent'
			}
	try:
		type = type_conversion[type]
	except KeyError:
		type = None

	url = getTextByTagName( trackxml, 'url' )
	if url.startswith('rtmp://'):
		# We don't want RTMP streams
		return

	# Generate new id for series
	track_id = None
	try:
		track_id = uuid.UUID(identifier)
		cur.execute('''select count(id) from lf_file
				where id = x'%s' ''' % track_id.hex )
		if cur.fetchone()[0]:
			raise ValueError('Id already exists for a different file')
	except ValueError as e:
		print( 'file: %s' % e )
		track_id = uuid.uuid4()

	query = '''insert into lf_file
			( id, media_id, format, type, quality, server_id, uri, 
				source, source_system, source_key )
			values ( x'%s', x'%s', %s, %s, %s, %s, %s, %s, %s, %s ) ''' % \
					( track_id.hex, media_id.hex, mysql_quote(mysql_escape(mimetype)),
							mysql_quote(type), mysql_quote(quality), 
							mysql_quote('video2uos'), 'NULL', 'NULL', 
							mysql_quote('Matterhorn13'),
							mysql_quote(mysql_escape(identifier)) )
	
	cur.execute( query )
	lf3db.commit()







cur.execute('''select id from lf_user 
		where name = "%s" ''' % __INSERT_AS['user'])
user = cur.fetchone()[0]

cur.execute('''select id from lf_group
		where name = "%s" ''' % __INSERT_AS['group'])
group = cur.fetchone()[0]


try:
	for url in services:
		f = urllib2.urlopen( url + endpoints['series'] )
		seriesxml = parse(f)
		f.close()

		# Get series:
		for result in seriesxml.getElementsByTagName('result'):
			# Check if result is a series
			if getTextByTagName(result, 'mediaType') == 'Series':
				new_series( url, result, user )
except KeyboardInterrupt as e:
	pass
