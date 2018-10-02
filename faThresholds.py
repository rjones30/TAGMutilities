#!/usr/bin/env python
#
# faThresholds.py - utility for reading the output from a run of setVbias
#                   and use that information to compute values for the
#                   online thresholds to use for optimal efficiency and
#                   rejection of background.
#
# author: richard.t.jones at uconn.edu
# version: january 12, 2018

import sys
import fileinput
import re

threshold_fraction = 0.33
pedestal_offset = 100

# ttag_tagm is taken from the ccdb record /Translation/DAQ2detector
# TAGM section. It is a map from fADC250 slot number in TAGM crate
# roctagm1 and channel number 0..15 within the slot to fiber 
# row,column index encoded as row*1000 + column.
ttab_tagm = {3: [3,2,1,6,5,4,1009,2009,3009,4009,5009,9,8,7,12,11],
             4: [10,15,14,13,18,17,16,21,20,19,24,23,22,1027,2027,3027],
             5: [4027,5027,27,26,25,30,29,28,33,32,31,36,35,34,39,38],
             6: [37,42,41,40,45,44,43,48,47,46,51,50,49,54,53,52],
             7: [57,56,55,60,59,58,63,62,61,66,65,64,69,68,67,72],
             8: [71,70,75,74,73,78,77,76,1081,2081,3081,4081,5081,81,80,79],
             9: [84,83,82,87,86,85,90,89,88,93,92,91,96,95,94,1099],
             10: [2099,3099,4099,5099,99,98,97,100,101,102]}

def usage():
   print "Usage: faThresholds.py <setVbias_logfile>"
   sys.exit(1)

def read_setVbias_log():
   """
   Reads from an external text stream the output from a prior run
   of setVbias, and returns the results in the form of an array
   P[row][column] containing the mean peak value for each fiber
   in the detector. Normally the fibers in a column should match.
   """

   peaks = [[0] * 103 for i in range(0, 6)]
   lines = 0
   values = 0
   for line in fileinput.input():
      colre = re.match(r"^expected pulse parameters in column ([0-9]+)", line)
      rowre = re.match(r"^  *row ([1-5]) : .* peak=([0-9.]+)fADCcounts", line)
      try:
         if colre:
            col = int(colre.group(1))
         elif rowre:
            row = int(rowre.group(1))
            peaks[row][col] = float(rowre.group(2))
            values += 1
            lines += 1
      except:
         print "did something go wrong? row,col=", row, col
         sys.exit(1)
   return peaks

peaks = read_setVbias_log()
for slot in ttab_tagm:
   print "slot " + str(slot) + ":"
   print "FADC250_ALLCH_THR   ",
   for ichan in range(0, len(ttab_tagm[slot])):
      col = ttab_tagm[slot][ichan] % 1000
      row = int(ttab_tagm[slot][ichan] / 1000)
      if row == 0:
         peak = 10000
         for row in range(1,6):
             p = peaks[row][col]
             peak = peak if peak < p or p == 0 else p
      else:
         peak = peaks[row][col]
      thresh = int(peak * threshold_fraction) + pedestal_offset
      thresh = thresh if thresh > 0 else 1000
      print " " + str(thresh),
   print ""
