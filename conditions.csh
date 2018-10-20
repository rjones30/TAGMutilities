#!/bin/tcsh
source /gluex/etc/hdonline.cshrc
cd /home/hdops/TAGMutilities
python ./conditions.py -s >&! conditions.log
