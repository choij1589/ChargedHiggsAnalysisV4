# BOARD

Feasibility study of B2G-25-013 with the **2024 data set alone** (NanoAODv15, RNTuple, SKNano 2.0 at KNU). Decisions and their reasons are in `docs/LOG_<Section>.md`; this board only tracks state. Updated 2026-11-27.

## Done

- SKNano 2.0 is installed at KNU in container-less mode: builds, ctest 7/7, submits from knu1. Patches are listed in `LOG_Computing.md`.
- Jobs read the inputs over xrootd, through the `/d0` input view (411k links; signal under `RNTuple/TTToHcToWA_AToMuMu/`).
- `CommonSampleInfo.json` (2024) is complete for all 127 KNU MC samples and the 5 data PDs:
  - cross sections from `config/xsec_2024.csv` (AN-25-154, MATRIX, LHCHWG arXiv:2402.09955, XSDB);
  - nmc, sumW and sumsign from GetEffLumi, checked against RNTuplizer.
- 2024 luminosity: 109.82 /fb (PPD table), set in the SKNano `HLT_Path.json`.
- Plotting library `Common/Tools/plotter.py` (styles `an`/`pw`) and the DiLepton plot scripts (`docs/PLAN_Plotting.md`).
- DiLepton analyzer (`HcToWA_Analyzers`, branch `HcToWA_Run3`, uncommitted) built and validated; DIMU, EMU and ZEE productions complete in `/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput/DiLepton/` (moved from /d0 2026-11-25).
- AN-26-267 is renamed, scoped to 2024, and builds (84 pages, 2026-11-27). Sections 1-4 (Introduction, Datasets, Object identification, Trigger) and their appendices finalized 2026-11-27 (an-writer): every TODO answerable from the outputs closed; 36 remain, each tagged user decision / later phase / not obtainable (`LOG_Dataset.md`, `LOG_ObjectID.md`, `LOG_Trigger.md` 2026-11-27).
- The `an-writer` agent and the `/an-section-update` skill are in place.

## On-going

- Skims (phase 2.1, 3.1): done 2026-11-27 (see Next step). Skim_TriLep and Skim_FakeRate (data + QCD) submitted 2026-11-26 (`hcto_prod/submit_skims.sh`, `LOG_Computing.md`). Skim_TriLep: first production removed 2026-11-25 (user: TnP first). Skim code patched and tested; resubmitted after the ID measurement. Skims compressed with ZSTD level 5 (user, 2026-11-25; 0.71 of the LZ4-1 size) (`LOG_Computing.md`).
- Phase 2.3, lepton ID SFs: plan in `docs/PLAN_LeptonID.md` (ntuples from our NanoAODv15, tnp_tamsa fits, POG 2024 setups); all decisions settled (L1-L8). Steps 1-2 done: `MuonTnPProducer` / `ElectronTnPProducer`, RNTuple->TTree conversion, tnp_tamsa configs and condor chain validated on test files (`LOG_ObjectID.md`, `LOG_Computing.md`). L4 revised 2026-11-25: measured on scale/smear-corrected pT. Step 3 done (TnP RNTuples on /pnfs). tnp_tamsa ported to NanoV15 (reads RNTuples, legacy RooFit backend; validated against CMSSW 6.26). Step 4 done: production fits of all 7 configs, fit checks and refits (`LOG_ObjectID.md` 2026-11-25). POG working points agree with the official 2024 SFs (muons to ~3e-4, electrons ~0.5-0.9%). Electrons: EGM alternative signal and EGM 2024 uncertainty rule (`combineElectronEGM.py`, `sf_egm.root`), uncertainties now match EGM's. Step 5 (user review of the SF maps, `LeptonID/plots/AN/2024/`) pending. Results stay on /d0 until the review, then go to /pnfs SKNanoOutput/TnP/2024/. Step 6: SFs applied in DiLepton (LepIDSF production done 2026-11-26: data/MC DIMU 0.944, EMU 0.941, ZEE 0.983; plots `DiLepton/plots/AN/2024/*_LepIDSF/`); final check by the user pending.

- Phase 2.4, trigger SFs: plan `docs/PLAN_Trigger.md`; decisions T1-T7 settled, step-2 decisions by the user 2026-11-26. Steps 1-2 done (legs, pairwise filters); step 3 done 2026-11-26: per-event SF in HcToWABase/DiLepton, TrigSF production (MC), DiLepton data/MC now DIMU 0.992, EMU 0.957, ZEE 0.983. Closure is a check (user): uncertainty from the measurements with the DZ spread (DblMu +0.18/-0.14%, EMu +0.31/-1.55%); EMU closure passes, DIMU inclusive fails (0.86% vs 0.21%) but closes under the TnP tag condition (IsoMu24 fired: 1.000 / 1.003, 4-file test); C_data = C_MC assumed (user), check on the IsoMu24 subset (`LOG_Trigger.md`). TrigDZ production done 2026-11-27 (lanes with the DZ uncertainty, closure subsets): all checks pass (DIMU on the IsoMu24 subset: DY 0.9987, tt 1.0018 vs sigma 0.20/0.27%; EMU tt 0.9968 vs 1.85%; C_MC 0.993/0.991); DiLepton plots on TrigDZ (DIMU, EMU; ZEE TrigSF). Open: AN text (still has the closure term); trilepton closure (signal, WZ) later.

