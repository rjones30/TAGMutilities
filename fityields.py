#!/bin/env python
#
# fityields.py - utility functions for reading TAGM pulse height spectra
#                from root trees created using DANA plugin TAGM_trees and
#                fitting them to a parameterized form that extracts the
#                average yield for each column of the microscope.
#
# author: richard.t.jones at uconn.edu
# version: april 1, 2016

from ROOT import *
import numpy
import math
import array
import re

interact = 1

pedestal = 900.
bg_start = 970.
bg_end = 3500.
fit_start = bg_start
fit_end = 8500.;
f_rebin = 1;

# standard values for converting from fADC integral to charge (pC)
# dq = V*dt/R = fADC*(1V/4096)*4ns/50Ohm = fADC*0.01953pC
#fADC_gain = 0.01953 # pC/count

# Empirical value based on pC/adc_peak = 0.011pC/count in makeVbiasconf.py
# which gets multiplied by the ratio of high/low gain on the preamplifiers
# and the empirical ratio adc_peak/adc_pulse_integral = 0.235 measured using
# row-by-row data in runs 40635 on December 19, 2017.
fADC_gain = 0.011 * 18 * 0.235 # pC per adc_pulse_integral
fADC_pedestal = 900

# This is where you need to specify the row-by-row scan runs that are used
# as a basis for the yields calibration. Together with the list of runs and
# -g values for each, you also need to specify the setVbias_conf file that
# was in play when the runs were taken. The gset table needs to have the
# same number of rows as the number of elements in gval, each of which is
# itself a list of 5 run numbers given in the order row=1,2,3,4,5 for which
# row was enabled during the run.

# Row-by-row scan data taken on 12/19/2017 [rtj]
gval = [0.25, 0.45, 0.35]
gset = [['40625', '40626', '40627', '40628', '40629'],
        ['40630', '40633', '40635', '40636', '40637'],
        ['40638', '40639', '40640', '40641', '40642']]
reference_setVbias_conf = "setVbias_fulldetector-12-5-2017.conf"

# Row-by-row scan data taken on 1/15/2018 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['125', '225', '325', '425', '525'],
        ['135', '235', '335', '435', '535'],
        ['145', '245', '345', '445', '545']]
reference_setVbias_conf = "setVbias_fulldetector-1-11-2018.conf"

# Row-by-row scan data taken on 9/23/2018 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['125', '225', '325', '425', '525'],
        ['135', '235', '335', '435', '535'],
        ['145', '245', '345', '445', '545']]
reference_setVbias_conf = "setVbias_fulldetector-8-22-2018.conf"

# These tables are nested dicts [column][run]
peakmean = {}
peaksigma = {}

def fitfunc(var, par):
   """
   User fitting function for defining a TF1,
   describing a gaussian peak over an exponentially
   falling background, with the following values in par:
     par[0] = background exponential curve height at x=xmin
     par[1] = xmin for purposes of background curve
     par[2] = background exponential factor, units of x
     par[3] = height of gaussian peak over background
     par[4] = mean of gaussian peak, units of x
     par[5] = sigma of gaussian peak, units of x
   The gaussian peak has been reparameterized on a log x scale
   so that it more faithfully reproduces the skewed shape
   see in the data.
   """
   if var[0] < pedestal:
      return 0
   elif par[0] < 0 or par[3] < 0:
      return 0
   elif par[4] < pedestal:
      return 0
   elif par[2] <= 10:
      return 0
   elif var[0] < bg_start or var[0] > bg_end:
      bg = 0
   else:
      try:
         bg = math.exp((par[1] - var[0]) / par[2])
      except:
         return 0
   logx = math.log(var[0] - pedestal)
   logmu = math.log(par[4] - pedestal)
   logsigma = math.log(par[4] + abs(par[5]) - pedestal) - logmu
   sig = math.exp(-0.5 * ((logx - logmu) / logsigma)**2)
   return par[0] * bg + par[3] * sig

