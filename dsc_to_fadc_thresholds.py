import fileinput
for line in fileinput.input():
   vals = line.rstrip().split()
   if "DSC2_ALLCH_THR" in vals[0]:
      print "FADC250_ALLCH_THR   ",
      for i in range(1, len(vals)):
         value = int(vals[i])
         print "  ", value * 2 + 100,
      print
   elif "slot" in vals[0]:
      slot = int(vals[1][:-1])
      print "FADC250_SLOTS   ", slot-1
   else:
      print line
