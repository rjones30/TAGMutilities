#!/usr/bin/env python3

import ROOT
import random
import numpy as np

fin = ROOT.TFile("TAGMtrees_120253.root")

try:
   fsaved = open("fadc250_time_calib.root")
   fsaved = ROOT.TFile("fadc250_time_calib.root")
   hitrate_col = fsaved.Get("hitrate_col")
   hitrate_row = fsaved.Get("hitrate_row")
   deltatr_col = fsaved.Get("deltatr_col")
   deltatr_row = fsaved.Get("deltatr_row")
   deltatn_col = fsaved.Get("deltatn_col")
   deltatn_row = fsaved.Get("deltatn_row")
   deltatf_col = fsaved.Get("deltatf_col")
   deltatf_row = fsaved.Get("deltatf_row")
   deltati_row = fsaved.Get("deltati_row")
except:
   fadc = fin.Get("fadc")
   fadc.Process("fadc250_time_calib.C++")
   hitrate_col = ROOT.gROOT.FindObject("hitrate_col")
   hitrate_row = ROOT.gROOT.FindObject("hitrate_row")
   hittime_col = ROOT.gROOT.FindObject("hittime_col")
   hittime_row = ROOT.gROOT.FindObject("hittime_row")
   deltatr_col = ROOT.gROOT.FindObject("deltatr_col")
   deltatr_row = ROOT.gROOT.FindObject("deltatr_row")
   deltatn_col = ROOT.gROOT.FindObject("deltatn_col")
   deltatn_row = ROOT.gROOT.FindObject("deltatn_row")
   deltatf_col = ROOT.gROOT.FindObject("deltatf_col")
   deltatf_row = ROOT.gROOT.FindObject("deltatf_row")
   deltati_row = ROOT.gROOT.FindObject("deltati_row")
   fsaved = ROOT.TFile("fadc250_time_calib.root", "create")
   hitrate_col.Write()
   hitrate_row.Write()
   deltatr_col.Write()
   deltatr_row.Write()
   deltatn_col.Write()
   deltatn_row.Write()
   deltatf_col.Write()
   deltatf_row.Write()
   deltati_row.Write()

def fittimerf(var, par):
   """
   Fit a picket fence time-tRF plot with a sum of gaussians
   with the following free fit parameters:
      par[0] = peak offset (ns) in range [0, period)
      par[1] = peak period (ns)
      par[2] = height of peaks
      par[3] = sigma of peaks
      par[4] = constant baseline
   """
   global niter
   try:
      niter += 1
   except:
      niter = 1
   n0 = round((var[0] - par[0]) / par[1])
   x = np.arange(var[0] - par[0] - (n0 + 2) * par[1], 
                 var[0] - par[0] - (n0 - 3) * par[1], par[1])
   res = par[2] * np.sum(np.exp(-0.5 * (x / par[3])**2)) + par[4]
   return res

