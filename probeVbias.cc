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
#include <TAGMcommunicator.h>

void usage()
{
   std::cerr << "Usage: probeVbias -l [remote_host[:port]::][netdev]"
             << std::endl
             << " where netdev is the name of an ethernet port, eg. eth0"
             << std::endl
             << " which may optionally be located on remote_host, served"
             << std::endl
             << " by a TAGMremotectrl daemon listening on port."
             << std::endl;
   exit(1);
}

int main(int argc, char *argv[])
{
   std::string server;
   char *netdev = 0;
   if (argc < 2) {
      usage();
   }
   else if (strcmp(argv[1], "-l") != 0) {
      usage();
   }
   else if (argc > 3) {
      usage();
   }
   else if (argc == 3) {
      server = argv[2];
      if (server.find(":") == server.npos) {
         netdev = argv[2];
         server = "";
      }
   }

   std::map<unsigned char, std::string> catalog;
   try {
      if (server.size()) 
         catalog = TAGMcommunicator::probe(server);
      else
         catalog = TAGMcontroller::probe(netdev);
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
