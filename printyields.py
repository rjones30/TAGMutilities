from ROOT import *
import re

h1 = TH1D("h1", "", 100, 0, 700)
h2 = TH1D("h1", "", 100, 0, 700)
h1.GetXaxis().SetTitle("mean pixels per tag")
for line in open("setVbias_fulldetector-9-29-2018.conf"):
   fields = line.split()
   if len(fields) == 7:
      try:
         col = int(fields[2])
         row = int(fields[3])
         y = float(fields[6])
      except:
         continue
      if col > 42:
         h2.Fill(2*y)
      h1.Fill(2*y)
print h1.GetEntries()
print h2.GetEntries()
h1.SetStats(0)
h1.Draw()
h2.SetStats(0)
h2.SetLineColor(kRed)
h2.Draw("same")
