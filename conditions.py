#!/usr/bin/env python
#
# conditions.py - script to read the frontend electronics environment
#                 parameters for all of the readout boards and report
#                 the results in tabular form.
#
# author: richard.t.jones at uconn.edu
# version: august 17, 2018

import os
import re
import subprocess

frendaddress = "gluon28.jlab.org:5692::"
readVbias = os.environ["HOME"] + "/TAGMutilities/bin/readVbias"

readings = {}
for gid in range(0x8e, 0x9f):
   readings[gid] = {}
   proc = subprocess.Popen([readVbias, hex(gid) + "@" + frendaddress], stdout=subprocess.PIPE)
   resp = proc.communicate()[0]
   for line in resp.split("\n"):
      m0 = re.match(r"^ *([^ ][^=]*) = (.*)$", line)
      if m0:
         readings[gid][m0.group(1)] = m0.group(2)

def print_table1():
   table_heads = ["+5V power", "-5V power", "+3.3V power", "+1.2V power"]
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
         print "{0:12s}".format(readings[gid][head]),
      print

def print_table2():
   table_heads = {"gainmode": "gainmode",
                  "sumref[1]": "preamp 1 sumref",
                  "sumref[2]": "preamp 2 sumref",
                  "DAC health": "DAC health level"}
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
         print "{0:12s}".format(" ".join(readings[gid][table_heads[head]].split()[0:2])),
      print

def print_table3():
   table_heads = {"ADC temp": "chip temperature",
                  "DAC temp": "DAC temperature",
                  "preamp[1]": "preamp 1 temperature",
                  "preamp[2]": "preamp 2 temperature"}
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
         print "{0:12s}".format(" ".join(readings[gid][table_heads[head]].split()[0:2])),
      print

print
print_table1()
print
print_table2()
print
print_table3()
