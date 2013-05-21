# -*- coding: utf-8 -*-

# Data of the redis storage
DATABASE_HOST   = 'localhost'
DATABASE_PORT   = 6379
DATABASE_DB     = 0
DATABASE_PASSWD = None

# Location of the core webservice
LERNFUNK_CORE_PROTOCOL = 'http'
LERNFUNK_CORE_HOST     = 'localhost'
LERNFUNK_CORE_PORT     = 5000
LERNFUNK_CORE_PATH     = '/'

# The minimum time between two feed updates.
FEED_UPDATE_TIME = '00:10:00'

# Feed updates are normally done asynchronously. Meaning that the request which
# triggered the update will not get the result of the update but the old data
# instead. You can, however, force the service to do the update synchronously
# if the feed age exceeds a specific limit:
FEED_UPDATE_TIME_SYNC = '00:45:00'

# The following title will be displayed as header of the html page listing all
# available feeds:
FEED_HTML_TITLE = u'University of Osnabrück: Feeds'

# Location of the logfile to write errors to if not in debug mode.
LOGFILE = 'lernfunk.feedgenerator.log'

# The minimum time between two updates of the information page which displays
# all available feeds.
INFO_UPDATE_TIME = '01:00:00'

# Minimum time before a synchronous update of the information page.
INFO_UPDATE_TIME_SYNC = '04:00:00'
