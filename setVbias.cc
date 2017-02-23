//
// setVbias - command-line tool to set the SiPM bias voltages 
//            on the GlueX tagger microscope readout electronics
//            from a configuration stored in a text file. It is
//            built on top of the low-level frontend communicator
//            class TAGMcontroller.
//
// author: richard.t.jones at uconn.edu
// version: created july 17, 2014
//          2.0 - november 21, 2015
//
// notes:
// 1) The format of the input text file is as follows:
//    >>>>>>>>> cut here
//    board(hex)   channel(0-31)   voltage(V)
//    ---------------------------------------
//      9f             0            71.950
//      9f             1            71.980
//    ... more lines like the above ...
//    >>>>>>>>> cut here
//    Lines starting with a space are assumed to contain 3 columns
//    of data ordered as shown above. All other lines are treated
//    as comments.
//
// 2) Version 2 introduces a new way to set voltage levels by means
//    of a config file and more flexible set of command-line options.
//    Usage:
//     $ setVbias -f <data_file>
//     $ setVbias [-H | -L] [-h <level>] [-C <config_file>] \
//                -r <rows> -c <columns> [-g <gain> [-p <peak>] | -V <level>]
//    where the meaning of the options is as follows.
//       -f <data_file>: reads voltage levels from a version 1 style
//                       input text file (see note 1 above).
//       -r <row_sequence>: selects channels with rows in row_sequence
//                       to be affected by this command, default is none.
//       -c <column_sequence>: selects only channels with columns in 
//                        column_sequence to be affected by this command,
//                        default is none.
//       -L : sets low gain mode on all boards addressed in this command,
//                        default is to leave it unchanged.
//       -H : sets high gain mode on all boards addressed in this command,
//                        default is to leave it unchanged.
//       -g <gain_pC>: set the Vbias levels to the level corresponding
//                        to gain_pC in pC per pixel.
//       -p <peak_pC>: set the Vbias levels to the level corresponding
//                        to average charge peak_pC hit for axial MIPS.
//       -h <health_V>: set the DAQHealth voltage to health_V, default
//                        is the standard value of 13V.
//       -V <fixed_V>: set all channels selected in this command to the
//                        same fixed_V voltage level.
//       -C <config_file>: selects an alternate config file, setVbias.config
//                        in the same directory as the executable is default.
//    and a row_sequence or column_sequence is a comma-separated list of
//    row and column index values or ranges as in 2,5,6,8-14,21 or 1-100.
//    Row and column numbers start with 1, not 0. If both -g and -p options
//    are given then the -p option overrides the standard behavior with -g,
//    except that the Vbias level will not exceed that specified by gain_pC.
//    If achieving the specified peak_pC value would require a Vbias level
//    greater than the gain_pC value specifies then that channel will be
//    effectively disabled by setting the Vbias level to less than its
//    threshold value.
//
// 3) To look up the board addresses that go with row,column pairs, and
//    to compute the Vbias levels corresponding with a stated single-pixel
//    gain, version 2 requires the existence of a config file. The config
//    file by default is setVbias.conf in the same directory as the
//    setVbias executable. An alternate can be specified on the command
//    line using the -C option. The format of the config file is as follows.
//    >>>>>>>>> cut here
//    board(hex) channel(0-31) column(1-6) row (1-5) threshold(V) gain(pF/pixel)
//    --------------------------------------------------------------------------
//      9f          0             1            1       71.950          0.225
//      9f          1             1            2       71.880          0.225
//      9f          2             1            3       71.850          0.225
//    ... more lines like the above ...
//    >>>>>>>>> cut here

#define MAX_ROWS 5
#define MAX_COLUMNS 102
#define DEFAULT_GAIN_PC 0.50
#define DEFAULT_PEAK_PC 0.00
#define DEFAULT_HEALTH_V 13.0

#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <getopt.h>
#include <string.h>
#include <math.h>

#if UPDATE_STATUS_IN_EPICS
#include <cadef.h> /* Structures and data types used by epics CA */
int epics_status;
chid epics_channelId[2];
int TAGM_bias_state;
double TAGM_gain_pC;
#endif

#include <iostream>
#include <fstream>
#include <map>
#include <stdexcept>

// Enable the following line to generate a hex dump of the last
// D packet and S packet received from each board before exit.
#define DUMP_LAST_PACKETS 1


