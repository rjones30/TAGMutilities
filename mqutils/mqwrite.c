/*
 * mqwrite - a small command-line utility to write to a proccessor
 *           message queue (do man mq_overview) for sharing state
 *           information between processes on a local host. If the
 *           named queue does not already exist, it is created with
 *           the current user as owner and no group/world privs.
 *
 * author: richard.t.jones at uconn.edu
 * version: november 18, 2015
 *
 * usage:
 *   $ mqwrite /myqueue_name "my message"
 *
 * see also: mqread.c
 *
 * notes:
 * 1) I added a special feature to support binary messages. If the
 *    message starts with 0x followed by a string of hex digits of
 *    any length then the message is encoded as a binary stream of
 *    bytes whose values are equal to the listed digits taken in
 *    pairs. If an odd number of pairs is listed then an implicit
 *    zero is assumed at the end of the string.
 *
 */

#define MAX_MESSAGE_LEN 99

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <mqueue.h>

void usage()
{
   printf("Usage: mqwrite /<your_queue_name> \"your message\"\n");
   printf("\n");
}

int main(int argc, char **argv)
{
   if (argc != 3 || argv[1][0] != '/') {
      usage();
      exit(1);
   }
   char *qname = argv[1];
   char *message = argv[2];
   char buffer[999];
   if (strlen(argv[2]) > 2 && strstr(argv[2], "0x") == argv[2]) {
      char *pout = buffer;
      char *pin = argv[2] + 2;
      char *pend = argv[2] + strlen(argv[2]);
      message = buffer;
      *pend = '0';
      while (pin < pend) {
         if (strspn(pin, "0123456789abcdef") < 2 || 
             sscanf(pin, "%2x", pout) != 1)
         {
            message = argv[2];
            break;
         }
         pin += 2;
         ++pout;
      }
      *pout = 0;
      *pend = 0;
   }
   if (strlen(message) > MAX_MESSAGE_LEN) {
      fprintf(stderr, "Warning: message length %d exceeds maximum message size"
                      " configured for this message queue.\n", strlen(message));
      fprintf(stderr, "Message truncated at %d characters.\n", MAX_MESSAGE_LEN);
      message[MAX_MESSAGE_LEN] = 0;
   }

   int err;
   mode_t mode;
   struct mq_attr attr;
   attr.mq_flags = O_NONBLOCK;
   attr.mq_maxmsg = 10;
   attr.mq_msgsize = 99;
   attr.mq_curmsgs = 0;
   mode = S_IRWXU;
   mqd_t mqd = mq_open(qname, O_WRONLY | O_NONBLOCK);
   if (mqd <= 0) {
      printf("creating a new queue named %s\n", qname);
      mqd = mq_open(qname, O_CREAT | O_WRONLY | O_NONBLOCK, mode, &attr);
      if (mqd <= 0) {
         perror("mq_open barfs up:");
      }
   }

   err = mq_send(mqd, message, strlen(message), 0);
   if (err < 0) {
      perror("mq_send barfs up:");
   }
   return mq_close(mqd);
}
