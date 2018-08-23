#!/bin/env python
#
# fitpeak.py - utility functions for reading TAGM pulse height spectra
#              created using DANA plugin TAGM_bias, fitting the primary
#              single-pixel peak to a gaussian, plotting the peak pulse
#              height vs bias voltage, and fitting it to a straight line
#              to extract the Vbias threshold and gain constants.
#
# author: aebarnes at jlab.org
# version: april 1, 2016

import os
import re
from ROOT import *
from array import array
import numpy
import time

minEntries = 1200
maxEntries = 100000

# empirical factor to convert from fit slope(adc_peak/V) to gain(pF)
fit_slope_to_gain_pF = 0.011 # pC per adc_peak

# dark rate runs taken in January, 2018
gval = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['40145', '40146', '40147', '40148', '40149'],
        ['40150', '40151', '40152', '40153', '40154'],
        ['40037', '40038', '40039', '40040', '40041'],
        ['40155', '40156', '40157', '40158', '40159'],
        ['40042', '40043', '40044', '40045', '40046'],
        ['40160', '40161', '40162', '40163', '40164'],
        ['40047', '40048', '40049', '40050', '40051']]

# dark rate runs taking in August, 2018
gval = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['50195', '50196', '50197', '50198', '50199'],
        ['50180', '50181', '50182', '50183', '50184'],
        ['50200', '50201', '50202', '50203', '50204'],
        ['50185', '50186', '50187', '50188', '50189'],
        ['50205', '50206', '50207', '50208', '50209'],
        ['50190', '50191', '50192', '50193', '50194']]

conf = 'setVbias_fulldetector-1-30-2018.conf'

peak_fit_query = False

latest_results = {}

def Fit1(row, col):
   """
   Fit a full set of single-pixel dark pulse spectra and write out
   a new set of calibration constants into fitpeaks.txt, overwriting
   the file if it exists already.
   """
   graph = TGraphErrors(len(gset))
   p = [0] * len(gset)
   V = [0] * len(gset)
   for ig in range(len(gset)):
      fin = TFile("TAGMbias_{0}.root".format(gset[ig][row-1]))
      hin = fin.Get("h_spectra_" + str(col))
      print hin

      # Check for bad electronic channels
      # if GetNumberPeaks(h25) < 2: continue
      # if GetNumberPeaks(h35) < 2: continue
      # if GetNumberPeaks(h45) < 2: continue
      # Add some kind of error recording

      # Get peaks from each histogram
      p[ig] = GetPeak(hin)
      if p[ig] < 0:
         print 'Fit failed for row', row, ' col ', col,
         print 'gain setting', gval[ig], 'entries', hin.GetEntries()
         p[ig] = 0

      # Get voltages
      V[ig] = GetVoltage(gval[ig], row, col, conf)

      # Load values into graph
      graph.SetPoint(ig, V[ig], p[ig])
      if p[ig] == 0:
         graph.SetPointError(ig, 0, 0)
         continue
      ncounts = hin.GetEntries()
      if ncounts > minEntries and ncounts < maxEntries:
         graph.SetPointError(ig, 0.01, minEntries/hin.GetEntries())
      else:
         graph.SetPointError(ig, 0, 0)

      # If top points are divergent, kill them off
      for ig in range(3, len(gset)):
         ey_ = graph.GetErrorY(ig-3)
         ey0 = graph.GetErrorY(ig-2)
         ey1 = graph.GetErrorY(ig-1)
         ey2 = graph.GetErrorY(ig)
         if ey_ * ey0 * ey1 * ey2 == 0:
            continue
         x0 = Double()
         y0 = Double()
         graph.GetPoint(ig-2, x0, y0)
         x1 = Double()
         y1 = Double()
         graph.GetPoint(ig-1, x1, y1)
         x = Double()
         y = Double()
         graph.GetPoint(ig, x, y)
         slope = (y1 - y0) / (x1 - x0)
         if slope < 5:
            continue
         yline = y0 + (x - x0) * slope
         if y > yline * 1.2:
            while ig < len(gset):
               graph.SetPointError(ig, 0, 0)
               ig += 1
            break

   # Fit TGraph
   fun1 = TF1("fun1", Hyperfit, 50, 100, 3)
   fun1.SetParameter(0, 71.0)
   fun1.SetParameter(1, 25)
   fun1.SetParameter(2, 5)
   ptr = graph.Fit(fun1, "s")
   xint = ptr.Parameters()[0]
   yint = ptr.Parameters()[1]
   rasymp = ptr.Parameters()[2]
   gref = 40
   Vref = xint + (gref**2 - yint**2)**0.5 / rasymp
   slope = (Vref - xint) * rasymp**2 / gref
   Vbd = Vref - gref / slope
   print Vbd, slope
   graph.SetTitle("gain curve for row " + 
                  str(row) + " col " + str(col))
   graph.Draw("A*")
   xasym = numpy.array([Vref - 2, Vref + 2], dtype=float)
   yasym = numpy.array([gref - 2*slope, gref + 2*slope], dtype=float)
   gasym = TGraph(2, xasym, yasym)
   gasym.SetLineColor(kRed)
   gasym.SetLineStyle(9)
   gasym.Draw("l")
   c1.Update()

   global peak_fit_query
   ans = raw_input("r to redo, enter to accept? ")
   if len(ans) > 0 and ans[0] == 'r':
      peak_fit_query = 1
      return Fit1(row, col)
   elif len(ans) > 0 and ans[0] == 'p':
      c1.Print("fitpeaks_{0}_{1}.png".format(row,col))
   else:
      peak_fit_query = 0

   gain_pF = slope * fit_slope_to_gain_pF
   latest_results[(row,col)] = "{0} {1}".format(Vbd, gain_pF)

