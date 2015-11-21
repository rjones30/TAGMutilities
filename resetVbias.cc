//
// resetVbias - command-line tool to reset the SiPM bias control card.
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
      std::cerr << "Usage: resetVbias <0xHH>" << std::endl
                << " where <0xHH> is the 8-bit geographic address" << std::endl
                << " of the desired Vbias card in hex notation, "
                << "or 0xff to reset all cards."
                << std::endl;
      exit(1);
   }
   int geoaddr;
   sscanf(argv[1],"%x", &geoaddr);

   TAGMcontroller *ctrl;
   try {
      ctrl = new TAGMcontroller((unsigned char)geoaddr);
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
}
