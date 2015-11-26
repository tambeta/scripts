## backup

```
See the example .backup.conf for configuration options and details.
```

## mp3tag

```
Copy filename in the form of "artist - title.mp3" to mp3 tags, or vice 
versa. mp3tag {-t | -f} filename [filename ...]
```

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

