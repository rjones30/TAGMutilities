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
import ROOT

# Enforce serial operation of the fit engine, avoids segfaults!!
ROOT.EnableImplicitMT(1)

from array import array
import numpy
import time
import random

import ctypes
Double = ctypes.c_double

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

# dark pulse runs taken on March 8, 2025
gval = [0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['000124', '000129', '000134', '000139', '000145'],
        ['000125', '000130', '000135', '000140', '000146'],
        ['000126', '000131', '000136', '000141', '000147'],
        ['000127', '000132', '000137', '000143', '000148'],
        ['000128', '000133', '000138', '000144', '000149']]
conffile = 'setVbias_fulldetector-1-8-2023.conf'

# dark pulse runs taken on March 12, 2025
gval = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
gset = [['000213', '000219', '000224', '000229', '000234'],
        ['000214', '000220', '000225', '000230', '000235'],
        ['000215', '000221', '000226', '000231', '000236'],
        ['000217', '000222', '000227', '000232', '000237'],
        ['000218', '000223', '000228', '000233', '000238'],
        ['000239', '000244', '000250', '000259', '000270'],
        ['000240', '000245', '000251', '000262', '000271'],
        ['000241', '000246', '000253', '000264', '000273'],
        ['000242', '000247', '000255', '000266', '000274'],
        ['000243', '000248', '000257', '000268', '000276']]
conffile = 'setVbias_fulldetector-3-12-2025_calib.conf'

# light pulse runs taken on April 10, 2025 [rtj]
gval = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
gset = [['130780', '130787', '130792', '130797', '130803'],
        ['130781', '130788', '130793', '130798', '130804'],
        ['130784', '130789', '130794', '130799', '130805'],
        ['130785', '130790', '130795', '130801', '130806'],
        ['130786', '130791', '130796', '130802', '130808'],
        ['130809', '130812', '130814', '130816', '130818'],
        ['130811', '130813', '130815', '130817', '130819'],
        ['130822', '130823', '130824', '130825', '130826']]
conffile = 'setVbias_fulldetector-4-6-2025_calib.conf'

# dark pulse runs taken on April 16, 2026 [ma,rtj]
gval = [0.30, 0.40, 0.50, 0.60, 0.70]
gset = [['000328', '000332', '000336', '000340', '000344'],
        ['000356', '000358', '000360', '000363', '000365'],
        ['000329', '000333', '000337', '000341', '000345'],
        ['000357', '000359', '000361', '000364', '000366'],
        ['000330', '000334', '000338', '000342', '000346']]
gset_proto = {106: ['130372', '130373', '130374', '130375', '130376'],
              107: ['130377', '130378', '130379', '130380', '130381'],
              108: ['130382', '130383', '130384', '130385', '130386']}
proto_to_colrow = {(103,1):(99,1), (103,2):(99,1), (103,3):(99,1), (103,4):(99,1), (103,5):(99,1), 
                   (104,1):(99,2), (104,2):(99,2), (104,3):(99,2), (104,4):(99,2), (104,5):(99,2),
                   (105,1):(99,3), (105,2):(99,3), (105,3):(99,3), (105,4):(99,3), (105,5):(99,3),
                   (106,11):(99,4), (107,11):(99,4), (108,11):(99,4), (109,11):(99,4), (110,11):(99,4),
                   (106,10):(99,5), (107,10):(99,5), (108,10):(99,5), (109,10):(99,5), (110,10):(99,5),
                   (108,1):(81,1), (108,2):(81,1), (108,3):(81,1), (108,4):(81,1), (108,5):(81,1),
                  }
conffile = 'setVbias_fulldetector-3-20-2026_calib.conf'

