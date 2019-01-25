#!/usr/bin/env python2
# vim:fileencoding=utf-8

""" Script to download R2 shows. See `r2get -h` for usage. """

from __future__ import print_function

import argparse
import base64
import collections
import datetime
import dateutil.parser
import mutagen.id3
import mutagen.mp4
import mutagen.easymp4
import mutagen.oggvorbis
import mutagen.flac
import json
import os
import re
import subprocess
import tempfile
import sys
import urllib

API_ROOT = "http://r2.err.ee/api"
SERIES_API_URL = API_ROOT + "/radio/getProgramSeriesData?radioId=405"
AIRTIMES_API_URL = API_ROOT + "/category/latest/?categoryId={0}"
PAGEDATA_API_URL = API_ROOT + "/radio/getRadioPageData?contentId={0}"

LOGLEVEL_DEFAULT = 0
LOGLEVEL_DEBUG = 1
LOGLEVEL_INFO = 2

# API access routines

def get_series_id(show_name, allow_partial=False):

    """ Return the series data structure for a show. """

    debug("Loading series attributes from " + SERIES_API_URL, LOGLEVEL_DEBUG)

    series = make_api_request(SERIES_API_URL)
    lname = show_name.lower()

    for s in series:
        incoming_lname = s["name"].lower()
        partial_match = allow_partial and lname in incoming_lname
        full_match = not allow_partial and lname == incoming_lname

        debug(u"Series: {0} ({1})".format(s["name"], s["id"]), LOGLEVEL_INFO)

        if partial_match or full_match:
            return s["id"]

    raise KeyError("Cannot find series ID for {0}".format(show_name))

def get_show_id_at(series_id, show_date=None):

    """ Return ID of the show of a given series, on a given date. Returns
    the most recent show ID if `show_date` is None. May raise a LookupError
    if no show found. Assumes the shows list is sorted chronologically,
    descending.

    TODO: This assumption does not hold. The list has to be sorted
    chronologically.
    """

    message = "Cannot find show for series ID {0}".format(series_id)
    url = AIRTIMES_API_URL.format(series_id)
    now = datetime.datetime.now()

    debug("Loading air times from " + url, LOGLEVEL_DEBUG)
    shows = make_api_request(url)

    for show in shows:
        start_ts = show["scheduleStart"]
        start_time = datetime.datetime.fromtimestamp(start_ts)
        most_recent = not show_date and start_time < now
        correct_date = show_date and show_date == start_time.date()

        debug("Found show ts {0} ({1})".format(start_ts, start_time), LOGLEVEL_INFO)

        if (most_recent or correct_date):
            return show["id"]

    if (show_date):
        message += " on {0}".format(show_date)
    else:
        message += " (most recent)"

    raise LookupError(message)

def get_show_attrs(show_id):

    """ Return attributes of a show as a namedtuple. """

    show_attrs = collections.namedtuple("ShowAttrs", "fullname date stream_urls image_url")
    url = PAGEDATA_API_URL.format(show_id)

    debug("Loading show attributes from " + url, LOGLEVEL_DEBUG)
    show = make_api_request(url)["pageControlData"]

    timestamp = show["pageItem"]["startTime"]
    fullname = show["pageItem"]["programName"]
    date = datetime.datetime.fromtimestamp(timestamp).date()
    stream_urls = get_show_stream_urls(show)
    img_url = get_show_image_url(show)

    return show_attrs(fullname, date, stream_urls, img_url)

def get_show_stream_urls(show):

    """ Helper for extracting the show RTMP stream URL from the show
    structure (pageControlData).
    """

    medias = show["mainContent"]["medias"]
    streams = []

    for m in medias:
        streams.append("http:" + m["src"]["file"])

    return streams

def get_show_image_url(show, preferred_width=1000):

    """ Helper for extracting an image URL from the show structure
    (pageControlData). Attempts to find an image with a width closest to
    `preferred_width`.
    """

    photos = show["pageItem"]["photos"][0]["photoTypes"]
    photo_deltas = []

    for p in photos.values():
        w_delta = abs(preferred_width - int(p["w"]))
        photo_deltas.append([w_delta, p["url"]])

    photo_deltas.sort(key=lambda a: a[0])
    return photo_deltas[0][1]

