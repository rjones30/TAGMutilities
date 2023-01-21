#!/bin/bash
if [ $# = 0 ]; then
    echo "Usage: PStags.bash [-o <offset>] <n1> [<n2> [...]]"
    echo "   where <nN> is 0..99999 the number of the line in PStags_runs.list"
    echo "   containing the name of the evio input file to process, offset"
    echo "   by <offset> if given."
    exit 1
fi

nskip=0
nevents=100000000
nthreads=4
batch=0
archive="/Gluex/beamline/PStags-1-2023"
ftpserver="nod28.phys.uconn.edu"

echo Running on `hostname`

source setup.sh
echo $LD_LIBRARY_PATH
ldd `which hd_root`

xrootdpath=root://nod25.phys.uconn.edu/gluex/uconn0
rawdata=/rawdata/TAGM_calib



if [[ $# > 0 ]]; then
    line=`expr $1 + 1`
    run=`head -n $line PStags_runs.list | tail -n 1`
    indir=$(echo $run | awk '{printf("'$xrootdpath$rawdata'/Run%06d", $1)}')
    infiles=""
    for infile in $(ls $indir | grep "\.evio$"); do
        infiles="$infiles $indir/$infile"
    done
else
    echo "usage: run_hdroot.sh <sequence number>"
    exit 1
fi


$HALLD_HOME/$BMS_OSNAME/bin/hd_root \
  -PPRINT_PLUGIN_PATHS=1 \
  -PJANA:BATCH_MODE=$batch \
  -PPLUGINS=PStagstudy \
  -PTAGMHit:CUT_FACTOR=0 \
  -PEVIO:PARSE_SSP=0 \
  -PEVENTS_TO_KEEP=$nevents \
  -PTHREAD_TIMEOUT_FIRST_EVENT=300 \
  -PAUTOACTIVATE=DTAGMHit:Calib \
  -PTHREAD_TIMEOUT=300 \
  -PNTHREADS=4 \
  --nthreads=4 \
  $infiles
retcode=$?

if [[ $retcode = 0 ]]; then
    outfile="PStagstudy2_${run}.root"
    mv hd_root.root $outfile
    while true; do
        uberftp $ftpserver "cd $archive; put $outfile" && break
        sleep 300
    done
    rm $outfile
else
    echo "Error processing input file $infile"
    echo "Cannot continue."
    exit $retcode
fi
