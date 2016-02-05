//
// Class implementation: TAGMcommunicator
//
// Purpose: represents a single Vbias control board for the 
//          GlueX tagger microscope readout electronics
//
// author: richard.t.jones at uconn.edu
// version: january 14, 2016
//
// This class exposes the exact same object interface as the
// TAGMcontroller class, but the implementation uses text messaging
// over a tcp connection to a remote server running the TAGMremotectrl
// daemon, where the physical connection to the frontend electronics
// is located. The only difference in usage between a TAGMcontroller
// and a TAGMcommunicator instance is the form of the server argument
// which replaces the netdev argument in the constructor arg list.
//               server := <hostname>[:port][::netdev]

#define DEFAULT_SERVER_PORT 5692

#include <iostream>
#include <stdexcept>
#include <string>
#include <map>
#include <sstream>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <arpa/inet.h>

#include "TAGMcommunicator.h"

std::map<std::string, int> TAGMcommunicator::fServer_sockfd;

TAGMcommunicator *TAGMcommunicator::fSelected;

TAGMcommunicator::TAGMcommunicator(unsigned char geoaddr, std::string server)
{
   if (fServer_sockfd.find(server) == fServer_sockfd.end())
      open_client_connection(server);
   fServer = server;
   char hexb[5];
   sprintf(hexb, "0x%2.2x", geoaddr);
   fBoard = hexb;
   select();
}

TAGMcommunicator::TAGMcommunicator(unsigned char MACaddr[6], std::string server)
{
   if (fServer_sockfd.find(server) == fServer_sockfd.end())
      open_client_connection(server);
   fServer = server;
   char hexb[20];
   sprintf(hexb, "%2.2x.%2.2x.%2.2x.%2.2x.%2.2x.%2.2x", 
                 MACaddr[0], MACaddr[1], MACaddr[2], 
                 MACaddr[3], MACaddr[4], MACaddr[5]);
   fBoard = hexb;
   select();
}

void TAGMcommunicator::open_client_connection(std::string server)
{
   std::string shost = server;
   std::string sport = server;
   std::size_t delim = shost.find(":");
   if (delim != shost.npos) {
      shost = shost.substr(0, delim);
      sport = server.substr(delim + 1);
   }
   delim = sport.find(":");
   if (delim == 0) {
      sport = "";
   }
   sport = sport.substr(0, delim);

   unsigned char ipaddr[4];
   unsigned short int ipport;
   if (sscanf(shost.c_str(), "%hhu.%hhu.%hhu.%hhu", 
                             &ipaddr[0], &ipaddr[1],
                             &ipaddr[2], &ipaddr[3]) != 4)
   {
      struct hostent *hent;
      hent = gethostbyname(shost.c_str());
      if (hent == 0 || 
          hent->h_addrtype != AF_INET || hent->h_length != 4 ||
          hent->h_addr_list[0] == 0)
      {
         char errmesg[1000];
         snprintf(errmesg, 999, "Cannot look up host %s", shost.c_str());
         throw std::runtime_error(errmesg);
      }
      for (int i=0; i<6; ++i)
         ipaddr[i] = hent->h_addr_list[0][i];
   }
   if (sport.size() == 0 || sscanf(sport.c_str(), "%hu", &ipport) != 1)
      ipport = DEFAULT_SERVER_PORT;

   int sockfd;
   if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
      char errmesg[1000];
      snprintf(errmesg, 999, "Cannot open network socket");
      throw std::runtime_error(errmesg);
   }

   struct sockaddr_in myaddr;
   memset((char *)&myaddr, 0, sizeof(myaddr));
   myaddr.sin_family = AF_INET;
   myaddr.sin_addr.s_addr = htonl(INADDR_ANY);
   myaddr.sin_port = htons(0);
   if (bind(sockfd, (const struct sockaddr*)&myaddr, sizeof(myaddr)) < 0) {
      char errmesg[1000];
      snprintf(errmesg, 999, "Cannot bind to network socket");
      throw std::runtime_error(errmesg);
   }

   unsigned int ip = ipaddr[3] + (ipaddr[2] << 8) + 
                                 (ipaddr[1] << 16) +
                                 (ipaddr[0] << 24);
   myaddr.sin_addr.s_addr = htonl(ip);
   myaddr.sin_port = htons(ipport);
   if (connect(sockfd, (struct sockaddr*)&myaddr, sizeof(myaddr)) != 0) {
      char errmesg[1000];
      snprintf(errmesg, 999, "Connection failed to server %s", server.c_str());
      throw std::runtime_error(errmesg);
   }
   fServer_sockfd[server] = sockfd;
}