def fit(run):
   """
   Make individual fiber spectra for each column and fit to
   a gaussian peak on an exponential tail from the pedestal.
   This function loops over all 102 columns in the TAGM and
   displays the fit for each one, then pauses for user input.
   Options for user input are as follows:
    a) <nothing> - accept this fit and continue to the next column
    b) <integer> - accept this fit and continue to column <integer>
    c)  <float>   - retry this fit with bg exponential starting at <float>
    d)     g      - regenerate this spectrum from the tree
    e)     *      - exit the fit loop
   """
   global bg_start
   global bg_end
   f = TFile("TAGMtrees_" + str(run) + ".root", "update")
   fitter = TF1("fitter", fitfunc, fit_start, fit_end, 6)
   fitter0 = TF1("fitter0", fitfunc, fit_start, fit_end, 6)
   fadc = gROOT.FindObject("fadc")
   global c1
   c1 = gROOT.FindObject("c1")
   if c1:
      c1.Delete()
   c1 = TCanvas("c1","c1",0,0,800,400)
   c1.Divide(2)
   c1.cd(1)
   c1_1 = gROOT.FindObject("c1_1")
   c1_1.SetLogy()
   colbase = 1
   h = 0
   global hreb
   for col in range(0, 99999):
      column = col + colbase
      if column > 102:
         break;
      h = gROOT.FindObject("col" + str(column))
      if not h:
         print "no histogram found for column", column, " so regenerating..."
         hpi = TH1D("hpi", "column " + str(column), 480, 0, 8160)
         try:
            fadc.Draw("pi>>hpi", "qf==0&&row==0&&col==" + str(column))
            h = gROOT.FindObject("hpi").Clone("col" + str(column))
         except:
            print "unable to generate histogram for column", column,
            print ", moving on..."
            if not column in peakmean:
               peakmean[column] = {}
               peaksigma[column] = {}
            peakmean[column][run] = 0
            peaksigma[column][run] = 0
            continue
      if not h:
         break
      global f_rebin
      rebname = h.GetName() + "reb"
      hreb = gROOT.FindObject(rebname)
      if hreb:
         hreb.Delete()
      if f_rebin > 1:
         hreb = h.Rebin(f_rebin, rebname)
      else:
         hreb = h.Clone(rebname)
      i0 = hreb.FindBin(bg_start)
      while hreb.Integral(1, i0) < 10 and i0 < hreb.GetNbinsX():
         i0 += 1
      x1bg = hreb.GetBinCenter(i0)
      y1bg = hreb.GetBinContent(i0)
      i1 = i0
      i = i0 + 1
      while hreb.GetBinContent(i) < hreb.GetBinContent(i-1) or \
            hreb.GetBinContent(i+1) < hreb.GetBinContent(i-1):
         if y1bg > hreb.GetBinContent(i):
            x1bg = hreb.GetXaxis().GetBinCenter(i)
            y1bg = hreb.GetBinContent(i)
            i1 = i
         i += 1
      i = i1
      while hreb.Integral(1,i) > 10:
         x0bg = hreb.GetXaxis().GetBinCenter(i)
         y0bg = hreb.GetBinContent(i)
         if y0bg > y1bg * 30 or i == i0:
            break
         i -= 1
      if y0bg > y1bg and y1bg > 0:
         bgslope = (x1bg - bg_start) / math.log(y0bg / y1bg)
      else:
         y0bg = 1
         bgslope = 1
      i = hreb.FindBin(x1bg)
      y0sig = y1bg
      x0sig = x1bg
      nmax = hreb.GetNbinsX()
      while hreb.Integral(i,nmax) > 10:
         if hreb.GetBinContent(i) > y0sig:
            y0sig = hreb.GetBinContent(i)
            x0sig = hreb.GetXaxis().GetBinCenter(i)
         i += 1
      xmax = hreb.GetXaxis().GetBinCenter(i)
      fitmean = 0
      fitsigma = 0
      if hreb.Integral(i0, i) > 100:
         fitter0.SetParameter(0, y1bg)
         fitter0.SetParameter(1, x1bg)
         fitter0.SetParameter(2, bgslope)
         fitter0.SetParameter(3, y0sig)
         fitter0.SetParameter(4, x0sig)
         fitter0.SetParameter(5, x0sig / 15.)
         c1.cd(1)
         hreb.Draw()
         fitter0.Draw("hist same")
         c1.cd(2)
         fitter.SetParameter(0, y1bg / f_rebin)
         fitter.SetParameter(1, x1bg)
         fitter.SetParameter(2, bgslope)
         fitter.SetParameter(3, y0sig / f_rebin)
         fitter.SetParameter(4, x0sig)
         fitter.SetParameter(5, x0sig / 15.)
         h.Fit(fitter, "", "", x0bg, xmax)
         bgheight = fitter.GetParameter(0)
         bgmin = fitter.GetParameter(1)
         bgslope = fitter.GetParameter(2)
         fitheight = fitter.GetParameter(3)
         fitmean = fitter.GetParameter(4)
         fitsigma = abs(fitter.GetParameter(5))
         if bgheight > 0 and fitheight > 0:
            h.GetXaxis().SetRangeUser(x0bg, fitmean + 5*fitsigma)
      else:
         c1.cd(1)
         hreb.Draw()
         c1.cd(2)
         h.Draw()
      h.Draw()
      c1.Update()
      if interact:
         print "press enter to accept,",
         print "# for column#,",
         print "p<ped> to set bg_start limit,",
         print "r<rb> to set rebin factor,",
         print "e<eb> to set bg_end limit,",
         print "g to regen,",
         resp = raw_input("or q to quit: ")
         if len(resp) > 0:
            isint = re.match(r"([0-9]+)$", resp)
            isped = re.match(r"p *([.0-9]+)$", resp)
            isrebin = re.match(r"r *([0-9]+)$", resp)
            isend = re.match(r"e *([.0-9]+)$", resp)
            if isint:
               colbase = int(isint.group(1)) - (col + 1)
            elif isped:
               bg_start = float(isped.group(1))
               colbase -= 1
               continue
            elif isrebin:
               f_rebin = int(isrebin.group(1))
               colbase -= 1
               continue
            elif isend:
               bg_end = float(isend.group(1))
               colbase -= 1
               continue
            elif re.match(r"g", resp):
               f.Delete("col" + str(column) + ";*")
               colbase -= 1
               continue
            elif re.match(r"p", resp):
               img = "fityields_" + str(run) + "_" + str(column) + ".png"
               print "saving image as", img
               c1.Print(img)
               continue
            else:
               break
      if not column in peakmean:
         peakmean[column] = {}
         peaksigma[column] = {}
      peakmean[column][run] = fitmean
      peaksigma[column][run] = fitsigma
      h.Write()
   h.SetDirectory(0)

