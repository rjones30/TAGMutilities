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

#define RETRY_COUNT 2
#define RESPONSE_TIMEOUT_MS 2000
#define RAMP_DELAY_US 0

// The following are needed by get_hostMACaddr()
#include <errno.h>
#include <string.h>
#include <stdio.h>
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

TAGMcontroller::TAGMcontroller() {
   fInitialized = false;
}

TAGMcontroller::TAGMcontroller(unsigned char geoaddr, const char *netdev) {
   fEthernet_timeout = RESPONSE_TIMEOUT_MS;
   open_network_device(netdev);
   fInitialized = false;

   for (int i=0; i < 32; ++i) {
      fLastVoltages[i] = 0;
   }
   fVoltages_latched = false;
   fStatus_latched = false;

   // format a broadcast packet to get the board at this
   // geoaddr to respond, so we can find its MAC address
   fGeoaddr = geoaddr;
   std::string hostMAC(get_hostMACaddr(netdev));
   unsigned int mac[6];
   if (sscanf(hostMAC.c_str(), "%2x:%2x:%2x:%2x:%2x:%2x",
              &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5]) != 6)
   {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller error: "
                      "unable to get the MAC address of host "
                      "ethernet adapter %s.",
              fEthernet_device);
      throw std::runtime_error(errmsg);
   }
   for (int i = 0; i < 6; ++i) {
      fDestMACaddr[i] = 0xff;
      fSrcMACaddr[i] = (unsigned char)mac[i];
   }
   if (fetch_status() != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller error: "
                      "no response from Vbias board "
                      "at geoaddr = %2.2x",
              fGeoaddr);
      throw std::runtime_error(errmsg);
   }
   else if (fLastPacket[14] != fGeoaddr && fGeoaddr != 0xff) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller error: "
                      "probe packet broadcast for geoaddr %2.2x, "
                      "but response packet comes from geoaddr %2.2x!",
              fGeoaddr, fLastPacket[14]);
      throw std::runtime_error(errmsg);
   }
   for (int i = 0; i < 6; ++i) {
      fDestMACaddr[i] = fLastPacket[i+6];
   }

   configure_network_filters();
   fInitialized = true;
}

TAGMcontroller::TAGMcontroller(unsigned char MACaddr[6], const char *netdev) {
   fEthernet_timeout = RESPONSE_TIMEOUT_MS;
   open_network_device(netdev);
   fInitialized = false;

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
      sprintf(errmsg, "TAGMcontroller error: "
                      "unable to get the MAC address of host "
                      "ethernet adapter %s.",
              fEthernet_device);
      throw std::runtime_error(errmsg);
   }
   for (int i = 0; i < 6; ++i) {
      fDestMACaddr[i] = MACaddr[i];
      fSrcMACaddr[i] = (unsigned char)mac[i];
   }
   if (fetch_status() != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGcontroller error: "
                      "no response from Vbias board at MAC addr = "
                      "%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x\n",
              MACaddr);
      throw std::runtime_error(errmsg);
   }
   fGeoaddr = fLastPacket[14];

   configure_network_filters();
   fInitialized = true;
}

TAGMcontroller::~TAGMcontroller() {
   if (fInitialized) {
      delete [] fEthernet_device;
      pcap_close(fEthernet_fp);   
   }
}

void TAGMcontroller::open_network_device(const char *netdev) {
   fEthernet_device = new char[80];
   if (netdev != 0)
      sprintf(fEthernet_device, netdev);
   else
      sprintf(fEthernet_device, DEFAULT_NETWORK_DEVICE);
   char errbuf[PCAP_ERRBUF_SIZE];
   fEthernet_fp = pcap_open_live(fEthernet_device, 100, 0,
                                 fEthernet_timeout, errbuf);
   if (fEthernet_fp == 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller error: "
                      "unable to open the ethernet adapter, "
                      "maybe you need root permission to open %s?\n",
              fEthernet_device);
      throw std::runtime_error(errmsg);
   }
}

void TAGMcontroller::configure_network_filters() {
   char filter_string[20];
   sprintf(filter_string, "ether src %2.2X:%2.2X:%2.2X:%2.2X:%2.2X:%2.2X",
           fDestMACaddr[0], fDestMACaddr[1], fDestMACaddr[2],
           fDestMACaddr[3], fDestMACaddr[4], fDestMACaddr[5]);
   struct bpf_program pcap_filter_program;
   int res = pcap_compile(fEthernet_fp, &pcap_filter_program,
                          filter_string, 1, PCAP_NETMASK_UNKNOWN);
   if (res != 0) {
      throw std::runtime_error("TAGMcontroller error: "
                               "pcap filter refuses to compile.");
   }
   res = pcap_setfilter(fEthernet_fp, &pcap_filter_program);
   if (res != 0) {
      throw std::runtime_error("TAGMcontroller error: "
                               "pcap filter refuses to load.");
   }
   pcap_freecode(&pcap_filter_program);
}

