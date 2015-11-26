
This repo contains a few sundry scripts potentially useful to the general
GNU/Linux-using public. The scripts are categorized into directories as follows:

* `arch` - [Arch Linux](http://archlinux.org)-specific scripts
* `eesti` - scripts specific to Estonian services
* `perl` - [Perl](https://www.perl.org/)-specific scripts
* `X` - scripts useful within a graphical user environment (X11)

The root directory contains miscellaneous other scripts, `lib` currently only
contains backends for `backup`, `data` contains configuration files. The scripts
expect a full-featured modern Linux system as their environment; standard
requirements like `perl`, `awk`, `wget` etc. are not listed for each script.
Many scripts can be run with no arguments, `-h` or `--help` for usage info. I'm
guilty of the mortal sin of using tabs (4) instad of spaces, so beware.

## backup

A multi-purpose script for backing up a directory tree into a tarball or via
[duplicity](http://duplicity.nongnu.org/). The script sources `.backup.conf`
from the current working directory for options. See `.backup.conf.example` for a
template and explanations of options. The tar backend supports

* numbered backups (000, 001, ...)
* rotating a fixed maximum number of backups through `logrotate`
* e-mailing the tarball through `mutt`
* keeping a log file for backups in README

Requires:

* GNU `tar` (for the tar backed)
* `duplicity` (for the duplicity backend)
* `logrotate` (for rotating the backups)
* `mutt` (for e-mailing the backups)

See `backup`, `lib/backup*` and `.backup.conf.example` for details.

## mp3tag

```
mp3tag {-t | -f} filename [filename ...]
```

Copy mp3 tags to the filename as `ARTIST - TITLE.mp3` (`-f`) or write the artist
and title tags to the mp3 file (`-t`) based on the filename formatted as such. Requires
[eyeD3](http://eyed3.nicfit.net/).

## reflow

A Perl script accepting a block of comments (lines starting with `#` or `//`)
on its standard input and piping a nicely formatted result to its standard
output.  Use as an editor extension (Geany, vim, ...). Requires
[Text::Autoformat](http://search.cpan.org/~neilb/Text-Autoformat-1.73/lib/Text/Autoformat.pm)
and pipes the cleaned input through its main routine.  As an extended feature,
supports formatting argument list documentation, i.e.

```
	// Add a tool to the toolbar. Attributes:
	//
	// id - identifier string, required
	// toggle - a boolean specifying whether the tool is a toggle button
	// handlers - an object of [jQuery] event handlers, keyed by event. The handler will 
	// receive the tool spec object as event.data.
```

will be formatted as

```
	// Add a tool to the toolbar. Attributes:
	// 
	// id       - identifier string, required
	// toggle   - a boolean specifying whether the tool is a toggle button
	// handlers - an object of [jQuery] event handlers, keyed by event. The 
	//            handler will receive the tool spec object as event.data.
```

## vid2x264

```
Convert a video stream into high quality x264; by default 720p, CRF 20, 
preset: slow.
```

Convenience frontend to `ffmpeg`. Convert input to x264 video, based on a
hardcoded profile. Available profiles are currently `720high` and `480med`.

Usage example:

`vid2x264 -i input.mp4 -p 720high output.mkv`

## arch/ckfpkgs

```
Check whether foreign packages have become available in binary 
repositories
```

## arch/nongrppkgs

```
List explicitly-installed packages that are not part of a group
```

## arch/pkgdate

```
Output packages sorted by install date, one per line with the install 
date prepended to the package name. All command line arguments are 
passed on to pacman.
```

## arch/rqfpkgs

```
List foreign packages (e.g. from AUR) that are required by other 
packages
```

## eesti/bank

```
A script to analyze a Swedbank CSV bank statement and group 
expenditures by function, based on the groups defined in 
`statementgroups`. Pass the statement and statement groups filenames as 
the arguments.
```

What it says on the tin. Pass a CSV account statement from Swedbank and a
statement groups file (see `data/statementgroups.example`, first column is the
group, second column is a pattern (full Perl regexp, really) to match against
the transaction comment or recipient). The output is a neat table of grouped
expenditures and incomes. Requires
[Text::ASCIITable](http://search.cpan.org/~lunatic/Text-ASCIITable-0.20/lib/Text/ASCIITable.pm)
and [Text::CSV](http://search.cpan.org/~makamaka/Text-CSV-1.33/lib/Text/CSV.pm).

## eesti/iptv

A script for watching or capturing Elion's multicast-based IPTV. Reads
`data/iptvrc` for channel definitions. If the passed network interface seems to
have the IPTV subnet address, attempts to open the multicast stream. To ensure
that it doesn't cut out, blasts IGMP join messages (using `nemesis`) until VLC
is running. This should not be necessary, but it was easier to do than debug all
possible software / hardware / router firmware issues that might have resulted
in bad multicast group behavior - simply opening the mcast URL with VLC did not
result in IGMP join messages reaching the ISP and the stream froze after ~3
minutes.

Requires:

* [nemesis](http://nemesis.sourceforge.net/)
* [VLC](http://www.videolan.org/vlc/index.html)
* [mplayer](http://www.mplayerhq.hu/design7/news.html) (for capturing)

`iptvrc` format:

* 1st column - channel ID
* 2nd column - mcast stream URL
* 3rd column - fallback (web) stream URL

Usage:

```
iptv [-c output.mp4] [-a] [-i interface]
```

* `-i interface` - network interface to use
* `-c filename` - dump stream to `filename` instead of opening in VLC
* `-a` - use alternative (fallback) stream

__Note:__ If you do decide to try out this script, keep in mind that it requires
advanced knowledge of network configuration to set up. Broadly, you need to a)
spoof a set-top box's MAC address to the desired network interface, b) set up
the multicast route (`route add -net 224.0.0.0 netmask 240.0.0.0 dev
interface_name`) c) force your system to use IGMPv2 d) add an `iptables` rule to
accept multicast packets, if using the firewall. Please do not contact me about
troubleshooting your network configuration.

## eesti/r2get.py

A script for downloading shows from [Raadio 2](http://r2.err.ee/). See `r2get.py
-h` for more or less comprehensive usage instructions, and the file header for
technical details.

Requirements:

* Python >=2.7, with
  * [mutagen](https://mutagen.readthedocs.org/en/latest/)
  * [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/)
* [ffmpeg](https://www.ffmpeg.org/)
* [rtmpdump](https://rtmpdump.mplayerhq.hu/)

## eesti/weather

```
Without arguments, print the current temperature from 
meteo.physic.ut.ee If -R is given, print the record temperature days 
this year. If -r is given, reverse the order (i.e. display the coldest 
dates). If -i is given, invert minima and maxima (i.e. show warmest 
daily minima with -R, coldest daily maxima with -Rr). -n determines the 
number of dates to output. -y determines year, current year by default.
```

## perl/plckmods

```
Utility for finding all Perl files under the current directory and 
listing dependency modules. $* is passed to scandeps.pl. Pass -n to 
list unavailable dependencies, in such case $* is ignored.
```

Requires
[scandeps.pl](http://search.cpan.org/~autrijus/Module-ScanDeps-0.54/script/scandeps.pl)

## perl/plinstall

```
Install Perl modules to a specific directory. Pass the prefix as the 
first argument and any modules to install as subsequent arguments.
```

## perl/plmodavail

```
Check availability of a Perl module
```

## perl/plstordmp

```
Dump the contents of a Storable serialized in a file, file name passed 
as the command line argument
```

## X/ckfs

```
Check if there are full-screen windows with title matching a pattern, 
in which case disable power management. Useful for running as a 
frequent cron job or from a periodic script.
```

## X/pidginctl

```
Command-line control of Pidgin via D-Bus. Currently toggles available / 
offline mode.
```

## X/remoted.pl

A remote control daemon leveraging the power of [LIRC](http://www.lirc.org/) to
turn your Android device into a remote for your machine using a client such as
[this
one](https://play.google.com/store/apps/details?id=com.chham.lirc_client&hl=en).

Usage:

* Set up LIRC on your machine. You may use the [generic remote
  definition](https://bpaste.net/raw/e1c14b4acbfc), either way, `remoted.pl`
  expects `devinput` as the remote's ID.
* Set up the
  [client](https://play.google.com/store/apps/details?id=com.chham.lirc_client&hl=en)
  on your android device, download the `devinput` definition from your LIRC
  server and configure your remote. Note: make sure to use SIMULATE mode.
* Create an action mapping file, see `data/remotedrc` as an example. This either
  maps actions to a command to run (two fields) *or* invokes an internal
  function (three or more fields). In the latter form, the second field is the
  name of the function in angle brackets and the rest are its arguments. Two
  functions are available:

  * `<mpris>` - Control VLC via [D-Bus /
	MPRIS](http://specifications.freedesktop.org/mpris-spec/latest/). See the
	[specification](http://specifications.freedesktop.org/mpris-spec/latest/Player_Interface.html)
	for details; methods for most expected actions (play, stop, seek, etc.) are available.
  * `<vlc_start>` - Start VLC and open the passed URI (3rd field). If VLC is
	already running, no new instance is spawned.
* Run `remoted.pl`, passing the action mapping file as a parameter. You should
  be able to control VLC and invoke any other actions via your Android device
  now.


## X/spotifyctl

```
Command-line control of Spotify. Pass "play", "pause", "next", "prev" 
or "previous" as the argument.
```

## X/windowdim

```
Resize a window (partially) matching the title.
```

