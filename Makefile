#EPICS_BASE = /cs/certified/apps/epics/v3.13.10-j1
EPICS_BASE = /gluex/controls/epics/R3-14-12-3-1/base
#EPICS_BUILD = rhel-6-x86_64
EPICS_BUILD = linux-x86_64
BIN = bin
LIB = lib

EXES = $(BIN)/sendpack $(BIN)/setVbias $(BIN)/resetVbias $(BIN)/probeVbias $(BIN)/readVbias \
       $(BIN)/TAGMremotectrl
OBJS = TAGMcommunicator.o TAGMcontroller.o sendpack.o setVbias.o resetVbias.o \
       probeVbias.o readVbias.o
LIBS = /usr/lib64/libpcap.so.1
#LIBS = /usr/lib/arm-linux-gnueabihf/libpcap.so

CFLAGS = -g -I. -I./include -O0 

# comment out this section if epics is not available on the build host
#EPICS_CFLAGS = -DUPDATE_STATUS_IN_EPICS=1 \
#               -I$(EPICS_BASE)/include -I$(EPICS_BASE)/include/os/Linux \
#               -L$(EPICS_BASE)/lib/$(EPICS_BUILD) -lca \
#               -Wl,-rpath,$(EPICS_BASE)/lib/$(EPICS_BUILD)

# replace "ssh" with "true" below if root access is not available on the build host
SSH := true

all: $(EXES)

$(BIN)/setVbias: setVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p $(BIN)
	${CXX} ${CFLAGS} ${EPICS_CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

$(BIN)/resetVbias: resetVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p $(BIN)
	${CXX} ${CFLAGS} ${EPICS_CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

$(BIN)/probeVbias: probeVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p $(BIN)
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

$(BIN)/readVbias: readVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p $(BIN)
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

$(BIN)/sendpack: sendpack.c
	mkdir -p $(BIN)
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

$(BIN)/TAGMremotectrl: TAGMremotectrl.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p $(BIN)
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

$(LIB)/epics.so: pyepics.cc
	mkdir -p $(LIB)
	${CXX} -fPIC -shared ${CFLAGS} ${EPICS_CFLAGS} -o $@ $^ ${LIBS}

clean:
	rm -f ${OBJS} ${EXES}

TAGMcontroller.cc: TAGMcontroller.h

TAGMcommunicator.cc: TAGMcommunicator.h
