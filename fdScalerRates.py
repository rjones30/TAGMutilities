#!/usr/bin/env python
#
# fdScalerRates.py - utility for reading the output from a run of
#                    ratevsthreshold_allchan that runs on the frontend
#                    discriminator roc and sweeps through a sequence of
#                    threshold values, reporting the scalers rates at
#                    each point in the sequence. To plot these rates,
#                    save the output files from one of these scans in
#                    a directory, and give the name of the directory
#                    as an argument to the hscan() method below.
#
# author: richard.t.jones at uconn.edu
# version: january 17, 2018

import re
import os
import sys
from ROOT import *
import numpy

# ttag_tagm is taken from the ccdb record /Translation/DAQ2detector
# TAGM section. It is a sequence map ordered by increasing discriminator
# slot, channel in the roctagm2 crate to fiber column. Individual
# fiber outputs from columns 7, 27, 81, and 97 show up as 103..122.
ttab_tagm = {4:[3,2,1,6,5,4,103,104,105,106,107,9,8,7,12,11],
             5:[10,15,14,13,18,17,16,21,20,19,24,23,22,108,109,110],
             6:[111,112,27,26,25,30,29,28,33,32,31,36,35,34,39,38],
             7:[37,42,41,40,45,44,43,48,47,46,51,50,49,54,53,52],
             8:[57,56,55,60,59,58,63,62,61,66,65,64,69,68,67,72],
             9:[71,70,75,74,73,78,77,76,113,114,115,116,117,81,80,79],
             10:[84,83,82,87,86,85,90,89,88,93,92,91,96,95,94,118],
             11:[119,120,121,122,99,98,97,100,101,102,123,124,125,126,127,128]}

def hscan(indir):
   """
   Reads scaler rates from 128 plain text files stored in the directory
   named in argument indir. It returns returns a 2D histogram containing
   the rate as a function of threshold vs column. Individual readout
   channels are assigned column numbers 103..122. Non-uniform steps are
   allowed between the threshold values in the scan.
   """
   rates = {}
   for f in os.listdir(indir):
      p = re.match(r"DSC_ratevthresh_roctagm2_..h.._s([0-9]+)c([0-9]+).txt", f)
      if p:
         try:
            slot = int(p.group(1))
            chan = int(p.group(2))
            col = ttab_tagm[slot][chan]
         except:
            print "bad slot, chan, col:", slot, chan, col
            continue
      else:
         print "bad match:", f
         continue
      for line in open(os.path.join(indir, f)):
         fields = line.split()
         thresh = float(fields[0])
         rate = float(fields[1])
         if not thresh in rates:
            rates[thresh] = [0] * 129;
         rates[thresh][col] = rate
   nthresh = len(rates.keys())
   if nthresh == 0:
      return 0
   threshes = sorted(rates.keys())
   threshes.append(threshes[-1] + 1)
   xbins = numpy.array(threshes, dtype=float)
   h2 = TH2D("h2","threshold scan", 128, 1, 129, nthresh, xbins)
   for thresh in rates:
      for i in range(0, len(rates[thresh])):
         j = h2.GetYaxis().FindBin(thresh)
         h2.SetBinContent(i, j, rates[thresh][i])
   h2.SetStats(0)
   h2.GetXaxis().SetTitle("TAGM column")
   h2.GetYaxis().SetTitle("threshold (discriminator mV)")
   h2.GetYaxis().SetTitleOffset(1.5)
   return h2

def combine(h2list):
   """
   Often there is a beam trip that takes place in the middle of a scan,
   which leaves an empty band across the plot where the counts are zero.
   This function takes a list of histograms created by hscan from different
   scans, and builds a composite image by using later histograms to fill
   in the empty bands that are there in earlier histograms. Valid data
   from the earlier histograms in the list are not overwritten by those
   that appear later in the list unless they are zero. All histograms in
   the list are presumed to have the same dimensions and axis binning.
   """
   if len(h2list) == 0:
      return 0
   hcomb = gROOT.FindObject("hcomb")
   if hcomb:
      hcomb.Delete()
   hcomb = h2list[0].Clone("hcomb")
   for ihist in range(1, len(h2list)):
      hy = hcomb.ProjectionY("hy")
      h2y = h2list[ihist].ProjectionY("h2y")
      nbinx = hcomb.GetNbinsX()
      nbiny = hcomb.GetNbinsY()
      ymax = 0
      ibiny = 1
      while ibiny < nbiny - 1:
         y = hy.GetBinContent(ibiny)
         ymax = y if y > ymax else ymax
         if ymax > 0 and y == 0:
            canfill = True
            for ibiny2 in range(ibiny-2, ibiny+3):
               y2 = h2y.GetBinContent(ibiny2)
               if y2 == 0:
                  canfill = False
            if canfill:
               ibiny2 = ibiny - 1
               while ibiny2 < nbiny - 1:
                  for ibinx in range(1, nbinx + 1):
                     y2 = h2list[ihist].GetBinContent(ibinx, ibiny2)
                     hcomb.SetBinContent(ibinx, ibiny2, y2)
                  ibiny2 += 1
                  if h2y.GetBinContent(ibiny2) == 0:
                     break
                  if hy.GetBinContent(ibiny2+1) == 0:
                     continue
                  if h2y.GetBinContent(ibiny2+1) == 0:
                     break
                  for ibinx in range(1, nbinx + 1):
                     y2 = h2list[ihist].GetBinContent(ibinx, ibiny)
                     hcomb.SetBinContent(ibinx, ibiny, y2)
                     y2 = h2list[ihist].GetBinContent(ibinx, ibiny+1)
                     hcomb.SetBinContent(ibinx, ibiny+1, y2)
                  ibiny2 += 2
                  break
               ibiny = ibiny2
            else:
               ibiny += 1
         else:
            ibiny += 1
      hy.Delete()
      h2y.Delete()
   return hcomb
      
