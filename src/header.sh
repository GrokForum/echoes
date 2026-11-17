#!/bin/sh
a=/tmp/e$$;sed 1,2d "$0"|lzcat>$a;chmod +x $a;s=`stty -g`;case $* in *s*)$a "$@"|(aplay -qr32000 -B60000||pacat --format=u8 --rate=32000 --channels=1 --latency-msec=60)2>&-;;*)$a "$@";;esac;stty $s;rm $a;exit