#include <TAGMcontroller.h>
#include <TAGMcommunicator.h>

std::string server;
const char *netdev = 0;

void version()
{
   std::cout << "setVbias version 2.0" << std::endl;
}

void usage()
{
   std::cerr << "Usage: setVbias -f <input_text_file> [<dest>]" << std::endl
             << "   or: setVbias [-H | -L] [-h <level>] [-C <config_file>] \\"
             << std::endl
             << "                -r <rows> -c <columns> \\"
             << std::endl
             << "                [-g <gain_pC> [-p <peak_pC>] | -V <level>] \\"
             << std::endl
             << "                [<dest>]"
             << std::endl
             << " where <dest> is a string indicating how to reach the network"
             << std::endl
             << " where the TAGM frontend resides, formatted as follows."
             << std::endl
             << "   <dest> := [<hostname>[:<port>]::][netdev]]" << std::endl
             << " where <netdev> is the network device (eg. eth0)" << std::endl
             << " that communicates with the TAGM frontend." << std::endl
             << " If <netdev> is on a remote host that is" << std::endl
             << " running the TAGMremotectrl daemon then that" << std::endl
             << " is specified by including the <hostname>" << std::endl
             << " and <port> fields as shown, otherwise it" << std::endl
             << " is assumed to reside on the local host." << std::endl
             << std::endl;
   std::cerr << "Options:"
             << std::endl
             << " -f <data_file>: reads voltage levels from a version 1 style"
             << std::endl
             << "                 input text file (see note 1 above)."
             << std::endl
             << " -r <row_sequence>: selects channels with rows in row_sequence"
             << std::endl
             << "                 to be affected by this command, default is none."
             << std::endl
             << " -c <column_sequence>: selects only channels with columns in "
             << std::endl
             << "                  column_sequence to be affected by this command,"
             << std::endl
             << "                  default is none."
             << std::endl
             << " -L : sets low gain mode on all boards addressed in this command,"
             << std::endl
             << "                  default is to leave it unchanged."
             << std::endl
             << " -H : sets high gain mode on all boards addressed in this command,"
             << std::endl
             << "                  default is to leave it unchanged."
             << std::endl
             << " -g <gain_pC>: set the Vbias levels to the level corresponding"
             << std::endl
             << "                  to gain_pC in pC per pixel."
             << std::endl
             << " -p <peak_pC>: set the Vbias levels to the level corresponding"
             << std::endl
             << "                  to peak_pC in pC per axial electron."
             << std::endl
             << " -h <health_V>: set the DAQHealth voltage to health_V, default"
             << std::endl
             << "                  is the standard value of 13V."
             << std::endl
             << " -V <fixed_V>: set all channels selected in this command to the"
             << std::endl
             << "                  same fixed_V voltage level."
             << std::endl
             << " -C <config_file>: selects an alternate config file, setVbias.config"
             << std::endl
             << "                  in the same directory as the executable is default."
             << std::endl
             << "A row_sequence or column_sequence is a comma-separated list of"
             << std::endl
             << "row and column index values or ranges as in 2,5,6,8-14,21 or 1-100."
             << std::endl
             << "Row and column numbers start with 1, not 0."
             << std::endl
             << std::endl;
   exit(1);
}

void help()
{
   usage();
}

char cmdline_opts[] = "f:HLh:C:r:c:g:p:V:?v";
struct option cmdline_longopts[] = {
   {"--help", no_argument, 0, '?'},
   {"--version", no_argument, 0, 'v'},
   {"--config", required_argument, 0, 'C'},
   {"--gain_pC", required_argument, 0, 'g'},
   {"--peak_pC", required_argument, 0, 'p'},
   {"--highgain", required_argument, 0, 'H'},
   {"--lowgain", required_argument, 0, 'L'},
   {"--health_V", required_argument, 0, 'h'},
   {"--level_V", required_argument, 0, 'V'},
   {"--row", required_argument, 0, 'r'},
   {"--column", required_argument, 0, 'c'},
   {0,0,0,0}
};
extern char *optarg;
extern int optind, opterr, optopt;

char *textfile = 0;
char *configfile = 0;
double gain_pC = DEFAULT_GAIN_PC;
double peak_pC = DEFAULT_PEAK_PC;
int gainmode = 0;
double health_V = DEFAULT_HEALTH_V;
double level_V = -1;
int rows = 0;
int columns = 0;
unsigned char rowselect[MAX_ROWS + 1] = {0};
unsigned char colselect[MAX_COLUMNS + 1] = {0};
std::map<unsigned char, TAGMcontroller*> boards;

