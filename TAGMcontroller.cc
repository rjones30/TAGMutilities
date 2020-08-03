//
// Class implementation: TAGMcontroller
//
// Purpose: represents a single Vbias control board for the 
//          GlueX tagger microscope readout electronics
//
// All communication with the frontend Vbias boards is done using
// raw ethernet packets over the specified interface. The boards
// are identified by either their geographical address set by
// jumpers on the readout backplane, or else by the MAC address
// of the board itself.
//
// Requires the PCAP library for access to the ethernet
// network transport layer.
//

#include "TAGMcontroller.h"
#include <iostream>
#include <stdexcept>
#include <sstream>
#include <fstream>
#include <ctime>

#define RETRY_COUNT 3
#define PROBE_TIMEOUT_MS 2000
#define RESET_TIMEOUT_MS 2000
#define STATUS_TIMEOUT_MS 1000
#define READ_TIMEOUT_MS 1000
#define RAMP_DELAY_US 1000
#define PRESEND_DELAY_US 1000

// The following are needed by get_hostMACaddr()
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <net/if_arp.h>

double TAGMcontroller::fADC_Vref = 2.5;
double TAGMcontroller::fDAC_Vref = 3.3;
double TAGMcontroller::fDACdiode_Vf = 0.650;
double TAGMcontroller::fDACdiode_Tref = 25.0;
double TAGMcontroller::fDACdiode_Tcoef = -0.0022;
double TAGMcontroller::fTcoef_therm[5] = {142.973,
                                          -34.6419,
                                            2.62172,
                                           -0.167948,
                                            0.00531447};

long int TAGMcontroller::max_logfile_size = 100000000;
std::ofstream TAGMcontroller::logfile;

TAGMcontroller::TAGMcontroller()
 : fEthernet_fp(0),
   fEthernet_timeout(0)
{
}

TAGMcontroller::TAGMcontroller(unsigned char geoaddr, const char *netdev)
 : fEthernet_fp(0),
   fEthernet_timeout(0)
{
   fEthernet_device = (netdev)? netdev : DEFAULT_NETWORK_DEVICE;
   open_network_device(PROBE_TIMEOUT_MS);

   for (int i=0; i < 32; ++i) {
      fLastVoltages[i] = 0;
   }
   fVoltages_latched = false;
   fStatus_latched = false;

   // format a broadcast packet to get the board at this
   // geoaddr to respond, so we can find its MAC address
   fGeoaddr = geoaddr;
   std::string hostMAC(get_hostMACaddr(fEthernet_device.c_str()));
   unsigned int mac[6];
   if (sscanf(hostMAC.c_str(), "%2x:%2x:%2x:%2x:%2x:%2x",
              &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5]) != 6)
   {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::TAGMcontroller error: "
                      "unable to get the MAC address of host "
                      "ethernet adapter %s.",
              fEthernet_device.c_str());
      throw std::runtime_error(errmsg);
   }
   for (int i = 0; i < 6; ++i) {
      fDestMACaddr[i] = 0xff;
      fSrcMACaddr[i] = (unsigned char)mac[i];
   }
   if (fetch_status() != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::TAGMcontroller error: "
                      "no response from Vbias board "
                      "at geoaddr = %2.2x",
              fGeoaddr);
      throw std::runtime_error(errmsg);
   }
   else if (fLastPacket[14] != fGeoaddr && fGeoaddr != 0xff) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::TAGMcontroller error: "
                      "probe packet broadcast for geoaddr %2.2x, "
                      "but response packet comes from geoaddr %2.2x!",
              fGeoaddr, fLastPacket[14]);
      throw std::runtime_error(errmsg);
   }
   for (int i = 0; i < 6; ++i) {
      fDestMACaddr[i] = fLastPacket[i+6];
   }

   configure_network_filters();
}