- Phase 3.4, conversion SF: plan `docs/PLAN_ConvSF.md` (2026-11-27, survey of B2G-25-013); decisions C1-C6 settled 2026-11-27 (user; `LOG_BkgEst.md`); SR data blinded throughout the feasibility study (user). TriLepton analyzer (C++, SR blinded) tested and produced 2026-11-27; ConvSF measured (`TriLepton/python/measConvSF.py`): e mu mu 0.759 +- 0.078, mu mu mu 0.947 +- 0.126; DYG cross-check double counts internal conversions (overlap removal to fix, open); WZ CR data/pred 0.92 with an N_jet dependence (PLAN 3.5). SF accepted and JSON installed (user 2026-11-27); DYG comparison deferred to the next iteration. Next: AN conversion subsection.

- Phase 3.1-3.3, fake rates and closure: plan `docs/PLAN_BkgEst.md` (2026-11-25; StatComm: closure as pass/fail, uncertainty from measurement variations; new efficient MeasFakeRate analyzer); implemented and tested (`MeasFakeRate`, `Skim_FakeRate`, 2026-11-26); decided F5 (prompt normalization, no floor), F6 (skim data and QCD only), F9 (no trigger matching anywhere, 2026-11-26); F7, F8 decided 2026-11-27 (V4 bins, electron |eta_SC| 1.444, no merging, a negative bin takes the previous pT bin's rate; electrons EMEnriched + bcToE, disjoint, muons MuEnriched); F1-F4 after the first rates.

## Next step

- Order (user, 2026-11-25): implement and test Skim_FakeRate + MeasFakeRate (PLAN_BkgEst step 1); then 1. finalize DiLepton and its AN sections, 2. skims (Skim_TriLep and Skim_FakeRate together), 3. fake-rate measurement and closure.

- User review of the DiLepton plots (`DiLepton/plots/AN/2024/`, TrigDZ production (ZEE TrigSF), all corrections in Central; findings in `LOG_ObjectID.md`, `LOG_Trigger.md`): data/MC DIMU 0.992, EMU 0.957, ZEE 0.983; PU modelling open.
- Fake-rate measurement production (PLAN_BkgEst step 2) done 2026-11-27 09:03 (`hcto_prod/submit_measfr.sh`, 971 jobs, all status 0; outputs synced; `LOG_BkgEst.md`). Rates script `MeasFakeRate/python/measFakeRate.py` (gate + rates, 2026-11-27; results `MeasFakeRate/results/2024/{mu,el}/`): prompt scale from the MT template fit bounded to the Z-window scale +-30%, uncertainty |s_fit/s_Z - 1| (user 2026-11-27); bin-by-bin rate uncertainty accepted (user); tt rerun without the top pT weight done 10:58 (effect < 0.7%), final rates by `MeasFakeRate/run_rates.sh`; AN fake-rate part being finalized (an-writer, without the Z+nonprompt plots); rates, plots and correctionlib JSON (`MeasFakeRate/results/2024/fakerate_HcToWA.json`) ready for the user review (step-3 gate). Decided 2026-11-27: F2 (no transfer correction), F3 (closure: yield + shape tests with QCD-MC rates), no top pT reweighting (MeasFakeRate tt rerun 10:17), MT/MET shape closed. F1 (one shape nuisance per flavour, central +- bin-by-bin total) and F4 (eps_p = 1, quantified) decided; all F decisions settled. F4 quantified by the closure only (user). MC closure done 2026-11-27 (`ClosFakeRate` analyzer, `evalClosure.py`): mu mu mu PASS, e mu mu FAIL in the yield test (1.084 +- 0.079, 1.07 sigma; shape PASS); documented in AN-26-267 (106 pages); e mu mu kept as is for the feasibility study (user 2026-11-27); prompt subtraction method revisited in the next revision round, after the full limit calculation. AN BkgEst nonprompt subsection drafted (numbers pending). Next: prompt scales, Z/W-region data/MC, nPV check (step-2 gate), then the rates.
- Skims complete 2026-11-27 07:48 (`LOG_Computing.md`): Skim_TriLep data/MC and Skim_FakeRate data/QCD, all DAGs status 0, 155 skim JSONs (16653 trees). Fixes: columns common to the job's files (data), 19 MC files regenerated, 3 FakeRate data trees accepted (user), stage-out with `--posc`, retries and checksum (user, 2026-11-27). Next: fake-rate measurement (MeasFakeRate on the skims + prompt MC).
- Still open for the user (`LOG_Dataset.md`): DY 10-50 (XSDB per-flavour records lack the /3) and s-channel single top (2.360/1.477 from the cited NNLO reference vs AN-25-154's 3.7/2.322).

## Phase index

Used by the `%% TODO` tags in AN-26-267 (e.g. "PLAN 2.6").

| Phase | Scope |
|---|---|
| 0 | SKNano at KNU: install (0.1), input view (0.2), sample metadata (0.3), condor smoke test (0.4) |
| 1 | HcToWA analyzers ported to an SKNano 2.0 analysis module |
| 2 | Objects and efficiencies: skims (2.1), DiLepton (2.2), lepton ID SFs (2.3), trigger (2.4), b-tag efficiency (2.5), jet requirements with the PUPPI fix (2.6) |
| 3 | Backgrounds: fake rates (3.1), prompt rates / matrix method (3.2), closure (3.3), ConvSF (3.4), WZ with FxFx (3.5), single-source normalization uncertainties (3.6) |
| 4 | Signal at mH+ = 130 GeV: shape fits (4.1), grid density (4.2), A-candidate assignment (4.3) |
| 5 | ParticleNet: retrain with 2024 (5.1), parameterized in mA (5.2), output categories (5.3) |
| 6 | Statistics: 2024-only expected limits (6.1), combination option (6.2), uncertainty breakdown and LEE (6.3), feasibility verdict (6.4) |
