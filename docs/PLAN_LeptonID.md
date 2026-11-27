# PLAN: lepton ID scale factors for 2024 (phase 2.3)

Goal: measure the data/MC efficiency and scale factor of our tight muon and electron IDs with tag and probe in Z -> ll, for 2024, and apply them in the analysis. Written 2026-11-24 from a survey of the B2G-25-013 measurement; decisions in `LOG_ObjectID.md`.

## 1. What is reproduced (B2G-25-013 Run 3)

The previous measurement used the private RooFit framework **tnp_tamsa** (`choij1589/tnp_tamsa`, copy on KNU in `/d0/scratch/choij/tnp_tamsa`), configs `TopHNT_Muon_Run3_v0.py` and `TopHNT_Electron_Run3_v1.py`. Only the **tight** ID ("TopHNT") was measured, as one step covering ID, isolation and impact parameters; the SF is applied to tight leptons only. Reconstruction SFs come from the POGs (electrons: EGM RECO; muons: none in Run 3).

| | Muons | Electrons |
|---|---|---|
| Ntuple | SKNano `MuonTnPProducer` (NanoAOD v12/13), tree `muon/Events` | EGM TnPTreeProducer (MiniAOD, CMSSW), tree `tnpEleIDs/fitter_tree` |
| Tag | POG tight, pfRelIso04 < 0.2, matched to IsoMu24, pT > 26, \|dxy\| < 0.2, \|dz\| < 0.5 | pT > 32, \|eta_SC\| < 2.5 outside the gap, mT(tag, MET) < 45; for probes with pT < 20 also tag MVA iso > 0.9 |
| Pair | opposite sign, m > 50, exactly one probe per tag | opposite sign |
| Probe (denominator) | tracker muon, \|dxy\| < 0.2, \|dz\| < 0.5 | reconstructed GSF electron |
| Passing (numerator) | Medium, \|dz\| < 0.1, SIP3D < 3, TkRelIso < 0.4, miniIso < 0.1 | MVA noIso WP90, miniIso < 0.1, SIP3D < 4, \|dz\| < 0.1, lostHits < 2, conversion veto, trigger emulation (EA 0.16544/0.05956 barrel, 0.13212/0.13052 endcap) |
| Binning | \|eta\| [0, 0.9, 1.2, 2.1, 2.4] x pT [10, 15, 20, 25, 30, 40, 50, 60, 120, 200] | eta_SC [-2.5, -2, -1.566, -1.444, -0.8, 0, ...mirrored] x pT [10, 15, 20, 35, 50, 100, 200, 500] |
| Nominal / alternative MC | MG LO / amc@NLO | amc@NLO / MG LO |
| Fit | m(ll) 70-110 GeV: gen-matched MC template (x) Gaussian; RooCMSShape background; pass and fail fitted separately, data and MC | same model, 60-120 GeV |
| Systematics | alternative signal (Crystal Ball), alternative background (exponential), alternative MC, tag iso 0.1/0.3, mass bins 50/200, fit window shifted | alternative signal, background, MC (deployed files also had tag pT > 37 and the fit window +-3 GeV) |
| Uncertainty | per set the largest deviation, sets in quadrature with stat; SF up/down = nominal +- total | same |
| Output | `efficiency.root` -> correctionlib JSON (`data`, `sim`, `sf`; inputs abseta or sceta, pt, syst) -> `MyCorrection::Get{Muon,Electron}IDSF("TopHNT")` | same; electron pT clamped at 99 GeV in Run 3 |

AN-25-154: `Sections/ObjectID.tex:96-103` (electrons), `:206-211` (muons); the AN text and the configs differ in a few muon fit details (mass binning, window), to be settled from the configs.

## 2. Design for 2024 (decided: ntuples from our NanoAODv15, user 2026-11-24)

- **Producers in `HcToWA_Analyzers`** (SKNano 2.0, branch `HcToWA_Run3`):
  - `MuonTnPProducer`: port of the old one (`SKNanoAnalyzer/Analyzers/src/MuonTnPProducer.cc`), same branch names so the muon config carries over. Tag trigger match via TrigObj (bit meanings checked for v15). Probe flags for the double-muon legs (Mu17, Mu8) are kept for phase 2.4.
  - `ElectronTnPProducer`: new. Probe = NanoAOD electron; tag = tight electron matched to `HLT_Ele30_WPTight_Gsf`. The probe carries every input of our ID (MVA noIso WP90, miniIso, SIP3D, dz, lostHits, conversion veto, the trigger-emulation variables from the v15 custom branches), so the numerator is exactly the analysis ID, computed by the same code as in `HcToWABase`.
  - One entry per tag-probe pair; gen matching (dR < 0.2, closest relative pT) and `pair_gen_mass` for the MC templates; genWeight and PU weight stored.