void dump_last_packet(const unsigned char *packet);
int decode_sequence(const char *seq, unsigned char *arr, int max);
void load_from_textfile();
void load_from_config();

int main(int argc, char *argv[])
{
   if (argc < 2) {
      usage();
   }

   // assign default pathname to config file
   configfile = (char*)malloc(strlen(argv[0]) + 9);
   sprintf(configfile, "%s.conf", argv[0]);
   char *base = strstr(configfile, "setVbias");
   sprintf(base, "../setVbias.conf", argv[0]);

   // parse command line arguments
   char opt;
   int longindex;
   while ((opt = getopt_long(argc, argv, cmdline_opts,
                             cmdline_longopts, &longindex)) > 0)
   {
      if (opt == 'f') {
         textfile = (char*)malloc(strlen(optarg) + 1);
         strcpy(textfile, optarg);
      }
      else if (opt == '?') {
         help();
         exit(0);
      }
      else if (opt == 'v') {
         version();
         exit(0);
      }
      else if (opt == 'C') {
         free(configfile);
         configfile = (char*)malloc(strlen(optarg) + 1);
         strcpy(configfile, optarg);
      }
      else if (opt == 'g') {
         sscanf(optarg, "%lf", &gain_pC);
      }
      else if (opt == 'p') {
         sscanf(optarg, "%lf", &peak_pC);
      }
      else if (opt == 'H') {
         if (gainmode == 1) {
            usage();
            exit(1);
         }
         gainmode = 2;
      }
      else if (opt == 'L') {
         if (gainmode == 2) {
            usage();
            exit(1);
         }
         gainmode = 1;
      }
      else if (opt == 'h') {
         sscanf(optarg, "%lf", &health_V);
      }
      else if (opt == 'V') {
         sscanf(optarg, "%lf", &level_V);
      }
      else if (opt == 'r') {
         rows = decode_sequence(optarg, rowselect, MAX_ROWS);
      }
      else if (opt == 'c') {
         columns = decode_sequence(optarg, colselect, MAX_COLUMNS);
      }
      else {
         usage();
      }
   }

   // decode the path to frontend network
   if (optind < argc) {
      std::string arglast(argv[optind]);
      if (arglast.find(":") == arglast.npos) {
         if (arglast.size() > 0)
            netdev = arglast.c_str();
      }
      else {
         server = arglast;
      }
   }

   // load external inputs
   if (textfile) {
      load_from_textfile();
   }
   else if (rows == 0 || columns == 0) {
      usage();
      exit(1);
   }
   else {
      load_from_config();
   }

#if UPDATE_STATUS_IN_EPICS

   // The following variables are maintained in epics
   // regarding the state of the TAGM frontend:
   //   *) TAGM:bias:state
   //   *) TAGM:gain:pC
   // The following notes are copied verbatim from HDLOG entry 
   // 3383180 submitted by aebarnes on Tue, 02/23/2016 - 11:46.
   //
   // These are used to keep track of the bias setting and gain setting
   // of the microscope which will be particularly useful when looking at
   // the alignment of the electron plane. TAGM:bias:state is a 16-bit word.
   // Starting with the least significant bit, the bits correspond to row 1,
   // row 2, row 3, row 4, row 5, high/low gain, status change, and the extra
   // bits are for future development.
   //
   // The values are as follows:
   // (1) 0 = row 1 is off, 1 = row 1 is on
   // (2) 0 = row 2 is off, 1 = row 2 is on
   // (3) 0 = row 3 is off, 1 = row 3 is on
   // (4) 0 = row 4 is off, 1 = row 4 is on
   // (5) 0 = row 5 is off, 1 = row 5 is on
   // (6) 0 = low gain, 1 = high gain
   // (7) 0 = not changing, 1 = changing
   // The convention for changing the state is to set the 7th bit to 1 and 
   // set the remaining bits to the values they are being set to. Once the
   // microscope is set the 7th bit is turned to 0 leaving the other bits
   // unchanged.
   //
   // Examples in binary (decimal):
   // The microscope is off would read 0000000 (0)
   // The microscope is turning on row 1 in high gain: 1100001 (97)
   // The microscope is in high gain for row 1 only: 0100001 (33)
   // The microscope is changing to low gain for all 5 rows: 1011111 (95)
   // The microscope is in low gain for all 5 rows: 0011111 (31)
   //
   // TAGM:gain:pC is a double. When any SiPM is biased this PV will have 
   // a value of the gain used which is nominally 0.45 pC/pixel. When all
   // SiPMs are off this PV will have a value of 0 pC/pixel.

   epics_status = ca_task_initialize();
   SEVCHK(epics_status, "1");
   epics_status = ca_search("TAGM:bias:state", &epics_channelId[0]);
   SEVCHK(epics_status, "2");
   epics_status = ca_search("TAGM:gain:pC", &epics_channelId[1]);
   SEVCHK(epics_status, "3");
   epics_status = ca_pend_io(0.0);
   SEVCHK(epics_status, "3.5");
   epics_status = ca_get(DBR_SHORT, epics_channelId[0], &TAGM_bias_state);
   SEVCHK(epics_status, "4");
   epics_status = ca_get(DBR_DOUBLE, epics_channelId[1], &TAGM_gain_pC);
   SEVCHK(epics_status, "5");
   epics_status = ca_pend_io(0.0);
   SEVCHK(epics_status, "6");
   TAGM_bias_state |= (1 << 6);
   epics_status = ca_put(DBR_SHORT, epics_channelId[0], &TAGM_bias_state);
   SEVCHK(epics_status, "7");

#endif

   // send commands to frontend
   std::map<unsigned char, TAGMcontroller*>::iterator iter;
   for (iter = boards.begin(); iter != boards.end(); ++iter) {
      if (! iter->second->ramp()) {
         std::cerr << "Error returned by ramp() method for board at "
                   << std::hex << (unsigned int)iter->first << std::endl;
         exit(4);
      }
#if DUMP_LAST_PACKETS
      iter->second->latch_voltages();
      dump_last_packet(iter->second->get_last_packet());
      iter->second->latch_status();
      dump_last_packet(iter->second->get_last_packet());
#endif
      delete iter->second;
   }

#if UPDATE_STATUS_IN_EPICS

   // write the final status to epics
   if (level_V >= 0)
      TAGM_gain_pC = -level_V;
   else if (peak_pC > 0)
      TAGM_gain_pC = peak_pC;
   else
      TAGM_gain_pC = gain_pC;
   epics_status = ca_put(DBR_DOUBLE, epics_channelId[1], &TAGM_gain_pC);
   SEVCHK(epics_status, "90");
   epics_status = ca_pend_io(0.0);
   SEVCHK(epics_status, "91");

   TAGM_bias_state &= 0x3f;
   if (gainmode == 1)
      TAGM_bias_state &= ~(1 << 5);
   else if (gainmode == 2)
      TAGM_bias_state |= (1 << 5);
   for (int r=0; r < 5; ++r)
      if (rowselect[r+1] == 0)
         TAGM_bias_state &= ~(1 << r);
      else
         TAGM_bias_state |= (1 << r);
   int allcolumns = 1;
   for (int c=0; c < 100; ++c) {
      if (colselect[c+1] == 0) {
         allcolumns = 0;
         break;
      }
   }
   if (allcolumns) {
      epics_status = ca_put(DBR_SHORT, epics_channelId[0], &TAGM_bias_state);
      SEVCHK(epics_status, "92");
      epics_status = ca_pend_io(0.0);
      SEVCHK(epics_status, "93");
   }
   else {
      for (int c=0; c < 100; ++c) {
         if (colselect[c+1] != 0) {
            TAGM_bias_state &= 0x3f;
            TAGM_bias_state |= ((c + 1) << 7);
            epics_status = ca_put(DBR_SHORT, epics_channelId[0], &TAGM_bias_state);
            SEVCHK(epics_status, "94");
            epics_status = ca_pend_io(0.0);
            SEVCHK(epics_status, "95");
         }
      }
   }
   ca_clear_channel(epics_channelId[0]);
   ca_clear_channel(epics_channelId[1]);
   ca_task_exit();

#endif

   exit(0);
}

