#include <HcToWA/ElectronTnPProducer.h>

#include <algorithm>
#include <cmath>
#include <iostream>

namespace {

using V = MyCorrection::variation;
constexpr float kElectronMass = 0.000511f;

// NanoAOD v15 (CMSSW_15_0_X PhysicsTools/NanoAOD/python/triggerObjects_cff.py)
// TrigObj id 11 qualityBits: 1 "hltEle*WPTight*TrackIsoFilter*",
// 6 "hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*" (1e-1mu),
// 12 "hltEle*CaloIdVTGsfTrkIdTGsfDphiFilter" (CaloIdVT_GsfTrkIdT),
// 14 "hltEG175HEFilter OR hltEG200HEFilter"; id 22 bit 7 "hltEG200HEFilter".
constexpr ULong64_t kEleWPTight = 1ull << 1;
constexpr ULong64_t kEle1e1mu = 1ull << 6;
constexpr ULong64_t kEleCaloIdVT = 1ull << 12;
constexpr ULong64_t kElePhoton175or200 = 1ull << 14;
constexpr ULong64_t kPhoEG200 = 1ull << 7;

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

struct TrigMatch {
    std::vector<std::size_t> idx; // e/gamma TrigObj (id 11 or 22) within dR
    std::size_t best = static_cast<std::size_t>(-1); // closest id 11 object
};
TrigMatch MatchTrigObjs(const TrigObjViewCollection &tos, float eta, float phi) {
    TrigMatch m;
    float bestDR = ElectronTnPProducer::kTrigDR;
    for (std::size_t k = 0; k < tos.size(); ++k) {
        const auto t = tos[k];
        const int id = t.Id();
        if (id != 11 && id != 22) continue;
        const float dr = DeltaR(eta, phi, t.Eta(), t.Phi());
        if (!(dr < ElectronTnPProducer::kTrigDR)) continue;
        m.idx.push_back(k);
        if (id == 11 && dr < bestDR) { bestDR = dr; m.best = k; }
    }
    return m;
}
bool HasBit(const TrigObjViewCollection &tos, const TrigMatch &m, int id, ULong64_t bit,
            float minPt) {
    for (const auto k : m.idx) {
        const auto t = tos[k];
        if (t.Id() == id && (t.FilterBits() & bit) && t.Pt() > minPt) return true;
    }
    return false;
}

} // namespace

ElectronTnPProducer::ElectronTnPProducer() {}
ElectronTnPProducer::~ElectronTnPProducer() {}

