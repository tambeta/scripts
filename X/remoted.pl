#!/usr/bin/perl

use strict;
use warnings;

use Data::Dumper;
use IO::Socket::UNIX;
use Net::DBus;

use constant {	
	SOCKET 				=> "/var/run/lirc/lircd",
	LISTEN_DEVICE		=> "devinput",
	
	ACTION_TYPE_SHELL	=> 1,
	ACTION_TYPE_CALL	=> 2,
};

$SIG{CHLD} = "IGNORE";



sub dmp {
	$Data::Dumper::Indent = 3;
	print Data::Dumper->Dump([shift]);
}

sub parse_conf_file {
	my ($conffn) = @_;
	my %eventmap;
	
	open(CONF, "<", $conffn)
		or die("Cannot open $conffn: $!");
		
	while (<CONF>) {
		next if (/^\s*#/ || /^\s*$/);
		
		my @f = 
			map { s/(^\s+|\s+$)//g; $_; } split(/\t/);
		my $event = $f[0];
		my $action = $f[1];
		my @params = @f[2 .. $#f];
		my $atype;
		
		if ($action =~ /^<.*>$/) { 
			$atype = ACTION_TYPE_CALL;
			$action =~ s/(^<|>$)//g;
		}
		else {
			$atype = ACTION_TYPE_SHELL; 
		}
			
		$eventmap{$event} = {
			action	=> $action,
			params	=> \@params,
			atype	=> $atype,
		};
	}
	
	\%eventmap;
}

sub event_loop {
	my ($cb) = @_;
	
	my $sock = IO::Socket::UNIX->new(
		Peer => SOCKET,
		Type => SOCK_STREAM,
	);
	
	die("No callback passed")
		unless($cb && ref($cb) eq "CODE");
	die("Cannot connect to socket " . SOCKET . ": $!")
		unless($sock);
	
	while (<$sock>) {
		my @f = split(" ");
		my $evt = $f[2];
		my $dev = $f[3];
		
		next unless ($dev eq LISTEN_DEVICE);
		$cb->($evt);
	}
}

sub get_vlc_dbus_service {
	
	# Get the VLC DBus service. If the force_start attribute is set, no VLC
	# instance is assumed to be available if the named bus / service isn't
	# available. A VLC instance will then be started.
	#
	# Throws Net::DBus::Error.
	
	my ($attrs) = @_;
	
	my $dbus;
	my $svc;	

	$attrs ||= {};
	$dbus = Net::DBus->session();

	eval {
		$svc = $dbus->get_service("org.mpris.MediaPlayer2.vlc");
		get_vlc_dbus_object($svc)->Seek(0); # test bus; Net::DBus caches services
	};
	if ($@ && ref($@) eq "Net::DBus::Error" && $attrs->{force_start}) {
		if (fork() == 0) { 
			exec("vlc"); 
			exit;
		}
		
		sleep 1;
		return get_vlc_dbus_service();
	}
	elsif ($@) {
		die($@);
	}
	
	$svc;
}

sub get_vlc_dbus_object {
	
	# Get the remote DBus object exposing the MPRIS interface for controlling
	# VLC. $service is optional, requested if not passed.
	# 
	# Throws Net::DBus::Error.
	
	my ($service) = @_;	
	my $obj;
	
	$service ||= get_vlc_dbus_service();
	$service->get_object("/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player");
}

# Actions

sub action_mpris {
	
	# Call any method on the DBus object, presumably methods defined by the
	# MPRIS interface.

	my ($method, @params) = @_;
	
	my $svc = get_vlc_dbus_service();
	my $obj = get_vlc_dbus_object($svc);			
	
	$obj->$method(@params);
}

sub action_vlc_start {
	
	# Open $url in VLC. Start VLC if no instance present.
	
	my ($url) = @_;
	
	my $svc = get_vlc_dbus_service({ force_start => 1 });
	my $obj = get_vlc_dbus_object($svc);		
	
	$obj->OpenUri($url);
}

# Entry point

sub main {
	my $eventmap;
	
	usage() && exit(1)
		unless($ARGV[0]);
	
	$eventmap = parse_conf_file($ARGV[0]);
	
	# Run event loop indefinitely
	
	event_loop(sub {
		return 
			unless (my $evt = $eventmap->{shift()});
		
		if ($evt->{atype} == ACTION_TYPE_CALL) {
			no strict 'refs';
			my $subname = "action_" . $evt->{action};
			
			# Don't die on action routine invocations
			
			eval {
				&$subname(@{$evt->{params}}); };
			if ($@) {
				warn($@); }
		}
		elsif ($evt->{atype} == ACTION_TYPE_SHELL) {
			system($evt->{action});
		}
	});
}

sub usage {
print <<END
Usage: $0 configuration_filename
END
}

main();
1;
