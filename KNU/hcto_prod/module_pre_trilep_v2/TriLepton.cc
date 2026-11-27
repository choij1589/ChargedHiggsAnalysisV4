#include <HcToWA/TriLepton.h>

#include <TLorentzVector.h>
#include <TVector2.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <iostream>

namespace {

using V = MyCorrection::variation;

const char *kChName[TriLepton::kNCh] = {"1E2MU", "3MU"};
const char *kRegName[TriLepton::kNReg] = {"SR", "ZFake", "ZG", "WZ"};
const char *kLaneName[TriLepton::kNLane] = {"Central", "DYGVeto", "Nonprompt", "Nonprompt_Up",
                                            "Nonprompt_Down"};
// fakerate_HcToWA.json sets of the nonprompt lanes
const char *kLaneKey[TriLepton::kNLane] = {"", "", "Central", "Total_Up", "Total_Down"};
// DYGto2LG generator phase space for the DY overlap removal (C1 (b)): leading prompt status-1
// photon above this pT and this far from the prompt leptons. From the DYG LHE spectra of the step-1
// test (2026-11-27, diag/lhe_photon_pt, diag/lhe_photon_dRl): pT(gamma) > 10 GeV, dR(gamma, l) > 0.1,
// no |eta| cut.
constexpr float kDYGPhoPtMin = 10.f;
constexpr float kDYGPhoDRMin = 0.1f;
constexpr float kMZ = 91.2f;

TLorentzVector P4(float pt, float eta, float phi, float m) {
    TLorentzVector v;
    v.SetPtEtaPhiM(pt, eta, phi, m);
    return v;
}
float PtCorr(float pt, float miniIso) { return pt * (1.f + std::max(0.f, miniIso - 0.1f)); }
float DR(float eta1, float phi1, float eta2, float phi2) {
    const float de = eta1 - eta2;
    const float dp = static_cast<float>(TVector2::Phi_mpi_pi(phi1 - phi2));
    return std::sqrt(de * de + dp * dp);
}

} // namespace

TriLepton::TriLepton() {}
TriLepton::~TriLepton() {}

void TriLepton::Book(VarHists &vh, const std::string &dir) {
    auto g = Hists(dir);
    vh.h[kM3l] = g.Book1D("trilep_mass", 300, 0., 300.);
    vh.h[kPairMass] = g.Book1D("pair_mass", 200, 0., 200.);
    vh.h[kPairLowM] = g.Book1D("pair_lowM_mass", 200, 0., 200.);
    vh.h[kPairHighM] = g.Book1D("pair_highM_mass", 300, 0., 300.);
    vh.h[kMu1Pt] = g.Book1D("muons_1_pt", 60, 0., 300.);
    vh.h[kMu2Pt] = g.Book1D("muons_2_pt", 60, 0., 300.);
    vh.h[kMu3Pt] = g.Book1D("muons_3_pt", 60, 0., 300.);
    vh.h[kMu1Eta] = g.Book1D("muons_1_eta", 48, -2.4, 2.4);
    vh.h[kMu2Eta] = g.Book1D("muons_2_eta", 48, -2.4, 2.4);
    vh.h[kMu3Eta] = g.Book1D("muons_3_eta", 48, -2.4, 2.4);
    vh.h[kElPt] = g.Book1D("electrons_1_pt", 60, 0., 300.);
    vh.h[kElScEta] = g.Book1D("electrons_1_scEta", 50, -2.5, 2.5);
    vh.h[kNJets] = g.Book1D("jets_size", 15, 0., 15.);
    vh.h[kNBJets] = g.Book1D("bjets_size", 10, 0., 10.);
    vh.h[kMET] = g.Book1D("METv_pt", 60, 0., 300.);
}

void TriLepton::Fill(VarHists &vh, const Vals &x, float w) {
    for (int k = 0; k < kNVar; ++k)
        if (x.has[k]) vh.h[k].Fill(x.v[k], w);
}