def fitall():
   """
   Make an initial non-interactive pass over all of the scan data runs,
   mainly just to create the histograms and do the initial fit, to make
   things go faster when we come back later for an interactive pass.
   """
   global interact
   interact = 0
   for ig in range(0, len(gval)):
      for run in gset[ig]:
         fit(run)
   interact = 1

def countall(cond="qf==0&&pi>1000"):
   """
   Make a pass through all of the datasets and plot the total counts
   that pass the condition given in string cond, saving the results
   in a color map.
   """
   global c1
   c1 = gROOT.FindObject("c1")
   if c1:
      c1.Delete()
   c1 = TCanvas("c1","c1",0,0,800,400)
   global hitmap
   hitmap = [0]*3
   for ig in range(0, len(gval)):
      hitmap[ig] = TH2D("hitmap" + str(ig),
                        "TAGM count map for row scans with g=" + str(gval[ig]),
                        102, 1, 103, 5, 1, 6)
      hitmap[ig].SetDirectory(0)
      hitmap[ig].SetStats(0)
      for irow in range(0, len(gset[ig])):
         row = irow + 1
         run = gset[ig][irow]
         f = TFile("TAGMtrees_" + str(run) + ".root")
         fadc = gROOT.FindObject("fadc")
         h = gROOT.FindObject("hpi")
         if h:
             h.Delete()
         h = TH1D("hpi", "", 102, 1, 103)
         fadc.Draw("col>>hpi", cond)
         for col in range(1, 103):
            hitmap[ig].SetBinContent(col, row, h.GetBinContent(col))
      hitmap[ig].Draw("colz")
      c1.Update()
   return hitmap

