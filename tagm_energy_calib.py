#!/usr/bin/env python3
#
# tagm_energy_calib.py - tools for matching the tagger microscope energy
#                        scale to that of the pair spectrometer.
#
# author: richard.t.jones at uconn.edu
# version: january 23, 2022
#
# usage: $ python3
#        >>> import tagm_energy_calib
#        >>> run = 120253 # must have PStagstudy2_{run}.root on disk
#        >>> h = tagm_energy_calib.fit_Epair_Etagm(run)
#        >>> h1 = tagm_energy_calib.ydist(h[1])
#        >>> # repeat above as necessary to get a good fit
#        >>> tagm_energy_calib.new_scaled_energy(run)

import ROOT
import numpy as np
import random
import subprocess
import glob

fin = 0
pstags = 0
ROOT.gROOT.ProcessLine(".L pstags.C++")
xrootdir = "root://nod26.phys.uconn.edu/Gluex/beamline/PStags-1-2023"
last_run = 0

def plot_Epair_Etagm(run):
   """
   Form a profile histogram of Epair vs Etagm, with bin edges set to
   the boundaries of the tagm physical channels, according to ccdb.
   Returns a list of histograms, with the profile histogram first, a
   2D histogram of the profile data with x and y axes swapped, and a
   2D histogram of time difference vs tagger channel number.
   """
   global fin
   global pstags
   global last_run
   last_run = run
   fin = ROOT.TXNetFile(xrootdir + f"/PStagstudy2_{run}.root")
   pstags = fin.Get("pstags")
   get_from_ccdb(run)
   pstags.Process("pstags", "", 5000000)
   h1 = ROOT.gROOT.FindObject("ttagm_pair")
   h2 = ROOT.gROOT.FindObject("Etagm_Epair")
   h3 = ROOT.gROOT.FindObject("Epair_Etagm")
   return h3, h2, h1

def new_scaled_energy(run, smoother="pol2"):
   """
   Write out a new list of numbers for the ccdb scaled_energy_range
   table that reflects a smooth fit to the energy from the PS.
   """
   get_from_ccdb(run)
   endpoint_calib = ROOT.pstags().endpoint_calib
   endpoint_energy = ROOT.pstags().endpoint_energy
   fout = open(f"new_scaled_energy.{run}", "w")
   Eps_tagm = ROOT.gROOT.FindObject("Epair_Etagm_fit")
   if not Eps_tagm:
      Eps_tagm = ROOT.gROOT.FindObject("Epair_Etagm")
   if not Eps_tagm:
      Eps_tagm = plot_Etagm_Epair(run)[0]
   Eps_tagm.Fit(smoother)
   for func in Eps_tagm.GetListOfFunctions():
      ntagm = Eps_tagm.GetNbinsX()
      for i in range(ntagm):
         Elow = Eps_tagm.GetXaxis().GetBinLowEdge(102-i)
         Ehigh = Eps_tagm.GetXaxis().GetBinUpEdge(102-i)
         f = [(endpoint_calib - endpoint_energy + func.Eval(E)) /
                                endpoint_calib for E in (Elow, Ehigh)]
         fout.write(f"{i+1}  {f[0]}  {f[1]}\n")
      break

