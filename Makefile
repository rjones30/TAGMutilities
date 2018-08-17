#EPICS = /cs/certified/apps/epics/v3.13.10-j1
EPICS = /gluex/controls/epics/R3-14-12-3-1/base
#BUILD = rhel-6-x86_64
BUILD = linux-x86_64

EXES = bin/sendpack bin/setVbias bin/resetVbias bin/probeVbias bin/readVbias \
       bin/TAGMremotectrl
OBJS = TAGMcommunicator.o TAGMcontroller.o sendpack.o setVbias.o resetVbias.o \
       probeVbias.o readVbias.o
LIBS = -lpcap

CFLAGS = -g -I. -O0

# comment out this section if epics is not available on the build host
 EPICS_CFLAGS = -DUPDATE_STATUS_IN_EPICS=1 -I$(EPICS)/include \
                -I$(EPICS)/include/os/Linux -L$(EPICS)/lib/$(BUILD) -lca \
                -Wl,-rpath,$(EPICS)/lib/$(BUILD)

# replace "ssh" with "true" below if root access is not available on the build host
SSH := true

all: $(EXES)

bin/setVbias: setVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p bin
	${CXX} ${CFLAGS} ${EPICS_CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

bin/resetVbias: resetVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p bin
	${CXX} ${CFLAGS} ${EPICS_CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

bin/probeVbias: probeVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

bin/readVbias: readVbias.cc TAGMcontroller.cc TAGMcommunicator.cc
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

bin/sendpack: sendpack.c
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

bin/TAGMremotectrl: TAGMremotectrl.cc TAGMcontroller.o TAGMcommunicator.cc
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	$(SSH) root@gryphn chown root `pwd`/$@
	$(SSH) root@gryphn chmod u+s `pwd`/$@

clean:
	rm -f ${OBJS} ${EXES} 

TAGMcontroller.cc: TAGMcontroller.h

TAGMcommunicator.cc: TAGMcommunicator.h

