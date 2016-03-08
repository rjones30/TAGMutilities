//
// TAGMremotectrl - daemon application that runs in the background on a
//                  machine with a NIC on the ethernet segment where the
//                  TAGM frontend resides. Remote tcp connections are
//                  accepted on a designated user-space port, and text
//                  messages are exchanged between the daemon and the
//                  remote client program that implement the functions
//                  of the TAGMcontroller base class.
//
// author: richard.t.jones at uconn.edu
// version: january 15, 2016
//
// programmer's notes:
// 1) The public interface of TAGMcontroller is exposed to remote clients
//    through a text message interface. The following commands and responses
//    are supported. The quotes are not a part of the literal message. All
//    requests must be terminated with a newline character.
//
//    *) "probe" - responds with a list of all Vbias boards that respond
//       to a broadcast query.
//    *) "select <address> [<netdev>]" - selects a particular front-end board
//       by its hardware address. The string <address> can either be a single
//       byte value in hexadecimal notation (eg. 0x9f) or it can be a full
//       ethernet address in dot notation (eg. 192.168.1.40).
//    *) "get_hostMACaddr [<netdev>]" - reports the ethernet MAC address of
//       the host running the TAGMremotectrl daemon on the network facing
//       the TAGM frontend.
//    *) "get_MACaddr" - reports the ethernet MAC address of the currently
//       selected board, or "none" if select has not been issued yet.
//    *) "get_Geoaddr" - reports the geographical address of the currently
//       selected board, or "none" if select has not been issued yet.
//    *) "get_Tchip" - reports the board temperature from T sensor chip (C)
//    *) "get_pos5Vpower" - reports the +5V power level (V)
//    *) "get_neg5Vpower" - reports the -5V power level (V)
//    *) "get_pos3_3Vpower" - reports the +3.3V power level (V)
//    *) "get_pos1_2Vpower" - reports the +1.2V power level (V)
//    *) "get_Vsumref_1" - reports the SUMREF from preamp 1 (V)
//    *) "get_Vsumref_2" - reports the SUMREF from preamp 2 (V)
//    *) "get_Vgainmode" - reports the GAINMODE shared by both preamps (V)
//    *) "get_gainmode" - reports the =0 (low) or =1 (high) or =-1 (undefined)
//    *) "get_Vtherm_1" - reports the thermister voltage on preamp 1 (V)
//    *) "get_Vtherm_2" - reports the thermister voltage on preamp 2 (V)
//    *) "get_Tpreamp_1" - reports the thermister temperature on preamp 1 (C)
//    *) "get_Tpreamp_2" - reports the thermister temperature on preamp 2 (C)
//    *) "get_VDAChealth" - reports the DAC channel 31 read-back level (V)
//    *) "get_VDACdiode" - reports the DAC temperature diode voltage (V)
//    *) "get_TDAC" - reports the DAC internal temperature reading (C)
//    *) "latch_status" - capture board status in state variables and return
//                          captured data in response to get_XXX()
//    *) "passthru_status" - reset saved state from last latch_levels() and
//                          have each get_XXX() request fresh data from board
//    *) "latch_voltages" - capture board's demand voltages in state variables
//                          and return captured data in response to getV()
//    *) "passthru_voltages" - reset saved voltages from last latch_voltages()
//                          and have each getV() request fresh data from board
//    *) "getV <chan>" - reports the voltage of channel <chan> on board (V)
//    *) "getVnew <chan>" - reports the voltage of channel <chan> to be set
//                          in next ramp (V)
//    *) "setV <chan> <V>" - );  // assign voltage <V> to channel <chan> to be
//                           set in next ramp (V)
//    *) "get_last_packet" - reports the last packet received from the board
//    *) "ramp" - push the new voltages to the board, if any
//    *) "reset" - send a hard reset to the board, if selected, otherwise
//                 send the hard reset to all boards in the frontend.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <sstream>
#include <iostream>
#include <stdexcept>
#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <errno.h>

#include <TAGMcontroller.h>

int listener_port = 5692;  // default listener port, you choose!
int listener_socket;
int listener_fd;
char *netdev = 0;
TAGMcontroller *Vboard;
std::map<std::string, TAGMcontroller*> Vboards;

