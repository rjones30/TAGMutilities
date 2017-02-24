#!/bin/env python

from ROOT import *
import math
import array
import re

interact = 1

pedestal = 900.
bg_start = 970.
bg_end = 3500.
fit_start = bg_start
fit_end = 2500.;

# standard values for converting from fADC integral to charge (pC)
fADC_gain = 400. / 4096
fADC_pedestal = 900

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
   fadc = gROOT.FindObject("fadc")
   colbase = 1
   h = 0
   for col in range(0, 102):
      column = col + colbase
      if column > 102:
         break;
      h = gROOT.FindObject("col" + str(column))
      if not h:
         print "no histogram found for column", column, " so regenerating..."
         fadc.Draw("pi", "qf==0&&row==0&&col==" + str(column))
         try:
            h = gROOT.FindObject("htemp").Clone("col" + str(column))
         except:
            print "unable to generate histogram for column", column,
            print ", moving on..."
            continue
      if not h:
         break
      i0 = h.FindBin(bg_start)
      y0bg = h.GetBinContent(i0)
      i = i0
      while h.GetBinContent(i) < h.GetBinContent(i-1):
         i += 1
      x1bg = h.GetXaxis().GetBinCenter(i)
      y1bg = h.GetBinContent(i)
      i -= 1
      while h.GetBinContent(i-1) > h.GetBinContent(i):
         y0bg = h.GetBinContent(i)
         if y0bg > y1bg * 8 or i == i0:
            break
         i -= 1
      x0bg = h.GetXaxis().GetBinCenter(i)
      if y0bg > y1bg and y1bg > 0:
         bgslope = (x1bg - bg_start) / math.log(y0bg / y1bg)
      else:
         y0bg = 1
         bgslope = 1
      i = h.FindBin(x1bg)
      y0sig = y1bg
      x1sig = x1bg
      while h.GetBinContent(i) > 10:
         if h.GetBinContent(i) > y0sig:
            y0sig = h.GetBinContent(i)
            x1sig = h.GetXaxis().GetBinCenter(i)
         i += 1
      xmax = h.GetXaxis().GetBinCenter(i)
      fitmean = 0
      fitsigma = 0
      if h.Integral(i0, i) > 100:
         fitter.SetParameter(0, y1bg)
         fitter.SetParameter(1, x1bg)
         fitter.SetParameter(2, bgslope)
         fitter.SetParameter(3, y0sig)
         fitter.SetParameter(4, x1sig)
         fitter.SetParameter(5, x1sig / 8.)
         h.Fit(fitter, "", "", x0bg, xmax)
         bgheight = fitter.GetParameter(0)
         bgmin = fitter.GetParameter(1)
         bgslope = fitter.GetParameter(2)
         fitheight = fitter.GetParameter(3)
         fitmean = fitter.GetParameter(4)
         fitsigma = abs(fitter.GetParameter(5))
         if bgheight > 0 and fitheight > 0:
            h.GetXaxis().SetRangeUser(x0bg, fitmean + 5*fitsigma)
      h.Draw()
      c1.Update()
      if interact:
         print "press enter to accept,",
         print "# for column#,",
         print "<ped>. to refit,",
         print "g to regen,"
         resp = raw_input("or q to quit: ")
         if len(resp) > 0:
            isint = re.match(r"([0-9]+)$", resp)
            isfloat = re.match(r"([.0-9]+)$", resp)
            if isint:
               colbase = int(isint.group(1)) - (col + 1)
            elif isfloat:
               bg_start = float(isfloat.group(1))
               colbase -= 1
               continue
            elif re.match(r"^e.*", resp):
               bg_end = float(re.match(r"^e(.*)", resp).group(1))
               colbase -= 1
               continue
            elif re.match(r"g", resp):
               f.Delete("col" + str(column) + ";*")
               colbase -= 1
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
   fit(30195)
   fit(30196)
   fit(30197)
   fit(30199)
   fit(30200)
   fit(30201)
   fit(30203)
   fit(30206)
   fit(30207)
   fit(30208)
   fit(30211)
   fit(30212)
   fit(30213)
   fit(30216)
   fit(30217)
   interact = 1

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
         grep = re.match(r" *([0-9a-fA-F]+)  *([0-9]+)  *([0-9]+)  *([0-9]+) " +
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

def add2tree(textfile, row, gCoulombs, setVbias_conf, rootfile="fitpeaks.root"):
   """
   Reads fit results from a text file previously created by save(file)
   above, and writes them into a root tree called peaks. The meaning of
   the arguments to this function is as follows.
    textfile  - pathname to an output file generated by fitpeaks.save()
    row       - fiber row number 1..5 that was active for this dataset
    gCoulombs - value of the -g argument to setVbias that was used
                to produce this dataset
    setVbias_conf - pathname to the setVbias.conf file that was used
                together with the -g option above to produce this dataset
    rootfile  - name of the root file in which to save the output tree
   If the output file already exists with an existing peaks tree inside,
   it appends to the existing tree, otherwise the old file is overwritten.
   """
   loadVbias(setVbias_conf)

   e_row = array.array("i", [0])
   e_col = array.array("i", [0])
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
   tre = gROOT.FindObject("peaks")
   if tre:
      tre.SetBranchAddress("row", e_row)
      tre.SetBranchAddress("col", e_col)
      tre.SetBranchAddress("Vbd", e_Vbd)
      tre.SetBranchAddress("G", e_G)
      tre.SetBranchAddress("Y", e_Y)
      tre.SetBranchAddress("gQ", e_gQ)
      tre.SetBranchAddress("qmean", e_qmean)
      tre.SetBranchAddress("qrms", e_qrms)
      tre.SetBranchAddress("run", e_run)
   else:
      tre = TTree("peaks", "fitpeaks output tree")
      tre.Branch("row", e_row, "row/I")
      tre.Branch("col", e_col, "col/I")
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
         e_Vbd[0] = setVbias_threshold[row][col]
         e_G[0] = setVbias_gain[row][col]
         e_Y[0] = setVbias_yield[row][col]
         e_gQ[0] = gCoulombs
         if mean > fADC_pedestal:
            e_qmean[0] = (mean - fADC_pedestal) * fADC_gain
         else:
            e_qmean[0] = 0
         e_qrms[0] = sigma * fADC_gain
         tre.Fill()
         written += 1
   print written, "entries added to peaks tree, ",
   print "new total is", tre.GetEntries()
   tre.Write()

def maketree_2017():
   """
   Calls add2tree for all of the runs in the Spring 2017 dataset
   """
   rootfile = "fitpeaks_2017.root"
   setVbias_conf = "/home/halld/online/TAGMutilities/" +\
                   "setVbias_fulldetector-4-21-2016.conf"
   f = TFile(rootfile, "recreate")
   f = 0

   add2tree("fitpeaks.30195", 1, 0.25, setVbias_conf, rootfile)
   add2tree("fitpeaks.30196", 2, 0.25, setVbias_conf, rootfile)
   add2tree("fitpeaks.30197", 3, 0.25, setVbias_conf, rootfile)
   add2tree("fitpeaks.30199", 4, 0.25, setVbias_conf, rootfile)
   add2tree("fitpeaks.30200", 5, 0.25, setVbias_conf, rootfile)
   add2tree("fitpeaks.30201", 1, 0.35, setVbias_conf, rootfile)
   add2tree("fitpeaks.30203", 2, 0.35, setVbias_conf, rootfile)
   add2tree("fitpeaks.30206", 3, 0.35, setVbias_conf, rootfile)
   add2tree("fitpeaks.30207", 4, 0.35, setVbias_conf, rootfile)
   add2tree("fitpeaks.30208", 5, 0.35, setVbias_conf, rootfile)
   add2tree("fitpeaks.30211", 1, 0.45, setVbias_conf, rootfile)
   add2tree("fitpeaks.30212", 2, 0.45, setVbias_conf, rootfile)
   add2tree("fitpeaks.30213", 3, 0.45, setVbias_conf, rootfile)
   add2tree("fitpeaks.30216", 4, 0.45, setVbias_conf, rootfile)
   add2tree("fitpeaks.30217", 5, 0.45, setVbias_conf, rootfile)

def fityields(rootfile):
   """
   Analyze a root tree of calibration data generated by fitpeaks.add2tree()
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
   tre = f.Get("peaks")
   if not tre:
      print "Cannot find peaks tree in", rootfile, ", giving up"
      return

   e_row = array.array("i", [0])
   e_col = array.array("i", [0])
   e_Vbd = array.array("d", [0])
   e_G = array.array("d", [0])
   e_Y = array.array("d", [0])
   ftre = TTree("fit", "fitpeaks results")
   ftre.Branch("row", e_row, "row/I")
   ftre.Branch("col", e_col, "col/I")
   ftre.Branch("Vbd", e_Vbd, "Vbd/D")
   ftre.Branch("G", e_G, "G/D")
   ftre.Branch("Y", e_Y, "Y/D")

   for row in range(1,6):
      for col in range(1,103):
         hname = "fit_{0}_{1}".format(row, col)
         htitle = "linear fit for row {0} column {1}".format(row, col)
         # The following binning was chosen assuming calibration data
         # were taken at g=0.25, g=0.35, and g=0.45, adjust as needed.
         h1 = TH1D(hname, htitle, 33, 0.2, 0.5)
         tre.Draw("gQ>>" + hname, "sqrt(qmean)*(qmean>25)*" +
                  "(row==" + str(row) + "&&" + "col==" + str(col) + ")")
         for b in range(1, h1.GetNbinsX()):
            if h1.GetBinContent(b) > 0:
               h1.SetBinError(b, 0.3)
         print "fitting row", row, "column", col
         h1.SetStats(0)
         if h1.GetEntries() > 0:
            h1.Fit("pol1")
            f1 = h1.GetFunction("pol1")
            yicept = f1.GetParameter(0)
            slope = f1.GetParameter(1)
         else:
            yicept = 0
            slope = 1e-99
         h1.Write()
         c1.Update()        
         for e in range(0, tre.GetEntries()):
            tre.GetEntry(e)
            if tre.row == row and tre.col == col:
               break
         if tre.row != row or tre.col != col:
            print "row", row, "column", col, "not found in peaks tree, ",
            print "giving up."
            return
         e_row[0] = row
         e_col[0] = col
         e_Vbd[0] = tre.Vbd - (yicept / (slope * tre.G))
         e_G[0] = tre.G
         e_Y[0] = tre.G * (slope ** 2)
         # correct the yield to match the scale of pC for spring 2017 data
         e_Y[0] /= 2.7;
         ftre.Fill()
   ftre.BuildIndex("row", "col")
   ftre.Write()

def write_setVbias_conf(new_setVbias_conf, old_setVbias_conf, rootfile):
   """
   Write a new setVbias.conf file by reading the old one (second argument)
   and overwriting the last 3 columns with new fit information saved in
   the fit tree in rootfile.
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
      grep = re.match(r"^ *([0-9a-fA-F]+)  *([0-9]+)  *([0-9]+)  *([0-9]+)" +
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
         out += "{0:13.3f}{1:12.3f}{2:16.2f}".format(ftre.Vbd,
                                                     ftre.G,
                                                     ftre.Y)
         confout.write(out + "\n")
      else:
         print "unrecognized format in", old_serVbias_conf,
         print " giving up"
         return
