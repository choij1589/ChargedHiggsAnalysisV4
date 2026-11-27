#include <HcToWA/MuonTnPProducer.h>

#include <algorithm>
#include <cmath>
#include <iostream>

namespace {

using V = MyCorrection::variation;
constexpr float kMuonMass = 0.1056584f;

// NanoAOD v15 (CMSSW_15_0_X PhysicsTools/NanoAOD/python/triggerObjects_cff.py),
// TrigObj id 13 qualityBits:
//   0 TrkIsoVVL, 1 Iso, 2 OverlapFilter PFTau, 3 1mu (hltL3crIsoL1*SingleMu*IsoFiltered*),
//   4 2mu (hltDiMuon*Filtered*), 5 1mu-1e (hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*)
constexpr ULong64_t kBit1mu = 1ull << 3;
constexpr ULong64_t kBit2mu = 1ull << 4;
constexpr ULong64_t kBit1mu1e = 1ull << 5;

inline float DeltaPhi(float a, float b) {
    float d = a - b;
    while (d > static_cast<float>(M_PI)) d -= 2.f * static_cast<float>(M_PI);
    while (d <= -static_cast<float>(M_PI)) d += 2.f * static_cast<float>(M_PI);
    return d;
}
inline float DeltaR(float eta1, float phi1, float eta2, float phi2) {
    const float de = eta1 - eta2, dp = DeltaPhi(phi1, phi2);
    return std::sqrt(de * de + dp * dp);
}

// Muon trigger objects near (eta, phi): OR of their filter bits per pT
// threshold is not needed; each query asks for one bit and a pT cut.
struct TrigMatch {
    std::vector<std::size_t> idx; // muon TrigObj within dR
    std::size_t best = static_cast<std::size_t>(-1);
};
TrigMatch MatchTrigObjs(const TrigObjViewCollection &tos, float eta, float phi, int id) {
    TrigMatch m;
    float bestDR = MuonTnPProducer::kTrigDR;
    for (std::size_t k = 0; k < tos.size(); ++k) {
        const auto t = tos[k];
        if (t.Id() != id) continue;
        const float dr = DeltaR(eta, phi, t.Eta(), t.Phi());
        if (!(dr < MuonTnPProducer::kTrigDR)) continue;
        m.idx.push_back(k);
        if (dr < bestDR) { bestDR = dr; m.best = k; }
    }
    return m;
}
bool HasBit(const TrigObjViewCollection &tos, const TrigMatch &m, ULong64_t bit, float minPt) {
    for (const auto k : m.idx) {
        const auto t = tos[k];
        if ((t.FilterBits() & bit) && t.Pt() > minPt) return true;
    }
    return false;
}

} // namespace

MuonTnPProducer::MuonTnPProducer() {}
MuonTnPProducer::~MuonTnPProducer() {}

