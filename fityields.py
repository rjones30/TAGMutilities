#!/bin/env python
#
# fityields.py - utility functions for reading TAGM pulse height spectra
#                from root spectra created using DANA plugin TAGM_bias and
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
fit_end = 8500.
f_rebin = 1
f_tilt = 0

# standard values for converting from fADC integral to charge (pC)
# dq = V*dt/R = fADC*(1V/4096)*4ns/50Ohm = fADC*0.01953pC
#fADC_gain = 0.01953 # pC/count

# Empirical value based on pC/adc_peak = 0.011pC/count in makeVbiasconf.py
# which gets multiplied by the ratio of high/low gain on the preamplifiers
# and the empirical ratio adc_peak/adc_pulse_integral = 0.235 measured using
# row-by-row data in runs 40635 on December 19, 2017.
fADC_gain = 0.011 * 18 * 0.235 # pC per adc_pulse_integral
fADC_pedestal = 900
fADC_mV_per_count = 1000. / 4096 # mV / fullcount
fADC_mV_per_pC = 50. / 20 # 50 Ohms / 20 ns

# If using discriminator rates, set these constants here
fADC_gain = 1
fADC_pedestal = 0
pedestal = 0.
bg_start = 5.
bg_end = 250.
fit_start = bg_start
fit_end = 750.;

# Here I go back to using fadc pulse-mode readout data -rtj, 9/20/2021
fADC_gain = 0.011 * 18 # pC per adc_pulse_peak
fADC_pedestal = 0
pedestal = 20.
bg_start = 20.
bg_end = 500.
fit_start = bg_start
fit_end = 750.
f_rebin = 8
f_tilt = 0

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

# Row-by-row scan data taken on 2/9/2019 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['125', '225', '325', '425', '525'],
        ['135', '235', '335', '435', '535'],
        ['145', '245', '345', '445', '545']]
reference_setVbias_conf = "setVbias_fulldetector-1-22-2019.conf"

# Row-by-row scan data taken on 12/7/2019 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['125', '225', '325', '425', '525'],
        ['135', '235', '335', '435', '535'],
        ['145', '245', '345', '445', '545']]
reference_setVbias_conf = "setVbias_fulldetector-12-2-2019.conf"

# Row-by-row dark pulse scan data taken on 9/9/2021 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['80386', '80389', '80392', '80395', '80398'],
        ['80387', '80390', '80393', '80396', '80399'],
        ['80388', '80391', '80394', '80397', '80400']]
reference_setVbias_conf = "setVbias_fulldetector-12-9-2019.conf"

# Row-by-row scan data taken on 9/23/2021 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['81152', '81155', '81143', '81146', '81149'],
        ['81153', '81156', '81144', '81147', '81150'],
        ['81154', '81157', '81145', '81148', '81151']]
reference_setVbias_conf = "setVbias_fulldetector-12-9-2019_calib.conf"

# Row-by-row scan data taken on 6/22/2022 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['100592', '100595', '100598', '100601', '100662'],
        ['100593', '100596', '100599', '100602', '100663'],
        ['100594', '100597', '100600', '100603', '100664']]
reference_setVbias_conf = 'setVbias_fulldetector-12-9-2019_calib.conf'

# Row-by-row scan data taken in August, 2022 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['110456', '110460', '110463', '110467', '110470'],
        ['110458', '110461', '110464', '110468', '110471'],
        ['110459', '110462', '110465', '110469', '110472']]
reference_setVbias_conf = 'setVbias_fulldetector-8-30-2022_calib.conf'

# Row-by-row scan data taken in January, 2023 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['120187', '120190', '120193', '120196', '120199'],
        ['120188', '120191', '120194', '120197', '120200'],
        ['120189', '120192', '120195', '120198', '120201']]
reference_setVbias_conf = 'setVbias_fulldetector-1-8-2023.conf'

# Row-by-row scan data taken in March, 2023 [rtj]
gval = [0.25, 0.35, 0.45]
gset = [['120895', '120898', '120901', '120904', '120907'],
        ['120896', '120899', '120902', '120905', '120908'],
        ['120897', '120900', '120903', '120906', '120909']]
reference_setVbias_conf = 'setVbias_fulldetector-1-16-2023.conf'

