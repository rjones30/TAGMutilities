#!/bin/bash

nskip=0
nevents=9999999
nthreads=4
batch=0

echo Running on `hostname`

source setup.sh
echo $LD_LIBRARY_PATH
ldd `which hd_root`

xrootdpath=root://nod25.phys.uconn.edu/gluex/uconn0
#rawdata=/rawdata/TAGM_calib
rawdata=/rawdata/winter_2023

if [[ $# > 0 ]]; then
    line=`expr $1 + 1`
    run=`head -n $line TAGMtraw_runs.list | tail -n 1`
    indir=$(echo $run | awk '{printf("'$xrootdpath$rawdata'/Run%06d", $1)}')
    infiles=""
    for infile in $(ls $indir | grep "\.evio$"); do
        infiles="$infiles $indir/$infile"
    done
else
    echo "usage: run_hdroot.sh <sequence number>"
    exit 1
fi

echo $HALLD_HOME/$BMS_OSNAME/bin/hd_root -PJANA:BATCH_MODE=1 -PPRINT_PLUGIN_PATHS=1 -PPLUGINS=TAGM_traw -PTHREAD_TIMEOUT_FIRST_EVENT=3000 -PTHREAD_TIMEOUT=3000 -PEVIO:RUN_NUMBER=$run $infiles
$HALLD_HOME/$BMS_OSNAME/bin/hd_root \
  -PPRINT_PLUGIN_PATHS=1 \
  -PJANA:BATCH_MODE=$batch \
  -PPLUGINS=TAGM_traw \
  -PEVIO:SYSTEMS_TO_PARSE=TAGM \
  -PEVIO:SYSTEMS_TO_PARSE_FORCE=1 \
  -PEVIO:RUN_NUMBER=$run \
  -PEVENTS_TO_SKIP=$nskip \
  -PEVENTS_TO_KEEP=$nevents \
  -PTHREAD_TIMEOUT_FIRST_EVENT=300 \
  -PTHREAD_TIMEOUT=300 \
  -PNTHREADS=4 \
  --nthreads=4 \
  $infiles
retcode=$?

if [[ $retcode = 0 ]]; then
    mv hd_root.root TAGMtraw_${run}.root
fi
exit $retcode
