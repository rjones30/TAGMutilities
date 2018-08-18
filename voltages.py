#!/usr/bin/env python
#
# voltages.py - script to read the frontend electronics bias voltages
#               for all of the SiPM readout boards and report
#               the results in tabular form.
#
# author: richard.t.jones at uconn.edu
# version: august 17, 2018

import os
import re
import sys
import subprocess

frendaddress = "gluon28.jlab.org:5692::"
readVbias = os.environ["HOME"] + "/TAGMutilities/bin/readVbias"

Vbias = {}
for gid in range(0x8e, 0x9f):
   Vbias[gid] = [0 for i in range(0, 30)]
   proc = subprocess.Popen([readVbias, hex(gid) + "@" + frendaddress], stdout=subprocess.PIPE)
   resp = proc.communicate()[0]
   for line in resp.split("\n"):
      m0 = re.match(r" *([0-9]+): *([0-9.]+)" * 5, line)
      if m0:
         for i in range(1,11,2):
           try:
            Vbias[gid][int(m0.group(i))] = float(m0.group(i+1))
           except:
            print "bad index", i, m0.group(i)
            sys.exit(1)

def print_table1():
   for gid in range(0x8e, 0x9f):
      for col in range(0,6):
         if col == 0:
            print "  {0}  ".format(hex(gid)),
         else:
            print "        ",
         for row in range(0,5):
            print "  {0:6.3f}".format(Vbias[gid][col * 5 + row]),
         print

print_table1()
