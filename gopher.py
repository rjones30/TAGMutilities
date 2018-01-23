#!/usr/bin/env python

from ROOT import *
import faScalerRates

h2 = 0

def take(fin):
   global h2
   h2 = faScalerRates.hscan(fin)

def gime(col, color):
   name = "hcol" + str(col)
   h = h2.ProjectionY(name, col, col)
   h.SetTitle("column " + str(col))
   h.SetLineColor(color)
   h.SetStats(0)
   return h

def gander(fin):
   take(fin)
   color = 1
   hcol = {}
   for col in range(80, 86):
      hcol[col] = gime(col, color)
      hcol[col].SetTitle("")
      hcol[col].SetMinimum(1)
      if color == 1:
         hcol[col].Draw()
      else:
         hcol[col].Draw("same")
      color += 1
   c1.SetLogy()
   c1.Print(fin + ".png")
