#define fadc250_time_calib_cxx
// The class definition in fadc250_time_calib.h has been generated automatically
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
// root> T->Process("fadc250_time_calib.C")
// root> T->Process("fadc250_time_calib.C","some options")
// root> T->Process("fadc250_time_calib.C+")
//

#define FADC250_TCUT0 20
#define FADC250_TCUT1 220

#include "fadc250_time_calib.h"
#include <TH2.h>
#include <TStyle.h>

void fadc250_time_calib::Begin(TTree * /*tree*/)
{
   // The Begin() function is called at the start of the query.
   // When running with PROOF Begin() is only called on the client.
   // The tree argument is deprecated (on PROOF 0 is passed).

   TString option = GetOption();
}

void fadc250_time_calib::SlaveBegin(TTree * /*tree*/)
{
   // The SlaveBegin() function is called after the Begin() function.
   // When running with PROOF SlaveBegin() is called on each slave server.
   // The tree argument is deprecated (on PROOF 0 is passed).

   TString option = GetOption();

   hitrate_col = new TH2D("hitrate_col", "rate vs column", 102, 1, 103, 5, 0, 5);
   hitrate_col->GetXaxis()->SetTitle("column");
   hitrate_col->GetYaxis()->SetTitle("hit rate");
   hitrate_row = new TH2D("hitrate_row", "rate vs row", 50, 0, 50, 5, 0, 5);
   hitrate_row->GetXaxis()->SetTitle("row + column*10");
   hitrate_row->GetYaxis()->SetTitle("hit rate");
   hittime_col = new TH2D("hittime_col", "time vs column", 102, 1, 103, 150/0.0625, 0, 300);
   hittime_col->GetXaxis()->SetTitle("column");
   hittime_col->GetYaxis()->SetTitle("hit time (ns)");
   hittime_row = new TH2D("hittime_row", "time vs row", 50, 0, 50, 150/0.0625, 0, 300);
   hittime_row->GetXaxis()->SetTitle("row + column*10");
   hittime_row->GetYaxis()->SetTitle("hit time (ns)");
   deltatr_col = new TH2D("deltatr_col", "time-tRF vs column", 102, 1, 103, 150/0.0625, 0, 300);
   deltatr_col->GetXaxis()->SetTitle("column");
   deltatr_col->GetYaxis()->SetTitle("hit time - RFtime (ns)");
   deltatr_row = new TH2D("deltatr_row", "time-tRF vs row", 50, 0, 50, 150/0.0625, 0, 300);
   deltatr_row->GetXaxis()->SetTitle("row + column*10");
   deltatr_row->GetYaxis()->SetTitle("hit time - RFtime (ns)");
   deltatn_col = new TH2D("deltatn_col", "t-diff for neighboring columns",
                          102, 1, 103, 1600, -50, 50);
   deltatn_col->GetXaxis()->SetTitle("column");
   deltatn_col->GetYaxis()->SetTitle("fadc250 hit time difference (ns)");
   deltatn_row = new TH2D("deltatn_row", "t-diff for neighboring rows",
                          50, 0, 50, 1600, -50, 50);
   deltatn_row->GetXaxis()->SetTitle("row + column*10");
   deltatn_row->GetYaxis()->SetTitle("fadc250 hit time difference (ns)");
   deltatf_col = new TH2D("deltatf_col", "t-diff for separated columns",
                          102, 1, 103, 1600, -50, 50);
   deltatf_col->GetXaxis()->SetTitle("column");
   deltatf_col->GetYaxis()->SetTitle("fadc250 hit time difference (ns)");
   deltatf_row = new TH2D("deltatf_row", "t-diff for separated rows",
                          50, 0, 50, 1600, -50, 50);
   deltatf_row->GetXaxis()->SetTitle("row + column*10");
   deltatf_row->GetYaxis()->SetTitle("fadc250 hit time difference (ns)");
   deltati_row = new TH2D("deltati_row", "t-diff for row - column sum",
                          50, 0, 50, 1600, -50, 50);
   deltati_row->GetXaxis()->SetTitle("row + column*10");
   deltati_row->GetYaxis()->SetTitle("fadc250 hit time difference (ns)");

   last_eventno = -1;
}

