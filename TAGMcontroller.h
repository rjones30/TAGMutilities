//
// Class TAGMcontroller
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

#ifndef TAGMCONTROLLER_H
#define TAGMCONTROLLER_H

#define DEFAULT_NETWORK_DEVICE "em2"

extern "C" {
#include <pcap.h>
}

#include <map>
#include <math.h>
#include <iostream>
#include <string>

class TAGMcontroller {
 public:
   TAGMcontroller(unsigned char geoaddr, const char *netdev=0);
   TAGMcontroller(unsigned char MACaddr[6], const char *netdev=0);
   virtual ~TAGMcontroller();

   static std::map<unsigned char, std::string> probe(const char *netdev=0);  // retrieve a list of all Vbias boards that respond to a broadcast query
   static const std::string  get_hostMACaddr(const char *netdev=0);  // get the ethernet MAC address of host interface
   virtual const unsigned char get_Geoaddr();   // get the backplane slot address of this board
   virtual const unsigned char *get_MACaddr();  // get the ethernet MAC address of this board

   virtual double get_Tchip();         // board temperature from T sensor chip (C)
   virtual double get_pos5Vpower();    // +5V power level (V)
   virtual double get_neg5Vpower();    // -5V power level (V)
   virtual double get_pos3_3Vpower();  // +3.3V power level (V)
   virtual double get_pos1_2Vpower();  // +1.2V power level (V)
   virtual double get_Vsumref_1();     // SUMREF from preamp 1 (V)
   virtual double get_Vsumref_2();     // SUMREF from preamp 2 (V)
   virtual double get_Vgainmode();     // GAINMODE shared by both preamps (V)
   virtual int get_gainmode();         // =0 (low) or =1 (high) or =-1 (undefined)
   virtual double get_Vtherm_1();      // thermister voltage on preamp 1 (V)
   virtual double get_Vtherm_2();      // thermister voltage on preamp 2 (V)
   virtual double get_Tpreamp_1();     // thermister temperature on preamp 1 (C)
   virtual double get_Tpreamp_2();     // thermister temperature on preamp 2 (C)
   virtual double get_VDAChealth();    // DAC channel 31 read-back level (V)
   virtual double get_VDACdiode();     // DAC temperature diode voltage (V)
   virtual double get_TDAC();          // DAC internal temperature reading (C)

   virtual void latch_status();        // capture board status in state variables
                                       // and return captured data in response to get_XXX()
   virtual void passthru_status();     // reset saved state from last latch_levels()
                                       // and have each get_XXX() request fresh data from board
   virtual void latch_voltages();      // capture board's demand voltages in state variables
                                       // and return captured data in response to getV()
   virtual void passthru_voltages();   // reset saved voltages from last latch_voltages()
                                       // and have each getV() request fresh data from board

   virtual double getV(unsigned int chan);          // voltage of channel reported by board (V)
   virtual double getVnew(unsigned int chan);       // voltage of channel to be set in next ramp (V)
   virtual void setV(unsigned int chan, double V);  // assign voltage of channel to be set in next ramp (V)
   virtual const unsigned char *get_last_packet();  // return a pointer to a read-only buffer containing the last packet received from the board

   virtual bool ramp();                // push the new voltages to the board, if any
   virtual bool reset();               // send a hard reset to the board

 protected:
   unsigned char fGeoaddr;
   unsigned char fSrcMACaddr[6];
   unsigned char fDestMACaddr[6];
   unsigned int fLastStatus[17];
   unsigned int fLastVoltages[32];
   unsigned char fLastPacket[270];
   std::map<unsigned int, unsigned int> fNextVoltages;

   static std::map<unsigned char, std::string> probe(pcap_t *fp, std::string hostMAC);

   int set_voltages(unsigned int mask, unsigned int values[32]);
   int fetch_voltages();
   int fetch_status();
   bool fVoltages_latched;
   bool fStatus_latched;

   TAGMcontroller();               // stripped down protected constructor for derived classes

 private:
   pcap_t *fEthernet_fp;           // pointer to ethernet file descriptor
   std::string fEthernet_device;   // name of pcap interface, eg. "eth0"
   int fEthernet_timeout;          // network response timeout (ms)
   static double fADC_Vref;        // Vref of ADC on frontend Vbias boards (V)
   static double fDAC_Vref;        // Vref of DAC on frontend Vbias boards (V)
   static double fDACdiode_Vf;     // Vf for DAC diode frontend Vbias boards (V)
   static double fDACdiode_Tref;   // Tref for DAC diode frontend Vbias boards (C)
   static double fDACdiode_Tcoef;  // Tcoef for DAC diode frontend Vbias boards (V/degC)
   static double fTcoef_therm[5];  // polynomial coefficients of thermister response

   typedef void (*pcap_handler)(unsigned char *user, 
                                const struct pcap_pkthdr *h,
                                const u_char *bytes);
   static void packet_reader(unsigned char *user,
                             const struct pcap_pkthdr *h,
                             const u_char *bytes);

   void open_network_device(int timeout_ms);
   void configure_network_filters();

   static void log_packet(std::string msg,
                          const unsigned char *packet=0,
                          const unsigned char *refpacket=0);
   static std::ofstream logfile;
   static long int max_logfile_size;
};

inline const unsigned char TAGMcontroller::get_Geoaddr() {
   return fGeoaddr;
}

