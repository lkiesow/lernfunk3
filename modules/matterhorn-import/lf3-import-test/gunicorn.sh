#!/bin/sh
if [ -f 'gunicorn.pid' ]
then
	kill `cat gunicorn.pid`
	usleep 500000
fi
rm -f gunicorn.acess.log gunicorn.error.log
gunicorn -D \
		--pid gunicorn.pid \
		--error-logfile gunicorn.error.log \
		--access-logfile gunicorn.acess.log \
		--log-level debug \
		-w 4 \
		-b 0.0.0.0:5000 \
		import-test:app

usleep 500000
if [ -f 'gunicorn.pid' ]
then
	echo gunicorn succesfull started with pid `cat gunicorn.pid`
else
	echo Failed to start gunicorn
fi