def save(file):
   """
   Save the fit results to an ouptut text file.
   """
   fout = open(file, "a")
   fout.write("column  run  fitmean  fitsigma\n")
   for column in peakmean:
      for run in peakmean[column]:
         fout.write("{0:4d} {1:6d} {2:12f} {3:12f}\n".format(column, run,
                    peakmean[column][run], peaksigma[column][run]))

def loadVbias(setVbias_conf):
   """
   Reads an existing setVbias.conf file (pathname passed in setVbias_conf)
   and saves the contents in a set of 2d arrays named as follows.
    setVbias_board[row][column] = "board" column (int)
    setVbias_channel[row][column] = "channel" column (int)
    setVbias_threshold[row][column] = "threshold" column (V)
    setVbias_gain[row][column] = "gain" column ((pF/pixel)
    setVbias_yield[row][column] = "yield" column (pixel/hit/V)
   """
   global setVbias_board
   global setVbias_channel
   global setVbias_threshold
   global setVbias_gain
   global setVbias_yield
   setVbias_board = {row : {} for row in range(0,6)}
   setVbias_channel = {row : {} for row in range(0,6)}
   setVbias_threshold = {row : {} for row in range(0,6)}
   setVbias_gain = {row : {} for row in range(0,6)}
   setVbias_yield = {row : {} for row in range(0,6)}
   for line in open(setVbias_conf):
      try:
         grep = re.match(r"  *([0-9a-fA-F]+)  *([0-9]+)  *([0-9]+)  *([0-9]+) " +
                         r" *([0-9.]+)  *([0-9.]+)  *([0-9.]+) *", line)
         if grep:
            row = int(grep.group(4))
            column = int(grep.group(3))
            setVbias_board[row][column] = int(grep.group(1), 16)
            setVbias_channel[row][column] = int(grep.group(2))
            setVbias_threshold[row][column] = float(grep.group(5))
            setVbias_gain[row][column] = float(grep.group(6))
            setVbias_yield[row][column] = float(grep.group(7))
      except:
         continue

