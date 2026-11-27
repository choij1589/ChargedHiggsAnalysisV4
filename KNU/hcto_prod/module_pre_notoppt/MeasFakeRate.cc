#include <HcToWA/MeasFakeRate.h>

#include <algorithm>
#include <cmath>
#include <iostream>

namespace {

using V = MyCorrection::variation;

const std::vector<float> kEtaEdges = {0.f, 0.8f, 0.9f, 1.2f, 1.444f, 1.479f, 1.566f, 1.6f, 2.0f, 2.1f, 2.4f, 2.5f};
std::vector<float> PtCorrEdges() {
    std::vector<float> e;
    for (int i = 10; i < 20; ++i) e.push_back(static_cast<float>(i));
    for (float x = 20.f; x < 40.f; x += 2.5f) e.push_back(x);
    for (float x : {40.f, 45.f, 50.f, 55.f, 60.f, 70.f, 80.f, 100.f, 120.f, 150.f, 200.f, 300.f}) e.push_back(x);
    return e;
}
const std::vector<float> kPtCorrEdges = PtCorrEdges();

const char *kRegionName[MeasFakeRate::kNRegions] = {"QCD", "W", "Inc"};
const char *kSelName[MeasFakeRate::kNSels] = {"Nom", "Away20", "Away30", "Away60", "BTag"};
const char *kLaneName[MeasFakeRate::kNLanes] = {
    "JetEnUp", "JetEnDown", "JetResUp", "JetResDown", "UnclusteredEnUp", "UnclusteredEnDown",
    "MuonEnUp", "MuonEnDown", "MuonResUp", "MuonResDown",
    "ElectronEnUp", "ElectronEnDown", "ElectronResUp", "ElectronResDown",
    "PileupUp", "PileupDown"};
const char *kIDName[2] = {"loose", "tight"};
const std::vector<std::string> kClsData = {"data"};
const std::vector<std::string> kClsMC = {"prompt", "conv", "b", "c", "light", "other"};
const std::vector<std::string> kCls2MC = {"prompt", "nonprompt"};
// control variables: MT, MET, pT, |eta|, nPVsGood
const char *kCtlName[5] = {"MT", "MET", "pt", "abseta", "nPVsGood"};
const char *kCtlZName[2] = {"nPVsGood", "ptLead"};

inline float DeltaR(float eta1, float phi1, float eta2, float phi2) {
    const float deta = eta1 - eta2;
    float dphi = std::fabs(phi1 - phi2);
    if (dphi > static_cast<float>(M_PI)) dphi = 2.f * static_cast<float>(M_PI) - dphi;
    return std::sqrt(deta * deta + dphi * dphi);
}
inline float DeltaPhi(float a, float b) {
    float d = std::fabs(a - b);
    if (d > static_cast<float>(M_PI)) d = 2.f * static_cast<float>(M_PI) - d;
    return d;
}

V JesVar(int lane) { return lane == MeasFakeRate::kJESUp ? V::up : (lane == MeasFakeRate::kJESDown ? V::down : V::nom); }
V JerVar(int lane) { return lane == MeasFakeRate::kJERUp ? V::up : (lane == MeasFakeRate::kJERDown ? V::down : V::nom); }
bool IsJetLane(int lane) { return lane >= MeasFakeRate::kJESUp && lane <= MeasFakeRate::kJERDown; }

} // namespace

MeasFakeRate::MeasFakeRate() {}
MeasFakeRate::~MeasFakeRate() {}

void MeasFakeRate::initializeAnalyzer() {
    HcToWABase::initializeAnalyzer();
    doMu_ = HasFlag("MeasMuFR");
    doEl_ = HasFlag("MeasElFR");
    if (!doMu_ && !doEl_) throw SKNano::ConfigError("[MeasFakeRate] no mode flag (MeasMuFR, MeasElFR)");
    nCls_ = IsDATA ? 1 : static_cast<int>(kClsMC.size());
    promptMC_ = !IsDATA && !MCSample.Contains("QCD");
    if (!IsDATA) LoadBTagCorrections();

    mu_.muon = true;
    mu_.paths = {{"HLT_Mu8_TrkIsoVVL", "Mu8", true, 10.f},
                 {"HLT_Mu17_TrkIsoVVL", "Mu17", true, 20.f}};
    el_.muon = false;
    el_.paths = {{"HLT_Ele8_CaloIdL_TrackIdL_IsoVL_PFJet30", "Ele8", false, 10.f},
                 {"HLT_Ele12_CaloIdL_TrackIdL_IsoVL_PFJet30", "Ele12", false, 15.f},
                 {"HLT_Ele23_CaloIdL_TrackIdL_IsoVL_PFJet30", "Ele23", false, 25.f}};
    if (doMu_) BookMode(mu_);
    if (doEl_) BookMode(el_);
    cout << "[MeasFakeRate] muons " << doMu_ << ", electrons " << doEl_ << ", prompt-MC lanes "
         << promptMC_ << ", b-tag weight " << BTagWeightAvailable() << endl;
}

