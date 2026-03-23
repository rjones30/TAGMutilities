#!/bin/bash
if [ $# = 0 ]; then
    echo "Usage: PStags.bash [-o <offset>] <n1> [<n2> [...]]"
    echo "   where <nN> is 0..99999 the number of the line in PStags_files.list"
    echo "   containing the name of the evio input file to process, offset"
    echo "   by <offset> if given."
    exit 1
fi

nskip=0
nevents=1000000000
nthreads=4
batch=0

echo Running on `hostname`

source setup.sh
export JANA_CALIB_CONTEXT="variation=default"
echo $LD_LIBRARY_PATH
ldd `which hd_root`

#inputURL="root://nod25.phys.uconn.edu"
inputURL="root://cn445.storrs.hpc.uconn.edu"
outputURL="root://stat25.phys.uconn.edu"
remotepath="/Gluex/beamline/PStags-1-2023"

vtoken="$(pwd)/vt_u7896"
credkey="$(cat credkey-jlab-gluex)"
htgettoken="htgettoken"
export XDG_RUNTIME_DIR=$(pwd)

function clean_exit() {
    ls -l 
    if [ "$1" = "" -o "$1" = "0" ]; then
        echo "Successful exit from PStags.bash"
        exit 0
    else
        echo "Error $1 in PStags.bash, $2"
        echo "Failed exit from PStags.bash"
        exit $1
    fi
}

function fetch_input() {
    cp $cvmfspath/$1 $2 || \
    $wget -O $2 $inputURL/$1
    return $?
}

function save_output() {
    maxretry=5
    retry=0
    while [[ $retry -le $maxretry ]]; do
        echo $htgettoken --credkey=$credkey --vaulttokeninfile=$vtoken -a htvault.jlab.org -i jlab -r gluex || clean_exit $? "error fetching bearer token from htvault.jlab.org"
        $htgettoken --credkey=$credkey --vaulttokeninfile=$vtoken -a htvault.jlab.org -i jlab -r gluex || clean_exit $? "error fetching bearer token from htvault.jlab.org"
        echo "alma9-container xrdcp -f $1 $outputURL/$remotepath/$2 2>xrdcp.err"
        alma9-container xrdcp -f $1 $outputURL/$remotepath/$2 2>xrdcp.err
        retcode=$?
        if [[ $retcode != 0 ]]; then
            cat xrdcp.err
        fi
        rm xrdcp.err
        if [[ $retcode = 0 ]]; then
            rm $1
            break
        elif [[ $retry -lt $maxretry ]]; then
            retry=$(expr $retry + 1)
            echo "xrdcp returned error code $retcode, waiting $retry minutes before retrying"
            sleep $(expr $retry \* 60)
        else
            retry=$(expr $retry + 1)
            echo "xrdcp returned error code $retcode, giving up"
        fi
    done
    # fall through to allow job file transfer return results, failure not fatal
    if [[ "$1" != "$2" ]]; then
        mv $1 $(basename $2)
    fi
    return 0
}

if [[ "$1" = "-o" ]]; then
	offset=$2
	shift
	shift
else
	offset=0
fi

if [[ $# > 0 ]]; then
    line=`expr $1 + $offset + 1`
    infile=`head -n $line PStags_files.list | tail -n 1`
    runno=`echo $infile | sed 's|.*/hd_rawdata_||' | awk -F[._] '{print $1}'`
    seqno=`echo $infile | sed 's|.*/hd_rawdata_||' | awk -F[._] '{print $2}'`
else
    echo "usage: PStags.bash [-o <offset> ] <sequence number> [<sequence number 2> ...]"
    exit 1
fi

echo run is $runno, sequence number is $seqno, infile is $infile
hd_root \
  -PPRINT_PLUGIN_PATHS=1 \
  -PJANA:BATCH_MODE=$batch \
  -PPLUGINS=PStagstudy \
  -PTAGMHit:CUT_FACTOR=0 \
  -PEVIO:PARSE_SSP=0 \
  -PEVENTS_TO_KEEP=$nevents \
  -PTHREAD_TIMEOUT_FIRST_EVENT=300 \
  -PAUTOACTIVATE=DTAGMHit:Calib \
  -PTHREAD_TIMEOUT=300 \
  -PNTHREADS=$nthreads \
  --nthreads=$nthreads \
  $inputURL/$infile || clean_exit $? "hd_root crashed during data processing"

outfile="PStagstudy2_${runno}_${seqno}.root"
mv hd_root.root $outfile
save_output $outfile $outfile || clean_exit $? "save of $outfile failed"
clean_exit