# ttab_roctagm1 is taken from the ccdb record /Translation/DAQ2detector
# TAGM section. It is a sequence map ordered by increasing fadc250
# slot, channel in the roctagm1 crate to fiber column. Individual
# fiber outputs from columns 9, 27, 81, and 99 show up as 103..122.
ttab_roctagm1 = {3:[3,2,1,6,5,4,103,104,105,106,107,9,8,7,12,11],
                 4:[10,15,14,13,18,17,16,21,20,19,24,23,22,108,109,110],
                 5:[111,112,27,26,25,30,29,28,33,32,31,36,35,34,39,38],
                 6:[37,42,41,40,45,44,43,48,47,46,51,50,49,54,53,52],
                 7:[57,56,55,60,59,58,63,62,61,66,65,64,69,68,67,72],
                 8:[71,70,75,74,73,78,77,76,113,114,115,116,117,81,80,79],
                 9:[84,83,82,87,86,85,90,89,88,93,92,91,96,95,94,118],
                10:[119,120,121,122,99,98,97,100,101,102,123,124,125,126,127,128]}

# ttab_roctagm2 is taken from the ccdb record /Translation/DAQ2detector
# TAGM section. It is a sequence map ordered by increasing discriminator
# slot, channel in the roctagm2 crate to fiber column. Individual
# fiber outputs from columns 9, 27, 81, and 99 show up as 103..122.
ttab_roctagm2 = {4:[3,2,1,6,5,4,103,104,105,106,107,9,8,7,12,11],
                 5:[10,15,14,13,18,17,16,21,20,19,24,23,22,108,109,110],
                 6:[111,112,27,26,25,30,29,28,33,32,31,36,35,34,39,38],
                 7:[37,42,41,40,45,44,43,48,47,46,51,50,49,54,53,52],
                 8:[57,56,55,60,59,58,63,62,61,66,65,64,69,68,67,72],
                 9:[71,70,75,74,73,78,77,76,113,114,115,116,117,81,80,79],
                10:[84,83,82,87,86,85,90,89,88,93,92,91,96,95,94,118],
                11:[119,120,121,122,99,98,97,100,101,102,123,124,125,126,127,128]}

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
   if var[0] <= pedestal:
      return 0
   elif par[0] <= 0 or par[3] <= 0:
      return 0
   elif par[4] <= pedestal:
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