def hall_1_2018(): 
   """
   Reads in a set of 6 scans done in January 2018 and put them out
   into a TAGMspectra file for input to fityields.
   """
   h2 = [hscan("test/scan" + str(i)) for i in range(1,7)]
   global hagg
   hagg = combine(h2[::-1])
   nbins = hagg.GetNbinsY()
   xbins = [hagg.GetYaxis().GetBinLowEdge(i) for i in range(1, nbins+2)]
   xbins_rescaled = map(lambda t: t * 10 + 1000, xbins)
   f = TFile("TAGMspectra_1_2018.root", "recreate")
   for col in range(1, 129):
      h = hagg.ProjectionY("col" + str(col), col, col)
      for i in range(1, nbins):
         rate = h.GetBinContent(i)
         rate -= h.GetBinContent(i+1)
         rate = rate if rate > 0 else 0
         h.SetBinContent(i, rate)
      h.SetBinContent(nbins, 0)
      h.GetXaxis().Set(nbins, numpy.array(xbins_rescaled, dtype=float))
      h.SetTitle("column " + str(col))
      h.Write()
   f.Close()

def hcollect(colog):
   """
   Reads scaler rates from a text file generated using the ROCutilities
   script ratevsthreshold_collect.py, which collects all of the output
   files from a series of ratevsthreshold_allchan runs and summarizes 
   the results in a single file. It returns returns a 2D histogram containing
   the rate as a function of threshold vs column. Individual readout
   channels are assigned column numbers 103..122. Non-uniform steps are
   allowed between the threshold values in the scan.
   """
   rates = {}
   for line in open(colog):
      p = re.match(r"threshold ([0-9]+)", line)
      if p:
         try:
            thresh = int(p.group(1))
         except:
            print "bad", line
            continue
      p = re.match(r"slot ([0-9]+):", line)
      if p:
         try:
            slot = int(p.group(1))
         except:
            print "bad", line
            continue
         fields = line.split()
         for chan in range(0,16):
            col = ttab_tagm[slot][chan]
            rate = float(fields[chan + 2])
            if not thresh in rates:
               rates[thresh] = [0] * 129;
            rates[thresh][col] = rate
   nthresh = len(rates.keys())
   if nthresh == 0:
      return 0
   threshes = sorted(rates.keys())
   threshes.append(threshes[-1] + 1)
   xbins = numpy.array(threshes, dtype=float)
   h2 = TH2D("h2","threshold scan", 128, 1, 129, nthresh, xbins)
   for thresh in rates:
      for i in range(0, len(rates[thresh])):
         j = h2.GetYaxis().FindBin(thresh)
         h2.SetBinContent(i, j, rates[thresh][i])
   h2.SetStats(0)
   h2.GetXaxis().SetTitle("TAGM column")
   h2.GetYaxis().SetTitle("threshold (discriminator mV)")
   h2.GetYaxis().SetTitleOffset(1.5)
   return h2

def visualize_thresholds(h2drates, threshold_file): 
   """
   Reads in a set of discriminator thresholds from a file written by
   fdThresholds.py, and marks where they fall on the pulse height spectrum
   based on discriminator threshold scan data.
   """
   threshes = [0] * 129
   for line in open(threshold_file):
      p = re.match(r"slot ([0-9]+):", line)
      if p:
         try:
            slot = int(p.group(1))
         except:
            print "bad", line
            continue
      if re.match(r"DSC2_ALLCH_THR ", line):
         fields = line.split()
         for chan in range(0,16):
            col = ttab_tagm[slot][chan]
            try:
               threshes[col] = int(fields[chan + 1])
            except:
               threshes[col] = 999
   nbins = h2drates.GetNbinsY()
   xbins = [h2drates.GetYaxis().GetBinLowEdge(i) for i in range(1, nbins+2)]
   col = 1
   while col < 129:
      h = h2drates.ProjectionY("col" + str(col), col, col)
      for i in range(1, nbins):
         rate = h.GetBinContent(i)
         rate -= h.GetBinContent(i+1)
         if rate < 0 and i > 1:
            rate = (rate + h.GetBinContent(i-1)) / 2
            h.SetBinContent(i-1, rate)
         h.SetBinContent(i, rate)
      h.SetBinContent(nbins, 0)
      h.SetTitle("column " + str(col))
      if not gROOT.FindObject("c1"):
         c1 = TCanvas("c1", "c1", 300, 300, 500, 500)
      c1.SetLogx()
      h.GetXaxis().SetRangeUser(1,2000)
      h.Draw()
      thresh = threshes[col]
      thrx = numpy.array([thresh, thresh], dtype=float)
      thry = numpy.array([0, 1e6], dtype=float)
      thrg = TGraph(2, thrx, thry)
      thrg.SetLineColor(kBlue)
      thrg.SetLineWidth(2)
      thrg.Draw("same")
      c1.Update()
      resp = raw_input("Press t<value> to change threshold to value, " +
                       "# to jump to column #, " +
                       "<enter> to accept, " +
                       "q to quit: ")
      if resp == 'q':
         break
      elif resp == 'p':
         c1.Print("disc_spectrum_col{0}.png".format(col))
      elif len(resp) > 0 and resp[0] == 't':
         threshes[col] = int(resp[1:])
         continue
      elif len(resp) > 0:
         try:
            nextcol = int(resp)
            col = nextcol
            continue
         except:
            pass
      col += 1
   return threshes