TAGMcommunicator::~TAGMcommunicator() { }

std::map<unsigned char, std::string> TAGMcommunicator::probe(std::string server)
{
   if (fServer_sockfd.find(server) == fServer_sockfd.end())
      open_client_connection(server);
   std::string req("probe");
   std::string netdev = get_netdev(server);
   if (netdev.size() > 0)
      req += " " + netdev;
   std::map<unsigned char, std::string> boards;
   std::string resp(request_response(req, server));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   while (sresp.rdbuf()->in_avail() > 0) {
      std::string line;
      getline(sresp, line);
      unsigned char geoaddr;
      char macaddr[20];
      if (sscanf(line.c_str(), "%hhx %17s", &geoaddr, macaddr) == 2)
         boards[geoaddr] = macaddr;
   }
   return boards;
}

const std::string TAGMcommunicator::get_hostMACaddr(std::string server)
{
   if (fServer_sockfd.find(server) == fServer_sockfd.end())
      open_client_connection(server);
   std::string req("get_hostMACaddr");
   std::string netdev = get_netdev(server);
   if (netdev.size() > 0)
      req += " " + netdev;
   std::string resp(request_response(req, server));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   std::string line;
   getline(sresp, line);
   return line;
}

bool TAGMcommunicator::ramp()
{
   select();
   std::string resp(request_response(std::string("ramp")));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   else if (resp.find("ok") == 0) 
      return true;
   else
      return false;
}

