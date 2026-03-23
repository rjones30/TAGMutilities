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
import random

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
conffile = 'setVbias_fulldetector-1-11-2018.conf'

# dark rate runs taking on August 19, 2018
gval = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['50195', '50196', '50197', '50198', '50199'],
        ['50180', '50181', '50182', '50183', '50184'],
        ['50200', '50201', '50202', '50203', '50204'],
        ['50185', '50186', '50187', '50188', '50189'],
        ['50205', '50206', '50207', '50208', '50209'],
        ['50190', '50191', '50192', '50193', '50194']]
conffile = 'setVbias_fulldetector-8-22-2018.conf'

# dark rate runs taking on August 26, 2018
gval = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['00072', '00073', '00074', '00075', '00076'],
        ['00057', '00058', '00059', '00060', '00061'],
        ['00077', '00078', '00079', '00080', '00081'],
        ['00062', '00063', '00064', '00065', '00066'],
        ['00082', '00083', '00084', '00085', '00086'],
        ['00067', '00068', '00069', '00070', '00071']]
conffile = 'setVbias_fulldetector-8-22-2018.conf'

# dark rate runs taking on August 28, 2018
gval = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['00105', '00106', '00107', '00108', '00109'],
        ['00090', '00091', '00092', '00093', '00094'],
        ['00110', '00111', '00112', '00113', '00114'],
        ['00095', '00096', '00097', '00098', '00099'],
        ['00115', '00116', '00117', '00118', '00119'],
        ['00100', '00101', '00102', '00103', '00104']]
conffile = 'setVbias_fulldetector-8-22-2018.conf'

# dark rate runs taking on January 21, 2019
gval = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['60158', '60161', '60164', '60167', '60170'],
        ['60142', '60145', '60148', '60152', '60155'],
        ['60159', '60162', '60165', '60168', '60171'],
        ['60143', '60146', '60149', '60153', '60156'],
        ['60160', '60163', '60166', '60169', '60172'],
        ['60144', '60147', '60150', '60154', '60157']]
conffile = 'setVbias_fulldetector-9-29-2018.conf'

# dark rate runs taken in November, 2019
gval = [0.45, 0.35, 0.25]
gset = [['70509', '70510', '70511', '70512', '70513'],
        ['70514', '70515', '70516', '70517', '70518'],
        ['70519', '70521', '70522', '70523', '70524']]
conffile = 'setVbias_fulldetector-2-9-2019.conf'

# dark rate runs taken in June, 2022
gval = [0.25, 0.35, 0.45]
gset = [['100293', '100296', '100299', '100302', '100305'],
        ['100294', '100297', '100300', '100303', '100306'],
        ['100295', '100298', '100301', '100304', '100307']]
conffile = 'setVbias_fulldetector-12-9-2019_calib.conf'

# light pulse runs taken in June, 2022
gval = [0.25, 0.35, 0.45]
gset = [['100592', '100595', '100598', '100601', '100662'],
        ['100593', '100596', '100599', '100602', '100663'],
        ['100594', '100597', '100600', '100603', '100664']]
conffile = 'setVbias_fulldetector-12-9-2019_calib.conf'

# light pulse runs taken in August, 2022
gval = [0.25, 0.35, 0.45]
gset = [['110456', '110460', '110463', '110467', '110470'],
        ['110458', '110461', '110464', '110468', '110471'],
        ['110459', '110462', '110465', '110469', '110472']]
conffile = 'setVbias_fulldetector-8-30-2022_calib.conf'

# dark pulse runs taken in January, 2023
gval = [0.25, 0.35, 0.45]
gset = [['120051', '120054', '120057', '120060', '120063'],
        ['120052', '120055', '120058', '120061', '120064'],
        ['120053', '120056', '120059', '120062', '120065']]
conffile = 'setVbias_fulldetector-8-30-2022_calib.conf'

# light pulse runs taken in January, 2023
gval = [0.25, 0.35, 0.45]
gset = [['120187', '120190', '120193', '120196', '120199'],
        ['120188', '120191', '120194', '120197', '120200'],
        ['120189', '120192', '120195', '120198', '120201']]
conffile = 'setVbias_fulldetector-1-8-2023.conf'

# Row-by-row scan data taken in March, 2023 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['120895', '120898', '120901', '120904', '120907'],
        ['120896', '120899', '120902', '120905', '120908'],
        ['120897', '120900', '120903', '120906', '120909']]
conffile = 'setVbias_fulldetector-1-16-2023.conf'

confref = conffile

peak_fit_query = False

latest_results = {}

