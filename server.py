#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flask
from flask.ext.cache import Cache

import inspect
import obspy
import os

import config
from event_shelve import EventShelve

ROOT_URL = "/fdsnws/event/1/"

PATH = os.path.dirname(os.path.abspath(inspect.getfile(
    inspect.currentframe())))


app = flask.Flask("FDSNEventService")
cache = Cache(app, config={"CACHE_TYPE": "simple"})

print("Initializing event shelve...")
# Init the event shelve.
event_shelve = EventShelve(
    shelve_path=config.SHELVE_DB_PATH,
    root_folder=config.QUAKEML_ROOT_DIR,
    quakeml_glob_expr=config.QUAKEML_FILES_GLOB,
    regex_expr=config.REGEX_FOR_EVENT_ID)
print("Done initializing event shelve...")


@app.route(ROOT_URL + "version")
def version():
    """
    Return the version string of the webservice.
    """
    return "0.0.1"


@app.route(ROOT_URL + "application.wadl")
@cache.cached()
def wadl():
    """
    Return the WADL file.
    """
    with open(os.path.join(PATH, "application.wadl"), "rb") as fh:
        wadl_string = fh.read()
    return wadl_string


@app.route(ROOT_URL + "query")
def query():
    """
    The actual query route.
    """
    arguments = {key: value for key, value in flask.request.args.items()}

    # Map short to long arguments.
    mappings = {
        "start": "starttime",
        "end": "endtime",
        "minlat": "minlatitude",
        "maxlat": "maxlatitude",
        "minlon": "minlongitude",
        "maxlon": "maxlongitude",
        "lat": "latitude",
        "lon": "longitude",
        "minmag": "minmagnitude",
        "maxmag": "maxmagnitude",
    }
    for key, value in mappings.items():
        if key in arguments:
            arguments[value] = arguments[key]

    # Convert times.
    if "starttime" in arguments:
        arguments["starttime"] = obspy.UTCDateTime(arguments["starttime"])
    if "endtime" in arguments:
        arguments["endtime"] = obspy.UTCDateTime(arguments["endtime"])
    arguments["query_id"] = flask.request.base_url

    cat = event_shelve.query(**arguments)

    if cat is None:
        return ("Request was properly formatted and submitted but no data "
                "matches the selection", 204, {})

    return cat


if __name__ == "__main__":
    if config.PUBLIC is True:
        app.run(host="0.0.0.0", port=config.PORT)
    else:
        app.run(port=config.PORT)
