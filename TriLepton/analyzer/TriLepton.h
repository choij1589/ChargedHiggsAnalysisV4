#ifndef HcToWA_TriLepton_h
#define HcToWA_TriLepton_h

// Trilepton analyzer for 2024 (ChargedHiggsAnalysisV4 docs/PLAN_ConvSF.md, decisions C1-C6 of
// 2026-11-27): signal region and the Z+fake, Z gamma and WZ control regions of B2G-25-013
// (old SKNano PyAnalyzers/PromptAnalyzer.py _selectSREvent / _selectCREvent and MatrixAnalyzer),
// on the HcToWABase objects with the ClosFakeRate selection code. Central lane only (systematic
// lanes later).
//
// Channels (user flags, both allowed in one job): Run1E2Mu (e mu mu), Run3Mu (mu mu mu). Data:
// MuonEG feeds e mu mu only, Muon0/1 mu mu mu only.
// Objects: loose (= veto) muons pT > 10 GeV, |eta| < 2.4; veto electrons loose pT > 10 GeV, loose
//   electrons pT > 15 GeV, |eta| < 2.5; jets tight ID, pT > 20 GeV, |eta| < 2.5, dR > 0.4 from the
//   veto leptons; b jets UParT Medium; MET = PUPPI with the jet, muon and electron propagation.
// Leptons: e mu mu = exactly 2 loose muons and 1 veto electron that is loose with pT > 15 GeV;
//   mu mu mu = exactly 3 loose muons and no veto electron. "Tight" event: all leptons tight;
//   otherwise >= 1 loose-not-tight lepton (nonprompt sideband).
// Common cuts: e mu mu: EMu paths, (mu1 > 25 and e > 15) or (mu1 > 10 and e > 25) GeV (raw pT),
//   OS muons, m(mumu) > 12 GeV; mu mu mu: DblMu path, 20/10/10 GeV, |sum q| = 1, both OS pairs
//   > 12 GeV. Kinematics after the cuts use pT_corr = pT (1 + max(0, miniIso - 0.1)) (= pT for tight).
// Regions (B2G-25-013):
//   SR    >= 2 jets, >= 1 b jet
//   ZFake >= 2 jets, 0 b jets, an OS pair on-Z (|m - 91.2| < 10 GeV)
//   ZG    MET < 40 GeV, 0 b jets, all OS pairs off-Z, |m(3l) - 91.2| < 10 GeV
//   WZ    MET > 40 GeV, 0 b jets, an OS pair on-Z
// Lanes (directory <channel>/<region>/<lane>):
//   MC, tight events: Central; DY 2J samples also DYGVeto (events with a generator photon in the
//     DYGto2LG phase space removed: cross-check C1 (b)).
//   Data, tight events: Central, control regions only. **The SR data are blinded** (user,
//     2026-11-27): tight data events in the SR are not written anywhere; for tight data events
//     only the control-region bins of the cutflow are filled (no preselection bins).
//   Data, loose-not-tight events: Nonprompt, Nonprompt_Up, Nonprompt_Down with
//     w = -prod(-f / (1 - f)) over the loose-not-tight leptons, f from
//     data/2024/FakeRate/fakerate_HcToWA.json (Central, Total_Up, Total_Down; F1).
// MC weight (C5): MCweight x lumi x PU x electron reco SF (POG) x muon and electron ID SFs (ours)
//   x trigger SF (DblMu / EMu, T1) x b-tag weight (method 1a); no top pT, no muon reco SF.
// Conversion samples (DYto2*_2J, DYGto2LG, TTG_1J; C2): an event is kept only if >= 1 lepton is of
//   a conversion type (4, 5, -5, -6) and no lepton is of type -1 to -4 (GenLeptonType).
// Stitching (C1): TTG_1J and DYGto2LG_1J_MLL50 photon-pT bins are made exclusive with the leading
//   LHE photon pT (inclusive < 100, PTG100 < 200, PTG200 < 400 (DYG) / open (TTG), PTG400 < 600).
// Object histograms (B2G-25-013 PromptAnalyzer fillObjects / _fillCRObjects): ZCand_mass = the Z
//   candidate (e mu mu: the muon pair; mu mu mu: the OS pair closer to 91.2 GeV); nonZLep_{pt,eta} = the
//   lepton outside the Z candidate (e mu mu: the electron; mu mu mu: the same-sign muon not in the Z
//   candidate) = B2G's "nonprompt" lepton, and in the ZG CR its "conversion" lepton; jets_1_{pt,eta} =
//   leading jet. trilep_mass is the Z candidate of the ZG CR.
// Truth diagnostics (MC): event category (0 prompt, 1 conversion, 2 conversion + hadronic/unmatched
//   lepton (vetoed), 3 hadronic/unmatched, 4 a type-0 lepton) before the conversion filter
//   (<channel>/event_category_prefilter, after the pair cuts) and per region with the lepton types
//   (truth/); LHE and generator photon spectra (diag/).