TAGMcontroller::TAGMcontroller(unsigned char MACaddr[6], const char *netdev)
 : fEthernet_fp(0),
   fEthernet_timeout(0)
{
   fEthernet_device = (netdev)? netdev : DEFAULT_NETWORK_DEVICE;
   open_network_device(PROBE_TIMEOUT_MS);

   for (int i=0; i < 32; ++i) {
      fLastVoltages[i] = 0;
   }
   fVoltages_latched = false;
   fStatus_latched = false;

   // send a probe packet to this Vbias board
   // and look in response packet for its geoaddr
   fGeoaddr = 0xff;
   std::string hostMAC(get_hostMACaddr(netdev));
   unsigned int mac[6];
   if (sscanf(hostMAC.c_str(), "%2x:%2x:%2x:%2x:%2x:%2x",
              &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5]) != 6)
   {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::TAGMcontroller error: "
                      "unable to get the MAC address of host "
                      "ethernet adapter %s.",
              fEthernet_device.c_str());
      throw std::runtime_error(errmsg);
   }
   for (int i = 0; i < 6; ++i) {
      fDestMACaddr[i] = MACaddr[i];
      fSrcMACaddr[i] = (unsigned char)mac[i];
   }
   if (fetch_status() != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGcontroller::TAGMcontroller error: "
                      "no response from Vbias board at MAC addr = "
                      "%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x\n",
              MACaddr);
      throw std::runtime_error(errmsg);
   }
   fGeoaddr = fLastPacket[14];

   configure_network_filters();
}

TAGMcontroller::~TAGMcontroller()
{
   if (fEthernet_fp)
      pcap_close(fEthernet_fp);
}

void TAGMcontroller::open_network_device(int timeout_ms)
{
   if (timeout_ms == fEthernet_timeout)
      return;
   else if (fEthernet_fp)
      pcap_close(fEthernet_fp);
   fEthernet_timeout = timeout_ms;
   char errbuf[PCAP_ERRBUF_SIZE];
   fEthernet_fp = pcap_open_live(fEthernet_device.c_str(), 100, 1,
                                 fEthernet_timeout, errbuf);
   if (fEthernet_fp == 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::open_network_device error: "
                      "unable to open the ethernet adapter, "
                      "maybe you need root permission to open %s?\n",
              fEthernet_device.c_str());
      throw std::runtime_error(errmsg);
   }
}

void TAGMcontroller::configure_network_filters()
{
   char filter_string[20];
   sprintf(filter_string, "ether src %2.2X:%2.2X:%2.2X:%2.2X:%2.2X:%2.2X",
           fDestMACaddr[0], fDestMACaddr[1], fDestMACaddr[2],
           fDestMACaddr[3], fDestMACaddr[4], fDestMACaddr[5]);
   struct bpf_program pcap_filter_program;
   int res = pcap_compile(fEthernet_fp, &pcap_filter_program,
                          filter_string, 1, PCAP_NETMASK_UNKNOWN);
   if (res != 0) {
      throw std::runtime_error("TAGMcontroller::configure_network_filters"
                               "error: pcap filter refuses to compile.");
   }
   res = pcap_setfilter(fEthernet_fp, &pcap_filter_program);
   if (res != 0) {
      throw std::runtime_error("TAGMcontroller::configure_network_filters"
                               " error: pcap filter refuses to load.");
   }
   pcap_freecode(&pcap_filter_program);
}

std::map<unsigned char, std::string> TAGMcontroller::probe(const char *netdev)
{
   char defnetdev[] = DEFAULT_NETWORK_DEVICE;
   if (netdev == 0)
      netdev = defnetdev;
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_t *fp = pcap_open_live(netdev, 100, 1, PROBE_TIMEOUT_MS, errbuf);
   if (fp == 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::probe error: "
                      "unable to open the ethernet adapter, "
                      "maybe you need root permission to open %s?\n",
              netdev);
      throw std::runtime_error(errmsg);
   }
   std::map<unsigned char, std::string> result;
   std::string hostMAC(get_hostMACaddr(netdev));
   result = probe(fp, hostMAC);
   pcap_close(fp);
   return result;
}

