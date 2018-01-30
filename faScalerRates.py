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
#
# threshold scans:
#    This module has been extended to interpret the output from fadc250
#    threshold scans performed using the utility faDoThresholdScan on
#    the roctagm1 frontend. Simply save the output from faDoThresholdScan
#    to a file, then give that filename as an argument to the hscan()
#    function below. It will return a 2D histogram with column number
#    on the x axis, threshold on the y axis, and rate on the z axis.

import re
import sys
from ROOT import *
import numpy

# ttag_tagm is taken from the ccdb record /Translation/DAQ2detector
# TAGM section. It is a sequence map ordered by increasing fADC250
# slot, channel in the roctagm1 crate to fiber column. Individual
# fiber outputs from columns 7, 27, 81, and 97 show up as 103..122.
ttab_tagm = [3,2,1,6,5,4,103,104,105,106,107,9,8,7,12,11,
             10,15,14,13,18,17,16,21,20,19,24,23,22,108,109,110,
             111,112,27,26,25,30,29,28,33,32,31,36,35,34,39,38,
             37,42,41,40,45,44,43,48,47,46,51,50,49,54,53,52,
             57,56,55,60,59,58,63,62,61,66,65,64,69,68,67,72,
             71,70,75,74,73,78,77,76,113,114,115,116,117,81,80,79,
             84,83,82,87,86,85,90,89,88,93,92,91,96,95,94,118,
             119,120,121,122,99,98,97,100,101,102,123,124,125,126,127,128]

def hist(infile):
   """
   Reads scaler rates from a plain text file output from faPrintScalerRates
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

def hscan(infile):
   """
   Reads scaler rates from a plain text file output from faDoThresholdScan
   and returns a histogram containing the rate on threshold vs column as a
   2D histogram. Individual readout channels are assigned column numbers
   103..122. Non-uniform bins are used on the threshold axis.
   """
   rates = {}
   thresh = []
   nthresh = 0
   for line in open(infile):
      threshre = re.match(r"threshold set to ([0-9]+)", line)
      if threshre:
         nthresh += 1
         thresh.append(float(threshre.group(1)))
         rates[nthresh] = [0] * 129
         itab = 0
      vals = line.split()
      for val in vals:
         if re.match(r"[0-9]+\.[0-9]$", val) and val != "250000.0":
            col = ttab_tagm[itab]
            try:
               rates[nthresh][col] = float(val)
            except:
               print "bad assign at thresh,col=", nthresh, col
            itab += 1
   thresh.append(2 * thresh[nthresh-1] - thresh[nthresh-2])
   xbins = numpy.array(thresh, dtype=float)
   h2 = TH2D("h2","threshold scan", 128, 1, 129, nthresh, xbins)
   for j in rates:
      for i in range(0, len(rates[j])):
         h2.SetBinContent(i, j, rates[j][i])
   h2.SetStats(0)
   h2.GetXaxis().SetTitle("TAGM column")
   h2.GetYaxis().SetTitle("threshold (fADC counts)")
   h2.GetYaxis().SetTitleOffset(1.5)
   return h2

def hdiffer(infile):
   """
   Reads scaler rates from a plain text file output from faDoThresholdScan
   and returns histograms containing the pulse amplitude spectrum that comes
   from differentiating the rate vs threshold for each column.
   """
   scalef = 1 / 0.235
   offset = 900
   spects = [0] * 129
   h2 = hscan(infile)
   nbins = h2.GetNbinsY()
   thresh = []
   for i in range(1, nbins + 1):
      thresh.append(h2.GetYaxis().GetBinLowEdge(i))
   thresh.append(h2.GetYaxis().GetBinUpEdge(nbins))
   thresh_rescaled = map(lambda t: (t - 100) / 0.235 + 900, thresh)
   xbins = numpy.array(thresh_rescaled, dtype=float)
   for col in range(1, 129):
      spects[col] = TH1D("col" + str(col), "column " + str(col), nbins, xbins)
      for i in range(1, nbins + 1):
         spects[col].SetBinContent(i, h2.GetBinContent(col, i) -
                                      h2.GetBinContent(col, i+1))
   return spects

def hall_1_2018():
   """
   Read in a set of 15 scans done in January 2018 and put them out
   into TAGMtree files for input to fityields.
   """
   for row in [1, 2, 3, 4, 5]:
      for gval in [25, 35, 45]:
         f = TFile("TAGMtrees_" + str(row) + str(gval) + ".root", "recreate")
         s = hdiffer("scans-1-30-2018/row" + str(row) + "g" + str(gval) + ".log")
         for h in s:
            if h:
               h.SetBinContent(h.GetNbinsX(), 0)
               h.Write()
         f.Close()