bool TAGMcommunicator::reset()
{
   select();
   std::string resp(request_response("reset"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   else if (resp.find("ok") == 0) 
      return true;
   else
      return false;
}

const unsigned char TAGMcommunicator::get_Geoaddr()
{
   select();
   std::string resp(request_response("get_Geoaddr"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   unsigned char geoaddr;
   if (sscanf(resp.c_str(), "%hhx", &geoaddr) == 1)
      return geoaddr;
   else
      return 0;
}

const unsigned char *TAGMcommunicator::get_MACaddr()
{
   select();
   std::string resp(request_response("get_MACaddr"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   sscanf(resp.c_str(), "%2hhx.%2hhx.%2hhx.%2hhx.%2hhx.%2hhx",
                      &fMACaddr[0], &fMACaddr[1], &fMACaddr[2],
                      &fMACaddr[3], &fMACaddr[4], &fMACaddr[5]);
   return fMACaddr;
}

double TAGMcommunicator::get_Tchip()
{
   // board temperature from T sensor chip (C)
   select();
   std::string resp(request_response("get_Tchip"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double T;
   sresp >> T;
   return T;
}

double TAGMcommunicator::get_pos5Vpower()
{
   // +5V power level (V)
   select();
   std::string resp(request_response("get_pos5Vpower"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_neg5Vpower()
{
   // -5V power level (V)
   select();
   std::string resp(request_response("get_neg5Vpower"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_pos3_3Vpower()
{
   // +3.3V power level (V)
   select();
   std::string resp(request_response("get_pos3_3Vpower"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_pos1_2Vpower()
{
   // +1.2V power level (V)
   select();
   std::string resp(request_response("get_pos1_2Vpower"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_Vsumref_1()
{
   // SUMREF from preamp 1 (V)
   select();
   std::string resp(request_response("get_Vsumref_1"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_Vsumref_2()
{
   // SUMREF from preamp 2 (V)
   select();
   std::string resp(request_response("get_Vsumref_2"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_Vgainmode()
{
   // GAINMODE shared by both preamps (V)
   select();
   std::string resp(request_response("get_Vgainmode"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

int TAGMcommunicator::get_gainmode()
{
   // =0 (low) or =1 (high) or -1 (undefined)
   select();
   std::string resp(request_response("get_gainmode"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   int mode;
   sresp >> mode;
   return mode;
}

double TAGMcommunicator::get_Vtherm_1()
{
   // thermister voltage on preamp 1 (V)
   select();
   std::string resp(request_response("get_Vtherm_1"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_Vtherm_2()
{
   // thermister voltage on preamp 2 (V)
   select();
   std::string resp(request_response("get_Vtherm_2"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_Tpreamp_1()
{
   // thermister temperature on preamp 1 (C)
   select();
   std::string resp(request_response("get_Tpreamp_1"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double T;
   sresp >> T;
   return T;
}

double TAGMcommunicator::get_Tpreamp_2()
{
   // thermister temperature on preamp 2 (C)
   select();
   std::string resp(request_response("get_Tpreamp_2"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double T;
   sresp >> T;
   return T;
}

double TAGMcommunicator::get_VDAChealth()
{
   // DAC channel 31 read-back level (V)
   select();
   std::string resp(request_response("get_VDAChealth"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_VDACdiode()
{
   // DAC thermal diode voltage (V)
   select();
   std::string resp(request_response("get_VDACdiode"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::get_TDAC()
{
   // DAC internal temperature reading (C)
   select();
   std::string resp(request_response("get_TDAC"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double T;
   sresp >> T;
   return T;
}

void TAGMcommunicator::latch_status()
{
   // capture board status in state variables
   select();
   request_response("latch_status");
}

void TAGMcommunicator::passthru_status()
{
   // reset saved state from last latch_levels()
   select();
   request_response("passthru_status");
}

void TAGMcommunicator::latch_voltages()
{
   // capture board's demand voltages in state variables
   select();
   request_response("latch_voltages");
}

void TAGMcommunicator::passthru_voltages()
{
   // reset saved voltages from last latch_voltages()
   select();
   request_response("passthru_voltages");
}

double TAGMcommunicator::getV(unsigned int chan)
{
   // voltage of channel reported by board (V)
   select();
   std::stringstream sreq;
   sreq << "getV " << chan;
   std::string resp(request_response(sreq.str()));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

double TAGMcommunicator::getVnew(unsigned int chan)
{ 
   // voltage of channel to be set in next ramp (V)
   select();
   std::stringstream sreq;
   sreq << "getVnew " << chan;
   std::string resp(request_response(sreq.str()));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   double V;
   sresp >> V;
   return V;
}

void TAGMcommunicator::setV(unsigned int chan, double V)
{
   // assign voltage of channel to be set in next ramp (V)
   select();
   std::stringstream sreq;
   sreq << "setV " << chan << " " << V;
   request_response(sreq.str());
}

const unsigned char *TAGMcommunicator::get_last_packet()
{
   // return a pointer to a read-only buffer containing
   // the last packet received from the board
   select();
   std::string resp(request_response("get_last_packet"));
   if (resp.find("error") != resp.npos)
      throw std::runtime_error(resp.c_str());
   std::stringstream sresp(resp);
   memset(fPacket, 0, sizeof(fPacket));
   int n = 0;
   while (sresp.rdbuf()->in_avail() > 0) {
      unsigned char byte;
      sresp >> byte;
      fPacket[n++] = byte;
   }
   return fPacket;
}

std::string TAGMcommunicator::get_netdev(std::string server)
{
   std::size_t pos = server.find("::");
   if (pos != server.npos)
      return server.substr(pos + 2);
   else
      return std::string("");
}

void TAGMcommunicator::select()
{
   if (fSelected == this)
      return;
   std::string req("select");
   req += " " + fBoard;
   std::string netdev = get_netdev(fServer);
   if (netdev.size() > 0)
      req += " " + netdev;
   std::string resp(request_response(req));
   if (resp.find("ok") != 0) {
      char errmesg[1000];
      snprintf(errmesg, 999, "TAGMcommunicator select - %s", resp.c_str());
      throw std::runtime_error(errmesg);
   }
   fSelected = this;
}

std::string TAGMcommunicator::request_response(std::string req, 
                                               std::string server)
{
   int fd = fServer_sockfd[server];

//#define VERBOSE 1
#if VERBOSE
   std::cout << "writing message \"" << req << "\""
             << " to output fd=" << fd << std::endl;
#endif

   req += "\n";
   if (write(fd, req.c_str(), req.size()) != req.size()) {
      char errmesg[1000];
      snprintf(errmesg, 999, "TAGMcommunicator request_response - "
                             "Error writing to network socket.");
      throw std::runtime_error(errmesg);
   }
   std::string response;
   while (1) {
      int bufsize = 999;
      char buf[bufsize];
      int nb = read(fd, buf, bufsize);
      for (int i=0; i < nb; ++i)
         response += buf[i];
      if (buf[nb - 1] == 0)
         break;
   }

#if VERBOSE
   std::cout << "got back response: " << response;
#endif

   return response;
}

std::string TAGMcommunicator::request_response(std::string req)
{
   return request_response(req, fServer);
}