# light pulse runs taken on May 2, 2026 [rtj]
"""
gval = [0.25, 0.35, 0.45, 0.55, 0.65]
gset = [['140213', '140219', '140224', '140231', '140238'],
        ['140214', '140220', '140226', '140232', '140239'],
        ['140215', '140221', '140227', '140233', '140240'],
        ['140216', '140222', '140229', '140234', '140242'],
        ['140217', '140223', '140230', '140235', '140243']]
gset_proto = {106: ['140248', '140249', '140252', '140253', '140254'],
              107: ['140255', '140256', '140257', '140258', '140259'],
              108: ['140260', '140261', '140262', '140263', '140264']}
proto_to_colrow = {(103,1):(99,1), (103,2):(99,1), (103,3):(99,1), (103,4):(99,1), (103,5):(99,1), 
                   (104,1):(99,2), (104,2):(99,2), (104,3):(99,2), (104,4):(99,2), (104,5):(99,2),
                   (105,1):(99,3), (105,2):(99,3), (105,3):(99,3), (105,4):(99,3), (105,5):(99,3),
                   (106,11):(99,4), (107,11):(99,4), (108,11):(99,4), (109,11):(99,4), (110,11):(99,4),
                   (106,10):(99,5), (107,10):(99,5), (108,10):(99,5), (109,10):(99,5), (110,10):(99,5),
                   (108,1):(81,1), (108,2):(81,1), (108,3):(81,1), (108,4):(81,1), (108,5):(81,1),
                  }
conffile = 'setVbias_fulldetector-4-27-2026_calib.conf'
"""

confref = conffile

peak_fit_query = False

latest_results = {}


