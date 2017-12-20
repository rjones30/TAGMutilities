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
import argparse
from ROOT import *
from array import array
import time

minEntries = 1200
maxEntries = 10000

def main():
   # Use argparse if required
   # maybe use config file that has run number next to row and voltage

   gval = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
   gset = [['40145', '40146', '40147', '40148', '40149'],
           ['40150', '40151', '40152', '40153', '40154'],
           ['40037', '40038', '40039', '40040', '40041'],
           ['40155', '40156', '40157', '40158', '40159'],
           ['40042', '40043', '40044', '40045', '40046'],
           ['40160', '40161', '40162', '40163', '40164'],
           ['40047', '40048', '40049', '40050', '40051']]

   files = sorted([f for f in os.listdir('.') \
                   if f.split('.')[-1] == 'root' and \
                      re.match(r"^TAGMbias_", f) ])
   conf = 'setVbias_fulldetector-2-23-2017.conf'

   outfile = open('fitpeaks.txt', 'w')

   graph = TGraphErrors(len(gset))

   gskip = 0
   for row in range(1,6):
      fin = [0] * len(gset)
      for ig in range(len(gset)):
           fin[ig] = TFile([f for f in files if gset[ig][row-1] in f][0])

      for col in range(1,103):
           p = [0] * len(gset)
           V = [0] * len(gset)
           for ig in range(len(gset)):
              hin = fin[ig].Get("h_spectra_" + str(col))

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
           if p[-1] > 0:
              ptr = graph.Fit("pol1", "sq")
              slope = ptr.Parameters()[1]
              yint = ptr.Parameters()[0]
              xint = -yint/slope
           else:
              slope = 0
              xint = 0
           if gskip > 0:
              gskip -= 1
           else:
              graph.SetTitle("gain curve for row " + 
                             str(row) + " col " + str(col))
              graph.Draw("A*")
              c1.Update()
              ans = raw_input("number to skip before next check [0]? ")
              try:
                 gskip = int(ans)
              except:
                 gskip = 0

           chan = GetChannel(row, col)
           geoaddr = GetGeoAddr(col)
           outfile.write(' {0} {1} {2} {3} {4} {5}\n'.format(
                         row-1, col-1, chan, geoaddr, xint, slope))
   outfile.close()

def GetPeak(h):
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

   #h.Draw()
   #c1.Update()
   #raw_input("press enter to continue: ")
   return float(mean)

def GetNumberPeaks(h):
   # Use this to make sure there are multiple peaks
   # If not, mark as problem channel

   if (h.GetEntries() < 100):
      return 0

   maximum = h.GetBinCenter( h.GetMaximumBin() )

   npeaks = 0
   return npeaks

def GetGeoAddr(col):
   baseAddr = int('8e', 16)
   geoaddr = baseAddr + int(col - 1)/6

   return hex(geoaddr).split('x')[-1]

def GetChannel(row, col):
   # Take cable swap into account (col 3 is actually col 1 electronically)

   newcol = 3*(1 + (col - 1)/3) - (col - 1)%3

   channel = 5*( (newcol - 1) % 6 ) + (row - 1)
   return channel

def GetVoltage(g, row, col, conf):
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

if __name__ == "__main__":
   main()
