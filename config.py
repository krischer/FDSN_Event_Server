#!/usr/bin/env python
# -*- coding: utf-8 -*-

# If False the server is only accessible from your own computer.
PUBLIC = False

# The port the webserver will run in.
PORT = 5000

# The directly where the QuakeML files are located. The script will search
# recursively through all subfolders.
QUAKEML_ROOT_DIR = "../../data/2014_04_15--VERCE_GCMT_Catalog/quakemls/"

# A glob expression to find the actual QuakeML files.
QUAKEML_FILES_GLOB = "*.xml"

# The location of the shelve file to store the event information.
SHELVE_DB_PATH = "event_db.shelve"

# The regex used on the resource id of the event to extract the event id. If
# not given or not found, a random one will be used. The first paranthesized
# subgroup will be used, e.g.
# event_id = re.match(REGEX_FOR_EVENT_ID, resource_id).group(1)
#
# The example will extract 'B061690B' from 'smi:local/ndk/B061690B/event'
REGEX_FOR_EVENT_ID = r"\w+\:\w+\/\w+\/(\w+)"
