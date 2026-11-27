#ifndef HcToWA_DiLepton_h
#define HcToWA_DiLepton_h

// Dilepton control regions for 2024 (port of the B2G-25-013 DiLepton.cc).
// Flags: RunDiMu, RunEMu, RunZEE (Z->ee electron-energy check with proxy EGM
// SFs, used nowhere else), RunSyst, RunNoJetVeto.
// Output: {DIMU,EMU,ZEE}/{lane}/..., {ALL,<CH>}/Central/cutflow,
//         JetEtaPhi/{BeforeEventVeto_Run3,PassedEventVeto_Run3}/eta_phi.

#include <HcToWA/HcToWABase.h>
#include "SystematicHelper.h"

#include <array>
#include <memory>
#include <string>
#include <vector>

class DiLepton : public HcToWABase {
public:
    DiLepton();
    ~DiLepton();

    void initializeAnalyzer() override;
    void executeEvent() override;

    enum Channel : int { kDIMU = 0, kEMU, kZEE, kNChannels };

    // Event-loop variations (one object/MET rebuild each).
    enum class EvtVar : int {
        Central = 0,
        JetResUp, JetResDown, JetEnUp, JetEnDown,
        ElectronResUp, ElectronResDown, ElectronEnUp, ElectronEnDown,
        MuonEnUp, MuonEnDown, MuonResUp, MuonResDown,
        UnclusteredEnUp, UnclusteredEnDown,
        N
    };

    // Event-weight factors.
    enum Factor : int {
        kFPU = 0, kFEleReco, kFBTag, kFEleIDProxy, kFEleTrigProxy, kFMuID, kFEleID, kNFactors
    };

    struct LepHists {
        Hist1DHandle pt, miniAODPt, eta, scEta, phi, mass, miniRelIso, sip3d, dz;
    };
    struct JetHists {
        Hist1DHandle pt, rawPt, originalPt, eta, phi, mass;
    };
    struct LaneHists {
        std::array<LepHists, 2> mu;
        std::array<LepHists, 2> el;
        std::array<JetHists, 5> jet;
        std::array<JetHists, 3> bjet;
        Hist1DHandle jetsSize, bjetsSize, metPt, metPhi, metDefPt, metDefPhi;
        Hist1DHandle pairPt, pairEta, pairPhi, pairMass, pairMassUncorr;
        Hist1DHandle nPV, nPVsGood, nTrueInt, nPileUp, rho;
    };
    struct WeightHists {
        Hist1DHandle genWeight, log10AbsGenWeight, mcWeight, pileupWeight,
            topPtWeight, eleRecoSF, btagSF, eleIDSFProxy, eleTrigSFProxy, muIDSF, eleIDSF, total;
    };

    // A weight-only lane: one factor swapped (value index), divided out
    // (notImplemented) or the top-pT weight multiplied in (topPt).
    struct WeightLane {
        std::string name;
        int factor = -1;
        int valueIndex = 0; // into FactorValues::vars[factor]
        bool notImplemented = false;
        bool topPt = false;
        LaneHists hists;
    };
    struct EvtLane {
        EvtVar var = EvtVar::Central;
        std::string name;
        LaneHists hists;
    };
    struct ChannelConf {
        bool enabled = false;
        std::string name;
        std::vector<EvtLane> evtLanes;       // [0] = Central
        std::vector<WeightLane> weightLanes; // MC + RunSyst only
        Hist1DHandle cutflow;
        WeightHists weights;
    };

    struct LepVals {
        float pt, miniAODPt, eta, scEta, phi, mass, miniRelIso, sip3d, dz;
    };
    struct JetVals {
        float pt, rawPt, originalPt, eta, phi, mass;
    };
    struct FillVals {
        int nMu = 0, nEl = 0, nJet = 0, nBJet = 0;
        std::array<LepVals, 2> mu{}, el{};
        std::array<JetVals, 5> jet{};
        std::array<JetVals, 3> bjet{};
        float jetsSize = 0, bjetsSize = 0;
        float metPt = 0, metPhi = 0, metDefPt = 0, metDefPhi = 0;
        bool hasPair = false;
        float pairPt = 0, pairEta = 0, pairPhi = 0, pairMass = 0, pairMassUncorr = 0;
        float nPV = 0, nPVsGood = 0, nTrueInt = 0, nPileUp = 0, rho = 0;
    };

    // nom/up/down (index 0/1/2) per factor; b tag has kNBTagLanes values.
    struct FactorValues {
        std::array<std::array<float, kNBTagLanes>, kNFactors> vars{};
        float nom(int f) const { return vars[f][0]; }
    };

private:
    // per-lane objects
    struct LepSel {
        std::vector<std::size_t> muLoose, muTight, elLoose, elTight; // raw idx, pT-sorted
    };

    void BookLane(LaneHists &h, int ch, const std::string &lane);
    void BookChannel(int ch);
    void BuildLeptons(EvtVar v, LepSel &out) const;
    float MuPt(const MuonView &m, EvtVar v) const;
    float ElPt(const ElectronView &e, EvtVar v) const;
    SelectedJetViewCollection BuildJets(EvtVar v, const LepSel &lep) const;
    Particle LaneMET(EvtVar v, const Event &ev) const;
    bool Select(int ch, EvtVar v, const LepSel &lep, const SelectedJetViewCollection *jets,
                std::vector<std::size_t> *bjetPos, float w0, bool central);
    void FillLane(const LaneHists &h, int ch, const FillVals &vals, float w) const;
    void MakeFillVals(int ch, EvtVar v, const Event &ev, const LepSel &lep,
                      const SelectedJetViewCollection *jets,
                      const std::vector<std::size_t> *bjetPos, FillVals &vals) const;
    void ComputeFactors(int ch, const LepSel &lep, const SelectedJetViewCollection *jets,
                        const std::vector<std::size_t> *bjetPos, bool allVariations,
                        FactorValues &fv) const;
    float ZEETriggerSF(const std::vector<std::size_t> &el, MyCorrection::variation var) const;
    void FillIDCheck(float w0);

    std::array<ChannelConf, kNChannels> channels_; //!
    std::vector<EvtVar> activeEvtVars_; //! union over channels, Central first
    std::unique_ptr<SystematicHelper> systHelper_; //!
    bool runSyst_ = false; //!
    bool runNoJetVeto_ = false; //!
    bool runIDCheck_ = false; //!
    Hist1DHandle idMu_, idEl_, idElMinCustom_, idElDEta_, idElDPhiSeed_, idElEcalIso_, idElHcalIso_, idElEcalIsoRel_, idElHcalIsoRel_; //!
    bool needJets_ = false; //!
    float lumi_ = -1.f; //!
    float topPtWeight_ = 1.f; //!
    std::array<float, 3> puWeight_{}; //!

    Hist1DHandle cutflowAll_; //!
    Hist2DHandle jetEtaPhiBefore_, jetEtaPhiAfter_; //!

    // per-event state (valid only inside executeEvent)
    MuonViewCollection muons_;         //!
    ElectronViewCollection electrons_; //!
    JetViewCollection jets_;           //!
    std::vector<std::uint8_t> muBits_, elBits_; //!
    std::array<bool, kNChannels> trig_{}; //!
    float rho_ = 0.f; //!
    // nominal MET pieces (px, py) for the current event
    double metJetNomX_ = 0, metJetNomY_ = 0, metMuNomX_ = 0, metMuNomY_ = 0,
           metElNomX_ = 0, metElNomY_ = 0; //!
};

#endif