void ElectronTnPProducer::initializeAnalyzer() {
    HcToWABase::initializeAnalyzer();
    if (!IsDATA) wNorm_ = (sumW != 0.f) ? sumSign / sumW : 1.f;
    cout << "[ElectronTnPProducer] weight normalisation sumSign/sumW = " << wNorm_ << endl;

    out_ = Output().Book("electron/Events");
    auto &r = r_;
    out_.Field("run", r.run).Field("lumi", r.lumi).Field("event", r.event)
        .Field("nPV", r.nPV).Field("nPVsGood", r.nPVsGood).Field("rho", r.rho)
        .Field("PuppiMET_pt", r.puppiMET_pt).Field("PuppiMET_phi", r.puppiMET_phi);
    if (!IsDATA) {
        out_.Field("nTrueInt", r.nTrueInt).Field("genWeight", r.genWeight)
            .Field("PUweight", r.PUweight).Field("PUweight_up", r.PUweight_up)
            .Field("PUweight_down", r.PUweight_down).Field("weight", r.weight);
    }
    out_.Field("tag_passEle32", r.tag_passEle32).Field("tag_passEle115", r.tag_passEle115)
        .Field("tag_passPhoton200", r.tag_passPhoton200).Field("tag_trig", r.tag_trig)
        .Field("tag_isMVANoIsoWP90", r.tag_isMVANoIsoWP90).Field("tag_cutBased", r.tag_cutBased)
        .Field("tag_q", r.tag_q).Field("tag_pt", r.tag_pt).Field("tag_pt_cor", r.tag_pt_cor)
        .Field("tag_eta", r.tag_eta).Field("tag_phi", r.tag_phi).Field("tag_sc_eta", r.tag_sc_eta)
        .Field("tag_miniPFRelIso", r.tag_miniPFRelIso).Field("tag_pfRelIso03", r.tag_pfRelIso03);
    out_.Field("probe_q", r.probe_q).Field("probe_cutBased", r.probe_cutBased)
        .Field("probe_lostHits", r.probe_lostHits).Field("probe_convVeto", r.probe_convVeto)
        .Field("probe_isMVANoIsoWP90", r.probe_isMVANoIsoWP90)
        .Field("probe_isMVANoIsoWP80", r.probe_isMVANoIsoWP80)
        .Field("probe_isMVAIsoWP90", r.probe_isMVAIsoWP90)
        .Field("probe_isMVAIsoWP80", r.probe_isMVAIsoWP80)
        .Field("probe_passTrigEmu", r.probe_passTrigEmu)
        .Field("probe_isHcToWALoose", r.probe_isHcToWALoose)
        .Field("probe_isHcToWATight", r.probe_isHcToWATight)
        .Field("probe_Ele23EMuLeg", r.probe_Ele23EMuLeg).Field("probe_Ele12EMuLeg", r.probe_Ele12EMuLeg)
        .Field("probe_Ele32", r.probe_Ele32)
        .Field("probe_trigBits", r.probe_trigBits).Field("probe_trigPt", r.probe_trigPt)
        .Field("probe_pt", r.probe_pt).Field("probe_pt_cor", r.probe_pt_cor)
        .Field("probe_eta", r.probe_eta).Field("probe_phi", r.probe_phi)
        .Field("probe_sc_eta", r.probe_sc_eta).Field("probe_sc_abseta", r.probe_sc_abseta)
        .Field("probe_mvaNoIso", r.probe_mvaNoIso).Field("probe_mvaIso", r.probe_mvaIso)
        .Field("probe_miniPFRelIso", r.probe_miniPFRelIso).Field("probe_pfRelIso03", r.probe_pfRelIso03)
        .Field("probe_sip3d", r.probe_sip3d).Field("probe_dz", r.probe_dz).Field("probe_dxy", r.probe_dxy)
        .Field("probe_sieie", r.probe_sieie).Field("probe_hoe", r.probe_hoe)
        .Field("probe_dEtaInSC", r.probe_dEtaInSC).Field("probe_dPhiInSeed", r.probe_dPhiInSeed)
        .Field("probe_ecalPFClusIso", r.probe_ecalPFClusIso)
        .Field("probe_hcalPFClusIso", r.probe_hcalPFClusIso)
        .Field("probe_dr03TkSumPt", r.probe_dr03TkSumPt);
    out_.Field("pair_probeMultiplicity", r.pair_probeMultiplicity)
        .Field("pair_mass", r.pair_mass).Field("pair_mass_cor", r.pair_mass_cor)
        .Field("pair_pt", r.pair_pt).Field("pair_dr", r.pair_dr);
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
    // 0 all, 1 event filters, 2 HLT OR, 3 >= 1 tag, 4 >= 1 pair
    cutflow_ = g.Book1D("cutflow", 5, 0., 5.);
    nTagsH_ = g.Book1D("nTags", 10, 0., 10.);
    nProbesH_ = g.Book1D("nProbeCandidates", 10, 0., 10.);
    nPairsH_ = g.Book1D("nPairs", 10, 0., 10.);
}