def find_time_offsets():
   """
   Fit the deltatr_col and deltatr_row picket-fence time distributions
   and extract the time offsets for each channel, together with the
   period and sigma of the peaks. Results are saved to a text file.
   """
   ffit = ROOT.TF1("ffit", fittimerf, 25, 215, 5)
   toffset = [[0] * 6 for i in range(103)]
   tperiod = [[0] * 6 for i in range(103)]
   tsigma = [[0] * 6 for i in range(103)]
   for icol in [0,1,3,4]:
      for row in range(1,6):
         irow = row + icol * 10
         col = [9, 27, 0, 81, 99][icol]
         hi = deltatr_row.ProjectionY(f"hi{irow}", irow+1, irow+1)
         hi.SetTitle(f"tADC - tRF for row,column {row},{col}")
         ffit.SetParameter(0, 0.1)
         ffit.SetParameter(1, 4)
         ffit.SetParameter(2, hi.GetMaximum())
         ffit.SetParameter(3, 0.4)
         ffit.SetParameter(4, hi.GetMaximum() / 5)
         print(f"fitting col,row {col},{row}:")
         res = hi.Fit(ffit, "s", "", 25, 215)
         while res != 0 or abs(res.Parameter(1) - 4.007) > 0.005\
                        or res.Parameter(0) < -2.1 or res.Parameter(0) > 2.1\
                        or res.Parameter(3) < 0 or res.Parameter(3) > 0.6:
            print("error from fit, trying again...")
            ffit.SetParameter(0, random.uniform(-2,2))
            ffit.SetParameter(1, 4 + 1e-4 * random.uniform(-1,1))
            ffit.SetParameter(2, hi.GetMaximum() * random.uniform(0,1))
            ffit.SetParameter(3, 0.5 * random.uniform(0,1))
            ffit.SetParameter(4, hi.GetMaximum() * 0.2 * random.uniform(0,1))
            res = hi.Fit(ffit, "s", "", 25, 215)
         hi.GetXaxis().SetRangeUser(25, 215)
         hi.Draw()
         ROOT.gROOT.FindObject("c1").Update()
         toffset[col][row] = res.Parameter(0)
         tperiod[col][row] = res.Parameter(1)
         tsigma[col][row] = res.Parameter(3)
   for col in range(1,103):
      hs = deltatr_col.ProjectionY(f"hs{col}", col, col)
      hs.SetTitle(f"tADC - tRF for sum column {col}")
      print("number of bins in projection is", hs.GetNbinsX())
      ffit.SetParameter(0, 0.1)
      ffit.SetParameter(1, 4)
      ffit.SetParameter(2, hs.GetMaximum())
      ffit.SetParameter(3, 0.4)
      ffit.SetParameter(4, hs.GetMaximum() / 5)
      print(f"fitting column {col}:")
      res = hs.Fit(ffit, "s", "", 25, 215)
      while res != 0 or abs(res.Parameter(1) - 4.007) > 0.005\
                     or res.Parameter(0) < -2.1 or res.Parameter(0) > 2.1\
                     or res.Parameter(3) < 0 or res.Parameter(3) > 0.6:
         print("error from fit, trying again...")
         ffit.SetParameter(0, random.uniform(-2,2))
         ffit.SetParameter(1, 4 + 1e-4 * random.uniform(-1,1))
         ffit.SetParameter(2, hs.GetMaximum() * random.uniform(0,1))
         ffit.SetParameter(3, 0.5 * random.uniform(0,1))
         ffit.SetParameter(4, hs.GetMaximum() * 0.2 * random.uniform(0,1))
         res = hs.Fit(ffit, "s", "", 25, 215)
      hs.GetXaxis().SetRangeUser(25, 215)
      hs.Draw()
      ROOT.gROOT.FindObject("c1").Update()
      toffset[col][0] = res.Parameter(0)
      tperiod[col][0] = res.Parameter(1)
      tsigma[col][0] = res.Parameter(3)
   foutname = "fadc250_time_calib.out"
   fout = open(foutname, "w")
   for row in range(6):
      for col in range(1,103):
         if tperiod[col][row] > 0:
            fout.write(f"{col} {row} " +
                       f"{toffset[col][row]} " +
                       f"{tperiod[col][row]} " +
                       f"{tsigma[col][row]}\n")
   print(f"fit results saved to {foutname}")

def fix_4ns_shifts(infile="fadc250_time_calib.conf",
                   outfile="fadc250_time_calib.out"):
   """
   Go through the nearest-neighbor time difference histograms and find
   all of the places where 4ns jumps appear between columns, then make
   adjustments to the time offsets in infile to take them out. Updated
   time calibration constants are written to outfile. In the case of the
   individual fiber channels, comparison is made to the corresponding
   sum channel to bring them into line with the sums.
   """
   shifts = [[0] * 6 for col in range(103)]
   shift = 0
   for col in range(1,103):
      hc = deltatn_col.ProjectionY("hc", col, col)
      tmax = hc.GetXaxis().GetBinCenter(hc.GetMaximumBin())
      shifts[col][0] = shift
      shift += round(tmax / 4)
      print(f"column {col} has shift {shifts[col][0]}")
   for icol in range(4):
      col = (9, 27, 81, 99)[icol]
      for row in range(1,6):
         irow = (1, 11, 31, 41)[icol] + row
         hr = deltati_row.ProjectionY("hr", irow, irow)
         tmax = hr.GetXaxis().GetBinCenter(hr.GetMaximumBin())
         shifts[col][row] = round(tmax / 4) + shifts[col][0]
         print(f"col,row {col},{row} has shift {shifts[col][row]}")
   fout = open(outfile, "w")
   for line in open(infile):
      lines = line.rstrip().split()
      col, row = [int(s) for s in lines[:2]]
      calib = [float(s) for s in lines[2:]]
      calib[0] += shifts[col][row] * calib[1]
      fout.write(f"{col} {row} {calib[0]} {calib[1]} {calib[2]}\n")

