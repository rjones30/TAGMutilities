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

int main(int argc, char *argv[])
{
   if (argc < 2 ||
       strstr(argv[1], "-?") == argv[1] ||
       strstr(argv[1], "-h") == argv[1] ||
       strstr(argv[1], "--help") == argv[1])
   {
      std::cerr << "Usage: readVbias <0xHH>" << std::endl
                << " where <0xHH> is the 8-bit geographic address" << std::endl
                << " of the desired Vbias card in hex notation."
                << std::endl;
      exit(1);
   }
   int geoaddr;
   sscanf(argv[1],"%x", &geoaddr);

   TAGMcontroller *ctrl;
   try {
      ctrl = new TAGMcontroller((unsigned char)geoaddr);
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
   delete ctrl;
}
