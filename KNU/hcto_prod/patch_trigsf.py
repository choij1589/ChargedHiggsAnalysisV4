import sys
B='/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/'
def rep(path,a,b,count=1):
    s=open(B+path).read()
    if s.count(a)!=count: sys.exit(f"{path}: pattern found {s.count(a)}x: {a[:70]!r}")
    s=s.replace(a,b); open(B+path,'w').write(s)

# ---------------- HcToWABase.h
rep('include/HcToWA/HcToWABase.h','''    float ElectronIDSF(float scEta, float pt, int var) const;
''','''    float ElectronIDSF(float scEta, float pt, int var) const;

    // Trigger efficiencies and SFs (ChargedHiggsAnalysisV4 PLAN_Trigger T1, step 3):
    // data/2024/Trigger/trigger_HcToWA.json (Trigger/python/makeTrigJson.py): leg efficiencies
    // in data and MC vs (|eta| (electrons |eta_SC|), corrected pT) and the inclusive pairwise
    // filters. Per-event efficiency = true OR of the paths from per-lepton leg probabilities
    // (nesting within a lepton: Mu17 => Mu8, Mu23 => Mu8, Ele23 => Ele12; independence between
    // leptons), enumerating the 3^N leg states, times the pairwise filter:
    //   DblMu: one muon passes Mu17 and a different one Mu8; x DZ (= DZ_Mass3p8)
    //   EMu:   (muon Mu23 and electron Ele12) or (muon Mu8 and electron Ele23); x DZ
    // SF = eff_data / eff_MC. var 1 (up): all data efficiencies up and MC down, var 2 the
    // opposite (one nuisance per path set, T3); the MC closure term (correction "TrigClosure",
    // if present) is added in quadrature to the relative variation.
    struct TrigLep { bool muon; float absEta; float pt; };
    enum TrigSet : int { kTrigDblMu = 0, kTrigEMu, kNTrigSets };
    void LoadTriggerEfficiencies();
    double TrigEff(int set, const std::vector<TrigLep> &leps, bool data, int var) const;
    float TrigSF(int set, const std::vector<TrigLep> &leps, int var) const;
''')
rep('include/HcToWA/HcToWABase.h','''    correction::Correction::Ref idSFElectron; //!
''','''    correction::Correction::Ref idSFElectron; //!
    std::unique_ptr<correction::CorrectionSet> trigSet; //!
    std::array<correction::Correction::Ref, 4> trigLegMu_;  //! DblMu17, DblMu8, EMu23, EMu8
    std::array<correction::Correction::Ref, 2> trigLegEl_;  //! EMu Ele23, Ele12
    correction::Correction::Ref trigPair_;                  //!
    std::array<double, kNTrigSets> trigClosure_{};          //!
''')

