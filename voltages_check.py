#!/usr/bin/env python
#
# voltages_check.py - script to read the output from a dry run of setVbias
#                     (replacing argument gluon28.jlab.org :5692 with dummy) 
#                     and output the set voltages in a format similar to the
#                     voltages.py script.
#
# author: richard.t.jones at uconn.edu
# version: january 27, 2020
# usage:
#          $ python voltages_check.py <setVbias.log>

import re
import sys
import fileinput

Vdemand = {}

def usage():
   print "Usage: python voltages_check.py <setVbias.log>"
   sys.exit(1)

def read_log():
   for line in fileinput.input():
      s = re.match(r"^setting channel ([0-9a-e][0-9a-e]):([0-9]+)\[.*\] to ([.0-9]+)V", line)
      if not s:
         s = re.match(r"^overwriting channel ([0-9a-e][0-9a-e]):([0-9]+)\[.*\] to ([.0-9]+)V", line)
      if s:
         board = int(s.group(1), 16)
         channel = int(s.group(2))
         voltage = float(s.group(3))
         if board in Vdemand:
            row = Vdemand[board]
            if "overwriting" in line:
               print "value", row[channel], "overwritten with", voltage
         else:
            row = [0 for channel in range(32)]
            Vdemand[board] = row
         row[channel] = voltage

read_log()
for board in Vdemand:
   print " ", hex(board), " ",
   for i in range(30):
      if i > 0 and (i % 5) == 0:
         print "\n", "        ",
      if i < 29:
         sys.stdout.write("{0:9.3f}".format(Vdemand[board][i]))
      else:
         print "{0:9.3f}".format(Vdemand[board][i])