def add2tree(textfile, row, gCoulombs, setVbias_conf, rootfile="fityields.root"):
   """
   Reads fit results from a text file previously created by save(file)
   above, and writes them into a root tree called yields. The meaning of
   the arguments to this function is as follows.
    textfile  - pathname to an output file generated by fityields.save()
    row       - fiber row number 1..5 that was active for this dataset
    gCoulombs - value of the -g argument to setVbias that was used
                to produce this dataset
    setVbias_conf - pathname to the setVbias.conf file that was used
                together with the -g option above to produce this dataset
    rootfile  - name of the root file in which to save the output tree
   If the output file already exists with an existing yields tree inside,
   it appends to the existing tree, otherwise the old file is overwritten.
   """
   loadVbias(setVbias_conf)

   e_row = array.array("i", [0])
   e_col = array.array("i", [0])
   e_Vbd0 = array.array("d", [0])
   e_Vbd = array.array("d", [0])
   e_G = array.array("d", [0])
   e_Y = array.array("d", [0])
   e_gQ = array.array("d", [0])
   e_qmean = array.array("d", [0])
   e_qrms = array.array("d", [0])
   e_run = array.array("i", [0])

   outfile = gROOT.FindObject(rootfile)
   if not outfile:
      outfile = TFile(rootfile, "update")
   tre = gROOT.FindObject("yields")
   if tre:
      tre.SetBranchAddress("row", e_row)
      tre.SetBranchAddress("col", e_col)
      tre.SetBranchAddress("Vbd0", e_Vbd0)
      tre.SetBranchAddress("Vbd", e_Vbd)
      tre.SetBranchAddress("G", e_G)
      tre.SetBranchAddress("Y", e_Y)
      tre.SetBranchAddress("gQ", e_gQ)
      tre.SetBranchAddress("qmean", e_qmean)
      tre.SetBranchAddress("qrms", e_qrms)
      tre.SetBranchAddress("run", e_run)
   else:
      tre = TTree("yields", "fityields output tree")
      tre.Branch("row", e_row, "row/I")
      tre.Branch("col", e_col, "col/I")
      tre.Branch("Vbd0", e_Vbd0, "Vbd0/D")
      tre.Branch("Vbd", e_Vbd, "Vbd/D")
      tre.Branch("G", e_G, "G/D")
      tre.Branch("Y", e_Y, "Y/D")
      tre.Branch("gQ", e_gQ, "gQ/d")
      tre.Branch("qmean", e_qmean, "qmean/D")
      tre.Branch("qrms", e_qrms, "qrms/D")
      tre.Branch("run", e_run, "run/I")

   written = 0
   for line in open(textfile):
      grep = re.match(r" *([0-9]+)  *([0-9]+)  *([0-9.]+)  *([0-9.]+) *", line)
      if grep:
         col = int(grep.group(1))
         run = int(grep.group(2))
         mean = float(grep.group(3))
         sigma = float(grep.group(4))
         e_row[0] = row
         e_col[0] = col
         e_run[0] = run
         try:
            e_Vbd0[0] = setVbias_threshold[row][col]
            e_Vbd[0] = setVbias_threshold[row][col]
            e_G[0] = setVbias_gain[row][col]
            e_Y[0] = setVbias_yield[row][col]
            e_gQ[0] = gCoulombs
         except:
            print "non-existent fiber reported in fityields file?"
            print "row=",row,",col=",col,"textfile=",textfile
            continue
         if mean > fADC_pedestal:
            e_qmean[0] = (mean - fADC_pedestal) * fADC_gain
         else:
            e_qmean[0] = 0
         e_qrms[0] = sigma * fADC_gain
         tre.Fill()
         written += 1
   print written, "entries added to yields tree, ",
   print "new total is", tre.GetEntries()
   tre.Write()

def maketree(rootfile, setVbias_conf):
   """
   Calls add2tree for all of the runs in the dataset
   """
   f = TFile(rootfile, "recreate")
   f = 0
   for ig in range(0, len(gval)):
      for row in range(1, 6):
         name = "row" + str(gset[ig][row-1][0]) + "g" + str(gset[ig][row-1][1:3]) + ".out"
         add2tree(name, row, gval[ig], setVbias_conf, rootfile)

