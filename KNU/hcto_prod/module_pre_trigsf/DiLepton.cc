#include <HcToWA/DiLepton.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

namespace {

using V = MyCorrection::variation;
using EvtVar = DiLepton::EvtVar;

const char *kChannelName[DiLepton::kNChannels] = {"DIMU", "EMU", "ZEE"};

// Proxy EGM SFs for the Z->ee check only (RunZEE). Closest EGM working points
// to our tight electron ID (MVA noIso WP90 + mini-iso + trigger emulation):
// ID "wp90noiso"; the 2024 HLT SFs exist only for ID-iso probes, closest is
// MVA iso WP90.
const char *kZEEIDKey = "wp90noiso";
const char *kZEETrigKey = "HLT_SF_Ele30_MVAiso90ID";
constexpr float kZEETrigMapMinPt = 25.f; // lower edge of the electronHlt maps

bool IsJetVar(EvtVar v) {
    return v == EvtVar::JetResUp || v == EvtVar::JetResDown ||
           v == EvtVar::JetEnUp || v == EvtVar::JetEnDown;
}
bool IsMuonVar(EvtVar v) {
    return v == EvtVar::MuonEnUp || v == EvtVar::MuonEnDown ||
           v == EvtVar::MuonResUp || v == EvtVar::MuonResDown;
}
bool IsElectronVar(EvtVar v) {
    return v == EvtVar::ElectronEnUp || v == EvtVar::ElectronEnDown ||
           v == EvtVar::ElectronResUp || v == EvtVar::ElectronResDown;
}
V JesVar(EvtVar v) {
    return v == EvtVar::JetEnUp ? V::up : (v == EvtVar::JetEnDown ? V::down : V::nom);
}
V JerVar(EvtVar v) {
    return v == EvtVar::JetResUp ? V::up : (v == EvtVar::JetResDown ? V::down : V::nom);
}
bool LaneApplies(int ch, EvtVar v) {
    if (v == EvtVar::Central) return true;
    if (ch == DiLepton::kZEE) return IsElectronVar(v);
    return true;
}

EvtVar EvtVarFromName(const std::string &syst, V var) {
    const bool up = var == V::up;
    if (syst == "JetRes") return up ? EvtVar::JetResUp : EvtVar::JetResDown;
    if (syst == "JetEn") return up ? EvtVar::JetEnUp : EvtVar::JetEnDown;
    if (syst == "ElectronRes") return up ? EvtVar::ElectronResUp : EvtVar::ElectronResDown;
    if (syst == "ElectronEn") return up ? EvtVar::ElectronEnUp : EvtVar::ElectronEnDown;
    if (syst == "MuonEn") return up ? EvtVar::MuonEnUp : EvtVar::MuonEnDown;
    if (syst == "MuonRes") return up ? EvtVar::MuonResUp : EvtVar::MuonResDown;
    if (syst == "UnclusteredEn") return up ? EvtVar::UnclusteredEnUp : EvtVar::UnclusteredEnDown;
    throw SKNano::ConfigError("[DiLepton] unknown event-loop systematic '" + syst + "'");
}

TLorentzVector P4(float pt, float eta, float phi, float m) {
    TLorentzVector v;
    v.SetPtEtaPhiM(pt, eta, phi, m);
    return v;
}

} // namespace

DiLepton::DiLepton() {}
DiLepton::~DiLepton() {}

