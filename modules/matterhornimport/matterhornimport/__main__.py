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
	print '  --help'
	print '  --port=5001'
	print '  --host=0.0.0.0'



def main():
	'''Reads a mediapackage in XML format which is passed as first command line
	argument and starts the import.

	Usage: matterhorn-import.py <mediapackage.xml>
	'''
	webserver = False
	port = 5001
	host = '0.0.0.0'

	try:                                
		opts, args = getopt.getopt(sys.argv[1:], "h", 
				["--help", "port=", 'host=', 'server']) 
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
	except (getopt.GetoptError, ValueError):
		usage()
		sys.exit(2)

	if webserver:
		matterhornimport.app.run(host=host, port=port)
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