std::map<unsigned char, std::string> TAGMcontroller::probe(pcap_t *fp, std::string hostMAC)
{
   // flush any pending packets from the input buffer
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_setnonblock(fp, 1, errbuf);
   u_char user[] = "C";
   int pcnt = pcap_dispatch(fp, -1, &packet_reader, user);
   pcap_setnonblock(fp, 0, errbuf);

   // send a broadcast Q-packet to solicit responses
   // from every Vbias board present on the network
   unsigned char packet[64];
   unsigned int mac[6];
   sscanf(hostMAC.c_str(), "%2x:%2x:%2x:%2x:%2x:%2x",
          &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5]);
   for (int i = 0; i < 6; ++i) {
      packet[i] = 0xff;
      packet[i+6] = (unsigned char)mac[i];
   }
   packet[12] = 0;
   packet[13] = 50;
   packet[14] = 0xff;
   packet[15] = 'Q';
   log_packet("TAGMcontroller::probe is broadcasting a Q request"
              " to all front-end boards", packet);
   if (PRESEND_DELAY_US > 0)
      usleep(PRESEND_DELAY_US);
   if (pcap_sendpacket(fp, packet, 64) != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::probe error: "
                      "failure transmitting Q-packet, %s\n",
              pcap_geterr(fp));
      log_packet(errmsg, packet);
      throw std::runtime_error(errmsg);
   }
 
   // wait for the response S-packets from each board
   std::map<unsigned char, std::string> catalog;
   int heartbeat = 0;
   for (int pcnt=0; pcnt < 999; ++pcnt) {
      pcap_pkthdr *packet_header;
      const unsigned char *packet_data;
      int resp = pcap_next_ex(fp, &packet_header, &packet_data);
      if (resp == 0) {
         log_packet("TAGMcontroller:probe exits, timeout reached.",
                    0, packet);
         break;
      }
      else if (resp < 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller::probe error: "
                         "failure receiving response from Vbias boards, %s\n",
                 pcap_geterr(fp));
         log_packet(errmsg, 0, packet);
         throw std::runtime_error(errmsg);
      }
      if (packet_data[15] != 'S') {
         log_packet("TAGMcontroller:probe error:"
                    " received unexpected packet:", packet_data, packet);
         if (++heartbeat > 5)
            break;
         continue;
      }
      log_packet("TAGMcontroller:probe received expected response:",
                 packet_data, packet);
      bool broadcasting = true;
      for (int i=0; i < 6; ++i) {
         if (packet_data[i+6] != 0xff)
            broadcasting = false;
      }
      if (broadcasting)
         continue;
      unsigned char geoaddr = packet_data[14];
      char MACaddr[25];
      sprintf(MACaddr, "%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x",
              packet_data[6], packet_data[7], packet_data[8],
              packet_data[9], packet_data[10], packet_data[11]);
      catalog[geoaddr] = std::string(MACaddr);
   }
   return catalog;
}

const std::string TAGMcontroller::get_hostMACaddr(const char *netdev)
{
   // return the host MAC address encoded as a string

   struct ifreq ifr;
   char defnetdev[] = DEFAULT_NETWORK_DEVICE;
   if (netdev == 0)
      netdev = defnetdev;
   size_t devname_len = strlen(netdev);
   if (devname_len < sizeof(ifr.ifr_name)) {
      memcpy(ifr.ifr_name, netdev, devname_len);
      ifr.ifr_name[devname_len] = 0;
   }
   else {
      char errmsg[80];
      sprintf(errmsg, "TAGMcontroller::get_hostMACaddr error: "
                      "interface name %s is too long",
                      "for host MAC address lookup method.",
              netdev);
      throw std::runtime_error(errmsg);
   }

   int fd = socket(AF_UNIX,SOCK_DGRAM,0);
   if (fd == -1) {
      char errmsg[80];
      sprintf(errmsg, "TAGMcontroller::get_hostMACaddr error: "
                      "failed to open ethernet socket on device %s.",
              netdev);
      throw std::runtime_error(errmsg);
   }
   if (ioctl(fd,SIOCGIFHWADDR,&ifr) == -1) {
      int temp_errno = errno;
      close(fd);
      throw std::runtime_error(strerror(temp_errno));
   }
   else if (ifr.ifr_hwaddr.sa_family != ARPHRD_ETHER) {
      char errmsg[80];
      sprintf(errmsg, "TAGMcontroller::get_hostMACaddr error: "
                      "%s is not an ethernet interface.",
              netdev);
      throw std::runtime_error(errmsg);
   }
   char MACaddr[25];
   sprintf(MACaddr, "%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x",
           (unsigned char)ifr.ifr_hwaddr.sa_data[0],
           (unsigned char)ifr.ifr_hwaddr.sa_data[1],
           (unsigned char)ifr.ifr_hwaddr.sa_data[2],
           (unsigned char)ifr.ifr_hwaddr.sa_data[3],
           (unsigned char)ifr.ifr_hwaddr.sa_data[4],
           (unsigned char)ifr.ifr_hwaddr.sa_data[5]);
   return std::string(MACaddr);
}

