#!/bin/bash
#
# do_sequence.sh - script to cycle through the the rows in a fiber bundle
#                  and set the bias voltages on by row or by individual sipm,
#                  ending with all bias voltages reset to zero.
#
# author: richard.t.jones at uconn.edu
# version: november 21, 2015

# Select a sequence by commenting out all but the desired scheme below.
#scheme=rowbyrow

opts=-L
delay=20
gain_pC=0.5

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
	echo "Usage: do_sequence [-r] [-d <delay_sec>] [-g <gain_pC>]"
	exit 0
    fi
done

tracefile=/tmp/ether_trace.log
cat /dev/null >$tracefile

cd ~halld/online/TAGMutilities
bin/setVbias $opts -c 1-102 -r 1-5 $row -V 0 >/dev/null

if [[ $byrow != "" ]]; then
    for row in 1 2 3 4 5; do
	echo "lighting up row $row"
	bin/setVbias $opts -c 1-102 -r $row -g $gain_pC >> $tracefile
	ssh halld@halldtrg5 mqwrite /Vbias 0x0$row
	sleep $delay
	ssh halld@halldtrg5 mqwrite /Vbias 0xff
	bin/setVbias $opts -c 1-102 -r 1-5 $row -V 0 >/dev/null
    done
else
    for col in 1 2 3 4 5 6; do
	for row in 1 2 3 4 5; do
	    sipm=`echo $row $col | awk '{printf("%2.2x", 1+($1-1)+($2-1)*5)}'`
	    echo "selecting sipm $sipm"
	    bin/setVbias $opts -c $col -r $row -g $gain_pC >> $tracefile
	    ssh halld@halldtrg5 mqwrite /Vbias 0x01$sipm
	    sleep $delay
	    ssh halld@halldtrg5 mqwrite /Vbias 0xff 
	    bin/setVbias $opts -c 1-102 -r 1-5 $row -V 0 >/dev/null
	done
    done
fi

echo "Trace of query packets during above sequences was:"
cat $tracefile
echo "End of query packets"
cat /dev/null >$tracefile