# ---------------- HcToWABase.cc
rep('src/HcToWABase.cc','''    if (!IsDATA) LoadIDScaleFactors();
''','''    if (!IsDATA) {
        LoadIDScaleFactors();
        LoadTriggerEfficiencies();
    }
''')
s=open(B+'src/HcToWABase.cc').read()
s+='''
// ---------------------------------------------------------------------------
// Trigger efficiencies (ChargedHiggsAnalysisV4 PLAN_Trigger T1, step 3).
void HcToWABase::LoadTriggerEfficiencies() {
    if (!is2024)
        throw SKNano::ConfigError("[HcToWABase] trigger efficiencies exist only for 2024");
    const char *home = std::getenv("SKNANO_HOME");
    if (!home) throw SKNano::ConfigError("[HcToWABase] SKNANO_HOME not set");
    std::string path;
    for (const char *sub : {"/analysis_modules/HcToWA_Analyzers", "/HcToWA_Analyzers"}) {
        const std::string candidate = std::string(home) + sub + "/data/2024/Trigger/trigger_HcToWA.json";
        if (FILE *fp = std::fopen(candidate.c_str(), "r")) {
            std::fclose(fp);
            path = candidate;
            break;
        }
    }
    if (path.empty())
        throw SKNano::ConfigError("[HcToWABase] data/2024/Trigger/trigger_HcToWA.json not found under " +
                                  std::string(home));
    trigSet = correction::CorrectionSet::from_file(path);
    trigLegMu_ = {trigSet->at("DblMu_Mu17Leg"), trigSet->at("DblMu_Mu8Leg"),
                  trigSet->at("EMu_Mu23Leg"), trigSet->at("EMu_Mu8Leg")};
    trigLegEl_ = {trigSet->at("EMu_Ele23Leg"), trigSet->at("EMu_Ele12Leg")};
    trigPair_ = trigSet->at("PairFilter");
    trigClosure_.fill(0.);
    try {
        const auto c = trigSet->at("TrigClosure");
        trigClosure_[kTrigDblMu] = c->evaluate({std::string("DblMu")});
        trigClosure_[kTrigEMu] = c->evaluate({std::string("EMu")});
    } catch (const std::exception &) {
        // no closure term yet
    }
    cout << "[HcToWABase] trigger efficiencies from " << path << " (closure term DblMu "
         << trigClosure_[kTrigDblMu] << ", EMu " << trigClosure_[kTrigEMu] << ")" << endl;
}

namespace {
// var 0 nominal; 1: data up and MC down; 2: data down and MC up
std::string TrigValType(bool data, int var) {
    if (data) return var == 1 ? "effDataUp" : (var == 2 ? "effDataDown" : "effData");
    return var == 1 ? "effMCDown" : (var == 2 ? "effMCUp" : "effMC");
}
double Clamp01(double x) { return std::min(std::max(x, 0.), 1.); }
} // namespace

double HcToWABase::TrigEff(int set, const std::vector<TrigLep> &leps, bool data, int var) const {
    const std::string vt = TrigValType(data, var);
    // per relevant lepton: probability of the high (tight) and low (loose) leg, pLo >= pHi
    std::vector<double> pHi, pLo;
    std::vector<bool> isMu;
    for (const auto &l : leps) {
        correction::Correction::Ref hi, lo;
        if (set == kTrigDblMu) {
            if (!l.muon) continue;
            hi = trigLegMu_[0]; lo = trigLegMu_[1];
        } else if (l.muon) {
            hi = trigLegMu_[2]; lo = trigLegMu_[3];
        } else {
            hi = trigLegEl_[0]; lo = trigLegEl_[1];
        }
        const double h = Clamp01(hi->evaluate({static_cast<double>(l.absEta), static_cast<double>(l.pt), vt}));
        const double o = Clamp01(lo->evaluate({static_cast<double>(l.absEta), static_cast<double>(l.pt), vt}));
        pHi.push_back(h);
        pLo.push_back(std::max(o, h));
        isMu.push_back(l.muon);
    }
    const std::size_t n = pHi.size();
    int nStates = 1;
    for (std::size_t i = 0; i < n; ++i) nStates *= 3;
    double p = 0.;
    for (int s = 0; s < nStates; ++s) {
        double prob = 1.;
        int t = s, nHi = 0, nLoOnly = 0;
        bool muHi = false, muLo = false, elHi = false, elLo = false;
        for (std::size_t i = 0; i < n && prob > 0.; ++i) {
            const int st = t % 3;
            t /= 3;
            prob *= st == 0 ? pHi[i] : (st == 1 ? pLo[i] - pHi[i] : 1. - pLo[i]);
            if (st == 0) { ++nHi; (isMu[i] ? muHi : elHi) = true; (isMu[i] ? muLo : elLo) = true; }
            else if (st == 1) { ++nLoOnly; (isMu[i] ? muLo : elLo) = true; }
        }
        if (prob <= 0.) continue;
        const bool fires = set == kTrigDblMu ? (nHi >= 2 || (nHi >= 1 && nLoOnly >= 1))
                                             : ((muHi && elLo) || (muLo && elHi));
        if (fires) p += prob;
    }
    const double pair = Clamp01(trigPair_->evaluate({std::string(set == kTrigDblMu ? "DblMu_DZ" : "EMu_DZ"), vt}));
    return p * pair;
}

float HcToWABase::TrigSF(int set, const std::vector<TrigLep> &leps, int var) const {
    if (IsDATA) return 1.f;
    const double d0 = TrigEff(set, leps, true, 0), m0 = TrigEff(set, leps, false, 0);
    if (m0 <= 0.) return 1.f;
    const double sf0 = d0 / m0;
    if (var == 0) return static_cast<float>(sf0);
    const double m = TrigEff(set, leps, false, var);
    const double sf = m > 0. ? TrigEff(set, leps, true, var) / m : sf0;
    const double rel = std::hypot(sf / sf0 - 1., trigClosure_[set]);
    return static_cast<float>(sf0 * (var == 1 ? 1. + rel : 1. - rel));
}
'''
open(B+'src/HcToWABase.cc','w').write(s)

# ---------------- DiLepton.h
rep('include/HcToWA/DiLepton.h','kFPU = 0, kFEleReco, kFBTag, kFEleIDProxy, kFEleTrigProxy, kFMuID, kFEleID, kNFactors',
    'kFPU = 0, kFEleReco, kFBTag, kFEleIDProxy, kFEleTrigProxy, kFMuID, kFEleID, kFDblMuTrig, kFEMuTrig, kNFactors')
