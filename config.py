#!/usr/bin/env python
# -*- coding: utf-8 -*-

QUAKEML_ROOT_DIR = "../../data/2014_04_15--VERCE_GCMT_Catalog/quakemls/"
QUAKEML_FILES_GLOB = "*.xml"

SHELVE_DB_PATH = "event_db.shelve"

# The regex used on the resource id of the event to extract the event id. If
# not given or not found, a random one will be used. The first paranthesized
# subgroup will be used, e.g.
# event_id = re.match(REGEX_FOR_EVENT_ID, resource_id).group(1)
#
# The example will extract 'B061690B' from 'smi:local/ndk/B061690B/event'
REGEX_FOR_EVENT_ID = r"\w+\:\w+\/\w+\/(\w+)"