void TriLepton::initializeAnalyzer() {
    HcToWABase::initializeAnalyzer();
    run1E2Mu_ = HasFlag("Run1E2Mu");
    run3Mu_ = HasFlag("Run3Mu");
    if (!run1E2Mu_ && !run3Mu_) throw SKNano::ConfigError("[TriLepton] no channel flag (Run1E2Mu, Run3Mu)");
    if (IsDATA) {
        // one primary dataset per channel: MuonEG -> e mu mu, Muon -> mu mu mu
        const bool muonEG = DataStream.Contains("MuonEG");
        if (muonEG) run3Mu_ = false;
        else run1E2Mu_ = false;
        if (!run1E2Mu_ && !run3Mu_)
            throw SKNano::ConfigError("[TriLepton] data stream " + std::string(DataStream.Data()) +
                                      " feeds no requested channel");
    }

    if (!IsDATA) {
        LoadBTagCorrections();
        isDY2J_ = MCSample.Contains("DYto2") && MCSample.Contains("_2J_");
        const bool isDYG = MCSample.Contains("DYGto2LG");
        const bool isTTG = MCSample.Contains("TTG_1J");
        isConvSample_ = isDY2J_ || isDYG || isTTG;
        hasLHEPhoton_ = isDYG || isTTG;
        // exclusive photon-pT bins
        if (MCSample.Contains("PTG600toInf")) stitchMax_ = -1.f;
        else if (MCSample.Contains("PTG400toInf")) stitchMax_ = 600.f;
        else if (MCSample.Contains("PTG200toInf")) stitchMax_ = isDYG ? 400.f : -1.f;
        else if (MCSample.Contains("PTG100toInf")) stitchMax_ = 200.f;
        else if (isTTG || MCSample.Contains("DYGto2LG_1J_MLL50toInf")) stitchMax_ = 100.f;
        auto d = Hists("diag");
        hStitch_ = d.Book1D("stitch", 2, 0., 2.);
        if (hasLHEPhoton_) {
            hLHEPhoPt_ = d.Book1D("lhe_photon_pt", 400, 0., 1000.);
            hLHEPhoDRl_ = d.Book1D("lhe_photon_dRl", 100, 0., 5.);
            hLHEPhoEta_ = d.Book1D("lhe_photon_eta", 100, -10., 10.);
        }
        if (isDY2J_ || isDYG) {
            hGenPhoPt_ = d.Book1D("gen_photon_pt", 400, 0., 1000.);
            hGenPhoDRl_ = d.Book1D("gen_photon_dRl", 100, 0., 5.);
        }
    }

    // fake rates (nonprompt lanes, data)
    if (IsDATA) {
        const char *home = std::getenv("SKNANO_HOME");
        if (!home) throw SKNano::ConfigError("[TriLepton] SKNANO_HOME not set");
        std::string path;
        for (const char *sub : {"/analysis_modules/HcToWA_Analyzers", "/HcToWA_Analyzers"}) {
            const std::string candidate = std::string(home) + sub + "/data/2024/FakeRate/fakerate_HcToWA.json";
            if (FILE *fp = std::fopen(candidate.c_str(), "r")) {
                std::fclose(fp);
                path = candidate;
                break;
            }
        }
        if (path.empty()) throw SKNano::ConfigError("[TriLepton] data/2024/FakeRate/fakerate_HcToWA.json not found");
        frSet_ = correction::CorrectionSet::from_file(path);
        frMu_ = frSet_->at("FakeRate_Muon");
        frEl_ = frSet_->at("FakeRate_Electron");
        cout << "[TriLepton] fake rates from " << path << endl;
    }

    // lanes per region
    for (int r = 0; r < kNReg; ++r) {
        if (IsDATA) {
            booked_[r][kCentral] = (r != kSR); // blinded SR
            booked_[r][kNonprompt] = booked_[r][kNonpromptUp] = booked_[r][kNonpromptDown] = true;
        } else {
            booked_[r][kCentral] = true;
            booked_[r][kDYGVeto] = isDY2J_;
        }
    }
    for (int ch = 0; ch < kNCh; ++ch) {
        if ((ch == k1E2Mu && !run1E2Mu_) || (ch == k3Mu && !run3Mu_)) continue;
        const std::string c = kChName[ch];
        cutflow_[ch] = Hists(c).Book1D("cutflow", 10, 0., 10.);
        if (IsDATA) cutflowLNT_[ch] = Hists(c).Book1D("cutflow_nonprompt", 10, 0., 10.);
        else truthPre_[ch] = Hists(c).Book1D("event_category_prefilter", 6, 0., 6.);
        for (int r = 0; r < kNReg; ++r) {
            for (int l = 0; l < kNLane; ++l)
                if (booked_[r][l]) Book(h_[ch][r][l], c + "/" + kRegName[r] + "/" + kLaneName[l]);
            if (!IsDATA) {
                auto t = Hists(c + "/" + kRegName[r] + "/truth");
                truth_[ch][r].category = t.Book1D("event_category", 6, 0., 6.);
                truth_[ch][r].lepType = t.Book1D("lepton_type", 13, -6.5, 6.5);
                truth_[ch][r].elTypeVsFlav = t.Book2D("electron_type_vs_genPartFlav", 13, -6.5, 6.5, 23, 0., 23.);
            }
        }
    }
    cout << "[TriLepton] 1E2Mu " << run1E2Mu_ << ", 3Mu " << run3Mu_ << ", conversion sample " << isConvSample_
         << ", DY 2J " << isDY2J_ << ", stitch max " << stitchMax_ << (IsDATA ? ", data: SR blinded" : "") << endl;
}