std::string process_request(const char* request)
{
   char mesg[strlen(request) + 2];
   strcpy(mesg, request);
   char *req = strtok(mesg, " ");
   if (req && strcmp(req, "probe") == 0) {
      const char *netdev = strtok(0, " ");
      if (netdev && strlen(netdev) == 0)
         netdev = 0;
      std::map<unsigned char, std::string> boardlist;
      boardlist = TAGMcontroller::probe(netdev);
      std::map<unsigned char, std::string>::iterator iter;
      std::stringstream response;
      for (iter = boardlist.begin(); iter != boardlist.end(); ++iter) {
         response << std::hex << (unsigned int)iter->first
                  << " " << iter->second << std::endl;
      }
      return response.str();
   }
   else if (strcmp(req, "get_hostMACaddr") == 0) {
      const char *netdev = strtok(0, " ");
      if (netdev && strlen(netdev) == 0)
         netdev = 0;
      TAGMcontroller *ctrl = Vboard;
      if (ctrl == 0) {
         try {
            ctrl = new TAGMcontroller((unsigned char)0xff, netdev);
         }
         catch (const std::runtime_error &err) {
            return std::string(err.what()) + "\n";
         }
      }
      return ctrl->get_hostMACaddr(netdev);
   }
   else if (strcmp(req, "reset") == 0) {
      TAGMcontroller *ctrl = Vboard;
      if (ctrl == 0) {
         try {
            ctrl = new TAGMcontroller((unsigned char)0xff);
         }
         catch (const std::runtime_error &err) {
            return std::string(err.what()) + "\n";
         }
      }
      if (! ctrl->reset()) {
         std::stringstream response;
         response << "TAGMremotectrl error - "
                  << "reset() method failed for board at "
                  << std::hex << (unsigned int)ctrl->get_Geoaddr()
                  << std::endl;
         return response.str();
      }
      if (Vboard == 0)
         delete ctrl;
      return std::string("ok\n");
   }
   else if (strcmp(req, "select") == 0) {
      unsigned char geoaddr;
      unsigned char macaddr[6];
      char *addr = strtok(0, " ");
      char *dev = strtok(0, " ");
      if (dev && strlen(dev) > 0) {
         if (netdev != 0) 
            free(netdev);
         netdev = (char*)malloc(strlen(dev));
         strcpy(netdev, dev);
      }
      else if (netdev == 0) {
         netdev = (char*)malloc(strlen(DEFAULT_NETWORK_DEVICE));
         strcpy(netdev, DEFAULT_NETWORK_DEVICE);
      }
      std::string boardId(addr);
      if (netdev != 0) {
         boardId += "::";
         boardId += netdev;
      }
      if (Vboards.find(boardId) != Vboards.end()) {
         Vboard = Vboards[boardId];
      }
      else if (sscanf(addr, "0x%2hhx", &geoaddr) == 1) {
         try {
            Vboard = new TAGMcontroller(geoaddr, netdev);
         }
         catch (const std::runtime_error &err) {
            Vboard = 0;
            return std::string(err.what()) + "\n";
         }
      }
      else if (sscanf(addr, "%2.2hhx.%2.2hhx.%2.2hhx.%2.2hhx.%2.2hhx.%2.2hhx", 
                      &macaddr[0], &macaddr[1], &macaddr[2],
                      &macaddr[3], &macaddr[4], &macaddr[5]) == 6)
      {
         try {
            Vboard = new TAGMcontroller(macaddr, netdev);
         }
         catch (const std::runtime_error &err) {
            Vboard = 0;
            return std::string(err.what()) + "\n";
         }
      }
      else {
         std::stringstream response;
         response << "TAGMremotectrl error - "
                  << "invalid address " << addr << std::endl;
         return response.str();
      }
      Vboards[boardId] = Vboard;
      return std::string("ok\n");
   }
   else if (Vboard == 0) {
      return std::string("TAGMremotectrl error - no board selected\n");
   }
   else if (strcmp(req, "get_MACaddr") == 0) {
      const unsigned char *macaddr = Vboard->get_MACaddr();
      std::stringstream response;
      for (int i=0; i<6; ++i) {
         char hexb[3];
         sprintf(hexb, "%2.2x", macaddr[i]);
         response << ((i>0)? "." : "") << hexb;
      }
      response << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Geoaddr") == 0) {
      const unsigned char geoaddr = Vboard->get_Geoaddr();
      char hexb[7];
      sprintf(hexb, "0x%2.2x\n", geoaddr);
      return std::string(hexb);
   }
   else if (strcmp(req, "get_Tchip") == 0) {
      std::stringstream response;
      response << Vboard->get_Tchip() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_pos5Vpower") == 0) {
      std::stringstream response;
      response << Vboard->get_pos5Vpower() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_neg5Vpower") == 0) {
      std::stringstream response;
      response << Vboard->get_neg5Vpower() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_pos3_3Vpower") == 0) {
      std::stringstream response;
      response << Vboard->get_pos3_3Vpower() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_pos1_2Vpower") == 0) {
      std::stringstream response;
      response << Vboard->get_pos1_2Vpower() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Vsumref_1") == 0) {
      std::stringstream response;
      response << Vboard->get_Vsumref_1() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Vsumref_2") == 0) {
      std::stringstream response;
      response << Vboard->get_Vsumref_2() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Vgainmode") == 0) {
      std::stringstream response;
      response << Vboard->get_Vgainmode() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_gainmode") == 0) {
      std::stringstream response;
      response << Vboard->get_gainmode() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Vtherm_1") == 0) {
      std::stringstream response;
      response << Vboard->get_Vtherm_1() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Vtherm_2") == 0) {
      std::stringstream response;
      response << Vboard->get_Vtherm_2() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Tpreamp_1") == 0) {
      std::stringstream response;
      response << Vboard->get_Tpreamp_1() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_Tpreamp_2") == 0) {
      std::stringstream response;
      response << Vboard->get_Tpreamp_2() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_VDAChealth") == 0) {
      std::stringstream response;
      response << Vboard->get_VDAChealth() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_VDACdiode") == 0) {
      std::stringstream response;
      response << Vboard->get_VDACdiode() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "get_TDAC") == 0) {
      std::stringstream response;
      response << Vboard->get_TDAC() << std::endl;
      return response.str();
   }
   else if (strcmp(req, "latch_status") == 0) {
      Vboard->passthru_status();
      Vboard->latch_status();
      return std::string("ok\n");
   }
   else if (strcmp(req, "passthru_status") == 0) {
      Vboard->passthru_status();
      return std::string("ok\n");
   }
   else if (strcmp(req, "latch_voltages") == 0) {
      Vboard->passthru_voltages();
      Vboard->latch_voltages();
      return std::string("ok\n");
   }
   else if (strcmp(req, "passthru_voltages") == 0) {
      Vboard->passthru_voltages();
      return std::string("ok\n");
   }
   else if (strcmp(req, "getV") == 0) {
      std::stringstream response;
      unsigned int chan;
      const char *arg = strtok(0, " ");
      if (arg && sscanf(arg, "%u", &chan) == 1) {
         response << Vboard->getV(chan) << std::endl;
      }
      else {
         response << "TAGMremotectrl error - "
                  << "invalid channel " << arg << std::endl;
      }
      return response.str();
   }
   else if (strcmp(req, "getVnew") == 0) {
      std::stringstream response;
      unsigned int chan;
      const char *arg = strtok(0, " ");
      if (arg && sscanf(arg, "%u", &chan) == 1) {
         response << Vboard->getVnew(chan) << std::endl;
      }
      else {
         response << "TAGMremotectrl error - "
                  << "invalid channel " << arg << std::endl;
      }
      return response.str();
   }
   else if (strcmp(req, "setV") == 0) {
      std::stringstream response;
      unsigned int chan;
      double V;
      const char *arg1 = strtok(0, " ");
      const char *arg2 = strtok(0, " ");
      if (arg1 == 0 || sscanf(arg1, "%u", &chan) != 1) {
         response << "TAGMremotectrl error - "
                  << "invalid channel " << arg1 << std::endl;
      }
      else if (arg2 == 0 || sscanf(arg2, "%lf", &V) != 1) {
         response << "TAGMremotectrl error - "
                  << "invalid voltage " << arg2 << std::endl;
      }
      else {
         Vboard->setV(chan, V);
         response << "ok\n";
      }
      return response.str();
   }
   else if (strcmp(req, "get_last_packet") == 0) {
      std::stringstream response;
      const unsigned char *pkt = Vboard->get_last_packet();
      int pktlen = pkt[13] + 14;
      for (int i=0; i < pktlen; ++i) {
         char hexb[3];
         sprintf(hexb, "%2.2x", pkt[i]);
         response << ((i>0)? " " : "") << hexb;
      }
      response << std::endl;
      return response.str();
   }
   else if (strcmp(req, "ramp") == 0) {
      if (Vboard->ramp()) {
         return std::string("ok");
      }
      else {
         std::stringstream response;
         response << "TAGMremotectrl error - "
                  << "error returned by ramp() method for board at "
                  << std::hex << (unsigned int)Vboard->get_Geoaddr()
                  << std::endl;
         return response.str();
      }
   }
   return std::string("unbelievable!\n");
}

