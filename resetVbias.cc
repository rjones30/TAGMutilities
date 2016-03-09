//
// resetVbias - command-line tool to reset the SiPM bias control card.
//
// author: richard.t.jones at uconn.edu
// version: july 17, 2014

#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <stdexcept>

#if UPDATE_STATUS_IN_EPICS
#include <cadef.h> /* Structures and data types used by epics CA */
int epics_status;
chid epics_channelId[2];
int TAGM_bias_state;
double TAGM_gain_pC;
#endif

#include <TAGMcontroller.h>
#include <TAGMcommunicator.h>

void usage()
{
   std::cerr << "Usage: resetVbias <0xHH>[@[<hostname>[:<port>]::][netdev]]" 
             << std::endl
             << " where <0xHH> is the 8-bit geographic address" << std::endl
             << " of the desired Vbias card in hex notation, " << std::endl
             << " (or the broadcast value 0xff to reset all cards)" << std::endl
             << " and <netdev> is the network device (eg. eth0)" << std::endl
             << " that communicates with the TAGM frontend." << std::endl
             << " If <netdev> is on another machine that is" << std::endl
             << " running the TAGMremotectrl daemon then that" << std::endl
             << " can be specified by including the <hostname>" << std::endl
             << " and <port> fields on the command line as shown." << std::endl;
   exit(1);
}

int main(int argc, char *argv[])
{
   if (argc < 2 ||
       strstr(argv[1], "-?") == argv[1] ||
       strstr(argv[1], "-h") == argv[1] ||
       strstr(argv[1], "--help") == argv[1])
   {
      usage();
   }
   int geoaddr;
   std::string arg1(argv[1]);
   std::size_t delim = arg1.find("@");
   if (sscanf(arg1.substr(0, delim).c_str(), "%x", &geoaddr) != 1) {
      usage();
   }
   std::string server;
   const char *netdev = 0;
   if (delim != arg1.npos) {
      arg1 = arg1.substr(delim + 1);
      if (arg1.find(":") == server.npos) {
         if (arg1.size() > 0)
            netdev = arg1.c_str();
      }
      else {
         server = arg1;
      }
   }

   TAGMcontroller *ctrl;
   try {
      if (server.size() == 0) {
         ctrl = new TAGMcontroller((unsigned char)geoaddr, netdev);
      }
      else {
         ctrl = new TAGMcommunicator((unsigned char)geoaddr, server);
      }
   }
   catch (const std::runtime_error &err) {
      std::cerr << err.what() << std::endl;
      exit(5);
   }
   if (! ctrl->reset()) {
      std::cerr << "Error returned by reset() method for board at "
                << std::hex << (unsigned int)ctrl->get_Geoaddr()
                << std::endl;
      exit(4);
   }
   delete ctrl;

#if UPDATE_STATUS_IN_EPICS

   epics_status = ca_task_initialize();
   SEVCHK(epics_status, "1");
   epics_status = ca_search("TAGM:bias:state", &epics_channelId[0]);
   SEVCHK(epics_status, "2");
   epics_status = ca_search("TAGM:gain:pC", &epics_channelId[1]);
   SEVCHK(epics_status, "3");
   epics_status = ca_pend_io(0.0);
   SEVCHK(epics_status, "3.5");
   TAGM_bias_state = 0;
   TAGM_gain_pC = 0;
   epics_status = ca_put(DBR_SHORT, epics_channelId[0], &TAGM_bias_state);
   SEVCHK(epics_status, "4");
   epics_status = ca_put(DBR_DOUBLE, epics_channelId[0], &TAGM_gain_pC);
   SEVCHK(epics_status, "5");
   epics_status = ca_pend_io(0.0);
   SEVCHK(epics_status, "6");
   ca_clear_channel(epics_channelId[0]);
   ca_clear_channel(epics_channelId[1]);
   ca_task_exit();

#endif
}