def fit(run, nadcbins=300, adcmax=1500):
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
   global pedestal
   global fit_start
   global fit_end
   global bg_start
   global bg_end
   ftree = TFile("TAGMtrees_" + str(run) + ".root")
   fadc = ftree.Get("fadc")
   f = TFile("TAGMspectra_" + str(run) + ".root", "update")
   fitter = TF1("fitter", fitfunc, fit_start, fit_end, 6)
   fitter0 = TF1("fitter0", fitfunc, fit_start, fit_end, 6)
   global c1
   c1 = gROOT.FindObject("c1")
   if c1:
      c1.Delete()
   c1 = TCanvas("c1","c1",0,0,800,400)
   c1.Divide(2)
   c1.cd(1)
   c1_1 = gROOT.FindObject("c1_1")
   c1_1.SetLogy()
   parfix = None
   colbase = 1
   h = 0
   global hreb
   for col in range(0, 99999):
      column = col + colbase
      if column > 102:
         break;
      h = gROOT.FindObject("col" + str(column))
      if not h:
         print("no histogram found for column", column, " so regenerating...")
         hpeak = TH1D("hpeak", "column " + str(column), nadcbins, 0, adcmax)
         try:
            fadc.Draw("peak-ped/4>>hpeak", "qf==0&&row==0&&col==" + str(column))
            h = gROOT.FindObject("hpeak").Clone("col" + str(column))
         except:
            print("unable to generate histogram for column", column,
                  ", moving on...")
            if not column in peakmean:
               peakmean[column] = {}
               peaksigma[column] = {}
            peakmean[column][run] = 0
            peaksigma[column][run] = 0
            continue
      if not h:
         break
      global f_rebin
      global f_tilt
      print("f_rebin, f_tilt=", f_rebin, f_tilt)
      rebname = h.GetName() + "reb"
      hreb = gROOT.FindObject(rebname)
      if hreb:
         hreb.Delete()
      if f_rebin > 1:
         hreb = h.Rebin(f_rebin, rebname)
      else:
         hreb = h.Clone(rebname)
      hreb.GetXaxis().SetRange(1, hreb.GetNbinsX())
      if f_tilt != 0:
         ysum = 0
         for i in range(hreb.GetNbinsX()):
            x = hreb.GetBinCenter(i+1)
            y = hreb.GetBinContent(i+1)
            hreb.SetBinContent(i+1, y*math.exp(x * f_tilt))
            ysum += y
            if ysum > 0 and y == 0:
               break
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
         fitter0.SetParameter(0, y1bg * math.exp(-x1bg * f_tilt))
         fitter0.SetParameter(1, x1bg)
         fitter0.SetParameter(2, 1 / (1/bgslope + f_tilt))
         fitter0.SetParameter(3, y0sig * math.exp(-x0sig * f_tilt))
         fitter0.SetParameter(4, x0sig)
         fitter0.SetParameter(5, x0sig / 15.)
         if parfix:
            fitter0.SetParameter(4, parfix[0])
            fitter0.SetParameter(5, parfix[1])
         c1.cd(1)
         hreb.Draw()
         fitter0.Draw("hist same")
         print(f"bg_start={bg_start},fit_start={fit_start}")
         c1.cd(2)
         fitter.SetParameter(0, y1bg / f_rebin * math.exp(-x1bg * f_tilt))
         fitter.SetParameter(1, x1bg)
         fitter.SetParameter(2, 1 / (1/bgslope + f_tilt))
         fitter.SetParameter(3, y0sig / f_rebin * math.exp(-x0sig * f_tilt))
         fitter.SetParameter(4, x0sig)
         fitter.SetParameter(5, x0sig / 15.)
         if parfix:
            fitter.FixParameter(1, 250.)
            fitter.FixParameter(2, 90.)
            fitter.FixParameter(4, parfix[0])
            fitter.FixParameter(5, parfix[1])
            parfix = None
         else:
            fitter.ReleaseParameter(4)
            fitter.ReleaseParameter(5)
         nhitinfit = h.Integral(h.FindBin(x0bg), h.FindBin(xmax))
         if nhitinfit > 10:
            h.Fit(fitter, "", "", x0bg, xmax)
            bgheight = fitter.GetParameter(0)
            bgmin = fitter.GetParameter(1)
            bgslope = fitter.GetParameter(2)
            fitheight = fitter.GetParameter(3)
            fitmean = fitter.GetParameter(4)
            fitsigma = abs(fitter.GetParameter(5))
         else:
            bgheight = 0
            bgmin = 0
            bgslope = 0
            fitheight = 0
            fitmean = 0
            fitsigma = 0
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
         print("press enter to accept,",
               "# for column#,",
               "p<ped> to set bg_start limit,",
               "r<rb> to set rebin factor,",
               "t<rb> to set tilt factor,",
               "e<eb> to set bg_end limit,",
               "g to regen,", end='')
         resp = input("or q to quit: ")
         if len(resp) > 0:
            isint = re.match(r"([0-9]+)$", resp)
            isped = re.match(r"p *([.0-9]+)$", resp)
            isrebin = re.match(r"r *([0-9]+)$", resp)
            istilt = re.match(r"t *([.0-9]+)$", resp)
            isfix = re.match(r" *([1-9][.0-9]*), *([1-9][.0-9]*)$", resp)
            isend = re.match(r"e *([.0-9]+)$", resp)
            if isfix:
               parfix = [float(isfix.group(1)), float(isfix.group(2))]
               colbase -= 1
               continue
            elif isint:
               colbase = int(isint.group(1)) - (col + 1)
            elif isped:
               bg_start = float(isped.group(1))
               pedestal = bg_start
               fit_start = bg_start
               colbase -= 1
               continue
            elif isrebin:
               f_rebin = int(isrebin.group(1))
               colbase -= 1
               continue
            elif istilt:
               f_tilt = float(istilt.group(1))
               colbase -= 1
               continue
            elif isend:
               bg_end = float(isend.group(1))
               fit_end = bg_end
               colbase -= 1
               continue
            elif re.match(r"g", resp):
               if fadc:
                  f.Delete("col" + str(column) + ";*")
                  colbase -= 1
               else:
                  h.Delete()
                  h = gROOT.FindObject("col" + str(column))
                  colbase -= 1
               continue
            elif re.match(r"p", resp):
               img = "fityields_" + str(run) + "_" + str(column) + ".png"
               print("saving image as", img)
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

