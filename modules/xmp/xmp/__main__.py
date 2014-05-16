# -*- coding: utf-8 -*-
from xmp import app
import sys
import getopt


def usage():
	opts = [
			'--help, -h       -- Show this help',
			'--port=VAL, -p   -- The port the webserver should listen on (default: 5002)',
			'--debug=VAL, -d  -- Enable or disable debug mode (1=enabled, 2=disabled; default: 0)',
		]
	print('Usage %s [options]\n\nOPTIONS:\n  %s' % \
			(sys.argv[0], '\n  '.join(opts)) )


if __name__ == '__main__':
	port = 5002
	debug=False
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hp:d:",
				["help", "port=", 'deug='])

		for opt, arg in opts:
			if opt in ("-h", "--help"):
				usage()
				exit(0)
			elif opt in ('-p', '--port'):
				port = int(arg)
			elif opt in ('-d', '--debug'):
				debug = int(arg) != 0
	except (getopt.GetoptError, ValueError):
		usage()
		sys.exit(2)
	app.run(debug=debug, port=port)