rep('include/HcToWA/DiLepton.h','topPtWeight, eleRecoSF, btagSF, eleIDSFProxy, eleTrigSFProxy, muIDSF, eleIDSF, total;',
    'topPtWeight, eleRecoSF, btagSF, eleIDSFProxy, eleTrigSFProxy, muIDSF, eleIDSF, dblMuTrigSF, emuTrigSF, total;')
rep('include/HcToWA/DiLepton.h','''        Hist1DHandle cutflow;
        WeightHists weights;
    };''','''        Hist1DHandle cutflow;
        WeightHists weights;
        // MC trigger closure (PLAN_Trigger step 3), offline selection without the trigger:
        // [var][den, obs (path fired), exp (weighted by the MC efficiency)]; vars incl, pt1,
        // pt2 (DIMU leading / subleading muon; EMU muon / electron), maxeta
        std::array<std::array<Hist1DHandle, 3>, 4> trigClosure;
    };''')
rep('include/HcToWA/DiLepton.h','''    void BuildLeptons(EvtVar v, LepSel &out) const;''','''    void BuildLeptons(EvtVar v, LepSel &out) const;
    void FillTrigClosure(const Event &ev, float w0);
    std::vector<TrigLep> TrigLeptons(const LepSel &lep) const;''')
rep('include/HcToWA/DiLepton.h','''    std::array<bool, kNChannels> trig_{}; //!''','''    std::array<bool, kNChannels> trig_{}; //!
    bool ignoreTrig_ = false; //! trigger closure: selection without the trigger requirement''')

# ---------------- DiLepton.cc
rep('src/DiLepton.cc','''            } else if (name == "ElectronTrigSFProxy") {
                factor = kFEleTrigProxy; chs = {kZEE};''','''            } else if (name == "ElectronTrigSFProxy") {
                factor = kFEleTrigProxy; chs = {kZEE};
            } else if (name == "DblMuTrigSF") {
                factor = kFDblMuTrig; chs = {kDIMU};
            } else if (name == "EMuTrigSF") {
                factor = kFEMuTrig; chs = {kEMU};''')
rep('src/DiLepton.cc','''                                               "MuonIDSF", "ElectronIDSF"};''','''                                               "MuonIDSF", "ElectronIDSF", "DblMuTrigSF", "EMuTrigSF"};''')
rep('src/DiLepton.cc','''        if (ch == kZEE) w.eleTrigSFProxy = g.Book1D("eleTrigSFProxy", 100, -5., 5.);
''','''        if (ch == kZEE) w.eleTrigSFProxy = g.Book1D("eleTrigSFProxy", 100, -5., 5.);
        if (ch == kDIMU) w.dblMuTrigSF = g.Book1D("dblMuTrigSF", 100, -5., 5.);
        if (ch == kEMU) w.emuTrigSF = g.Book1D("emuTrigSF", 100, -5., 5.);
        if (ch == kDIMU || ch == kEMU) {
            const auto t = Hists(c + "/Central/TrigClosure");
            const char *kind[3] = {"den", "obs", "exp"};
            for (int k = 0; k < 3; ++k) {
                conf.trigClosure[0][k] = t.Book1D(std::string("incl_") + kind[k], 1, 0., 1.);
                conf.trigClosure[1][k] = t.Book1D(std::string("pt1_") + kind[k], 49, 10., 255.);
                conf.trigClosure[2][k] = t.Book1D(std::string("pt2_") + kind[k], 49, 10., 255.);
                conf.trigClosure[3][k] = t.Book1D(std::string("maxeta_") + kind[k], 10, 0., 2.5);
            }
        }
''')
rep('src/DiLepton.cc','''            if (!trig_[kDIMU]) return false;''','''            if (!trig_[kDIMU] && !ignoreTrig_) return false;''')
rep('src/DiLepton.cc','''            if (!trig_[kEMU]) return false;''','''            if (!trig_[kEMU] && !ignoreTrig_) return false;''')
rep('src/DiLepton.cc','''    trig_[kZEE] = channels_[kZEE].enabled && ev.PassTrigger(TString("HLT_Ele30_WPTight_Gsf"));
''','''    trig_[kZEE] = channels_[kZEE].enabled && ev.PassTrigger(TString("HLT_Ele30_WPTight_Gsf"));
    if (!IsDATA) FillTrigClosure(ev, w0);
''')
rep('src/DiLepton.cc','''    if (ch == kZEE) {
        const float tn = ZEETriggerSF(lep.elTight, V::nom);''','''    if (ch == kDIMU || ch == kEMU) {
        const int set = ch == kDIMU ? kTrigDblMu : kTrigEMu;
        const int f = ch == kDIMU ? kFDblMuTrig : kFEMuTrig;
        const auto tl = TrigLeptons(lep);
        const float n = TrigSF(set, tl, 0);
        fv.vars[f][0] = n;
        fv.vars[f][1] = allVariations ? TrigSF(set, tl, 1) : n;
        fv.vars[f][2] = allVariations ? TrigSF(set, tl, 2) : n;
    }
    if (ch == kZEE) {
        const float tn = ZEETriggerSF(lep.elTight, V::nom);''')
