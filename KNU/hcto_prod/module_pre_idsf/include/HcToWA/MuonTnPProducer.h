#ifndef HcToWA_MuonTnPProducer_h
#define HcToWA_MuonTnPProducer_h

// Muon tag-and-probe ntuple for the 2024 tight-ID scale factors (phase 2.3,
// docs/PLAN_LeptonID.md). Port of the B2G-25-013 producer (old SKNano
// Analyzers/src/MuonTnPProducer.cc) with the branch names kept, so the
// tnp_tamsa muon configs carry over.
//
// One entry per tag-probe pair, 50 < m(tag, probe) < 130 GeV, opposite charge.
// - Tag (preselection; the configs re-apply the nominal cuts): POG tight,
//   NanoAOD (uncorrected) pT > 26 GeV, |eta| < 2.4, |dxy| < 0.2, |dz| < 0.5,
//   pfRelIso04 < 0.3 (loosest tag-iso variation; nominal 0.2 in the config),
//   HLT_IsoMu24 fired and matched (dR < 0.1) to a muon TrigObj with
//   filterBit 3 ("1mu", hltL3crIsoL1*SingleMu*IsoFiltered*) and pT > 24 GeV.
// - Probe (denominator): tracker muon, NanoAOD pT > 10 GeV, |eta| < 2.4,
//   |dxy| < 0.2, |dz| < 0.5.
// - pair_probeMultiplicity: probes of this tag in the mass window.
//   probe_isDuplicated: the probe is paired with more than one tag passing the
//   nominal tag selection (iso < 0.2), as the MUO NanoAOD TnP defines it
//   (getDuplicatedProbes: a probe index appearing in more than one pair);
//   probe_nTagsIso0p{1,2,3} give the count for the three tag-iso choices.
// - Our IDs (HcToWABase::EvaluateMuonIDs): probe_isHcToWATight/Loose.
// - pT is the NanoAOD (MiniAOD) pT (L4); *_cor is the corrected pT.
// - MC: gen matching to prompt status-1 muons (dR < 0.2, smallest relative
//   pT difference, each gen muon used once), genWeight, PU weight, and
//   weight = genWeight * PUweight * sumSign / sumW (normalised to <|w|> ~ 1).
// Output: RNTuple "muon/Events" (key muon_Events), histograms TnP/*.

#include <HcToWA/HcToWABase.h>

#include <cstdint>
#include <vector>

class MuonTnPProducer : public HcToWABase {
public:
    MuonTnPProducer();
    ~MuonTnPProducer();

    void initializeAnalyzer() override;
    void executeEvent() override;

    static constexpr float kTagPt = 26.f;
    static constexpr float kTagIsoMax = 0.3f;
    static constexpr float kTagIsoNominal = 0.2f;
    static constexpr float kProbePt = 10.f;
    static constexpr float kEta = 2.4f;
    static constexpr float kDxy = 0.2f;
    static constexpr float kDz = 0.5f;
    static constexpr float kMassLow = 50.f;
    static constexpr float kMassHigh = 130.f;
    static constexpr float kTrigDR = 0.1f;
    static constexpr float kGenDR = 0.2f;

    struct Row {
        // event
        unsigned int run = 0, lumi = 0;
        ULong64_t event = 0;
        int nPV = 0, nPVsGood = 0;
        float rho = 0.f, puppiMET_pt = 0.f, puppiMET_phi = 0.f;
        // MC weights
        float nTrueInt = 0.f, genWeight = 1.f, PUweight = 1.f, PUweight_up = 1.f,
              PUweight_down = 1.f, weight = 1.f;
        // tag
        bool tag_IsoMu24 = false, tag_isTight = false, tag_isMedium = false,
             tag_isLoose = false;
        float tag_pt = 0, tag_pt_cor = 0, tag_eta = 0, tag_phi = 0;
        int tag_q = 0;
        float tag_pfRelIso03 = 0, tag_pfRelIso04 = 0, tag_tkRelIso = 0,
              tag_miniPFRelIso = 0, tag_sip3d = 0, tag_dz = 0, tag_dxy = 0;
        // probe
        bool probe_isTracker = false, probe_isGlobal = false, probe_isSA = false,
             probe_isPF = false, probe_isTight = false, probe_isMedium = false,
             probe_isLoose = false, probe_TkIsoLoose = false, probe_PFIsoTight = false,
             probe_isHcToWALoose = false, probe_isHcToWATight = false;
        bool probe_IsoMu24 = false, probe_Mu17Leg1 = false, probe_Mu8Leg2 = false,
             probe_Mu23EMuLeg = false, probe_Mu8EMuLeg = false;
        ULong64_t probe_trigBits = 0;
        float probe_trigPt = -1.f;
        bool probe_isDuplicated = false;
        int probe_nTagsIso0p1 = 0, probe_nTagsIso0p2 = 0, probe_nTagsIso0p3 = 0;
        float probe_pt = 0, probe_pt_cor = 0, probe_eta = 0, probe_phi = 0;
        int probe_q = 0;
        float probe_pfRelIso03 = 0, probe_pfRelIso04 = 0, probe_tkRelIso = 0,
              probe_miniPFRelIso = 0, probe_sip3d = 0, probe_dz = 0, probe_dxy = 0;
        // pair
        unsigned int pair_probeMultiplicity = 0;
        float pair_mass = 0, pair_mass_cor = 0, pair_pt = 0, pair_dr = 0;
        bool pair_EMTF = false;
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
    std::vector<std::uint8_t> muBits_; //!
};

#endif