// ---------------------------------------------------------------------------
void DiLepton::initializeAnalyzer() {
    HcToWABase::initializeAnalyzer();

    channels_[kDIMU].enabled = HasFlag("RunDiMu");
    channels_[kEMU].enabled = HasFlag("RunEMu");
    channels_[kZEE].enabled = HasFlag("RunZEE");
    for (int ch = 0; ch < kNChannels; ++ch) channels_[ch].name = kChannelName[ch];
    if (!channels_[kDIMU].enabled && !channels_[kEMU].enabled && !channels_[kZEE].enabled)
        throw SKNano::ConfigError("[DiLepton] no channel flag (RunDiMu, RunEMu, RunZEE)");
    runSyst_ = HasFlag("RunSyst") && !IsDATA;
    runNoJetVeto_ = HasFlag("RunNoJetVeto");
    runIDCheck_ = HasFlag("RunIDCheck");
    needJets_ = channels_[kDIMU].enabled || channels_[kEMU].enabled;

    if (channels_[kEMU].enabled && !IsDATA) {
        LoadBTagCorrections();
        if (!BTagWeightAvailable())
            cout << "\033[1;31m[DiLepton] b-tag weight = 1 (no efficiency map); "
                    "BtagSF lanes omitted\033[0m" << endl;
    }

    // Central lane for every enabled channel.
    for (int ch = 0; ch < kNChannels; ++ch) {
        if (!channels_[ch].enabled) continue;
        EvtLane central;
        central.var = EvtVar::Central;
        central.name = "Central";
        channels_[ch].evtLanes.push_back(std::move(central));
    }

    if (runSyst_) {
        const char *home = std::getenv("SKNANO_HOME");
        if (!home) throw SKNano::ConfigError("[DiLepton] SKNANO_HOME not set");
        // Batch jobs run from the run's source snapshot, which keeps modules
        // under analysis_modules/; an interactive checkout has them at the top.
        std::string yaml;
        for (const char *sub : {"/analysis_modules/HcToWA_Analyzers", "/HcToWA_Analyzers"}) {
            const std::string candidate =
                std::string(home) + sub + "/data/DiLeptonSystematics.yaml";
            if (FILE *fp = std::fopen(candidate.c_str(), "r")) {
                std::fclose(fp);
                yaml = candidate;
                break;
            }
        }
        if (yaml.empty())
            throw SKNano::ConfigError("[DiLepton] DiLeptonSystematics.yaml not found under " +
                                      std::string(home));
        cout << "[DiLepton] systematics: " << yaml << endl;
        systHelper_ = std::make_unique<SystematicHelper>(yaml, MCSample, DataEra);

        for (const auto &it : *systHelper_) {
            if (it.iter_name == "Central") continue;
            const EvtVar v = EvtVarFromName(it.syst_name, it.variation);
            for (int ch = 0; ch < kNChannels; ++ch) {
                if (!channels_[ch].enabled || !LaneApplies(ch, v)) continue;
                EvtLane lane;
                lane.var = v;
                lane.name = it.iter_name;
                channels_[ch].evtLanes.push_back(std::move(lane));
            }
        }

        for (const auto &name : systHelper_->getWeightOnlySystematics()) {
            int factor = -1;
            int up = 1, down = 2;
            bool topPt = false;
            std::vector<int> chs;
            if (name == "PileupReweight") {
                factor = kFPU; chs = {kDIMU, kEMU, kZEE};
            } else if (name == "ElectronRecoSF") {
                factor = kFEleReco; chs = {kEMU, kZEE}; // DiMu has no electron
            } else if (name.rfind("BtagSF_", 0) == 0) {
                factor = kFBTag; chs = {kEMU};
                if (!BTagWeightAvailable()) chs.clear();
                if (name == "BtagSF_HFcorr") { up = kBTagHFcorrUp; down = kBTagHFcorrDown; }
                else if (name == "BtagSF_HFuncorr") { up = kBTagHFuncorrUp; down = kBTagHFuncorrDown; }
                else if (name == "BtagSF_LFcorr") { up = kBTagLFcorrUp; down = kBTagLFcorrDown; }
                else if (name == "BtagSF_LFuncorr") { up = kBTagLFuncorrUp; down = kBTagLFuncorrDown; }
                else throw SKNano::ConfigError("[DiLepton] unknown b-tag systematic " + name);
            } else if (name == "MuonIDSF") {
                factor = kFMuID; chs = {kDIMU, kEMU};
            } else if (name == "ElectronIDSF") {
                factor = kFEleID; chs = {kEMU, kZEE};
            } else if (name == "ElectronIDSFProxy") {
                factor = kFEleIDProxy; chs = {kZEE};
            } else if (name == "ElectronTrigSFProxy") {
                factor = kFEleTrigProxy; chs = {kZEE};
            } else if (name == "TopPtReweight") {
                topPt = true; chs = {kDIMU, kEMU, kZEE};
                if (!isTTPowheg) chs.clear();
            } else {
                throw SKNano::ConfigError("[DiLepton] unknown weight systematic '" + name + "'");
            }
            for (int ch : chs) {
                auto &conf = channels_[ch];
                if (!conf.enabled) continue;
                if (topPt) {
                    WeightLane wl;
                    wl.name = "TopPtReweight_Applied";
                    wl.topPt = true;
                    conf.weightLanes.push_back(std::move(wl));
                    continue;
                }
                WeightLane wu, wd;
                wu.name = name + "_Up"; wu.factor = factor; wu.valueIndex = up;
                wd.name = name + "_Down"; wd.factor = factor; wd.valueIndex = down;
                conf.weightLanes.push_back(std::move(wu));
                conf.weightLanes.push_back(std::move(wd));
            }
        }
        // One "_NotImplemented" lane per factor present (the four b-tag
        // sources share one factor, so a single BtagSF_NotImplemented).
        const char *notImplName[kNFactors] = {"PileupReweight", "ElectronRecoSF", "BtagSF",
                                               "ElectronIDSFProxy", "ElectronTrigSFProxy",
                                               "MuonIDSF", "ElectronIDSF"};
        for (int ch = 0; ch < kNChannels; ++ch) {
            auto &conf = channels_[ch];
            if (!conf.enabled) continue;
            std::array<bool, kNFactors> present{};
            for (const auto &wl : conf.weightLanes)
                if (wl.factor >= 0) present[wl.factor] = true;
            for (int f = 0; f < kNFactors; ++f) {
                if (!present[f]) continue;
                WeightLane wl;
                wl.name = std::string(notImplName[f]) + "_NotImplemented";
                wl.factor = f;
                wl.notImplemented = true;
                conf.weightLanes.push_back(std::move(wl));
            }
        }
    }

    // Union of event-loop variations, Central first.
    activeEvtVars_.clear();
    activeEvtVars_.push_back(EvtVar::Central);
    for (int k = 1; k < static_cast<int>(EvtVar::N); ++k) {
        const EvtVar v = static_cast<EvtVar>(k);
        for (int ch = 0; ch < kNChannels; ++ch) {
            bool found = false;
            for (const auto &l : channels_[ch].evtLanes) if (l.var == v) found = true;
            if (found) { activeEvtVars_.push_back(v); break; }
        }
    }

    // Book everything once.
    cutflowAll_ = Hists("ALL/Central").Book1D("cutflow", 9, 0., 9.);
    jetEtaPhiBefore_ = Hists("JetEtaPhi/BeforeEventVeto_Run3").Book2D("eta_phi", 100, -5., 5., 64, -3.2, 3.2);
    jetEtaPhiAfter_ = Hists("JetEtaPhi/PassedEventVeto_Run3").Book2D("eta_phi", 100, -5., 5., 64, -3.2, 3.2);
    for (int ch = 0; ch < kNChannels; ++ch)
        if (channels_[ch].enabled) BookChannel(ch);
    if (runIDCheck_) {
        // Validation only: object-level ID pass counts (MiniAOD pT > 10 GeV).
        const auto g = Hists("IDCheck");
        idMu_ = g.Book1D("muon/pass", 3, 0., 3.);       // all, loose, tight
        idEl_ = g.Book1D("electron/pass", 4, 0., 4.);   // all, trig. emulation, loose, tight
        idElMinCustom_ = g.Book1D("electron/minCustom", 200, -1000., 1000.);
        idElDEta_ = g.Book1D("electron/DeltaEtaInSC", 200, -0.1, 0.1);
        idElDPhiSeed_ = g.Book1D("electron/DeltaPhiInSeed", 200, -0.5, 0.5);
        idElEcalIso_ = g.Book1D("electron/ecalPFClusIso", 200, 0., 50.);
        idElHcalIso_ = g.Book1D("electron/hcalPFClusIso", 200, 0., 50.);
        idElEcalIsoRel_ = g.Book1D("electron/ecalPFClusIsoOverPt", 200, 0., 2.);
        idElHcalIsoRel_ = g.Book1D("electron/hcalPFClusIsoOverPt", 200, 0., 2.);
    }

    for (int ch = 0; ch < kNChannels; ++ch) {
        if (!channels_[ch].enabled) continue;
        cout << "[DiLepton] " << channels_[ch].name << " lanes:";
        for (const auto &l : channels_[ch].evtLanes) cout << " " << l.name;
        for (const auto &l : channels_[ch].weightLanes) cout << " " << l.name;
        cout << endl;
    }
}

