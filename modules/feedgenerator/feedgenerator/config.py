# -*- coding: utf-8 -*-

_DATABASE_HOST   = 'localhost'
_DATABASE_PORT   = 6379
_DATABASE_DB     = 0
_DATABASE_PASSWD = None

_LERNFUNK_CORE_PROTOCOL = 'http'
_LERNFUNK_CORE_HOST     = 'localhost'
_LERNFUNK_CORE_PORT     = 5000
_LERNFUNK_CORE_PATH     = '/'

# The minimum time between two feed updates.
_FEED_UPDATE_TIME                = '00:10:00'

# Feed updates are normally done asynchronously. Meaning that the request which
# triggered the update will not get the result of the update but the old data
# instead. You can, however, force the service to do the update synchronously
# if the feed age exceeds a specific limit:
_FEED_UPDATE_TIME_SYNC = '00:45:00'

_FEED_HTML_TITLE = u'University of Osnabrück: Feeds'