def fitall(active=0):
   """
   Make an initial non-interactive pass over all of the scan data runs,
   mainly just to create the histograms and do the initial fit, to make
   things go faster when we come back later for an interactive pass.
   """
   global interact
   interact = active
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
         f = TFile("TAGMspectra_" + str(run) + ".root")
         fadc = gROOT.FindObject("fadc")
         h = gROOT.FindObject("hcol")
         if h:
             h.Delete()
         h = TH1D("hcol", "", 102, 1, 103)
         fadc.Draw("col>>hcol", cond)
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
   and saves the contents in a set of global 2d arrays named as follows.
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
   e_G0 = array.array("d", [0])
   e_G = array.array("d", [0])
   e_Y0 = array.array("d", [0])
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
      tre.SetBranchAddress("G0", e_G)
      tre.SetBranchAddress("G", e_G)
      tre.SetBranchAddress("Y0", e_Y0)
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
      tre.Branch("G0", e_G0, "G0/D")
      tre.Branch("G", e_G, "G/D")
      tre.Branch("Y0", e_Y0, "Y0/D")
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
            e_G0[0] = setVbias_gain[row][col]
            e_G[0] = setVbias_gain[row][col]
            e_Y0[0] = setVbias_yield[row][col]
            e_Y[0] = setVbias_yield[row][col]
            e_gQ[0] = gCoulombs
         except:
            print("non-existent fiber reported in fityields file?")
            print("row=", row, ",col=", col, "textfile=", textfile)
            continue
         if mean > fADC_pedestal:
            e_qmean[0] = (mean - fADC_pedestal) * fADC_gain
         else:
            e_qmean[0] = 0
         e_qrms[0] = sigma * fADC_gain
         tre.Fill()
         written += 1
   print(written, "entries added to yields tree, ",
         "new total is", tre.GetEntries())
   tre.Write()

def maketree(rootfile, setVbias_conf, textfile=0):
   """
   Calls add2tree for all of the runs in the dataset, reading fit results from input
   textfile generated by fitresults.save(textfile). If textfile is allowed to default
   to zero then the fit results are looked up in individual text files with names like
   row1g25.out for the run with row=1, g=0.25 and so on, one for each run. If textfile
   contains more than one result for any given row and column, the later ones override
   the earlier.
   """
   def run2igrow(run):
      for ig in range(len(gval)):
         for row in range(1, 6):
            if int(gset[ig][row-1]) == run:
               return (ig, row)
      return (0,0)
   if textfile:
      textline = {}
      for line in open(textfile):
         sline = line.strip().split()
         if sline[0][0].isnumeric():
            col = int(sline[0])
            run = int(sline[1])
            if not run in textline:
               textline[run] = {}
            textline[run][col] = line
      for run in textline:
         ig,row = run2igrow(run)
         name = "row" + str(row) + "g" + str(gval[ig])[2:] + ".out"
         with open(name, "w") as fout:
            for col in sorted(textline[run]):
               fout.write(textline[run][col])
   f = TFile(rootfile, "recreate")
   f = 0
   for ig in range(0, len(gval)):
      for row in range(1, 6):
         name = "row" + str(row) + "g" + str(gval[ig])[2:] + ".out"
         add2tree(name, row, gval[ig], setVbias_conf, rootfile)

