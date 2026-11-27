#include <HcToWA/HcToWABase.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

#include <yaml-cpp/yaml.h>

HcToWABase::HcToWABase() {}
HcToWABase::~HcToWABase() {}

void HcToWABase::initializeAnalyzer() {
    if (Run != 3)
        throw SKNano::ConfigError("[HcToWABase] only Run 3 (2024) is supported");
    is2024 = (DataEra == "2024");

    if (!myCorr)
        myCorr = new MyCorrection(DataEra, DataPeriod,
                                  IsDATA ? DataStream : MCSample, IsDATA);

    // Required: a file without the private electron branches fails here.
    elCols.reset(new ElectronCustomColumns{
        GetColumnHandle<float>("Electron_DeltaEtaInSC", ColumnRequirement::Required),
        GetColumnHandle<float>("Electron_DeltaPhiInSC", ColumnRequirement::Required),
        GetColumnHandle<float>("Electron_DeltaPhiInSeed", ColumnRequirement::Required),
        GetColumnHandle<float>("Electron_ecalPFClusIso", ColumnRequirement::Required),
        GetColumnHandle<float>("Electron_hcalPFClusIso", ColumnRequirement::Required),
        GetColumnHandle<float>("Electron_dr03HcalTowerSumEt", ColumnRequirement::Required),
        GetColumnHandle<float>("Electron_superclusterPhi", ColumnRequirement::Required),
        GetColumnHandle<float>("Electron_superclusterEnergy", ColumnRequirement::Required)});

    bTagWP = myCorr->GetBTaggingWP(JetTagging::JetFlavTagger::ParT,
                                   JetTagging::JetFlavTaggerWP::Medium);
    isTTPowheg = !IsDATA && MCSample.Contains("TT") && MCSample.Contains("powheg");
    cout << "[HcToWABase] UParT Medium WP = " << bTagWP
         << ", TT powheg = " << isTTPowheg << endl;
}

// ---------------------------------------------------------------------------
// Muon IDs (old DataFormats/src/Muon.cc:179-204). Loose = Run 3 loose with
// SIP3D < 5 (decided 2026-11-24). TkRelIso is relative (trigger emulation).
void HcToWABase::EvaluateMuonIDs(const MuonViewCollection &muons,
                                 std::vector<std::uint8_t> &bits) const {
    const std::size_t n = muons.size();
    bits.assign(n, 0);
    for (std::size_t i = 0; i < n; ++i) {
        const auto mu = muons[i];
        if (!mu.isPOGMediumId()) continue;
        if (!(std::fabs(mu.dZ()) < 0.1f)) continue;
        if (!(mu.TkRelIso() < 0.4f)) continue;
        const float sip = mu.SIP3D();
        const float iso = mu.MiniPFRelIso();
        std::uint8_t b = 0;
        if (sip < 5.f && iso < 0.4f) b |= kLoose;
        if (sip < 3.f && iso < 0.1f) b |= kTight;
        bits[i] = b;
    }
}

// ---------------------------------------------------------------------------
// HLT CaloIdL_TrackIdL_IsoVL emulation (old Electron.cc:120-147), on the
// private v15 branches. pT in the relative cuts is the uncorrected NanoAOD
// (MiniAOD) pT, as in the old code (Run 3 NanoAOD electrons are uncalibrated),
// so the ID does not move with the energy-scale variations. The effective
// areas are those of B2G-25-013 (AN-25-154: "maintained up to Run3 2023").
bool HcToWABase::PassElectronTriggerEmulation(const ElectronView &e,
                                              std::size_t i, float rho) const {
    const float absScEta = std::fabs(e.ScEta());
    if (absScEta >= 1.444f && absScEta < 1.566f) return false; // ECAL gap
    const bool barrel = absScEta < 1.444f;
    const float pt = e.MiniAODPt();
    const float dEtaInSC = (*elCols).deltaEtaInSC[i];
    const float dPhiInSeed = (*elCols).deltaPhiInSeed[i];
    const float ecalIso = (*elCols).ecalPFClusIso[i];
    const float hcalIso = (*elCols).hcalPFClusIso[i];
    if (barrel) {
        if (!(e.sieie() < 0.013f)) return false;
        if (!(std::fabs(dEtaInSC) < 0.01f)) return false;
        if (!(std::fabs(dPhiInSeed) < 0.07f)) return false;
        if (!(e.hoe() < 0.13f)) return false;
        if (!(std::max(0.f, ecalIso - rho * 0.16544f) < 0.5f * pt)) return false;
        if (!(std::max(0.f, hcalIso - rho * 0.05956f) < 0.3f * pt)) return false;
    } else {
        if (!(e.sieie() < 0.035f)) return false;
        if (!(std::fabs(dEtaInSC) < 0.015f)) return false;
        if (!(std::fabs(dPhiInSeed) < 0.1f)) return false;
        if (!(e.hoe() < 0.13f)) return false;
        if (!(std::max(0.f, ecalIso - rho * 0.13212f) < 0.5f * pt)) return false;
        if (!(std::max(0.f, hcalIso - rho * 0.13052f) < 0.3f * pt)) return false;
    }
    if (!(e.dr03TkSumPt() < 0.2f * pt)) return false;
    return true;
}

