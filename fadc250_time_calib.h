//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Tue Jan 17 07:46:14 2023 by ROOT version 6.22/06
// from TTree fadc/
// found on file: TAGMtrees_120187.root
//////////////////////////////////////////////////////////

#ifndef fadc250_time_calib_h
#define fadc250_time_calib_h

#include <TROOT.h>
#include <TChain.h>
#include <TFile.h>
#include <TSelector.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <TTreeReaderArray.h>

#include <vector>
#include <TH2D.h>

// Headers needed by this particular selector


class fadc250_time_calib : public TSelector {
public :
   TTreeReader     fReader;  //!the tree reader
   TTree          *fChain = 0;   //!pointer to the analyzed TTree or TChain

   // Histograms
   TH2D *hitrate_col;  // rate vs column 1..102
   TH2D *hitrate_row;  // rate vs row 1..20 (column 9, 27, 81, 99)
   TH2D *hittime_col;  // time vs column 1..102
   TH2D *hittime_row;  // time vs row 1..20 (column 9, 27, 81, 99)
   TH2D *deltatr_col;  // t_tagm - t_rf vs column 1..102
   TH2D *deltatr_row;  // t_tagm - t_rf row 1..20 (column 9, 27, 81, 99)
   TH2D *deltatn_col;  // t-diff for neighboring columns vs column 1..102
   TH2D *deltatn_row;  // t-diff for neighboring rows vs row 1..20
   TH2D *deltatf_col;  // t-diff for separated columns vs column 1..102
   TH2D *deltatf_row;  // t-diff for separated rows vs row 1..20
   TH2D *deltati_row;  // t-diff for rows with column sum vs row 1..20

   int last_eventno;   // keep track of event boundaries
   std::vector<int> hit_row;
   std::vector<int> hit_column;
   std::vector<double> hit_time;
   std::vector<double> hit_peak;
   double tRF;

   // Readers to access the data (delete the ones you do not need).
   TTreeReaderValue<Int_t> runno = {fReader, "runno"};
   TTreeReaderValue<Int_t> eventno = {fReader, "eventno"};
   TTreeReaderValue<Int_t> row = {fReader, "row"};
   TTreeReaderValue<Int_t> col = {fReader, "col"};
   TTreeReaderValue<Int_t> pi = {fReader, "pi"};
   TTreeReaderValue<Int_t> pt = {fReader, "pt"};
   TTreeReaderValue<Int_t> ped = {fReader, "ped"};
   TTreeReaderValue<Int_t> qf = {fReader, "qf"};
   TTreeReaderValue<Int_t> npi = {fReader, "npi"};
   TTreeReaderValue<Int_t> nped = {fReader, "nped"};
   TTreeReaderValue<Int_t> peak = {fReader, "peak"};
   TTreeReaderValue<Double_t> rftime = {fReader, "rftime"};


   fadc250_time_calib(TTree * /*tree*/ =0) { }
   virtual ~fadc250_time_calib() { }
   virtual Int_t   Version() const { return 2; }
   virtual void    Begin(TTree *tree);
   virtual void    SlaveBegin(TTree *tree);
   virtual void    Init(TTree *tree);
   virtual Bool_t  Notify();
   virtual Bool_t  Process(Long64_t entry);
   virtual Int_t   GetEntry(Long64_t entry, Int_t getall = 0) { return fChain ? fChain->GetTree()->GetEntry(entry, getall) : 0; }
   virtual void    SetOption(const char *option) { fOption = option; }
   virtual void    SetObject(TObject *obj) { fObject = obj; }
   virtual void    SetInputList(TList *input) { fInput = input; }
   virtual TList  *GetOutputList() const { return fOutput; }
   virtual void    SlaveTerminate();
   virtual void    Terminate();

   ClassDef(fadc250_time_calib,0);

};

#endif

#ifdef fadc250_time_calib_cxx
void fadc250_time_calib::Init(TTree *tree)
{
   // The Init() function is called when the selector needs to initialize
   // a new tree or chain. Typically here the reader is initialized.
   // It is normally not necessary to make changes to the generated
   // code, but the routine can be extended by the user if needed.
   // Init() will be called many times when running on PROOF
   // (once per file to be processed).

   fReader.SetTree(tree);
}

Bool_t fadc250_time_calib::Notify()
{
   // The Notify() function is called when a new file is opened. This
   // can be either for a new TTree in a TChain or when when a new TTree
   // is started when using PROOF. It is normally not necessary to make changes
   // to the generated code, but the routine can be extended by the
   // user if needed. The return value is currently not used.

   return kTRUE;
}


#endif // #ifdef fadc250_time_calib_cxx