def shared_fraction(col, row):
   """
   Measure the fraction of scintillation light that is seen between adjacent
   columns (row=0) or adjacent rows in a single column (row>0) based on 
   pulse time coincidences seen in the fadc250. Special cases for negative
   arguments are also supported:
      col>0,row<0 : fraction of hits in col,|row| that are also coincident
                    with a hit in the summed column col
      col<0,row=0 : fraction of hits in summed column |col| that are also
                    coincidence with one of the individual rows in |col|
   """
   if row == 0 and col in range(1,103):
      hnear = deltatn_col.ProjectionY("hnear", col, col)
      hfar = deltatf_col.ProjectionY("hfar", col, col)
      hall = deltatr_col.ProjectionY("hall", col, col)
      iplus2ns = hnear.GetXaxis().FindBin(2)
      iminus2ns = hnear.GetXaxis().FindBin(-2)
      iplus200ns = hnear.GetXaxis().FindBin(220)
      iminus200ns = hnear.GetXaxis().FindBin(20)
      near_coin = hnear.Integral(iminus2ns, iplus2ns)
      far_coin = hfar.Integral(iminus2ns, iplus2ns)
      all_coin = hall.Integral(iminus2ns, iplus2ns)
      near_sum = hnear.Integral()
      far_sum = hfar.Integral()
      all_sum = hall.Integral(iminus200ns, iplus200ns)
      normfar = (near_sum - near_coin) / (far_sum - far_coin)
      hfar.Scale(normfar)
      hnear.Draw()
      hfar.SetLineColor(ROOT.kRed)
      hfar.Draw("same")
      shared_fraction = (near_coin - far_coin * normfar) / all_sum
   elif row in range(1,5) and col in range(1,103):
      irow = {9: 1, 27: 11, 81: 31, 99: 41}[col] + row
      hnear = deltatn_row.ProjectionY("hnear", irow, irow)
      hfar = deltatf_row.ProjectionY("hfar", irow, irow)
      hall = deltatr_row.ProjectionY("hall", irow, irow)
      iplus2ns = hnear.GetXaxis().FindBin(2)
      iminus2ns = hnear.GetXaxis().FindBin(-2)
      iplus200ns = hnear.GetXaxis().FindBin(220)
      iminus200ns = hnear.GetXaxis().FindBin(20)
      near_coin = hnear.Integral(iminus2ns, iplus2ns)
      far_coin = hfar.Integral(iminus2ns, iplus2ns)
      all_coin = hall.Integral(iminus2ns, iplus2ns)
      near_sum = hnear.Integral()
      far_sum = hfar.Integral()
      all_sum = hall.Integral(iminus200ns, iplus200ns)
      normfar = (near_sum - near_coin) / (far_sum - far_coin)
      hfar.Scale(normfar)
      hnear.Draw()
      hfar.SetLineColor(ROOT.kRed)
      hfar.Draw("same")
      shared_fraction = (near_coin - far_coin * normfar) / all_sum
   elif -row in range(1,6) and col in range(1,103):
      irow = {9: 1, 27: 11, 81: 31, 99: 41}[col] - row
      hnear = deltati_row.ProjectionY("hnear", irow, irow)
      hfar = deltatf_row.ProjectionY("hfar", irow, irow)
      hall = deltatr_row.ProjectionY("hall", irow, irow)
      iplus2ns = hnear.GetXaxis().FindBin(2)
      iminus2ns = hnear.GetXaxis().FindBin(-2)
      iplus200ns = hall.GetXaxis().FindBin(220)
      iminus200ns = hall.GetXaxis().FindBin(20)
      near_coin = hnear.Integral(iminus2ns, iplus2ns)
      far_coin = hfar.Integral(iminus2ns, iplus2ns)
      all_coin = hall.Integral(iminus2ns, iplus2ns)
      near_sum = hnear.Integral()
      far_sum = hfar.Integral()
      all_sum = hall.Integral(iminus200ns, iplus200ns)
      normfar = (near_sum - near_coin) / (far_sum - far_coin)
      hfar.Scale(normfar)
      hnear.Draw()
      hfar.SetLineColor(ROOT.kRed)
      hfar.Draw("same")
      shared_fraction = (near_coin - far_coin * normfar) / all_sum
   elif row == 0 and -col in (9, 27, 81, 99):
      irow = {9: 1, 27: 11, 81: 31, 99: 41}[-col]
      hnear = deltati_row.ProjectionY("hnear", irow+1, irow+5)
      hfar = deltatf_row.ProjectionY("hfar", irow+1, irow+5)
      hall = deltatr_col.ProjectionY("hall", -col, -col)
      iplus2ns = hnear.GetXaxis().FindBin(2)
      iminus2ns = hnear.GetXaxis().FindBin(-2)
      iplus200ns = hall.GetXaxis().FindBin(220)
      iminus200ns = hall.GetXaxis().FindBin(20)
      near_coin = hnear.Integral(iminus2ns, iplus2ns)
      far_coin = hfar.Integral(iminus2ns, iplus2ns)
      all_coin = hall.Integral(iminus2ns, iplus2ns)
      near_sum = hnear.Integral()
      far_sum = hfar.Integral()
      all_sum = hall.Integral(iminus200ns, iplus200ns)
      normfar = (near_sum - near_coin) / (far_sum - far_coin)
      hfar.Scale(normfar)
      hnear.Draw()
      hfar.SetLineColor(ROOT.kRed)
      hfar.Draw("same")
      shared_fraction = (near_coin - far_coin * normfar) / all_sum
   else:
      print(f"error - invalid row,col = {row},{col}")
      shared_fraction = 0
   print(f"{row} {col} {shared_fraction}")
   return shared_fraction

