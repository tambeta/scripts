
This repo contains a few sundry scripts potentially useful to the general
GNU/Linux-using public. The scripts are categorized into directories as follows:

* `arch` - [Arch Linux](http://archlinux.org)-specific scripts
* `eesti` - scripts specific to Estonian services
* `perl` - [Perl](https://www.perl.org/)-specific scripts
* `X` - scripts useful within a graphical user environment (X11)

The root directory contains miscellaneous other scripts, `lib` currently only
contains backends for `backup`, `data` contains configuration files.

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
Copy filename in the form of "artist - title.mp3" to mp3 tags, or vice 
versa. mp3tag {-t | -f} filename [filename ...]
```

Copy mp3 tags to the filename as `ARTIST - TITLE.mp3` (`-f`) or write the artist
and title tags to the mp3 file based on the filename formatted as such.

## reflow

```
Script to reflow a block of comments wrapped to a given length. 
Intended to be used as an editor extension. The TABW constant is the 
allowed width of the pure block, i.e. only text starting from the first 
non-space character after the hash (`#`) on a line.
```




## vid2x264

```
Convert a video stream into high quality x264; by default 720p, CRF 20, 
preset: slow.
```

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

## eesti/iptv

```
IPTV frontend. Takes the channel ID as argument. Blasts IGMP join 
messages to the channel mcast IP to ensure that the stream doesn't cut 
out. If the proper interface is not connected, falls back to web stream.
```

## eesti/weather

```
Without arguments, print the current temperature from 
meteo.physic.ut.ee If -R is given, print the record temperature days 
this year If -r is given, reverse the order (i.e. display the coldest 
dates) If -i is given, invert minima and maxima (i.e. show warmest 
daily minima with -R, coldest daily maxima with -Rr) -n determines the 
number of dates to output -y determines year, current year by default
```

## perl/plckmods

```
Utility for finding all Perl files under the current directory and 
listing dependency modules. $* is passed to scandeps.pl. Pass -n to 
list unavailable dependencies, in such case $* is ignored.
```

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

## X/spotifyctl

```
Command-line control of Spotify. Pass "play", "pause", "next", "prev" 
or "previous" as the argument.
```

## X/windowdim

```
Resize a window (partially) matching the title.
```