float TriLepton::Rate(bool muon, float absEta, float ptcorr, const std::string &key) const {
    const auto &c = muon ? frMu_ : frEl_;
    return static_cast<float>(c->evaluate({static_cast<double>(absEta), static_cast<double>(ptcorr), key}));
}

float TriLepton::LeadingLHEPhotonPt() {
    const auto lhe = GetAllLHEViews();
    float best = -1.f, bestEta = 0.f, bestPhi = 0.f;
    for (std::size_t i = 0; i < lhe.size(); ++i) {
        const auto p = lhe[i];
        if (p.PdgId() != 22 || p.Status() != 1) continue;
        if (p.Pt() > best) {
            best = p.Pt();
            bestEta = p.Eta();
            bestPhi = p.Phi();
        }
    }
    if (best > 0.f) {
        float dmin = 99.f;
        for (std::size_t i = 0; i < lhe.size(); ++i) {
            const auto p = lhe[i];
            const int a = std::abs(p.PdgId());
            if (p.Status() != 1 || !(a == 11 || a == 13 || a == 15)) continue;
            dmin = std::min(dmin, DR(bestEta, bestPhi, p.Eta(), p.Phi()));
        }
        hLHEPhoPt_.Fill(best, 1.);
        hLHEPhoDRl_.Fill(dmin, 1.);
        hLHEPhoEta_.Fill(bestEta, 1.);
    }
    return best;
}

bool TriLepton::GenPhotonInDYGPhaseSpace() {
    // leading prompt status-1 photon and its distance to the prompt status-1 leptons
    float best = -1.f, bestEta = 0.f, bestPhi = 0.f;
    for (std::size_t i = 0; i < gens_.size(); ++i) {
        const auto p = gens_[i];
        if (p.PdgId() != 22 || p.Status() != 1 || !p.isPrompt()) continue;
        if (p.Pt() > best) {
            best = p.Pt();
            bestEta = p.Eta();
            bestPhi = p.Phi();
        }
    }
    if (best < 0.f) return false;
    float dmin = 99.f;
    for (std::size_t i = 0; i < gens_.size(); ++i) {
        const auto p = gens_[i];
        const int a = std::abs(p.PdgId());
        if (p.Status() != 1 || !p.isPrompt() || !(a == 11 || a == 13)) continue;
        dmin = std::min(dmin, DR(bestEta, bestPhi, p.Eta(), p.Phi()));
    }
    hGenPhoPt_.Fill(best, 1.);
    hGenPhoDRl_.Fill(dmin, 1.);
    return best > kDYGPhoPtMin && dmin > kDYGPhoDRMin;
}