void DiLepton::BookChannel(int ch) {
    auto &conf = channels_[ch];
    const std::string c = conf.name;
    conf.cutflow = Hists(c + "/Central").Book1D("cutflow", 9, 0., 9.);
    if (!IsDATA) {
        const auto g = Hists(c + "/Central/weights");
        auto &w = conf.weights;
        w.genWeight = g.Book1D("genWeight", 200, -10000., 10000.);
        w.log10AbsGenWeight = g.Book1D("log10AbsGenWeight", 140, -4., 10.);
        w.mcWeight = g.Book1D("log10AbsMCWeightTimesLumi", 140, -10., 4.);
        w.pileupWeight = g.Book1D("pileupWeight", 100, -5., 5.);
        w.topPtWeight = g.Book1D("topPtWeight", 100, -5., 5.);
        w.total = g.Book1D("totalSF", 100, 0., 5.);
        if (ch != kDIMU) w.eleRecoSF = g.Book1D("eleRecoSF", 100, -5., 5.);
        if (ch == kEMU) w.btagSF = g.Book1D("btagSF", 600, -3., 3.);
        if (ch != kZEE) w.muIDSF = g.Book1D("muIDSF", 100, -5., 5.);
        if (ch != kDIMU) w.eleIDSF = g.Book1D("eleIDSF", 100, -5., 5.);
        if (ch == kZEE) w.eleTrigSFProxy = g.Book1D("eleTrigSFProxy", 100, -5., 5.);
    }
    for (auto &l : conf.evtLanes) BookLane(l.hists, ch, l.name);
    for (auto &l : conf.weightLanes) BookLane(l.hists, ch, l.name);
}

void DiLepton::BookLane(LaneHists &h, int ch, const std::string &lane) {
    const auto g = Hists(channels_[ch].name + "/" + lane);
    const int nMu = ch == kDIMU ? 2 : (ch == kEMU ? 1 : 0);
    const int nEl = ch == kZEE ? 2 : (ch == kEMU ? 1 : 0);
    for (int i = 0; i < nMu; ++i) {
        const auto m = g.Group("muons/" + std::to_string(i + 1));
        auto &x = h.mu[i];
        x.pt = m.Book1D("pt", 300, 0., 300.);
        x.miniAODPt = m.Book1D("miniAODPt", 300, 0., 300.);
        x.eta = m.Book1D("eta", 48, -2.4, 2.4);
        x.phi = m.Book1D("phi", 64, -3.2, 3.2);
        x.mass = m.Book1D("mass", 10, 0., 1.);
        x.miniRelIso = m.Book1D("miniRelIso", 100, 0., 1.);
        x.sip3d = m.Book1D("sip3d", 100, 0., 10.);
        x.dz = m.Book1D("dz", 100, -0.5, 0.5);
    }
    for (int i = 0; i < nEl; ++i) {
        const auto e = g.Group("electrons/" + std::to_string(i + 1));
        auto &x = h.el[i];
        x.pt = e.Book1D("pt", 300, 0., 300.);
        x.miniAODPt = e.Book1D("miniAODPt", 300, 0., 300.);
        x.eta = e.Book1D("eta", 50, -2.5, 2.5);
        x.scEta = e.Book1D("scEta", 50, -2.5, 2.5);
        x.phi = e.Book1D("phi", 64, -3.2, 3.2);
        x.mass = e.Book1D("mass", 100, 0., 1.);
        x.miniRelIso = e.Book1D("miniRelIso", 100, 0., 1.);
        x.sip3d = e.Book1D("sip3d", 100, 0., 10.);
        x.dz = e.Book1D("dz", 100, -0.5, 0.5);
    }
    if (ch != kZEE) {
        for (int i = 0; i < 5; ++i) {
            const auto j = g.Group("jets/" + std::to_string(i + 1));
            auto &x = h.jet[i];
            x.pt = j.Book1D("pt", 300, 0., 300.);
            x.rawPt = j.Book1D("rawPt", 300, 0., 300.);
            x.originalPt = j.Book1D("originalPt", 300, 0., 300.);
            x.eta = j.Book1D("eta", 50, -2.5, 2.5); // |eta| < 2.5 in 2024 (old: 48 bins, 2.4)
            x.phi = j.Book1D("phi", 64, -3.2, 3.2);
            x.mass = j.Book1D("mass", 100, 0., 100.);
        }
        for (int i = 0; i < 3; ++i) {
            const auto j = g.Group("bjets/" + std::to_string(i + 1));
            auto &x = h.bjet[i];
            x.pt = j.Book1D("pt", 300, 0., 300.);
            x.eta = j.Book1D("eta", 50, -2.5, 2.5);
            x.phi = j.Book1D("phi", 64, -3.2, 3.2);
            x.mass = j.Book1D("mass", 100, 0., 100.);
        }
        h.jetsSize = g.Book1D("jets/size", 20, 0., 20.);
        h.bjetsSize = g.Book1D("bjets/size", 15, 0., 15.);
        h.metPt = g.Book1D("METv/pt", 300, 0., 300.);
        h.metPhi = g.Book1D("METv/phi", 64, -3.2, 3.2);
        h.metDefPt = g.Book1D("METv_default/pt", 300, 0., 300.);
        h.metDefPhi = g.Book1D("METv_default/phi", 64, -3.2, 3.2);
    }
    if (ch == kDIMU || ch == kZEE) {
        h.pairPt = g.Book1D("pair/pt", 300, 0., 300.);
        h.pairEta = g.Book1D("pair/eta", 100, -5., 5.);
        h.pairPhi = g.Book1D("pair/phi", 64, -3.2, 3.2);
        h.pairMass = g.Book1D("pair/mass", 300, 0., 300.);
        h.pairMassUncorr = g.Book1D("pair/massMiniAOD", 300, 0., 300.);
    }
    h.nPV = g.Book1D("nPV", 200, 0., 200.);
    h.nPVsGood = g.Book1D("nPVsGood", 200, 0., 200.);
    h.nTrueInt = g.Book1D("nTrueInt", 200, 0., 200.);
    h.nPileUp = g.Book1D("nPileUp", 200, 0., 200.);
    h.rho = g.Book1D("rho", 200, -100., 100.);
}

