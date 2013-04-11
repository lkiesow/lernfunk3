Configuration
=============

The Lernfunk3 Matterhorn import module can be highly configured. Options that can be set:

* Access data to the Core Webservice
* Debugging and logging settings
* Archive of imported Mediapackages
* Default values (Used if not present in the Mediapackage or linked dublincore catalogues)
* What should be imported:
   * Tracks
   * Metadata
   * Attachments

Import Rules
------------

Import rules can be defined for *tracks*, *metadata* and *attachments*. Only
those elements of a Matterhorn Mediapackage which matches one of the defined
rules are imported. The rules can also be used to overwrite certain vales of
the imported objects. If more than one ruleset applies, the first one is used.

A ruleset can contain three types of rules. First, the rules which require that
a certain value is not prsent. These rules always have a minus sign as prefix.
Second, the rules which require the presence of a certain value. They have no
prefix. And third the rules which add or overwrite certain data. They have
"lf-" as prefix.

   "name"          : "import-hq-mp4",
   "comment"       : "Import WebM",

   "extension"     : ".mp4",
   "mimetype" : "image/jpeg",
   "protocol"      : "http",
   "source_system" : "localhost",
   "tags"          : [ "publish", "high-quality", "engage" ],
   "type"          : "presenter/delivery",

   "-tags"         : [ "test" ],

   "lf-format"     : "video/webm",
   "lf-quality"    : "high",
   "lf-server-id"  : "video2uos"
   "lf-source"     : "http://video2.virtuos.uos.de:8080"
   "lf-type"       : "video/mp4",

   "use-for"  : "media"

Example::

   {
      "lf-url" : "http://localhost:5000",
      "username" : "lkiesow",
      "password" : "test",
      "logfile"  : "matterhorn-import.log",
      "loglovel" : "debug",
      "defaults" : {
         "language" : "de",
         "visibility" : 1,
         "published" : 1,
         "publisher" : [1],
         "contributor" : []
      },
      "delimeter": {
         "creator"     : ";",
         "contributor" : ";",
         "subject"     : ";,"
      },
      "trackrules" : [
         {
            "name"          : "import-webm",
            "comment"       : "Import WebM",
            "mimetype"      : "video/webm",
            "tags"          : [ "publish", "web" ],
            "extension"     : ".webm",
            "protocol"      : "http",
            "-tags"         : [ "test" ],
            "source_system" : "localhost",
            "lf-format"     : "video/webm",
            "lf-type"       : "vga",
            "lf-quality"    : "high",
            "lf-source"     : "http://video2.virtuos.uos.de:8080"
         },{
            "name"          : "import-hq-mp4",
            "comment"       : "Import mp4 files tagged with high-quality",
            "mimetype"      : "video/mp4",
            "tags"          : [ "publish", "high-quality", "engage" ],
            "extension"     : ".mp4",
            "protocol"      : "http",
            "-tags"         : [ "work" ],
            "source_system" : "localhost",
            "type"          : "presenter/delivery",
            "lf-type"       : "video/mp4",
            "lf-quality"    : "high-quality",
            "lf-server-id"  : "video2uos"
         }
      ],
      "metadatarules" : [
         {
            "name"     : "import-episode-dc",
            "comment"  : "Import DC episode data",
            "mimetype" : "text/xml",
            "tags"     : [ "publish" ],
            "type"     : "dublincore/episode",
            "use-for"  : "media"
         }, {
            "name"     : "import-series-dc",
            "comment"  : "Import DC series data",
            "mimetype" : "text/xml",
            "tags"     : [ "publish" ],
            "type"     : "dublincore/series",
            "use-for"  : "series"
         }
      ],
      "attachmentrules" : [
         {
            "name"     : "import-preview-image",
            "comment"  : "Import player preview image",
            "mimetype" : "image/jpeg",
            "tags"     : [ "publish", "engage" ],
            "type"     : "presenter/player+preview"
         }
      ]
   }
