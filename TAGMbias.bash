#!/bin/bash

echo Running on `hostname`

source setup.sh
export JANA_CALIB_CONTEXT="variation=default"
echo $LD_LIBRARY_PATH
ldd `which hd_root`

pnfspath=/pnfs4/phys.uconn.edu/data
rawdata=Gluex/calibration/TAGM/rawdata

if [[ $# > 0 ]]; then
    line=`expr $1 + 1`
    run=`head -n $line TAGMbias_run7.list | tail -n 1`
    export infile=`ls $pnfspath/$rawdata/Run0$run/*.evio`
else
    echo "usage: run_hdroot.sh <sequence number>"
    exit 1
fi

firstfile=`echo $infile | awk '{print $1}'`
if [[ ! -r $firstfile ]]; then
    echo "Error - unable to open input file $firstfile"
    exit 1
fi

echo hd_root -PJANA:BATCH_MODE=1 -PPRINT_PLUGIN_PATHS=1 -PPLUGINS=TAGM_bias -PTHREAD_TIMEOUT_FIRST_EVENT=3000 -PTHREAD_TIMEOUT=3000 $infile
hd_root \
  -PPLUGINS=TAGM_bias \
  -PTHREAD_TIMEOUT_FIRST_EVENT=300 \
  -PTHREAD_TIMEOUT=300 \
  -PPRINT_PLUGIN_PATHS=1 \
  -PEVIO:RUN_NUMBER=$run \
  $infile
retcode=$?
#  -PJANA:BATCH_MODE=1 \
#  -PEVIO:SYSTEMS_TO_PARSE=TAGM \
#  -PEVIO:VERBOSE=99 \

if [[ $retcode = 0 ]]; then
    mv hd_root.root TAGMbias_${run}.root
fi
exit $retcode