def bias2spectra(runno=0):
   """
   The fityields module normally reads its input from a root file
   created by the TAGM_trees plugin, containing a TTree named fadc,
   from which pulse height spectra for individual columns named
   col1..102 are generated. By convention, these files are named
   TAGMspectra_<run>.root, and can be quite large for high-statistics
   calibration runs. An alternate path to the same result is to use
   use TAGM_bias plugin that creates pulse height spectra directly
   during raw data analysis. The TAGM_bias plugin saves its output
   histograms in files named TAGMbias_<run>.root, with names like
   h_spectra_1..102. This function automates the conversion from
   TAGMbias_<run>.root to TAGMspectra_<run>.root histogram format.
   Functions like countall() that require the existence of the fadc
   tree will not work with these TAGMspectra_<run>.root files.
   """
   for ig in range(0, len(gval)):
      for run in gset[ig]:
         if runno > 0 and int(run) != runno:
            print("skipping", run, runno)
            continue
         f1 = TFile("TAGMbias_" + str(run) + ".root")
         f2 = TFile("TAGMspectra_" + str(run) + ".root", "recreate")
         for col in range(1, 103):
            h1 = f1.Get("h_spectra_{}".format(col))
            f2.cd()
            h2 = h1.Clone("col{}".format(col))
            h2.Write()

def fityields(new_setVbias_conf, rootfile):
   """
   Analyze a root tree of calibration data generated by fityields.add2tree()
   and fit the fitted mean pulse height qmean as a quadratic function of
   the bias voltage minus breakdown threshold (V - Vbd).  The primary output
   of fityields is an updated value for the pixel yield Y for each row,column
   under the new assumed values for Vbd and G contained in new_setVbias_conf.

              qmean = Y G (Vbias - Vbd)**2

   The result of the fit is a new value for Y and a chisquare from the fit,
   while the values of G and Vbd from new_setVbias_conf are assumed fixed.
   The values of Vbias for each qmean measurement are extracted from the
   fit results in rootfile as follows.

              Vbias = Vbd_scan + g_scan / G_scan

   where the values used for the breakdown voltage Vbd_scan and channel
   gain G_scan are those assumed when the scan was taken, saved with the
   peak fit results the rootfile yields tree. The new values for Y are
   saved in a new tree called "fit".
   """
   loadVbias(new_setVbias_conf)
   f = gROOT.FindObject(rootfile)
   if not f:
      f = TFile(rootfile, "update")
   tre = f.Get("yields")
   if not tre:
      print("Cannot find yields tree in", rootfile, ", giving up")
      return

   e_row = array.array("i", [0])
   e_col = array.array("i", [0])
   e_Vbd0 = array.array("d", [0])
   e_Vbd = array.array("d", [0])
   e_G0 = array.array("d", [0])
   e_G = array.array("d", [0])
   e_Y0 = array.array("d", [0])
   e_Y = array.array("d", [0])
   ftre = TTree("fit", "fityields results")
   ftre.Branch("row", e_row, "row/I")
   ftre.Branch("col", e_col, "col/I")
   ftre.Branch("Vbd0", e_Vbd0, "Vbd0/D")
   ftre.Branch("Vbd", e_Vbd, "Vbd/D")
   ftre.Branch("G0", e_G, "G/D")
   ftre.Branch("G", e_G, "G/D")
   ftre.Branch("Y", e_Y0, "Y0/D")
   ftre.Branch("Y", e_Y, "Y/D")

   f1 = TF1("f1", "[0]*(x-[1])*(x-[1])", 70, 75)

   pause_on_chisqr = 0
   for row in range(1,6):
      for col in range(1,103):
         hname = "fit_{0}_{1}".format(row, col)
         htitle = "quadratic fit for row {0} column {1}".format(row, col)
         h1 = TH1D(hname, htitle, 100, 70, 75)
         h1.GetXaxis().SetTitle("Vbias (V)")
         h1.GetYaxis().SetTitle("mean yield (pC)")
         tre.Draw("gQ/G+Vbd>>" + hname, "qmean*" +
                  "(row==" + str(row) + "&&" + "col==" + str(col) + ")")
         ymax = h1.GetMaximum()
         errorbar = 10
         imaxbin = 0
         for b in range(1, h1.GetNbinsX()):
            if h1.GetBinContent(b) > 0:
               h1.SetBinError(b, errorbar)
               errorbar = 3
               imaxbin = b
         ithresh = h1.FindBin(setVbias_threshold[row][col])
         h1.GetXaxis().SetRange(ithresh - 5, imaxbin + 5)
         h1.SetBinContent(ithresh, 0)
         h1.SetBinError(ithresh, 0.5)
         h1.SetMarkerStyle(20)
         h1.SetMaximum(ymax * 1.2)
         print("fitting row", row, "column", col)
         h1.SetStats(0)
         if h1.Integral() > 0:
            h1.SetStats(0)
            f1.SetParameter(0, 50)
            f1.FixParameter(1, setVbias_threshold[row][col])
            if h1.Fit(f1, "s").Get().IsValid():
               h1.Draw("E1")
               YG = f1.GetParameter(0)
               chisqr = f1.GetChisquare()
            else:
               YG = 0
               chisqr = 1e99
         else:
            YG = 0
            chisqr = 1e99
         c1 = gROOT.FindObject("c1")
         c1.Update()
         if chisqr > pause_on_chisqr:
            print("p to save plot, q to abort, enter to continue: ", end='')
            ans = input()
            if ans == "p":
               c1.Print("yieldfit_" + str(row) + "_" + str(col) + ".png")
            elif ans == "q":
               return
            elif chisqr > 1e10:
               YG = 0
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
            print("row", row, "column", col, "not found in yields tree, ",
                  "giving up.")
            return
         e_row[0] = row
         e_col[0] = col
         e_Vbd0[0] = tre.Vbd0
         e_Vbd[0] = setVbias_threshold[row][col]
         e_G0[0] = tre.G
         e_G[0] = setVbias_gain[row][col]
         e_Y0[0] = tre.Y
         if YG > 1 and setVbias_gain[row][col] > 0:
            e_Y[0] = YG / setVbias_gain[row][col]
         else:
            e_Y[0] = 0
         ftre.Fill()
   ftre.BuildIndex("row", "col")
   ftre.Write()

