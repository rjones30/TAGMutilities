
//
//
// This program is to allow the hdops account to 
// change the permissions on 5 specific files in
// the ~hdops/TAGMutilities directory to be run
// as root. This is needed to give them access to
// the special ethernet device on gluon28 that is
// directly connected to the tagger microscope.
//
// A compiled program is needed since Linux does
// not honor the uid being set to the root user 
// for scripts due to security.
//
// If modifications to this file are made, one
// will need sudo priviliges to remake it and
// set the correct permissions on the resulting
// executable.
//
//  > sudo rm tagmutil_chmod
//  > c++ -o tagmutil_chmod tagmutil_chmod.cc
//  > sudo chown root tagmutil_chmod
//  > sudo chmod 4755 tagmutil_chmod
//
//
// Questions about this should be directed to
// Alex Barnes (aebarnes@jlab.org)
// David Lawrence (davidl@jlab.org)



#include <sys/stat.h>
#include <unistd.h>
#include <stdint.h>

#include <string>
#include <vector>
#include <iostream>
using namespace std;

int main(int narg, char* argv[])
{

	string path="/gluonfs1/home/hdops/TAGMutilities/bin";

	vector<string> files;
	files.push_back("probeVbias");
	files.push_back("readVbias");
	files.push_back("resetVbias");
	files.push_back("sendpack");
	files.push_back("setVbias");

	for(uint32_t i=0; i<files.size(); i++){
		string fullpath = path + "/" + files[i];
		
		mode_t mode = S_ISUID + S_IRUSR + S_IWUSR + S_IXUSR;
		
		cout << "Changing owner/perms on " << fullpath << endl;
		chmod(fullpath.c_str(), mode);
		chown(fullpath.c_str(), 0, 0);
	}

	return 0;
}