void MeasFakeRate::BookMode(Mode &m) {
    const std::string top = m.muon ? "MuFR" : "ElFR";
    const int nEta = static_cast<int>(kEtaEdges.size()) - 1, nPt = static_cast<int>(kPtCorrEdges.size()) - 1;
    const auto &cls = IsDATA ? kClsData : kClsMC;
    const std::vector<std::string> cls2 = IsDATA ? kClsData : kCls2MC;
    const int nP = static_cast<int>(m.paths.size());
    m.cutflow = Hists(top).Book1D("cutflow", 8, 0., 8.);
    m.h2.resize(static_cast<std::size_t>(nP) * kNRegions * 2 * kNSels * nCls_);
    m.hZ.resize(static_cast<std::size_t>(nP) * 2 * kNSels * nCls_ * 2);
    m.ctl.resize(static_cast<std::size_t>(nP) * kNRegions * 2 * cls2.size() * 5);
    m.ctlZ.resize(static_cast<std::size_t>(nP) * 2 * cls2.size() * 2);
    for (int p = 0; p < nP; ++p) {
        const std::string pl = top + "/" + m.paths[p].label;
        for (int id = 0; id < 2; ++id) {
            for (int s = 0; s < kNSels; ++s)
                for (int c = 0; c < nCls_; ++c) {
                    for (int r = 0; r < kNRegions; ++r)
                        m.h2[I2(m, p, r, id, s, c)] =
                            Hists(pl + "/" + kRegionName[r] + "/" + kIDName[id] + "/" + kSelName[s] + "/" + cls[c])
                                .Book2D("ptcorr_abseta", nEta, kEtaEdges.data(), nPt, kPtCorrEdges.data());
                    for (int sign = 0; sign < 2; ++sign)
                        m.hZ[IZ(p, id, s, c, sign)] =
                            Hists(pl + "/Z/" + kIDName[id] + "/" + kSelName[s] + "/" + cls[c])
                                .Book1D(sign == 0 ? "mll_os" : "mll_ss", 60, 60., 120.);
                }
            for (std::size_t c2 = 0; c2 < cls2.size(); ++c2) {
                for (int r = 0; r < kNRegions; ++r) {
                    auto g = Hists(pl + "/Control/" + kRegionName[r] + "/" + kIDName[id] + "/" + cls2[c2]);
                    const std::size_t b = (((static_cast<std::size_t>(p) * kNRegions + r) * 2 + id) * cls2.size() + c2) * 5;
                    m.ctl[b + 0] = g.Book1D(kCtlName[0], 60, 0., 150.);
                    m.ctl[b + 1] = g.Book1D(kCtlName[1], 60, 0., 150.);
                    m.ctl[b + 2] = g.Book1D(kCtlName[2], 100, 0., 200.);
                    m.ctl[b + 3] = g.Book1D(kCtlName[3], 25, 0., 2.5);
                    m.ctl[b + 4] = g.Book1D(kCtlName[4], 100, 0., 100.);
                }
                auto gz = Hists(pl + "/Control/Z/" + kIDName[id] + "/" + cls2[c2]);
                const std::size_t bz = ((static_cast<std::size_t>(p) * 2 + id) * cls2.size() + c2) * 2;
                m.ctlZ[bz + 0] = gz.Book1D(kCtlZName[0], 100, 0., 100.);
                m.ctlZ[bz + 1] = gz.Book1D(kCtlZName[1], 100, 0., 200.);
            }
        }
    }
    if (promptMC_) {
        m.lane2.resize(static_cast<std::size_t>(kNLanes) * nP * 2);
        m.laneZ.resize(static_cast<std::size_t>(kNLanes) * nP * 2);
        for (int l = 0; l < kNLanes; ++l)
            for (int p = 0; p < nP; ++p)
                for (int id = 0; id < 2; ++id) {
                    const std::size_t i = (static_cast<std::size_t>(l) * nP + p) * 2 + id;
                    const std::string d = top + "/" + m.paths[p].label + "/Lanes/" + kLaneName[l] + "/" + kIDName[id];
                    m.lane2[i] = Hists(d).Book2D("QCD_ptcorr_abseta", nEta, kEtaEdges.data(), nPt, kPtCorrEdges.data());
                    m.laneZ[i] = Hists(d).Book1D("Z_mll_os", 60, 60., 120.);
                }
    }
}

