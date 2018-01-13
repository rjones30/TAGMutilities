#!/usr/bin/env python
#
# faScalerRates.py - utility for reading the output from a run of
#                    faPrintScalerRates that runs on the frontend roc
#                    and prints out scalers rates every second for all
#                    fadc250 cards in the crate. To plot these rates,
#                    save a 1-second segment output segment from that
#                    utility to a file and give the name of the file
#                    as an argument to the hist() method below.
#
# author: richard.t.jones at uconn.edu
# version: january 12, 2018

import re
import sys
from ROOT import *

threshold_fraction = 0.5
pedestal_offset = 100

# ttag_tagm is taken from the ccdb record /Translation/DAQ2detector
# TAGM section. It is a map from fADC250 slot number in TAGM crate
# roctagm1 and channel number 0..15 within the slot to fiber 
# row,column index encoded as row*1000 + column.
ttab_tagm = [3,2,1,6,5,4,103,104,105,106,107,9,8,7,12,11,
             10,15,14,13,18,17,16,21,20,19,24,23,22,108,109,110,
             111,112,27,26,25,30,29,28,33,32,31,36,35,34,39,38,
             37,42,41,40,45,44,43,48,47,46,51,50,49,54,53,52,
             57,56,55,60,59,58,63,62,61,66,65,64,69,68,67,72,
             71,70,75,74,73,78,77,76,113,114,115,116,117,81,80,79,
             84,83,82,87,86,85,90,89,88,93,92,91,96,95,94,118,
             119,120,121,122,99,98,97,102,101,100,123,124,125,126,127,128]

def hist(infile):
   """
   Reads scaler rates from a plain text file (output from faPrintScalerRates)
   and returns a histogram containing the rate vs column. Individual readout
   channels are assigned column numbers 103..122.
   """
   h = TH1D("h","scaler rates",128,1,129)
   itab = 0
   for line in open(infile):
      vals = line.split()
      for val in vals:
         if re.match(r"[0-9]+\.[0-9]$", val) and val != "250000.0":
            col = ttab_tagm[itab]
            h.SetBinContent(col,float(val))
            itab += 1
   h.SetStats(0)
   h.GetXaxis().SetTitle("TAGM column")
   h.GetYaxis().SetTitle("rate (Hz)")
   h.GetYaxis().SetTitleOffset(1.5)
   return h