// ---------------------------------------------------------------------------
float DiLepton::MuPt(const MuonView &m, EvtVar v) const {
    switch (v) {
    case EvtVar::MuonEnUp: return m.MomentumScaleUp();
    case EvtVar::MuonEnDown: return m.MomentumScaleDown();
    case EvtVar::MuonResUp: return m.MomentumResUp();
    case EvtVar::MuonResDown: return m.MomentumResDown();
    default: return m.Pt();
    }
}

float DiLepton::ElPt(const ElectronView &e, EvtVar v) const {
    switch (v) {
    case EvtVar::ElectronEnUp: return e.ScaleUpPt();
    case EvtVar::ElectronEnDown: return e.ScaleDownPt();
    case EvtVar::ElectronResUp: return e.SmearUpPt();
    case EvtVar::ElectronResDown: return e.SmearDownPt();
    default: return e.Pt();
    }
}

void DiLepton::BuildLeptons(EvtVar v, LepSel &out) const {
    out.muLoose.clear(); out.muTight.clear(); out.elLoose.clear(); out.elTight.clear();
    const EvtVar mv = IsMuonVar(v) ? v : EvtVar::Central;
    const EvtVar ev = IsElectronVar(v) ? v : EvtVar::Central;
    std::vector<std::pair<float, std::size_t>> tmp;
    for (std::size_t i = 0; i < muBits_.size(); ++i) {
        if (!(muBits_[i] & kLoose)) continue;
        const auto m = muons_[i];
        if (!(std::fabs(m.Eta()) < 2.4f)) continue;
        const float pt = MuPt(m, mv);
        if (!(pt > 10.f)) continue;
        tmp.emplace_back(pt, i);
    }
    std::sort(tmp.begin(), tmp.end(), [](const auto &a, const auto &b) { return a.first > b.first; });
    for (const auto &p : tmp) {
        out.muLoose.push_back(p.second);
        if (muBits_[p.second] & kTight) out.muTight.push_back(p.second);
    }
    tmp.clear();
    for (std::size_t i = 0; i < elBits_.size(); ++i) {
        if (!(elBits_[i] & kLoose)) continue;
        const auto e = electrons_[i];
        if (!(std::fabs(e.Eta()) < 2.5f)) continue;
        const float pt = ElPt(e, ev);
        if (!(pt > 10.f)) continue;
        tmp.emplace_back(pt, i);
    }
    std::sort(tmp.begin(), tmp.end(), [](const auto &a, const auto &b) { return a.first > b.first; });
    for (const auto &p : tmp) {
        out.elLoose.push_back(p.second);
        if ((elBits_[p.second] & kTight) && p.first > 15.f) out.elTight.push_back(p.second);
    }
}

SelectedJetViewCollection DiLepton::BuildJets(EvtVar v, const LepSel &lep) const {
    const V jes = JesVar(v), jer = JerVar(v);
    auto idx = SelectJetIndices(jets_, JetView::JetID::TIGHT, 20.f, 2.5f, jes, jer);
    idx = RemoveOverlapIndices(jets_, idx, electrons_, lep.elLoose, 0.4f);
    idx = RemoveOverlapIndices(jets_, idx, muons_, lep.muLoose, 0.4f);
    return SelectJetViews(jets_, std::move(idx), jes, jer);
}

Particle DiLepton::LaneMET(EvtVar v, const Event &ev) const {
    Particle raw;
    if (v == EvtVar::UnclusteredEnUp)
        raw = ev.GetMETVector(Event::MET_Type::PUPPI, SKNano::Variation::up, Event::MET_Syst::UE);
    else if (v == EvtVar::UnclusteredEnDown)
        raw = ev.GetMETVector(Event::MET_Type::PUPPI, SKNano::Variation::down, Event::MET_Syst::UE);
    else
        raw = ev.GetMETVector(Event::MET_Type::PUPPI);
    double jx = metJetNomX_, jy = metJetNomY_, mx = metMuNomX_, my = metMuNomY_,
           ex = metElNomX_, ey = metElNomY_;
    if (IsJetVar(v)) {
        Particle z;
        PropagateJetSystToMET(jets_, z, JesVar(v), JerVar(v));
        jx = z.Px(); jy = z.Py();
    } else if (IsMuonVar(v)) {
        Particle z;
        const V s = v == EvtVar::MuonEnUp ? V::up : (v == EvtVar::MuonEnDown ? V::down : V::nom);
        const V r = v == EvtVar::MuonResUp ? V::up : (v == EvtVar::MuonResDown ? V::down : V::nom);
        PropagateMuonCorrToMET(muons_, z, s, r);
        mx = z.Px(); my = z.Py();
    } else if (IsElectronVar(v)) {
        Particle z;
        const V s = v == EvtVar::ElectronEnUp ? V::up : (v == EvtVar::ElectronEnDown ? V::down : V::nom);
        const V r = v == EvtVar::ElectronResUp ? V::up : (v == EvtVar::ElectronResDown ? V::down : V::nom);
        PropagateElectronCorrToMET(electrons_, z, s, r);
        ex = z.Px(); ey = z.Py();
    }
    Particle met;
    met.SetXYZM(raw.Px() + jx + mx + ex, raw.Py() + jy + my + ey, 0., 0.);
    return met;
}