def Hyperfit(var, par):
   """
   Hyperbolic fit function to apply to graphs of single-pixel
   pulse height maximum versus bias voltage. This should normally
   be a straight line, but there is shift toward high pulse height
   at low values of Vbias that comes from the fadc readout threshold
   suppressing pulses below a certain minimum pulse height.
   """
   V = var[0]
   V0 = par[0]
   y0 = par[1]
   slope = par[2]
   return ((slope * (V - V0))**2 + y0**2)**0.5

def GetPeak(h):
   """
   Find the x value of the maximum of the primary peak in histogram h
   """
   h.RebinX(4)
   maximum = h.GetBinCenter( h.GetMaximumBin() )
   if h.GetEntries() < 1:
      return 0

   try:
      ptr = h.Fit("gaus", "sqr", "", maximum - 5, maximum + 5)
      sigma = ptr.Parameters()[0]
      mean = ptr.Parameters()[1]
   except:
      mean = -1
      sigma = -1
   #if (sigma > 6):
   #    mean = -1
   if peak_fit_query:
      h.Draw()
      c1.Update()
      ans = raw_input("x to reject, enter to accept? ")
      if len(ans) > 0 and ans[0] == 'x':
         return 0
   return float(mean)

def GetNumberPeaks(h):
   """
   Check that there are multiple peaks in histogram h, 
   and if not, mark as problem channel.
   """
   if (h.GetEntries() < 100):
      return 0

   maximum = h.GetBinCenter( h.GetMaximumBin() )

   npeaks = 0
   return npeaks

def GetGeoAddr(col):
   """
   Look up the geographical address of the board that contains
   the sum circuit for TAGM column col.
   """
   baseAddr = int('8e', 16)
   geoaddr = baseAddr + int(col - 1)/6

   return hex(geoaddr).split('x')[-1]

def GetChannel(row, col):
   """
   Look up the fadc250 board channel number that digitizes
   the sum signal for TAGM column col, taking the cable swap
   into account, eg. col 3 is actually col 1 electronically.
   """
   newcol = 3*(1 + (col - 1)/3) - (col - 1)%3

   channel = 5*( (newcol - 1) % 6 ) + (row - 1)
   return channel

def GetVoltage(g, row, col, conf):
   """
   Compute the Vbias voltage that would be applied to the SiPM
   that reads out fiber row,col if it is set to gain g, using the
   calibration contained in setVbias.conf file conf.
   """
   conf_file = open(conf, 'r')
   for line in conf_file:
      if not line.split()[0][0].isdigit():
         continue
      if int(line.split()[2]) == col and int(line.split()[3]) == row:
         thresh = float(line.split()[4])
         gain = float(line.split()[5])

   voltage = thresh + (g / gain)

   conf_file.close()
   return float(voltage)

def Write():
   """
   Write new results to a file in the standard format of setVbias.conf
   using the prior conf file as a source of the light yield constants,
   since these cannot be evaluated based on dark count data.
   """
   outfile = open('fitpeaks.txt', 'w')
   conf_file = open(conf, 'r')
   for line in conf_file:
      if not line.split()[0][0].isdigit():
         outfile.write(line)
         continue
      (geo, cha, col, row, Vbd, gpF, ypi) = line.split()
      r = int(row)
      c = int(col)
      if (r,c) in latest_results:
         line = line[0:42]
         line += "{0:13.3f}".format(float(latest_results[(r,c)].split()[0]))
         line += "{0:12.3f}".format(float(latest_results[(r,c)].split()[1]))
         line += "{0:16.2f}".format(float(ypi))
         line += "\n"
      outfile.write(line)
   outfile.close()
