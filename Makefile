EXES = bin/sendpack bin/setVbias bin/resetVbias bin/probeVbias bin/readVbias
OBJS = TAGMcontroller.o sendpack.o setVbias.o resetVbias.o \
       probeVbias.o readVbias.o
LIBS = -lpcap

CFLAGS = -g -I. -O0

all: $(EXES)

bin/setVbias: setVbias.cc TAGMcontroller.cc
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	ssh root@gryphn chown root `pwd`/$@
	ssh root@gryphn chmod u+s `pwd`/$@

bin/resetVbias: resetVbias.cc TAGMcontroller.cc
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	ssh root@gryphn chown root `pwd`/$@
	ssh root@gryphn chmod u+s `pwd`/$@

bin/probeVbias: probeVbias.cc TAGMcontroller.cc
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	ssh root@gryphn chown root `pwd`/$@
	ssh root@gryphn chmod u+s `pwd`/$@

bin/readVbias: readVbias.cc TAGMcontroller.cc
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	ssh root@gryphn chown root `pwd`/$@
	ssh root@gryphn chmod u+s `pwd`/$@

bin/sendpack: sendpack.c
	mkdir -p bin
	${CXX} ${CFLAGS} -o $@ $^ ${LIBS}
	ssh root@gryphn chown root `pwd`/$@
	ssh root@gryphn chmod u+s `pwd`/$@

clean:
	rm -f ${OBJS} ${EXES} 

TAGMcontroller.cc: TAGMcontroller.h
