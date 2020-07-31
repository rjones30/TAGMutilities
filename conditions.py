#!/usr/bin/env python
#
# conditions.py - script to read the frontend electronics environment
#                 parameters for all of the readout boards and report
#                 the results in tabular form, optionally saving them
#                 to EPICS.
#
# author: richard.t.jones at uconn.edu
# version: august 17, 2018

import os
import re
import sys
import subprocess

frendaddress = "gluon28.jlab.org:5692::"
readVbias = os.environ["HOME"] + "/online/TAGMutilities/bin/readVbias"

def usage():
   print "Usage: python conditions.py [options]"
   print " where options may include the following,"
   print "  -s : save the readback values to EPICS"
   sys.exit(1)

epics = False
for i in range(1,len(sys.argv)):
   if sys.argv[i] == '-s':
      import epics
   else:
      usage()

def read_frontend():
   readings = {}
   for gid in range(0x8e, 0x9f):
      readings[gid] = {}
      proc = subprocess.Popen([readVbias, hex(gid) + "@" + frendaddress], stdout=subprocess.PIPE)
      resp = proc.communicate()[0]
      for line in resp.split("\n"):
         m0 = re.match(r"^ *([^ ][^=]*) = (.*)$", line)
         if m0:
            readings[gid][m0.group(1)] = m0.group(2)
   return readings

def print_table1():
   table_heads = ["+5V power", "-5V power", "+3.3V power", "+1.2V power"]
   epics_names = ["power:1", "power:2", "power:3", "power:4"]
   print "{0:12s}".format(" "),
   for head in table_heads:
      print "{0:12s}".format(head),
   print
   print "{0:11s}".format(" "),
   for head in table_heads:
      print "{0:12s}".format("------------"),
   print
   for gid in range(0x8e, 0x9f):
      print "{0:12s}".format(hex(gid)),
      i = 0
      for head in table_heads:
        try:
         print "{0:12s}".format(readings[gid][head]),
         if epics:
            evar = "TAGM:cb:{0}:{1}".format(gid - 0x8d, epics_names[i])
            evalue = float(readings[gid][head].split()[0])
            epics.caput(evar, evalue)
            i += 1
        except:
         print "{0:12s}".format("0"),
      print

def print_table2():
   table_heads = {"gainmode": "gainmode",
                  "sumref[1]": "preamp 1 sumref",
                  "sumref[2]": "preamp 2 sumref",
                  "DAC health": "DAC health level"}
   epics_names = {"gainmode": "status:1",
                  "sumref[1]": "status:2",
                  "sumref[2]": "status:3",
                  "DAC health": "status:4"}
   print "{0:12s}".format(" "),
   for head in table_heads:
      print "{0:12s}".format(head),
   print
   print "{0:11s}".format(" "),
   for head in table_heads:
      print "{0:12s}".format("------------"),
   print
   for gid in range(0x8e, 0x9f):
      print "{0:12s}".format(hex(gid)),
      for head in table_heads:
        try:
         print "{0:12s}".format(" ".join(readings[gid][table_heads[head]].split()[0:2])),
         if epics:
            evar = "TAGM:cb:{0}:{1}".format(gid - 0x8d, epics_names[head])
            evalue = float(readings[gid][table_heads[head]].split()[0])
            epics.caput(evar, evalue)
        except:
         print "{0:12s}".format("0"),
      print

def print_table3():
   table_heads = {"ADC temp": "chip temperature",
                  "DAC temp": "DAC temperature",
                  "preamp[1]": "preamp 1 temperature",
                  "preamp[2]": "preamp 2 temperature"}
   epics_names = {"ADC temp": "temp:1",
                  "DAC temp": "temp:2",
                  "preamp[1]": "temp:3",
                  "preamp[2]": "temp:4"}
   print "{0:12s}".format(" "),
   for head in sorted(table_heads):
      print "{0:12s}".format(head),
   print
   print "{0:11s}".format(" "),
   for head in sorted(table_heads):
      print "{0:12s}".format("------------"),
   print
   for gid in range(0x8e, 0x9f):
      print "{0:12s}".format(hex(gid)),
      for head in sorted(table_heads):
        try:
         print "{0:12s}".format(" ".join(readings[gid][table_heads[head]].split()[0:2])),
         if epics:
            evar = "TAGM:cb:{0}:{1}".format(gid - 0x8d, epics_names[head])
            evalue = float(readings[gid][table_heads[head]].split()[0])
            epics.caput(evar, evalue)
        except:
         print "{0:12s}".format("0"),
      print

readings = read_frontend()
print
print_table1()
print
print_table2()
print
print_table3()
