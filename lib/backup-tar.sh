
# tar backup module for ../backup

# Give default values for unset parameters

[ -n "$BACKUPDIR" ]   || BACKUPDIR="backup"
[ -n "$PROJECTNAME" ] || PROJECTNAME=$(echo $WORKDIR | perl -ple 's|^.*/(.*)$|\1|g')
[ -n "$BACKUPFILE" ]  || BACKUPFILE="$PROJECTNAME.tar.gz"
[ -n "$BACKUPID" ]    || BACKUPID=BACKUP_$(echo $PROJECTNAME | tr a-z A-Z)
[ -n "$ROTATE" ]      && NOEDIT=1

# Check if backupdir exists, create if necessary

cd $WORKDIR
[ -d "$BACKUPDIR" ] ||\
	mkdir $BACKUPDIR 2>/dev/null
[ -d "$BACKUPDIR" ] || {
	echo "Cannot create directory $BACKUPDIR";
	exit 2;
}

# Get number for this backup

FULLPATH=$BACKUPDIR/$BACKUPFILE
N=$(ls -1 $FULLPATH.* 2>/dev/null | sort | tail -n-1 | rev | cut -d '.' -f1 | rev)
N=$(expr $N + 1)

# Parse exclude patterns to tar options

EXCLUDE="$EXCLUDE $BACKUPDIR"
EXCLUDE=$(incl_excl "$EXCLUDE")

# Create archive

rm -f $FULLPATH
TARCMD=$(echo tar -cvvvf - $EXCLUDE $TAROPTS $FILES)
$TARCMD | gzip > $FULLPATH

if [ -n "$ROTATE" ]; then
	TMPFN="/tmp/logrotate.conf.$RANDOM" # logrotate won't allow /dev/fd/x
	STFN="/tmp/logrotate.state.$RANDOM" # logrotate whines on /dev/null

	echo -e "\"$FULLPATH\" {\nrotate $ROTATE\n}" > $TMPFN
	logrotate -vfs $STFN $TMPFN
	rm $TMPFN $STFN
	GENFN=$BACKUPFILE.1
else
	N=$(printf '%03d' $N)
	GENFN="$BACKUPFILE.$N"
	mv $FULLPATH $BACKUPDIR/$GENFN
fi

# Link latest backup to constant file name

[ -f $BACKUPDIR/$GENFN ] || {
	echo "Expected $GENFN, but doesn't exist" >&2
	exit 1
}
[ -f $FULLPATH ] && {
	echo "$FULLPATH exists, but not expected" >&2
	exit 1
}

CWD=$(pwd)
cd $BACKUPDIR
ln -sv $GENFN $BACKUPFILE
cd $CWD

# Edit history

[ -n "$NOEDIT" ] || {
	echo "$N - " >> $BACKUPDIR/README
	[ -z "$EDITOR" ] && EDITOR=vim
	$EDITOR $BACKUPDIR/README
}

# Mail backup

[ -n "$ROTATE" ] && N=""
[ -n "$NOEDIT" ] ||\
	COMMENT=$(egrep "$N - " $BACKUPDIR/README | head -n 1 | sed -r 's/^[0-9]{3} - //g')
[ -n "$EMAIL" ] && {
	echo -e "$BACKUPID\n\n$COMMENT" |\
	mutt -a $FULLPATH -s "[$BACKUPID] $N" -- $EMAIL
}

echo "Wrote $FULLPATH ($GENFN)"