- **Consistency gain over B2G-25-013 (electrons):** the old electron ntuples were MiniAOD-based, so e.g. `dr03TkSumPt` was filled at all pT, while the NanoAOD analysis sees 0 below 35 GeV (`LOG_ObjectID.md`). Measuring on NanoAOD makes the SF describe the ID that is applied.
- **Format:** SKNano 2.0 writes RNTuples only; tnp_tamsa reads TTrees (`TChain` + `TTreeFormula`). A conversion script (RDataFrame `Snapshot` to TTree, merged per sample) sits between them. tnp_tamsa is not modified beyond its setup.
- **tnp_tamsa on KNU:** fix `TNP_BASE` in `setup.sh`; check its condor submission on knu1 (no `SingularityImage`, inputs on `/d0`, no proxy needed). New configs `HcToWA_Muon_2024.py` and `HcToWA_Electron_2024.py` in the tnp_tamsa checkout.
- **Samples:** data Muon0/Muon1 (muons) and EGamma0/EGamma1 (electrons), periods C-I; MC DYto2Mu/DYto2E 2Jets amcatnloFXFX and 4Jets madgraphMLM (MLL 50; MLL 10-50 not needed in the 70-110 GeV window), both available at KNU.
- **Application:** convert `efficiency.root` to correctionlib JSON in `data/Run3_v15_Run2_v15/2024/{MUO,EGM}/efficiency_HcToWA.json`; `HcToWABase` loads it directly (correctionlib) and provides the tight-lepton SF with nominal/up/down, as lanes `MuonIDSF` and `ElectronIDSF` in DiLepton. No framework change.

## 2b. Measurement setup: follow the POG 2024 central measurements (decided, user 2026-11-24)

**Muons** follow the MUO 2024 medium-pT measurement (`docs/CMS/MUO/MUO_MediumPt_SFs_2024_20250519.pdf`, summary in `docs/CMS/MUO/README.md`), with our tight ID as the numerator over TrackerMuons:

