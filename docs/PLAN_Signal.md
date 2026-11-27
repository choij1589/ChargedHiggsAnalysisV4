# PLAN: Signal, templates and Baseline limits (phases 2.5, 4, 6.1)

Plan of 2026-11-27 for the step after the background estimation (user, 2026-11-27: signal and limits with the Baseline selection before ParticleNet). Decisions are logged in `LOG_TmpCnstrct.md` (method, A candidate), `LOG_ObjectID.md` (b tagging), `LOG_Result.md` (limits) when they happen.

## Decided

- **Order (user):** b-tag efficiencies -> signal at mH+ = 130 GeV -> expected limits with the Baseline selection (SR without ParticleNet) -> ParticleNet (phase 5) with the same templates.
- **Method (user):** binned shape templates of `docs/previous_analysis/ChargedHiggsAnalysisV3/SignalRegionStudyV4`: DCB fit of the signal per mass point and channel -> x0, sigma_eff = sqrt((sigma_L^2 + sigma_R^2) / 2); window x0 +- 10 sigma_eff (lower edge >= 12 GeV); n_core uniform bins in +-5 sigma_eff plus one sideband bin on each side; n_core scanned 15 -> 5 until every background bin has n_eff >= 5 (`template_utils.py:298`, `binned_template_core.py:470`).
- **mu mu mu A candidate (user):** the previous rule is nominal: the higher-mass opposite-sign pair iff mH+ >= 100 GeV and mA >= 60 GeV, else the lower-mass pair (`SignalRegionStudyV4/python/preprocess.py:327`). For mH+ = 130 GeV: lower pair for mA < 60, higher pair for mA >= 60. Other options are studies (step 2.4).
- **SR data stay blinded:** expected limits on Asimov data only (`--blind` of the V4 chain).

## What exists