void TriLepton::executeEvent() {
    Event ev = GetEvent();
    if (lumi_ < 0.f) lumi_ = IsDATA ? 1.f : ev.GetTriggerLumi("Full");
    const float w0 = IsDATA ? 1.f : MCweight() * lumi_;

    // photon-pT stitching of TTG / DYG (before anything else, also for the diagnostics)
    if (hasLHEPhoton_) {
        const float ptg = LeadingLHEPhotonPt();
        const bool keep = stitchMax_ < 0.f || ptg < stitchMax_;
        hStitch_.Fill(keep ? 1. : 0., w0);
        if (!keep) return;
    }
    bool dygPhase = false;
    if (!IsDATA && (isDY2J_ || hGenPhoPt_)) {
        gens_ = GetAllGenViews();
        dygPhase = GenPhotonInDYGPhaseSpace();
    }

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
    const bool is3Mu = run3Mu_ && mu.size() == 3 && elVeto.empty();
    if (!is1E2Mu && !is3Mu) return;
    const int ch = is1E2Mu ? k1E2Mu : k3Mu;

    bool allTight = true;
    for (auto i : mu) if (!(muBits_[i] & kTight)) allTight = false;
    for (auto i : el) if (!(elBits_[i] & kTight)) allTight = false;
    if (!IsDATA && !allTight) return; // MC: prompt mode only
    // data, tight: no preselection cutflow (blinded SR events would enter it); region bins only
    auto &cf = allTight ? cutflow_[ch] : cutflowLNT_[ch];
    const bool fillPre = !(IsDATA && allTight);
    auto cut = [&](int bin) { if (fillPre) cf.Fill(bin, allTight ? w0 : 1.f); };
    cut(0);

    if (ch == k1E2Mu) {
        if (!ev.PassTrigger(RVec<TString>{"HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
                                          "HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ"})) return;
        cut(1);
        const float pm1 = muons_[mu[0]].Pt(), pe = electrons_[el[0]].Pt();
        if (!((pm1 > 25.f && pe > 15.f) || (pm1 > 10.f && pe > 25.f))) return;
    } else {
        if (!ev.PassTrigger(TString("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8"))) return;
        cut(1);
        if (!(muons_[mu[0]].Pt() > 20.f && muons_[mu[1]].Pt() > 10.f && muons_[mu[2]].Pt() > 10.f)) return;
    }
    cut(2);

    // pT_corr-scaled four-vectors (identity for tight leptons)
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
    bool onZ = false, allOffZ = false;
    if (ch == k1E2Mu) {
        if (muons_[mu[0]].Charge() + muons_[mu[1]].Charge() != 0) return;
        const float mll = (pm[0] + pm[1]).M();
        if (!(mll > 12.f)) return;
        onZ = std::fabs(mll - kMZ) < 10.f;
        allOffZ = !onZ;
        x.v[kPairMass] = mll; x.has[kPairMass] = true;
        x.v[kElPt] = pe[0].Pt(); x.has[kElPt] = true;
        x.v[kElScEta] = electrons_[el[0]].ScEta(); x.has[kElScEta] = true;
        x.v[kM3l] = (pm[0] + pm[1] + pe[0]).M(); x.has[kM3l] = true;
    } else {
        const int q = muons_[mu[0]].Charge() + muons_[mu[1]].Charge() + muons_[mu[2]].Charge();
        if (std::abs(q) != 1) return;
        int os = -1;
        for (int a = 0; a < 3; ++a)
            if (muons_[mu[a]].Charge() != muons_[mu[(a + 1) % 3]].Charge() &&
                muons_[mu[a]].Charge() != muons_[mu[(a + 2) % 3]].Charge()) os = a;
        const int ss1 = (os + 1) % 3, ss2 = (os + 2) % 3;
        const float m1 = (pm[ss1] + pm[os]).M(), m2 = (pm[ss2] + pm[os]).M();
        if (!(m1 > 12.f && m2 > 12.f)) return;
        onZ = std::fabs(m1 - kMZ) < 10.f || std::fabs(m2 - kMZ) < 10.f;
        allOffZ = std::fabs(m1 - kMZ) > 10.f && std::fabs(m2 - kMZ) > 10.f;
        x.v[kPairLowM] = std::min(m1, m2); x.has[kPairLowM] = true;
        x.v[kPairHighM] = std::max(m1, m2); x.has[kPairHighM] = true;
        x.v[kMu3Pt] = pm[2].Pt(); x.has[kMu3Pt] = true;
        x.v[kMu3Eta] = pm[2].Eta(); x.has[kMu3Eta] = true;
        x.v[kM3l] = (pm[0] + pm[1] + pm[2]).M(); x.has[kM3l] = true;
    }
    x.v[kMu1Pt] = pm[0].Pt(); x.has[kMu1Pt] = true;
    x.v[kMu2Pt] = pm[1].Pt(); x.has[kMu2Pt] = true;
    x.v[kMu1Eta] = pm[0].Eta(); x.has[kMu1Eta] = true;
    x.v[kMu2Eta] = pm[1].Eta(); x.has[kMu2Eta] = true;
    cut(3);

    // truth (MC): lepton types, conversion filter with the veto (C2)
    int category = 0; // 0 prompt, 1 conversion, 2 conversion + fake (vetoed), 3 fake, 4 type 0 present
    std::vector<int> types;
    std::vector<std::pair<int, int>> elTypeFlav;
    if (!IsDATA) {
        gens_ = GetAllGenViews(); // cached per entry by the framework
        truthTool_.SetEvent(&gens_);
        bool conv = false, fake = false, err = false;
        for (auto i : mu) {
            const auto m = muons_[i];
            const int t = truthTool_.Type(false, m.Pt(), m.Eta(), m.Phi());
            types.push_back(t);
        }
        for (auto i : el) {
            const auto e = electrons_[i];
            const int t = truthTool_.Type(true, e.Pt(), e.Eta(), e.Phi());
            types.push_back(t);
            elTypeFlav.emplace_back(t, static_cast<int>(e.GenPartFlav()));
        }
        for (int t : types) {
            if (GenLeptonType::IsConversion(t)) conv = true;
            else if (GenLeptonType::IsHadronicOrUnmatched(t)) fake = true;
            else if (t == 0) err = true;
        }
        category = conv ? (fake ? 2 : 1) : (fake ? 3 : (err ? 4 : 0));
        truthPre_[ch].Fill(static_cast<double>(category), static_cast<double>(w0));
        if (isConvSample_ && category != 1) return;
    }
    cut(4);

    // jets cleaned from the veto leptons
    auto idx = SelectJetIndices(jets_, JetView::JetID::TIGHT, 20.f, 2.5f);
    idx = RemoveOverlapIndices(jets_, idx, electrons_, elVeto, 0.4f);
    idx = RemoveOverlapIndices(jets_, idx, muons_, mu, 0.4f);
    const auto sj = SelectJetViews(jets_, std::move(idx), V::nom, V::nom);
    std::vector<bool> tagged(sj.size(), false);
    int nB = 0;
    for (std::size_t k = 0; k < sj.size(); ++k)
        if (sj[k].GetTaggerResult(JetTagging::JetFlavTagger::ParT, JetTagging::JetFlavTaggerScoreType::B) > bTagWP) {
            tagged[k] = true;
            ++nB;
        }
    const int nJ = static_cast<int>(sj.size());
    x.v[kNJets] = static_cast<float>(nJ); x.has[kNJets] = true;
    x.v[kNBJets] = static_cast<float>(nB); x.has[kNBJets] = true;
    float met = 0.f;
    {
        Particle raw = ev.GetMETVector(Event::MET_Type::PUPPI), z1, z2, z3;
        PropagateJetSystToMET(jets_, z1);
        PropagateMuonCorrToMET(muons_, z2);
        PropagateElectronCorrToMET(electrons_, z3);
        met = static_cast<float>(std::hypot(raw.Px() + z1.Px() + z2.Px() + z3.Px(),
                                            raw.Py() + z1.Py() + z2.Py() + z3.Py()));
    }
    x.v[kMET] = met; x.has[kMET] = true;

    std::array<bool, kNReg> inReg{};
    inReg[kSR] = nJ >= 2 && nB >= 1;
    inReg[kZFake] = nJ >= 2 && nB == 0 && onZ;
    inReg[kZG] = met < 40.f && nB == 0 && allOffZ && std::fabs(x.v[kM3l] - kMZ) < 10.f;
    inReg[kWZ] = met > 40.f && nB == 0 && onZ;
    if (IsDATA && allTight) inReg[kSR] = false; // blinded
    bool any = false;
    for (int r = 0; r < kNReg; ++r) any = any || inReg[r];
    if (!any) return;

    if (allTight) {
        float w = w0;
        if (!IsDATA) {
            w *= myCorr->GetPUWeight(ev.nTrueInt(), V::nom);
            std::vector<TrigLep> tl;
            for (auto i : mu) {
                w *= MuonIDSF(muons_[i].Eta(), muons_[i].Pt(), 0);
                tl.push_back({true, std::fabs(muons_[i].Eta()), muons_[i].Pt()});
            }
            for (auto i : el) {
                const auto e = electrons_[i];
                w *= myCorr->GetElectronRECOSF(e, V::nom) * ElectronIDSF(e.ScEta(), e.Pt(), 0);
                tl.push_back({false, std::fabs(e.ScEta()), e.Pt()});
            }
            w *= TrigSF(ch == k1E2Mu ? kTrigEMu : kTrigDblMu, tl, 0);
            std::vector<BTagJet> bj;
            bj.reserve(sj.size());
            for (std::size_t k = 0; k < sj.size(); ++k)
                bj.push_back({sj[k].Pt(), sj[k].Eta(), static_cast<int>(sj[k].HadronFlavour()), static_cast<bool>(tagged[k])});
            std::array<float, kNBTagLanes> bw;
            BTagWeights(bj, false, bw);
            w *= bw[kBTagNom];
        }
        for (int r = 0; r < kNReg; ++r) {
            if (!inReg[r]) continue;
            cutflow_[ch].Fill(5 + r, w);
            Fill(h_[ch][r][kCentral], x, w);
            if (isDY2J_ && !dygPhase) Fill(h_[ch][r][kDYGVeto], x, w);
            if (!IsDATA) {
                truth_[ch][r].category.Fill(static_cast<double>(category), static_cast<double>(w));
                for (int t : types) truth_[ch][r].lepType.Fill(static_cast<double>(t), static_cast<double>(w));
                for (const auto &tf : elTypeFlav) truth_[ch][r].elTypeVsFlav.Fill(static_cast<double>(tf.first), static_cast<double>(tf.second), static_cast<double>(w));
            }
        }
        return;
    }

    // data, loose-not-tight: fake weight per rate set
    struct LNT { bool muon; float absEta; float ptcorr; };
    std::vector<LNT> lnt;
    for (std::size_t a = 0; a < mu.size(); ++a)
        if (!(muBits_[mu[a]] & kTight)) lnt.push_back({true, std::fabs(muons_[mu[a]].Eta()), static_cast<float>(pm[a].Pt())});
    for (std::size_t a = 0; a < el.size(); ++a)
        if (!(elBits_[el[a]] & kTight)) lnt.push_back({false, std::fabs(electrons_[el[a]].ScEta()), static_cast<float>(pe[a].Pt())});
    for (int l : {kNonprompt, kNonpromptUp, kNonpromptDown}) {
        float fw = -1.f;
        for (const auto &p : lnt) {
            const float fr = Rate(p.muon, p.absEta, p.ptcorr, kLaneKey[l]);
            fw *= -fr / (1.f - fr);
        }
        for (int r = 0; r < kNReg; ++r) {
            if (!inReg[r]) continue;
            if (l == kNonprompt) cutflowLNT_[ch].Fill(5 + r, fw);
            Fill(h_[ch][r][l], x, fw);
        }
    }
}