inline const unsigned char *TAGMcontroller::get_MACaddr() {
   return fDestMACaddr;
}

inline double TAGMcontroller::get_Tchip() {         // board temperature from T sensor chip (C)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[0]*0.25;
}

inline double TAGMcontroller::get_pos5Vpower() {    // +5V power level (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[3]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_neg5Vpower() {    // -5V power level (V)
   double R1 = 100e3;
   double R2 = 33.2e3;
   double pos5V = get_pos5Vpower();
   double Vlevel = fLastStatus[1]*1.001 * 2*fADC_Vref/(1 << 12);
   return Vlevel*(R1+R2)/R2 - pos5V*R1/R2;
}

inline double TAGMcontroller::get_pos3_3Vpower() {  // +3.3V power level (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[2]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_pos1_2Vpower() {  // +1.2V power level (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[4]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_Vsumref_1() {     // SUMREF from preamp 1 (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[13]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_Vsumref_2() {     // SUMREF from preamp 2 (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[10]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_Vgainmode() {     // GAINMODE shared by both preamps (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[11]*2.018 * 2*fADC_Vref/(1 << 12);
}

inline int TAGMcontroller::get_gainmode() {         // =0 (low) or =1 (high) or -1 (undefined)
   double Vgain = get_Vgainmode();
   return (Vgain > 4.9 && Vgain < 5.1)? 0 :
          (Vgain > 9.9 && Vgain < 10.1)? 1 : -1;
}

inline double TAGMcontroller::get_Vtherm_1() {      // thermister voltage on preamp 1 (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[16]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_Vtherm_2() {      // thermister voltage on preamp 2 (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[12]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_Tpreamp_1() {     // thermister temperature on preamp 1 (C)
   double Vtherm = get_Vtherm_1();
   bool latched = fStatus_latched;
   fStatus_latched = true;
   double pos5V = get_pos5Vpower();
   fStatus_latched = latched;
   double logVtherm = log(100*(pos5V-Vtherm)/Vtherm);
   return  ((((fTcoef_therm[4])*logVtherm +
               fTcoef_therm[3])*logVtherm +
               fTcoef_therm[2])*logVtherm +
               fTcoef_therm[1])*logVtherm +
               fTcoef_therm[0];
}

inline double TAGMcontroller::get_Tpreamp_2() {     // thermister temperature on preamp 2 (C)
   double Vtherm = get_Vtherm_2();
   bool latched = fStatus_latched;
   fStatus_latched = true;
   double pos5V = get_pos5Vpower();
   fStatus_latched = latched;
   double logVtherm = log(100*(pos5V-Vtherm)/Vtherm);
   return  ((((fTcoef_therm[4])*logVtherm +
               fTcoef_therm[3])*logVtherm +
               fTcoef_therm[2])*logVtherm +
               fTcoef_therm[1])*logVtherm +
               fTcoef_therm[0];
}

inline double TAGMcontroller::get_VDAChealth() {    // DAC channel 31 read-back level (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[15]*40.5 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_VDACdiode() {     // DAC thermal diode voltage (V)
   if (! fStatus_latched)
      fetch_status();
   return fLastStatus[14]*1.005 * 2*fADC_Vref/(1 << 12);
}

inline double TAGMcontroller::get_TDAC() {          // DAC internal temperature reading (C)
   double Vdiode = get_VDACdiode();
   bool latched = fStatus_latched;
   fStatus_latched = true;
   double pos5V = get_pos5Vpower();
   fStatus_latched = latched;
   return fDACdiode_Tref + (pos5V - Vdiode - fDACdiode_Vf)/fDACdiode_Tcoef;
}

inline void TAGMcontroller::latch_status() {       // capture board status in state variables
   if (fetch_status() == 0)
      fStatus_latched = true;
}

inline void TAGMcontroller::passthru_status() {
   // reset saved state from last latch_levels()
   fStatus_latched = false;
}

inline void TAGMcontroller::latch_voltages() {
   // capture board's demand voltages in state variables
   if (fetch_voltages() == 0)
      fVoltages_latched = true;
}

inline void TAGMcontroller::passthru_voltages() {
   // reset saved voltages from last latch_voltages()
   fVoltages_latched = false;
}

inline double TAGMcontroller::getV(unsigned int chan) {          // voltage of channel reported by board (V)
   if (! fVoltages_latched)
      fetch_voltages();
   if (chan < 32)
      return fLastVoltages[chan] * (50*fDAC_Vref/(1 << 14));
   else
      return 0;
}

inline double TAGMcontroller::getVnew(unsigned int chan) {       // voltage of channel to be set in next ramp (V)
   if (chan < 32)
      return fNextVoltages[chan] * (50*fDAC_Vref/(1 << 14));
   else
      return 0;
}

inline void TAGMcontroller::setV(unsigned int chan, double V) {  // assign voltage of channel to be set in next ramp (V)
   if (chan < 32)
      fNextVoltages[chan] = int(V * (1 << 14) / (50*fDAC_Vref) + 0.5);
}

inline int TAGMcontroller::fetch_voltages() {
   // send a P-packet, receive a D-packet from board
   return set_voltages(0,fLastVoltages);
}

inline const unsigned char *TAGMcontroller::get_last_packet() {
   // return a pointer to a read-only buffer containing
   // the last packet received from the board
   return fLastPacket;
}

#endif
