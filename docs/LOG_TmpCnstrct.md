# LOG: TmpCnstrct

Decisions and findings for the Template construction section of AN-26-267 (signal modelling, binning, templates, mu mu mu A-candidate choice). Newest entry first.

## 2026-11-28 (user decisions: interpolation gate and port choices)

- **Interpolation gate passed** (user): interp-signal templates after the KNU downtime (after 11/30 20:00).
- **Port choices kept** (user): minimum 10 good direct fits per shape parametrization (2 points per coefficient at degree 4; never binding: 20-21 points per category) and the 8% per-point yield error of the G fit (previous Run 3 value; a uniform error, so it does not move G, the F-test order or the LOO normalization uncertainty, only the G band and the yield-closure pulls).

## 2026-11-28 (mA interpolation gate on the final production)

- **Chain** (`run_interpolation.sh all` = fits .. deltas, loo, export; condor 11:31-12:05; results `SignalRegionStudy/results/interpolation/`, SRS 307225c). Polynomial orders by the up-only F-test (user, 2026-11-28): SR1E2Mu x0 2, sigmaL 2, sigmaR 2, alphaL 1, alphaR 3; SR3Mu_lowM x0 4, sigmaL 4, sigmaR 2, alphaL 4, alphaR 2; SR3Mu_highM x0 3, sigmaL 2, sigmaR 3, alphaL 0, alphaR 3, fsig 3, c1 3, c2 2; G order 4 in both channels. SR3Mu_highM mA = 15 dropped (bad fit; outside its production range).
- **Leave-one-out interpolation uncertainties** (`closure/loo_uncertainties.json`, production-restricted values = those that enter the datacards): norm (lnN) SR1E2Mu 1.028 / 1.014 / 1.017 (below / on / above Z), SR3Mu_lowM 1.041 (below Z; on / above Z unreachable), SR3Mu_highM 1.010 (floor) / 1.031 / 1.029; peak position |x0_pred - x0_direct| / sigma_eff: SR1E2Mu 0.036, SR3Mu_lowM 0.029, SR3Mu_highM 0.029; width |sigma_pred / sigma_direct - 1|: 0.015, 0.021, 0.019. Largest single LOO deviations: norm 5.4% (SR1E2Mu), 7.4% (SR3Mu_lowM); scale 0.07 / 0.04 / 0.07 sigma. All small compared with the signal-shape and normalization systematics. **Gate passed: approved by the user 2026-11-28** (interp-signal templates go ahead after the KNU downtime, i.e. after 11/30 20:00: `export-config`, `grid`, interp groups).

## 2026-11-28 (SignalRegionStudy port; first signal numbers)

- **Port** (agent; `SignalRegionStudy` 35b98d0, 3769da0, 90e87ca, 50e875a; record `SignalRegionStudy/docs/PORT.md`): template / datacard / limit chain and the mA interpolation for 2024, Baseline only, RNTuples read directly, Asimov everywhere (SR blinded), outputs to /pnfs. Interpolation reduced to fixed degree-4 fits in mA (no F-test), >= 10 good fits per parametrization (SR3Mu_highM has 14 points), k_era = 1, yield error floor 0.08 (previous Run3), within-study RMS uncertainties: **for the user to confirm**.
- **Previous interp-signal key quirk: no effect on B2G-25-013 (corrected 2026-11-28).** The previous producer wrote the member signal variations of the per-era files under keys without `_` (`signal_{era}{syst}Up`, `makeBinnedTemplates.py:956`), but each histogram's own name is correct and the merge clones by `GetName()` (`mergeRunPeriodTemplates.py:142`). The datacards used for the results exist only at the merged level (`interp-signal/All/{SR1E2Mu,SR3Mu,Combined}/points/<mp>/`). Checked on the frozen MHc130_MA89p5: member `Run2/SR1E2Mu/points/.../shapes.root` has 200 of 204 signal keys differing from the names, the merged `All/Combined` 0 of 752. Its datacard has the signal shape nuisances, including `CMS_interp_res/scale` (shape) and `CMS_interp_norm` (lnN) in the signal columns. The previous author documented the quirk (`plotTemplateClosure.py:141-153`, which reads both key forms). The earlier entry ("no signal shape nuisances, relevant for B2G-25-013") was wrong: it looked at a per-era member file only. The port writes `signal_{era}_{syst}` (consistent keys; needed for the per-channel 2024 datacards, which read their own file).
- **Signal normalization check:** our signal samples are 5 fb x filter efficiency (`LOG_Dataset.md`), so B_sig = r x 5 fb / (2 x 923.6 pb x 0.5456); the previous /3 is not applied.
- **mu mu mu pairing, first number** (MHc130_MA90, validation RNTuples): the generator A pair is the higher-mass pair in 68% and the lower-mass pair in 31% of the SR events (1% unmatched); e mu mu: 98.6% matched. With the nominal rule (higher pair for mA >= 60) 68% of the mu mu mu signal sits in the peak.

