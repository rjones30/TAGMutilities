//
// readVbias - command-line tool to read all control and status values
//             on a single SiPM bias control card, addressed by geoaddr
//
// author: richard.t.jones at uconn.edu
// version: july 17, 2014

#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <stdexcept>

#include <TAGMcontroller.h>
#include <TAGMcommunicator.h>

std::string server;

void usage()
{
   std::cerr << "Usage: readVbias <0xHH>[@[<hostname>[:<port>]::][netdev]]" 
             << std::endl
             << " where <0xHH> is the 8-bit geographic address" << std::endl
             << " of the desired Vbias card in hex notation, " << std::endl
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
   if (argc != 2 ||
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
   const char *netdev = 0;
   if (delim != arg1.npos) {
      std::string arg1dev = arg1.substr(delim + 1);
      if (arg1dev.find(":") == arg1dev.npos) {
         if (arg1dev.size() > 0)
            netdev = arg1dev.c_str();
      }
      else {
         server = arg1dev;
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
      ctrl->latch_status();
      ctrl->latch_voltages();
   }
   catch (const std::runtime_error &err) {
      std::cerr << err.what() << std::endl;
      exit(5);
   }

   std::cout << std::endl
             << "Readings received from Vbias board " 
             << std::hex << (unsigned int)ctrl->get_Geoaddr() << ":"
             << std::endl
             << "    +5V power = " << ctrl->get_pos5Vpower()
             << " V" << std::endl
             << "    -5V power = " << ctrl->get_neg5Vpower()
             << " V" << std::endl
             << "    +3.3V power = " << ctrl->get_pos3_3Vpower()
             << " V" << std::endl
             << "    +1.2V power = " << ctrl->get_pos1_2Vpower()
             << " V" << std::endl
             << "    gainmode = " << ctrl->get_Vgainmode()
             << " V " << ((ctrl->get_gainmode() == 0)? "(low)" :
                          (ctrl->get_gainmode() == 1)? "(high)" :
                          "(undefined)")
             << std::endl
             << "    preamp 1 sumref = " << ctrl->get_Vsumref_1()
             << " V" << std::endl
             << "    preamp 2 sumref = " << ctrl->get_Vsumref_2()
             << " V" << std::endl
             << "    DAC health level = " << ctrl->get_VDAChealth()
             << " V" << std::endl
             << "    chip temperature = " << ctrl->get_Tchip()
             << " C" << std::endl
             << "    DAC temperature = " << ctrl->get_TDAC()
             << " C" << std::endl
             << "    preamp 1 temperature = " << ctrl->get_Tpreamp_1()
             << " C" << std::endl
             << "    preamp 2 temperature = " << ctrl->get_Tpreamp_2()
             << " C" << std::endl
             << "    channel voltages are (V):";
   for (int chan=0; chan < 32; ) {
      std::cout << std::endl << "    ";
      for (int c=0; c < 5 && chan < 32; ++c, ++chan) {
         char str[10];
         sprintf(str, "%4d:%7.3f", chan, ctrl->getV(chan));
         std::cout << str;
      }
   }
   std::cout << std::endl << std::endl;
   //delete ctrl;
}