void MuonTnPProducer::initializeAnalyzer() {
    HcToWABase::initializeAnalyzer();
    if (!IsDATA) wNorm_ = (sumW != 0.f) ? sumSign / sumW : 1.f;
    cout << "[MuonTnPProducer] weight normalisation sumSign/sumW = " << wNorm_ << endl;

    out_ = Output().Book("muon/Events");
    auto &r = r_;
    out_.Field("run", r.run).Field("lumi", r.lumi).Field("event", r.event)
        .Field("nPV", r.nPV).Field("nPVsGood", r.nPVsGood).Field("rho", r.rho)
        .Field("PuppiMET_pt", r.puppiMET_pt).Field("PuppiMET_phi", r.puppiMET_phi);
    if (!IsDATA) {
        out_.Field("nTrueInt", r.nTrueInt).Field("genWeight", r.genWeight)
            .Field("PUweight", r.PUweight).Field("PUweight_up", r.PUweight_up)
            .Field("PUweight_down", r.PUweight_down).Field("weight", r.weight);
    }
    out_.Field("tag_IsoMu24", r.tag_IsoMu24).Field("tag_isTight", r.tag_isTight)
        .Field("tag_isMedium", r.tag_isMedium).Field("tag_isLoose", r.tag_isLoose)
        .Field("tag_pt", r.tag_pt).Field("tag_pt_cor", r.tag_pt_cor)
        .Field("tag_eta", r.tag_eta).Field("tag_phi", r.tag_phi).Field("tag_q", r.tag_q)
        .Field("tag_pfRelIso03", r.tag_pfRelIso03).Field("tag_pfRelIso04", r.tag_pfRelIso04)
        .Field("tag_tkRelIso", r.tag_tkRelIso).Field("tag_miniPFRelIso", r.tag_miniPFRelIso)
        .Field("tag_sip3d", r.tag_sip3d).Field("tag_dz", r.tag_dz).Field("tag_dxy", r.tag_dxy);
    out_.Field("probe_isTracker", r.probe_isTracker).Field("probe_isGlobal", r.probe_isGlobal)
        .Field("probe_isSA", r.probe_isSA).Field("probe_isPF", r.probe_isPF)
        .Field("probe_isTight", r.probe_isTight).Field("probe_isMedium", r.probe_isMedium)
        .Field("probe_isLoose", r.probe_isLoose).Field("probe_TkIsoLoose", r.probe_TkIsoLoose)
        .Field("probe_PFIsoTight", r.probe_PFIsoTight)
        .Field("probe_isHcToWALoose", r.probe_isHcToWALoose)
        .Field("probe_isHcToWATight", r.probe_isHcToWATight)
        .Field("probe_IsoMu24", r.probe_IsoMu24).Field("probe_Mu17Leg1", r.probe_Mu17Leg1)
        .Field("probe_Mu8Leg2", r.probe_Mu8Leg2).Field("probe_Mu23EMuLeg", r.probe_Mu23EMuLeg)
        .Field("probe_Mu8EMuLeg", r.probe_Mu8EMuLeg)
        .Field("probe_trigBits", r.probe_trigBits).Field("probe_trigPt", r.probe_trigPt)
        .Field("probe_isDuplicated", r.probe_isDuplicated)
        .Field("probe_nTagsIso0p1", r.probe_nTagsIso0p1)
        .Field("probe_nTagsIso0p2", r.probe_nTagsIso0p2)
        .Field("probe_nTagsIso0p3", r.probe_nTagsIso0p3)
        .Field("probe_pt", r.probe_pt).Field("probe_pt_cor", r.probe_pt_cor)
        .Field("probe_eta", r.probe_eta).Field("probe_phi", r.probe_phi).Field("probe_q", r.probe_q)
        .Field("probe_pfRelIso03", r.probe_pfRelIso03).Field("probe_pfRelIso04", r.probe_pfRelIso04)
        .Field("probe_tkRelIso", r.probe_tkRelIso).Field("probe_miniPFRelIso", r.probe_miniPFRelIso)
        .Field("probe_sip3d", r.probe_sip3d).Field("probe_dz", r.probe_dz).Field("probe_dxy", r.probe_dxy);
    out_.Field("pair_probeMultiplicity", r.pair_probeMultiplicity)
        .Field("pair_mass", r.pair_mass).Field("pair_mass_cor", r.pair_mass_cor)
        .Field("pair_pt", r.pair_pt).Field("pair_dr", r.pair_dr).Field("pair_EMTF", r.pair_EMTF);
    if (!IsDATA) {
        out_.Field("tag_gen_matched", r.tag_gen_matched).Field("probe_gen_matched", r.probe_gen_matched)
            .Field("pair_gen_matched", r.pair_gen_matched).Field("pair_gen_mass", r.pair_gen_mass)
            .Field("tag_gen_pt", r.tag_gen_pt).Field("tag_gen_eta", r.tag_gen_eta)
            .Field("tag_gen_phi", r.tag_gen_phi).Field("tag_gen_dR", r.tag_gen_dR)
            .Field("tag_gen_reldpt", r.tag_gen_reldpt)
            .Field("probe_gen_pt", r.probe_gen_pt).Field("probe_gen_eta", r.probe_gen_eta)
            .Field("probe_gen_phi", r.probe_gen_phi).Field("probe_gen_dR", r.probe_gen_dR)
            .Field("probe_gen_reldpt", r.probe_gen_reldpt);
    }

    const auto g = Hists("TnP");
    // 0 all, 1 event filters, 2 HLT_IsoMu24, 3 >= 1 tag, 4 >= 1 pair
    cutflow_ = g.Book1D("cutflow", 5, 0., 5.);
    nTagsH_ = g.Book1D("nTags", 10, 0., 10.);
    nProbesH_ = g.Book1D("nProbeCandidates", 10, 0., 10.);
    nPairsH_ = g.Book1D("nPairs", 10, 0., 10.);
}

