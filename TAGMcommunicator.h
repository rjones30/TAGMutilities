//
// Class TAGMcommunicator
//
// Purpose: represents a single Vbias control board for the 
//          GlueX tagger microscope readout electronics
//
// This class exposes the exact same object interface as the
// TAGMcontroller class, but the implementation uses text messaging
// over a tcp connection to a remote server running the TAGMremotectrl
// daemon, where the physical connection to the frontend electronics
// is located. The only difference in usage between a TAGMcontroller
// and a TAGMcommunicator instance is the form of the server argument
// which replaces the netdev argument in the constructor arg list.
//               server := <hostname>[:port][::netdev]
//
// programmer's notes:
// (1) My wish here is to create a clone of the TAGMcontroller class
//     that replicates all of its functions using a server daemon
//     running the TAGMremotectrl daemon, communicating with the client
//     over a remote tcp socket.
// (2) Any user code that currently works with TAGMcontroller objects
//     should immediately work from a remote host by simply replacing
//     the TAGMcontroller instance with a TAGMcommunicator. I do this
//     with private inheritance since I want to inherit only the
//     interface, and not any of the actual methods of TAGMcontroller.
// (3) This was mostly possible by making the member functions of the
//     TAGMcontroller base class virtual, except for the special case
//     of static methods. For this, I made a subtle work-around by
//     changing the signature of the overriding methods in the derived
//     class, switching the second argument type from a traditional c
//     string to a std::string object. USER BEWARE! If you think that
//     automatic conversion from a string literal to a std::string
//     argument will work with these static methods, it won't.

#ifndef TAGMCOMMUNICATOR_H
#define TAGMCOMMUNICATOR_H

#include "TAGMcontroller.h"

class TAGMcommunicator: public TAGMcontroller {
 public:
   TAGMcommunicator(unsigned char geoaddr, std::string server);
   TAGMcommunicator(unsigned char MACaddr[6], std::string server);
   ~TAGMcommunicator();

   static std::map<unsigned char, std::string> probe(std::string server);  // retrieve a list of all Vbias boards that respond to a broadcast query
   static const std::string  get_hostMACaddr(std::string server);  // get the ethernet MAC address of host interface
   const unsigned char get_Geoaddr();   // get the backplane slot address of this board
   const unsigned char *get_MACaddr();  // get the ethernet MAC address of this board

   double get_Tchip();         // board temperature from T sensor chip (C)
   double get_pos5Vpower();    // +5V power level (V)
   double get_neg5Vpower();    // -5V power level (V)
   double get_pos3_3Vpower();  // +3.3V power level (V)
   double get_pos1_2Vpower();  // +1.2V power level (V)
   double get_Vsumref_1();     // SUMREF from preamp 1 (V)
   double get_Vsumref_2();     // SUMREF from preamp 2 (V)
   double get_Vgainmode();     // GAINMODE shared by both preamps (V)
   int get_gainmode();         // =0 (low) or =1 (high) or =-1 (undefined)
   double get_Vtherm_1();      // thermister voltage on preamp 1 (V)
   double get_Vtherm_2();      // thermister voltage on preamp 2 (V)
   double get_Tpreamp_1();     // thermister temperature on preamp 1 (C)
   double get_Tpreamp_2();     // thermister temperature on preamp 2 (C)
   double get_VDAChealth();    // DAC channel 31 read-back level (V)
   double get_VDACdiode();     // DAC temperature diode voltage (V)
   double get_TDAC();          // DAC internal temperature reading (C)

   void latch_status();        // capture board status in state variables
                               // and return captured data in response to get_XXX()
   void passthru_status();     // reset saved state from last latch_levels()
                               // and have each get_XXX() request fresh data from board
   void latch_voltages();      // capture board's demand voltages in state variables
                               // and return captured data in response to getV()
   void passthru_voltages();   // reset saved voltages from last latch_voltages()
                               // and have each getV() request fresh data from board

   double getV(unsigned int chan);          // voltage of channel reported by board (V)
   double getVnew(unsigned int chan);       // voltage of channel to be set in next ramp (V)
   void setV(unsigned int chan, double V);  // assign voltage of channel to be set in next ramp (V)
   const unsigned char *get_last_packet();  // return a pointer to a read-only buffer containing the last packet received from the board

   bool ramp();                // push the new voltages to the board, if any
   bool reset();               // send a hard reset to the board

 protected:
   std::string fBoard;
   std::string fServer;
   unsigned char fMACaddr[6];
   unsigned char fPacket[270];

   static std::map<std::string, int> fServer_sockfd;
   static TAGMcommunicator *fSelected;

   static void open_client_connection(std::string server);
   static std::string request_response(std::string req, std::string server);
   static std::string get_netdev(std::string server);

   std::string request_response(std::string req);
   void select();
};

#endif
