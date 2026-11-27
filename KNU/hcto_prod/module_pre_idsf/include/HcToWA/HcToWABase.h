#ifndef HcToWA_HcToWABase_h
#define HcToWA_HcToWABase_h

// Shared base of the H+ -> W A (A -> mu mu) analyzers for 2024 (NanoAODv15,
// RNTuple), ported from the B2G-25-013 production code (old SKNano
// Analyzers/src/DiLeptonBase.cc, DataFormats/src/{Muon,Electron}.cc).
//
// - Our lepton IDs, evaluated once per object per event into a bitmask. The
//   SKNano 2.0 built-in HcToWA* IDs are NOT used (electron trigger-emulation
//   variables are stubs there; the muon tight ID compares TkRelIso with
//   0.4*Pt()).
// - Electron trigger emulation reads the private v15 custom branches through
//   required column handles (a missing branch fails the job at init).
// - Event filters: JME Run 3 noise filters (PassNoiseFilter) AND
//   Flag_ecalBadCalibFilter for 2024 (missing from the SKNano 2.0 Run 3 list).
// - b tagging: UParT Medium, fixed-WP method-1a event weight (no SKNano helper
//   exists), BTV "mujets" SFs for b/c jets and "light" for light jets, with the
//   correlated/uncorrelated variations; efficiencies from the era btagging_eff.
// - Top pT: the analytic function of the old MyCorrection (data/NNLO fit),
//   since SKNano 2.0 only offers a 13 TeV ONNX model.

#include <AnalyzerFramework/AnalyzerCore.h>

#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

class HcToWABase : public AnalyzerCore {
public:
    HcToWABase();
    ~HcToWABase();

    void initializeAnalyzer() override;
    void executeEvent() override {}

    enum IDBit : std::uint8_t { kLoose = 1u << 0, kTight = 1u << 1 };

    // b-tag event weight lanes (method 1a)
    enum BTagLane : int {
        kBTagNom = 0,
        kBTagHFcorrUp, kBTagHFcorrDown, kBTagHFuncorrUp, kBTagHFuncorrDown,
        kBTagLFcorrUp, kBTagLFcorrDown, kBTagLFuncorrUp, kBTagLFuncorrDown,
        kNBTagLanes
    };
    struct BTagJet {
        float pt;
        float eta;
        int flav;
        bool tagged;
    };

protected:
    // Private v15 electron branches (RNTuplizer branch table names).
    struct ElectronCustomColumns {
        ColumnHandle<float> deltaEtaInSC;      // Electron_DeltaEtaInSC
        ColumnHandle<float> deltaPhiInSC;      // Electron_DeltaPhiInSC
        ColumnHandle<float> deltaPhiInSeed;    // Electron_DeltaPhiInSeed
        ColumnHandle<float> ecalPFClusIso;     // Electron_ecalPFClusIso
        ColumnHandle<float> hcalPFClusIso;     // Electron_hcalPFClusIso
        ColumnHandle<float> dr03HcalTowerSumEt;// Electron_dr03HcalTowerSumEt
        ColumnHandle<float> superclusterPhi;   // Electron_superclusterPhi
        ColumnHandle<float> superclusterEnergy;// Electron_superclusterEnergy
    };

    // Lepton IDs (bitmask per raw object index).
    void EvaluateMuonIDs(const MuonViewCollection &muons,
                         std::vector<std::uint8_t> &bits) const;
    void EvaluateElectronIDs(const ElectronViewCollection &electrons, float rho,
                             std::vector<std::uint8_t> &bits) const;
    bool PassElectronTriggerEmulation(const ElectronView &electron,
                                      std::size_t rawIdx, float rho) const;

    // Event filters (noise filters + ecalBadCalibFilter for 2024).
    bool PassEventFilters(const JetViewCollection &jets, const Event &ev);

    // Top pT reweighting (analytic, TT powheg only; 1 otherwise).
    float TopPtWeight();

    // Method-1a b-tag weight. With allVariations=false only kBTagNom is set.
    void BTagWeights(const std::vector<BTagJet> &jets, bool allVariations,
                     std::array<float, kNBTagLanes> &out) const;
    bool BTagWeightAvailable() const { return btagReady; }
    void LoadBTagCorrections();

    std::unique_ptr<ElectronCustomColumns> elCols; //!
    correction::Correction::Ref btagRefHF;  //!
    correction::Correction::Ref btagRefLF;  //!
    correction::Correction::Ref btagRefEff; //!
    std::string btagWPStr;     //!
    bool btagReady = false; //!
    float bTagWP = 0.f; //!
    bool isTTPowheg = false; //!
    bool is2024 = false; //!
};

#endif
