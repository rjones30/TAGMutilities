#!/bin/bash

nskip=0
nevents=999999999
nthreads=1
batch=0
loglevel=INFO
plugin=PStagstudy

echo Running on `hostname`

#source /opt/rh/devtoolset-11/enable
#source setup_centos7.sh
#echo $LD_LIBRARY_PATH
#ldd `which hd_root`

#xrootdpath=root://nod25.phys.uconn.edu/gluex/uconn0
xrootdhost=cn445.storrs.hpc.uconn.edu
xrootdfs=/gluex/uconn1
xrootdpath=root://$xrootdhost$xrootdfs
#rawdata=/rawdata/TAGM_calib
rawdata=/rawdata/spring_2025
#rawdata=/calibration/TAGM_dark
#rawdata=/rawdata/calibration/TAGM_light

if [[ $# > 0 ]]; then
    line=`expr $1 + 1`
    run=`awk -F_ '{if(NR=='$line'){print $1}}' TAGMtrees_runs.list`
    fileno=`awk -F_ '{if(NR=='$line'){print $2}}' TAGMtrees_runs.list`
    if [ -z "$run" ]; then
        echo "nothing to do, quitting"
        exit 1
    fi
    indir="$xrootdpath$rawdata"
    infiles=""
    for infile in $(/usr/bin/xrdfs $xrootdhost ls $xrootdfs/$rawdata/Run$run | grep "${run}_${fileno}\.evio$"); do
        #infiles="$infiles root://$xrootdhost/$infile"
	infiles="$infiles $(basename $infile)"
    done
else
    echo "usage: TAGMtrees.bash <sequence number>"
    exit 1
fi

# old-style jana commandline arguments
#echo $HALLD_RECON_HOME/$BMS_OSNAME/bin/hd_root \
#  -PPRINT_PLUGIN_PATHS=1 \
#  -PJANA:BATCH_MODE=$batch \
#  -PPLUGINS=$plugin \
#  -PEVIO:SYSTEMS_TO_PARSE=TAGM \
#  -PEVIO:SYSTEMS_TO_PARSE_FORCE=1 \
#  -PEVIO:RUN_NUMBER=$run \
#  -PEVIO:PARSE_HELICITY=0 \
#  -PEVENTS_TO_SKIP=$nskip \
#  -PEVENTS_TO_KEEP=$nevents \
#  -PTHREAD_TIMEOUT_FIRST_EVENT=300 \
#  -PTHREAD_TIMEOUT=300 \
#  -PNTHREADS=$nthreads \
#  --nthreads=$nthreads \
#  $infiles

# new-style jana commandline arguments
echo $HALLD_RECON_HOME/$BMS_OSNAME/bin/hd_root \
  -Pjana:parameter_verbosity=1 \
  -Pjana:global_loglevel=$loglevel \
  -Pplugins=$plugin \
  -Pevio:RUN_NUMBER=$run \
  -Pjana:nskip=$nskip \
  -Pjana:nevents=$nevents \
  -Pjana:warmup_timeout=300 \
  -Pjana:timeout=300 \
  -Pnthreads=$nthreads \
  $infiles
#gdb $HALLD_RECON_HOME/$BMS_OSNAME/bin/hd_root
#exit
$HALLD_RECON_HOME/$BMS_OSNAME/bin/hd_root \
  -Pjana:parameter_verbosity=1 \
  -Pjana:global_loglevel=$loglevel \
  -Pplugins=$plugin \
  -PEVIO:RUN_NUMBER=$run \
  -Pjana:nskip=$nskip \
  -Pjana:nevents=$nevents \
  -Pjana:warmup_timeout=300 \
  -Pjana:timeout=300 \
  -Pnthreads=$nthreads \
  $infiles
retcode=$?

if [[ $retcode = 0 ]]; then
    mv hd_root.root ${plugin}_${run}_${fileno}.root
else
    echo "hd_root failed with exit code $retcode"
    exit $retcode
fi

exit $retcode
