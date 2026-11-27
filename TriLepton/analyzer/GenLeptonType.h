#ifndef HcToWA_GenLeptonType_h
#define HcToWA_GenLeptonType_h

// Lepton truth classification of B2G-25-013, ported to SKNano 2.0 (NanoAODv15 GenPart through
// GenView) for ChargedHiggsAnalysisV4 docs/PLAN_ConvSF.md C2. Source: old SKNanoAnalyzer
// Analyzers/src/AnalyzerCore.cc (GetLeptonType, GetLeptonType_Public, GetGenMatchedLepton,
// GetGenMatchedPhoton, GetGenPhotonType, GetPrElType_InSameSCRange_Public, IsFromHadron,
// IsFinalPhotonSt23_Public, TrackGenSelfHistory).
//
// Types of a reconstructed lepton:
//   1 EW prompt (W, Z, H or hard process), 2 signal daughter, 3 daughter of a prompt tau,
//   4 internal conversion (gamma* from shower / t, W, Z, lepton radiation), 5 internal conversion
//   from a hard-process photon, 6 from an off-shell W (mother 37);
//  -1 unmatched and not a conversion, -2 hadron daughter, -3 daughter of a tau from a hadron or
//   parton, -4 internal conversion with hadronic origin, -5 external conversion of a hard-process
//   photon, -6 external conversion of a photon from t, W or a lepton; 0 error.
// Matching: status-1 generator lepton of the same flavour within dR < 0.1 (closest); without one, a
// generator photon (status 1, or 23 when that is the last copy) with pT > 10 GeV,
// |pT(l)/pT(gamma) - 1| < 0.5 and dR < 0.2 (closest). Types 4/5 of an electron are replaced by the
// type (1-3) of a prompt generator electron in the same supercluster range (|deta| < 0.1,
// |dphi| < 0.3), as the old code.
//
// Deviations from the old code (its intent, not its letter):
//  - IsFromHadron compares absolute PDG ids: the old code compared signed ids, so W-, anti-top,
//    positively charged leptons and negative hadrons stopped nothing in the ancestry walk.
//  - The same-supercluster search uses |dphi|: the old code used the signed DeltaPhi, so any
//    negative difference passed.

#include "GenView.h"

class GenLeptonType {
public:
    void SetEvent(const GenViewCollection *gens) {
        g_ = gens;
        st23Done_ = false;
    }
    // Type of a reconstructed lepton (electron: |pdg| 11, muon: 13).
    int Type(bool electron, float pt, float eta, float phi) const;
    // Type of a status-1 generator lepton (GetLeptonType_Public).
    int TypeOfGen(int idx) const;
    static bool IsConversion(int t) { return t == 4 || t == 5 || t == -5 || t == -6; }
    static bool IsHadronicOrUnmatched(int t) { return t <= -1 && t >= -4; }

private:
    int MatchLepton(int absPdg, float eta, float phi) const;
    int MatchPhoton(float pt, float eta, float phi) const;
    int PhotonType(int idx) const;
    int SameSCPromptElectronType(int idx) const;
    bool IsFromHadron(int idx) const;
    bool FinalPhotonIsStatus23() const;
    void SelfHistory(int idx, int &firstCopy, int &mother) const;
    static bool IsSignalPID(int pid);
    int N() const { return static_cast<int>(g_->size()); }
    const GenView G(int i) const { return (*g_)[i]; }

    const GenViewCollection *g_ = nullptr;
    mutable bool st23Done_ = false;
    mutable bool st23_ = false;
};

#endif