def fityields_old_method(rootfile):
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
      print("Cannot find yields tree in", rootfile, ", giving up")
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
         h1 = TH1D(hname, htitle, 21, -0.0125, 0.5125)
         h1.GetXaxis().SetTitle("g value (pF)")
         h1.GetYaxis().SetTitle("sqrt(mean yield) (pC^0.5)")
         tre.Draw("gQ>>" + hname, "sqrt(qmean)*(qmean>0)*" +
                  "(row==" + str(row) + "&&" + "col==" + str(col) + ")")
         errorbar = 1.0
         for b in range(1, h1.GetNbinsX()):
            if h1.GetBinContent(b) > 0:
               h1.SetBinError(b, errorbar)
               errorbar = 0.3
         h1.SetBinContent(1,0)
         h1.SetBinError(1,0.1)
         print("fitting row", row, "column", col)
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
         c1 = gROOT.FindObject("c1")
         c1.Update()
         if chisqr > pause_on_chisqr:
            print("p to save plot, q to abort, enter to continue: ", end='')
            ans = input()
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
                  print("p to save plot, q to abort, enter to continue: ", end='')
                  c1.Update()
                  ans = input()
            elif len(ans) > 0 and ans[0] == "s":
               while len(ans) > 0 and ans[0] == "s":
                  slope = float(ans.split()[1])
                  sfix = TF1("sfix", "[0]+" + str(slope) + "*x", 60, 80)
                  sfix.SetParameter(0, 1)
                  if h1.Fit(sfix, "s").Get().IsValid():
                     yicept = sfix.GetParameter(0)
                     chisqr = sfix.GetChisquare()
                  print("p to save plot, q to abort, enter to continue: ", end='')
                  c1.Update()
                  ans = input()
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
            print("row", row, "column", col, "not found in yields tree, ",
                  "giving up.")
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