| | 2024 (MUO central setup) | change from B2G-25-013 Run 3 |
|---|---|---|
| Tag | tight ID, pT > 26, PF iso (dR 0.4) < 0.2, matched to IsoMu24, \|dxy\| < 0.2, \|dz\| < 0.5, pair_probeMultiplicity, !probe_isDuplicated | adds !probe_isDuplicated |
| Probe | TrackerMuons with the same IP cuts (MUO probes general tracks; ID WPs are measured over TrackerMuons) | same |
| Binning | signed eta [-2.4, -2.1, -1.6, -1.2, -0.9, -0.3, -0.2, 0.2, 0.3, 0.9, 1.2, 1.6, 2.1, 2.4] x pT [10, 15, 20, 25, 30, 40, 50, 60, 120, 200] | 13 signed eta bins instead of 4 \|eta\| bins |
| Signal | MadGraph LO DY template (x) Gaussian | nominal MC MadGraph LO (as before) |
| Background | RooCMSShape | same |
| Fit | 70-110 GeV, 80 mass bins | 80 instead of 100 bins |
| Systematics | tag iso < 0.3 / < 0.1; mass bins 160 / 40; mass range 75-115 / 65-105; alternative signal template amc@NLO DY; alternative background exponential | no Crystal Ball alternative; the alternative MC is the alternative signal (in tnp_tamsa it swaps the whole simulation, template and MC efficiency, as B2G-25-013's altmc; user 2026-11-24); window shifted by 5 GeV instead of +-3 |

The 2024 MC: MadGraph LO = DYto2Mu 4Jets madgraphMLM (MLL 50), amc@NLO = DYto2Mu 2Jets amcatnloFXFX (MLL 50).

**Electrons** follow the EGM 2024 electron ID measurement (`docs/CMS/EGM/EGM_EleID_SFs_2024_20250704.pdf`, summary in `docs/CMS/EGM/README.md`), with our tight ID as the numerator over reconstructed electrons:

| | 2024 (EGM central setup) | change from B2G-25-013 Run 3 |
|---|---|---|
| Tag | OR of HLT_Ele32_WPTight_Gsf, HLT_Ele115_CaloIdVT_GsfTrkIdT, HLT_Photon200 (all in the 2024 files); cut-based tight ID; pT > 35 GeV, \|eta\| < 2.5; opposite charge; **tag outside the ECAL gap** 1.4442 < \|eta_SC\| < 1.566 (user 2026-11-24, as B2G-25-013; EGM does not veto it) | was pT > 32, mT(tag, MET) < 45, tag MVA iso for low-pT probes |
| Probe | NanoAOD electron, pT > 10 GeV, \|eta\| < 2.5, dR(tag, probe) > 0.1 | dR cut new |
| Binning | eta_SC [-2.5, -2.0, -1.566, -1.4442, -0.8, 0, 0.8, 1.4442, 1.566, 2.0, 2.5] x pT [10, 20, 35, 50, 70, 100, 200, 300]; above 300 GeV the 200-300 SF with an uncertainty growing linearly to 1 TeV; the two gap columns are not fitted (our ID rejects the gap; left at 0 in `efficiency.root`, set to 1 in the JSON, never looked up) (user 2026-11-24) | pT 50-70 and 70-100 split (was 50-100) |
| MC | DYto2E 2Jets MLL-50 amcatnloFXFX; DYto2E 4Jets MLL-50 madgraphMLM (LO) produced as a separate alternative-MC cross-check, not in the systematic set (user 2026-11-24) | nominal amc@NLO (as before) |
| Fit | EGM framework model: MC template (x) Gaussian, RooCMSShape background (as tnp_tamsa's nominal) | - |
| Systematics | alternative signal fit, alternative background fit (data) | no alternative MC, tag pT or window variations |

Above 100 GeV EGM uses pT(ll)-binned DYto2L samples that are not converted at KNU; we measure 100-200 and 200-300 with the inclusive sample and extrapolate above 300 GeV as EGM proposes (L8).

## 3. Steps and gates

1. **tnp_tamsa on KNU.** Setup and a condor smoke test on a toy tree. **Gate:** hist, fit and sum steps run on knu1 condor.
2. **Producers.** Port `MuonTnPProducer`, write `ElectronTnPProducer`, conversion script. **Gate:** on one data and one DY file, the pair mass peaks at the Z, the tag and probe counts are sane, every ID input is filled (no -999), the numerator reproduces the analysis ID on the same events.
3. **Production** on condor from knu1 (all 2024 data periods of the four PDs, DY 2J and 4J). **Gate:** all outputs present, event counts per sample recorded.
4. **Validation with POG working points.** Measure POG Medium (muons) and MVA noIso WP90 (electrons) with our ntuples and compare with the official 2024 POG SFs, as the old `POGMuon*`/`POGElectron*` configs did. **Gate:** agreement within the uncertainties, or understood differences.
5. **Tight-ID measurement** with the full systematic set; check fit status, refit bad bins. **Gate:** all bins converged; SF and uncertainty maps reviewed with the user.
6. **Application.** JSON, SF in `HcToWABase`, rerun DiLepton, compare DIMU/EMU data/MC before and after. **Gate:** user review.
7. Record in `LOG_ObjectID.md`; AN section via `/an-section-update ObjectID`.

## 4. Open decisions (user)

- **L1 (decided):** ntuples from our 2024 NanoAODv15 with SKNano 2.0 producers (option 2); the old `MuonTnPProducer.cc` is the starting point.
- **L2 (decided, POG setups):** muons MadGraph LO (4Jets MLM) nominal, amc@NLO (2Jets FxFx) alternative; electrons amc@NLO (DYto2E 2Jets MLL-50) only.
- **L3 (decided, user):** MC templates and efficiencies weighted with genWeight x PU weight, for both leptons (B2G-25-013 muons used genWeight only).
- **L4 (decided, user; revised 2026-11-25):** SFs measured and applied in the scale/smear-corrected pT, with the corrected pair mass in the fits (`*_cor` ntuple fields). The 2026-11-24 choice (uncorrected NanoAOD pT, as B2G-25-013 did for muons with `OriginalPt`) is superseded.
- **L5 (decided, EGM setup):** electron tag = OR of Ele32 WPTight, Ele115, Photon200, cut-based tight, pT > 35 GeV. (Superseded proposal: The 2024 single-electron trigger is `HLT_Ele30_WPTight_Gsf`; proposed tag pT > 35 GeV (above the turn-on; B2G-25-013 used 32), alternative 38 GeV as a systematic.)
- **L6 (decided, POG setups):** muons tag iso, mass bins, mass range, alternative signal template (amc@NLO), alternative background; electrons alternative signal and background fits.
- **L7 (decided, POG setups):** muons signed eta (13 bins) x pT (9 bins); electrons eta_SC (10 bins) x pT [10, 20, 35, 50, 70, 100, 200, 300] (L8).
- **L8 (decided, user):** electron pT bins [10, 20, 35, 50, 70, 100, 200, 300] GeV, all from the inclusive DYto2E 2Jets MLL-50 sample. Above 300 GeV the 200-300 SF is used with an uncertainty growing linearly to 1 TeV (the EGM 2024 prescription). Statistics (Z->ee region, 2024): ~600k data / ~300k effective MC probes in 100-200, ~40k / ~20k in 200-300. Share of e-mu electrons: 11.3% in 100-200, 0.9% in 200-300, 0.14% above 300 GeV.
