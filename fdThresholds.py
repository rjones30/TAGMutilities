#!/usr/bin/env python
#
# fdThresholds.py - utility for reading the output from a run of fityields
#                   over discriminator threshold scan data and use that
#                   information to compute values for the online discriminator
#                   thresholds to use for optimal efficiency and rejection
#                   of background.
#
# author: richard.t.jones at uconn.edu
# version: january 16, 2018

import sys
import fileinput
import re

threshold_fraction = 0.5
pedestal_offset = 100

# ttag_tagm is taken from the ccdb record /Translation/DAQ2detector
# TAGM section. It is a map from fADC250 slot number in TAGM crate
# roctagm1 and channel number 0..15 within the slot to fiber 
# row,column index encoded as row*1000 + column.
ttab_tagm = {4: [3,2,1,6,5,4,103,104,105,106,107,9,8,7,12,11],
             5: [10,15,14,13,18,17,16,21,20,19,24,23,22,108,109,110],
             6: [111,112,27,26,25,30,29,28,33,32,31,36,35,34,39,38],
             7: [37,42,41,40,45,44,43,48,47,46,51,50,49,54,53,52],
             8: [57,56,55,60,59,58,63,62,61,66,65,64,69,68,67,72],
             9: [71,70,75,74,73,78,77,76,113,114,115,116,117,81,80,79],
             10: [84,83,82,87,86,85,90,89,88,93,92,91,96,95,94,118],
             11: [119,120,121,122,99,98,97,100,101,102]}

def usage():
   print "Usage: fdThresholds.py <fityields_out>"
   sys.exit(1)

def read_fityields_out():
   """
   Reads from an external text stream the output from a prior run
   of fityields.fit(), and returns the results in the form of an array
   T[column] containing the optimal discriminator threshold for each
   column. Normally all of the fibers in a column should match.
   """

   thresh = [0] * 129
   for line in fileinput.input():
      if not re.match("^ ", line):
         continue
      fields = line.split()
      column = int(fields[0])
      run = int(fields[1])
      mean = float(fields[2])
      sigma = float(fields[3])
      thresh[column] = mean
   thresh = map(lambda x: (x - 900) * threshold_fraction + 900, thresh)
   thresh = map(lambda x: (x - 1000) / 10, thresh)
   return thresh

thresh = read_fityields_out()
print thresh
for slot in ttab_tagm:
   print "slot " + str(slot) + ":"
   print "DSC2_ALLCH_THR   ",
   for ichan in range(0, len(ttab_tagm[slot])):
      col = ttab_tagm[slot][ichan]
      t = thresh[col]
      t = t if t > 0 else 10
      print " " + str(int(round(t))),
   print ""