std::map<unsigned char, std::string> TAGMcontroller::probe(const char *netdev)
{
   char defnetdev[] = DEFAULT_NETWORK_DEVICE;
   if (netdev == 0)
      netdev = defnetdev;
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_t *fp = pcap_open_live(netdev, 100, 1, RESPONSE_TIMEOUT_MS, errbuf);
   if (fp == 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller error: "
                      "unable to open the ethernet adapter, "
                      "maybe you need root permission to open %s?\n",
              netdev);
      throw std::runtime_error(errmsg);
   }
   //
   // flush any pending packets from the input buffer
   pcap_setnonblock(fp, 1, errbuf);
   u_char user[] = "C";
   int pcnt = pcap_dispatch(fp, -1, &packet_reader, user);
   pcap_setnonblock(fp, 0, errbuf);

   // send a broadcast Q-packet to solicit responses
   // from every Vbias board present on the network
   unsigned char packet[64];
   std::string hostMAC(get_hostMACaddr(netdev));
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
   if (pcap_sendpacket(fp, packet, 64) != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller error: "
                      "failure transmitting Q-packet, %s\n",
              pcap_geterr(fp));
      throw std::runtime_error(errmsg);
   }
 
   // wait for the response S-packets from each board
   std::map<unsigned char, std::string> catalog;
   for (int pcnt=0; pcnt < 999; ++pcnt) {
      pcap_pkthdr *packet_header;
      const unsigned char *packet_data;
      int resp = pcap_next_ex(fp, &packet_header, &packet_data);
      if (resp == 0) {
         break;
      }
      else if (resp < 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller error: "
                         "failure receiving response from Vbias boards, %s\n",
                 pcap_geterr(fp));
         throw std::runtime_error(errmsg);
      }
      if (packet_data[15] != 'S')
         continue;
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

