#!env python
#
# reconfig.py - uses information from a rowbyrow scan of the TAGM response
#               under normal tagging conditions to adjust the values in the
#               Yield (pixel/hit/V) column for better agreement with the
#               measured values.
#
# author: richard.t.jones at uconn.edu
# version: april 21, 2016
#
# usage:
# 1. Take a series of 5 runs, each one selecting one row for readout, as
#        $ setVbias -g 0 -r 1-5 -c 1-100 $OPTIONS
#        $ setVbias -g 0.45 -p 15 -r $ROW -c 1-100 $OPTIONS
#    where ROW varies from 1 to 5 across the 5 runs, and
#    OPTIONS="-H -C setVbias_fulldetector.conf gluon28.jlab.org:"
#    or some variation thereof.
# 2. Pass over all of the data files collected in step 1 above using the
#    TAGM_online plugin (eg. see script hd_root_evio.sh in this directory).
#    Use hadd to combine all output files from one run into a single output
#    root file (see script summer.sh).
# 3. Use the peaks.py python script and methods therein to fit the peaks
#    in the tagm_adc_pint_col directory to a gaussian over exponential 
#    background curve, then save the results to a three-column filen (see
#    fits-all-p15.out for an example) with columns row, column, peakmean.
# 4. Use reconfig.py (this script) to take the 500-line text file created
#    in step 3 above and use it to generate an updated setVbias.conf file.
#        $ python
#        >>> import reconfig
#        >>> reconfig.readconf("setVbias_fulldetector.conf")
#        >>> reconfig.readfits("fits-all-p15.out")
#        >>> reconfig.adjust(p=15, g=0.45)
#        >>> reconfig.writeconf("setVbias_fulldetector_new.conf")
#        >>>

Vconf = "/home/halld/online/TAGMutilities/setVbias_fulldetector-1-30-2016.conf"

row = range(0, 500)
column = range(0, 500)
board = range(0, 500)
channel = range(0, 500)
Vthresh = range(0, 500)
gain_pF = range(0, 500)
yield_iV = range(0, 500)
peak_log10 = range(0, 500)

import math

def readconf(conf=0):
   """
   Read the configuration file that was used to produce the Vbias settings
   when the TAGM row-scan calibration data were taken. The default input
   configuration file is the one hard-coded into the source line above.
   """
   if conf:
      global Vconf
      Vconf = conf
   Vconf_in = open(Vconf)
   for line in Vconf_in:
      try:
         c = int(line.split()[2])
         r = int(line.split()[3])
      except (IndexError, ValueError):
         continue
      i = (r - 1)*100 + (c - 1)
      row[i] = r
      column[i] = c
      board[i] = int(line.split()[0], 16)
      channel[i] = int(line.split()[1])
      Vthresh[i] = float(line.split()[4])
      gain_pF[i] = float(line.split()[5])
      yield_iV[i] = float(line.split()[6])

def readfits(fitsfile):
   """
   Read the peak fit values obtained by fitting the measured spectra to
   a gaussian over an exponential background. These are stored in an input
   text file in 3-column format: row column peakvalue
   where peakvalue is expressed as a log10(pint), pint being a pulse integral
   (pint) as defined by the FADC250 firmware.
   """
   fin = open(fitsfile)
   for line in fin:
      try:
         r = int(line.split()[0])
         c = int(line.split()[1])
         peak_log10[(r - 1)*100 + (c - 1)] = float(line.split()[2])
      except ValueError:
         pass

def adjust(p=15, g=0.45, peak_target=5000):
   """
   Use the informtion read from the fits file (assumes readfits has already
   been called) to rewrite the TAGM calibration information in memory,
   based on the values for the -p and -g arguments to setVbias that were
   used when the fitted data were collected. The adjustments are calculated
   so as to move all channels as close as possible to the peak_target value
   for the average pint value.
   """
   for i in range(0, 500):
      Vp = math.sqrt(p / (gain_pF[i] * yield_iV[i] + 1e-99))
      Vg = g / (gain_pF[i] + 1e-99)
      if Vp < Vg:
         peak = 10**peak_log10[i]
         yield_iV[i] *= peak / peak_target

def writeconf(conf):
   """
   Write out an updated config file, including adjustments based on the fits
   to measured data (assumes readfits and adjust have already been called).
   """
   Vconf_out = open(conf, "w")
   Vconf_in = open(Vconf)
   for line in Vconf_in:
      try:
         c = int(line.split()[2])
         r = int(line.split()[3])
         i = (r - 1)*100 + (c - 1)
         line = format(board[i], "5x")
         line += format(channel[i], "12d")
         line += format(column[i], "13d")
         line += format(row[i], "12d")
         line += format(Vthresh[i], "13.3f")
         line += format(gain_pF[i], "12.3f")
         line += format(yield_iV[i], "16.1f")
         Vconf_out.write(line + '\n')
      except (IndexError, ValueError):
         Vconf_out.write(line)
