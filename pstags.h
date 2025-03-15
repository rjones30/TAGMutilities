//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Sun Jan 22 03:56:16 2023 by ROOT version 6.22/06
// from TTree pstags/PS tag study
// found on file: root://nod26.phys.uconn.edu/Gluex/beamline/PStags-1-2023/PStagstudy2_120253.root
//////////////////////////////////////////////////////////

#ifndef pstags_h
#define pstags_h

#include <TROOT.h>
#include <TChain.h>
#include <TFile.h>
#include <TSelector.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <TTreeReaderArray.h>

#include <TH2D.h>
#include <TProfile.h>

// Headers needed by this particular selector


class pstags : public TSelector {
public :
   TTreeReader     fReader;  //!the tree reader
   TTree          *fChain = 0;   //!pointer to the analyzed TTree or TChain

   TH2D *Etagm_Epair;
   TProfile *Epair_Etagm;
   TH2D *ttagm_pair;

   static double endpoint_energy; // GeV
   static double endpoint_calib;  // GeV
   static double scaled_energy[2][102];

   // Readers to access the data (delete the ones you do not need).
   TTreeReaderValue<UInt_t> runno = {fReader, "runno"};
   TTreeReaderValue<UInt_t> eventno = {fReader, "eventno"};
   TTreeReaderValue<ULong64_t> timestamp = {fReader, "timestamp"};
   TTreeReaderValue<Int_t> nrf = {fReader, "nrf"};
   TTreeReaderArray<Int_t> rf_sys = {fReader, "rf_sys"};
   TTreeReaderArray<Double_t> rf_time = {fReader, "rf_time"};
   TTreeReaderValue<Int_t> ntagm = {fReader, "ntagm"};
   TTreeReaderArray<Int_t> tagm_seqno = {fReader, "tagm_seqno"};
   TTreeReaderArray<Int_t> tagm_channel = {fReader, "tagm_channel"};
   TTreeReaderArray<Float_t> tagm_peak = {fReader, "tagm_peak"};
   TTreeReaderArray<Float_t> tagm_pint = {fReader, "tagm_pint"};
   TTreeReaderArray<Float_t> tagm_tadc = {fReader, "tagm_tadc"};
   TTreeReaderArray<Float_t> tagm_ttdc = {fReader, "tagm_ttdc"};
   TTreeReaderArray<Float_t> tagm_time = {fReader, "tagm_time"};
   TTreeReaderArray<Float_t> tagm_Etag = {fReader, "tagm_Etag"};
   TTreeReaderArray<Float_t> tagm_pmax = {fReader, "tagm_pmax"};
   TTreeReaderArray<Float_t> tagm_ped = {fReader, "tagm_ped"};
   TTreeReaderArray<Int_t> tagm_multi = {fReader, "tagm_multi"};
   TTreeReaderArray<Int_t> tagm_qf = {fReader, "tagm_qf"};
   TTreeReaderArray<Int_t> tagm_bg = {fReader, "tagm_bg"};
   TTreeReaderArray<Int_t> tagm_has_adc = {fReader, "tagm_has_adc"};
   TTreeReaderArray<Int_t> tagm_has_tdc = {fReader, "tagm_has_tdc"};
   TTreeReaderArray<Int_t> tagm_nped = {fReader, "tagm_nped"};
   TTreeReaderArray<Int_t> tagm_nint = {fReader, "tagm_nint"};
   TTreeReaderValue<Int_t> ntagh = {fReader, "ntagh"};
   TTreeReaderArray<Int_t> tagh_seqno = {fReader, "tagh_seqno"};
   TTreeReaderArray<Int_t> tagh_counter = {fReader, "tagh_counter"};
   TTreeReaderArray<Float_t> tagh_peak = {fReader, "tagh_peak"};
   TTreeReaderArray<Float_t> tagh_pint = {fReader, "tagh_pint"};
   TTreeReaderArray<Float_t> tagh_tadc = {fReader, "tagh_tadc"};
   TTreeReaderArray<Float_t> tagh_ttdc = {fReader, "tagh_ttdc"};
   TTreeReaderArray<Float_t> tagh_time = {fReader, "tagh_time"};
   TTreeReaderArray<Float_t> tagh_Etag = {fReader, "tagh_Etag"};
   TTreeReaderArray<Float_t> tagh_pmax = {fReader, "tagh_pmax"};
   TTreeReaderArray<Float_t> tagh_ped = {fReader, "tagh_ped"};
   TTreeReaderArray<Int_t> tagh_multi = {fReader, "tagh_multi"};
   TTreeReaderArray<Int_t> tagh_qf = {fReader, "tagh_qf"};
   TTreeReaderArray<Int_t> tagh_bg = {fReader, "tagh_bg"};
   TTreeReaderArray<Int_t> tagh_has_adc = {fReader, "tagh_has_adc"};
   TTreeReaderArray<Int_t> tagh_has_tdc = {fReader, "tagh_has_tdc"};
   TTreeReaderArray<Int_t> tagh_nped = {fReader, "tagh_nped"};
   TTreeReaderArray<Int_t> tagh_nint = {fReader, "tagh_nint"};
   TTreeReaderValue<Int_t> nbeam = {fReader, "nbeam"};
   TTreeReaderArray<Int_t> beam_sys = {fReader, "beam_sys"};
   TTreeReaderArray<Float_t> beam_E = {fReader, "beam_E"};
   TTreeReaderArray<Float_t> beam_t = {fReader, "beam_t"};
   TTreeReaderArray<Float_t> beam_z = {fReader, "beam_z"};
   TTreeReaderValue<Int_t> npairps = {fReader, "npairps"};
   TTreeReaderArray<Float_t> Epair = {fReader, "Epair"};
   TTreeReaderArray<Float_t> tpair = {fReader, "tpair"};
   TTreeReaderArray<Float_t> psleft_peak = {fReader, "psleft_peak"};
   TTreeReaderArray<Float_t> psright_peak = {fReader, "psright_peak"};
   TTreeReaderArray<Float_t> psleft_pint = {fReader, "psleft_pint"};
   TTreeReaderArray<Float_t> psright_pint = {fReader, "psright_pint"};
   TTreeReaderArray<Float_t> psleft_time = {fReader, "psleft_time"};
   TTreeReaderArray<Float_t> psright_time = {fReader, "psright_time"};
   TTreeReaderArray<Float_t> psEleft = {fReader, "psEleft"};
   TTreeReaderArray<Float_t> psEright = {fReader, "psEright"};
   TTreeReaderArray<Float_t> pstleft = {fReader, "pstleft"};
   TTreeReaderArray<Float_t> pstright = {fReader, "pstright"};
   TTreeReaderArray<Int_t> nleft_ps = {fReader, "nleft_ps"};
   TTreeReaderArray<Int_t> nright_ps = {fReader, "nright_ps"};
   TTreeReaderValue<Int_t> npairpsc = {fReader, "npairpsc"};
   TTreeReaderArray<Int_t> pscleft_seqno = {fReader, "pscleft_seqno"};
   TTreeReaderArray<Int_t> pscright_seqno = {fReader, "pscright_seqno"};
   TTreeReaderArray<Int_t> pscleft_module = {fReader, "pscleft_module"};
   TTreeReaderArray<Int_t> pscright_module = {fReader, "pscright_module"};
   TTreeReaderArray<Float_t> pscleft_peak = {fReader, "pscleft_peak"};
   TTreeReaderArray<Float_t> pscright_peak = {fReader, "pscright_peak"};
   TTreeReaderArray<Float_t> pscleft_pint = {fReader, "pscleft_pint"};
   TTreeReaderArray<Float_t> pscright_pint = {fReader, "pscright_pint"};
   TTreeReaderArray<Float_t> pscleft_ttdc = {fReader, "pscleft_ttdc"};
   TTreeReaderArray<Float_t> pscright_ttdc = {fReader, "pscright_ttdc"};
   TTreeReaderArray<Float_t> pscleft_tadc = {fReader, "pscleft_tadc"};
   TTreeReaderArray<Float_t> pscright_tadc = {fReader, "pscright_tadc"};
   TTreeReaderArray<Float_t> pscleft_t = {fReader, "pscleft_t"};
   TTreeReaderArray<Float_t> pscright_t = {fReader, "pscright_t"};
   TTreeReaderArray<Float_t> pscleft_ped = {fReader, "pscleft_ped"};
   TTreeReaderArray<Float_t> pscright_ped = {fReader, "pscright_ped"};
   TTreeReaderArray<Int_t> pscleft_qf = {fReader, "pscleft_qf"};
   TTreeReaderArray<Int_t> pscright_qf = {fReader, "pscright_qf"};


   pstags(TTree * /*tree*/ =0) { }
   virtual ~pstags() { }
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

   ClassDef(pstags,0);

};

#endif

#ifdef pstags_cxx
void pstags::Init(TTree *tree)
{
   // The Init() function is called when the selector needs to initialize
   // a new tree or chain. Typically here the reader is initialized.
   // It is normally not necessary to make changes to the generated
   // code, but the routine can be extended by the user if needed.
   // Init() will be called many times when running on PROOF
   // (once per file to be processed).

   fReader.SetTree(tree);
}

Bool_t pstags::Notify()
{
   // The Notify() function is called when a new file is opened. This
   // can be either for a new TTree in a TChain or when when a new TTree
   // is started when using PROOF. It is normally not necessary to make changes
   // to the generated code, but the routine can be extended by the
   // user if needed. The return value is currently not used.

   return kTRUE;
}


#endif // #ifdef pstags_cxx
