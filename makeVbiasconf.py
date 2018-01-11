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
#     makeVbiasconf.py [options] input_text_file > output_conf_file
#   or
#     cat input_text_file | makeVbiasconf.py [options] > output_conf_file
#   where options may include:
#     -C <config_file>: selects an input config file, eg. setVbias.config
#                       in the same directory as the executable is default.
#   If an input config file is supplied as an option, the values in the
#   input config are copied to the output, with gain values overridden by
#   new constants computed on the basis of data in the input text file. If
#   no input config file is specified, a virgin config file is written to
#   the output with null values in the yields column.
#
# input:
#  The input should be a text file in a free-form space-delimited multi-column
#  format. The order and meaning of the columns is as follows.
#          row  col  channel  geoaddr x-int(V)  slope(adc/V)
#  Column headers and comments are allowed anywhere in the file, because
#  any line not starting with a number is interpreted as a comment.
#
# output:
#  A new setVbias.conf file that can be used with the setVbias utility to
#  apply a flexible set of bias conditions to the TAGM. Note that at this
#  point in the calibration procedures nothing is known about the yields
#  of the fibers in response to electrons, so the values in that column
#  are left at zero. To fill those in, see the reconfig.py utility.

import fileinput
import sys

nrows = 5
ncols = 102

# empirical factor to convert from fit slope(adc_peak/V) to gain(pF)
fit_slope_to_gain_pF = 0.011

# global values for config_conf table
nchan = nrows * ncols
rownum = [0] * nchan
column = [0] * nchan
board = [0] * nchan
channel = [0] * nchan
Vthresh = [0] * nchan
gain_pF = [0] * nchan
yield_iV = [0] * nchan

def usage():
   print "Usage:"
   print "     makeVbiasconf.py [options] input_text_file > output_conf_file"
   print "  or"
   print "     cat input_text_file | makeVbiasconf.py [options] > output_conf_file"
   print "  where options may include:"
   print "     -C <config_file>: selects an input config file, eg. setVbias.config"
   print "                       in the same directory as the executable is default."
   print "     -h (or --help):   print this message and exit."
   print
   
def readconf(conf):
   """
   Read the configuration from an input config file
   specified on the command line.
   """
   for line in open(conf):
      try:
         c = int(line.split()[2])
         r = int(line.split()[3])
      except (IndexError, ValueError):
         continue
      i = (r - 1)*ncols + (c - 1)
      rownum[i] = r
      column[i] = c
      board[i] = int(line.split()[0], 16)
      channel[i] = int(line.split()[1])
      Vthresh[i] = float(line.split()[4])
      gain_pF[i] = float(line.split()[5])
      yield_iV[i] = float(line.split()[6])

# parse the commandline options
while len(sys.argv) > 1 and sys.argv[1][0] == '-':
   arg = sys.argv.pop(1)
   if arg == "-C":
      conf = sys.argv.pop(1)
      readconf(conf)
   else:
      usage()
      sys.exit(1)

# read input from stdin or file specified on the commandline
for line in fileinput.input():
   fields = line.split()
   if len(fields) < 6:
      continue
   try:
      int(fields[0])
   except ValueError:
      continue
   row = int(fields[0]) + 1
   col = int(fields[1]) + 1
   chan = int(fields[2])
   addr = int(fields[3], 16)
   thresh = float(fields[4])
   slope = float(fields[5])
   found = 0
   if row == 0 or col == 0:
      continue
   for i in range(0, nchan):
      if row == rownum[i] and col == column[i]:
         if addr == board[i] and chan == channel[i]:
            Vthresh[i] = thresh
            gain_pF[i] = slope * fit_slope_to_gain_pF
            found = 1
            break
         else:
            print "Error - board,channel mismatch on row=", row,
            print ", column=", col, "- cannot continue!"
            print "  setup_conf file shows board={0:02x}, channel={1}".format(board[i], channel[i])
            print "  but input file shows board={0:02x}, channel={1}".format(addr, chan)
            sys.exit(1)
   if found == 0:
      for i in range(0, nchan):
         if rownum[i] == 0 or column[i] == 0:
            rownum[i] = row
            column[i] = col
            board[i] = addr
            channel[i] = chan
            Vthresh[i] = thresh
            gain_pF[i] = slope * fit_slope_to_gain_pF
            yield_iV[i] = 0
            break

# send the output to stdout in setup_conf format
print "".join(["board(hex) channel(0-31) column(1-6) row(1-5) ",
               "threshold(V) gain(pF/pixel) yield(pixel/hit/V)"])
print "".join(["----------------------------------------------",
               "----------------------------------------------"])

for i in range(0, nchan):
   if rownum[i] == 0 or column[i] == 0:
      break
   print "   {0:02x}{1:12d}".format(board[i], channel[i]),
   print "{0:12d}{1:12d}".format(column[i], rownum[i]),
   if Vthresh[i] >= 0:
      print "{0:11.3f}".format(Vthresh[i]),
   else:
      print "{0:8d}   ".format(0),
   if gain_pF[i] > 0:
      print "{0:12.3f}".format(gain_pF[i]),
   else:
      print "{0:8d}    ".format(1),
   print "{0:15.1f}".format(yield_iV[i])
