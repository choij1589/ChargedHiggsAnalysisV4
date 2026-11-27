#include <HcToWA/ClosFakeRate.h>

#include <TLorentzVector.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <iostream>

namespace {

using V = MyCorrection::variation;

const char *kChName[ClosFakeRate::kNCh] = {"1E2MU", "3MU", "3MU_onZ", "3MU_offZ"};
// rate sets of fakerate_HcToWA.json (MeasFakeRate/python/makeFakeRateJson.py)
const std::vector<std::string> kKeys = {"MC_QCD", "MC_TT", "Central", "Stat_Up", "Stat_Down",
                                        "PromptNorm_Up", "PromptNorm_Down", "AwayJet_Up", "AwayJet_Down",
                                        "BTag", "Total_Up", "Total_Down"};

TLorentzVector P4(float pt, float eta, float phi, float m) {
    TLorentzVector v;
    v.SetPtEtaPhiM(pt, eta, phi, m);
    return v;
}
float PtCorr(float pt, float miniIso) { return pt * (1.f + std::max(0.f, miniIso - 0.1f)); }

} // namespace

ClosFakeRate::ClosFakeRate() {}
ClosFakeRate::~ClosFakeRate() {}

void ClosFakeRate::Book(VarHists &vh, const std::string &dir) {
    auto g = Hists(dir);
    vh.h[kPairMass] = g.Book1D("pair_mass", 200, 0., 200.);
    vh.h[kPairLowM] = g.Book1D("pair_lowM_mass", 200, 0., 200.);
    vh.h[kPairHighM] = g.Book1D("pair_highM_mass", 300, 0., 300.);
    vh.h[kMu1Pt] = g.Book1D("muons_1_pt", 60, 0., 300.);
    vh.h[kMu2Pt] = g.Book1D("muons_2_pt", 60, 0., 300.);
    vh.h[kMu3Pt] = g.Book1D("muons_3_pt", 60, 0., 300.);
    vh.h[kElPt] = g.Book1D("electrons_1_pt", 60, 0., 300.);
    vh.h[kElScEta] = g.Book1D("electrons_1_scEta", 50, -2.5, 2.5);
    vh.h[kNJets] = g.Book1D("jets_size", 15, 0., 15.);
    vh.h[kNBJets] = g.Book1D("bjets_size", 10, 0., 10.);
    vh.h[kMET] = g.Book1D("METv_pt", 60, 0., 300.);
}

void ClosFakeRate::Fill(VarHists &vh, const Vals &x, float w) {
    for (int k = 0; k < kNVar; ++k)
        if (x.has[k]) vh.h[k].Fill(x.v[k], w);
}

void ClosFakeRate::initializeAnalyzer() {
    HcToWABase::initializeAnalyzer();
    run1E2Mu_ = HasFlag("Run1E2Mu");
    run3Mu_ = HasFlag("Run3Mu");
    if (!run1E2Mu_ && !run3Mu_) throw SKNano::ConfigError("[ClosFakeRate] no channel flag (Run1E2Mu, Run3Mu)");
    if (IsDATA) throw SKNano::ConfigError("[ClosFakeRate] MC closure only");

    const char *home = std::getenv("SKNANO_HOME");
    if (!home) throw SKNano::ConfigError("[ClosFakeRate] SKNANO_HOME not set");
    std::string path;
    for (const char *sub : {"/analysis_modules/HcToWA_Analyzers", "/HcToWA_Analyzers"}) {
        const std::string candidate = std::string(home) + sub + "/data/2024/FakeRate/fakerate_HcToWA.json";
        if (FILE *fp = std::fopen(candidate.c_str(), "r")) {
            std::fclose(fp);
            path = candidate;
            break;
        }
    }
    if (path.empty()) throw SKNano::ConfigError("[ClosFakeRate] data/2024/FakeRate/fakerate_HcToWA.json not found");
    frSet_ = correction::CorrectionSet::from_file(path);
    frMu_ = frSet_->at("FakeRate_Muon");
    frEl_ = frSet_->at("FakeRate_Electron");
    keys_ = kKeys;
    cout << "[ClosFakeRate] rates from " << path << "; 1E2Mu " << run1E2Mu_ << ", 3Mu " << run3Mu_ << endl;

    for (int ch = 0; ch < kNCh; ++ch) {
        if ((ch == k1E2Mu && !run1E2Mu_) || (ch != k1E2Mu && !run3Mu_)) continue;
        const std::string c = kChName[ch];
        cutflow_[ch] = Hists(c).Book1D("cutflow", 10, 0., 10.);
        Book(hSR_[ch], c + "/SR/Observed");
        Book(hSRAllPrompt_[ch], c + "/SR_genAllPrompt/Observed");
        Book(hSBPromptLNT_[ch], c + "/SB_genPromptLNT/MC_QCD");
        Book(hSBNonpromptLNT_[ch], c + "/SB_genNonpromptLNT/MC_QCD");
        hSB_[ch].resize(keys_.size());
        for (std::size_t k = 0; k < keys_.size(); ++k) Book(hSB_[ch][k], c + "/SB/" + keys_[k]);
    }
}