def plot_shared_fraction():
   """
   Go through all of the sum columns and make a plot of the shared light
   fraction. Repeat for the individual fiber rows.
   """
   hsharec = ROOT.TH1D("hsharec", "shared light fraction between columns",
                       102, 1, 103)
   hsharec.GetXaxis().SetTitle("column")
   hsharec.GetYaxis().SetTitle("shared light fraction")
   hsharer = ROOT.TH1D("hsharer", "shared light fraction between rows",
                       51, 0, 50)
   hsharer.GetXaxis().SetTitle("row (with offset)")
   hsharer.GetYaxis().SetTitle("shared light fraction")
   hsharerc = ROOT.TH1D("hsharerc", "fraction of row in its column sum",
                         51, 0, 50)
   hsharerc.GetXaxis().SetTitle("row (with offset)")
   hsharerc.GetYaxis().SetTitle("common hit fraction")
   hsharecr = ROOT.TH1D("hsharecr", "fraction of column sum in its rows",
                        51, 0, 50)
   hsharecr.GetXaxis().SetTitle("row (with offset)")
   hsharecr.GetYaxis().SetTitle("common hit fraction")
   for col in range(1,103):
      hsharec.Fill(col, shared_fraction(col, 0))
   for icol in range(4):
      col = (9, 27, 81, 99)[icol]
      for row in range(1,6):
         irow = (1, 11, 31, 41)[icol] + row
         hsharer.Fill(irow, shared_fraction(col, row))
         hsharerc.Fill(irow, shared_fraction(col, -row))
         hsharecr.Fill(irow, shared_fraction(-col, 0))
   for i in range(1,103):
      if hsharec.GetBinContent(i) > 0:
         hsharec.SetBinError(i, 2e-3)
   for i in range(1,51):
      if hsharer.GetBinContent(i) > 0:
         hsharer.SetBinError(i, 2e-3)
      if hsharerc.GetBinContent(i) > 0:
         hsharerc.SetBinError(i, 0.01)
      if hsharecr.GetBinContent(i) > 0:
         hsharecr.SetBinError(i, 0.01)
   return hsharec, hsharer, hsharerc, hsharecr