- Signal skims `Skim_TriLep_TTToHcToWAToMuMu-MHc130_MA{15,20,...,125}` (23 mass points), already in the TriLepton production (SR histograms only).
- TriLepton SR (>= 2 jets, >= 1 b) with the nonprompt (fake weight Central / Total_Up / Total_Down), conversion (ConvSF) and prompt MC estimates; weights C5; no systematic lanes besides the nonprompt ones.
- b tagging: UParT Medium 0.1272, method 1a; efficiencies from `2024/BTV/btaggingEff.json` (another analysis's selection: approximate until phase 2.5, `LOG_ObjectID.md`). SKNano has the converter `scripts/makeTaggingEffJson.py` (histogram keys `tagging#b##era#..##tagger#..##working_point#M##flavor#F##systematic#central##{num,den}`), but no analyzer in our tree fills those histograms.
- Previous chain: SignalRegionStudyV4 (preprocess -> binned templates -> datacard -> validation -> asymptotic limits), CMSSW_14_1_0_pre4 + Combine v10 (ROOT 6.30; newer ROOT segfaults its template making). CMSSW_14_1_0_pre4 is on /cvmfs at KNU (el9_amd64_gcc12); Combine has to be built in a CMSSW area on /d0 (code only).
- Previous systematics (`SignalRegionStudyV4/configs/systematics.2023.json`): lumi, pileup, muon scale and ID, electron scale, resolution, ID and reco, trigger, JES, JER, unclustered MET, b tagging (light / bc, correlated / uncorrelated), normalizations (nonprompt per channel, WZ N_jet SF shape, ZZ, ttW, ttZ, ttH, tZq, others, conversion per channel), signal theory (muF, muR, 100 PDF members, alpha_s, ISR, FSR).

## Steps and gates

### 1. b-tag efficiencies (phase 2.5)

1. Fill num / den histograms per flavour (0, 4, 5) in pT x |eta| for the jets of the selection (S1), in the key format of `makeTaggingEffJson.py`, in a small `MeasJetTagEff` mode (S1) on the Skim_TriLep MC.
2. Convert with `makeTaggingEffJson.py`, install in `HcToWA_Analyzers/data/2024/BTV/`, point HcToWABase at it.
3. Rerun TriLepton (V3) and DiLepton EMU; compare N_b and the SR yields with the current efficiencies.

Gate: user review of the efficiency maps and of the change of the SR prediction.

### 2. Signal at mH+ = 130 GeV (phase 4)

1. **SR tree mode in TriLepton (S3):** for the SR, one TTree per systematic variation in the format of the V4 preprocess (`mass` (selected pair), `mass1`, `mass2`, `pT`, `weight`), for signal and prompt MC (Central and variations), the data nonprompt lane (Central and its variations), conversion MC (ConvSF applied); no tight data in the SR. Signal adds the generator-matched A pair (for 2.4).
2. **Systematic lanes (S4, S5):** the variations of the list above that exist in 2024 (Table in S4), as weight lanes or object variations.
3. **Signal fits:** DCB per mass point and channel (V4 `makeBinnedTemplates.py` fit), x0 and sigma_eff vs mA, signal efficiency vs mA; comparison with 2022-2023 (AN-25-154).
4. **mu mu mu pairing study:** with `mass1`, `mass2` and the matched pair: fraction of signal with the A pair picked by the nominal rule, fraction of signal and background events with both pairs in the window, signal efficiency and background gain of option (1) "pair inside the window" (`LOG_TmpCnstrct.md`). Study only.

Gate: user review of the signal fits, efficiencies and the pairing study.

### 3. Expected limits with the Baseline selection (phase 6.1)

1. Port the V4 chain into this repository (`SignalRegionStudy/`, self-contained, one era 2024, channels SR1E2Mu, SR3Mu, Combined; S7). Read the TriLepton trees directly (the preprocess step becomes a reader).
2. Templates, datacards, validation, asymptotic expected limits (blind) per mass point; impacts on Asimov.
3. Compare with the 2022-2023 expected limits of B2G-25-013 scaled to the luminosity (109.8 vs 62 /fb).

Gate: user review; then the feasibility verdict inputs (phase 6.4) and ParticleNet (phase 5).

## Open decisions

- **S1 b-tag efficiency selection and samples:** (a) jets of the TriLepton preselection (3 leptons, all MC, low statistics), (b) Skim_TriLep loose preselection, all MC summed, (c) ttbar-dominated selection (DiLepton EMU, most statistics, different flavour mix). Recommendation: (b), with (a) as a check.
- **S2 mass points:** the 23 generated points MHc130_MA15-125 in 5 GeV steps; the previous baseline list for MHc130 (15, 30, 55, 83, 85, 90, 95, 100, 112, 125) includes interpolated points. Recommendation: the 23 generated points, no interpolation in the feasibility study.
- **S3 producer:** tree mode in TriLepton (one SR definition for histograms and templates) or a separate analyzer. Recommendation: TriLepton flag `SRTree`.
- **S4 systematic scope:** the full previous list, or a reduced set for the feasibility study (normalizations, lumi, b tagging, JES / JER, lepton ID / trigger, nonprompt, signal theory scale / PDF), the rest added later. Recommendation: the full list where the inputs exist in 2024, document the missing ones.
- **S5 nonprompt nuisances in the templates:** F1 decided one shape nuisance per flavour (central +- bin-by-bin total); needs per-flavour Nonprompt lanes (now Total only) or the previous per-channel lnN (15% / 30%) as a fallback.
- **S6 2024 luminosity uncertainty:** value and correlation scheme (LUM POG 2024 recommendation).
- **S7 chain environment:** CMSSW_14_1_0_pre4 + Combine v10 at KNU, as the previous analysis (recommended), or a newer Combine.
- **S8 signal normalization:** limits on BR(t -> H+ b) x BR(H+ -> W A) x BR(A -> mu mu) as in B2G-25-013 (`SignalRegionStudyV4/docs/XSEC_RECOMPUTATION.md`), with the 2024 ttbar cross section.
