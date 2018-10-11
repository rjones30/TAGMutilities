from ROOT import *
import re

reference_setVbias_conf = "setVbias_fulldetector-8-22-2018.conf"
replacement_setVbias_conf = "setVbias_fulldetector-9-29-2018.conf"

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

ref_conf = read_setVbias_conf(reference_setVbias_conf)
rep_conf = read_setVbias_conf(replacement_setVbias_conf)

h1 = TH1D("h1", "", 300, -2, 2)
h1.GetXaxis().SetTitle("Vbd difference (V)")
h1.GetYaxis().SetTitle("counts")
h1.GetYaxis().SetTitleOffset(1.5)
h2 = TH2D("h2", "", 250, 68, 73, 250, 68, 73)
h2.SetStats(0)
h2.GetXaxis().SetTitle("Vbd from single-pixel fits (V)")
h2.GetYaxis().SetTitle("Vbd from light-yield fits (V)")
h2.GetYaxis().SetTitleOffset(1.5)
h3 = TH2D("h3", "", 250, -2, 2, 250, 0, 250)
h3.SetStats(0)
h3.GetXaxis().SetTitle("Vbd difference (V)")
h3.GetYaxis().SetTitle("light yield (pixels)")
h3.GetYaxis().SetTitleOffset(1.5)

if len(ref_conf['board']) != len(rep_conf['board']):
   print "lines in 2 setVbias.conf files not the same, cannot compare!"
   sys.exit(1)
for i in range(0, len(ref_conf['board'])):
   Vbd_ref = float(ref_conf['Vthresh'][i])
   Vbd_rep = float(rep_conf['Vthresh'][i])
   Y_pixels = float(rep_conf['Yield'][i])
   h1.Fill(Vbd_ref - Vbd_rep)
   h2.Fill(Vbd_ref, Vbd_rep)
   h3.Fill(Vbd_ref - Vbd_rep, Y_pixels)
