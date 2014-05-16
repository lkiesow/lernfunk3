#!/bin/env python
# -*- coding: utf-8 -*-
'''
	Lernfunk3: Matterhorn Import Service
	====================================

	:copyright: 2013, Lars Kiesow <lkiesow@uos.de>

	:license: FreeBSD and LGPL, see LICENSE for more details.
'''

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import getopt
import matterhornimport



def usage():
	print 'Usage: python -m matterhornimport <mediapackage.xml> | --server [ opts ]'
	print ''
	print 'opts:'
	print '  --debug        -- Enable debug mode of build-in webserver'
	print '  --help         -- Show this help'
	print '  --host=0.0.0.0 -- Host of the build-in webserver'
	print '  --port=5001    -- Port of the build-in webserver'
	print '  --server       -- Run as webservice using the build-in webserver'



def main():
	'''Reads a mediapackage in XML format which is passed as first command line
	argument and starts the import.

	Usage: matterhorn-import.py <mediapackage.xml>
	'''
	webserver = False
	port  = 5001
	host  = '0.0.0.0'
	debug = False

	try:
		opts, args = getopt.getopt(sys.argv[1:], "h",
				["--help", "port=", 'host=', 'server', 'debug'])
		for opt, arg in opts:
			if opt in ("-h", "--help"):
				usage()
				sys.exit()
			if opt == '--port':
				port = int(arg)
			if opt == '--host':
				host = arg
			if opt == '--server':
				webserver = True
			if opt == '--debug':
				debug = True
	except (getopt.GetoptError, ValueError):
		usage()
		sys.exit(2)

	if webserver:
		matterhornimport.app.run(host=host, port=port, debug=debug)
	else:
		if len(args) != 1:
			usage()
			exit(1)
		if matterhornimport.program( args[0] ):
			print( 'Import successful' )
		else:
			print( 'Import failed. See logs for more details' )



if __name__ == "__main__":
	main()
