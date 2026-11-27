#ifndef HcToWA_Skim_TriLep_h
#define HcToWA_Skim_TriLep_h

// Trilepton skim for the 2024 TriLepton regions (port of the B2G-25-013
// Skim_TriLep.cc). Keeps the full input schema for events with
//   >= 3 leptons (muons |eta| < 2.4, electrons |eta| < 2.5, no ID), NanoAOD pT > 8 GeV,
//   leading lepton pT > 15 GeV.
// No corrections are loaded: the cuts use the NanoAOD pT, with margin below the
// analysis thresholds (10 GeV) for the momentum corrections.
// Run with SKNano.py --skimming_mode; output: Skim_TriLep_<sample>.

#include <AnalyzerFramework/AnalyzerCore.h>

#include <vector>

class Skim_TriLep : public AnalyzerCore {
public:
    Skim_TriLep();
    ~Skim_TriLep();

    void initializeAnalyzer() override;
    void executeEvent() override;
    void WriteHist() override;

    static constexpr float kMinPt = 8.f;
    static constexpr float kLeadPt = 15.f;
    static constexpr float kMuonEta = 2.4f;
    static constexpr float kElectronEta = 2.5f;

private:
    std::vector<Long64_t> selected_; //!
    Long64_t nSeen_ = 0;             //!

};

#endif