def Fit1(row, col, interact=1):
   """
   Fit a the single-pixel dark pulse spectra for a single fiber and
   save a new set of calibration constants in an in-memory array.
   """
   graph = TGraphErrors(len(gset))
   p = [0] * len(gset)
   V = [0] * len(gset)
   for ig in range(len(gset)):
      fbias = "TAGMbias_{0}.root".format(gset[ig][row-1])
      if os.path.exists(fbias):
         fin = TFile(fbias)
         hin = fin.Get("h_spectra_" + str(col))
         print(hin)
      else:
         ftrees = "TAGMtrees_{0}.root".format(gset[ig][row-1])
         fin = TFile(ftrees)
         hin = TH1D("h_spectra_" + str(col), 
                    "fadc spectrum for column " + str(col),
                    300, 0, 300)
         fadc = fin.Get("fadc")
         fadc.Draw("peak-ped/4>>h_spectra_" + str(col),
                   "pt>300&&qf==0&&row==0&&col==" + str(col))
         print(hin)

      # Check for bad electronic channels
      # if GetNumberPeaks(h25) < 2: continue
      # if GetNumberPeaks(h35) < 2: continue
      # if GetNumberPeaks(h45) < 2: continue
      # Add some kind of error recording

      # Get peaks from each histogram
      p[ig] = GetPeak(hin)
      if p[ig] < 0:
         print('Fit failed for row', row, ' col ', col, end='')
         print('gain setting', gval[ig], 'entries', hin.GetEntries())
         p[ig] = 0

      # Get voltages
      V[ig] = GetVoltage(gval[ig], row, col, conffile)

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

   # Increase errors on points below threshold
   for ig in range(1, len(gset)):
      x = numpy.array([0], dtype=float)
      y = numpy.array([0], dtype=float)
      graph.GetPoint(ig-1, x, y)
      ylast = y[0]
      graph.GetPoint(ig, x, y)
      ythis = y[0]
      if ylast < ythis:
         break
      for iig in range(0, ig):
         ex = graph.GetErrorX(iig)
         ey = graph.GetErrorY(iig)
         ey = 0
         graph.SetPointError(iig, ex, ey)
   
   # Fit TGraph
   fun1 = TF1("fun1", Hyperfit, 50, 100, 3)
   global peak_fit_query
   if peak_fit_query:
      fun1.SetParameter(0, 71.0 + 0.5 * (random.uniform(0,1) - 0.5))
      fun1.SetParameter(1, 25 + 5 * random.uniform(0,1))
      fun1.SetParameter(2, 5 + 2 * random.uniform(0,1))
   else:
      fun1.SetParameter(0, 71.0)
      fun1.SetParameter(1, 25)
      fun1.SetParameter(2, 5)
   ptr = graph.Fit(fun1, "s")
   xint = ptr.Parameters()[0]
   yint = abs(ptr.Parameters()[1])
   rasymp = abs(ptr.Parameters()[2])
   gref = 40
   if gref > yint:
      Vref = xint + (gref**2 - yint**2)**0.5 / rasymp
   else:
      Vref = xint + gref / rasymp
   slope = (Vref - xint) * rasymp**2 / gref
   Vbd = Vref - gref / slope
   print(Vbd, slope)
   graph.SetTitle("gain curve for row " + 
                  str(row) + " col " + str(col))
   graph.Draw("A*")
   xasym = numpy.array([Vref - 2, Vref + 2], dtype=float)
   yasym = numpy.array([gref - 2*slope, gref + 2*slope], dtype=float)
   gasym = TGraph(2, xasym, yasym)
   gasym.SetLineColor(kRed)
   gasym.SetLineStyle(9)
   gasym.Draw("l")
   gline = Draw_gvsV(row, col, confref)
   gROOT.FindObject("c1").Update()

   if interact:
      ans = input("r to redo, enter to accept? ")
   else:
      ans = ''
   if len(ans) > 0 and ans[0] == 'r':
      peak_fit_query = 1
      return Fit1(row, col)
   elif len(ans) > 0 and ans[0] == 'p':
      gROOT.FindObject("c1").Print("fitpeaks_{0}_{1}.png".format(row,col))
   else:
      peak_fit_query = 0

   gain_pF = slope * fit_slope_to_gain_pF
   latest_results[(row,col)] = "{0} {1}".format(Vbd, gain_pF)
   return graph, gasym, gline

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

def Linearfit(var, par):
   """
   Linear fit function to apply to graphs of single-pixel
   pulse height maximum versus bias voltage. 
   """
   V = var[0]
   V0 = par[0]
   slope = par[1]
   return slope * (V - V0)