bool TAGMcontroller::ramp()
{
   // push the new voltages to the board, if any
 
   if (fNextVoltages.size() == 0)
      return true;
   if (fetch_voltages() != 0)
      return false;

   unsigned int target_values[32];
   for (int chan=0; chan < 32; ++chan)
      if (fNextVoltages.find(chan) != fNextVoltages.end())
         target_values[chan] = fNextVoltages[chan];
      else
         target_values[chan] = fLastVoltages[chan];

   int max_delta_allowed = 10; // max DAC code change in one step, ~100mV
   int steps;
   for (steps = 0; steps < 9999; ++steps) {
      unsigned int next_mask = 0;
      unsigned int next_values[32];
      for (int chan=0; chan < 32; ++chan) {
         int delta = target_values[chan] - fLastVoltages[chan];
         delta = (delta > +max_delta_allowed)? max_delta_allowed :
                 (delta < -max_delta_allowed)? -max_delta_allowed : delta;
         if (delta != 0) {
            next_values[chan] = fLastVoltages[chan] + delta;
            next_mask |= (1 << chan);
         }
      }

      if (next_mask == 0)
         return true;
      else if (set_voltages(next_mask, next_values) != 0)
         break;
      else if (RAMP_DELAY_US > 0)
         usleep(RAMP_DELAY_US);
   }
   return false;
}

int TAGMcontroller::set_voltages(unsigned int mask, unsigned int values[32])
{
   // send a P-packet, receive

   open_network_device(READ_TIMEOUT_MS);

   // flush any pending packets from the input buffer
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_setnonblock(fEthernet_fp, 1, errbuf);
   u_char user[] = "P";
   int pcnt = pcap_dispatch(fEthernet_fp, -1, &packet_reader, user);
   pcap_setnonblock(fEthernet_fp, 0, errbuf);
   if (pcnt > 0)
      std::cerr << "program saw " << pcnt << " unrequested packets"
                << std::endl;
   
   // send out the P-packet
   unsigned char packet[84];
   for (int i=0; i < 6; i++) {
      packet[i] = fDestMACaddr[i];
      packet[i+6] = fSrcMACaddr[i];
   }
   packet[12] = 0;
   packet[13] = 70;
   packet[14] = fGeoaddr;
   packet[15] = 'P';
   packet[16] = mask  & 0xff;
   packet[17] = (mask >> 8) & 0xff;
   packet[18] = (mask >> 16) & 0xff;
   packet[19] = (mask >> 24) & 0xff;
   for (int i=0; i < 32; ++i) {
      packet[2*i+20] = (values[i] >> 8) & 0xff;
      packet[2*i+21] = values[i] & 0xff;
   }

   for (int retry=0; retry < RETRY_COUNT; ++retry) {
      log_packet("TAGMcontroller::set_voltages sends request packet:",
                 packet);
      if (PRESEND_DELAY_US > 0)
         usleep(PRESEND_DELAY_US);
      if (pcap_sendpacket(fEthernet_fp, packet, 84) != 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller::set_voltages error: "
                         "P-packet transmit failed, %s\n",
                 pcap_geterr(fEthernet_fp));
         log_packet(errmsg, 0, packet);
         throw std::runtime_error(errmsg);
      }
 
      // wait for the response D-packet
      for (int pcnt=0; pcnt < 999; ++pcnt) {
         pcap_pkthdr *packet_header;
         const unsigned char *packet_data;
         if (pcnt > 0) {
            std::cerr << "program saw " << pcnt 
                      << " unexpected response packets, header bytes follow:"
                      << std::endl;
            for (int n=0; n < 16; ++n) {
               char str[4];
               sprintf(str, "%2.2x ", (unsigned int)packet_data[n]);
               std::cerr << str;
            }
            std::cerr << std::endl;
            log_packet("TAGMcontroller::set_voltages error:"
                       " saw unexpected response packet:", packet_data, packet);
         }
         int resp = pcap_next_ex(fEthernet_fp, &packet_header, &packet_data);
         if (resp == 0) {
            log_packet("TAGMcontroller::set_voltages response error:"
                       " no packets received within timeout.", 0, packet);
            break;
         }
         else if (resp < 0) {
            char errmsg[99];
            sprintf(errmsg, "TAGMcontroller::set_voltages error: "
                            "failure receiving response from Vbias board, %s\n",
                    pcap_geterr(fEthernet_fp));
            log_packet(errmsg, 0, packet);
            throw std::runtime_error(errmsg);
         }
         if (packet_data[15] != 'D') {
            log_packet("TAGMcontroller::set_voltages error:"
                       " received unexpected response:", packet_data, packet);
            continue;
         }
         if (fGeoaddr != 0xff && packet_data[14] != fGeoaddr) {
            log_packet("TAGMcontroller::set_voltages error:"
                       " received response from unexpected source:",
                       packet_data, packet);
            continue;
         }
         bool broadcast = true;
         bool matching = true;
         for (int i=0; i < 6; ++i) {
            if (fDestMACaddr[i] != 0xff)
               broadcast = false;
            if (packet_data[i+6] != fDestMACaddr[i])
               matching = false;
         }
         if (! (broadcast || matching)) {
            log_packet("TAGMcontroller::set_voltages error:"
                       " response consistency check failed:",
                       packet_data, packet);
            continue;
         }
         else {
            log_packet("TAGMcontroller::set_voltages received expected"
                       " response:", packet_data, packet);
         }
 
         // verify the values sent back and
         // throw an exception on mismatch
         for (int i=0; i < 32; ++i) {
            if ((mask & (1 << i)) == 0)
               continue;
            if (packet_data[16 + 2*i] != packet[20 + 2*i] ||
                packet_data[17 + 2*i] != packet[21 + 2*i])
            {
               char errmsg[99];
               sprintf(errmsg, "TAGMcontroller::set_voltages error:"
                       " mismatch between Vbias values requested and read back!");
               log_packet("TAGMcontroller::set_voltages error:"
                          " mismatch between expected and readback voltages,"
                          "resetting the card, and aborting...");
               reset();
               throw std::runtime_error(errmsg);
            }
         }

         int packet_len = packet_data[13] + 14;
         for (int i=0; i < packet_len; ++i)
            fLastPacket[i] = packet_data[i];
         for (int i=0; i < 32; ++i) {
            unsigned int byte1 = (unsigned int)packet_data[2*i+16];
            unsigned int byte2 = (unsigned int)packet_data[2*i+17];
            fLastVoltages[i] = (byte1 << 8) + byte2;
         }
         return 0;
      }
      std::stringstream msg;
      msg << "TAGMcontroller::set_voltages retry count is " << retry;
      log_packet(msg.str());
   }
   return -1;
}

