#!/bin/bash

bin=bin
SETVBIAS="$bin/setVbias -H -C setVbias_fulldetector-3-12-2025_calib.conf -c 1-102"
CTRLHOST="gluon28.jlab.org:5692"

function put {
	echo $SETVBIAS -r 1-5 -V 50 $CTRLHOST
	$SETVBIAS -r 1-5 -V 50 $CTRLHOST
	echo $SETVBIAS -r $1 -g $2 $CTRLHOST
	$SETVBIAS -r $1 -g $2 $3 $4 $5 $6 $CTRLHOST
}

function fin {
	put 1-5 0.45 -l
	echo "you are back in business again"
	exit 0
}

for row in 1 2 3 4 5; do
	#for gval in 25 30 35 40 45; do
	for gval in 0 05 10 15 20; do
		put $row 0.$gval
		echo -n "ready for scan row${row}g${gval},"
		echo -n "press enter when done, q to quit: "
		read ans
		if [[ "$ans" = "q" ]]; then
			fin
		fi
	done
done
fin
