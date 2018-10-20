#!/bin/tcsh
source /gluex/etc/hdonline.cshrc
cd /home/hdops/TAGMutilities
python ./voltages.py -s >&! voltages.log
