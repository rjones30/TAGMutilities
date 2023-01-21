#!/usr/bin/env python3
#
# darkrate.py - python module to analyze and display dark pulse
#               rates measured using fadc250 threshold scans.
#
# author: richard.t.jones at uconn.edu
# version: february 23, 2022

import ROOT
import fityields
import faScalerRates
import numpy as np

scansets = {40000: "scans-1-16-2018/r{0}g{1}.out",
            50000: "scans-9-23-2018/row{0}g{1}.log",
            60000: "scans-2-9-2019/row{0}g{1}.log",
            90000: "scans-2-23-2022/row{0}g{1}.log",
           }

setVbias_conf = {40000: "setVbias_fulldetector-1-11-2018.conf",
                 50000: "setVbias_fulldetector-8-22-2018.conf",
                 60000: "setVbias_fulldetector-1-22-2019.conf",
                 90000: "setVbias_fulldetector-12-9-2019_calib.conf",
                }

gains = [25, 35, 45]
rows = [1, 2, 3, 4, 5]
runs = [40000, 50000, 60000, 90000]

threshold = 110  # fadc250 counts

def histrate(run, row, col, tV=threshold, prof=0):
   fityields.loadVbias(setVbias_conf[run])
   pointV = []
   pointR = []
   for g in gains:
      deltaV = g / (100 * fityields.setVbias_gain[row][col])
      h2 = faScalerRates.hscan(scansets[run].format(row, g))
      h1 = h2.ProjectionY("py", col, col)
      rate = h1.GetBinContent(h1.FindBin(tV))
      pointV.append(deltaV)
      pointR.append(rate)
      if prof:
         prof.Fill(deltaV, rate)
   g = ROOT.TGraph(len(pointV), np.array(pointV, dtype=float),
                                np.array(pointR, dtype=float))
   name = "h{0}r{1}c{2}".format(run, row, col)
   title = "dark rate for run {0}, row {1}, col {2}".format(run, row, col)
   h = ROOT.TH1D(name, title, 10, 0, 3)
   h.GetXaxis().SetTitle("Vbias over threshold (V)")
   h.GetYaxis().SetTitle("dark pixel rate (Hz)")
   h.SetStats(0)
   h.SetMinimum(0)
   h.SetMaximum(max(pointR) * 1.5)
   h.Draw()
   g.Draw("same")
   ROOT.gROOT.FindObject("c1").Update()
   return g,h

def histrates(run, tV=threshold, color=1):
   name = "h{0}".format(run)
   title = "dark rates for run {0}".format(run)
   prof = ROOT.TProfile(name, title, 100, 0, 3, 1e3, 1e8)
   prof.GetXaxis().SetTitle("Vbias over threshold (V)")
   prof.GetYaxis().SetTitle("dark pixel rate (Hz)")
   prof.SetStats(0)
   for row in range(1,6):
      for col in range(1,103):
         histrate(run, row, col, tV, prof=prof)
   return prof
