#!/usr/bin/python
#
# makeVbiasconf.py - simple script to build a new setVbias.conf file
#                    out of inputs provided to me in a different text
#                    format by Alex Barnes.
#
# author: richard.t.jones at uconn.edu
# version: january 29, 2016
#
# usage:
#         makeVbiasconf.py <input_text_file> > <output_conf_file>
#   or
#         cat <input_text_file> | makeVbiasconf.py > <output_conf_file>
#
# input:
#  The input should be a text file in a free-form space-delimited multi-column
#  format. The order and meaning of the columns is as follows.
#          row  col  channel  geoaddr x-int(V)  slope(adc/V)
#  Column headers and comments are allowed anywhere in the file, because
#  any line not starting with a number is interpreted as a comment.

import fileinput

print "board(hex) channel(0-31) column(1-6) row (1-5)",
print " threshold(V) gain(pF/pixel)"
print "----------------------------------------------",
print "----------------------------"

for line in fileinput.input():
   fields = line.split()
   if len(fields) < 6:
      continue
   try:
      int(fields[0])
   except ValueError:
      continue
   row = int(fields[0])
   col = int(fields[1])
   chan = int(fields[2])
   addr = fields[3]
   thresh = float(fields[4])
   slope = float(fields[5])
   print "  {0}{1:11d}".format(addr, chan),
   print "{0:13d}{1:13d}".format(col + 1, row + 1),
   if thresh > 0:
      print "{0:12.3f}".format(thresh),
   else:
      print "{0:8d}    ".format(0),
   if slope > 0:
      print "{0:13.3f}".format(slope / 100),
   else:
      print "{0:9d}   ".format(1),
   print
