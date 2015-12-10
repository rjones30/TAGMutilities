/*
 * mqread - a small command-line utility to read from to a proccessor
 *          message queue (do man mq_overview) for sharing state
 *          information between processes on a local host. If the
 *          option -r is given, the named queue is deleted.
 *
 * author: richard.t.jones at uconn.edu
 * version: november 18, 2015
 *
 * usage:
 *   $ mqread [-r] /myqueue_name
 *
 * see also: mqread.c
 *
 */

#define MAX_MESSAGE_LEN 99

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <mqueue.h>
#include <errno.h>

void usage()
{
   printf("Usage: mqread [-r] /<your_queue_name>\n");
   printf("\n");
}

int main(int argc, char **argv)
{
   if (argc == 3) {
      if (strcmp(argv[1], "-r") == 0) {
         exit(mq_unlink(argv[2]));
      }
   }
   if (argc != 2) {
      usage();
      return 0;
   }

      
   int err;
   int prio;
   char *qname = argv[1];
   char message[9999];
   mqd_t mqd = mq_open(qname, O_RDONLY | O_NONBLOCK);
   if (mqd < 0) {
      perror("mq_open barfs up:");
      exit(1);
   }
   err = mq_receive(mqd, message, 9999, &prio);
   if (err < 0 && errno != EAGAIN) {
      perror("mq_receive barfs up:");
   }
   else if (err > 0) {
      printf("message received: %s\n", message);
   }
   else {
      printf("no message available\n");
   }
   return mq_close(mqd);
}