void load_from_textfile()
{
   // Implements the version 1 algorithm, which reads a set of voltages from
   // an input text file and prepares them for uploading to the frontend.

   std::ifstream fin(textfile);
   if (!fin.good()) {
      std::cerr << "Error opening input file " << textfile << std::endl;
      exit(3);
   }

   while (fin.good()) {
      char line[999];
      fin.getline(line, 99);
      if (line[0] != ' ')
         continue;
      unsigned char geoaddr;
      unsigned int chan;
      double voltage;
      if (sscanf(line, " %x %d %lf", &geoaddr, &chan, &voltage) == 3) {
         if (boards.find(geoaddr) == boards.end()) {
            try {
               if (server.size() > 0) {
                  boards[geoaddr] = new TAGMcommunicator(geoaddr, server);
               }
               else {
                  boards[geoaddr] = new TAGMcontroller(geoaddr, netdev);
               }
            }
            catch (const std::runtime_error &err) {
               std::cerr << err.what() << std::endl;
               exit(5);
            }
         }
         boards[geoaddr]->setV(chan, voltage);
      }
   }
   fin.close();
}

void load_from_config()
{
   // Implements the version 2 algorithm, which reads the threshold Vbias
   // level and pixel capacitance (pF/pixel) from the config file, and 
   // uses them to compute the set values for the set of output channels
   // selected on the command line by row and column indices.

   std::ifstream fin(configfile);
   if (!fin.good()) {
      std::cerr << "Error opening config file " << configfile << std::endl;
      exit(4);
   }

   while (fin.good()) {
      char line[999];
      fin.getline(line, 99);
      if (line[0] != ' ')
         continue;
      unsigned char geoaddr;
      unsigned int chan;
      unsigned int row, col;
      double thresh_V;
      double pixelcap_pF;
      double meanyield_pix;
      if (sscanf(line, " %x %d %d %d %lf %lf %lf", &geoaddr, &chan,
                 &col, &row, &thresh_V, &pixelcap_pF, &meanyield_pix) == 7)
      {
         if (rowselect[row] == 0 || colselect[col] == 0)
            continue;
         if (boards.find(geoaddr) == boards.end()) {
            try {
               if (server.size() > 0) {
                  boards[geoaddr] = new TAGMcommunicator(geoaddr, server);
               }
               else {
                  boards[geoaddr] = new TAGMcontroller(geoaddr, netdev);
               }
               boards[geoaddr]->setV(31, health_V);
               boards[geoaddr]->setV(30, (gainmode < 2)? 5.0 : 10.);
            }
            catch (const std::runtime_error &err) {
               std::cerr << err.what() << std::endl;
               exit(5);
            }
         }
         if (level_V < 0) {
            double Vg = thresh_V + gain_pC / pixelcap_pF;
            if (peak_pC > 0) {
               double Vp = thresh_V + 
                           sqrt(peak_pC / (pixelcap_pF * meanyield_pix));
               boards[geoaddr]->setV(chan, (Vg > Vp)? Vp : Vg); 
            }
            else {
               boards[geoaddr]->setV(chan, Vg);
            }
         }
         else {
            boards[geoaddr]->setV(chan, level_V);
         }
      }
   }
   fin.close();
}

