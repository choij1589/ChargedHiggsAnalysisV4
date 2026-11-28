# LOG: SystUnc

Decisions and findings for the Systematic uncertainties section of AN-26-267: the nuisance parameters of the datacards, their sources, sizes, correlation naming and impacts. Newest entry first.

## 2026-11-28 (S6 decided)

- **S6 (user):** `lumi_2024` lnN 1.016 (LUM 2024 preliminary 1.6%, CERN-CMS-DP-2026-003); the luminosity stays 109.82 /fb from PPD (the B2G/LUM page may not be up to date). `configs/systematics.2024.json` (SRS aafed83); limits rerun with output tag `HcToWABTagEff_v2` (cluster 2256095, 14:55).
- **B2G statistics tests** (pulls, blinded GoF with a measurement region, signal injection, F-test note): after the KNU downtime (user).

## 2026-11-28 (LUM recommendation, copy in docs/CMS)

- **Source:** `docs/CMS/LUM_LumiRecommendationsRun3.md` (LumiRecommendationsRun3 TWiki, 2024 entry "updated Dec./2025", provided by the user 2026-11-28; identical to `docs/AN-26-267/docs/LumiRecommendationsRun3_CMS_TWiki.md`).
- **2024 alone:** preliminary uncertainty 1.6% (cite CERN-CMS-DP-2026-003, cds 2952191); brilcalc with `normtag_PHYSICS.json`. For a 2024-only datacard: one `lumi_2024` lnN 1.016 (replaces the 1.020 placeholder). The lumi_1/2/3 split (2024: 1.0020 / 1.0068 / 1.0144; 2023+2024 scheme 1.0161) applies only to combinations with 2022/2023 (PLAN 6.2).
- **Central value:** the LUM combination quotes 110.11 +- 1.77 /fb for the 2024 Golden JSON; we use 109.82 /fb (PPD table, `LOG_Dataset.md`), 0.26% lower. To check with brilcalc on our JSON (normtag_PHYSICS) before the final numbers (S6, user).

## 2026-11-28 (AN: first version of the section, an-writer)

- **Written** in `docs/AN-26-267/Sections/SystUnc.tex`. The section was empty headers before this.
  - Introduction and the correlation naming: `_2024` per era, `_13p6TeV` per Run, no suffix for all periods, as in AN-25-154.
  - Summary table `tab:SystUncSummary`: 40 rows with name, type, processes, and the yield change of the signal and of the total background per channel, as the min-max over the 23 points.
  - Subsections:
    - nonprompt (`ssec:NonpromptSyst`, new label): per-flavour effects on the nonprompt yield;
    - conversion (`ssec:ConvSFSyst`): lnN 1.103 / 1.133, the shape-to-lnN fallback values;
    - WZ (`ssec:WZSyst`): 12% lnN, correlated between the channels;
    - experimental (`ssec:ExpSyst`): lumi placeholder, pileup, lepton scale and resolution, ID and reco, trigger, JES and JER, b tagging, unclustered, and the Run 2 items not used;
    - theory (`ssec:TheoryUnc`): tt cross-section lnN placeholder, muF, muR, PDF, alpha_s, ISR, FSR with the generator-level normalization, and the prompt cross sections;
    - interpolation (`ssec:InterpUncSummary`): names and rules; not in the mc-signal datacards;
    - template statistics (`ssec:MCStatSyst`, new label);
    - impacts (`ssec:SystImpacts`, new label) with Fig. `fig:SystImpacts`: four noMCStat impact plots copied to `docs/AN-26-267/Figures/SystUnc/2024/`.
  - Target build compiles. Only cross-section references are undefined. Three small overfull boxes remain (table and two paragraphs, up to 16 pt).
- **Sources:**
  - `SignalRegionStudy/configs/{systematics.2024.json, chain.json, samplegroups.json}`, `python/{printDatacard.py, sample_reader.py, binned_template_core.py, makeBinnedTemplates.py, interpolation_config.py, param_signal.py}`, `scripts/runImpacts.sh`, `docs/PORT.md` (SRS 4cf23a2).
  - The 69 datacards, `lowstat.json`, and `shapes{_original,}.root` of `SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v1/templates/MHc130_MA*/Baseline/mc-signal/2024/` (local copy of /pnfs).
  - `SignalRegionStudy/results/json/impacts_asimov/mc-signal/MHc130_MA{30,60,90,110}.Combined.impacts.json`.
  - `SignalRegion/plots/AN/2024/impacts/*_noMCStat.png` (13:39).
  - `SignalRegionStudy/results/interpolation/closure/loo_uncertainties.json`.
  - The analyzer `~/Sync/workspace/SKNanoAnalyzer_Run3/HcToWA_Analyzers/src/TriLepton.cc:661` (c657425).
  - Yield changes were computed with scratch scripts (`syst_sizes.py`, `np_sizes.py`, `shape_shift.py`, `pu_contrib.py`, NanoV15 ROOT 6.40). They take the template integrals in the window.