// ---------------------------------------------------------------------------
// Stage 1 of every channel: leptons, trigger, kinematics (no jets needed).
bool DiLepton::Select(int ch, EvtVar v, const LepSel &lep,
                      const SelectedJetViewCollection *jets,
                      std::vector<std::size_t> *bjetPos, float w0, bool central) {
    auto cut = [&](int bin) { if (central) channels_[ch].cutflow.Fill(bin, w0); };
    const EvtVar mv = IsMuonVar(v) ? v : EvtVar::Central;
    const EvtVar ev = IsElectronVar(v) ? v : EvtVar::Central;
    if (jets == nullptr) {
        if (ch == kDIMU) {
            if (!(lep.muTight.size() == 2 && lep.muLoose.size() == 2 && lep.elLoose.empty())) return false;
            cut(3);
            if (!trig_[kDIMU]) return false;
            cut(4);
            const auto m1 = muons_[lep.muTight[0]];
            const auto m2 = muons_[lep.muTight[1]];
            const float pt1 = MuPt(m1, mv), pt2 = MuPt(m2, mv);
            if (!(pt1 > 20.f && pt2 > 10.f)) return false;
            if (m1.Charge() + m2.Charge() != 0) return false;
            const float mass = (P4(pt1, m1.Eta(), m1.Phi(), m1.M()) + P4(pt2, m2.Eta(), m2.Phi(), m2.M())).M();
            if (!(mass > 50.f)) return false;
            cut(5);
            return true;
        }
        if (ch == kEMU) {
            if (!(lep.muTight.size() == 1 && lep.muLoose.size() == 1 &&
                  lep.elTight.size() == 1 && lep.elLoose.size() == 1)) return false;
            cut(3);
            if (!trig_[kEMU]) return false;
            cut(4);
            const auto m = muons_[lep.muTight[0]];
            const auto e = electrons_[lep.elTight[0]];
            const float ptm = MuPt(m, mv), pte = ElPt(e, ev);
            if (!((ptm > 25.f && pte > 15.f) || (ptm > 10.f && pte > 25.f))) return false;
            if (m.Charge() + e.Charge() != 0) return false;
            if (!(P4(ptm, m.Eta(), m.Phi(), m.M()).DeltaR(P4(pte, e.Eta(), e.Phi(), e.M())) > 0.4)) return false;
            cut(5);
            return true;
        }
        // ZEE
        if (!(lep.elTight.size() == 2 && lep.elLoose.size() == 2 && lep.muLoose.empty())) return false;
        cut(3);
        if (!trig_[kZEE]) return false;
        cut(4);
        const auto e1 = electrons_[lep.elTight[0]];
        const auto e2 = electrons_[lep.elTight[1]];
        const float pt1 = ElPt(e1, ev), pt2 = ElPt(e2, ev);
        if (!(pt1 > 35.f && pt2 > 15.f)) return false;
        if (e1.Charge() + e2.Charge() != 0) return false;
        const float mass = (P4(pt1, e1.Eta(), e1.Phi(), e1.M()) + P4(pt2, e2.Eta(), e2.Phi(), e2.M())).M();
        if (!(std::fabs(mass - 91.1876f) < 30.f)) return false;
        cut(5);
        return true;
    }
    // Stage 2: jets (only EMu cuts on them).
    bjetPos->clear();
    for (std::size_t k = 0; k < jets->size(); ++k)
        if ((*jets)[k].GetTaggerResult(JetTagging::JetFlavTagger::ParT,
                                       JetTagging::JetFlavTaggerScoreType::B) > bTagWP)
            bjetPos->push_back(k);
    if (ch == kEMU) {
        if (!(jets->size() >= 2)) return false;
        cut(6);
        if (!(bjetPos->size() >= 1)) return false;
        cut(7);
    }
    return true;
}

// ---------------------------------------------------------------------------
float DiLepton::ZEETriggerSF(const std::vector<std::size_t> &el, V var) const {
    // Event SF for one single-electron trigger and two electrons:
    // [1 - prod(1 - effData)] / [1 - prod(1 - effMC)], electrons below the map
    // lower edge do not contribute. Variation: data efficiency up/down.
    double pData = 1., pMC = 1.;
    for (const auto i : el) {
        const auto e = electrons_[i];
        if (e.MiniAODPt() < kZEETrigMapMinPt) continue;
        const float effD = std::clamp(myCorr->GetElectronTriggerDataEff(kZEETrigKey, e, var), 0.f, 1.f);
        const float effM = std::clamp(myCorr->GetElectronTriggerMCEff(kZEETrigKey, e, V::nom), 0.f, 1.f);
        pData *= 1. - effD;
        pMC *= 1. - effM;
    }
    const double den = 1. - pMC;
    return den > 0. ? static_cast<float>((1. - pData) / den) : 1.f;
}

void DiLepton::ComputeFactors(int ch, const LepSel &lep, const SelectedJetViewCollection *jets,
                              const std::vector<std::size_t> *bjetPos, bool allVariations,
                              FactorValues &fv) const {
    for (auto &a : fv.vars) a.fill(1.f);
    if (IsDATA) return;
    fv.vars[kFPU][0] = puWeight_[0];
    fv.vars[kFPU][1] = puWeight_[1];
    fv.vars[kFPU][2] = puWeight_[2];
    if (ch == kEMU || ch == kZEE) {
        float n = 1.f, u = 1.f, d = 1.f;
        for (const auto i : lep.elTight) {
            const auto e = electrons_[i];
            n *= myCorr->GetElectronRECOSF(e, V::nom);
            if (allVariations) {
                u *= myCorr->GetElectronRECOSF(e, V::up);
                d *= myCorr->GetElectronRECOSF(e, V::down);
            }
        }
        fv.vars[kFEleReco][0] = n;
        fv.vars[kFEleReco][1] = allVariations ? u : n;
        fv.vars[kFEleReco][2] = allVariations ? d : n;
    }
    if (ch == kEMU && jets) {
        std::vector<BTagJet> bj;
        bj.reserve(jets->size());
        std::size_t next = 0;
        for (std::size_t k = 0; k < jets->size(); ++k) {
            const auto j = (*jets)[k];
            const bool tagged = next < bjetPos->size() && (*bjetPos)[next] == k;
            if (tagged) ++next;
            bj.push_back({j.Pt(), j.Eta(), static_cast<int>(j.HadronFlavour()), tagged});
        }
        BTagWeights(bj, allVariations, fv.vars[kFBTag]);
    }
    // Our lepton ID SFs (tight leptons; corrected pT): muons in DiMu and EMu,
    // electrons in EMu and Z->ee. In Z->ee they replace the EGM proxy ID SF
    // (2026-11-25), whose factor stays 1; the trigger SF there is still the proxy.
    if (ch == kDIMU || ch == kEMU) {
        float n = 1.f, u = 1.f, d = 1.f;
        for (const auto i : lep.muTight) {
            const auto m = muons_[i];
            n *= MuonIDSF(m.Eta(), m.Pt(), 0);
            if (allVariations) {
                u *= MuonIDSF(m.Eta(), m.Pt(), 1);
                d *= MuonIDSF(m.Eta(), m.Pt(), 2);
            }
        }
        fv.vars[kFMuID][0] = n;
        fv.vars[kFMuID][1] = allVariations ? u : n;
        fv.vars[kFMuID][2] = allVariations ? d : n;
    }
    if (ch == kEMU || ch == kZEE) {
        float n = 1.f, u = 1.f, d = 1.f;
        for (const auto i : lep.elTight) {
            const auto e = electrons_[i];
            n *= ElectronIDSF(e.ScEta(), e.Pt(), 0);
            if (allVariations) {
                u *= ElectronIDSF(e.ScEta(), e.Pt(), 1);
                d *= ElectronIDSF(e.ScEta(), e.Pt(), 2);
            }
        }
        fv.vars[kFEleID][0] = n;
        fv.vars[kFEleID][1] = allVariations ? u : n;
        fv.vars[kFEleID][2] = allVariations ? d : n;
    }
    if (ch == kZEE) {
        const float tn = ZEETriggerSF(lep.elTight, V::nom);
        fv.vars[kFEleTrigProxy][0] = tn;
        fv.vars[kFEleTrigProxy][1] = allVariations ? ZEETriggerSF(lep.elTight, V::up) : tn;
        fv.vars[kFEleTrigProxy][2] = allVariations ? ZEETriggerSF(lep.elTight, V::down) : tn;
    }
}