# Audio retrieval and packaging routines

def download_audio(streams, retries, quick_test=False):

    # Retrieve raw AAC sources to temporary files. Note that `quick_test`
    # doesn't currenty seem to result in functional files.

    dumps = []

    for s in streams:
        d = tempfile.NamedTemporaryFile(suffix='.m4a')
        args = ["curl", "-o", d.name, s]
        resume_flag = False

        debug("Dumping " + s + " to " + d.name)

        if (quick_test):
            args += ["-r", "0-6000000"]
            subprocess.check_call(args)
        else:
            for i in range(0, retries):
                if (i > 0):
                    debug("Retrying (" + str(i+1) + " / " + str(retries) + ")")
                    if (not resume_flag):
                        args += ["-C", "-"]
                        resume_flag = True

                try:
                    subprocess.check_call(args)
                except subprocess.CalledProcessError as e:
                    if (e.returncode == 18 and i < (retries-1)): # incomplete transfer
                        continue
                    else:
                        err("Failed fetching stream after " + str(retries) + " times", e)
                break

        dumps.append(d)

    return dumps

def package_audio(show_name, fullname, showdate, show_imgurl, infns, outputs):

    # Package dumped raw RTMP stream into a proper m4a (aka ipod)
    # container, apply tags including cover art. infns can be a list of
    # strings (file names) or a list of NamedTemporaryFiles. outputs is
    # a dict of output ID - directory mappings.

    showfn_prefix = re.sub(r"\s+", "-", show_name.lower())

    # Fetch cover image

    coverf = urllib.urlopen(show_imgurl)
    if (coverf.info().gettype() != "image/jpeg" or coverf.getcode() != 200):
        warn("Cannot retrieve JPEG cover art")
    cover = coverf.read()

    # Loop over input stream dumps

    for i, infn in enumerate(infns):
        if (len(infns) <= 1):
            showfn_suffix = "-1"
        else:
            showfn_suffix = "-" + str(i + 1)
        if (type(infn) is not str):
            infn = infn.name

        show_index = re.sub(r"-", " ", showfn_suffix)
        show_title = fullname + " " + str(showdate) + show_index

        # Loop over output formats

        for k in outputs:
            outdir = outputs[k]
            showfn = outdir + "/" + showfn_prefix + showfn_suffix

            if (k == "mp3"):
                showfn += ".mp3"
                package_mp3(infn, showfn, show_title, cover)
            if (k == "ogg"):
                showfn += ".ogg"
                package_ogg(infn, showfn, show_title, cover)
            elif (k == "mp4"):
                showfn += ".m4a"
                package_mp4(infn, showfn, show_title, cover)

def package_mp4(infn, outfn, title, cover):
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", infn, "-acodec", "copy", outfn])

    tags = mutagen.mp4.MP4(outfn)
    cover = [mutagen.mp4.MP4Cover(cover)]

    tags["\xa9ART"] = "R2"
    tags["\xa9nam"] = title
    tags["\xa9alb"] = "R2"
    tags["covr"] = cover
    tags.save()

def package_mp3(infn, outfn, title, cover):
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", infn, "-acodec", "libmp3lame", "-q:a", "1", outfn])

    tags = mutagen.id3.ID3(outfn)
    tags.add(mutagen.id3.TPE1(encoding=3, text="R2"))
    tags.add(mutagen.id3.TIT2(encoding=3, text=title))
    tags.add(mutagen.id3.TALB(encoding=3, text="R2"))
    tags.add(mutagen.id3.APIC(encoding=3, type=3, data=cover))
    tags.save()

def package_ogg(infn, outfn, title, cover):
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", infn, "-codec:a", "libvorbis", "-qscale:a", "6", outfn])

    ogg = mutagen.oggvorbis.OggVorbis(outfn)
    ogg.tags["artist"] = u"R2"
    ogg.tags["title"] = title
    ogg.tags["album"] = u"R2"
    write_ogg_image(ogg, cover)
    ogg.save()

# Auxiliary routines

def parse_date(s):

    # Coerce a string into a date object.

    d = dateutil.parser.parse(s)
    return datetime.date(d.year, d.month, d.day)