def visualize_threshold(new_setVbias_conf, threshold=0.5, select_gval=0.45,
                        nadcbins=300, adcmax=1500):
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
            print("run lookup error, ig=", ig ,"row=", row)
            return
         if thisrun != run:
             run = thisrun
             f = TFile("TAGMspectra_" + str(run) + ".root")
         h = gROOT.FindObject("col" + str(column))
         if not h:
            print("no histogram found for column", column, " so regenerating...")
            hpeak = TH1D("hpeak", "column " + str(column), nadcbins, 0, adcmax)
            fadc.Draw("peak-ped/4>>hpeak", "qf==0&&row==0&&col==" + str(column))
            try:
               h = gROOT.FindObject("hpeak").Clone("col" + str(column))
            except:
               print("unable to generate histogram for column", column,
                     ", moving on...")
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
         nbins = h.GetNbinsX();
         xbins = [h.GetBinLowEdge(i) for i in range(1, nbins+2)]
         xbins = numpy.array(xbins, dtype=float)
         #xbins = (xbins - fADC_pedestal) * fADC_gain;
         h.SetBins(nbins, xbins)
         h.Draw()
         xthresh = numpy.array([xdip, xdip])
         #xthresh = (xthresh - fADC_pedestal) * fADC_gain;
         ythresh = numpy.array([0, h.GetMaximum()])
         gthresh = TGraph(2, xthresh, ythresh)
         gthresh.SetLineColor(kBlue)
         gthresh.SetLineWidth(5)
         gthresh.Draw("same")
         xsumit = numpy.array([xpeak, xpeak])
         #xsumit = (xsumit - fADC_pedestal) * fADC_gain;
         ysumit = numpy.array([0, h.GetMaximum()])
         gsumit = TGraph(2, xsumit, ysumit)
         gsumit.SetLineColor(kYellow)
         gsumit.SetLineWidth(5)
         gsumit.Draw("same")
         c1.Update()
         if skip > 0:
            skip -= 1
            continue
         print("threshold was", round(xdip),
               "peak was", round(xpeak),
               "run was", run,
               "press enter to continue,", end='')
         resp = input("p to print, or q to quit: ")
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
      print("Error - cannot open \"", setVbias_conf, "\" for input,",
            "cannot continue.")
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
      print("Error - cannot find fit tree in", rootfile)
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
            print("row", row, "column", col, "not found in fit tree, ",
                  "giving up")
            return
         out = "{0:5x}{1:12d}{2:13d}{3:12d}".format(int(grep.group(1), 16),
                                                    int(grep.group(2)),
                                                    int(grep.group(3)),
                                                    int(grep.group(4)))
         out += "{0:13.3f}{1:12.3f}{2:16.2f}".format(ftre.Vbd,
                                                     ftre.G,
                                                     ftre.Y)
         confout.write(out + "\n")
      elif re.match(r"^ ", line):
         print("unrecognized format in", old_setVbias_conf,
               " giving up")
         return

def write_fadc250_thresholds(outfile, new_setVbias_conf,
                             threshold=0.5, select_gval=0.5, minthresh=120):
   """
   Write out a new fadc250 readout thresholds file based on the calibration
   contained in the new_setVbias_conf file and fit results in rootfile.
   The thresholds are adjusted to place the online cut at the spot on the
   peak spectrum given by qmean(select_gval) * threshold. The minthresh
   argument is provided to prevent low-gain channels from being assigned
   a readout threshold so low it is succeptible to excessive noise.
   """
   loadVbias(new_setVbias_conf)

   fout = open(outfile, "w")
   for slot in ttab_roctagm1:
      fout.write("slot " + str(slot) + ":" + "\n")
      fout.write("FADC250_ALLCH_THR   ")
      for ichan in range(0, len(ttab_roctagm1[slot])):
         col = ttab_roctagm1[slot][ichan]
         if col > 102:
            t = 199
         else:
            qbase = 1e5
            for row in range(1,6):
               if setVbias_threshold[row][col] > 70: # don't include dead fibers
                  qmean = (setVbias_yield[row][col] * select_gval**2 / 
                           setVbias_gain[row][col])
                  qbase = min(qbase,qmean)
            print(f"column {col} has qbase={qbase}")
            t = 100 + qbase * threshold / fADC_gain 
         t = t if t > minthresh else minthresh
         fout.write(" {0:3d}".format(int(round(t))))
      fout.write("\n")
   fout.close()

