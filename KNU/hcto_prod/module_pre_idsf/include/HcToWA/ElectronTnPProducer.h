#ifndef HcToWA_ElectronTnPProducer_h
#define HcToWA_ElectronTnPProducer_h

// Electron tag-and-probe ntuple for the 2024 tight-ID scale factors (phase
// 2.3, docs/PLAN_LeptonID.md), following the EGM 2024 electron ID setup
// (docs/CMS/EGM/README.md) with NanoAOD electrons as probes.
//
// One entry per tag-probe pair, 50 < m(tag, probe) < 130 GeV, opposite charge,
// dR(tag, probe) > 0.1.
// - Tag: cut-based tight, NanoAOD (uncorrected) pT > 35 GeV, |eta_SC| < 2.5,
//   matched (dR < 0.1) to an e/gamma TrigObj of a fired path of the OR
//   HLT_Ele32_WPTight_Gsf      (id 11, bit 1 "hltEle*WPTight*TrackIsoFilter*", pT > 32)
//   HLT_Ele115_CaloIdVT_GsfTrkIdT (id 11, bit 12 "CaloIdVT_GsfTrkIdT", pT > 115)
//   HLT_Photon200              (id 11 bit 14 or id 22 bit 7 "hltEG200HEFilter", pT > 200)
// - Probe (denominator): NanoAOD electron, pT > 10 GeV, |eta_SC| < 2.5.
// - Numerator: probe_isHcToWATight from HcToWABase::EvaluateElectronIDs (the
//   analysis tight ID, incl. the trigger emulation on the v15 custom
//   branches); every input is stored as well. POG flags for the validation.
// - Probe e-mu trigger legs: id 11 bit 6 ("1e-1mu",
//   hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*) with pT > 23 / 12.
// - pT is the NanoAOD pT (L4); *_cor is the EGM-corrected pT.
// - MC: gen matching to prompt status-1 electrons (dR < 0.2, smallest
//   relative pT difference), genWeight, PU weight, weight as for muons.
// Output: RNTuple "electron/Events" (key electron_Events), histograms TnP/*.

#include <HcToWA/HcToWABase.h>

#include <cstdint>
#include <vector>

class ElectronTnPProducer : public HcToWABase {
public:
    ElectronTnPProducer();
    ~ElectronTnPProducer();

    void initializeAnalyzer() override;
    void executeEvent() override;

    static constexpr float kTagPt = 35.f;
    static constexpr float kProbePt = 10.f;
    static constexpr float kEta = 2.5f;
    static constexpr float kMinDR = 0.1f;
    static constexpr float kMassLow = 50.f;
    static constexpr float kMassHigh = 130.f;
    static constexpr float kTrigDR = 0.1f;
    static constexpr float kGenDR = 0.2f;

    struct Row {
        unsigned int run = 0, lumi = 0;
        ULong64_t event = 0;
        int nPV = 0, nPVsGood = 0;
        float rho = 0.f, puppiMET_pt = 0.f, puppiMET_phi = 0.f;
        float nTrueInt = 0.f, genWeight = 1.f, PUweight = 1.f, PUweight_up = 1.f,
              PUweight_down = 1.f, weight = 1.f;
        // tag
        bool tag_passEle32 = false, tag_passEle115 = false, tag_passPhoton200 = false,
             tag_trig = false, tag_isMVANoIsoWP90 = false;
        int tag_cutBased = 0, tag_q = 0;
        float tag_pt = 0, tag_pt_cor = 0, tag_eta = 0, tag_phi = 0, tag_sc_eta = 0,
              tag_miniPFRelIso = 0, tag_pfRelIso03 = 0;
        // probe
        int probe_q = 0, probe_cutBased = 0, probe_lostHits = 0;
        bool probe_convVeto = false, probe_isMVANoIsoWP90 = false, probe_isMVANoIsoWP80 = false,
             probe_isMVAIsoWP90 = false, probe_isMVAIsoWP80 = false, probe_passTrigEmu = false,
             probe_isHcToWALoose = false, probe_isHcToWATight = false;
        bool probe_Ele23EMuLeg = false, probe_Ele12EMuLeg = false, probe_Ele32 = false;
        ULong64_t probe_trigBits = 0;
        float probe_trigPt = -1.f;
        float probe_pt = 0, probe_pt_cor = 0, probe_eta = 0, probe_phi = 0, probe_sc_eta = 0,
              probe_sc_abseta = 0;
        float probe_mvaNoIso = 0, probe_mvaIso = 0, probe_miniPFRelIso = 0, probe_pfRelIso03 = 0,
              probe_sip3d = 0, probe_dz = 0, probe_dxy = 0;
        float probe_sieie = 0, probe_hoe = 0, probe_dEtaInSC = 0, probe_dPhiInSeed = 0,
              probe_ecalPFClusIso = 0, probe_hcalPFClusIso = 0, probe_dr03TkSumPt = 0;
        // pair
        unsigned int pair_probeMultiplicity = 0;
        float pair_mass = 0, pair_mass_cor = 0, pair_pt = 0, pair_dr = 0;
        // gen
        bool tag_gen_matched = false, probe_gen_matched = false, pair_gen_matched = false;
        float pair_gen_mass = -999.f;
        float tag_gen_pt = -999.f, tag_gen_eta = -999.f, tag_gen_phi = -999.f,
              tag_gen_dR = -999.f, tag_gen_reldpt = -999.f;
        float probe_gen_pt = -999.f, probe_gen_eta = -999.f, probe_gen_phi = -999.f,
              probe_gen_dR = -999.f, probe_gen_reldpt = -999.f;
    };

private:
    RNTupleHandle out_; //!
    Row r_;             //!
    float wNorm_ = 1.f; //!
    Hist1DHandle cutflow_, nTagsH_, nProbesH_, nPairsH_; //!
    std::vector<std::uint8_t> elBits_; //!
};

#endif
