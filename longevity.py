#!/usr/bin/env python3
#
# longevity.py -- set of macros to plot data that explore the aging
#                 of the tagger microscope detector and readout electronics.
#
# author: richard.t.jones at uconn.edu
# version: january 22, 2022

import ROOT
import fityields

runrange = {20000: "4-21-2016",
            30000: "2-23-2017",
            40000: "12-5-2017",
            50000: "9-29-2018",
            60000: "2-9-2019",
            70000: "12-9-2019",
            80000: "9-23-2021",
           }

setVbias = {}
globhists = {}

def read_setVbias(run):
   """
   Fetch setVbias.conf calibration data from disk and store in the
   internal hash setVbias.
   """
   setVbias.clear()
   fityields.loadVbias("setVbias_fulldetector-" +
                       runrange[run] + ".conf")
   for row in range(1,6):
      for col in range(1,103):
         name = "Gr{0}c{1}".format(row,col)
         title = "TAGM gain vs run number, row={0}, col={1}".format(row,col)
         if not name in globhists:
            globhists[name] = ROOT.TH1D(name, title, 10, 0, 100000)
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM gain (pF / V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         g = fityields.setVbias_gain[row][col]
         globhists[name].Fill(run, g)
         globhists[name].SetBinError(globhists[name].FindBin(run), g/20.)

         name = "Gc{0}".format(col)
         title = "TAGM gain vs run number, row=all, col={0}".format(col)
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM gain (pF / V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         globhists[name].Fill(run, g)

         name = "Gc1-42"
         title = "TAGM gain vs run number, row=all, col=1-42"
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM gain (pF / V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         if col <= 42:
            globhists[name].Fill(run, g)

         name = "Gc43-102"
         title = "TAGM gain vs run number, row=all, col=43-102"
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM gain (pF / V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         if col > 42:
            globhists[name].Fill(run, g)

         name = "Yr{0}c{1}".format(row,col)
         title = "TAGM yield vs run number, row={0}, col={1}".format(row,col)
         if not name in globhists:
            globhists[name] = ROOT.TH1D(name, title, 10, 0, 100000)
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM yield (pix/V/tag)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         y = fityields.setVbias_yield[row][col]
         globhists[name].Fill(run, y)
         globhists[name].SetBinError(globhists[name].FindBin(run), y/20.)

         name = "Yc{0}".format(col)
         title = "TAGM yield vs run number, all rows, col={0}".format(col)
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1000, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM yield (pix/V/tag)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         globhists[name].Fill(run, y)

         name = "Yc1-42"
         title = "TAGM yield vs run number, all rows, col=1-42"
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1000, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM yield (pix/V/tag)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         if col <= 42:
            globhists[name].Fill(run, y)

         name = "Yc43-102"
         title = "TAGM yield vs run number, all rows, col=43-102"
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1000, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM yield (pix/V/tag)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         if col > 42:
            globhists[name].Fill(run, y)

         name = "Vbr{0}c{1}".format(row,col)
         title = "TAGM Vbreakdown vs run number, row={0}, col={1}".format(row,col)
         if not name in globhists:
            globhists[name] = ROOT.TH1D(name, title, 10, 0, 100000)
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM Vbreakdown (V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         V = fityields.setVbias_threshold[row][col]
         globhists[name].Fill(run, V)
         globhists[name].SetBinError(globhists[name].FindBin(run), V/20.)

         name = "Vbc{0}".format(col)
         title = "TAGM Vbreakdown vs run number, all rows, col={0}".format(col)
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1000, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM Vbreakdown (V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         globhists[name].Fill(run, V)

         name = "Vbc1-42"
         title = "TAGM Vbreakdown vs run number, all rows, col=1-42"
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1000, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM Vbreakdown (V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         if col <= 42 and V > 65:
            globhists[name].Fill(run, V)

         name = "Vbc43-102"
         title = "TAGM Vbreakdown vs run number, all rows, col=43-102"
         if not name in globhists:
            globhists[name] = ROOT.TProfile(name, title, 10, 0, 100000,
                                                             0, 1000, 's')
            globhists[name].GetXaxis().SetTitle("run number")
            globhists[name].GetYaxis().SetTitle("SiPM Vbreakdown (V)")
            globhists[name].SetStats(0)
            globhists[name].Sumw2()
         if col > 42 and V > 65:
            globhists[name].Fill(run, V)
   return globhists

def read_all_setVbias():
   hlist = []
   for run in runrange.keys():
      hlist.append(read_setVbias(run))
   return hlist
