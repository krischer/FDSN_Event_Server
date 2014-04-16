#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict
import fnmatch
import obspy
import os
import re
import shelve
import warnings
import uuid


class EventShelveException(Exception):
    """
    Exception raised by this module.
    """
    pass


class EventShelveWarning(UserWarning):
    """
    Warning raised by this module.
    """
    pass


class EventShelve(object):
    def __init__(self, shelve_path, root_folder, quakeml_glob_expr,
                 regex_expr=None):
        """
        Initializes the EventShelve object.

        :param shelve_path:
        :param root_folder:
        :param quakeml_glob_expr:
        :param regex_expr:
        """
        self._s = shelve.open(shelve_path)

        # First step is to get all files.
        quakeml_filenames = []
        for root, _, filenames in os.walk(root_folder):
            for filename in fnmatch.filter(filenames, quakeml_glob_expr):
                quakeml_filenames.append(os.path.abspath(
                    os.path.join(root, filename)))

        quakeml_filenames = set(quakeml_filenames)
        filenames_in_shelve = set(self._s.keys())

        # Delete all files no longer available.
        to_be_removed = filenames_in_shelve - quakeml_filenames
        for filename in to_be_removed:
            del self._s[filename]

        filenames_in_shelve = set(self._s.keys())

        # Find files that need to be added.
        to_be_added = quakeml_filenames - filenames_in_shelve
        for _i, filename in enumerate(to_be_added):
            print("Indexing file %i: %s ..." % (_i, filename))
            cat = obspy.readEvents(filename)
            if len(cat) == 0:
                continue
            elif len(cat) > 1:
                msg = ("File '%s' contains %i events. Only one event per "
                       "file is supported. Will be skipped." %
                       (filename, len(cat)))
                warnings.warn(msg)
                continue

            ev = cat[0]

            # Get the event id used for that event.
            event_id = None
            if regex_expr is not None:
                match = re.match(regex_expr, ev.resource_id.id)
                if match:
                    try:
                        event_id = match.group(1)
                    except IndexError:
                        pass
            if not event_id:
                event_id = str(uuid.uuid4())

            origin = ev.preferred_origin() or ev.origins[0]
            magnitude = ev.preferred_magnitude() or ev.magnitudes[0]

            event_info = {
                "event_id": event_id,
                "latitude": origin.latitude,
                "longitude": origin.longitude,
                "time": origin.time,
                "depth_in_km": origin.depth / 1000.0,
                "magnitude": magnitude.mag,
                "magnitude_type": magnitude.magnitude_type
            }

            self._s[filename] = event_info

        # Copy to in memory dictionary.
        self.events = OrderedDict(self._s)

        # Close shelve.
        self._s.close()

    def query(self, starttime=None, endtime=None, minlatitude=None,
              maxlatitude=None, minlongitude=None, maxlongitude=None,
              latitude=None, longitude=None, maxradius=None, minradius=None,
              mindepth=None, maxdepth=None, minmagnitude=None,
              maxmagnitude=None, limit=None, offset=1, orderby="time",
              event_id=None, query_id=None, **kwargs):
        """
        FDSN event service like queries.
        """
        counter = 0
        actually_used_counter = 0

        found_events = {}

        # Find all events according to the query.
        for filename, event in self.events.iteritems():
            if (event_id is None or event["event_id"] == event_id) and \
                    (starttime is None or event["time"] >= starttime) and \
                    (endtime is None or event["time"] <= endtime) and \
                    (minlatitude is None or
                     event["latitude"] >= float(minlatitude)) and \
                    (maxlatitude is None or
                     event["latitude"] <= float(maxlatitude)) and \
                    (minlongitude is None or
                     event["longitude"] >= float(minlongitude)) and \
                    (maxlongitude is None or
                     event["longitude"] <= float(maxlongitude)) and \
                    (mindepth is None or
                     event["depth"] >= float(mindepth)) and \
                    (maxdepth is None or
                     event["depth"] <= float(maxdepth)) and \
                    (minmagnitude is None or
                     event["magnitude"] >= float(minmagnitude)) and \
                    (maxmagnitude is None or
                     event["magnitude"] <= float(maxmagnitude)):
                counter += 1
                if counter <= offset:
                    continue
                actually_used_counter += 1
                if limit is not None and limit >= actually_used_counter:
                    break
                found_events[filename] = event

        print "Found events:", len(found_events)
        if not found_events:
            return None

        # Sort the events.
        if orderby == "time":
            found_events = OrderedDict(sorted(found_events.iteritems(),
                                       key=lambda x: x[1]["time"]))
        elif orderby == "time-asc":
            found_events = OrderedDict(sorted(found_events.iteritems(),
                                       key=lambda x: x[1]["time"])[::-1])
        elif orderby == "magnitude":
            found_events = OrderedDict(sorted(found_events.iteritems(),
                                              key=lambda x: x[1]["time"]))
        elif orderby == "magnitude-asc":
            found_events = OrderedDict(sorted(
                found_events.iteritems(),
                key=lambda x: x[1]["magnitude"])[::-1])
        else:
            msg = ("orderby '%s' is not valid. Valid orderings: 'time', "
                   "'time-asc', 'magnitude', 'magnitude-asc'" % orderby)
            raise ValueError(msg)

        if query_id is None:
            query_id = "smi:local/%s" % str(uuid.uuid4())
        else:
            query_id = "smi:" + query_id.replace("http://", "")

        cat_str = ("<?xml version='1.0' encoding='utf-8'?>\n"
                   '<ns0:quakeml xmlns:ns0="http://quakeml.org/xmlns/quakeml/'
                   '1.2" xmlns="http://quakeml.org/xmlns/bed/1.2">\n'
                   '  <eventParameters publicID="%s">\n'
                   "    {events}\n"
                   "  </eventParameters>\n"
                   "</ns0:quakeml>" % query_id)

        pattern = re.compile(r"<event\s.*<\/event>", re.DOTALL)
        event_strings = []
        for filename in found_events.iterkeys():
            with open(filename, "rt") as fh:
                event_str = fh.read()
                event_str = re.findall(pattern, event_str)[0]
                if event_str is None:
                    msg = ("Could not extract event string from event '%'. "
                           "Will be skipped." % filename)
                    warnings.warn(EventShelveWarning)
                    continue
                event_strings.append(event_str)

        cat_str = cat_str.format(events="\n    ".join(event_strings))
        return cat_str

    def __del__(self):
        self._s.close()