def fityields(rootfile):
   """
   Analyze a root tree of calibration data generated by fityields.add2tree()
   and fit the fitted mean pulse height qmean as a quadratic function of
   the normalized bias voltage gQ. The fit is done in sqrt(qmean) vs gQ
   because the linear term in the quadratic is supposed to be zero:

              qmean = Y G (Vbias - Vbd)**2
              gQ = G (Vbias - Vbd)
   leading to
              sqrt(qmean) = sqrt(Y / G) gQ - sqrt(Y G) Vbd_correction

   The slope and y-intercept from the linear fit give new values for Y
   and Vbd, but not for G which must be taken from the setVbias.conf file.
   The new values for Y and G are saved in a new tree called "fit".
   """
   f = gROOT.FindObject(rootfile)
   if not f:
      f = TFile(rootfile, "update")
   tre = f.Get("yields")
   if not tre:
      print "Cannot find yields tree in", rootfile, ", giving up"
      return

   e_row = array.array("i", [0])
   e_col = array.array("i", [0])
   e_Vbd0 = array.array("d", [0])
   e_Vbd = array.array("d", [0])
   e_G = array.array("d", [0])
   e_Y = array.array("d", [0])
   ftre = TTree("fit", "fityields results")
   ftre.Branch("row", e_row, "row/I")
   ftre.Branch("col", e_col, "col/I")
   ftre.Branch("Vbd0", e_Vbd0, "Vbd0/D")
   ftre.Branch("Vbd", e_Vbd, "Vbd/D")
   ftre.Branch("G", e_G, "G/D")
   ftre.Branch("Y", e_Y, "Y/D")

   pause_on_chisqr = 0
   for row in range(1,6):
      for col in range(1,103):
         hname = "fit_{0}_{1}".format(row, col)
         htitle = "linear fit for row {0} column {1}".format(row, col)
         # The following binning was chosen assuming calibration data
         # were taken at g=0.25, g=0.35, and g=0.45, adjust as needed.
         h1 = TH1D(hname, htitle, 33, 0.2, 0.5)
         tre.Draw("gQ>>" + hname, "sqrt(qmean)*(qmean>0)*" +
                  "(row==" + str(row) + "&&" + "col==" + str(col) + ")")
         for b in range(1, h1.GetNbinsX()):
            if h1.GetBinContent(b) > 0:
               h1.SetBinError(b, 0.3)
         print "fitting row", row, "column", col
         h1.SetStats(0)
         if h1.Integral(1,33) > 0:
            h1.SetStats(0)
            if h1.Fit("pol1", "s").Get().IsValid():
               f1 = h1.GetFunction("pol1")
               yicept = f1.GetParameter(0)
               slope = f1.GetParameter(1)
               chisqr = f1.GetChisquare()
            else:
               yicept = 0
               slope = 1e-99
               chisqr = 1e99
         else:
            yicept = 0
            slope = 1e-99
            chisqr = 1e99
         c1.Update()
         if chisqr > pause_on_chisqr:
            print "p to save plot, q to abort, enter to continue: ",
            ans = raw_input()
            if ans == "p":
               c1.Print("yieldfit_" + str(row) + "_" + str(col) + ".png")
            elif ans == "q":
               return
            elif ans == "r":
               while ans == "r":
                  topbin = h1.FindBin(0.45)
                  h1.SetBinError(topbin, h1.GetBinError(topbin) * 5)
                  if h1.Fit("pol1", "s").Get().IsValid():
                     f1 = h1.GetFunction("pol1")
                     yicept = f1.GetParameter(0)
                     slope = f1.GetParameter(1)
                     chisqr = f1.GetChisquare()
                  print "p to save plot, q to abort, enter to continue: ",
                  c1.Update()
                  ans = raw_input()
            elif len(ans) > 0 and ans[0] == "s":
               while len(ans) > 0 and ans[0] == "s":
                  slope = float(ans.split()[1])
                  sfix = TF1("sfix", "[0]+" + str(slope) + "*x", 60, 80)
                  sfix.SetParameter(0, 1)
                  if h1.Fit(sfix, "s").Get().IsValid():
                     yicept = sfix.GetParameter(0)
                     chisqr = sfix.GetChisquare()
                  print "p to save plot, q to abort, enter to continue: ",
                  c1.Update()
                  ans = raw_input()
            elif chisqr > 1e10:
               yicept = 0
               slope = 1e-99
               chisqr = 1e99
            try:
               t = float(ans)
               pause_on_chisqr = t
            except:
               pass
         h1.Write()
         c1.Update()        
         for e in range(0, tre.GetEntries()):
            tre.GetEntry(e)
            if tre.row == row and tre.col == col:
               break
         if tre.row != row or tre.col != col:
            print "row", row, "column", col, "not found in yields tree, ",
            print "giving up."
            return
         e_row[0] = row
         e_col[0] = col
         e_Vbd0[0] = tre.Vbd0
         e_Vbd[0] = tre.Vbd0 - (yicept / (slope * tre.G))
         e_G[0] = tre.G
         e_Y[0] = tre.G * (slope ** 2)
         ftre.Fill()
   ftre.BuildIndex("row", "col")
   ftre.Write()

