#define pstags_cxx
// The class definition in pstags.h has been generated automatically
// by the ROOT utility TTree::MakeSelector(). This class is derived
// from the ROOT class TSelector. For more information on the TSelector
// framework see $ROOTSYS/README/README.SELECTOR or the ROOT User Manual.


// The following methods are defined in this file:
//    Begin():        called every time a loop on the tree starts,
//                    a convenient place to create your histograms.
//    SlaveBegin():   called after Begin(), when on PROOF called only on the
//                    slave servers.
//    Process():      called for each event, in this function you decide what
//                    to read and fill your histograms.
//    SlaveTerminate: called at the end of the loop on the tree, when on PROOF
//                    called only on the slave servers.
//    Terminate():    called at the end of the loop on the tree,
//                    a convenient place to draw/fit your histograms.
//
// To use this file, try the following session on your Tree T:
//
// root> T->Process("pstags.C")
// root> T->Process("pstags.C","some options")
// root> T->Process("pstags.C+")
//


#include "pstags.h"
#include <TH2.h>
#include <TStyle.h>
#include <string>
#include <sstream>

double pstags::endpoint_energy; // GeV
double pstags::endpoint_calib;  // GeV
double pstags::scaled_energy[2][102];

static int read_ccdb_text(std::ifstream &ifs, const std::string &column_name, double *column_data);

void pstags::Begin(TTree * /*tree*/)
{
   // The Begin() function is called at the start of the query.
   // When running with PROOF Begin() is only called on the client.
   // The tree argument is deprecated (on PROOF 0 is passed).

   endpoint_energy = -1;
   TString option = GetOption();
}

void pstags::SlaveBegin(TTree * /*tree*/)
{
   // The SlaveBegin() function is called after the Begin() function.
   // When running with PROOF SlaveBegin() is called on each slave server.
   // The tree argument is deprecated (on PROOF 0 is passed).

   TString option = GetOption();

   Etagm_Epair = new TH2D("Etagm_Epair", "Etagm vs Eps", 190, 3.0, 10.0,
                                                         190, 3.0, 10.0);
   Etagm_Epair->GetXaxis()->SetTitle("E_pair (GeV)");
   Etagm_Epair->GetYaxis()->SetTitle("E_tagm (GeV)");
   Epair_Etagm = new TProfile("Epair_Etagm", "Eps vs Etagm", 190, 3.0, 10.0,
                                                             3.0, 10.0, "");
   Epair_Etagm->GetXaxis()->SetTitle("E_tagm (GeV)");
   Epair_Etagm->GetYaxis()->SetTitle("E_pair (GeV)");
   ttagm_pair = new TH2D("ttagm_pair", "TAGM time - PS time", 128, 0, 128,
                                                           1600, -250, 250);
   ttagm_pair->GetXaxis()->SetTitle("tagm channel");
   ttagm_pair->GetYaxis()->SetTitle("t_tagm - t_pair (ns)");
}

Bool_t pstags::Process(Long64_t entry)
{
   // The Process() function is called for each entry in the tree (or possibly
   // keyed object in the case of PROOF) to be processed. The entry argument
   // specifies which entry in the currently loaded tree is to be processed.
   // When processing keyed objects with PROOF, the object is already loaded
   // and is available via the fObject pointer.
   //
   // This function should contain the \"body\" of the analysis. It can contain
   // simple or elaborate selection criteria, run algorithms on the data
   // of the event and typically fill histograms.
   //
   // The processing can be stopped by calling Abort().
   //
   // Use fStatus to set the return value of TTree::Process().
   //
   // The return value is currently not used.

   fReader.SetLocalEntry(entry);

   // read the tagm energy bins from a ccdb calibration dump file, if exists
   if (endpoint_energy < 0) {
      std::stringstream calibf;
      calibf << "endpoint_energy." << *runno;
      try {
         std::ifstream ifee(calibf.str().c_str());
         if (read_ccdb_text(ifee, "PHOTON_BEAM_ENDPOINT_ENERGY", &endpoint_energy) == 0)
            exit(6);
         calibf.str("");
         calibf << "endpoint_calib." << *runno;
         std::ifstream ifec(calibf.str().c_str());
         if (read_ccdb_text(ifec, "TAGGER_CALIB_ENERGY", &endpoint_calib) == 0)
            exit(7);
         calibf.str("");
         calibf << "scaled_energy_range." << *runno;
         std::ifstream ifse(calibf.str().c_str());
         if (read_ccdb_text(ifse, "xlow", scaled_energy[0]) == 0)
            exit(8);
         if (read_ccdb_text(ifse, "xhigh", scaled_energy[1]) == 0)
            exit(9);
         double tagm_energy_bins[103];
         for (int i=0; i < 102; ++i) {
            tagm_energy_bins[101-i] = endpoint_energy - endpoint_calib * (1 - scaled_energy[0][i]);
         }
         tagm_energy_bins[102] = endpoint_energy - endpoint_calib * (1 - scaled_energy[1][0]);
         Etagm_Epair->GetYaxis()->Set(102, tagm_energy_bins);
         Epair_Etagm->GetXaxis()->Set(102, tagm_energy_bins);
      }
      catch (...) {
         endpoint_energy = 0;
      }
   }

   for (int ips=0; ips < *npairps; ++ips) {
      for (int itagm=0; itagm < *ntagm; ++itagm) {
         double tdiff = tagm_time[itagm] - tpair[ips];
         if (*runno >=100000 && *runno < 120000) {
            if (tdiff > 34 and tdiff < 40) {
               Etagm_Epair->Fill(Epair[ips], tagm_Etag[itagm]);
               Epair_Etagm->Fill(tagm_Etag[itagm], Epair[ips]);
            }
         }
         else {
            if (tdiff > -5 and tdiff < 5) {
               Etagm_Epair->Fill(Epair[ips], tagm_Etag[itagm]);
               Epair_Etagm->Fill(tagm_Etag[itagm], Epair[ips]);
            }
         }
         ttagm_pair->Fill(tagm_channel[itagm], tdiff);
      }
   }

   return kTRUE;
}

void pstags::SlaveTerminate()
{
   // The SlaveTerminate() function is called after all entries or objects
   // have been processed. When running with PROOF SlaveTerminate() is called
   // on each slave server.

}

void pstags::Terminate()
{
   // The Terminate() function is the last function to be called during
   // a query. It always runs on the client, it can be used to present
   // the results graphically or save the results to file.

}

static int read_ccdb_text(std::ifstream &ifs, const std::string &column_name, double *column_data)
{
   ifs.clear();
   ifs.seekg(0);
   int column_number(-1);
   double *cdata = column_data;
   for (std::string line; std::getline(ifs, line, '\n');) {
      if (line[0] != '|')
         continue;
      std::stringstream sline(line);
      int cno(0);
      for (std::string scol; std::getline(sline, scol, '|'); ++cno) {
         if (column_number < 0) {
            if (scol.find(column_name) == 1) {
               column_number = cno;
               break;
            }
         }
         else if (cno == column_number) {
            try {
               double val = std::stod(scol);
               *(cdata++) = val;
               break;
            }
            catch (...) {
            }
         }
      }
   }
   return cdata - column_data;
}