const std::string TAGMcontroller::get_hostMACaddr(const char *netdev) {
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
      sprintf(errmsg, "TAGMcontroller error: "
                      "interface name %s is too long",
                      "for host MAC address lookup method.",
              netdev);
      throw std::runtime_error(errmsg);
   }

   int fd = socket(AF_UNIX,SOCK_DGRAM,0);
   if (fd == -1) {
      char errmsg[80];
      sprintf(errmsg, "TAGMcontroller error: "
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
      sprintf(errmsg, "TAGMcontroller error: "
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

bool TAGMcontroller::ramp() {
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

   // flush any pending packets from the input buffer
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_setnonblock(fEthernet_fp, 1, errbuf);
   u_char user[] = "P";
   int pcnt = pcap_dispatch(fEthernet_fp, -1, &packet_reader, user);
   pcap_setnonblock(fEthernet_fp, 0, errbuf);
   if (fInitialized && pcnt > 0)
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
      if (pcap_sendpacket(fEthernet_fp, packet, 84) != 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller error: "
                         "P-packet transmit failed, %s\n",
                 pcap_geterr(fEthernet_fp));
         throw std::runtime_error(errmsg);
      }
 
      // wait for the response D-packet
      for (int pcnt=0; pcnt < 999; ++pcnt) {
         pcap_pkthdr *packet_header;
         const unsigned char *packet_data;
         if (fInitialized && pcnt > 0) {
            std::cerr << "program saw " << pcnt 
                      << " unexpected response packets, header bytes follow:"
                      << std::endl;
            for (int n=0; n < 16; ++n) {
               char str[4];
               sprintf(str, "%2.2x ", (unsigned int)packet_data[n]);
               std::cerr << str;
            }
            std::cerr << std::endl;
         }
         int resp = pcap_next_ex(fEthernet_fp, &packet_header, &packet_data);
         if (resp == 0) {
            break;
         }
         else if (resp < 0) {
            char errmsg[99];
            sprintf(errmsg, "TAGMcontroller error: "
                            "failure receiving response from Vbias board, %s\n",
                    pcap_geterr(fEthernet_fp));
            throw std::runtime_error(errmsg);
         }
         if (packet_data[15] != 'D')
            continue;
         if (fGeoaddr != 0xff && packet_data[14] != fGeoaddr)
            continue;
         bool broadcast = true;
         bool matching = true;
         for (int i=0; i < 6; ++i) {
            if (fDestMACaddr[i] != 0xff)
               broadcast = false;
            if (packet_data[i+6] != fDestMACaddr[i])
               matching = false;
         }
         if (! (broadcast || matching))
            continue;
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
   }
   return -1;
}

bool TAGMcontroller::reset() {
   // send a R-packet, receive an S-packet from board, 
   // send a P-packet with zeros, receive a D-packet from board.

   // flush any pending packets from the input buffer
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_setnonblock(fEthernet_fp, 1, errbuf);
   u_char user[] = "R";
   int pcnt = pcap_dispatch(fEthernet_fp, -1, &packet_reader, user);
   pcap_setnonblock(fEthernet_fp, 0, errbuf);
   if (fInitialized && pcnt > 0)
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

   if (pcap_sendpacket(fEthernet_fp, packet, 64) != 0) {
      char errmsg[99];
      sprintf(errmsg, "TAGMcontroller error: "
                      "R-packet transmit failed, %s\n",
              pcap_geterr(fEthernet_fp));
      throw std::runtime_error(errmsg);
   }
 
   // wait for the response S-packet
   for (int pcnt=0; pcnt < 999; ++pcnt) {
      pcap_pkthdr *packet_header;
      const unsigned char *packet_data;
      if (fInitialized && pcnt > 0) {
         std::cerr << "reset saw " << pcnt
                   << " unexpected response packets, header bytes follow:"
                   << std::endl;
         for (int n=0; n < 16; ++n) {
            char str[4];
            sprintf(str, "%2.2x ", (unsigned int)packet_data[n]);
            std::cerr << str;
         }
         std::cerr << std::endl;
      }
      int resp = pcap_next_ex(fEthernet_fp, &packet_header, &packet_data);
      if (resp == 0) {
         break;
      }
      else if (resp < 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller error: "
                         "failure receiving response from Vbias board: %s\n",
                 pcap_geterr(fEthernet_fp));
         throw std::runtime_error(errmsg);
      }
      if (packet_data[15] != 'S')
         continue;
      if (fGeoaddr != 0xff && packet_data[14] != fGeoaddr)
         continue;
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
      if (! (broadcasting || broadcast || matching))
         continue;
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

int TAGMcontroller::fetch_status() {
   // send a Q-packet, receive an S-packet from board

   // flush any pending packets from the input buffer
   char errbuf[PCAP_ERRBUF_SIZE];
   pcap_setnonblock(fEthernet_fp, 1, errbuf);
   u_char user[] = "Q";
   int pcnt = pcap_dispatch(fEthernet_fp, -1, &packet_reader, user);
   pcap_setnonblock(fEthernet_fp, 0, errbuf);
   if (fInitialized && pcnt > 0)
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
      if (pcap_sendpacket(fEthernet_fp, packet, 64) != 0) {
         char errmsg[99];
         sprintf(errmsg, "TAGMcontroller error: "
                         "failure transmitting Q-packet, %s\n",
                 pcap_geterr(fEthernet_fp));
         throw std::runtime_error(errmsg);
      }
 
      // wait for the response S-packet
      for (int pcnt=0; pcnt < 999; ++pcnt) {
         pcap_pkthdr *packet_header;
         const unsigned char *packet_data;
         if (fInitialized && pcnt > 0) {
            std::cerr << "status saw " << pcnt 
                      << " unexpected response packets, header bytes follow:"
                      << std::endl;
            for (int n=0; n < 16; ++n) {
               char str[4];
               sprintf(str, "%2.2x ", (unsigned int)packet_data[n]);
               std::cerr << str;
            }
            std::cerr << std::endl;
         }
         int resp = pcap_next_ex(fEthernet_fp, &packet_header, &packet_data);
         if (resp == 0) {
            break;
         }
         else if (resp < 0) {
            char errmsg[99];
            sprintf(errmsg, "TAGMcontroller error: "
                            "failure receiving response from Vbias board, %s\n",
                    pcap_geterr(fEthernet_fp));
            throw std::runtime_error(errmsg);
         }
         if (packet_data[15] != 'S')
            continue;
         if (fGeoaddr != 0xff && packet_data[14] != fGeoaddr)
            continue;
         bool broadcast = true;
         bool matching = true;
         for (int i=0; i < 6; ++i) {
            if (fDestMACaddr[i] != 0xff)
               broadcast = false;
            if (packet_data[i+6] != fDestMACaddr[i])
               matching = false;
         }
         if (! (broadcast || matching))
            continue;
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
{ }