def visualize_threshold(new_setVbias_conf, threshold=0.5, select_gval=0.45):
   """
   Make a pass through all of the datasets and plot the pulse height
   spectra with the threshold as a fraction of the mean pulse integral
   marked at the appropriate place on the plot. To generate these plots
   you need the original channel Vbd values that were used when the
   scan data were generated, but you need the new Vbd fit values from
   the fityields analysis. That is why I have created a second method
   for reading config data from setVbias_conf files. It is also why
   I wrote a special function just to generate these plots.
   """
   global c1
   c1 = gROOT.FindObject("c1")
   if c1:
      c1.Delete()
   c1 = TCanvas("c1","c1",0,0,550,500)

   loadVbias(reference_setVbias_conf)

   global newconf
   try:
      newconf = newconf
   except:
      newconf = read_setVbias_conf(new_setVbias_conf)
   run = 0
   skip = 0
   for ig in range(0, len(gval)):
      if gval[ig] != select_gval:
         continue
      for ichan in range(0, len(newconf['board'])):
         row = newconf['row'][ichan]
         column = newconf['column'][ichan]
         Vbd = newconf['Vthresh'][ichan]
         Gain = newconf['Gain'][ichan]
         Yield = newconf['Yield'][ichan]
         Vbd0 = setVbias_threshold[row][column]
         try:
            thisrun = gset[ig][row - 1]
         except:
            print "run lookup error, ig=", ig ,"row=", row
            return
         if thisrun != run:
             run = thisrun
             f = TFile("TAGMtrees_" + str(run) + ".root")
         h = gROOT.FindObject("col" + str(column))
         if not h:
            print "no histogram found for column", column, " so regenerating..."
            hpi = TH1D("hpi", "column " + str(column), 480, 0, 8160)
            fadc.Draw("pi>>hpi", "qf==0&&row==0&&col==" + str(column))
            try:
               h = gROOT.FindObject("hpi").Clone("col" + str(column))
            except:
               print "unable to generate histogram for column", column,
               print ", moving on..."
               continue
            if not h:
               break
         qmean = (Yield / Gain) * (gval[ig] + Gain * (Vbd0 - Vbd))**2
         xpeak = qmean / fADC_gain + fADC_pedestal
         xdip = qmean * threshold / fADC_gain + fADC_pedestal
         h.GetXaxis().SetRangeUser(xdip * 0.5, xdip * 5)
         h.SetTitle("row " + str(row) + " column " + str(column) +
                    " at g=" + str(gval[ig]))
         c1.SetLogy()
         h.Draw()
         xthresh = numpy.array([xdip, xdip])
         ythresh = numpy.array([0, h.GetMaximum()])
         gthresh = TGraph(2, xthresh, ythresh)
         gthresh.SetLineColor(kBlue)
         gthresh.SetLineWidth(5)
         gthresh.Draw("same")
         xsumit = numpy.array([xpeak, xpeak])
         ysumit = numpy.array([0, h.GetMaximum()])
         gsumit = TGraph(2, xsumit, ysumit)
         gsumit.SetLineColor(kYellow)
         gsumit.SetLineWidth(5)
         gsumit.Draw("same")
         c1.Update()
         if skip > 0:
            skip -= 1
            continue
         print "threshold was", round(xdip),
         print "peak was", round(xpeak),
         print "run was", run
         print "press enter to continue,",
         resp = raw_input("p to print, or q to quit: ")
         if resp == 'p':
            c1.Print("thresh_" + str(row) + "_" + str(column) + ".png")
         elif resp == 'q':
            return
         elif len(resp) > 0:
            try:
               skip = int(resp)
            except:
               skip = 0