int decode_sequence(const char *seq, unsigned char *arr, int max)
{
   // Takes a string representing a set of unsigned integers, eg. "2,5,8-10"
   // and set the elements of arr to 1 for each member of the set.

   int set = 0;
   char *next;
   char *seq_copy = (char*)malloc(strlen(seq));
   strcpy(seq_copy, seq);
   char *tok = seq_copy;
   while ((next = strtok(tok, ","))) {
      tok = 0;
      int i = atoi(next);
      if (i < 1 || i > max) {
         usage();
         exit(2);
      }
      char *hyph = strchr(next, '-');
      int ilast = hyph? atoi(++hyph) : i;
      for (; i <= ilast && i <= max; ++i)
         arr[i] = 1;
      ++set;
   }
   return set;
}

void dump_last_packet(const unsigned char *packet) {
   if (packet == 0) {
      std::cerr << "dump_last_packet warning: The last packet returned"
                << " by the frontend boards was garbled or null."
                << std::endl;
      return;
   }
   int packet_len = (unsigned int)packet[13] + 14;
   for (int n=0; n < packet_len; n += 2) {
         char str[8];
         sprintf(str, "%2.2x%2.2x ", packet[n], packet[n+1]);
         std::cout << str;
   }
   std::cout << std::endl;
}