Bool_t fadc250_time_calib::Process(Long64_t entry)
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

   int row_count[50] = {0};
   int column_count[103] = {0};
   int row_offset[100] = {0,0,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,10,0,0,
                          0,0,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,0,0,
                          0,30,0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,0,40};

   static double toffset[103][6] = {0};
   static int toffset_loaded(0);
   try {
      if (!toffset_loaded ) {
         toffset_loaded = 1;
         std::ifstream calib_file("fadc250_time_calib.conf");
         int row, col;
         double tshift, tperiod, tsigma;
         while (calib_file >> col >> row >> tshift >> tperiod >> tsigma) {
            toffset[col][row] = tshift;
            //std::cout << "loaded toffset[" << col << "][" << row << "]" << std::endl;
         }
      }
   }
   catch (std::exception e) {
      // nothing to do, toffset table not available
   }

   if (last_eventno > 0 and last_eventno != *eventno) {
      for (int i=0; i < (int)hit_row.size(); ++i) {
         int irow = hit_row[i] + row_offset[hit_column[i]];
         if (hit_row[i] == 0) {
            hittime_col->Fill(hit_column[i], hit_time[i]);
            deltatr_col->Fill(hit_column[i], hit_time[i] - tRF);
            ++column_count[hit_column[i]];
         }
         else {
            hittime_row->Fill(irow, hit_time[i]);
            deltatr_row->Fill(irow, hit_time[i] - tRF);
            ++row_count[irow];
         }
         for (int j=0; j < i; ++j) {
            if (hit_time[i] < FADC250_TCUT0 || hit_time[j] < FADC250_TCUT0 ||
                hit_time[i] > FADC250_TCUT1 || hit_time[j] > FADC250_TCUT1)
            {
               continue;
            }
            if (hit_row[i] == 0 and hit_row[j] == 0) {
               if (hit_column[i] == hit_column[j] + 1) {
                  deltatn_col->Fill(hit_column[j], hit_time[i] - hit_time[j]);
               }
               else if (hit_column[i] == hit_column[j] - 1) {
                  deltatn_col->Fill(hit_column[i], hit_time[j] - hit_time[i]);
               }
               else if (abs(hit_column[i] - hit_column[j]) > 15) {
                  deltatf_col->Fill(hit_column[i], hit_time[i] - hit_time[j]);
                  deltatf_col->Fill(hit_column[j], hit_time[j] - hit_time[i]);
               }
            }
            else if (hit_row[i] > 0 and hit_row[j] > 0) {
               int jrow = hit_row[j] + row_offset[hit_column[j]];
               if (hit_column[i] == hit_column[j]) {
                  if (hit_row[i] == hit_row[j] + 1) {
                     deltatn_row->Fill(jrow, hit_time[i] - hit_time[j]);
                  }
                  else if (hit_row[i] == hit_row[j] - 1) {
                     deltatn_row->Fill(irow, hit_time[j] - hit_time[i]);
                  }
               }
               else {
                  deltatf_row->Fill(irow, hit_time[i] - hit_time[j]);
                  deltatf_row->Fill(jrow, hit_time[j] - hit_time[i]);
               }
            }
            else if (hit_row[i] == 0 && hit_row[j] > 0) {
               int jrow = hit_row[j] + row_offset[hit_column[j]];
               if (hit_column[i] == hit_column[j]) {
                  deltati_row->Fill(jrow, hit_time[j] - hit_time[i]);
               }
            }
         }
      }
      hit_row.clear();
      hit_column.clear();
      hit_time.clear();
      hit_peak.clear();
      for (int i=1; i < 103; ++i)
         hitrate_col->Fill(i, column_count[i]);
      for (int i=1; i < 50; ++i)
         hitrate_row->Fill(i, row_count[i]);
   }
   last_eventno = *eventno;

   hit_row.push_back(*row);
   hit_column.push_back(*col);
   hit_time.push_back(*pt * 0.0625 - toffset[*col][*row]);
   hit_peak.push_back(*peak);
   tRF = *rftime;

   return kTRUE;
}

void fadc250_time_calib::SlaveTerminate()
{
   // The SlaveTerminate() function is called after all entries or objects
   // have been processed. When running with PROOF SlaveTerminate() is called
   // on each slave server.

}

void fadc250_time_calib::Terminate()
{
   // The Terminate() function is the last function to be called during
   // a query. It always runs on the client, it can be used to present
   // the results graphically or save the results to file.

}