bool TAGMcontroller::reset()
{
   // send a R-packet, receive an S-packet from board, 
   // send a P-packet with zeros, receive a D-packet from board.

   open_network_device(RESET_TIMEOUT_MS);

   // flush any pending packets from the input buffer
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_setnonblock(fEthernet_fp, 1, errbuf);
   u_char user[] = "R";
   int pcnt = pcap_dispatch(fEthernet_fp, -1, &packet_reader, user);
   pcap_setnonblock(fEthernet_fp, 0, errbuf);
   if (pcnt > 0)
      std::cerr << "reset saw " << pcnt << " unrequested packets"
                << std::endl;
   
   // send out an R-packet
   unsigned char packet[64];
   for (int i=0; i < 6; i++) {
      packet[i] = fDestMACaddr[i];
      packet[i+6] = fSrcMACaddr[i];
   }
   packet[12] = 0;
   packet[13] = 50;
   packet[14] = fGeoaddr;
   packet[15] = 'R';
   for (int i=16; i < 64; ++i) {
      packet[i] = 0;
   }

   log_packet("TAGMcontroller::reset sends request:", packet);
   if (PRESEND_DELAY_US > 0)
      usleep(PRESEND_DELAY_US);
   if (pcap_sendpacket(fEthernet_fp, packet, 64) != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller::reset error: "
                      "R-packet transmit failed, %s\n",
              pcap_geterr(fEthernet_fp));
      log_packet(errmsg, 0, packet);
      throw std::runtime_error(errmsg);
   }
 
   // wait for the response S-packet
   for (int pcnt=0; pcnt < 999; ++pcnt) {
      pcap_pkthdr *packet_header;
      const unsigned char *packet_data;
      if (pcnt > 0) {
         std::cerr << "reset saw " << pcnt
                   << " unexpected response packets, header bytes follow:"
                   << std::endl;
         for (int n=0; n < 16; ++n) {
            char str[4];
            sprintf(str, "%2.2x ", (unsigned int)packet_data[n]);
            std::cerr << str;
         }
         std::cerr << std::endl;
         log_packet("TAGMcontroller::reset error:"
                    " saw unexpected response packet:", packet_data, packet);
      }
      int resp = pcap_next_ex(fEthernet_fp, &packet_header, &packet_data);
      if (resp == 0) {
         log_packet("TAGMcontroller::reset response error:"
                    " no packets received within timeout!", 0, packet);
         break;
      }
      else if (resp < 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller::reset error: "
                         "failure receiving response from Vbias board: %s\n",
                 pcap_geterr(fEthernet_fp));
         log_packet(errmsg, 0, packet);
         throw std::runtime_error(errmsg);
      }
      if (packet_data[15] != 'S') {
         log_packet("TAGMcontroller::reset error:"
                    " saw unexpected response packet:", packet_data, packet);
         continue;
      }
      if (fGeoaddr != 0xff && packet_data[14] != fGeoaddr) {
         log_packet("TAGMcontroller::reset error:"
                    " saw response packet from unexpected source:",
                    packet_data, packet);
         continue;
      }
      bool broadcast = true;
      bool matching = true;
      bool broadcasting = true;
      for (int i=0; i < 6; ++i) {
         if (fDestMACaddr[i] != 0xff)
             broadcast = false;
         if (packet_data[i+6] != fDestMACaddr[i])
             matching = false;
         if (packet_data[i] != 0xff)
             broadcasting = false;
      }
      if (! (broadcasting || broadcast || matching)) {
         log_packet("TAGMcontroller::reset error:"
                    " response consistency check failed:",
                    packet_data, packet);
         continue;
      }
      else {
         log_packet("TAGMcontroller::reset received expected response:",
                    packet_data, packet);
      }
      int packet_len = packet_data[13] + 14;
      for (int i=0; i < packet_len; ++i)
         fLastPacket[i] = packet_data[i];
      for (int i=0; i < 17; ++i) {
         unsigned int byte1 = (unsigned int)packet_data[2*i+16];
         unsigned int byte2 = (unsigned int)packet_data[2*i+17];
         fLastStatus[i] = (byte1 << 8) + byte2;
      }
      break;
   }

   // If the host is outside the ethernet broadcast domain of the board
   // then the initial S-packet will not be seen. That is ok if we can
   // query the board directly for its status. Do that here just in case.
   if (fetch_status() != 0)
      return false;

   // A hard reset does not zero the FPGA voltage registers
   // but it does reset the DAC, so set the FPGA registers to zero.
   unsigned int zeros[32];
   for (int i=0; i < 32; i++)
      zeros[i] = 0;
   return (set_voltages(0xffffffff, zeros) == 0);
}

