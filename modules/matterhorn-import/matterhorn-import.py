#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import json
from xml.dom.minidom import parseString
from pprint import pprint


def load_config():
	f = open( 'config.json', 'r')
	config = json.load(f)
	f.close()

	# Check/normalize config
	for entry in config:
		for key in ['name','comment']:
			if not key in entry.keys():
				entry[key] = ''
		for key in ['mimetype', '-mimetype', 'extension', '-extension', \
				'protocol', '-protocol', 'source_system', '-source_system', \
				'lf-quality', 'lf-server-id', 'lf-type']:
			if not key in entry.keys():
				entry[key] = None
		for key in ['tags', '-tags']:
			if not key in entry.keys():
				entry[key] = []

	return config


def import_media( mp ):
	global config

	# This will be a post field:
	source_system = 'localhost'

	mp = parseString( mp )
	for track in mp.getElementsByTagNameNS('*', 'track'):
		mimetype = track.getElementsByTagNameNS('*', 'mimetype')[0].childNodes[0].data
		type = track.getAttribute('type')
		id = track.getAttribute('ref').lstrip('track').lstrip(':')
		tags = [ tag.childNodes[0].data \
				for tag in track.getElementsByTagNameNS('*', 'tag') ]
		url = track.getElementsByTagNameNS('*', 'url')[0].childNodes[0].data

		for c in config:
			# Check rules defined in configuration. If a rule does not apply jump
			# straight to the next set of rules.
			if c['-mimetype'] == mimetype:
				continue
			if c['-extension'] and url.endwith(c['-extension']):
				continue
			if c['-protocol'] and url.startswith(c['-protocol']):
				continue
			if c['-source_system'] == source_system:
				continue
			if c['mimetype'] and c['mimetype'] != mimetype:
				continue
			if c['extension'] and not url.endswith( c['extension'] ):
				continue
			if c['protocol'] and not url.startswith( c['protocol'] ):
				continue
			if c['source_system'] and c['source_system'] != source_system:
				continue
			# Finally check the tags
			if True in [ t in tags for t in c['-tags'] ]:
				continue
			if False in [ t in tags for t in c['tags'] ]:
				continue

			# Build request
			pprint( [id,mimetype,type,tags,url] )

			# Send request
			# http://docs.python.org/2/library/urllib2.html



def main():
	global config
	config = load_config()
	pprint( config )

	f = open( '1363631448.81.xml', 'r' )
	mediapackage = f.read()
	f.close()

	import_media( mediapackage )


if __name__ == "__main__":
	main()
