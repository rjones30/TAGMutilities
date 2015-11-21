//
// probeVbias - command-line tool to probe for all SiPM bias control cards
//              that are present and powered on.
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
   if (argc < 2 || (strcmp(argv[1], "-l") != 0)) {
      std::cerr << "Usage: probeVbias -l" << std::endl;
      exit(1);
   }

   std::map<unsigned char, std::string> catalog;
   try {
      catalog = TAGMcontroller::probe();
   }
   catch (const std::runtime_error &err) {
      std::cerr << err.what() << std::endl;
      exit(5);
   }

   if (catalog.size() == 0) {
      std::cout << "No boards responding" << std::endl;
      exit(0);
   }

   std::cout << std::endl
             << "backplane address     Vbias board MAC" << std::endl
             << "---------------------------------------" << std::endl;
   std::map<unsigned char, std::string>::iterator iter;
   for (iter = catalog.begin(); iter != catalog.end(); ++iter) {
      std::cout << "      " << std::hex << (unsigned int)iter->first
                << "             " << iter->second << std::endl;
   }
   exit(0);
}