def Fit1(row, col, interact=1):
   """
   Fit a the single-pixel dark pulse spectra for a single fiber and
   save a new set of calibration constants in an in-memory array.
   """
   graph = ROOT.TGraphErrors(len(gset))
   p = [0] * len(gset)
   V = [0] * len(gset)
   for ig in range(len(gset)):
      if col < 103:
         rowno = 0
         colno = col
         runno = gset[ig][row-1]
      elif col in gset_proto and row > 5:
         rowno = proto_to_colrow[(col,row)][1]
         colno = proto_to_colrow[(col,row)][0]
         runno = gset_proto[col][ig]
      else:
         rowno = proto_to_colrow[(col,row)][1]
         colno = proto_to_colrow[(col,row)][0]
         runno = gset[ig][row-1]
      fbias = f"TAGMbias_{runno}.root"
      if os.path.exists(fbias):
         fin = ROOT.TFile(fbias)
         hin = fin.Get(f"h_spectra_{col}")
      else:
         ftrees = f"TAGMtrees_{runno}.root"
         fin = ROOT.TFile(ftrees)
         hin = ROOT.TH1D(f"h_spectra_{col}", 
                    f"fadc spectrum for column {col}, row {row}, g={gval[ig]}",
                    300, 0, 300)
         fadc = fin.Get("fadc")
         pedestal = 100.0
         #fadc.Draw("peak-ped/4>>h_spectra_" + str(col),
         fadc.Draw(f"peak-{pedestal}>>h_spectra_" + str(col),
                   f"pt>300&&qf==0&&row=={rowno}&&col=={colno}")
      if hin.GetEntries() < 100:
         print("no entries")
         return None
      print(hin)

      # Check for bad electronic channels
      # if GetNumberPeaks(h25) < 2: continue
      # if GetNumberPeaks(h35) < 2: continue
      # if GetNumberPeaks(h45) < 2: continue
      # Add some kind of error recording

      # Get peaks from each histogram
      p[ig] = GetPeak2(hin)
      ROOT.gROOT.FindObject("c1").Update()
      #p[ig] = hin.GetMean()
      if p[ig] < 0:
         print('Fit failed for row', row, ' col ', col, end='')
         print(', gain setting', gval[ig], 'entries', hin.GetEntries())
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
         slope = (y1.value - y0.value) / (x1.value - x0.value + 1e-99)
         if slope < 5:
            continue
         yline = y0.value + (x.value - x0.value) * slope
         if y.value > yline * 1.2:
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
   ex = graph.GetErrorX(0)
   ey = graph.GetErrorY(0)
   
   # Fit TGraph
   fit_to_hyperbola = False
   fit_to_thesin = False
   fit_to_theexp = True
   if fit_to_hyperbola:
      fun1 = ROOT.TF1("fun1", Hyperfit, 50, 100, 3)
      global peak_fit_query
      fun1.SetParameter(0, 71.0)
      fun1.SetParameter(1, 15)
      fun1.SetParameter(2, 8)
      fun1.SetParameter(3, 1)
      while True:
         ptr = graph.Fit(fun1, "s")
         if ptr.IsValid():
            break
         fun1.SetParameter(0, 71.0 + random.uniform(-0.5,0.5))
         fun1.SetParameter(1, 15 + random.uniform(-3, 3))
         fun1.SetParameter(2, 7 + random.uniform(-0.5, 0.5))
         fun1.SetParameter(3, 1)
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
      graph.GetXaxis().SetTitle("Vbias (V)")
      graph.GetYaxis().SetTitle("fadc <counts> / pixel")
      graph.Draw("A*")
      xasym = numpy.array([Vref - 2, Vref + 2], dtype=float)
      yasym = numpy.array([gref - 2*slope, gref + 2*slope], dtype=float)
      gasym = ROOT.TGraph(2, xasym, yasym)
      gasym.SetLineColor(ROOT.kRed)
      gasym.SetLineStyle(9)
      gasym.Draw("l")
      gasym.GetYaxis().SetRangeUser(10,40)
      gline = Draw_gvsV(row, col, confref)
      ROOT.gROOT.FindObject("c1").Update()

   elif fit_to_thesin:
      fun1 = ROOT.TF1("fun1", Thesinfit, 50, 100, 4)
      fun1.SetParameter(0, 71.0)
      fun1.SetParameter(1, 15)
      fun1.SetParameter(2, 16)
      fun1.SetParameter(3, 3)
      
      # sculpt the error bars to make the fit behave properly
      graph.SetPointError(iig, ex, ey)
      while True:
         ptr = graph.Fit(fun1, "s")
         if ptr.IsValid():
            break
         fun1.SetParameter(0, 71.0 + 0.3 * random.uniform(-0.5, 0.5))
         fun1.SetParameter(1, 15 + 2 * random.uniform(-0.5, 0.5))
         fun1.SetParameter(2, 16)
         fun1.SetParameter(3, 3)
      V0 = ptr.Parameters()[0]
      G = ptr.Parameters()[1]
      f0 = ptr.Parameters()[2]
      Vs = ptr.Parameters()[3]
      slope = G / (Vs + 1e-99)
      Vbd = V0 - f0 / (slope + 1e-99)
      print(Vbd, slope)
      graph.SetTitle("gain curve for row " + 
                     str(row) + " col " + str(col))
      graph.GetXaxis().SetTitle("Vbias (V)")
      graph.GetYaxis().SetTitle("fadc <counts> / pixel")
      graph.Draw("A*")
      xfit = numpy.array([Vbd, Vbd + 3], dtype=float)
      yfit = numpy.array([0, slope * 3], dtype=float)
      gasym = ROOT.TGraph(2, xfit, yfit)
      gasym.SetLineColor(ROOT.kRed)
      gasym.SetLineStyle(9)
      gasym.Draw("l")
      gasym.GetYaxis().SetRangeUser(10,40)
      gline = Draw_gvsV(row, col, confref)
      ROOT.gROOT.FindObject("c1").Update()

   elif fit_to_theexp:
      fun1 = ROOT.TF1("fun1", Theexp, 50, 100, 4)
      fun1.SetParameter(0, 71.0)
      fun1.SetParameter(1, 15)
      fun1.SetParameter(2, 8)
      fun1.SetParameter(3, 1)

      # sculpt the errors to make the fit behave
      #yerrs = [5, 4, 3, 2, 1, 1, 2, 3, 4, 5]
      yerrs = [1, 1, 1, 1, 1, 2, 2, 3, 4, 5]
      for i in range(len(gval)):
         ex = graph.GetErrorX(0)
         ey = yerrs[i]
         graph.GetPoint(i, x, y)
         if i < 3 and y / gval[i] < 30:
            print(gval[i], y / gval[i])
            ey = 5
         elif i < 3 and y / gval[i] > 70:
            print(gval[i], y / gval[i])
            ey = 3
         elif i < 3:
            xnext = numpy.array([0], dtype=float)
            ynext = numpy.array([0], dtype=float)
            graph.GetPoint(i+1, xnext, ynext)
            if y > ynext:
               ey = 5
         graph.SetPointError(i, ex, ey)
      while True:
         ptr = graph.Fit(fun1, "s")
         if ptr.IsValid():
            break
         fun1.SetParameter(0, 71.0 + random.uniform(-0.5, 0.5))
         fun1.SetParameter(1, 15 + random.uniform(-0.5, 0.5))
         fun1.SetParameter(2, 8 + random.uniform(-0.5, 0.5))
         fun1.SetParameter(3, 1 + random.uniform(-0.1, 0.1))
      V0 = ptr.Parameters()[0]
      G = ptr.Parameters()[1]
      f0 = ptr.Parameters()[2]
      Vs = ptr.Parameters()[3]
      f1 = 30 # fadc pulse height where the single-pixel peak and mean peak vs Vbias curves cross
      dV1 = Vs * numpy.log(1 + (f1 - f0)/G)
      slope = (G / Vs) * numpy.exp(dV1 / Vs)
      Vbd = V0 + dV1 - f1 / slope
      def fadc_at(V):
         return f0 + G * (numpy.exp((V - V0)/Vs) - 1)
      g = 0.40
      V = Vbd + g / fit_slope_to_gain_pF / slope
      print(f"setVbias -g {g} gives Vbias={V:5.2f} and",
            f"yield mean={fadc_at(V)} fadc/photoelectron")
      graph.SetTitle("gain curve for row " + 
                     str(row) + " col " + str(col))
      graph.GetXaxis().SetTitle("Vbias (V)")
      graph.GetYaxis().SetTitle("fadc <counts> / pixel")
      graph.Draw("A*")
      xfit = numpy.array([Vbd, Vbd + 3], dtype=float)
      yfit = numpy.array([0, slope * 3], dtype=float)
      gasym = ROOT.TGraph(2, xfit, yfit)
      gasym.SetLineColor(ROOT.kRed)
      gasym.SetLineStyle(9)
      gasym.Draw("l")
      gasym.GetYaxis().SetRangeUser(10,40)
      gline = Draw_gvsV(row, col, confref)
      ROOT.gROOT.FindObject("c1").Update()

   else:
      print("no gain curve model is active, cannot continue")
      return None

   if interact:
      ans = input("r to redo, enter to accept? ")
   else:
      time.sleep(2)
      ans = ''
   if len(ans) > 0 and ans[0] == 'r':
      peak_fit_query = 1
      return Fit1(row, col)
   elif len(ans) > 0 and ans[0] == 'p':
      ROOT.gROOT.FindObject("c1").Print("fitpeaks_{0}_{1}.png".format(row,col))
   #else:
   #   peak_fit_query = 0

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

