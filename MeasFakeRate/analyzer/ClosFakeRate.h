#ifndef HcToWA_ClosFakeRate_h
#define HcToWA_ClosFakeRate_h

// MC closure of the nonprompt (fake-factor) method for 2024 (ChargedHiggsAnalysisV4
// docs/PLAN_BkgEst.md step 4, criterion F3 decided 2026-11-27). Port of the B2G-25-013
// ClosFakeRate / MatrixAnalyzer selections on the HcToWABase objects (as DiLepton).
// Channels (user flags, both allowed in one job): Run1E2Mu (e mu mu), Run3Mu (mu mu mu).
// Objects: loose muons pT > 10 GeV |eta| < 2.4 (= veto muons); veto electrons loose pT > 10,
//   loose electrons pT > 15 GeV, |eta| < 2.5; tight electrons need pT > 15 GeV; pT = corrected pT.
//   Jets: tight ID, pT > 20, |eta| < 2.5, dR > 0.4 from veto leptons; b jets UParT Medium.
//   Event filters and the jet veto map as DiLepton.
// e mu mu: exactly 2 loose muons, 1 veto (= loose) electron; EMu paths (Mu23_Ele12_DZ or
//   Mu8_Ele23_DZ); (mu1 > 25 and e > 15) or (mu1 > 10 and e > 25) GeV; then the loose leptons are
//   scaled to pT_corr = pT (1 + max(0, miniIso - 0.1)); OS muons, m(mumu) > 12 GeV; >= 2 jets, >= 1 b jet.
// mu mu mu: exactly 3 loose muons, no veto electron; DblMu path (Mu17_Mu8_DZ_Mass3p8); pT > 20,
//   10, 10 GeV; pT_corr scaling; |sum q| = 1, both OS pair masses > 12 GeV; >= 2 jets, >= 1 b jet;
//   also split on-Z (an OS pair with |m - 91.2| < 10 GeV) and off-Z.
// Regions: SR = all leptons tight (observed); SB = at least one loose-not-tight lepton, weighted by
//   w = -prod(-f / (1 - f)) over the loose-not-tight leptons (eps_p = 1, F4), f from
//   data/2024/FakeRate/fakerate_HcToWA.json (FakeRate_Muon |eta|, FakeRate_Electron |eta_SC|; pT_corr)
//   for each rate set: MC_QCD (pass/fail, F3), MC_TT, Central and the data variations.
// Generator splits (MC, diagnostics): SB with MC_QCD rates for "a loose-not-tight lepton is prompt"
//   (genPartFlav 1 or 15) vs "all loose-not-tight leptons nonprompt"; SR events with all leptons prompt.
// MC weight: MCweight x lumi x PU (no top pT, user 2026-11-27; no ID, trigger or b-tag SFs: MC closure).

#include <HcToWA/HcToWABase.h>

#include <array>
#include <cstdint>
#include <string>
#include <vector>

class ClosFakeRate : public HcToWABase {
public:
    ClosFakeRate();
    ~ClosFakeRate();

    void initializeAnalyzer() override;
    void executeEvent() override;

    enum Ch : int { k1E2Mu = 0, k3Mu, k3MuOnZ, k3MuOffZ, kNCh };
    enum Var : int {
        kPairMass = 0, kPairLowM, kPairHighM, kMu1Pt, kMu2Pt, kMu3Pt, kElPt, kElScEta,
        kNJets, kNBJets, kMET, kNVar
    };

private:
    struct VarHists { std::array<Hist1DHandle, kNVar> h; };
    struct Vals {
        float v[kNVar];
        bool has[kNVar];
    };

    void Book(VarHists &vh, const std::string &dir);
    void Fill(VarHists &vh, const Vals &x, float w);
    float Rate(bool muon, float absEta, float ptcorr, const std::string &key) const;

    bool run1E2Mu_ = false, run3Mu_ = false; //!
    float lumi_ = -1.f;                      //!
    std::vector<std::string> keys_;          //! rate sets
    std::array<Hist1DHandle, kNCh> cutflow_; //!
    std::array<VarHists, kNCh> hSR_, hSRAllPrompt_, hSBPromptLNT_, hSBNonpromptLNT_; //!
    std::array<std::vector<VarHists>, kNCh> hSB_; //! [ch][key]
    std::unique_ptr<correction::CorrectionSet> frSet_; //!
    correction::Correction::Ref frMu_, frEl_; //!
    MuonViewCollection muons_;         //!
    ElectronViewCollection electrons_; //!
    JetViewCollection jets_;           //!
    std::vector<std::uint8_t> muBits_; //!
    std::vector<std::uint8_t> elBits_; //!
};

#endif
