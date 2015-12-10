all: mqread mqwrite

mqread: mqread.c
	gcc -g -o $@ $^ -lrt

mqwrite: mqwrite.c
	gcc -g -o $@ $^ -lrt

clean:
	rm -f mqread mqwrite *.o