def Thesinfit(var, par):
   """
   Theta-sinusoidal fit function to apply to graphs of single-pixel
   pulse height maximum versus bias voltage. 
   """
   V = var[0]
   V0 = par[0]
   slope = par[1]
   f0 = par[2]
   Vs = par[3]
   if V > V0:
      return f0 + slope * numpy.sin((V - V0)/Vs)
   else:
      return f0

def Theexp(var, par):
   """
   Theta-exponential fit function to apply to graphs of single-pixel
   pulse height mean versus bias voltage. 
   """
   V = var[0]
   V0 = par[0]
   G = par[1]
   f0 = par[2]
   Vs = par[3]
   if V > V0 and (V - V0)/Vs < 10:
      return f0 + G * (numpy.exp((V - V0) / Vs) - 1)
   else:
      return f0

def GetPeak_simple(h):
   """
   DEPRECATED -- assumes an isolated single-photoelectron peak
                 undistorted by a threshold cut, not very robust. 
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
      ROOT.gROOT.FindObject("c1").Update()
      ans = input("x to reject, enter to accept? ")
      if len(ans) > 0 and ans[0] == 'x':
         return 0
   return float(mean)

def GetPeak_multiple(h):
   """
   Find the x value of the maximum of the primary peak in histogram h
   """
   if h.GetEntries() < 1:
      return 0

   # Initial guess for primary peak center is the maximum bin iff
   # the maximum is not the first non-zero bin in the spectrum,
   # otherwise find the second maximum and divide by two.
   imax1 = h.GetMaximumBin()
   for i in range(1, h.GetNbinsX()):
      if h.GetBinContent(i) > 0:
         ifirst = i
         break
   for i in range(ifirst + 1, h.GetNbinsX()):
      if h.GetBinContent(i) < h.GetBinContent(i-1):
         imin1 = i
         if h.GetBinContent(i) <= h.GetBinContent(i+1) and \
            h.GetBinContent(i) <= h.GetBinContent(i+2) and \
            h.GetBinContent(i) <= h.GetBinContent(i+3) and \
            h.GetBinContent(i) <= h.GetBinContent(i+4) and \
            h.GetBinContent(i) <= h.GetBinContent(i+5):
            break
   for i in range(imin1 + 1, h.GetNbinsX()):
      if h.GetBinContent(i) > h.GetBinContent(i-1):
         imax1 = i
         if h.GetBinContent(i) >= h.GetBinContent(i-2) and \
            h.GetBinContent(i) >= h.GetBinContent(i+1) and \
            h.GetBinContent(i) >= h.GetBinContent(i+2) and \
            h.GetBinContent(i) >= h.GetBinContent(i+3) and \
            h.GetBinContent(i) >= h.GetBinContent(i+4) and \
            h.GetBinContent(i) >= h.GetBinContent(i+5):
            break
   print("found ifirst,imin1,imax1=",ifirst,imin1,imax1)

   def tf1_multipeak(var, par):
      """
      var = [fadc]
      par = [mean, sigma, height1, height2, ...]
      """
      f = 0
      for ipeak in range(5):
         x = (var[0] - par[0]*(ipeak + 1)) / (par[1] * (ipeak+1)**0.5)
         if abs(x) < 10:
            f += par[ipeak+2]**2 * numpy.exp(-0.5 * x**2)
      return f

   xfirst = h.GetBinLowEdge(imin1)
   fmp = ROOT.TF1("tf1_multipeak", tf1_multipeak, xfirst, 300, 7)
   fmp.SetParameters(imax1, 4,
                     (h.GetBinContent(imax1) + 1)**0.5,
                     (h.GetBinContent(2 * imax1) + 1)**0.5,
                     (h.GetBinContent(3 * imax1) + 1)**0.5,
                     (h.GetBinContent(4 * imax1) + 1)**0.5,
                     (h.GetBinContent(5 * imax1) + 1)**0.5)
   try:
      ptr = h.Fit(fmp, "R")
      mean = fmp.GetParameter(0)
      sigma = fmp.GetParameter(1)
   except:
      mean = -1
      sigma = -1
   print("starting mean was", imax1)
   print("final value of mean is", mean)
   if (sigma > 6):
       mean = -1
   h.GetXaxis().SetTitle("fadc channels")
   h.GetYaxis().SetTitle("counts")
   h.Draw()
   ROOT.gROOT.FindObject("c1").Update()
   if peak_fit_query:
      ans = input("x to reject, enter to accept? ")
      if len(ans) > 0 and ans[0] == 'x':
         return 0
      elif len(ans) > 0:
         return mean / float(ans)
   if imax1 > imin1 + 1:
      return float(mean)
   else:
      return h.GetMean()

def GetPeak2(h):
   """
   Find the x value of the maximum of the primary peak in histogram h.
   This algorithm was developed for the case where the first photoelectron peak
   was being clipped by the fadc250 pulse readout threshold, so only peaks 2...
   could be fitted.
   """
   if h.GetEntries() < 1:
      return 0

   # Initial guess for primary peak center is the maximum bin iff
   # the maximum is not the first non-zero bin in the spectrum,
   # otherwise find the second maximum and divide by two.
   imax1 = h.GetMaximumBin()
   if imax1 > 50:
      imax1 = imax1 // 2
   for i in range(1, h.GetNbinsX()):
      if h.GetBinContent(i) > 0:
         ifirst = i
         break
   for i in range(imax1 + 1, h.GetNbinsX()):
      if h.GetBinContent(i) < h.GetBinContent(i-1):
         imin1 = i
         if h.GetBinContent(i) <= h.GetBinContent(i-2) and \
            h.GetBinContent(i) <= h.GetBinContent(i+1) and \
            h.GetBinContent(i) <= h.GetBinContent(i+2) and \
            h.GetBinContent(i) <= h.GetBinContent(i+3) and \
            h.GetBinContent(i) <= h.GetBinContent(i+4) and \
            h.GetBinContent(i) <= h.GetBinContent(i+5):
            break
   imax2 = imin1
   for i in range(imin1 + 1, h.GetNbinsX()):
      if h.GetBinContent(i) > h.GetBinContent(imax2):
         imax2 = i
   for i in range(imax1, imax2):
      if h.GetBinContent(i) < h.GetBinContent(imin1):
         imin1 = i
   imin1 = min(imin1, (imax1 + imax2) // 2)

   print("found ifirst,imax1,imin1,imax2=",ifirst,imax1,imin1,imax2)

   def tf1_multipeak(var, par):
      """
      var = [fadc]
      par = [mean, sigma, height1, height2, ...]
      """
      f = 0
      for ipeak in range(5):
         x = (var[0] - par[0]*(ipeak + 1)) / (par[1] * (ipeak+1)**0.5)
         if abs(x) < 10:
            f += par[ipeak+2]**2 * numpy.exp(-0.5 * x**2)
      return f

   i1 = imax1 + 4
   xfirst = h.GetBinLowEdge(i1)
   fmp = ROOT.TF1("tf1_multipeak", tf1_multipeak, xfirst, 300, 7)
   fmp.SetParameters(imax1, 4,
                     (h.GetBinContent(imax1) + 1)**0.5,
                     (h.GetBinContent(imax2) + 1)**0.5,
                     (h.GetBinContent(3 * imax1) + 1)**0.5,
                     (h.GetBinContent(4 * imax1) + 1)**0.5,
                     (h.GetBinContent(5 * imax1) + 1)**0.5)

   try:
      ptr = h.Fit(fmp, "R")
      mean = fmp.GetParameter(0)
      sigma = fmp.GetParameter(1)
   except:
      mean = -1
      sigma = -1
   print("starting mean was", imax2 / 2)
   print("final value of mean is", mean)
   #if (sigma > 6):
   #    mean = -1
   h.GetXaxis().SetTitle("fadc channels")
   h.GetYaxis().SetTitle("counts")
   h.Draw()
   ROOT.gROOT.FindObject("c1").Update()
   if peak_fit_query:
      ans = input("x to reject, enter to accept? ")
      if len(ans) > 0 and ans[0] == 'x':
         return 0
      elif len(ans) > 0:
         return mean / float(ans)
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

   try:
      voltage = thresh + (g / gain)
   except:
      print("Error in GetVoltage:", conffile, "does not contain a line for",
            f"row={row}, column={col}")
      voltage = 0

   conf_file.close()
   return float(voltage)

def Draw_gvsV(row, col, conf=0):
   """
   Draw the linear function g(V) as an overlay on the graph
   presently displayed on c1.
   """
   gline = ROOT.TF1("gline", Linearfit, 50, 100, 2)
   if conf == 0 and (row,col) in latest_results:
      Vbd = float(latest_results[(row,col)].split()[0])
      slope = float(latest_results[(row,col)].split()[1])
   elif conf == 0:
      Vbd = GetVoltage(0, row, col, conffile)
      slope = 1 / (GetVoltage(1, row, col, conf) - Vbd)
   else:
      Vbd = GetVoltage(0, row, col, conf)
      slope = 1 / (GetVoltage(1, row, col, conf) - Vbd + 1e-99)
   gline.SetParameter(0, Vbd)
   gline.SetParameter(1, slope / fit_slope_to_gain_pF)
   gline.SetLineColor(ROOT.kBlue)
   gline.SetLineStyle(9)
   gline.Draw("same")
   ROOT.gROOT.FindObject("c1").Update()
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
   if the TAGM_bias plugin had produced them. If ig<0, run over all
   gain values for the given rows. If row<0, run over all rows as well.
   """
   if ig < 0:
      igrange = [0,len(gval)]
   else:
      igrange = [ig, ig+1]
   if row < 0:
      rowrange = [1, 6]
   else:
      rowrange = [row, row+1]
   for ig in range(igrange[0], igrange[1]):
      for row in range(rowrange[0], rowrange[1]):
         ftrees = "TAGMtrees_{0}.root".format(gset[ig][row-1])
         fin = ROOT.TFile(ftrees)
         fadc = fin.Get("fadc")
         fbias = "TAGMbias_{0}.root".format(gset[ig][row-1])
         fout = ROOT.TFile(fbias, "update")
         h2d = ROOT.TH2D("h_spectra", "fadc vs column", 
                         nfadcbins, 0, maxfadc, 110, 1, 111)
         fadc.Draw("col:peak-ped/4>>h_spectra", "pt>300&&qf==0&&row==0")
         h2d = ROOT.TH2D("h_spectra", "fadc vs column", 
                         nfadcbins, 0, maxfadc, 110, 1, 111)
         fadc.Draw("col:peak-ped/4>>h_spectra", "pt>300&&qf==0&&row==0")
         for col in range(1,103):
            hin = h2d.ProjectionX("h_spectra_" + str(col), col, col)
            hin.SetTitle(f"row {row}, column {col}, g={gval[ig]}")
            hin.GetXaxis().SetTitle("fadc peak minus pedestal")
            hin.GetYaxis().SetTitle("counts")
            hin.Draw()
            ROOT.gROOT.FindObject("c1").SetLogy()
            ROOT.gROOT.FindObject("c1").Update()
            hin.Write()
            print(hin)

