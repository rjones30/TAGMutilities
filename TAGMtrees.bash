#!/bin/bash

nskip=0
nevents=999999999
nthreads=1
batch=0
loglevel=INFO
plugin=TAGM_trees

echo Running on `hostname`

#source /opt/rh/devtoolset-11/enable
#source setup_centos7.sh
#echo $LD_LIBRARY_PATH
#ldd `which hd_root`
source setup_alma9.sh
export XDG_RUNTIME_DIR=`pwd`

xrootdpath=root://nod25.phys.uconn.edu
xrootdhost=nod25.phys.uconn.edu
xrootdfs=/gluex/uconn0
xrootdpath=root://$xrootdhost$xrootdfs
#rawdata=/rawdata/TAGM_calib
#rawdata=/rawdata/spring_2025
rawdata=/calibration/TAGM_dark/spring-2026
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
    for infile in $(/usr/bin/xrdfs $xrootdhost ls $xrootdfs/$rawdata | grep "hd_rawdata_${run}_${fileno}\.evio$"); do
        #infiles="$infiles root://$xrootdhost/$infile"
        xrdcp --force root://$xrootdhost/$infile $(basename $infile) && infiles="$infiles $(basename $infile)"
    done
else
    echo "usage: TAGMtrees.bash <sequence number>"
    exit 1
fi
echo infiles is $infiles

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
#run=$(expr $run + 130000)
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
/bin/rm $infiles

if [[ $retcode = 0 ]]; then
    mv hd_root.root ${plugin}_${run}_${fileno}.root
else
    echo "hd_root failed with exit code $retcode"
    exit $retcode
fi

#htgettoken

exit $retcode
