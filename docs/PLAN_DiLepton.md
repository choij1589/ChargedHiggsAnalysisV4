# PLAN: DiLepton analyzer for 2024 (phase 2.2)

Goal: check every object and its corrections in the dimuon and electron-muon control regions with 2024 data, using SKNano 2.0 at KNU. The reference is the production C++ analyzer of B2G-25-013 (old SKNano `Analyzers/src/DiLepton.cc`, `DiLeptonBase.cc`; the old `PyAnalyzers/DiLepton.py` is outdated and not used). Written 2026-11-24; decisions in `LOG_ObjectID.md`.

## 1. What is reproduced

| Item | B2G-25-013 (old `DiLepton.cc`) | 2024 |
|---|---|---|
| Flags | `RunDiMu`, `RunEMu`, `RunSyst` (+ `RunNoJetVeto`) | same, plus `RunZEE` (Z->ee check, see below) |
| Data | DiMu: DoubleMuon/Muon/Muon0/Muon1; EMu: MuonEG | DiMu: Muon0, Muon1; EMu: MuonEG; periods C-I incl. I_v2 |
| Triggers | DiMu: `Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8`; EMu: `Mu23_TrkIsoVVL_Ele12_..._DZ` OR `Mu8_TrkIsoVVL_Ele23_..._DZ` | same (all present in the 2024 `HLT_Path.json`) |
| Event filters | Run 3 noise filters; event-level jet veto map | JME Run 3 list (`PassNoiseFilter`) **plus `Flag_ecalBadCalibFilter`** (2024: stored flag; missing from SKNano 2.0's Run 3 list); event veto with `jetvetomap` and JERC's Run 3 jet selection (SKNano 2.0 `PassJetVetoMap`: tightLepVeto, pT > 15, EM fraction < 0.9, no muon overlap) |
| Muons | loose/tight HcToWA, pT > 10, \|eta\| < 2.4 | loose: SIP3D < 5 (decided); tight unchanged |
| Electrons | loose pT > 10, \|eta\| < 2.5; tight pT > 15; ECAL gap removed; 2018 HEM veto | same, without HEM; IDs on the v15 custom branches |
| Jets | tight ID (hand-made), pT > 20, \|eta\| < 2.5, dR > 0.4 to loose leptons | JME `jetid.json` **AK4PUPPI_Tight** (decided), same kinematics |
| b jets | DeepJet medium | UParT, WP open (D1) |
| MET | PUPPI, re-Type-I corrected for jets, muons, electrons | same (via `PropagateJetSystToMET`, `PropagateMuon/ElectronCorrToMET`) |
| DiMu | 2 tight = 2 loose muons, 0 loose e, trigger, pT > 20/10, OS, m(mumu) > 50 | same |
| EMu | 1 mu + 1 e (tight = loose), trigger, (pT_mu > 25 & pT_e > 15) or (pT_mu > 10 & pT_e > 25), OS, dR > 0.4, >= 2 jets, >= 1 b jet | same |
| Weights | MCweight x lumi x prefire x PU x topPt x mu/e RECO x mu/e ID x trigger x PUJetID (x btag 1a in EMu) | MCweight x lumi x PU x e RECO (POG) x btag 1a (EMu). Our lepton ID and trigger SFs = 1 until measured (phases 2.3, 2.4; decided). No prefire, no PUJetID in Run 3. Top pT: open (D3) |
| Systematics | event loop: JetRes, JetEn, ElectronRes, ElectronEn, MuonEn, UnclusteredEn; weights: L1Prefire, triggers, PU, ID SFs, PUJetID, BtagSF x4; plus `<syst>_NotImplemented` lanes | event loop: JetRes, JetEn, ElectronRes, ElectronEn, MuonEn, MuonRes, UnclusteredEn; weights: PileupReweight, ElectronRecoSF, BtagSF (EMu only). `_NotImplemented` lanes kept for the V3 plotting |
| Output | `{DIMU,EMU}/{lane}/...` (muons, electrons, jets, bjets, METv, pair, pileup, weights), cutflow, jet eta-phi | same layout and names, so the V3 `DiLepton/python/plot.py` works with small changes |

## 2. Implementation

Analysis module `HcToWA_Analyzers` in branch `HcToWA_Run3` of the KNU SKNano checkout (auto-detected as `*_Analyzers`), C++ only.

- **`HcToWABase : AnalyzerCore`** (shared with the later TriLepton port)
  - Our lepton IDs, evaluated once per object per event into a bitmask (loose/tight); no string dispatch.
    - Electrons read the custom branches through `GetColumnHandle<T>(..., ColumnRequirement::Required)`: `Electron_{superclusterEta, superclusterPhi, superclusterEnergy, DeltaEtaInSC, DeltaPhiInSC, DeltaPhiInSeed, ecalPFClusIso, hcalPFClusIso, dr03HcalTowerSumEt}`. A missing branch fails the job.
    - The SKNano 2.0 built-in `HcToWA*` IDs are not used (electron variables are stubs; the muon tight ID compares `TkRelIso` with `0.4*Pt()`).
  - Jets, b tagging, MET, noise filters, jet veto map and golden JSON from SKNano 2.0, wrapped once.
  - b-tag method-1a event weight implemented here (SKNano 2.0 has none), with per-jet SFs and efficiencies computed once per event for nominal and each variation.
- **`DiLepton : HcToWABase`**: channels DiMu and EMu.

**Efficiency rules** (each addresses a measured problem in the old code):

1. **Weights.** Every weight factor (PU, e RECO, b tag) is evaluated once per event for nom/up/down. Weight lanes are products with one factor swapped, and `_NotImplemented` lanes divide one factor out. This replaces about 30 full `getWeights` calls per event.
2. **Event-loop variations rebuild only what changes.**
   - JES/JER: jets, b jets, MET.
   - Electron scale/smear: electrons, MET.
   - Muon scale/res: muons, MET.
   - UnclusteredEn: MET only.

   The varied pT values come directly from the views (`MomentumScaleUp`, `ScaleUpPt`, `JesPtUp`, ...), and selections are done on index lists, not object copies.
3. **Histograms** are booked once per (channel, lane) at initialization with `Hists(...).Book1D` handles, with no string formatting per fill. Lanes identical to Central are not booked: no prefire or PUJetID lanes, and b-tag lanes only in EMu.
4. **Lookups.** Gen particles are built once per event, and no `GetAll*()` calls happen inside the weight or variation loops. Correction references are cached at initialization if SKNano 2.0 looks them up by string per call (to be checked when implementing).
5. **Performance check.** Events per second and memory (condor `MemoryUsage`) are measured on one TTLL file with `RunSyst` and compared with GetEffLumi as the I/O floor.

## 3. Steps and gates

1. Module skeleton (CMake, LinkDef, `HcToWABase`, `DiLepton`), build on knu1, ctest. **Gate:** the analyzer appears in `analyzers.manifest`.
2. Object IDs.
   - Unit-style check on one 2024 file: fraction of muons/electrons passing loose and tight, compared with the same IDs evaluated from the raw branches in a standalone RNTuple script.
   - Electron trigger-emulation cuts checked on the custom branches.
   - **Gate:** no −999 or missing values.
3. Central DiMu and EMu on a small data and MC subset (`--reduction`). **Gate:** cutflow, m(mumu) peak and sane yields.
4. Systematic lanes and performance check (rule 5). **Gate:** every lane present, Central unchanged with `RunSyst`, throughput recorded.
5. Production on condor from knu1, `-n -100`:
   - Data: Muon0, Muon1 (DiMu); MuonEG (EMu).
   - MC: DY 2J FxFx (e, mu, tau; MLL 10-50 and 50), TTLL/TTLJ powheg, single top (t-ch lep, tW, s-ch), WW/WZ/ZZ pythia, W 2J FxFx.
6. Plots: port `ChargedHiggsAnalysisV3/DiLepton` plotting into this repository.
   - 2024 aliases (`config/sample_aliases_2024.json`), lumi from `HLT_Path.json`, groups W, Z, TT, ST, VV.
   - Per-object checks with each correction switched off in turn via the `_NotImplemented` lanes (PU, b tag, e RECO) and raw vs corrected pT (jets: rawPt/originalPt; leptons: MiniAOD pT).
   - Record findings in `LOG_ObjectID.md`.

## 3b. Z->ee check (`RunZEE`, decided 2026-11-24)

- **Selection:** EGamma0/1 data, `HLT_Ele30_WPTight_Gsf`; two opposite-sign electrons with our tight ID, leading pT above the trigger plateau; m(ee) window around the Z.
- **Simulation:** the same samples as the DiMu/EMu regions (decided 2026-11-24).
- **Proxy SFs:** official EGM single-electron trigger (`electronHlt.json`), ID (closest working point to our tight ID) and reconstruction SFs.
- **Histograms:** m(ee), electron pT/eta, uncorrected vs corrected, compared as normalized shapes.
- **Documentation:** the AN must state that these proxy SFs appear only in this validation region, not in the trilepton analysis.
- **Order:** submitted after the main production.

## 3c. Status (2026-11-24)

Steps 1-5 done (numbers in `LOG_ObjectID.md` and `LOG_Computing.md`). Differences from the V3 layout that the plotting must handle: lane `TopPtReweight_Applied` (new), one `BtagSF_NotImplemented` lane (V3: `BtagSF_HFcorr_NotImplemented`), `weights/*` only in Central, new `miniAODPt` lepton histograms, jet eta 50 bins over +-2.5. Next: step 6 (plots), with `PLAN_Plotting.md`.

## 4. Open decisions (user)

- **D1 (decided):** UParT Medium.
- **D2 (decided):** MC normalization `sign(genWeight) x xsec / sumSign`, as in B2G-25-013 (`MCweight(usesign=true)`). The `weights/genWeight` histogram is kept, to see where |genWeight| varies within a sample (where this differs from genWeight/sumW).
- **D3 (decided):** check the ttbar data/MC agreement with and without top pT reweighting: a dedicated weight lane. The old code had an analytic function; SKNano 2.0 offers ONNX models trained at 13 TeV (its own warning). Which one to use is to be fixed when implementing.
- **D4 (resolved from the JME/JERC pages in `docs/CMS/`):** add `Flag_ecalBadCalibFilter` for 2024; the jet veto map follows JERC Run 3 (no muon overlap), which SKNano 2.0 already does. Jet ID for analysis jets: Tight (user).
- **D5 (decided):** no lumi mask in the analyzer; the golden JSON was applied in the NanoAODv15 production.
- **D6 (decided):** module `HcToWA_Analyzers` in branch `HcToWA_Run3` of the KNU SKNano checkout (uncommitted).
