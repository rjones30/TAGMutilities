//
// pyepics.cc - implements a python module for the epics i/o interface.
//
// author: richard.t.jones@uconn.edu
// version: october 17, 2018
//

#include <Python.h>
#include <cadef.h> /* Structures and data types used by epics CA */

std::map<std::string,chid> epics_channelId;

int epics_start_communication();
int epics_get_value(std::string epics_var, chtype ca_type, void *value, int len=1);
int epics_put_value(std::string epics_var, chtype ca_type, void *value, int len=1, int finalize=1);
int epics_stop_communication();

int epics_start_communication()
{
   epics_status = ca_task_initialize();
   SEVCHK(epics_status, "0");
   return (epics_status == ECA_NORMAL);
}

int epics_get_value(std::string epics_var, chtype ca_type, void *value, int len)
{
   if (epics_channelId.find(epics_var) == epics_channelId.end()) {
      epics_status = ca_search(epics_var.c_str(), &epics_channelId[epics_var]);
      SEVCHK(epics_status, "1");
      if (epics_status != ECA_NORMAL) {
         epics_channelId[epics_var] = 0;
         return 9;
      }
      epics_status = ca_pend_io(0.0);
      SEVCHK(epics_status, "1.5");
      if (epics_status != ECA_NORMAL) {
         epics_channelId[epics_var] = 0;
         return 9;
      }
   }
   else if (epics_channelId[epics_var] == 0) {
      return 9;
   }
   epics_status = ca_array_get(ca_type, len, epics_channelId[epics_var], value);
   SEVCHK(epics_status, "2");
   epics_status = ca_pend_io(0.0);
   SEVCHK(epics_status, "3");
   return (epics_status == ECA_NORMAL);
}

int epics_put_value(std::string epics_var, chtype ca_type, void *value, int len, int finalize)
{
   if (epics_channelId.find(epics_var) == epics_channelId.end()) {
      epics_status = ca_search(epics_var.c_str(), &epics_channelId[epics_var]);
      SEVCHK(epics_status, "4");
      if (epics_status != ECA_NORMAL) {
         epics_channelId[epics_var] = 0;
         return 9;
      }
      epics_status = ca_pend_io(0.0);
      SEVCHK(epics_status, "4.5");
      if (epics_status != ECA_NORMAL) {
         epics_channelId[epics_var] = 0;
         return 9;
      }
   }
   else if (epics_channelId[epics_var] == 0) {
      return 9;
   }
   epics_status = ca_array_put(ca_type, len, epics_channelId[epics_var], value);
   SEVCHK(epics_status, "5");
   if (finalize) {
      epics_status = ca_pend_io(0.0);
      SEVCHK(epics_status, "6");
   }
   return (epics_status == ECA_NORMAL);
}

int epics_stop_communication()
{
   std::map<std::string, chid>::iterator iter;
   for (iter = epics_channelId.begin();
        iter != epics_channelId.end();
        ++iter)
   {
      ca_clear_channel(iter->second);
   }
   ca_task_exit();
}