#include <HcToWA/GenLeptonType.h>
#include <HcToWA/HcToWABase.h>

#include <array>
#include <cstdint>
#include <string>
#include <vector>

class TriLepton : public HcToWABase {
public:
    TriLepton();
    ~TriLepton();

    void initializeAnalyzer() override;
    void executeEvent() override;

    enum Ch : int { k1E2Mu = 0, k3Mu, kNCh };
    enum Region : int { kSR = 0, kZFake, kZG, kWZ, kNReg };
    enum Lane : int { kCentral = 0, kDYGVeto, kNonprompt, kNonpromptUp, kNonpromptDown, kNLane };
    enum Var : int {
        kM3l = 0, kPairMass, kPairLowM, kPairHighM, kMu1Pt, kMu2Pt, kMu3Pt, kMu1Eta, kMu2Eta,
        kMu3Eta, kElPt, kElScEta, kNJets, kNBJets, kMET, kZMass, kNonZPt, kNonZEta, kJet1Pt, kJet1Eta, kNVar
    };

private:
    struct VarHists { std::array<Hist1DHandle, kNVar> h; };
    struct TruthHists {
        Hist1DHandle category;
        Hist1DHandle lepType;
        Hist2DHandle elTypeVsFlav;
    };
    struct Vals {
        float v[kNVar];
        bool has[kNVar];
    };

    void Book(VarHists &vh, const std::string &dir);
    static void Fill(VarHists &vh, const Vals &x, float w);
    float Rate(bool muon, float absEta, float ptcorr, const std::string &key) const;
    float LeadingLHEPhotonPt();
    bool GenPhotonInDYGPhaseSpace();

    bool run1E2Mu_ = false, run3Mu_ = false; //!
    bool isConvSample_ = false, isDY2J_ = false, hasLHEPhoton_ = false; //!
    float stitchMax_ = -1.f; //! upper LHE photon pT (< 0: none)
    float lumi_ = -1.f;      //!
    std::array<Hist1DHandle, kNCh> cutflow_, cutflowLNT_, truthPre_; //! truthPre_: category before the conversion filter (MC)
    std::array<std::array<std::array<VarHists, kNLane>, kNReg>, kNCh> h_; //!
    std::array<std::array<bool, kNLane>, kNReg> booked_{}; //!
    std::array<std::array<TruthHists, kNReg>, kNCh> truth_; //!
    Hist1DHandle hLHEPhoPt_, hLHEPhoDRl_, hLHEPhoEta_, hGenPhoPt_, hGenPhoDRl_, hStitch_; //!
    std::unique_ptr<correction::CorrectionSet> frSet_; //!
    correction::Correction::Ref frMu_, frEl_; //!
    GenLeptonType truthTool_; //!
    GenViewCollection gens_;  //!
    MuonViewCollection muons_;         //!
    ElectronViewCollection electrons_; //!
    JetViewCollection jets_;           //!
    std::vector<std::uint8_t> muBits_; //!
    std::vector<std::uint8_t> elBits_; //!
};

#endif