// Old Electron.cc:149-204 (tight; loose = Run 3 loose).
void HcToWABase::EvaluateElectronIDs(const ElectronViewCollection &electrons,
                                     float rho,
                                     std::vector<std::uint8_t> &bits) const {
    const std::size_t n = electrons.size();
    bits.assign(n, 0);
    for (std::size_t i = 0; i < n; ++i) {
        const auto e = electrons[i];
        // Baseline
        if (!PassElectronTriggerEmulation(e, i, rho)) continue;
        if (!e.ConvVeto()) continue;
        if (!(e.LostHits() < 2)) continue;
        if (!(std::fabs(e.dZ()) < 0.1f)) continue;
        const float sip = e.SIP3D();
        const float iso = e.MiniPFRelIso();
        const bool wp90 = e.isMVANoIsoWP90();
        std::uint8_t b = 0;
        if (wp90 && sip < 4.f && iso < 0.1f) b |= kTight;
        if (sip < 6.f && iso < 0.4f) {
            const float absScEta = std::fabs(e.ScEta());
            const float cut = absScEta < 0.8f ? 0.8f : (absScEta < 1.444f ? 0.5f : -0.8f);
            if (wp90 || e.MvaNoIso() > cut) b |= kLoose;
        }
        bits[i] = b;
    }
}

// ---------------------------------------------------------------------------
bool HcToWABase::PassEventFilters(const JetViewCollection &jets, const Event &ev) {
    if (!PassNoiseFilter(jets, ev)) return false;
    // JME Run 3 list, 2024: "use the stored flag" (data and simulation).
    if (is2024 && !static_cast<bool>(Flag_ecalBadCalibFilter)) return false;
    return true;
}

// ---------------------------------------------------------------------------
// Old MyCorrection.cc:1366-1394 (first hard-process top and antitop).
float HcToWABase::TopPtWeight() {
    if (!isTTPowheg) return 1.f;
    const auto gens = GetAllGenViews();
    float topPt = -1.f, antitopPt = -1.f;
    for (std::size_t i = 0; i < gens.size(); ++i) {
        const auto g = gens[i];
        if (!g.isHardProcess()) continue;
        const int pid = g.PdgId();
        if (pid == 6 && topPt < 0.f) topPt = g.Pt();
        else if (pid == -6 && antitopPt < 0.f) antitopPt = g.Pt();
        if (topPt >= 0.f && antitopPt >= 0.f) break;
    }
    if (topPt < 0.f || antitopPt < 0.f) return 1.f;
    if (topPt > 2000.f || antitopPt > 2000.f) return 1.f;
    constexpr float a = 0.103f, b = -0.0118f, c = 0.000134f, d = 0.973f;
    const float sfT = a * std::exp(b * topPt) - c * topPt + d;
    const float sfA = a * std::exp(b * antitopPt) - c * antitopPt + d;
    return std::sqrt(sfT * sfA);
}