void ElectronTnPProducer::executeEvent() {
    cutflow_.Fill(0.);
    Event ev = GetEvent();
    const auto jets = GetAllJetViews();
    if (!PassEventFilters(jets, ev)) return;
    cutflow_.Fill(1.);
    const bool hEle32 = static_cast<bool>(HLT_Ele32_WPTight_Gsf);
    const bool hEle115 = static_cast<bool>(HLT_Ele115_CaloIdVT_GsfTrkIdT);
    const bool hPho200 = static_cast<bool>(HLT_Photon200);
    if (!(hEle32 || hEle115 || hPho200)) return;
    cutflow_.Fill(2.);

    const auto electrons = GetAllElectronViews();
    const std::size_t n = electrons.size();
    if (n < 2) return;
    const auto tos = GetAllTrigObjViews();

    std::vector<char> isTag(n, 0), isProbe(n, 0);
    std::vector<TrigMatch> tm(n);
    // Preselection passes if the raw (MiniAOD) or the scale/smear-corrected pT passes,
    // so the measurement can bin and cut on either (both are stored).
    std::vector<float> ptRaw(n), ptPre(n), scEta(n);
    std::vector<char> pEle32(n, 0), pEle115(n, 0), pPho200(n, 0);
    for (std::size_t i = 0; i < n; ++i) {
        const auto e = electrons[i];
        ptRaw[i] = e.MiniAODPt();
        ptPre[i] = std::max(ptRaw[i], static_cast<float>(e.Pt()));
        scEta[i] = e.ScEta();
        if (!(std::fabs(scEta[i]) < kEta)) continue;
        if (ptPre[i] > kProbePt) isProbe[i] = 1;
        if (ptPre[i] > kTagPt && e.CutBased() == LeptonID::ElectronCutBasedWP::TIGHT) {
            tm[i] = MatchTrigObjs(tos, e.Eta(), e.Phi());
            pEle32[i] = hEle32 && HasBit(tos, tm[i], 11, kEleWPTight, 32.f);
            pEle115[i] = hEle115 && HasBit(tos, tm[i], 11, kEleCaloIdVT, 115.f);
            pPho200[i] = hPho200 && (HasBit(tos, tm[i], 11, kElePhoton175or200, 200.f) ||
                                     HasBit(tos, tm[i], 22, kPhoEG200, 200.f));
            if (pEle32[i] || pEle115[i] || pPho200[i]) isTag[i] = 1;
        }
    }
    int nTag = 0, nProbe = 0;
    for (std::size_t i = 0; i < n; ++i) { nTag += isTag[i]; nProbe += isProbe[i]; }
    nTagsH_.Fill(nTag);
    nProbesH_.Fill(nProbe);
    if (nTag == 0) return;
    cutflow_.Fill(3.);

    auto p4raw = [&](std::size_t i) {
        TLorentzVector v;
        v.SetPtEtaPhiM(ptRaw[i], electrons[i].Eta(), electrons[i].Phi(), kElectronMass);
        return v;
    };
    auto p4cor = [&](std::size_t i) {
        TLorentzVector v;
        v.SetPtEtaPhiM(electrons[i].Pt(), electrons[i].Eta(), electrons[i].Phi(), kElectronMass);
        return v;
    };
    auto inWindow = [](float m) { return m > kMassLow && m < kMassHigh; };
    std::vector<std::pair<std::size_t, std::size_t>> pairs;
    for (std::size_t i = 0; i < n; ++i) {
        if (!isTag[i]) continue;
        for (std::size_t j = 0; j < n; ++j) {
            if (j == i || !isProbe[j]) continue;
            if (electrons[i].Charge() + electrons[j].Charge() != 0) continue;
            if (!(DeltaR(electrons[i].Eta(), electrons[i].Phi(), electrons[j].Eta(),
                         electrons[j].Phi()) > kMinDR)) continue;
            if (!inWindow((p4raw(i) + p4raw(j)).M()) && !inWindow((p4cor(i) + p4cor(j)).M())) continue;
            pairs.emplace_back(i, j);
        }
    }
    nPairsH_.Fill(pairs.size());
    if (pairs.empty()) return;
    cutflow_.Fill(4.);
    std::vector<unsigned int> mult(n, 0);
    for (const auto &p : pairs) ++mult[p.first];

    auto &r = r_;
    r.rho = Rho_fixedGridRhoFastjetAll;
    EvaluateElectronIDs(electrons, r.rho, elBits_);

    r.run = RunNumber;
    r.lumi = luminosityBlock;
    r.event = event;
    r.nPV = PV_npvs;
    r.nPVsGood = PV_npvsGood;
    r.puppiMET_pt = PuppiMET_pt;
    r.puppiMET_phi = PuppiMET_phi;

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
            if (std::abs(g.PdgId()) != 11 || g.Status() != 1 || !g.isPrompt()) continue;
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
                if (!(DeltaR(g.Eta(), g.Phi(), electrons[i].Eta(), electrons[i].Phi()) < kGenDR)) continue;
                const float d = std::fabs((ptRaw[i] - g.Pt()) / g.Pt());
                if (d < best) { best = d; bi = static_cast<int>(i); }
            }
            if (bi >= 0) genOf[bi] = static_cast<int>(k);
        }
    }

    for (const auto &p : pairs) {
        const std::size_t it = p.first, ip = p.second;
        const auto tag = electrons[it];
        const auto probe = electrons[ip];

        r.tag_passEle32 = pEle32[it];
        r.tag_passEle115 = pEle115[it];
        r.tag_passPhoton200 = pPho200[it];
        r.tag_trig = true;
        r.tag_isMVANoIsoWP90 = tag.isMVANoIsoWP90();
        r.tag_cutBased = static_cast<int>(tag.CutBased());
        r.tag_q = tag.Charge();
        r.tag_pt = ptRaw[it];
        r.tag_pt_cor = tag.Pt();
        r.tag_eta = tag.Eta();
        r.tag_phi = tag.Phi();
        r.tag_sc_eta = scEta[it];
        r.tag_miniPFRelIso = tag.MiniPFRelIso();
        r.tag_pfRelIso03 = tag.PfRelIso03();

        r.probe_q = probe.Charge();
        r.probe_cutBased = static_cast<int>(probe.CutBased());
        r.probe_lostHits = probe.LostHits();
        r.probe_convVeto = probe.ConvVeto();
        r.probe_isMVANoIsoWP90 = probe.isMVANoIsoWP90();
        r.probe_isMVANoIsoWP80 = probe.isMVANoIsoWP80();
        r.probe_isMVAIsoWP90 = probe.isMVAIsoWP90();
        r.probe_isMVAIsoWP80 = probe.isMVAIsoWP80();
        r.probe_passTrigEmu = PassElectronTriggerEmulation(probe, ip, r.rho);
        r.probe_isHcToWALoose = elBits_[ip] & kLoose;
        r.probe_isHcToWATight = elBits_[ip] & kTight;
        const TrigMatch ptm = MatchTrigObjs(tos, probe.Eta(), probe.Phi());
        r.probe_Ele23EMuLeg = HasBit(tos, ptm, 11, kEle1e1mu, 23.f);
        r.probe_Ele12EMuLeg = HasBit(tos, ptm, 11, kEle1e1mu, 12.f);
        r.probe_Ele32 = HasBit(tos, ptm, 11, kEleWPTight, 32.f);
        if (ptm.best != static_cast<std::size_t>(-1)) {
            r.probe_trigBits = tos[ptm.best].FilterBits();
            r.probe_trigPt = tos[ptm.best].Pt();
        } else {
            r.probe_trigBits = 0;
            r.probe_trigPt = -1.f;
        }
        r.probe_pt = ptRaw[ip];
        r.probe_pt_cor = probe.Pt();
        r.probe_eta = probe.Eta();
        r.probe_phi = probe.Phi();
        r.probe_sc_eta = scEta[ip];
        r.probe_sc_abseta = std::fabs(scEta[ip]);
        r.probe_mvaNoIso = probe.MvaNoIso();
        r.probe_mvaIso = probe.MvaIso();
        r.probe_miniPFRelIso = probe.MiniPFRelIso();
        r.probe_pfRelIso03 = probe.PfRelIso03();
        r.probe_sip3d = probe.SIP3D();
        r.probe_dz = probe.dZ();
        r.probe_dxy = probe.dXY();
        r.probe_sieie = probe.sieie();
        r.probe_hoe = probe.hoe();
        r.probe_dEtaInSC = (*elCols).deltaEtaInSC[ip];
        r.probe_dPhiInSeed = (*elCols).deltaPhiInSeed[ip];
        r.probe_ecalPFClusIso = (*elCols).ecalPFClusIso[ip];
        r.probe_hcalPFClusIso = (*elCols).hcalPFClusIso[ip];
        r.probe_dr03TkSumPt = probe.dr03TkSumPt();

        const TLorentzVector pr = p4raw(it) + p4raw(ip);
        TLorentzVector tc, pc;
        tc.SetPtEtaPhiM(tag.Pt(), tag.Eta(), tag.Phi(), kElectronMass);
        pc.SetPtEtaPhiM(probe.Pt(), probe.Eta(), probe.Phi(), kElectronMass);
        r.pair_probeMultiplicity = mult[it];
        r.pair_mass = pr.M();
        r.pair_mass_cor = (tc + pc).M();
        r.pair_pt = pr.Pt();
        r.pair_dr = DeltaR(tag.Eta(), tag.Phi(), probe.Eta(), probe.Phi());

        if (!IsDATA) {
            auto fillGen = [&](int k, std::size_t i, bool &matched, float &pt, float &eta,
                               float &phi, float &dR, float &reldpt) {
                matched = k >= 0;
                if (!matched) { pt = eta = phi = dR = reldpt = -999.f; return; }
                const auto g = gens[k];
                pt = g.Pt(); eta = g.Eta(); phi = g.Phi();
                dR = DeltaR(g.Eta(), g.Phi(), electrons[i].Eta(), electrons[i].Phi());
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
