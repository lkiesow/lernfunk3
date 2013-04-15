About Lernfunk3
===============

The Lernfunk media aggregation, enrichment and distribution system can import
media of any type, administer it, add metadata and export these media. It is
centered around a Core REST webservice. Thus it is easy distributable and
extensible.

The Idea
--------

The basic idea is to have a single system which aggregates all types of media
created and held by other systems and distribute these to the “enduser systems”
(portals, etc.) rather than connecting each “creating” system with every single
portal directly.

This way it is easy to manage all media, its metadat and the places they should
appear from a single system.

::

                              Metadata
                                  |
                                  |     ------------ Portal
        Opencast                  |    /
      Matterhorn 1 ------------   |   /  ------------- RSS/ATOM 
                               \  v  /  /               Feeds
                                \   /  /
     Image  ------------------ Lernfunk3 ------------------- StudIP (LMS)
    Archive                     /   \  \
                               /     \  ------------ Youtube
        Opencast   ------------       \
      Matterhorn 2                     --------- Blogs

Features
--------

- aggregate media from different sources
- distribute media to different destinations
- manage metadata
- versioning of media
- handle different languages

Technical Stuff
---------------

*Python* is the main programming language used for Lernfunk3. However, as the
modules communicate with each other using HTTP you can basically use any
programming language you like for building new modules.

*REST* over HTTP is used for communication between modules. This makes it easy
to create a distributed environment for the system and furthermore does not
enforce the use of a specific programming language or operating system.

*MySQL* is used as database backend.