// ---------------------------------------------------------------------------
// b-tag corrections are loaded here rather than through MyCorrection because
// MyCorrection::GetBTaggingSF only offers up/down (not the correlated /
// uncorrelated split) and looks the correction up by name on every call.
// The file paths follow MyCorrection::GetEraConfig exactly.
void HcToWABase::LoadBTagCorrections() {
    const char *pogPath = std::getenv("JSONPOG_REPO_PATH");
    const char *dataPath = std::getenv("SKNANO_DATA");
    if (!pogPath || !dataPath)
        throw SKNano::ConfigError("[HcToWABase] JSONPOG_REPO_PATH or SKNANO_DATA not set");
    const std::string eraDir = std::string(dataPath) + "/" + DataEra.Data();
    const std::string cfgPath = eraDir + "/Correction/era_config.yml";
    YAML::Node yaml = YAML::LoadFile(cfgPath);
    const std::string campaign = yaml["campaign"].as<std::string>();
    const YAML::Node spec = yaml["pog_files"]["btagging"];
    const YAML::Node effNode = yaml["data_files"]["btagging_eff"];
    if (!spec || !effNode) {
        cout << "\033[1;31m[HcToWABase] era config has no btagging or btagging_eff entry: "
                "b-tag weight stays 1 and the BtagSF lanes are omitted\033[0m" << endl;
        btagReady = false;
        return;
    }
    std::string snapshot;
    const YAML::Node snapshots = yaml["snapshots"];
    if (const char *tag = std::getenv("SKNANO_CORRECTION_TAG")) snapshot = tag;
    else if (spec["snapshot"]) snapshot = spec["snapshot"].as<std::string>();
    else if (snapshots && snapshots["BTV"]) snapshot = snapshots["BTV"].as<std::string>();
    else snapshot = snapshots ? snapshots["default"].as<std::string>("latest") : "latest";
    const std::string sfPath = std::string(pogPath) + "/BTV/" + campaign + "/" +
                               snapshot + "/" + spec["name"].as<std::string>();
    const std::string effPath = eraDir + "/" + effNode.as<std::string>();

    const std::string tagger =
        JetTagging::GetTaggerCorrectionLibStr(JetTagging::JetFlavTagger::ParT).Data();
    btagWPStr = JetTagging::GetTaggerCorrectionWPStr(JetTagging::JetFlavTaggerWP::Medium).Data();
    auto csetSF = correction::CorrectionSet::from_file(sfPath);
    auto csetEff = correction::CorrectionSet::from_file(effPath);
    btagRefHF = csetSF->at(tagger + "_mujets");
    btagRefLF = csetSF->at(tagger + "_light");
    btagRefEff = csetEff->at(tagger);
    // Check the efficiency map covers the WP (throws otherwise).
    for (int flav : {0, 4, 5})
        static_cast<void>(btagRefEff->evaluate({std::string("central"), btagWPStr, flav, 1.0, 50.0}));
    btagReady = true;
    cout << "[HcToWABase] b-tag SF: " << sfPath << " (" << tagger << "_mujets, "
         << tagger << "_light, WP " << btagWPStr << ")" << endl;
    cout << "[HcToWABase] b-tag efficiency: " << effPath << " (" << tagger << ")" << endl;
}

void HcToWABase::BTagWeights(const std::vector<BTagJet> &jets, bool allVariations,
                             std::array<float, kNBTagLanes> &out) const {
    out.fill(1.f);
    if (!btagReady) return;
    static const std::string kCentral = "central";
    static const std::string kSyst[4] = {"up_correlated", "down_correlated",
                                         "up_uncorrelated", "down_uncorrelated"};
    const int nLanes = allVariations ? kNBTagLanes : 1;
    double pMC = 1.;
    std::array<double, kNBTagLanes> pData;
    pData.fill(1.);
    for (const auto &j : jets) {
        const int flav = (j.flav == 5 || j.flav == 4) ? j.flav : 0;
        const bool heavy = flav != 0;
        // BTV maps end at |eta| = 2.5 with flow 'error'; jets are |eta| <= 2.5.
        const double absEta = std::min(std::fabs(static_cast<double>(j.eta)), 2.4999);
        const double pt = j.pt;
        const auto &ref = heavy ? btagRefHF : btagRefLF;
        float eff = btagRefEff->evaluate({kCentral, btagWPStr, flav, absEta, pt});
        eff = std::clamp(eff, 1e-6f, 1.f - 1e-6f);
        std::array<float, kNBTagLanes> sf;
        sf[kBTagNom] = ref->evaluate({kCentral, btagWPStr, flav, absEta, pt});
        for (int k = 1; k < nLanes; ++k) sf[k] = sf[kBTagNom];
        if (allVariations) {
            const int first = heavy ? kBTagHFcorrUp : kBTagLFcorrUp;
            for (int s = 0; s < 4; ++s)
                sf[first + s] = ref->evaluate({kSyst[s], btagWPStr, flav, absEta, pt});
        }
        if (j.tagged) {
            pMC *= eff;
            for (int k = 0; k < nLanes; ++k) pData[k] *= sf[k] * eff;
        } else {
            pMC *= (1. - eff);
            for (int k = 0; k < nLanes; ++k)
                pData[k] *= std::max(0., 1. - static_cast<double>(sf[k]) * eff);
        }
    }
    for (int k = 0; k < nLanes; ++k)
        out[k] = pMC > 0. ? static_cast<float>(pData[k] / pMC) : 1.f;
}