// ---------------------------------------------------------------------------
void DiLepton::MakeFillVals(int ch, EvtVar v, const Event &ev, const LepSel &lep,
                            const SelectedJetViewCollection *jets,
                            const std::vector<std::size_t> *bjetPos, FillVals &x) const {
    const EvtVar mv = IsMuonVar(v) ? v : EvtVar::Central;
    const EvtVar evv = IsElectronVar(v) ? v : EvtVar::Central;
    x = FillVals{};
    x.nMu = ch == kDIMU ? 2 : (ch == kEMU ? 1 : 0);
    x.nEl = ch == kZEE ? 2 : (ch == kEMU ? 1 : 0);
    for (int i = 0; i < x.nMu; ++i) {
        const auto m = muons_[lep.muTight[i]];
        x.mu[i] = {MuPt(m, mv), m.MiniAODPt(), m.Eta(), 0.f, m.Phi(), m.M(),
                   m.MiniPFRelIso(), m.SIP3D(), m.dZ()};
    }
    for (int i = 0; i < x.nEl; ++i) {
        const auto e = electrons_[lep.elTight[i]];
        x.el[i] = {ElPt(e, evv), e.MiniAODPt(), e.Eta(), e.ScEta(), e.Phi(), e.M(),
                   e.MiniPFRelIso(), e.SIP3D(), e.dZ()};
    }
    if (jets) {
        x.jetsSize = jets->size();
        x.bjetsSize = bjetPos->size();
        x.nJet = std::min<int>(5, jets->size());
        for (int i = 0; i < x.nJet; ++i) {
            const auto j = (*jets)[i];
            const JetView &raw = j;
            x.jet[i] = {j.Pt(), raw.Pt() * (1.f - raw.RawFactor()), raw.Pt(), j.Eta(), j.Phi(), j.M()};
        }
        x.nBJet = std::min<int>(3, bjetPos->size());
        for (int i = 0; i < x.nBJet; ++i) {
            const auto j = (*jets)[(*bjetPos)[i]];
            x.bjet[i] = {j.Pt(), 0.f, 0.f, j.Eta(), j.Phi(), j.M()};
        }
        const Particle met = LaneMET(v, ev);
        x.metPt = met.Pt(); x.metPhi = met.Phi();
        Particle def;
        if (v == EvtVar::UnclusteredEnUp)
            def = ev.GetMETVector(Event::MET_Type::PUPPI, SKNano::Variation::up, Event::MET_Syst::UE);
        else if (v == EvtVar::UnclusteredEnDown)
            def = ev.GetMETVector(Event::MET_Type::PUPPI, SKNano::Variation::down, Event::MET_Syst::UE);
        else
            def = ev.GetMETVector(Event::MET_Type::PUPPI);
        x.metDefPt = def.Pt(); x.metDefPhi = def.Phi();
    }
    if (ch == kDIMU) {
        const auto &a = x.mu[0], &b = x.mu[1];
        const TLorentzVector p = P4(a.pt, a.eta, a.phi, a.mass) + P4(b.pt, b.eta, b.phi, b.mass);
        const TLorentzVector q = P4(a.miniAODPt, a.eta, a.phi, a.mass) + P4(b.miniAODPt, b.eta, b.phi, b.mass);
        x.hasPair = true;
        x.pairPt = p.Pt(); x.pairEta = p.Eta(); x.pairPhi = p.Phi(); x.pairMass = p.M();
        x.pairMassUncorr = q.M();
    } else if (ch == kZEE) {
        const auto &a = x.el[0], &b = x.el[1];
        const TLorentzVector p = P4(a.pt, a.eta, a.phi, a.mass) + P4(b.pt, b.eta, b.phi, b.mass);
        const TLorentzVector q = P4(a.miniAODPt, a.eta, a.phi, a.mass) + P4(b.miniAODPt, b.eta, b.phi, b.mass);
        x.hasPair = true;
        x.pairPt = p.Pt(); x.pairEta = p.Eta(); x.pairPhi = p.Phi(); x.pairMass = p.M();
        x.pairMassUncorr = q.M();
    }
    x.nPV = static_cast<float>(PV_npvs.get());
    x.nPVsGood = ev.nPVsGood();
    if (!IsDATA) {
        x.nTrueInt = ev.nTrueInt();
        x.nPileUp = ev.nPileUp();
    }
    x.rho = rho_;
}

