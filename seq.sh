#!/bin/bash

bin=bin
SETVBIAS="$bin/setVbias -L -C setVbias_fulldetector-4-27-2026_calib.conf -c 1-110"
CTRLHOST="gluon28.jlab.org:5692"

function put {
	echo $SETVBIAS -r 1-11 -V 50 $CTRLHOST
	$SETVBIAS -r 1-5 -V 50 $CTRLHOST
	echo $SETVBIAS -r $1 -g $2 $CTRLHOST
	$SETVBIAS -r $1 -g $2 $3 $4 $5 $6 $CTRLHOST
}

function fin {
	put 1-5 0.45 -l
	echo "you are back in business again"
	exit 0
}

for row in 1 2 3 4 5 10 11; do
   for gval in 30 40 50 60 70 80; do
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