def parse_command_line():
    parser = argparse.ArgumentParser(description = "Fetch a show from R2.")
    parser.add_argument(
        "-d", "--date",
        help="specify desired show airdate, e.g. \"15\", \"2015-02-12\""
    )
    parser.add_argument(
        "-s", "--skip",
        help="skip download, use specified filename as audio input"
    )
    parser.add_argument(
        "-q", "--quick-test",
        action="store_true",
        help="quick sanity test of the pipeline, download 30 first seconds only"
    )
    parser.add_argument(
        "-p", "--partial-name",
        action="store_true",
        help="allow partial match for show name; only makes sense with -d"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="increase verbosity"
    )
    parser.add_argument(
        "-r", "--retry", type=int, default=5,
        help="number of retries in case of incomplete transfers, default 5"
    )
    parser.add_argument(
        "-D", "--mp4-dir", default=".",
        help="mp4 (unmodified stream) output directory"
    )
    parser.add_argument(
        "--mp3-dir", default=None,
        help="mp3 output directory"
    )
    parser.add_argument(
        "--ogg-dir", default=None,
        help="ogg output directory"
    )
    parser.add_argument("show_name")
    return parser.parse_args()

def gather_outputs(args):
    o = dict()

    if (args.mp4_dir):
        o["mp4"] = args.mp4_dir
    if (args.mp3_dir):
        o["mp3"] = args.mp3_dir
    if (args.ogg_dir):
        o["ogg"] = args.ogg_dir

    for k in o:
        if (not os.access(o[k], os.F_OK or os.W_OK)):
            err(o[k] + " does not exist or isn't writable")

    return o

def make_api_request(url):

    """ Convenience routine to make a HTTP GET API request to a JSON
    endpoint and return the decoded result.
    """

    return json.load(urllib.urlopen(url))

def write_ogg_image(ogg, cover):

    # Write an image block to OGG Vorbis, see
    # http://mutagen.readthedocs.io/en/latest/user/vcomment.html

    picture = mutagen.flac.Picture()
    picture.data = cover
    picture.type = 3
    picture.mime = u"image/jpeg"

    base64_picture = base64.b64encode(picture.write())
    ogg["metadata_block_picture"] = [base64_picture.decode("ascii")]

def debug(msg, verbosity=0):
    if (verbosity > (debug.verbosity or 0)):
        return
    try:
        print(msg, file=sys.stderr)
    except UnicodeEncodeError as e:
        err(
            "Please set PYTHONIOENCODING=UTF-8 to avoid encoding errors " +
            "in case of badly detected or non-Unicode stderr", e
        )

def warn(msg, is_error=0):
    if (is_error):
        msg = "ERROR: " + msg
    else:
        msg = "WARNING: " + msg
    debug(msg)

def err(msg, e=None):

    # If exception `e` is passed, raise it instead of sys.exit-ing

    warn(msg, is_error=1)

    if (e == None):
        sys.exit(1)
    else:
        raise e

def debug_set_verbosity(v):
    debug.verbosity = v;

def main():

    # show_name is the identifier from the command line, possibly
    # partial, used for file names. fullname is the name from R2.

    args = parse_command_line()
    show_name = args.show_name.strip()
    infns = None
    showdate = None

    if (args.skip):
        infns = [args.skip]
    if (args.date):
        showdate = parse_date(args.date)

    debug_set_verbosity(args.verbose)

    outputs = gather_outputs(args)
    series_id = get_series_id(show_name, args.partial_name)
    show_id = get_show_id_at(series_id, showdate)
    show_attrs = get_show_attrs(show_id)

    debug("Show name:\t" + show_attrs.fullname)
    debug("Show date:\t" + str(show_attrs.date))
    debug("Stream URLs:\t" + str(show_attrs.stream_urls))
    debug("Image URL:\t" + show_attrs.image_url)

    if (not infns):
        infns = download_audio(show_attrs.stream_urls, args.retry, args.quick_test)
    package_audio(
        show_name, show_attrs.fullname, show_attrs.date,
        show_attrs.image_url, infns, outputs
    )

main()