float MeasFakeRate::LepPt(bool muon, std::size_t i, int lane) const {
    if (muon) {
        const auto m = muons_[i];
        switch (lane) {
        case kMuEnUp: return m.MomentumScaleUp();
        case kMuEnDown: return m.MomentumScaleDown();
        case kMuResUp: return m.MomentumResUp();
        case kMuResDown: return m.MomentumResDown();
        default: return m.Pt();
        }
    }
    const auto e = electrons_[i];
    switch (lane) {
    case kElEnUp: return e.ScaleUpPt();
    case kElEnDown: return e.ScaleDownPt();
    case kElResUp: return e.SmearUpPt();
    case kElResDown: return e.SmearDownPt();
    default: return e.Pt();
    }
}

// 0 prompt, 1 conv, 2 b, 3 c, 4 light, 5 other (MC only).
int MeasFakeRate::LepClass(bool muon, std::size_t i) const {
    if (IsDATA) return 0;
    const unsigned char flav = muon ? muons_[i].GenPartFlav() : electrons_[i].GenPartFlav();
    if (flav == 1 || flav == 15) return 0;
    if (flav == 22) return 1;
    const short j = muon ? muons_[i].JetIdx() : electrons_[i].JetIdx();
    if (j < 0 || static_cast<std::size_t>(j) >= jets_.size()) return 5;
    const auto jet = jets_[j];
    if (jet.GenJetIdx() < 0) return 5;
    switch (jet.HadronFlavour()) {
    case 5: return 2;
    case 4: return 3;
    case 0: return 4;
    default: return 5;
    }
}

bool MeasFakeRate::PassSel(int s, const Kin &k) const {
    switch (s) {
    case kNom: return k.awayPt > 40.f;
    case kAway20: return k.awayPt > 20.f;
    case kAway30: return k.awayPt > 30.f;
    case kAway60: return k.awayPt > 60.f;
    case kBTag: return k.awayPt > 40.f && k.nB >= 1;
    default: return false;
    }
}

