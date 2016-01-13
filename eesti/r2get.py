#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""
Script to download R2 shows. See `r2get -h` for usage.

Tech notes
----------

Passed parameters:

$SHOW - show name (case-insensitive)
$DATE - show date (optional)

Operation:

1. If $DATE not set, get latest show date from [1].
2. Get show $ID and cover art URL from [2].
3. Fetch show page from [3].
4. Extract RTMP stream URLs.
5. Fetch streams and cover art.
6. Convert streamdumps to a suitable container via ffmpeg.
7. Apply tags, including cover art.

References:

API = "http://r2.err.ee/api/loader"

[1] $API/airtimesforprogram/$SHOW?channel=raadio2&ShowAll=False
[2] $API/GetTimeLineDay/?$DATE
[3] http://r2.err.ee/v/$SHOW/saated/$ID
"""

import argparse
import calendar
import datetime
import dateutil.parser
import mutagen.id3
import mutagen.mp4
import mutagen.easymp4
import mutagen.oggvorbis
import json
import os
import re
import stat
import subprocess
import tempfile
import sys
import urllib
import urlparse

from bs4 import BeautifulSoup

R2_ROOT_URL = "http://r2.err.ee"
API_ROOT_URL = R2_ROOT_URL + "/api/loader"
IMG_ROOT_URL = "http://static.err.ee/gridfs"

LOGLEVEL_DEFAULT = 0
LOGLEVEL_DEBUG = 1
LOGLEVEL_INFO = 2
VERBOSITY = LOGLEVEL_DEFAULT

# API access routines

def get_last_showdate(showname):

	# Return last airdate of a show.

	showid = re.sub(r"\s+", "", showname)

	f = urllib.urlopen(
		API_ROOT_URL + "/airtimesforprogram/" +
		showid + "?channel=raadio2&ShowAll=False"
	)

	tree = json.load(f)
	return parse_date(tree[0]["AirDate"])

def get_show_attrs(showname, date, partial_name):

	# Return the canonical name, GUID and artwork URL
	# of a show on a given date.

	url = \
		API_ROOT_URL + "/GetTimeLineDay/" + \
		"?year=" + str(date.year) + "&month=" + str(date.month) + "&day=" + str(date.day)
	
	debug("Fetching show attributes from " + url, LOGLEVEL_DEBUG)
	
	f = urllib.urlopen(url)
	tree = json.load(f)
	lname = showname.lower()
	sid = None
	arturl = None
	artopts = None
	
	def is_name_match(header_entry):
		header_entry = header_entry.lower()
		
		if (partial_name):
			return (True if header_entry.find(lname) != -1 else False)
		else:
			return header_entry == lname
	
	for i in tree:
		header_entry = i["Header"];
		debug("\tHeader entry: " + header_entry, LOGLEVEL_INFO)
		
		if (is_name_match(header_entry)):
			imgurl = None

			if (i["Image"]):
				imgurl = ""
				imgurl += IMG_ROOT_URL + "/" + i["Image"]
				if (i["ImageResizerOptions"]):
					imgurl += i["ImageResizerOptions"]
				else:
					imgurl += "?width=1200"

			return (
				i["Header"],
				i["Id"],
				imgurl
			)

	raise KeyError(
		"Cannot get show attributes for \"" + showname +
		"\" on " + str(date)
	)

def get_show_streams(showname, sid):

	# Return the RTMP stream URLs of a show with a
	# given GUID.
	
	streams = []
	url = R2_ROOT_URL + "/v/" + showname + "/saated/" + sid
	f = urllib.urlopen(url)
	soup = BeautifulSoup(f, "html.parser")
	
	for stag in soup.findAll("script"):
		suris = re.findall("media\.err\.ee.*?m4a", str(stag))
		for suri in (suris):
			suri = "rtmp://" + re.sub("r2/@", "r2/", suri);
			streams.append(suri)
	
	streams = list_uniq(streams)

	if (len(streams) < 1):
		raise RuntimeError("Cannot retrieve any stream URLs for \"" + showname + "\"")
	return streams

# Audio retrieval and packaging routines

def download_audio(streams, quick_test=False):

	# Dump raw RTMP streams into temporary files.

	dumps = []

	for s in streams:
		d = tempfile.NamedTemporaryFile(suffix='.m4a')
		args = ["rtmpdump", "-v", "-o", d.name, "-r", s]
		debug("Dumping " + s + " to " + d.name)

		if (quick_test):
			args += ["-B", "10"]  # call instead check_call because
			subprocess.call(args) # rtmpdump returns non-zero w/ -B
		else:
			subprocess.check_call(args)
		dumps.append(d)

	return dumps

def package_audio(showname, showdate, show_imgurl, infns, outputs):

	# Package dumped raw RTMP stream into a proper m4a (aka ipod)
	# container, apply tags including cover art. infns can be a list of
	# strings (file names) or a list of NamedTemporaryFiles. outputs is
	# a dict of output ID - directory mappings.

	showfn_prefix = re.sub(r"\s+", "-", showname.lower())

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
		show_title = showname + " " + str(showdate) + show_index

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
	tags["covr"] = cover
	tags.save()

def package_mp3(infn, outfn, title, cover):
	subprocess.check_call(
		["ffmpeg", "-y", "-i", infn, "-acodec", "libmp3lame", "-q:a", "1", outfn])

	tags = mutagen.id3.ID3(outfn)
	tags.add(mutagen.id3.TIT2(encoding=3, text=title))
	tags.add(mutagen.id3.TPE1(encoding=3, text="R2"))
	tags.add(mutagen.id3.APIC(encoding=3, type=3, data=cover))
	tags.save()
	
def package_ogg(infn, outfn, title, cover):
	
	# Note: cover currently ignored for OGG Vorbis output
	
	subprocess.check_call(
		["ffmpeg", "-y", "-i", infn, "-codec:a", "libvorbis", "-qscale:a", "6", outfn])
	
	ogg = mutagen.oggvorbis.OggVorbis(outfn)
	ogg.tags["artist"] = u"R2"
	ogg.tags["title"] = title
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
		help="quick sanity test of the pipeline, download 10 first seconds only"
	)
	parser.add_argument(
		"-p", "--partial-name",
		action="store_true",
		help="allow partial match for show name"
	)
	parser.add_argument(
		"-v", "--verbose",
		action="count",
		help="increase verbosity"
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
	parser.add_argument("showname")
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

def debug(msg, verbosity=0):
	if (verbosity > VERBOSITY):
		return	
	sys.stderr.write(msg)
	sys.stderr.write("\n")

def warn(msg, is_error=0):
	if (is_error):
		msg = "ERROR: " + msg
	else:
		msg = "WARNING: " + msg
	debug(msg)

def err(msg):
	warn(msg, is_error=1)
	sys.exit(1)

def list_uniq(l):
	s = set()
	r = []
	
	for i in (l):
		if (i not in s):
			r.append(i)
			s.add(i)
	
	return r

def main():	
	args = parse_command_line()
	showname = args.showname.strip()
	streams = None
	infns = None
	outputs = None
	
	global VERBOSITY
	VERBOSITY = args.verbose or 0
	
	outputs = gather_outputs(args)
	
	if (args.skip):
		infns = [args.skip]
	if (args.date):
		showdate = parse_date(args.date)
	else:
		showdate = get_last_showdate(showname)

	(showname, sid, show_imgurl) = \
		get_show_attrs(showname, showdate, args.partial_name)
	debug("Show name:\t" + showname)
	debug("Show date:\t" + str(showdate))
	debug("Show ID:\t" + sid)
	debug("Image URL:\t" + show_imgurl)

	if (not infns):
		streams = get_show_streams(showname, sid)
		debug("Stream URLs:\t" + str(streams))
		infns = download_audio(streams, args.quick_test)
	package_audio(showname, showdate, show_imgurl, infns, outputs)

main()