int TAGMcontroller::fetch_status()
{
   // send a Q-packet, receive an S-packet from board

   open_network_device(STATUS_TIMEOUT_MS);

   // flush any pending packets from the input buffer
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_setnonblock(fEthernet_fp, 1, errbuf);
   u_char user[] = "Q";
   int pcnt = pcap_dispatch(fEthernet_fp, -1, &packet_reader, user);
   pcap_setnonblock(fEthernet_fp, 0, errbuf);
   if (pcnt > 0)
      std::cerr << "status saw " << pcnt << " unrequested packets"
                << std::endl;
   
   // send out a Q-packet
   unsigned char packet[64];
   for (int i=0; i < 6; i++) {
      packet[i] = fDestMACaddr[i];
      packet[i+6] = fSrcMACaddr[i];
   }
   packet[12] = 0;
   packet[13] = 50;
   packet[14] = fGeoaddr;
   packet[15] = 'Q';
   for (int i=16; i < 64; ++i) {
      packet[i] = 0;
   }
   for (int retry=0; retry < RETRY_COUNT; ++retry) {
      log_packet("TAGMcontroller::fetch_status sends request packet:", packet);
      if (PRESEND_DELAY_US > 0)
         usleep(PRESEND_DELAY_US);
      if (pcap_sendpacket(fEthernet_fp, packet, 64) != 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller::fetch_status error: "
                         "failure transmitting Q-packet, %s\n",
                 pcap_geterr(fEthernet_fp));
         log_packet(errmsg, 0, packet);
         throw std::runtime_error(errmsg);
      }
 
      // wait for the response S-packet
      for (int pcnt=0; pcnt < 999; ++pcnt) {
         pcap_pkthdr *packet_header;
         const unsigned char *packet_data;
         if (pcnt > 0) {
            std::cerr << "status saw " << pcnt 
                      << " unexpected response packets, header bytes follow:"
                      << std::endl;
            for (int n=0; n < 16; ++n) {
               char str[4];
               sprintf(str, "%2.2x ", (unsigned int)packet_data[n]);
               std::cerr << str;
            }
            std::cerr << std::endl;
            log_packet("TAGMcontroller::fetch_status error:"
                       " saw unexpected response packet:", packet_data, packet);
         }
         int resp = pcap_next_ex(fEthernet_fp, &packet_header, &packet_data);
         if (resp == 0) {
            log_packet("TAGMcontroller::fetch_status response error:"
                       " no packets received within timeout", 0, packet);
            break;
         }
         else if (resp < 0) {
            char errmsg[99];
            sprintf(errmsg, "TAGMcontroller::fetch_status error: "
                            "failure receiving response from Vbias board, %s\n",
                    pcap_geterr(fEthernet_fp));
            throw std::runtime_error(errmsg);
         }
         if (packet_data[15] != 'S') {
            log_packet("TAGMcontroller::fetch_status error:"
                       " saw unexpected response packet:", packet_data, packet);
            continue;
         }
         if (fGeoaddr != 0xff && packet_data[14] != fGeoaddr) {
            log_packet("TAGMcontroller::fetch_status error:"
                       " response received from unexpected source:",
                       packet_data, packet);
            continue;
         }
         bool broadcast = true;
         bool matching = true;
         for (int i=0; i < 6; ++i) {
            if (fDestMACaddr[i] != 0xff)
               broadcast = false;
            if (packet_data[i+6] != fDestMACaddr[i])
               matching = false;
         }
         if (! (broadcast || matching)) {
            log_packet("TAGMcontroller::fetch_status error:"
                       " saw unexpected response packet:", packet_data, packet);
            continue;
         }
         else {
            log_packet("TAGMcontroller::fetch_status received expected response:",
                       packet_data, packet);
         }
         int packet_len = packet_data[13] + 14;
         for (int i=0; i < packet_len; ++i)
            fLastPacket[i] = packet_data[i];
         for (int i=0; i < 17; ++i) {
            unsigned int byte1 = (unsigned int)packet_data[2*i+16];
            unsigned int byte2 = (unsigned int)packet_data[2*i+17];
            fLastStatus[i] = (byte1 << 8) + byte2;
         }
         return 0;
      }
   }
   return -1;
}