## 2026-11-27 (format, environment, systematics, signal normalization, user)

- **S3:** TriLepton tree mode (`SRTree`), RNTuple output read directly by the chain (ROOT 6.36), no TTree conversion; gate: 6.36.07 reads our 6.40.02 RNTuples.
- **S7:** CMSSW_16_0_0 (ROOT 6.36.07) + Combine v11.1.0 (current recommendation), clean build with n-2 cores; no CombineHarvester (combineTool.py / plotImpacts.py are in Combine). Gates: template step reproduces a previous point (the previous notes say ROOT 6.36 segfaulted template making), v11.1.0 limit on a previous datacard agrees with v10.5.1.
- **S4:** full previous systematic list where 2024 inputs exist (DiLepton lanes; muon resolution new; trigger as shape from the measured SFs; ZZ 4.2%; WZ 12% correlated); object variations as separate RNTuples, weight variations as fields.
- **Signal (user proposal):** B_sig limits only; tt cross-section lnN on the signal; theory variations (muF, muR, PDF + alpha_s, ISR, FSR) normalized at generator level (sum of weights over all generated events), so they keep the acceptance effect and drop the inclusive cross-section effect covered by the lnN. The previous chain normalized the signal to a 5 fb reference and converted to B_sig with the central sigma(tt) (no tt uncertainty in the fit), with raw theory weights.

## 2026-11-27 (mass points: mA interpolation as in the previous study, user)

- **Decided (user), S2 of `PLAN_Signal.md`:** the mA interpolation of `SignalRegionStudyV4` (docs/interpolation/WORKFLOW.md) on the 23 generated MHc130 points, reduced to fits in mA at mH+ = 130 GeV (the previous (mH+, mA) surfaces need the seven mH+ studies; 2024 has only 130 GeV), with the previous model choices, deltas, LOO closure and within-study RMS uncertainties.
- **Gate (user):** check the size of the interpolation (modelling) uncertainties first; if large, use only the simulated mass points until the full simulation exists.

## 2026-11-27 (method and mu mu mu A candidate, user)

- **Decided (user):** the limits use the binned shape method of B2G-25-013 `ChargedHiggsAnalysisV3/SignalRegionStudyV4` (`python/makeBinnedTemplates.py`, `binned_template_core.py`, `template_utils.py:298`): DCB fit of the signal per mass point -> x0, sigma_eff = sqrt((sigma_L^2 + sigma_R^2) / 2); window x0 +- 10 sigma_eff (lower edge >= 12 GeV); n_core uniform bins in +-5 sigma_eff plus one sideband bin on each side; n_core scanned 15 -> 5 until every background bin has n_eff = round(y^2 / sigma^2) >= 5 (autoMCStats rule). First with the Baseline selection (SR without ParticleNet), then the ParticleNet selection with the same templates.
- **Decided (user):** mu mu mu A candidate: nominal is the previous rule (`SignalRegionStudyV4/python/preprocess.py:327` `pairing_for`): the higher-mass opposite-sign pair iff mH+ >= 100 GeV and mA >= 60 GeV, else the lower-mass pair. Other options are studies only:
  - (1) per mass hypothesis, the pair inside the window x0 +- 10 sigma_eff, with a rule (closest to x0) or a separate category when both pairs are inside; every event enters once, so the Poisson likelihood stays valid;
  - (2) 2D (m_low, m_high) template, unrolled (equivalent to (1) plus the both-inside category, sparse);
  - (3) both candidates stacked in one template (user's idea): breaks the independence of the entries only for events with both pairs in the window; would need event-level toys to calibrate the test statistic; cross-check at most.
  - Inputs needed: per signal mass point and background, both pair masses per event (2D histogram or tree) and the generator-matched A pair, to get the fraction with both pairs in the window and the signal-efficiency gain over the nominal rule.