void DiLepton::FillLane(const LaneHists &h, int ch, const FillVals &x, float w) const {
    for (int i = 0; i < x.nMu; ++i) {
        const auto &v = x.mu[i];
        const auto &k = h.mu[i];
        k.pt.Fill(v.pt, w); k.miniAODPt.Fill(v.miniAODPt, w); k.eta.Fill(v.eta, w);
        k.phi.Fill(v.phi, w); k.mass.Fill(v.mass, w); k.miniRelIso.Fill(v.miniRelIso, w);
        k.sip3d.Fill(v.sip3d, w); k.dz.Fill(v.dz, w);
    }
    for (int i = 0; i < x.nEl; ++i) {
        const auto &v = x.el[i];
        const auto &k = h.el[i];
        k.pt.Fill(v.pt, w); k.miniAODPt.Fill(v.miniAODPt, w); k.eta.Fill(v.eta, w);
        k.scEta.Fill(v.scEta, w); k.phi.Fill(v.phi, w); k.mass.Fill(v.mass, w);
        k.miniRelIso.Fill(v.miniRelIso, w); k.sip3d.Fill(v.sip3d, w); k.dz.Fill(v.dz, w);
    }
    if (ch != kZEE) {
        for (int i = 0; i < x.nJet; ++i) {
            const auto &v = x.jet[i];
            const auto &k = h.jet[i];
            k.pt.Fill(v.pt, w); k.rawPt.Fill(v.rawPt, w); k.originalPt.Fill(v.originalPt, w);
            k.eta.Fill(v.eta, w); k.phi.Fill(v.phi, w); k.mass.Fill(v.mass, w);
        }
        for (int i = 0; i < x.nBJet; ++i) {
            const auto &v = x.bjet[i];
            const auto &k = h.bjet[i];
            k.pt.Fill(v.pt, w); k.eta.Fill(v.eta, w); k.phi.Fill(v.phi, w); k.mass.Fill(v.mass, w);
        }
        h.jetsSize.Fill(x.jetsSize, w);
        h.bjetsSize.Fill(x.bjetsSize, w);
        h.metPt.Fill(x.metPt, w); h.metPhi.Fill(x.metPhi, w);
        h.metDefPt.Fill(x.metDefPt, w); h.metDefPhi.Fill(x.metDefPhi, w);
    }
    if (x.hasPair) {
        h.pairPt.Fill(x.pairPt, w); h.pairEta.Fill(x.pairEta, w); h.pairPhi.Fill(x.pairPhi, w);
        h.pairMass.Fill(x.pairMass, w); h.pairMassUncorr.Fill(x.pairMassUncorr, w);
    }
    h.nPV.Fill(x.nPV, w);
    h.nPVsGood.Fill(x.nPVsGood, w);
    if (!IsDATA) {
        h.nTrueInt.Fill(x.nTrueInt, w);
        h.nPileUp.Fill(x.nPileUp, w);
    }
    h.rho.Fill(x.rho, w);
}

// ---------------------------------------------------------------------------
void DiLepton::FillIDCheck(float w0) {
    static_cast<void>(w0);
    for (std::size_t i = 0; i < muBits_.size(); ++i) {
        const auto m = muons_[i];
        if (!(m.MiniAODPt() > 10.f && std::fabs(m.Eta()) < 2.4f)) continue;
        idMu_.Fill(0.5);
        if (muBits_[i] & kLoose) idMu_.Fill(1.5);
        if (muBits_[i] & kTight) idMu_.Fill(2.5);
    }
    for (std::size_t i = 0; i < elBits_.size(); ++i) {
        const auto e = electrons_[i];
        if (!(e.MiniAODPt() > 10.f && std::fabs(e.Eta()) < 2.5f)) continue;
        const auto &c = *elCols;
        const float vals[8] = {c.deltaEtaInSC[i], c.deltaPhiInSC[i], c.deltaPhiInSeed[i],
                               c.ecalPFClusIso[i], c.hcalPFClusIso[i], c.dr03HcalTowerSumEt[i],
                               c.superclusterPhi[i], c.superclusterEnergy[i]};
        float mn = vals[0];
        for (float v : vals) mn = std::min(mn, v);
        idElMinCustom_.Fill(std::max(mn, -999.5f));
        idElDEta_.Fill(vals[0]);
        idElDPhiSeed_.Fill(vals[2]);
        idElEcalIso_.Fill(vals[3]);
        idElHcalIso_.Fill(vals[4]);
        idElEcalIsoRel_.Fill(vals[3] / e.MiniAODPt());
        idElHcalIsoRel_.Fill(vals[4] / e.MiniAODPt());
        idEl_.Fill(0.5);
        if (PassElectronTriggerEmulation(e, i, rho_)) idEl_.Fill(1.5);
        if (elBits_[i] & kLoose) idEl_.Fill(2.5);
        if (elBits_[i] & kTight) idEl_.Fill(3.5);
    }
}