// lane < 0: central. Jet quantities are recomputed only for the JES/JER lanes;
// the other lanes copy them from the central Kin passed in `k`.
void MeasFakeRate::ComputeKin(const Mode &m, const std::vector<std::size_t> &lep, int lane, const Event &ev, Kin &k) {
    for (std::size_t i = 0; i < lep.size() && i < 2; ++i) k.lepPt[i] = LepPt(m.muon, lep[i], lane);
    const float eta0 = m.muon ? muons_[lep[0]].Eta() : electrons_[lep[0]].Eta();
    const float phi0 = m.muon ? muons_[lep[0]].Phi() : electrons_[lep[0]].Phi();
    if (lane < 0 || IsJetLane(lane)) {
        const V jes = lane < 0 ? V::nom : JesVar(lane), jer = lane < 0 ? V::nom : JerVar(lane);
        auto idx = SelectJetIndices(jets_, JetView::JetID::TIGHT, 20.f, 2.5f, jes, jer);
        idx = RemoveOverlapIndices(jets_, idx, electrons_, elLoose_, 0.4f);
        idx = RemoveOverlapIndices(jets_, idx, muons_, muLoose_, 0.4f);
        const auto sj = SelectJetViews(jets_, std::move(idx), jes, jer);
        k.awayPt = -1.f;
        k.nB = 0;
        std::vector<BTagJet> bj;
        for (std::size_t j = 0; j < sj.size(); ++j) {
            const auto jet = sj[j];
            const float pt = jet.Pt();
            if (DeltaR(eta0, phi0, jet.Eta(), jet.Phi()) > 0.7f && pt > k.awayPt) k.awayPt = pt;
            const bool tagged = jet.GetTaggerResult(JetTagging::JetFlavTagger::ParT,
                                                    JetTagging::JetFlavTaggerScoreType::B) > bTagWP;
            if (tagged) ++k.nB;
            if (!IsDATA) bj.push_back({pt, jet.Eta(), static_cast<int>(jet.HadronFlavour()), tagged});
        }
        k.btagW = 1.f;
        if (!IsDATA && lane < 0 && BTagWeightAvailable()) {
            std::array<float, kNBTagLanes> out{};
            BTagWeights(bj, false, out);
            k.btagW = out[kBTagNom];
        }
    }
    // MET: raw PUPPI + corrections propagated from jets, muons, electrons (as DiLepton).
    Particle raw = rawMET_;
    if (lane == kUEUp) raw = ev.GetMETVector(Event::MET_Type::PUPPI, SKNano::Variation::up, Event::MET_Syst::UE);
    if (lane == kUEDown) raw = ev.GetMETVector(Event::MET_Type::PUPPI, SKNano::Variation::down, Event::MET_Syst::UE);
    double jx = dMetJetNom_[0], jy = dMetJetNom_[1], mx = dMetMuNom_[0], my = dMetMuNom_[1],
           ex = dMetElNom_[0], ey = dMetElNom_[1];
    if (IsJetLane(lane)) {
        Particle z;
        PropagateJetSystToMET(jets_, z, JesVar(lane), JerVar(lane));
        jx = z.Px(); jy = z.Py();
    } else if (lane >= kMuEnUp && lane <= kMuResDown) {
        Particle z;
        const V s = lane == kMuEnUp ? V::up : (lane == kMuEnDown ? V::down : V::nom);
        const V r = lane == kMuResUp ? V::up : (lane == kMuResDown ? V::down : V::nom);
        PropagateMuonCorrToMET(muons_, z, s, r);
        mx = z.Px(); my = z.Py();
    } else if (lane >= kElEnUp && lane <= kElResDown) {
        Particle z;
        const V s = lane == kElEnUp ? V::up : (lane == kElEnDown ? V::down : V::nom);
        const V r = lane == kElResUp ? V::up : (lane == kElResDown ? V::down : V::nom);
        PropagateElectronCorrToMET(electrons_, z, s, r);
        ex = z.Px(); ey = z.Py();
    }
    const double px = raw.Px() + jx + mx + ex, py = raw.Py() + jy + my + ey;
    k.metPt = static_cast<float>(std::hypot(px, py));
    k.metPhi = static_cast<float>(std::atan2(py, px));
}

void MeasFakeRate::executeEvent() {
    Event ev = GetEvent();
    // 1. Trigger decision first (most data events fail the prescaled paths).
    bool any = false;
    for (Mode *m : {&mu_, &el_}) {
        if ((m == &mu_ && !doMu_) || (m == &el_ && !doEl_)) continue;
        for (auto &p : m->paths) {
            p.fired = ev.PassTrigger(TString(p.hlt));
            any |= p.fired;
        }
    }
    if (!any) return;

    if (lumi_ < 0.f) lumi_ = IsDATA ? 1.f : ev.GetTriggerLumi("Full");
    float w0 = 1.f;
    if (!IsDATA) {
        pu_[0] = myCorr->GetPUWeight(ev.nTrueInt(), V::nom);
        pu_[1] = promptMC_ ? myCorr->GetPUWeight(ev.nTrueInt(), V::up) : pu_[0];
        pu_[2] = promptMC_ ? myCorr->GetPUWeight(ev.nTrueInt(), V::down) : pu_[0];
        w0 = MCweight() * lumi_ * pu_[0] * TopPtWeight();
    }
    if (doMu_) mu_.cutflow.Fill(0., w0);
    if (doEl_) el_.cutflow.Fill(0., w0);

    // 2. Event filters, jet veto map.
    jets_ = GetAllJetViews();
    if (!PassEventFilters(jets_, ev)) return;
    if (!PassJetVetoMap(jets_, "jetvetomap")) return;
    if (doMu_) mu_.cutflow.Fill(1., w0);
    if (doEl_) el_.cutflow.Fill(1., w0);

    // 3. One lepton pass: loose leptons with pT > 10 GeV (corrected), pT-sorted.
    muons_ = GetAllMuonViews();
    electrons_ = GetAllElectronViews();
    EvaluateMuonIDs(muons_, muBits_);
    EvaluateElectronIDs(electrons_, Rho_fixedGridRhoFastjetAll, elBits_);
    muLoose_.clear();
    elLoose_.clear();
    for (std::size_t i = 0; i < muBits_.size(); ++i)
        if ((muBits_[i] & kLoose) && std::fabs(muons_[i].Eta()) < 2.4f && muons_[i].Pt() > 10.f) muLoose_.push_back(i);
    for (std::size_t i = 0; i < elBits_.size(); ++i)
        if ((elBits_[i] & kLoose) && std::fabs(electrons_[i].Eta()) < 2.5f && electrons_[i].Pt() > 10.f) elLoose_.push_back(i);
    std::sort(muLoose_.begin(), muLoose_.end(), [&](std::size_t a, std::size_t b) { return muons_[a].Pt() > muons_[b].Pt(); });
    std::sort(elLoose_.begin(), elLoose_.end(), [&](std::size_t a, std::size_t b) { return electrons_[a].Pt() > electrons_[b].Pt(); });
    const bool muCand = doMu_ && elLoose_.empty() && (muLoose_.size() == 1 || muLoose_.size() == 2);
    const bool elCand = doEl_ && muLoose_.empty() && (elLoose_.size() == 1 || elLoose_.size() == 2);
    if (!muCand && !elCand) return;

    // 4. Shared per-event inputs, only for candidate events.
    rawMET_ = ev.GetMETVector(Event::MET_Type::PUPPI);
    {
        Particle z1, z2, z3;
        PropagateJetSystToMET(jets_, z1);
        PropagateMuonCorrToMET(muons_, z2);
        PropagateElectronCorrToMET(electrons_, z3);
        dMetJetNom_[0] = z1.Px(); dMetJetNom_[1] = z1.Py();
        dMetMuNom_[0] = z2.Px(); dMetMuNom_[1] = z2.Py();
        dMetElNom_[0] = z3.Px(); dMetElNom_[1] = z3.Py();
    }
    if (muCand) RunMode(mu_, ev, w0);
    if (elCand) RunMode(el_, ev, w0);
}