def fit_Epair_Etagm(run, Eshift=0):
   """
   Generally the profile histogram of Epair vs Etagm does not give a
   high enough precision to be a basis for the scaled_energy_range
   tagm energy calibration because the coincidence spectra of Epair
   for a given tagm counter contains a lot of randoms in addition to
   the sharp coincidence spike. This function goes through the 2D
   Etagm_Epair histogram row-by-row and does a fit to the sharp peak
   corresponding to the true tagm-ps coincidences, and returns a 1D
   hitogram with the fit results and errors for the Epair centroid
   in each tagm channel. If plot_Epair_Etagm(run) has not yet been
   called, it is called automatically by fit_Epair_Etagm.
   """
   if run < 20000:
      title = f"run {run}, GlueX spring 2016"
   elif run < 30000:
      title = f"run {run}, GlueX fall 2016"
   elif run < 40000:
      title = f"run {run}, GlueX spring 2017"
   elif run < 50000:
      title = f"run {run}, GlueX spring 2018"
   elif run < 60000:
      title = f"run {run}, GlueX fall 2018"
   elif run < 70000:
      title = f"run {run}, Primex spring 2019"
   elif run < 80000:
      title = f"run {run}, GlueX spring 2020"
   elif run < 90000:
      title = f"run {run}, Primex fall 2021"
   elif run < 100000:
      title = f"run {run}, SRC fall 2021"
   elif run < 110000:
      title = f"run {run}, CPP summer 2022"
   elif run < 120000:
      title = f"run {run}, Primex fall 2022"
   elif run < 130000:
      title = f"run {run}, GlueX spring 2023"
   else:
      title = f"run {run}, unknown run period"
   if run != last_run:
      reset()
   Epair_Etagm = ROOT.gROOT.FindObject("Epair_Etagm")
   if not Epair_Etagm:
      Epair_Etagm, Etagm_Epair, ttagm_pair = plot_Epair_Etagm(run)
   else:
      Etagm_Epair = ROOT.gROOT.FindObject("Etagm_Epair")
   gausbg = ROOT.TF1("gausbg", fgausbg, 0, 9, 4)
   Epair_Etagm_fit = Epair_Etagm.ProjectionX("Epair_Etagm_fit")
   Epair_Etagm_fit.SetTitle(title)
   Epair_Etagm_fit.Reset()
   dEpair_Etagm_fit = Epair_Etagm_fit.Clone("dEpair_Etagm_fit")
   dEpair_Etagm_fit.GetYaxis().SetTitle("E_pair - E_tagm (GeV)")
   for icol in range(1,103):
      hx = Etagm_Epair.ProjectionX("hx", icol, icol)
      if hx.Integral() == 0:
         print("no events in column", 103 - icol, "so skipping...")
         continue
      ROOT.gStyle.SetOptStat(0)
      Etagm = Etagm_Epair.GetYaxis().GetBinCenter(icol)
      gausbg.SetParameter(0, Etagm)
      gausbg.SetParameter(1, 0.05)
      gausbg.SetParameter(2, hx.GetMaximum())
      gausbg.SetParameter(3, hx.Integral() / hx.GetNbinsX())
      print(f"trying fit to icolumn {icol} with parameters",
            gausbg.GetParameter(0), gausbg.GetParameter(1),
            gausbg.GetParameter(2), gausbg.GetParameter(3))
      fit = hx.Fit(gausbg, "s")
      while fit.Status() != 0 or abs(fit.Parameter(1)) > 5e-2\
                              or abs(fit.Parameter(1)) < 2e-2\
                              or abs(fit.Parameter(0) - Etagm) > 0.5:
         gausbg.SetParameter(0, Etagm + random.uniform(-0.05, 0.05))
         gausbg.SetParameter(1, random.uniform(0, 0.1))
         gausbg.SetParameter(2, hx.GetMaximum() * random.uniform(0,1))
         gausbg.SetParameter(3, hx.Integral() / hx.GetNbinsX() * random.uniform(0,1))
         print(f"retrying fit to icolumn {icol} with parameters",
               gausbg.GetParameter(0), gausbg.GetParameter(1),
               gausbg.GetParameter(2), gausbg.GetParameter(3))
         fit = hx.Fit(gausbg, "s", "", Etagm - random.uniform(0,1),
                                       Etagm + random.uniform(0,1))
         ROOT.gROOT.FindObject("c1").Update()
      ROOT.gROOT.FindObject("c1").Update()
      Ecent = fit.Parameter(0)
      Ewidt = abs(fit.Parameter(1))
      print(f"fit result for icolumn {icol}: {Ecent} +/- {Ewidt}")
      #ans = input("ok? ")
      Epair_Etagm_fit.SetBinContent(icol, Ecent - Eshift)
      Epair_Etagm_fit.SetBinError(icol, Ewidt)
      dEpair_Etagm_fit.SetBinContent(icol, Ecent - Eshift - Etagm)
      dEpair_Etagm_fit.SetBinError(icol, Ewidt)
   dEpair_Etagm_fit.Draw()
   ROOT.gROOT.FindObject("c1").Update()
   return Epair_Etagm_fit, dEpair_Etagm_fit

def fgausbg(v,p):
   """
   Fit function for Epair distributions for a single tagm counter, a
   gaussian peak over a flat background, best if the range of the fit
   is limited to a region over which the background is approx. flat.
   """
   return np.exp(-0.5 * ((v[0] - p[0]) / p[1])**2) * p[2] + p[3]

def get_from_ccdb(run):
   """
   Get beam energy and tagm scaled_energy_range tables from ccdb
   and save them in plain text files in the working directory,
   if they don't exist there already.
   """
   if glob.glob(f"endpoint_energy.{run}") and\
      glob.glob(f"endpoint_calib.{run}") and\
      glob.glob(f"scaled_energy_range.{run}"):
      return 0
   child = subprocess.Popen(["ccdb", "-i"], stdin=subprocess.PIPE, 
                                            stdout=subprocess.PIPE)
   child.communicate(f"""
      run {run}
      var rtjtest
      cat PHOTON_BEAM/endpoint_energy > endpoint_energy.{run}
      cat PHOTON_BEAM/hodoscope/endpoint_calib > endpoint_calib.{run}
      cat PHOTON_BEAM/microscope/scaled_energy_range > scaled_energy_range.{run}
      quit
      """.encode())
   return child.returncode

def reset():
   """
   Clear out ROOT histograms from previous runs.
   """
   for hist in ("Epair_Etagm", "Etagm_Epair", "ttagm_pair", 
               "Epair_Etagm_fit", "dEpair_Etagm_fit"):
      h = ROOT.gROOT.FindObject(hist)
      if h:
         h.Delete()

def ydist(hin, nbins=100):
   """
   Take a 1D histogram and form the distribution of its y values
   as a second 1D histogram.
   """
   ydist = ROOT.gROOT.FindObject("ydist")
   if ydist:
      ydist.Delete()
   ymin = (hin.GetMinimum() * (1 + 0.5/nbins) -
           hin.GetMaximum() * (0.5/nbins))
   ymax = (hin.GetMaximum() * (1 + 0.5/nbins) -
           hin.GetMinimum() * (0.5/nbins))
   ydist = ROOT.TH1D("ydist", hin.GetTitle(), nbins, ymin, ymax)
   for i in range(hin.GetNbinsX()):
      y = hin.GetBinContent(i+1)
      if y != 0:
         ydist.Fill(y)
   ydist.GetXaxis().SetTitle("E_pair - E_tagm (GeV)")
   ydist.GetYaxis().SetTitle("columns")
   ydist.SetStats(1)
   ydist.Draw()
   ROOT.gStyle.SetOptStat(1111)
   ydist.Draw()
   return ydist
