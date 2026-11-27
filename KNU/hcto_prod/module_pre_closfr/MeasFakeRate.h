#ifndef HcToWA_MeasFakeRate_h
#define HcToWA_MeasFakeRate_h

// Tight-to-loose (fake) rates of muons and electrons for 2024 (ChargedHiggsAnalysisV4
// docs/PLAN_BkgEst.md; decisions F5, F6, F9 in docs/LOG_BkgEst.md). Port of the
// B2G-25-013 MeasFakeRateV4 with its selection, rewritten for speed:
//   trigger decision first; one object pass with loose/tight bits; the selection
//   variations (away-jet pT, b tag) as cuts on cached quantities; histograms booked
//   once and addressed by index; object systematics only for the prompt-normalization
//   transfer, in the prompt (non-QCD) MC.
// Modes (user flags): MeasMuFR (paths Mu8, Mu17_TrkIsoVVL; data Muon0/1),
//                     MeasElFR (Ele8/12/23_CaloIdL_TrackIdL_IsoVL_PFJet30; EGamma0/1).
// Selection (V4): exactly one (measurement) or two (Z region) loose leptons of the
//   measured flavour, no loose lepton of the other flavour (pT > 10 GeV); measured
//   muon pT > 10, electron pT > 15 GeV; tight jets (pT > 20, |eta| < 2.5, cleaned
//   from loose leptons with dR < 0.4); away jet = leading jet with dR(l, j) > 0.7.
//   Per path: lepton pT above the path's offline (trigger-safe) cut; no trigger-object
//   matching (user, 2026-11-25: same treatment for muons and electrons; NanoAODv15 has no
//   trigger object for the Mu8/Mu17_TrkIsoVVL legs, docs/LOG_BkgEst.md). In the Z region
//   the leading lepton carries the cut; |m(ll) - 91.2| window is applied in the script
//   (m(ll) histograms, OS and SS).
// Regions (single lepton): QCD (MET < 25 and MT < 25 GeV), W (MT > 60 GeV), Inc.
// Selection variations: away-jet pT > 40 (nominal), 20, 30, 60 GeV; nominal + >= 1
//   b-tagged jet (UParT Medium, pT > 20 GeV; MC with the method-1a b-tag weight).
// MC classes of the measured lepton: prompt (genPartFlav 1, 15), conv (22),
//   nonprompt by the hadron flavour of the lepton's NanoAOD jet: b, c, light,
//   other (no jet or no gen jet).
// Histograms: 2D (|eta| (electrons |eta_SC|), pTcorr), pTcorr = pT (1 + max(0, miniIso - 0.1)),
//   fine bins (merged in the script). MC weight: MCweight x lumi x PU x top pT (TT powheg).
// Prompt-MC lanes (F5 c): JES, JER, unclustered MET, muon and electron scale and
//   resolution, PU, each up/down; leptons fixed (IDs central), pT, MET, MT and jets
//   recomputed; filled for the nominal selection: QCD-region 2D and Z-region m(ll).

#include <HcToWA/HcToWABase.h>

#include <array>
#include <cstdint>
#include <string>
#include <vector>

class MeasFakeRate : public HcToWABase {
public:
    MeasFakeRate();
    ~MeasFakeRate();

    void initializeAnalyzer() override;
    void executeEvent() override;

    enum Region : int { kQCD = 0, kW, kInc, kNRegions };
    enum Sel : int { kNom = 0, kAway20, kAway30, kAway60, kBTag, kNSels };
    enum Lane : int {
        kJESUp = 0, kJESDown, kJERUp, kJERDown, kUEUp, kUEDown,
        kMuEnUp, kMuEnDown, kMuResUp, kMuResDown, kElEnUp, kElEnDown, kElResUp, kElResDown,
        kPUUp, kPUDown, kNLanes
    };

private:
    struct Path {
        std::string hlt, label;
        bool muon;
        float offPt; // offline (trigger-safe) pT cut
        bool fired = false;
    };
    struct Mode {
        bool muon;
        std::vector<Path> paths;
        // booked histograms, addressed by index
        std::vector<Hist2DHandle> h2;      // [p][region][id][sel][cls]
        std::vector<Hist1DHandle> hZ;      // [p][id][sel][cls][os/ss]
        std::vector<Hist2DHandle> lane2;   // [lane][p][id]
        std::vector<Hist1DHandle> laneZ;   // [lane][p][id]
        std::vector<Hist1DHandle> ctl;     // [p][region][id][cls2][var]
        std::vector<Hist1DHandle> ctlZ;    // [p][id][cls2][var]
        Hist1DHandle cutflow;
    };
    // Per-event quantities of one lane (central or an object variation).
    struct Kin {
        float lepPt[2] = {0.f, 0.f};
        float metPt = 0.f, metPhi = 0.f;
        float awayPt = -1.f; // leading jet with dR > 0.7 from lepton 0
        int nB = 0;
        float btagW = 1.f;
    };

    void BookMode(Mode &m);
    void RunMode(Mode &m, const Event &ev, float w0);
    void ComputeKin(const Mode &m, const std::vector<std::size_t> &lep, int lane, const Event &ev, Kin &k);
    float LepPt(bool muon, std::size_t i, int lane) const;
    int LepClass(bool muon, std::size_t i) const;
    bool PassSel(int s, const Kin &k) const;

    std::size_t I2(const Mode &m, int p, int r, int id, int s, int c) const {
        return (((static_cast<std::size_t>(p) * kNRegions + r) * 2 + id) * kNSels + s) * nCls_ + c;
    }
    std::size_t IZ(int p, int id, int s, int c, int sign) const {
        return ((((static_cast<std::size_t>(p) * 2 + id) * kNSels + s) * nCls_ + c) * 2) + sign;
    }

    bool doMu_ = false, doEl_ = false; //!
    bool promptMC_ = false;            //!
    int nCls_ = 1;                     //!
    float lumi_ = -1.f;                //!
    std::array<float, 3> pu_{};        //! nom, up, down
    Mode mu_, el_;                     //!
    MuonViewCollection muons_;         //!
    ElectronViewCollection electrons_; //!
    JetViewCollection jets_;           //!
    std::vector<std::uint8_t> muBits_; //!
    std::vector<std::uint8_t> elBits_; //!
    std::vector<std::size_t> muLoose_, elLoose_; //! pT-sorted, pT > 10 GeV
    Particle rawMET_;                  //!
    float dMetJetNom_[2] = {0.f, 0.f}, dMetMuNom_[2] = {0.f, 0.f}, dMetElNom_[2] = {0.f, 0.f}; //!
};

#endif
