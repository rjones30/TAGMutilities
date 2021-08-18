#!/bin/bash
#
# do_sequence.sh - script to cycle through the the rows in a fiber bundle
#	           and set the bias voltages on by row or by individual sipm,
#	           ending with all bias voltages reset to zero.
#
# author: richard.t.jones at uconn.edu
# version: november 21, 2015
#
# Usage: do ./do_sequence.sh -h
#
# Notes: 
#  1. This script was built to run on the darkbox setup at UConn.
#     Do NOT ATTEMPT to use it with the full TAGM detector readout
#     at Jefferson Lab. For that, maybe you are looking for seq.sh?

# Select a sequence by commenting out all but the desired scheme below.
#scheme=rowbyrow

opts=-L
delay=20
gain_pC=0.45
V0=50
netdev=gluon2.phys.uconn.edu:

while [[ $# -gt 0 ]]; do
	if `echo $1 | grep -q -- -d`; then
	delay=`echo $1 | awk '/-d/{print substr($1,3)}'`
		shift
		if [[ $delay = "" ]]; then
		delay=$1
		shift
		fi
	elif `echo $1 | grep -q -- -g`; then
	gain_pC=`echo $1 | awk '/-g/{print substr($1,3)}'`
		shift
		if [[ $gain_pC = "" ]]; then
		gain_pC=$1
		shift
		fi
	elif `echo $1 | grep -q -- -r`; then
	byrow=1
		shift
	elif `echo $1 | grep -q -- -H`; then
	opts=-H
		shift
	elif `echo $1 | grep -q -- -L`; then
	opts=-L
		shift
	else
	echo "Usage: do_sequence [-r] [-H | -L] [-d <delay_sec>] [-g <gain_pC>]"
	exit 0
	fi
done

tracefile=/tmp/ether_trace.log
cat /dev/null >$tracefile

cd ~halld/online/TAGMutilities
$bin/setVbias $opts -c 1-6 -r 1-5 -V $V0 $netdev >/dev/null

if [[ $byrow != "" ]]; then
	for row in 1 2 3 4 5; do
		echo "lighting up row $row"
		$bin/setVbias $opts -c 1-6 -r $row -g $gain_pC $netdev >> $tracefile
		ssh halld@halldtrg5 mqwrite /Vbias 0x0$row
		sleep $delay
		ssh halld@halldtrg5 mqwrite /Vbias 0xff
		$bin/setVbias $opts -c 1-6 -r 1-5 -V $V0 $netdev >/dev/null
	done
else
	for col in 1 2 3; do
		for row in 1 2 3 4 5; do
			chan=`echo $row $col | awk '{printf("%2.2x", 1+($1-1)+($2-1)*5)}'`
			cols=`echo $col | awk '{printf("%d,%d", $1, $1+3)}'`
			echo "selecting channel $chan"
			$bin/setVbias $opts -c $cols -r $row -g $gain_pC $netdev >>$tracefile
			ssh halld@halldtrg5 mqwrite /Vbias 0x01$chan
			sleep $delay
			ssh halld@halldtrg5 mqwrite /Vbias 0xff 
			$bin/setVbias $opts -c 1-6 -r 1-5 -V $V0 $netdev >/dev/null
		done
	done
fi

echo "Trace of query packets during above sequences was:"
cat $tracefile
echo "End of query packets"
rm -f $tracefile