def trees2spectra_proto(ig=-1, row=-1, nfadcbins=300, maxfadc=300):
   """
   Clone of trees2specta, except that it uses special tables to look
   up the run numbers and readout channels for the test prototypes
   that were installed in the microscope for the 2026 run period.
   """
   if ig < 0:
      igrange = [0,len(gval)]
   else:
      igrange = [ig, ig+1]
   if row < 0:
      rows = [1, 2, 3, 4, 5, 10, 11]
   else:
      rows = [row]
   for ig in range(igrange[0], igrange[1]):
      for row in rows:
         h2d = ROOT.gDirectory.FindObject("h_spectra")
         if h2d:
            h2d.Clear()
         else:
            h2d = ROOT.TH2D("h_spectra", "fadc vs column", 
                            nfadcbins, 0, maxfadc, 110, 1, 111)
         for col in range(103,109):
            if row < 10:
               run = gset[ig][row-1]
            elif col in gset_proto:
               run = gset_proto[col][ig]
            else:
               continue
            ftrees = f"TAGMtrees_{run}.root"
            fin = ROOT.TFile(ftrees)
            fadc = fin.Get("fadc")
            if (col,row) in proto_to_colrow:
               colrow = proto_to_colrow[(col,row)]
               h2d.SetDirectory(ROOT.gDirectory)
               fadc.Draw(f"{col}:peak-ped/4 >> +h_spectra",
                         f"pt>300&&qf==0&&col=={colrow[0]}&&row=={colrow[1]}")
               h2d.SetDirectory(0)
         for col in range(103,109):
            if row < 10:
               run = gset[ig][row-1]
            elif col in gset_proto:
               run = gset_proto[col][ig]
            else:
               continue
            fbias = f"TAGMbias_{run}.root"
            fout = ROOT.TFile(fbias, "update")
            hin = h2d.ProjectionX("h_spectra_" + str(col), col, col)
            hin.SetTitle(f"row {row}, column {col}, g={gval[ig]}")
            hin.GetXaxis().SetTitle("fadc peak minus pedestal")
            hin.GetYaxis().SetTitle("counts")
            hin.Draw()
            ROOT.gROOT.FindObject("c1").SetLogy()
            ROOT.gROOT.FindObject("c1").Update()
            hin.Write()
            print(hin)
            fout.Write()
            fout.Close()
            del fout
