#define _BITTYPES_H 1

#include <stdlib.h>
#include <stdio.h>
#include <pcap.h>

int main(int argc, char **argv)
{
   pcap_t *fp;
   char errbuf[PCAP_ERRBUF_SIZE];
   u_char packet[512];
   u_char c;
   const u_char destMAC[] = "\xFF\xFF\xFF\xFF\xFF\xFF";
   const u_char srcMAC[] ="\xbc\xae\xc5\x78\x0d\xe1";
   const u_char destLocStamp = '\x9F';
   const int HeaderSize=14;
   const int FirstPayloadArg=2;

   int i;
   int BytesInArgs = argc - 1;
   int PktSize = BytesInArgs + HeaderSize - 1;
   PktSize = (PktSize < 64)? 64 : PktSize;

   /* Check the validity of the command line */
   if (argc < 2 || argc > (256 + FirstPayloadArg - 1)){
      printf("usage: %s interface [byte1] [byte2] ...\n", argv[0]);
      printf("         where the bytes (up to 256) are listed in hex.\n");
      return 1;
   }
    
   /* Open the adapter */
   if ((fp = pcap_open_live(argv[1],  // name of the device
                            65536,    // portion of the packet to capture. It doesn't matter in this case 
                            1,        // promiscuous mode (nonzero means promiscuous)
                            1000,     // read timeout
                            errbuf    // error buffer
                           )) == NULL)
   {
      fprintf(stderr,"\nUnable to open the adapter. %s is not supported by WinPcap\n", argv[1]);
      return 2;
   }

   for (i=0; i < 512; i++)
      packet[i] = 0;

   /* Fill the rest of the packet  */
   for (i=FirstPayloadArg; i <= BytesInArgs; i++) {
      sscanf(argv[i],"%x",&c);
      packet[i-FirstPayloadArg+HeaderSize] = c;
   }

   // set MAC addresses -----------------------
   for (i=0; i < 6; i++) {
      packet[i] = destMAC[i];
      printf("%.2x-", destMAC[i]);
   }
   printf("\b ");
   for (i=0; i < 6; i++) {
      packet[i+6] = srcMAC[i];
      printf("%.2x-", srcMAC[i]);
   }
   printf("\b \n");
   //-----------------------------------------
   
   packet[12] = 0;
   packet[13] = PktSize-HeaderSize;
   printf("sending packet with payload size %d\n", packet[12]*256+packet[13]);

   if (pcap_sendpacket(fp,     // Adapter
                       packet, // buffer with the packet
                       PktSize // size
                      ) != 0)
   {
       fprintf(stderr,"\nError sending the packet: %s\n", pcap_geterr(fp));
       return 3;
     }
   
   pcap_close(fp);   
   return 0;
}