float ClosFakeRate::Rate(bool muon, float absEta, float ptcorr, const std::string &key) const {
    const auto &c = muon ? frMu_ : frEl_;
    return static_cast<float>(c->evaluate({static_cast<double>(absEta), static_cast<double>(ptcorr), key}));
}

void ClosFakeRate::executeEvent() {
    Event ev = GetEvent();
    if (lumi_ < 0.f) lumi_ = ev.GetTriggerLumi("Full");
    const float w0 = MCweight() * lumi_;
    auto cut = [&](int ch, int bin, float w) { cutflow_[ch].Fill(bin, w); };
    const bool any3 = run3Mu_;

    jets_ = GetAllJetViews();
    if (!PassEventFilters(jets_, ev)) return;
    if (!PassJetVetoMap(jets_, "jetvetomap")) return;

    muons_ = GetAllMuonViews();
    electrons_ = GetAllElectronViews();
    EvaluateMuonIDs(muons_, muBits_);
    EvaluateElectronIDs(electrons_, Rho_fixedGridRhoFastjetAll, elBits_);

    std::vector<std::size_t> mu, elVeto, el;
    for (std::size_t i = 0; i < muBits_.size(); ++i)
        if ((muBits_[i] & kLoose) && std::fabs(muons_[i].Eta()) < 2.4f && muons_[i].Pt() > 10.f) mu.push_back(i);
    for (std::size_t i = 0; i < elBits_.size(); ++i)
        if ((elBits_[i] & kLoose) && std::fabs(electrons_[i].Eta()) < 2.5f && electrons_[i].Pt() > 10.f) {
            elVeto.push_back(i);
            if (electrons_[i].Pt() > 15.f) el.push_back(i);
        }
    std::sort(mu.begin(), mu.end(), [&](std::size_t a, std::size_t b) { return muons_[a].Pt() > muons_[b].Pt(); });
    std::sort(el.begin(), el.end(), [&](std::size_t a, std::size_t b) { return electrons_[a].Pt() > electrons_[b].Pt(); });

    const bool is1E2Mu = run1E2Mu_ && mu.size() == 2 && elVeto.size() == 1 && el.size() == 1;
    const bool is3Mu = any3 && mu.size() == 3 && elVeto.empty();
    if (is1E2Mu) cut(k1E2Mu, 0, w0);
    if (is3Mu) cut(k3Mu, 0, w0);
    if (!is1E2Mu && !is3Mu) return;

    int ch = -1;
    if (is1E2Mu) {
        if (!ev.PassTrigger(RVec<TString>{"HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
                                          "HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ"})) return;
        cut(k1E2Mu, 1, w0);
        const float pm1 = muons_[mu[0]].Pt(), pe = electrons_[el[0]].Pt();
        if (!((pm1 > 25.f && pe > 15.f) || (pm1 > 10.f && pe > 25.f))) return;
        cut(k1E2Mu, 2, w0);
        ch = k1E2Mu;
    } else {
        if (!ev.PassTrigger(TString("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8"))) return;
        cut(k3Mu, 1, w0);
        if (!(muons_[mu[0]].Pt() > 20.f && muons_[mu[1]].Pt() > 10.f && muons_[mu[2]].Pt() > 10.f)) return;
        cut(k3Mu, 2, w0);
        ch = k3Mu;
    }

    // pT_corr-scaled four-vectors (after the trigger-safe cuts, as B2G-25-013)
    std::vector<TLorentzVector> pm, pe;
    for (auto i : mu) {
        const auto m = muons_[i];
        pm.push_back(P4(PtCorr(m.Pt(), m.MiniPFRelIso()), m.Eta(), m.Phi(), m.M()));
    }
    for (auto i : el) {
        const auto e = electrons_[i];
        pe.push_back(P4(PtCorr(e.Pt(), e.MiniPFRelIso()), e.Eta(), e.Phi(), 0.f));
    }

    Vals x{};
    std::fill(std::begin(x.has), std::end(x.has), false);
    bool onZ = false;
    if (ch == k1E2Mu) {
        if (muons_[mu[0]].Charge() + muons_[mu[1]].Charge() != 0) return;
        const float mll = (pm[0] + pm[1]).M();
        if (!(mll > 12.f)) return;
        cut(ch, 3, w0);
        x.v[kPairMass] = mll; x.has[kPairMass] = true;
        x.v[kElPt] = pe[0].Pt(); x.has[kElPt] = true;
        x.v[kElScEta] = electrons_[el[0]].ScEta(); x.has[kElScEta] = true;
    } else {
        const int q = muons_[mu[0]].Charge() + muons_[mu[1]].Charge() + muons_[mu[2]].Charge();
        if (std::abs(q) != 1) return;
        // the odd-charge muon and the two same-sign ones
        int os = -1;
        for (int a = 0; a < 3; ++a)
            if (muons_[mu[a]].Charge() != muons_[mu[(a + 1) % 3]].Charge() &&
                muons_[mu[a]].Charge() != muons_[mu[(a + 2) % 3]].Charge()) os = a;
        const int ss1 = (os + 1) % 3, ss2 = (os + 2) % 3;
        const float m1 = (pm[ss1] + pm[os]).M(), m2 = (pm[ss2] + pm[os]).M();
        if (!(m1 > 12.f && m2 > 12.f)) return;
        cut(ch, 3, w0);
        x.v[kPairLowM] = std::min(m1, m2); x.has[kPairLowM] = true;
        x.v[kPairHighM] = std::max(m1, m2); x.has[kPairHighM] = true;
        onZ = std::fabs(m1 - 91.2f) < 10.f || std::fabs(m2 - 91.2f) < 10.f;
        x.v[kMu3Pt] = pm[2].Pt(); x.has[kMu3Pt] = true;
    }
    x.v[kMu1Pt] = pm[0].Pt(); x.has[kMu1Pt] = true;
    x.v[kMu2Pt] = pm[1].Pt(); x.has[kMu2Pt] = true;

    // jets cleaned from the veto leptons
    auto idx = SelectJetIndices(jets_, JetView::JetID::TIGHT, 20.f, 2.5f);
    idx = RemoveOverlapIndices(jets_, idx, electrons_, elVeto, 0.4f);
    idx = RemoveOverlapIndices(jets_, idx, muons_, mu, 0.4f);
    const auto sj = SelectJetViews(jets_, std::move(idx), V::nom, V::nom);
    int nB = 0;
    for (std::size_t k = 0; k < sj.size(); ++k)
        if (sj[k].GetTaggerResult(JetTagging::JetFlavTagger::ParT, JetTagging::JetFlavTaggerScoreType::B) > bTagWP) ++nB;
    if (!(sj.size() >= 2)) return;
    cut(ch, 4, w0);
    if (!(nB >= 1)) return;
    cut(ch, 5, w0);
    x.v[kNJets] = static_cast<float>(sj.size()); x.has[kNJets] = true;
    x.v[kNBJets] = static_cast<float>(nB); x.has[kNBJets] = true;
    {
        Particle raw = ev.GetMETVector(Event::MET_Type::PUPPI), z1, z2, z3;
        PropagateJetSystToMET(jets_, z1);
        PropagateMuonCorrToMET(muons_, z2);
        PropagateElectronCorrToMET(electrons_, z3);
        x.v[kMET] = static_cast<float>(std::hypot(raw.Px() + z1.Px() + z2.Px() + z3.Px(),
                                                  raw.Py() + z1.Py() + z2.Py() + z3.Py()));
        x.has[kMET] = true;
    }

    const float w = w0 * myCorr->GetPUWeight(ev.nTrueInt(), V::nom);
    // loose-not-tight leptons: (muon?, raw index, pT_corr)
    struct LNT { bool muon; std::size_t i; float ptcorr; };
    std::vector<LNT> lnt;
    bool allPrompt = true;
    for (std::size_t a = 0; a < mu.size(); ++a) {
        const auto m = muons_[mu[a]];
        const int f = m.GenPartFlav();
        if (!(f == 1 || f == 15)) allPrompt = false;
        if (!(muBits_[mu[a]] & kTight)) lnt.push_back({true, mu[a], static_cast<float>(pm[a].Pt())});
    }
    for (std::size_t a = 0; a < el.size(); ++a) {
        const auto e = electrons_[el[a]];
        const int f = e.GenPartFlav();
        if (!(f == 1 || f == 15)) allPrompt = false;
        if (!(elBits_[el[a]] & kTight)) lnt.push_back({false, el[a], static_cast<float>(pe[a].Pt())});
    }
    std::vector<int> chs = {ch};
    if (ch == k3Mu) chs.push_back(onZ ? k3MuOnZ : k3MuOffZ);

    if (lnt.empty()) {
        for (int c : chs) {
            cut(c, 6, w);
            Fill(hSR_[c], x, w);
            if (allPrompt) Fill(hSRAllPrompt_[c], x, w);
        }
        return;
    }
    bool promptLNT = false;
    for (const auto &l : lnt) {
        const int f = l.muon ? muons_[l.i].GenPartFlav() : electrons_[l.i].GenPartFlav();
        if (f == 1 || f == 15) promptLNT = true;
    }
    for (std::size_t k = 0; k < keys_.size(); ++k) {
        float fw = -1.f;
        for (const auto &l : lnt) {
            const float aeta = l.muon ? std::fabs(muons_[l.i].Eta()) : std::fabs(electrons_[l.i].ScEta());
            const float fr = Rate(l.muon, aeta, l.ptcorr, keys_[k]);
            fw *= -fr / (1.f - fr);
        }
        for (int c : chs) {
            Fill(hSB_[c][k], x, w * fw);
            if (k == 0) {
                cut(c, 7, w * fw);
                Fill(promptLNT ? hSBPromptLNT_[c] : hSBNonpromptLNT_[c], x, w * fw);
            }
        }
    }
}
