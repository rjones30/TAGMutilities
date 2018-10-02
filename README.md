# TAGMutilities - tools for setting bias voltages and monitoring conditions on the GlueX tagger microscope frontend electronics

## Authors

* Richard Jones, University of Connecticut, Storrs, CT

## Description

The GlueX tagger microscope consists of 510 scintillating fibers arranged in 102 columns x 5 rows. Each scintillator is read out by an individual silicon photomultiplier (sipm), each with its own independent Vbias level.  Communication from a user on a linux workstation to the frontend controller takes place over ethernet. The TAGMcontroller class in this toolkit provides the low-level functionality for setting voltage levels in the frontend controller, and for reading back set levels and other conditions on the frontend such as power supply levels and operating temperatures.  User-level control is intended to take place through the following command line utilities.

1. **probeVbias** - broadcasts a query to all frontend controllers on the local ethernet segment, used to find out which boards are alive and reachable on the local segment.
2. **readVbias** - reads the current set points of all Vbias levels on a particular board#, and also reports any available supply levels and temperatures that the controller sends back.
3. **setVbias** - used to set Vbias levels on individual or sets of sipms, selected by row,column or by board#,channel#; also used to select between high/low gain setting on the preamplifiers.
4. **resetVbias** - sends a soft reset to a particular board#, or all boards if board# = 0xff; reboots the controller firmware, setVbias is a more gentle way to turn off voltages as it uses a slow ramp whereas reset is an abrupt way to cut bias voltage to all channels.
5. **sendpack** - low-level tests using pcap library to diagnose problems communicating with frontend boards, experts only!

## History

This library was developed for use with the dark box fiber testing setup at UConn.  It was packaged into a repository because it may also be useful for running bias calibrations at Jefferson Lab.

## Release history

Initial release on November 21, 2015.

## Usage synopsis

To see the usage synopsis for any of the utilities listed above under Description, invoke it with the option "--help".

## Dependencies

To build this package, you must have the pcap and pcap-devel packages installed on the Linux host. It should work on any flavor of Linux, not tested on Windows or Mac, but if the pcap library is installed then it should be straight-forward to modify the Makefile for building on those platforms.

## Building instructions

Simply cd to the top-level project directory and type "make".

## Documentation

Just this README.

## System Architecture at JLab

The system uses ethernet packets directly so does not rely on IP. There is a dedicated NIC on gluon28 for this purpose. It is device em2 and does not belong to any IP network. The programs listed above all rely on a program TAGMremotectrl to be running which communicates with the controller via this dedicated NIC. That process is therefore crucial for this system to work. Since the TAGMremotectrl process must access the device at a very low level, it is run as root and therefore cannot be started and stopped from the standard operations or user accounts. Instead, it is managed by the supervisord service whose configuration is maintained in /etc/supervisord.conf. If the TAGMremotectrl process dies, it will be restarted automatically.

The status of the process can be checked either with simple "ps" or via:

sudo supervisorctl status TAGMremotectrl

There has been occasion where the process was running, but not communicating so it had to be killed and restarted. This must be done via root on gluon28. It is worth noting that the last time I did this, it did not seem to get automatically restarted as I would have expected. I tried restarting it with the following:

sudo supervisorctl restart TAGMremotectrl

There seemed to be some delay though and it looked like it had problems starting up. I had to leave it but when I checked later, it was running OK (??)

## Testing

/home/hdops/TAGMutilities/bin/probeVbias -l gluon28.jlab.org:5692

## Troubleshooting

You are on your own here, but a good place to start in case of problems would be to read the comments in the TAGMcontroller.h and TAGMcontroller.cc source files. This is the best documentation that exists on the ethernet protocol supported by the controller firmware.

## Bugs

Please report to the author richard.t.jones at uconn.edu in case of problems.

## How to contribute

Addition of a high-level EPICS gui designed in a similar fashion to the other EPICS gui's in use by GlueX would be much appreciated.

## Contact the authors

Contact the author richard.t.jones at uconn.edu for more information.
