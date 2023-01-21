//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Fri Jun 24 18:35:51 2022 by ROOT version 6.22/06
// from TTree fadc/
// found on file: TAGMtrees_100597.root
//////////////////////////////////////////////////////////

#ifndef doublets_h
#define doublets_h

#include <TROOT.h>
#include <TChain.h>
#include <TH2D.h>
#include <TFile.h>
#include <TSelector.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <TTreeReaderArray.h>

// Headers needed by this particular selector


class doublets : public TSelector {
public :
   TTreeReader     fReader;  //!the tree reader
   TTree          *fChain = 0;   //!pointer to the analyzed TTree or TChain
   TH2D *h2corr;

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


   doublets(TTree * /*tree*/ =0) { }
   virtual ~doublets() { }
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

   ClassDef(doublets,0);

};

#endif

#ifdef doublets_cxx
void doublets::Init(TTree *tree)
{
   // The Init() function is called when the selector needs to initialize
   // a new tree or chain. Typically here the reader is initialized.
   // It is normally not necessary to make changes to the generated
   // code, but the routine can be extended by the user if needed.
   // Init() will be called many times when running on PROOF
   // (once per file to be processed).

   fReader.SetTree(tree);
}

Bool_t doublets::Notify()
{
   // The Notify() function is called when a new file is opened. This
   // can be either for a new TTree in a TChain or when when a new TTree
   // is started when using PROOF. It is normally not necessary to make changes
   // to the generated code, but the routine can be extended by the
   // user if needed. The return value is currently not used.

   return kTRUE;
}


#endif // #ifdef doublets_cxx