def read_setVbias_conf(setVbias_conf=reference_setVbias_conf):
   """
   Open an existing setVbias_conf file and read the contents 
   into a local table. The table is returned as an associative
   array with the columns as named arrays "board", "channel",
   "column", "row", "Vthresh", "Gain", and "Yield".
   """
   conf = {"board"   : [],
           "channel" : [],
           "column"  : [],
           "row"     : [],
           "Vthresh" : [],
           "Gain"    : [],
           "Yield"   : []}
   try:
      confin = open(setVbias_conf)
   except:
      print "Error - cannot open \"", setVbias_conf, "\" for input,",
      print "cannot continue."
      return conf
   for line in confin:
      grep = re.match(r"^  *([0-9a-fA-F]+)  *([0-9]+)  *([0-9]+)  *([0-9]+)" +
                      r"  *([0-9.]+)  *([0-9.]+)  *([0-9.]+)", line)
      if grep:
         board = grep.group(1)
         channel = grep.group(2)
         column = grep.group(3)
         row = grep.group(4)
         Vthresh = grep.group(5)
         Gain = grep.group(6)
         Yield = grep.group(7)
         try:
            channel = int(channel)
            column = int(column)
            row = int(row)
            Vthresh = float(Vthresh)
            Gain = float(Gain)
            Yield = float(Yield)
         except:
            continue
         conf['board'].append(board)
         conf['channel'].append(channel)
         conf['column'].append(column)
         conf['row'].append(row)
         conf['Vthresh'].append(Vthresh)
         conf['Gain'].append(Gain)
         conf['Yield'].append(Yield)
   return conf

def write_setVbias_conf(new_setVbias_conf, old_setVbias_conf, rootfile):
   """
   Write a new setVbias.conf file by reading the old one (second argument)
   and overwriting the last 3 columns with new fit information saved in
   the fit tree in rootfile.
   --- change introduced on 10-4-2018, rtj ---
   Formerly, I was overwriting the Vthresh values from the input file with
   new Vbd values derived from the linear fits to the light yields data.
   Those Vbd values are systematically biased low when the light yields
   are small, which spoils the calibration procedure. After this change,
   I now retain the Vthresh values from the input file, so that the only
   update to the input file that is performed is to overwrite the last
   column (Yields) with the results from the current light-yield fits.
   """
   confin = open(old_setVbias_conf)
   confout = open(new_setVbias_conf, "w")
   confout.write(confin.readline())
   confout.write(confin.readline())
   f = TFile(rootfile)
   ftre = f.Get("fit")
   if not ftre:
      print "Error - cannot find fit tree in", rootfile
      return
   for line in confin:
      grep = re.match(r"^  *([0-9a-fA-F]+)  *([0-9]+)  *([0-9]+)  *([0-9]+)" +
                      r"  *([0-9.]+)  *([0-9.]+)  *([0-9.]+)", line)
      if grep:
         col = int(grep.group(3))
         row = int(grep.group(4))
         found = 0
         for entry in range(0, ftre.GetEntries() + 1):
            ftre.GetEntry(entry)
            if ftre.row == row and ftre.col == col:
               found = 1
               break
         if not found:
            print "row", row, "column", col, "not found in fit tree, ",
            print "giving up"
            return
         out = "{0:5x}{1:12d}{2:13d}{3:12d}".format(int(grep.group(1), 16),
                                                    int(grep.group(2)),
                                                    int(grep.group(3)),
                                                    int(grep.group(4)))
         out += "{0:13.3f}{1:12.3f}{2:16.2f}".format(ftre.Vbd0,
                                                     ftre.G,
                                                     ftre.Y)
         confout.write(out + "\n")
      elif re.match(r"^ ", line):
         print "unrecognized format in", old_setVbias_conf,
         print " giving up"
         return