int main(int argc, char *argv[])
{
   netdev = 0;
   for (int iarg = 1; iarg < argc; ++iarg) {
      if (strcmp(argv[iarg], "-p") == 0 &&
          sscanf(argv[++iarg], "%x", &listener_port) == 1)
      {
         ++iarg;
      }
      else if (strcmp(argv[iarg], "-?") == 0 ||
               strcmp(argv[iarg], "-h") == 0 ||
               strcmp(argv[iarg], "--help") == 0 ||
               argv[iarg][0] == '-' || argc - iarg > 2)
      {
         std::cerr << "Usage: TAGMremotectrl [-p <port>] [<network_device>]"
                   << std::endl
                   << " where <port> is the listening port"
                   << " through which clients will connect to this daemon"
                   << std::endl
                   << " and <network_device> is the name of the NIC" 
                   << " connecting to the TAGM frontend, eg. eth0"
                   << std::endl;
         exit(1);
      }
      else {
         netdev = (char *)malloc(strlen(argv[iarg]) + 1);
         strcpy(netdev, argv[iarg]);
      }
   }
   Vboard = 0;

   // open a listening tcp port and wait for incoming connections

   if ((listener_socket = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
      char errmesg[100];
      sprintf(errmesg, "Cannot open listener on port %d", listener_port);
      perror(errmesg);
      exit(1);
   }
   struct sockaddr_in myaddr;
   memset((char *)&myaddr, 0, sizeof(myaddr));
   myaddr.sin_family = AF_INET;
   myaddr.sin_addr.s_addr = htonl(INADDR_ANY);
   myaddr.sin_port = htons(listener_port);
   if (bind(listener_socket,
            (const struct sockaddr*)&myaddr,
            sizeof(myaddr)) < 0)
   {
      char errmesg[100];
      sprintf(errmesg, "Cannot bind listener on port %d", listener_port);
      perror(errmesg);
      exit(1);
   }
   if (listen(listener_socket, 0) < 0) {
      char errmesg[100];
      sprintf(errmesg, "Cannot listen on port %d", listener_port);
      perror(errmesg);
      exit(1);
   }
   
   for (;;) {
      printf("waiting for a client to connect...\n");
      socklen_t clientaddr_len;
      struct sockaddr_in clientaddr;
      while ((listener_fd = accept(listener_socket, 
                                   (sockaddr*)&clientaddr, 
                                   &clientaddr_len)) < 0)
      {
         // we may break out of accept if the system call
         // was interrupted. In this case, loop back and try again
         if ((errno != ECHILD) && (errno != ERESTART) && (errno != EINTR)) {
            perror("accept failed");
            exit(1);
         }
      }
      printf("just got a new connection, waiting for messages.\n");

      for (;;) {
         int request_len;
         int buffer_size = 999;
         char request[buffer_size];
         char *buffer = request;
         while (int nbytes = read(listener_fd, buffer, buffer_size)) {
            buffer_size -= nbytes;
            buffer += nbytes;
            if (buffer[-1] == '\n') {
               buffer[-1] = 0;
               break;
            }
         }
         if (buffer == request) {
            break;
         }
         else {
            std::string response = process_request(request);
            write(listener_fd, response.c_str(), response.size() + 1);
         }
      }
   }
   close(listener_fd);
}