void MuonTnPProducer::executeEvent() {
    cutflow_.Fill(0.);
    Event ev = GetEvent();
    const auto jets = GetAllJetViews();
    if (!PassEventFilters(jets, ev)) return;
    cutflow_.Fill(1.);
    const bool hltIsoMu24 = static_cast<bool>(HLT_IsoMu24);
    if (!hltIsoMu24) return;
    cutflow_.Fill(2.);

    const auto muons = GetAllMuonViews();
    const std::size_t n = muons.size();
    if (n < 2) return;
    const auto tos = GetAllTrigObjViews();

    // Tag and probe candidates (raw muon indices).
    std::vector<char> isTagCand(n, 0), isProbe(n, 0);
    std::vector<TrigMatch> tm(n);
    // Preselection passes if the raw (MiniAOD) or the scale/smear-corrected pT passes,
    // so the measurement can bin and cut on either (both are stored).
    std::vector<float> ptRaw(n), ptPre(n);
    for (std::size_t i = 0; i < n; ++i) {
        const auto m = muons[i];
        ptRaw[i] = m.MiniAODPt();
        ptPre[i] = std::max(ptRaw[i], static_cast<float>(m.Pt()));
        const bool kin = std::fabs(m.Eta()) < kEta && std::fabs(m.dXY()) < kDxy &&
                         std::fabs(m.dZ()) < kDz;
        if (!kin) continue;
        if (ptPre[i] > kProbePt && static_cast<bool>(Muon_isTracker[i])) isProbe[i] = 1;
        if (ptPre[i] > kTagPt && m.isPOGTightId() && m.PfRelIso04() < kTagIsoMax) {
            tm[i] = MatchTrigObjs(tos, m.Eta(), m.Phi(), 13);
            if (HasBit(tos, tm[i], kBit1mu, 24.f)) isTagCand[i] = 1;
        }
    }
    int nTag = 0, nProbe = 0;
    for (std::size_t i = 0; i < n; ++i) { nTag += isTagCand[i]; nProbe += isProbe[i]; }
    nTagsH_.Fill(nTag);
    nProbesH_.Fill(nProbe);
    if (nTag == 0) return;
    cutflow_.Fill(3.);

    auto p4raw = [&](std::size_t i) {
        TLorentzVector v;
        v.SetPtEtaPhiM(ptRaw[i], muons[i].Eta(), muons[i].Phi(), kMuonMass);
        return v;
    };
    auto p4cor = [&](std::size_t i) {
        TLorentzVector v;
        v.SetPtEtaPhiM(muons[i].Pt(), muons[i].Eta(), muons[i].Phi(), kMuonMass);
        return v;
    };
    auto inWindow = [](float m) { return m > kMassLow && m < kMassHigh; };
    // Pairs in the window (raw or corrected mass): (tag, probe).
    std::vector<std::pair<std::size_t, std::size_t>> pairs;
    for (std::size_t i = 0; i < n; ++i) {
        if (!isTagCand[i]) continue;
        for (std::size_t j = 0; j < n; ++j) {
            if (j == i || !isProbe[j]) continue;
            if (muons[i].Charge() + muons[j].Charge() != 0) continue;
            if (!inWindow((p4raw(i) + p4raw(j)).M()) && !inWindow((p4cor(i) + p4cor(j)).M())) continue;
            pairs.emplace_back(i, j);
        }
    }
    nPairsH_.Fill(pairs.size());
    if (pairs.empty()) return;
    cutflow_.Fill(4.);

    // Per-tag probe multiplicity and per-probe tag counts (tag iso choices).
    std::vector<unsigned int> mult(n, 0);
    std::vector<int> nT01(n, 0), nT02(n, 0), nT03(n, 0);
    for (const auto &p : pairs) {
        ++mult[p.first];
        const float iso = muons[p.first].PfRelIso04();
        if (iso < 0.1f) ++nT01[p.second];
        if (iso < kTagIsoNominal) ++nT02[p.second];
        if (iso < 0.3f) ++nT03[p.second];
    }

    EvaluateMuonIDs(muons, muBits_);

    // Event-level quantities.
    auto &r = r_;
    r.run = RunNumber;
    r.lumi = luminosityBlock;
    r.event = event;
    r.nPV = PV_npvs;
    r.nPVsGood = PV_npvsGood;
    r.rho = Rho_fixedGridRhoFastjetAll;
    r.puppiMET_pt = PuppiMET_pt;
    r.puppiMET_phi = PuppiMET_phi;

    // Gen matching (MC): prompt status-1 muons, leading first.
    std::vector<int> genOf(n, -1);
    GenViewCollection gens;
    if (!IsDATA) {
        r.nTrueInt = ev.nTrueInt();
        r.genWeight = genWeight;
        r.PUweight = myCorr->GetPUWeight(ev.nTrueInt(), V::nom);
        r.PUweight_up = myCorr->GetPUWeight(ev.nTrueInt(), V::up);
        r.PUweight_down = myCorr->GetPUWeight(ev.nTrueInt(), V::down);
        r.weight = r.genWeight * r.PUweight * wNorm_;

        gens = GetAllGenViews();
        std::vector<std::size_t> gl;
        for (std::size_t k = 0; k < gens.size(); ++k) {
            const auto g = gens[k];
            if (std::abs(g.PdgId()) != 13 || g.Status() != 1 || !g.isPrompt()) continue;
            gl.push_back(k);
        }
        std::sort(gl.begin(), gl.end(),
                  [&](std::size_t a, std::size_t b) { return gens[a].Pt() > gens[b].Pt(); });
        for (const auto k : gl) {
            const auto g = gens[k];
            float best = 1e9f;
            int bi = -1;
            for (std::size_t i = 0; i < n; ++i) {
                if (genOf[i] >= 0) continue;
                if (!(DeltaR(g.Eta(), g.Phi(), muons[i].Eta(), muons[i].Phi()) < kGenDR)) continue;
                const float d = std::fabs((ptRaw[i] - g.Pt()) / g.Pt());
                if (d < best) { best = d; bi = static_cast<int>(i); }
            }
            if (bi >= 0) genOf[bi] = static_cast<int>(k);
        }
    }

    for (const auto &p : pairs) {
        const std::size_t it = p.first, ip = p.second;
        const auto tag = muons[it];
        const auto probe = muons[ip];

        r.tag_IsoMu24 = true; // tag candidates are matched by construction
        r.tag_isTight = tag.isPOGTightId();
        r.tag_isMedium = tag.isPOGMediumId();
        r.tag_isLoose = tag.isPOGLooseId();
        r.tag_pt = ptRaw[it];
        r.tag_pt_cor = tag.Pt();
        r.tag_eta = tag.Eta();
        r.tag_phi = tag.Phi();
        r.tag_q = tag.Charge();
        r.tag_pfRelIso03 = tag.PfRelIso03();
        r.tag_pfRelIso04 = tag.PfRelIso04();
        r.tag_tkRelIso = tag.TkRelIso();
        r.tag_miniPFRelIso = tag.MiniPFRelIso();
        r.tag_sip3d = tag.SIP3D();
        r.tag_dz = tag.dZ();
        r.tag_dxy = tag.dXY();

        r.probe_isTracker = static_cast<bool>(Muon_isTracker[ip]);
        r.probe_isGlobal = static_cast<bool>(Muon_isGlobal[ip]);
        r.probe_isSA = static_cast<bool>(Muon_isStandalone[ip]);
        r.probe_isPF = static_cast<bool>(Muon_isPFcand[ip]);
        r.probe_isTight = probe.isPOGTightId();
        r.probe_isMedium = probe.isPOGMediumId();
        r.probe_isLoose = probe.isPOGLooseId();
        r.probe_TkIsoLoose = probe.PassID(LeptonID::MuonID::POG_TKISO_LOOSE);
        r.probe_PFIsoTight = probe.PassID(LeptonID::MuonID::POG_PFISO_TIGHT);
        r.probe_isHcToWALoose = muBits_[ip] & kLoose;
        r.probe_isHcToWATight = muBits_[ip] & kTight;
        const TrigMatch ptm = MatchTrigObjs(tos, probe.Eta(), probe.Phi(), 13);
        r.probe_IsoMu24 = HasBit(tos, ptm, kBit1mu, 24.f);
        r.probe_Mu17Leg1 = HasBit(tos, ptm, kBit2mu, 17.f);
        r.probe_Mu8Leg2 = HasBit(tos, ptm, kBit2mu, 8.f);
        r.probe_Mu23EMuLeg = HasBit(tos, ptm, kBit1mu1e, 23.f);
        r.probe_Mu8EMuLeg = HasBit(tos, ptm, kBit1mu1e, 8.f);
        if (ptm.best != static_cast<std::size_t>(-1)) {
            r.probe_trigBits = tos[ptm.best].FilterBits();
            r.probe_trigPt = tos[ptm.best].Pt();
        } else {
            r.probe_trigBits = 0;
            r.probe_trigPt = -1.f;
        }
        r.probe_nTagsIso0p1 = nT01[ip];
        r.probe_nTagsIso0p2 = nT02[ip];
        r.probe_nTagsIso0p3 = nT03[ip];
        r.probe_isDuplicated = nT02[ip] > 1;
        r.probe_pt = ptRaw[ip];
        r.probe_pt_cor = probe.Pt();
        r.probe_eta = probe.Eta();
        r.probe_phi = probe.Phi();
        r.probe_q = probe.Charge();
        r.probe_pfRelIso03 = probe.PfRelIso03();
        r.probe_pfRelIso04 = probe.PfRelIso04();
        r.probe_tkRelIso = probe.TkRelIso();
        r.probe_miniPFRelIso = probe.MiniPFRelIso();
        r.probe_sip3d = probe.SIP3D();
        r.probe_dz = probe.dZ();
        r.probe_dxy = probe.dXY();

        const TLorentzVector pr = p4raw(it) + p4raw(ip);
        TLorentzVector tc, pc;
        tc.SetPtEtaPhiM(tag.Pt(), tag.Eta(), tag.Phi(), kMuonMass);
        pc.SetPtEtaPhiM(probe.Pt(), probe.Eta(), probe.Phi(), kMuonMass);
        r.pair_probeMultiplicity = mult[it];
        r.pair_mass = pr.M();
        r.pair_mass_cor = (tc + pc).M();
        r.pair_pt = pr.Pt();
        r.pair_dr = DeltaR(tag.Eta(), tag.Phi(), probe.Eta(), probe.Phi());
        r.pair_EMTF = r.tag_eta * r.probe_eta > 0 && std::fabs(r.tag_eta) > 0.9f &&
                      std::fabs(r.probe_eta) > 0.9f &&
                      std::fabs(DeltaPhi(r.tag_phi, r.probe_phi)) < 70.f / 180.f * static_cast<float>(M_PI);

        if (!IsDATA) {
            auto fillGen = [&](int k, std::size_t i, bool &matched, float &pt, float &eta,
                               float &phi, float &dR, float &reldpt) {
                matched = k >= 0;
                if (!matched) { pt = eta = phi = dR = reldpt = -999.f; return; }
                const auto g = gens[k];
                pt = g.Pt(); eta = g.Eta(); phi = g.Phi();
                dR = DeltaR(g.Eta(), g.Phi(), muons[i].Eta(), muons[i].Phi());
                reldpt = (ptRaw[i] - g.Pt()) / g.Pt();
            };
            fillGen(genOf[it], it, r.tag_gen_matched, r.tag_gen_pt, r.tag_gen_eta, r.tag_gen_phi,
                    r.tag_gen_dR, r.tag_gen_reldpt);
            fillGen(genOf[ip], ip, r.probe_gen_matched, r.probe_gen_pt, r.probe_gen_eta,
                    r.probe_gen_phi, r.probe_gen_dR, r.probe_gen_reldpt);
            r.pair_gen_matched = r.tag_gen_matched && r.probe_gen_matched;
            if (r.pair_gen_matched) {
                const auto g1 = gens[genOf[it]], g2 = gens[genOf[ip]];
                TLorentzVector a, b;
                a.SetPtEtaPhiM(g1.Pt(), g1.Eta(), g1.Phi(), g1.Mass());
                b.SetPtEtaPhiM(g2.Pt(), g2.Eta(), g2.Phi(), g2.Mass());
                r.pair_gen_mass = (a + b).M();
            } else {
                r.pair_gen_mass = -999.f;
            }
        }
        out_.Fill();
    }
}