- **Numbers:**
  - Signal yield changes:
    - b-tag bc correlated 2.1-2.5%;
    - JES 0.8-2.2%;
    - pileup 0.2-2.1%;
    - electron ID 1.4-1.7%;
    - EMu trigger +0.5 / -1.7%;
    - muon ID 0.4-1.1%;
    - electron reco 0.5-0.8%;
    - DblMu trigger +0.2 / -0.2%;
    - theory after the generator normalization: muF up to 0.7%, PDF and alpha_s up to 0.1%, ISR up to 1.0%, FSR up to 1.8%.
  - Muon scale moves the signal mean by at most 7e-5 relative. Muon resolution changes the RMS by at most 0.3%.
  - Nonprompt yield changes:
    - mu nuisance: e mu mu +6..+13 / -5..-12%, mu mu mu +13..+21 / -12..-18%;
    - el nuisance: e mu mu +1..+19 / -1..-16%, mu mu mu 0.
  - The nonprompt background is 37-73% (e mu mu) and 54-73% (mu mu mu) of the window background.
  - Impacts (Asimov, r = 1):
    - nonprompt mu leads at all four points: 0.040, 0.072, 0.18, 0.058. It is constrained to 0.57-0.77, and el to 0.74 / 0.81 at MA90 / 110.
    - tt xsec 0.043-0.044 away from the Z.
    - MA90: Norm_others 0.10, ttZ 0.080, JES 0.077, b-tag bc 0.083.
    - Signal theory impacts are below 0.01.
    - There are 28-47 autoMCStats parameters.
- **Mismatches / findings:**
  - **The lumi placeholder is in the limits.** `lumi_2024` lnN 1.020 is in all 69 datacards and in the impacts (0.022-0.064). `LOG_Result.md` (2026-11-28) says "No luminosity uncertainty yet". The expected limits of that entry include the 2% placeholder. The AN states this. The copy of the LUM TWiki in `docs/AN-26-267/docs/LumiRecommendationsRun3_CMS_TWiki.md` (copied 2026-11-24, "updated Dec./2025") gives a preliminary 2024 uncertainty of 1.6% (CMS-DP-2026-003) and a 2022+2023+2024 split (lumi_1/2/3: 1.0020, 1.0068, 1.0144 for 2024). Not applied. That is S6, a user decision.
  - **The unclustered-energy nuisance has no effect.** Its templates equal the nominal in every bin at all points, because the SR (`nJ >= 2 && nB >= 1`) and the dimuon mass do not use ptmiss. It is kept in the datacards and is harmless. The AN says so.
  - **The PDF prescription.** The signal uses lhaid 325300 (NNPDF31_nnlo_as_0118_mc_hessian_pdfas), which is a Hessian set. The code takes the bin-by-bin envelope (max/min) of the 100 members (`createEnvelopeHists`), as V4 did. AN-25-154 calls these "100 replicas" with an envelope "following PDF4LHC". PDF4LHC prescribes the quadrature sum for Hessian sets. The effect is negligible (≤ 0.1% yield, impact ≤ 2e-4). The AN states what the code does and has a user-decision TODO.
  - **Conversion fallback lnN.** The fallback is applied at 15 (e mu mu) and 17 (mu mu mu) points. It turns statistical fluctuations of the varied conversion templates into normalization terms, up to 1.30 (e mu mu) and 1.72 (mu mu mu) for pileup and up to 1.18 / 1.19 for JES. The pileup change of the total background (up to 5.7%) comes from these templates: SR1E2Mu MA30 conversion contributes +4.8 of +5.2%, SR3Mu MA20 +6.2 of +5.7%.
  - **The mu mu mu conversion nuisance name** is era-specific (`_SR3Mu_2024`). AN-25-154 shared it between Run 2 and Run 3. This matters only for a combination (PORT.md open point 6).
  - **SR3Mu nuisances with no effect.** `CMS_B2G25013_nonprompt_el_2024` is listed for the nonprompt column in SR3Mu but has zero effect, since there is no electron. The electron scale and resolution apply in SR3Mu with an effect below 0.05%. Both are harmless.
  - **gg -> H -> ZZ -> 4l** is in `others` (50%). AN-25-154 gave it 5% separately. The ttW, ttZ, ttH and tZq values are the 13 TeV values of AN-25-154.
  - **The muon resolution nuisance is new.** AN-25-154 had one "muon pT scale, resolution" row and the V4 config had the scale only.
- **Open:**
  - user decision: 2024 luminosity uncertainty and nuisance structure (S6). The datacards and the limits use the 1.020 placeholder (PLAN 6.1).
  - information to log: the source of the tt cross-section lnN 1.044 and of the 923.6 pb citation (`chain.json` TODO) (PLAN 6.1).
  - user decision: PDF prescription for the Hessian set 325300, envelope or quadrature sum. Negligible effect (PLAN 6.1).
  - user decision: 2024 pileup recommendation and the residual nPV shift. This is the same item as `LOG_ObjectID.md` (PLAN 2.2).
  - next iteration: smoothing or symmetrizing the conversion fallback lnN terms, with the heavy-weight conversion events (`LOG_TmpCnstrct.md`, `LOG_Result.md`) (PLAN 6.1).
  - later phase: interp-signal datacards with `CMS_interp_{scale,res,norm}_{SR1E2Mu,SR3Mu}_2024`, after 2026-11-30 (PLAN 4.2, 6.1). ParticleNet interpolation terms (PLAN 5.3).
  - later phase: correlation naming with 2022-2023, including the mu mu mu conversion (PLAN 6.2). Grouped uncertainty breakdown (PLAN 6.3). JES sources split if JES leads after ParticleNet (PLAN 6.3). 13.6 TeV values of ttW, ttZ, ttH and tZq (PLAN 3.6). Trilepton trigger closure (PLAN 2.4).