void DiLepton::executeEvent() {
    Event ev = GetEvent();
    if (lumi_ < 0.f) lumi_ = IsDATA ? 1.f : ev.GetTriggerLumi("Full");
    const float w0 = IsDATA ? 1.f : MCweight() * lumi_;
    cutflowAll_.Fill(0., w0);
    if (runIDCheck_) {
        // Before any event filter, so it compares with a plain branch scan.
        muons_ = GetAllMuonViews();
        electrons_ = GetAllElectronViews();
        rho_ = Rho_fixedGridRhoFastjetAll;
        EvaluateMuonIDs(muons_, muBits_);
        EvaluateElectronIDs(electrons_, rho_, elBits_);
        FillIDCheck(w0);
    }

    jets_ = GetAllJetViews();
    if (!PassEventFilters(jets_, ev)) return;
    cutflowAll_.Fill(1., w0);

    // Jet eta-phi of the veto-map jet selection (as in PassJetVetoMap).
    const auto vetoJets = SelectJetIndices(jets_, JetView::JetID::TIGHTLEPVETO, 15.f, 5.f);
    for (const auto i : vetoJets) {
        const auto j = jets_[i];
        if (j.ChEmEF() + j.NeEmEF() > 0.9f) continue;
        jetEtaPhiBefore_.Fill(j.Eta(), j.Phi(), w0);
    }
    if (!runNoJetVeto_ && !PassJetVetoMap(jets_, "jetvetomap")) return;
    cutflowAll_.Fill(2., w0);
    for (const auto i : vetoJets) {
        const auto j = jets_[i];
        if (j.ChEmEF() + j.NeEmEF() > 0.9f) continue;
        jetEtaPhiAfter_.Fill(j.Eta(), j.Phi(), w0);
    }

    muons_ = GetAllMuonViews();
    electrons_ = GetAllElectronViews();
    rho_ = Rho_fixedGridRhoFastjetAll;
    EvaluateMuonIDs(muons_, muBits_);
    EvaluateElectronIDs(electrons_, rho_, elBits_);
    cutflowAll_.Fill(3., w0);

    trig_[kDIMU] = channels_[kDIMU].enabled &&
                   ev.PassTrigger(TString("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8"));
    trig_[kEMU] = channels_[kEMU].enabled &&
                  ev.PassTrigger(RVec<TString>{"HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
                                               "HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ"});
    trig_[kZEE] = channels_[kZEE].enabled && ev.PassTrigger(TString("HLT_Ele30_WPTight_Gsf"));
    if (!trig_[kDIMU] && !trig_[kEMU] && !trig_[kZEE]) {
        // Still fill the lepton-stage cutflow bin for consistency with the old
        // code: lepton counts are checked before the trigger.
        LepSel lep;
        BuildLeptons(EvtVar::Central, lep);
        for (int ch = 0; ch < kNChannels; ++ch)
            if (channels_[ch].enabled) Select(ch, EvtVar::Central, lep, nullptr, nullptr, w0, true);
        return;
    }

    bool weightsReady = false;
    bool metNomReady = false;
    LepSel nomLep, varLep;
    BuildLeptons(EvtVar::Central, nomLep);
    SelectedJetViewCollection nomJets, varJets;
    bool nomJetsReady = false;
    std::vector<std::size_t> bjetPos;
    FillVals vals;
    FactorValues fv;

    for (const EvtVar v : activeEvtVars_) {
        const bool central = v == EvtVar::Central;
        const LepSel *lep = &nomLep;
        if (IsMuonVar(v) || IsElectronVar(v)) {
            BuildLeptons(v, varLep);
            lep = &varLep;
        }
        for (int ch = 0; ch < kNChannels; ++ch) {
            auto &conf = channels_[ch];
            if (!conf.enabled || !LaneApplies(ch, v)) continue;
            const EvtLane *lane = nullptr;
            for (const auto &l : conf.evtLanes) if (l.var == v) { lane = &l; break; }
            if (!lane) continue;
            if (!Select(ch, v, *lep, nullptr, nullptr, w0, central)) continue;

            const SelectedJetViewCollection *jets = nullptr;
            if (ch != kZEE) {
                const bool sameLeptons = lep->muLoose == nomLep.muLoose && lep->elLoose == nomLep.elLoose;
                if (!IsJetVar(v) && sameLeptons) {
                    if (!nomJetsReady) { nomJets = BuildJets(EvtVar::Central, nomLep); nomJetsReady = true; }
                    jets = &nomJets;
                } else {
                    varJets = BuildJets(v, *lep);
                    jets = &varJets;
                }
                if (!metNomReady) {
                    Particle z1, z2, z3;
                    PropagateJetSystToMET(jets_, z1);
                    PropagateMuonCorrToMET(muons_, z2);
                    PropagateElectronCorrToMET(electrons_, z3);
                    metJetNomX_ = z1.Px(); metJetNomY_ = z1.Py();
                    metMuNomX_ = z2.Px(); metMuNomY_ = z2.Py();
                    metElNomX_ = z3.Px(); metElNomY_ = z3.Py();
                    metNomReady = true;
                }
                if (!Select(ch, v, *lep, jets, &bjetPos, w0, central)) continue;
            }
            if (central) conf.cutflow.Fill(8, w0);

            if (!IsDATA && !weightsReady) {
                puWeight_[0] = myCorr->GetPUWeight(ev.nTrueInt(), V::nom);
                puWeight_[1] = runSyst_ ? myCorr->GetPUWeight(ev.nTrueInt(), V::up) : puWeight_[0];
                puWeight_[2] = runSyst_ ? myCorr->GetPUWeight(ev.nTrueInt(), V::down) : puWeight_[0];
                topPtWeight_ = TopPtWeight();
                weightsReady = true;
            }
            const bool allVar = central && runSyst_;
            ComputeFactors(ch, *lep, jets, &bjetPos, allVar, fv);
            float sfProd = 1.f;
            for (int f = 0; f < kNFactors; ++f) sfProd *= fv.nom(f);
            const float wc = w0 * sfProd;

            MakeFillVals(ch, v, ev, *lep, jets, &bjetPos, vals);
            FillLane(lane->hists, ch, vals, wc);

            if (central && !IsDATA) {
                auto &wh = conf.weights;
                const float gw = genWeight;
                wh.genWeight.Fill(gw, 1.f);
                wh.log10AbsGenWeight.Fill(gw != 0.f ? std::log10(std::fabs(gw)) : -4.f, 1.f);
                wh.mcWeight.Fill(w0 != 0.f ? std::log10(std::fabs(w0)) : -10.f, 1.f);
                wh.pileupWeight.Fill(fv.nom(kFPU), 1.f);
                wh.topPtWeight.Fill(topPtWeight_, 1.f);
                wh.total.Fill(sfProd, 1.f);
                if (wh.eleRecoSF) wh.eleRecoSF.Fill(fv.nom(kFEleReco), 1.f);
                if (wh.btagSF) wh.btagSF.Fill(fv.nom(kFBTag), 1.f);
                if (wh.eleIDSFProxy) wh.eleIDSFProxy.Fill(fv.nom(kFEleIDProxy), 1.f);
                if (wh.eleTrigSFProxy) wh.eleTrigSFProxy.Fill(fv.nom(kFEleTrigProxy), 1.f);
                if (wh.muIDSF) wh.muIDSF.Fill(fv.nom(kFMuID), 1.f);
                if (wh.eleIDSF) wh.eleIDSF.Fill(fv.nom(kFEleID), 1.f);
            }
            if (allVar) {
                for (const auto &wl : conf.weightLanes) {
                    float w = w0;
                    if (wl.topPt) {
                        w = wc * topPtWeight_;
                    } else {
                        for (int f = 0; f < kNFactors; ++f) {
                            if (f != wl.factor) w *= fv.nom(f);
                            else if (!wl.notImplemented) w *= fv.vars[f][wl.valueIndex];
                        }
                    }
                    FillLane(wl.hists, ch, vals, w);
                }
            }
        }
    }
}
