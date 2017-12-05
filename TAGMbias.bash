#!/bin/bash

echo Running on `hostname`

source setup.sh
echo $LD_LIBRARY_PATH
ldd `which hd_root`

pnfspath=/pnfs4/phys.uconn.edu/data
rawdata=/Gluex/calibration/TAGM/rawdata

if [[ $# > 0 ]]; then
    line=`expr $1 + 1`
    run=`head -n $line runs.list | tail -n 1`
    export infile=`ls $pnfspath/$rawdata/Run0$run/*.evio`
else
    echo "usage: run_hdroot.sh <sequence number>"
    exit 1
fi
if [[ ! -r $infile ]]; then
    echo "Error - unable to open input file $infile"
    exit 1
fi

echo $HALLD_HOME/$BMS_OSNAME/bin/hd_root -PJANA:BATCH_MODE=1 -PPRINT_PLUGIN_PATHS=1 -PPLUGINS=TAGM_bias -PTHREAD_TIMEOUT_FIRST_EVENT=3000 -PTHREAD_TIMEOUT=3000 -PEVIO:RUN_NUMBER=$run $infile
$HALLD_HOME/$BMS_OSNAME/bin/hd_root \
  -PPRINT_PLUGIN_PATHS=1 \
  -PJANA:BATCH_MODE=1 \
  -PPLUGINS=TAGM_bias \
  -PEVIO:RUN_NUMBER=$run \
  -PTHREAD_TIMEOUT_FIRST_EVENT=300 \
  -PTHREAD_TIMEOUT=300 \
  $infile
#   -PEVIO:SYSTEMS_TO_PARSE=TAGM \
#  -PEVIO:VERBOSE=99 \
retcode=$?

if [[ $retcode = 0 ]]; then
    mv hd_root.root TAGMbias_${run}.root
fi
exit $retcode