def write_discrim_thresholds(outfile, new_setVbias_conf,
                             threshold=0.25, select_gval=0.5, minthresh=10):
   """
   Write out a new discriminator thresholds file based on the calibration
   contained in the new_setVbias_conf file and fit results in rootfile.
   The thresholds are adjusted to place the online cut at the spot on the
   peak spectrum given by qmean(select_gval) * threshold. The minthresh
   argument is provided to prevent low-gain channels from being assigned
   a discrimintor threshold so low it is succeptible to excessive noise.
   """
   loadVbias(new_setVbias_conf)

   fout = open(outfile, "w")
   for slot in ttab_roctagm2:
      fout.write("slot " + str(slot) + ":" + "\n")
      fout.write("DSC2_ALLCH_THR   ")
      for ichan in range(0, len(ttab_roctagm2[slot])):
         col = ttab_roctagm2[slot][ichan]
         if col > 102:
            t = 99
         else:
            qbase = 1e5
            for row in range(1,6):
               if setVbias_threshold[row][col] > 70: # don't include dead fibers
                  qmean = (setVbias_yield[row][col] * select_gval**2 / 
                           setVbias_gain[row][col])
                  qbase = min(qbase,qmean)
            print(f"column {col} has qbase={qbase}")
            t = qbase * threshold * fADC_mV_per_pC
         t = t if t > minthresh else minthresh
         fout.write(" {0:3d}".format(int(round(t))))
      fout.write("\n")
   fout.close()

def write_thresholds_old_method(new_setVbias_conf, old_setVbias_conf, outfile,
                                threshold=0.33, select_gval=0.45, minthresh=20):
   """
   Write out a new discriminator thresholds file based on the calibration
   contained in the new_setVbias_conf file based on old_setVbias_conf.
   """
   global c1
   c1 = gROOT.FindObject("c1")
   if c1:
      c1.Delete()
   c1 = TCanvas("c1","c1",0,0,550,500)

   loadVbias(old_setVbias_conf)

   global newconf
   try:
      newconf = newconf
   except:
      newconf = read_setVbias_conf(new_setVbias_conf)
   run = 0
   skip = 0
   threshes = [999] * 129;
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
            print("run lookup error, ig=", ig ,"row=", row)
            return
         if thisrun != run:
             run = thisrun
             f = TFile("TAGMspectra_" + str(run) + ".root")
         h = gROOT.FindObject("col" + str(column))
         if not h:
            print("no histogram found for column", column, " so regenerating...")
            hpeak = TH1D("hpeak", "column " + str(column), 300, 0, 1500)
            fadc.Draw("peak-ped/4>>hpeak", "qf==0&&row==0&&col==" + str(column))
            try:
               h = gROOT.FindObject("hpeak").Clone("col" + str(column))
            except:
               print("unable to generate histogram for column", column,
                     ", moving on...")
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
         nbins = h.GetNbinsX();
         xbins = [h.GetBinLowEdge(i) for i in range(1, nbins+2)]
         xbins = numpy.array(xbins, dtype=float)
         xbins = (xbins - fADC_pedestal) * fADC_gain;
         h.SetBins(nbins, xbins)
         h.Draw()
         xthresh = numpy.array([xdip, xdip])
         xthresh = (xthresh - fADC_pedestal) * fADC_gain;
         ythresh = numpy.array([0, h.GetMaximum()])
         gthresh = TGraph(2, xthresh, ythresh)
         gthresh.SetLineColor(kBlue)
         gthresh.SetLineWidth(5)
         gthresh.Draw("same")
         xsumit = numpy.array([xpeak, xpeak])
         xsumit = (xsumit - fADC_pedestal) * fADC_gain;
         ysumit = numpy.array([0, h.GetMaximum()])
         gsumit = TGraph(2, xsumit, ysumit)
         gsumit.SetLineColor(kYellow)
         gsumit.SetLineWidth(5)
         gsumit.Draw("same")
         c1.Update()
         if xsumit[0] < minthresh:
            print("Warning - column", column, "wanting threshold",
                  xsumit[0], "is ignored, min value is", minthresh)
         elif xsumit[0] < threshes[column]:
            threshes[column] = xsumit[0]
         if column == 9:
            threshes[102 + row] = xsumit[0]
         elif column == 27:
            threshes[107 + row] = xsumit[0]
         elif column == 81:
            threshes[112 + row] = xsumit[0]
         elif column == 99:
            threshes[117 + row] = xsumit[0]
   fout = open(outfile, "w")
   for slot in ttab_roctagm2:
      fout.write("slot " + str(slot) + ":" + "\n")
      fout.write("DSC2_ALLCH_THR   ")
      for ichan in range(0, len(ttab_roctagm2[slot])):
         col = ttab_roctagm2[slot][ichan]
         t = threshes[col]
         t = t if t > 0 else 999
         fout.write(" {0:3d}".format(int(round(t))))
      fout.write("\n")
   fout.close()