PyObject *epics_get(PyObject *self, PyObject *args, PyObject *keywds)
{
   char *varname;
   char *vartype;
   int varlength=1;
   char *kwlist[] = {"var", "type", "len", NULL};
   if (!PyArg_ParseTupleAndKeywords(args, keywds, "ss|i", 
                                    &varname, &vartype, &varlength))
      return NULL;
   std::string epics_var(varname);
   std::string epics_type(vartype);
   if (vartype == "string") {
      char value[65536];
      int status = epics_get_value(epics_var, DBF_STRING, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("s");
         for (int i=1; i<varlength; ++i)
            form << ",s";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "char" || vartype == "int8") {
      char value[65536];
      int status = epics_get_value(epics_var, DBF_CHAR, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("b");
         for (int i=1; i<varlength; ++i)
            form << ",b";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "uchar" || vartype == "uint8") {
      unsigned char value[65536];
      int status = epics_get_value(epics_var, DBF_UCHAR, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("b");
         for (int i=1; i<varlength; ++i)
            form << ",b";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "short" || vartype == "int16") {
      short int value[65536];
      int status = epics_get_value(epics_var, DBF_SHORT, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("h");
         for (int i=1; i<varlength; ++i)
            form << ",h";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "ushort" || vartype == "uint16") {
      unsigned short int value[65536];
      int status = epics_get_value(epics_var, DBF_USHORT, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("H");
         for (int i=1; i<varlength; ++i)
            form << ",H";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "int" || vartype == "int32") {
      int value[65536];
      int status = epics_get_value(epics_var, DBF_LONG, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("i");
         for (int i=1; i<varlength; ++i)
            form << ",l";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "uint" || vartype == "uint32") {
      unsigned int value[65536];
      int status = epics_get_value(epics_var, DBF_ULONG, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("I");
         for (int i=1; i<varlength; ++i)
            form << ",I";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "long" || vartype == "int64") {
      long int value[65536];
      int status = epics_get_value(epics_var, DBF_LONG, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("l");
         for (int i=1; i<varlength; ++i)
            form << ",l";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "ulong" || vartype == "uint64") {
      unsigned long int value[65536];
      int status = epics_get_value(epics_var, DBF_ULONG, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("k");
         for (int i=1; i<varlength; ++i)
            form << ",k";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "float") {
      float value[65536];
      int status = epics_get_value(epics_var, DBF_FLOAT, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("f");
         for (int i=1; i<varlength; ++i)
            form << ",f";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "double") {
      float value[65536];
      int status = epics_get_value(epics_var, DBF_DOUBLE, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("d");
         for (int i=1; i<varlength; ++i)
            form << ",d";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "enum") {
      char value[65536];
      int status = epics_get_value(epics_var, DBF_ENUM, value, varlength);
      if (status == ECA_NORMAL) {
         std::stringstream form("b");
         for (int i=1; i<varlength; ++i)
            form << ",b";
         return Py_BuildValue(form, value);
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else {
      PyErr_SetString(PyExc_TypeError, "unsupported EPICS variable type");
   }
   return NULL;
}

int epics_put_value(std::string epics_var, chtype ca_type, void *value, int len, int finalize)
PyObject *epics_get(PyObject *self, PyObject *args)
{
   char *varname;
   char *vartype;
   PyObject *value;
   int varlength=1;
   int finalize=1;
   char *kwlist[] = {"var", "type", "value", "len", "finalize", NULL};
   if (!PyArg_ParseTupleAndKeywords(args, keywds, "sso|ii", 
                                    &varname, &vartype, &value,
                                    &varlength, &finalize))
      return NULL;
   if (varlength > 1 && PySequence_Size(value) < varlength) {
      PyErr_SetString(PyExc_ValueError, "insufficient values supplied for writing");
      return NULL;
   }
   std::string epics_var(varname);
   std::string epics_type(vartype);
   if (vartype == "string") {
      if (varlength == 1)
         int status = epics_put_value(epics_var, DBF_STRING, PyString_AsString(value));
         if (status == ECA_NORMAL) {
            Py_INCREF(Py_None);
            return Py_None;
         }
         PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
      }
      else {
         PyErr_SetString(PyExc_ValueError, "only one string allowed per put");
      }
   }
   else if (vartype == "char" || vartype == "int8") {
      char byteval[varlength];
      if (PyInt_Check(value)) {
         byteval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            byteval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            byteval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_CHAR, &byteval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "uchar" || vartype == "uint8") {
      unsigned char byteval[varlength];
      if (PyInt_Check(value)) {
         byteval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            byteval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            byteval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_UCHAR, &byteval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "short" || vartype == "int16") {
      short int shortval[varlength];
      if (PyInt_Check(value)) {
         shortval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            shortval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            shortval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_SHORT, &shortval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "ushort" || vartype == "uint16") {
      unsigned short int shortval[varlength];
      if (PyInt_Check(value)) {
         shortval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            shortval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            shortval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_USHORT, &shortval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "int" || vartype == "int32") {
      int intval[varlength];
      if (PyInt_Check(value)) {
         intval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            intval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            intval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_USHORT, &intval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "uint" || vartype == "uint32") {
      unsigned int intval[varlength];
      if (PyInt_Check(value)) {
         intval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            intval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            intval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_USHORT, &intval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "long" || vartype == "int64") {
      long int longval[varlength];
      if (PyInt_Check(value)) {
         longval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            longval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            longval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_USHORT, &longval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "ulong" || vartype == "uint64") {
      unsigned long int longval[varlength];
      if (PyInt_Check(value)) {
         longval[0] = PyInt_AsLong(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            longval[i] = PyInt_AsLong(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            longval[i] = PyInt_AsLong(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_USHORT, &longval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "float") {
      float floatval[varlength];
      if (PyInt_Check(value)) {
         floatval[0] = PyInt_AsDouble(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            floatval[i] = PyInt_AsDouble(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            floatval[i] = PyInt_AsDouble(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_USHORT, &floatval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "double") {
      double floatval[varlength];
      if (PyInt_Check(value)) {
         floatval[0] = PyInt_AsDouble(value);
      }
      else if (PyList_Check(value)) {
         for (int i=0; i < varlength; ++i)
            floatval[i] = PyInt_AsDouble(PyList_GetItem(value, i));
      }
      else if (PyTuple_Check(value)) {
         for (int i=0; i < varlength; ++i)
            floatval[i] = PyInt_AsDouble(PyTuple_GetItem(value, i));
      }
      else {
         PyErr_SetString(PyExc_TypeError, "put value does not match stated type");
         return NULL;
      }
      int status = epics_put_value(epics_var, DBF_USHORT, &floatval, varlength, finalize);
      if (status == ECA_NORMAL) {
         Py_INCREF(Py_None);
         return Py_None;
      }
      PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
   }
   else if (vartype == "enum") {
      if (varlength == 1)
         int status = epics_put_value(epics_var, DBF_ENUM, PyString_AsString(value));
         if (status == ECA_NORMAL) {
            Py_INCREF(Py_None);
            return Py_None;
         }
         PyErr_SetString(PyExc_IOError, "invalid epics variable name or type");
      }
      else {
         PyErr_SetString(PyExc_ValueError, "only one string allowed per put");
      }
   }
   else {
      PyErr_SetString(PyExc_TypeError, "unsupported EPICS variable type");
   }
   return NULL;
}