rep('src/DiLepton.cc','''                if (wh.eleIDSF) wh.eleIDSF.Fill(fv.nom(kFEleID), 1.f);
''','''                if (wh.eleIDSF) wh.eleIDSF.Fill(fv.nom(kFEleID), 1.f);
                if (wh.dblMuTrigSF) wh.dblMuTrigSF.Fill(fv.nom(kFDblMuTrig), 1.f);
                if (wh.emuTrigSF) wh.emuTrigSF.Fill(fv.nom(kFEMuTrig), 1.f);
''')
s=open(B+'src/DiLepton.cc').read()
s+='''
// ---------------------------------------------------------------------------
// Trigger SF inputs and MC closure (ChargedHiggsAnalysisV4 PLAN_Trigger step 3).
std::vector<HcToWABase::TrigLep> DiLepton::TrigLeptons(const LepSel &lep) const {
    std::vector<TrigLep> out;
    for (const auto i : lep.muTight) out.push_back({true, std::fabs(muons_[i].Eta()), muons_[i].Pt()});
    for (const auto i : lep.elTight) out.push_back({false, std::fabs(electrons_[i].ScEta()), electrons_[i].Pt()});
    return out;
}

void DiLepton::FillTrigClosure(const Event &ev, float w0) {
    // Lepton-level offline selection of DIMU and EMU without the trigger (EMU: no jet cuts);
    // observed = path decision, expected = per-event MC efficiency (T1). Weight: MC x PU.
    if (!channels_[kDIMU].enabled && !channels_[kEMU].enabled) return;
    LepSel lep;
    BuildLeptons(EvtVar::Central, lep);
    float w = -1.f;
    for (int ch : {kDIMU, kEMU}) {
        auto &conf = channels_[ch];
        if (!conf.enabled) continue;
        ignoreTrig_ = true;
        const bool pass = Select(ch, EvtVar::Central, lep, nullptr, nullptr, w0, false);
        ignoreTrig_ = false;
        if (!pass) continue;
        if (w < 0.f) w = w0 * myCorr->GetPUWeight(ev.nTrueInt(), V::nom);
        const auto tl = TrigLeptons(lep);
        const double eff = TrigEff(ch == kDIMU ? kTrigDblMu : kTrigEMu, tl, false, 0);
        float pt1, pt2, maxEta = 0.f;
        if (ch == kDIMU) { pt1 = tl[0].pt; pt2 = tl[1].pt; }
        else { pt1 = tl[0].pt; pt2 = tl[1].pt; } // muon first, then electron
        for (const auto &l : tl) maxEta = std::max(maxEta, l.absEta);
        const float x[4] = {0.5f, std::min(pt1, 254.f), std::min(pt2, 254.f), std::min(maxEta, 2.49f)};
        for (int k = 0; k < 4; ++k) {
            conf.trigClosure[k][0].Fill(x[k], w);
            if (trig_[ch]) conf.trigClosure[k][1].Fill(x[k], w);
            conf.trigClosure[k][2].Fill(x[k], w * static_cast<float>(eff));
        }
    }
}
'''
open(B+'src/DiLepton.cc','w').write(s)

# ---------------- YAML
rep('data/DiLeptonSystematics.yaml','''  - syst: ElectronTrigSFProxy
''','''  - syst: ElectronTrigSFProxy
  - syst: DblMuTrigSF
  - syst: EMuTrigSF
''')
rep('data/DiLeptonSystematics.yaml','''# Central has NO top-pT weight;''','''# DblMuTrigSF (DIMU) / EMuTrigSF (EMU): per-event trigger SF from the leg efficiencies
# (data/2024/Trigger/trigger_HcToWA.json, PLAN_Trigger T1/T3; 2026-11-26).
# Central has NO top-pT weight;''')
print("patched")