void TAGMcontroller::packet_reader(unsigned char *user,
                                   const struct pcap_pkthdr *h,
                                   const u_char *bytes)
{
   std::stringstream msg;
   msg << "TAGMcontroller::packet_reader received unexpected packet,"
       << " while setting up to send a " << user[0] << " packet request";
   log_packet(msg.str(), bytes);
}

void TAGMcontroller::log_packet(std::string msg, 
                                const unsigned char *packet,
                                const unsigned char *refpacket)
{
   if (!logfile) {
      logfile.open("/tmp/TAGMcontroller.log", std::ios_base::app);
      if (!logfile) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller::log_packet error:"
                         "cannot open logfile /tmp/TAGMcontroller.log");
         throw std::runtime_error(errmsg);
      }
   }
   logfile.seekp(0, std::ios_base::end);
   long int len = logfile.tellp();
   if (len > max_logfile_size) {
      logfile.close();
      rename("/tmp/TAGMcontroller.log", "/tmp/TAGMcontroller.log.old");
      return log_packet(msg, packet, refpacket);
   }

   time_t rawtime;
   struct tm * timeinfo;
   char timebuffer[80];
   time(&rawtime);
   timeinfo = localtime(&rawtime);
   strftime(timebuffer, sizeof(timebuffer),"%d-%m-%Y %H:%M:%S", timeinfo);
   std::string timestr(timebuffer);
   if (packet == 0) {
      logfile << timestr << " " << msg << std::endl;
      return;
   }

   int geoaddr = packet[14];
   char destaddr[30];
   char srcaddr[30];
   if (geoaddr == 0xff) {
      sprintf(destaddr, "0xff (broadcast)");
      sprintf(srcaddr, "0x?? (%02x:%02x:%02x:%02x:%02x:%02x)",
              packet[6], packet[7], packet[8],
              packet[9], packet[10], packet[11]);
   }
   else {
      sprintf(destaddr, "0x%02x (%02x:%02x:%02x:%02x:%02x:%02x)",
              geoaddr, packet[0], packet[1], packet[2],
              packet[3], packet[4], packet[5]);
      sprintf(srcaddr, "0x%02x (%02x:%02x:%02x:%02x:%02x:%02x)",
              geoaddr, packet[6], packet[7], packet[8],
              packet[9], packet[10], packet[11]);
   }
   if (packet) {
      char type = packet[15];
      if (type == 'R') {
         logfile << timestr << " " << msg << std::endl
                 << "  request packet type R (hard reset)"
                 << " to card " << destaddr << std::endl;
      }
      else if (type == 0xd5) {
         logfile << timestr << " " << msg << std::endl
                 << "  request packet type R' (soft reset)"
                 << " to card " << destaddr << std::endl;
      }
      else if (type == 'Q') {
         logfile << timestr << " " << msg << std::endl
                 << "  request packet type Q (card state)"
                 << " to card " << destaddr << std::endl;
      }
      else if (type == 'S') {
         logfile << "  response packet type S (card state)"
                 << " from card " << srcaddr << std::endl;
         int tempval = (packet[16] << 8) + packet[17];
         double tempC = tempval * 0.25;
         logfile << "    temperature = " << tempC << " C" << std::endl;
         for (int i=0; i < 16; ++i) {
            char a[30];
            sprintf(a, "    adc[%x]=0x%03x", i,
                         packet[19 + i*2] + (packet[18 + i*2] & 0xf));
            logfile << a;
            if (i % 4 == 3)
               logfile << std::endl;
         }
      }
      else if (type == 'P') {
         logfile << timestr << " " << msg << std::endl
                 << "  request packet type P (set/get Vbias values)"
                 << " to card " << destaddr << std::endl;
         long int mask = packet[16] + (packet[17] << 8) +
                         (packet[18] << 16) + (packet[19] << 24);
         int n=0;
         std::stringstream updates;
         for (int i=0; i < 32; ++i) {
            if (mask & (1 << i)) {
               char a[30];
               sprintf(a, "    V[%02x]=0x%04x", i,
                       (packet[20 +i*2] << 8) + packet[21 + i*2]);
               updates << a;
               if (n % 4 == 3)
                  updates << std::endl;
               ++n;
            }
         }
         logfile << "    " << n << " updated values requested" << std::endl;
         if (n > 0) {
            logfile << updates.str();
            if (n % 4 != 0)
               logfile << std::endl;
         }
      }
      else if (type == 'D') {
         logfile << "  response packet type D (Vbias readback)"
                 << " from card " << srcaddr;
         long int mask = 0;
         if (refpacket) {
            mask = refpacket[16] + (refpacket[17] << 8) +
                   (refpacket[18] << 16) + (refpacket[19] << 24);
            char a[30];
            sprintf(a, ", using write mask 0x%08x", (unsigned int)mask);
            logfile << a;
         }
         logfile << std::endl;
         for (int i=0; i < 32; ++i) {
            char a[30];
            unsigned int V = (packet[16 +i*2] << 8) + packet[17 + i*2];
            sprintf(a, "    V[%02x]=0x%04x", i, V);
            logfile << a;
            if (refpacket) {
               int Vref = (refpacket[20 +i*2] << 8) + refpacket[21 + i*2];
               if (mask & (1 << i)) {
                  if (V == Vref)
                     logfile << "(good)";
                  else
                     logfile << "(BAD!)";
               }
            }
            if (i % 4 == 3)
               logfile << std::endl;
         }
      }
      else {
         logfile << "  unrecognized packet received from " << srcaddr
                 << " to " << destaddr << std::endl;
         for (int i=0; i < 8; ++i) {
            char a[30];
            sprintf(a, "    0x04%x", packet[12 + i]);
            logfile << a;
         }
         logfile << std::endl;
      }
   }
}