def GetPeak(h):
   """
   Find the x value of the maximum of the primary peak in histogram h
   """
   #h.Rebin(4)
   maximum = h.GetBinCenter( h.GetMaximumBin() )
   if h.GetEntries() < 1:
      return 0

   try:
      ptr = h.Fit("gaus", "sqr", "", maximum * 0.7, maximum * 1.3)
      sigma = ptr.Parameters()[0]
      mean = ptr.Parameters()[1]
   except:
      mean = -1
      sigma = -1
   #if (sigma > 6):
   #    mean = -1
   if peak_fit_query:
      h.Draw()
      gROOT.FindObject("c1").Update()
      ans = input("x to reject, enter to accept? ")
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

def GetVoltage(g, row, col, conf=conffile):
   """
   Compute the Vbias voltage that would be applied to the SiPM
   that reads out fiber row,col if it is set to gain g, using the
   calibration contained in setVbias.conf file conf.
   """
   conf_file = open(conf, 'r')
   for line in conf_file:
      sline = line.strip().split()
      if not sline[0][0].isdigit():
         continue
      if int(sline[2]) == col and int(sline[3]) == row:
         thresh = float(sline[4])
         gain = float(sline[5])

   voltage = thresh + (g / gain)

   conf_file.close()
   return float(voltage)

def Draw_gvsV(row, col, conf=0):
   """
   Draw the linear function g(V) as an overlay on the graph
   presently displayed on c1.
   """
   gline = TF1("gline", Linearfit, 50, 100, 2)
   if conf == 0 and (row,col) in latest_results:
      Vbd = float(latest_results[(row,col)].split()[0])
      slope = float(latest_results[(row,col)].split()[1])
   elif conf == 0:
      Vbd = GetVoltage(0, row, col, conffile)
      slope = 1 / (GetVoltage(1, row, col, conf) - Vbd)
   else:
      Vbd = GetVoltage(0, row, col, conf)
      slope = 1 / (GetVoltage(1, row, col, conf) - Vbd)
   gline.SetParameter(0, Vbd)
   gline.SetParameter(1, slope / fit_slope_to_gain_pF)
   gline.SetLineColor(kBlue)
   gline.SetLineStyle(9)
   gline.Draw("same")
   gROOT.FindObject("c1").Update()
   return gline

def Write():
   """
   Write new results to a file in the standard format of setVbias.conf
   using the prior conf file as a source of the light yield constants,
   since these cannot be evaluated based on dark count data.
   """
   outfile = open('fitpeaks.txt', 'w')
   conf_file = open(conffile, 'r')
   for line in conf_file:
      sline = line.strip().split()
      if not sline[0][0].isdigit():
         outfile.write(line)
         continue
      (geo, cha, col, row, Vbd, gpF, ypi) = sline
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

def trees2spectra(ig=-1, row=-1, nfadcbins=300, maxfadc=300):
   """
   Read fadc tree data from a TAGMtrees_<run>.root produced by the
   TAGM_tree plugin and fill histograms h_spectra_<col> for each sum
   column, write out the histograms into file TAGMbias_<run>.root as
   if the TAGM_bias plugin had produced them. If ig=0, run over all
   gain values for the given rows. If row=0, run over all rows as well.
   """
   if ig < 0:
      igrange = [0,3]
   else:
      igrange = [ig, ig+1]
   if row < 0:
      rowrange = [1, 6]
   else:
      rowrange = [row, row+1]
   for ig in range(igrange[0], igrange[1]):
      for row in range(rowrange[0], rowrange[1]):
         ftrees = "TAGMtrees_{0}.root".format(gset[ig][row-1])
         fin = TFile(ftrees)
         fadc = fin.Get("fadc")
         fbias = "TAGMbias_{0}.root".format(gset[ig][row-1])
         fout = TFile(fbias, "create")
         h2d = TH2D("h_spectra", "fadc vs column", nfadcbins, 0, maxfadc,
                                                   102, 1, 103)
         fadc.Draw("col:peak-ped/4>>h_spectra", "pt>300&&qf==0&&row==0")
         for col in range(1,103):
            hin = h2d.ProjectionX("h_spectra_" + str(col), col, col)
            hin.SetTitle("row 0 column " + str(col))
            hin.GetXaxis().SetTitle("fadc peak minus pedestal")
            hin.GetYaxis().SetTitle("counts")
            hin.Draw()
            gROOT.FindObject("c1").SetLogy()
            gROOT.FindObject("c1").Update()
            hin.Write()
            print(hin)
