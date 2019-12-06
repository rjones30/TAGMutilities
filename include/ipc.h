
/* ipc.h */

#ifdef  __cplusplus
extern "C" {
#endif

  int epics_json_msg_sender_init(const char *expid, const char *session, const char *unique_id, const char *topic);
  int epics_json_msg_send(const char *caname, const char *catype, int nelem, void *data);
  int epics_json_msg_close();
  int send_daq_message_to_epics(const char *expid, const char *session, const char *myname, const char *caname, const char *catype, int nelem, void *data);

#ifdef  __cplusplus
}
#endif