void MeasFakeRate::RunMode(Mode &m, const Event &ev, float w0) {
    const std::vector<std::size_t> &lep = m.muon ? muLoose_ : elLoose_;
    const std::vector<std::uint8_t> &bits = m.muon ? muBits_ : elBits_;
    const bool single = lep.size() == 1;
    if (single && !m.muon && !(electrons_[lep[0]].Pt() > 15.f)) return;
    m.cutflow.Fill(single ? 2. : 3., w0);

    auto lepEta = [&](std::size_t i) { return m.muon ? muons_[i].Eta() : electrons_[i].Eta(); };
    auto lepPhi = [&](std::size_t i) { return m.muon ? muons_[i].Phi() : electrons_[i].Phi(); };
    auto lepM = [&](std::size_t i) { return m.muon ? muons_[i].M() : electrons_[i].M(); };
    auto binEta = [&](std::size_t i) {
        return m.muon ? std::fabs(muons_[i].Eta()) : std::fabs(electrons_[i].ScEta());
    };
    auto relIso = [&](std::size_t i) {
        return m.muon ? muons_[i].MiniPFRelIso() : electrons_[i].MiniPFRelIso();
    };

    Kin k;
    ComputeKin(m, lep, -1, ev, k);
    const bool tight0 = bits[lep[0]] & kTight;
    const bool tightAll = single ? tight0 : (tight0 && (bits[lep[1]] & kTight));
    // electrons: tight requires pT > 15 GeV, as in the analysis
    const bool tightOK = m.muon ? tightAll
                                : (tightAll && electrons_[lep[0]].Pt() > 15.f &&
                                   (single || electrons_[lep[1]].Pt() > 15.f));
    int cls = LepClass(m.muon, lep[0]);
    if (!single && cls == 0) cls = LepClass(m.muon, lep[1]); // Z: the non-prompt lepton, if any
    const int cls2 = IsDATA ? 0 : (cls == 0 ? 0 : 1);
    const std::size_t nCls2 = IsDATA ? 1 : 2;
    const float npv = static_cast<float>(ev.nPVsGood());
    const int nP = static_cast<int>(m.paths.size());

    // Quantities per lane for the single-lepton region and the Z region.
    auto ptcorrOf = [&](float pt) { return pt * (1.f + std::max(0.f, relIso(lep[0]) - 0.1f)); };
    auto mtOf = [&](float pt, const Kin &kk) {
        return std::sqrt(2.f * pt * kk.metPt * (1.f - std::cos(DeltaPhi(lepPhi(lep[0]), kk.metPhi))));
    };
    auto mllOf = [&](const Kin &kk) {
        TLorentzVector a, b;
        a.SetPtEtaPhiM(kk.lepPt[0], lepEta(lep[0]), lepPhi(lep[0]), lepM(lep[0]));
        b.SetPtEtaPhiM(kk.lepPt[1], lepEta(lep[1]), lepPhi(lep[1]), lepM(lep[1]));
        return static_cast<float>((a + b).M());
    };
    const int sign = single ? 0 : ((m.muon ? muons_[lep[0]].Charge() * muons_[lep[1]].Charge()
                                           : electrons_[lep[0]].Charge() * electrons_[lep[1]].Charge()) < 0 ? 0 : 1);

    bool filled = false;
    for (int p = 0; p < nP; ++p) {
        const Path &path = m.paths[p];
        if (!path.fired) continue;
        if (!(k.lepPt[0] > path.offPt)) continue;

        if (single) {
            const float ptcorr = ptcorrOf(k.lepPt[0]);
            const float aeta = binEta(lep[0]);
            const float mt = mtOf(k.lepPt[0], k);
            const bool inReg[kNRegions] = {k.metPt < 25.f && mt < 25.f, mt > 60.f, true};
            for (int id = 0; id < 2; ++id) {
                if (id == 1 && !tightOK) continue;
                for (int s = 0; s < kNSels; ++s) {
                    if (!PassSel(s, k)) continue;
                    const float w = s == kBTag ? w0 * k.btagW : w0;
                    for (int r = 0; r < kNRegions; ++r)
                        if (inReg[r]) m.h2[I2(m, p, r, id, s, cls)].Fill(aeta, ptcorr, w);
                    if (s != kNom) continue;
                    filled = true;
                    for (int r = 0; r < kNRegions; ++r) {
                        if (!inReg[r]) continue;
                        const std::size_t b = (((static_cast<std::size_t>(p) * kNRegions + r) * 2 + id) * nCls2 + cls2) * 5;
                        m.ctl[b + 0].Fill(mt, w);
                        m.ctl[b + 1].Fill(k.metPt, w);
                        m.ctl[b + 2].Fill(k.lepPt[0], w);
                        m.ctl[b + 3].Fill(aeta, w);
                        m.ctl[b + 4].Fill(npv, w);
                    }
                }
            }
        } else {
            const float mll = mllOf(k);
            for (int id = 0; id < 2; ++id) {
                if (id == 1 && !tightOK) continue;
                for (int s = 0; s < kNSels; ++s) {
                    if (!PassSel(s, k)) continue;
                    const float w = s == kBTag ? w0 * k.btagW : w0;
                    m.hZ[IZ(p, id, s, cls, sign)].Fill(mll, w);
                    if (s == kNom && sign == 0 && std::fabs(mll - 91.2f) < 15.f) {
                        filled = true;
                        const std::size_t bz = ((static_cast<std::size_t>(p) * 2 + id) * nCls2 + cls2) * 2;
                        m.ctlZ[bz + 0].Fill(npv, w);
                        m.ctlZ[bz + 1].Fill(k.lepPt[0], w);
                    }
                }
            }
        }
    }
    if (filled) m.cutflow.Fill(single ? 4. : 5., w0);

    // Prompt-MC lanes (F5 c): nominal selection only.
    if (!promptMC_) return;
    for (int l = 0; l < kNLanes; ++l) {
        if (m.muon && l >= kElEnUp && l <= kElResDown) continue;   // no effect on the muon selection
        if (!m.muon && l >= kMuEnUp && l <= kMuResDown) continue;  // except MET, negligible without muons
        Kin kl = k;
        ComputeKin(m, lep, l, ev, kl);
        const float wl = l == kPUUp ? w0 * pu_[1] / pu_[0] : (l == kPUDown ? w0 * pu_[2] / pu_[0] : w0);
        if (!PassSel(kNom, kl)) continue;
        for (int p = 0; p < nP; ++p) {
            const Path &path = m.paths[p];
            if (!path.fired || !(kl.lepPt[0] > path.offPt)) continue;
            for (int id = 0; id < 2; ++id) {
                if (id == 1 && !tightOK) continue;
                const std::size_t i = (static_cast<std::size_t>(l) * nP + p) * 2 + id;
                if (single) {
                    const float mt = mtOf(kl.lepPt[0], kl);
                    if (kl.metPt < 25.f && mt < 25.f) m.lane2[i].Fill(binEta(lep[0]), ptcorrOf(kl.lepPt[0]), wl);
                } else if (sign == 0) {
                    m.laneZ[i].Fill(mllOf(kl), wl);
                }
            }
        }
    }
}
