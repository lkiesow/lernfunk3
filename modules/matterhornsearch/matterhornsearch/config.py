# -*- coding: utf-8 -*-

# Location of the core webservice
LERNFUNK_CORE_PROTOCOL = 'http'
LERNFUNK_CORE_HOST     = 'localhost'
LERNFUNK_CORE_PORT     = 5000
LERNFUNK_CORE_PATH     = '/'

# Credentials for accessing the core webservice:
LERNFUNK_CORE_USERNAME = 'lkiesow'
LERNFUNK_CORE_PASSWORD = '123'

# Specifies the XMF file repository which is a directory on the filesystem in
# which all XMP files will be stored:
XMP_FILE_REPOSITORY = 'xmpfiles'

# The minimum time between two feed updates.
CACHE_TIME = '00:10:00'

# Location of the logfile to write errors to if not in debug mode.
LOGFILE = 'lernfunk.xmp.log'

# Enable or disable language handling.
# Disabling this will speed up the XMP module.
LANGUAGE_SUPPORT = True

# Only import languages which fit the following regular expression:
# Use IETF language tags.
LANGUAGES = '^(en|de)(-\w+)*$'

# The language which should be assumed if:
# - no language is specified in the dc:language entry
# - LANGUAGE_SUPPORT is set to False
LANGUAGE_DEFAULT = 'de'

# This flag decides that if
# - no language is specified in the dc:language entry
# - LANGUAGE_SUPPORT is set to False
# the system should try to get the entries from the default language.
# If this flag is set to True, entries in the default language will be used if
# they exist. Otherwise the entries with no or the “x-default“ language tag
# will be used. Entries with other tags will not be taken.
# If this flag is set to False, the first entry will always be used regardless
# of its actual language marking and the default language will be assumed.
LANGUAGE_TRY_DEFAULT = True
