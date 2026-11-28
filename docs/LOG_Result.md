# LOG: Result

Decisions and findings for the Results section of AN-26-267 (expected limits, Combine diagnostics). Newest entry first.

## 2026-11-28 18:00 (FitDiagnostics)

- **FitDiagnostics on Asimov** (cluster 2256079, `--robustFit 1`, robust Hesse): MA60 finished (outputs `SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v1/templates/MHc130_MA60/.../Combined/combine_output/fitdiag/`, local copy); MA30, MA90, MA110 still in the numerical Hesse after 6 h and removed at 18:00 (KNU downtime 20:00; user: run until 18:00). To redo after 11/30, with faster settings (e.g. no robust Hesse, or `--cminDefaultMinimizerStrategy 0` without `--robustHesse`), together with the pulls of the B2G statistics checklist.

## 2026-11-28 (B2G statistics recommendations vs the current chain)

Source: `docs/CMS/B2G_StatisticsRecommendations.md` (B2GStatisticsRecommendations TWiki, provided by the user 2026-11-28). Tests the B2G Combine contact asks for at the object review, and where we stand:
- **Nuisance pulls** (diffNuisances on FitDiagnostics): not yet (FitDiagnostics on Asimov running; on Asimov the pulls are 0 by construction, the constraints are informative).
- **Impacts:** done on Asimov, MA30/60/90/110, r range symmetric (no physics bound, as recommended). Post-fit impacts on data at unblinding.
- **GoF:** saturated algorithm (recommended), but on Asimov it is trivial (statistic 0). B2G blinded recipe: fit a measurement region (CR/sideband) with the SR masked (`--channel-masks`, `mask_<SR>=1`), generate toys from the MR post-fit with `--toysFrequentist --bypassFrequentistFit`, compare. Our datacards have no CR channel (nonprompt from the sideband, normalizations fixed) — to design (PLAN 6.1).
- **Signal injection (bias) tests:** not done. B2G asks for 3 mass points x injected r in {0, -1 sigma, median, +1 sigma expected} = 12 tests, from a background-only data-like model (blinded: `--toysFrequentist --bypassFrequentistFit`), rMin < 0, fit_status == 0 (< 10% failures), report mean/width of r - r_inj and of the pull; for low-yield searches with a bias, rerun with the backgrounds x 10.
- **F-test:** "ask the Combine contacts" — our F-test is for the polynomial orders of the signal mA interpolation (not a background function in the fit); to mention to the contact.
- **Documentation items:** MC-statistics treatment (autoMCStats 5 = Barlow-Beeston lite; bins with stat error > 30% -> lnN fallback, in line with the "< 20-30%" check), vertical template morphing (shape?), profiling; +-1 sigma plots of all shape uncertainties (not yet), post-fit pulls and correlations (with FitDiagnostics), impacts for >= 2 mass points (done, 4). PDF/scale: acceptance effects in the limit (done: generator-level normalization keeps the acceptance effect), normalization quoted in the text (tt cross-section lnN, placeholder). Binning by resolution and no empty bins (done: sigma_eff binning, floor).

## 2026-11-28 14:20 (AN Results section written, an-writer)

- **Updated** `docs/AN-26-267/Sections/Result.tex` (skeleton replaced): method (AsymptoticLimits, Asimov, expected only, no observed values; the `obs` key of the JSONs is the Asimov value and is not used), B_sig definition and conversion (Eq. BsigConversion of TmpCnstrct, 923.6 pb; no rescaling vs B2G-25-013), placeholders lumi 2.0% / tt xsec 4.4% (LUM POG preliminary 1.6% exists, not applied); `ssec:Limits` with Table `tab:ExpLimits` (23 points: combined median, 68/95% intervals, per channel), Figs. `fig:ExpLimits` (3 brazil plots), `fig:ExpLimitsChannels`; `ssec:Impacts` (refers to SystUnc `ssec:SystImpacts`, GoF, FitDiagnostics status); `ssec:Feasibility` with Table `tab:CompareB2G25013` and Fig. `fig:CompareB2G25013`. Figures copied to `docs/AN-26-267/Figures/Result/2024/`. `Appendix/Result.tex` unchanged (skeleton). Section builds.
- **Sources:** `SignalRegionStudy/results/json/BR/2024/limits.2024[.SR1E2Mu|.SR3Mu].Asymptotic.Baseline.json`; `SignalRegion/plots/AN/2024/limits/comparison.txt` and PNGs (14:02); `results/json/impacts_asimov/mc-signal/*.impacts.json`; `results/json/gof/mc-signal/*.gof.json`; binning.json of the local template copy; `configs/chain.json`, `configs/systematics.2024.json`, `scripts/run{Asymptotic,GoF,FitDiagnostics}.sh`.
- **Numbers added:** 68% band +41-53% / -28-33% of the median; channels: e mu mu lower at MA20-70 and >= 100, mu mu mu at MA15 and 75-95; mu mu mu 3.2-4.6e-6 at MA >= 105. Ratio 2024 / B2G-25-013 (Baseline region) 1.06-1.65, median 1.25, 13 of 20 below sqrt(200/109.8) = 1.35; PN window 1.64-1.81; vs B2G-25-013 Baseline interp at MA85/90/95 (1.79, 4.89, 2.70e-6) 1.27/1.18/1.25. MA90 r interval 2.3-2.7 x the other three points.
- **GoF (Asimov):** saturated, r frozen at 0, 500 toys: statistic 0 and p = 1 at all four points by construction (technical check only); toy medians 21.9 / 28.3 / 34.0 / 34.8 vs 21 / 28 / 34 / 34 bins (MA30/60/90/110).
- **FitDiagnostics:** not available; condor cluster 2256079 (4 jobs) still running at 14:17, no output on /pnfs `combine_output/`. Stated as pending in the AN.
- **Mismatch (SystUnc):** `Sections/SystUnc.tex` (ssec:SystImpacts, line ~198) says the nonprompt mu nuisance has the largest impact "at all four points"; at MA30 the tt cross-section placeholder is first (0.0437 vs 0.0405, `MHc130_MA30.Combined.impacts.json`). The Results text states the correct ranking; SystUnc not edited.
- **Minor:** `SignalRegion/python/plotLimits.py` docstring says the brazil plots are "log y", the layout has `logy: False` (plots are linear).
- **Open:**
  - sigma(tt, 13.6 TeV) = 923.6 pb reference and its uncertainty (`chain.json#signal.ttbar_xsec_source` = TODO; lnN 1.044 placeholder) — user decision (PLAN 6.1).
  - S6 2024 luminosity uncertainty in the datacards (placeholder 1.020; preliminary 1.6%) — user decision (PLAN 6.1).
  - Uneven limits at MA25 / MA30 / MA40-45 (heavy-weight conversion events, five-core-bin floor) — PLAN 6.1.
  - FitDiagnostics results (cluster 2256079) — PLAN 6.1.
  - Fine-grid (interp-signal) limits after 2026-11-30 — PLAN 4.2, 6.1.
  - Later phase: HybridNew check, signal injection, grouped uncertainty breakdown (PLAN 6.3), GoF on unblinded regions (decision on what to unblind), decomposition of the 2024 / B2G-25-013 ratio (luminosity, cross section, acceptance; PLAN 6.4), ParticleNet in the Z window (PLAN 5), combination (PLAN 6.2), feasibility verdict (PLAN 6.4).

## 2026-11-28 (plots of the 2024 Baseline results)

- **Plots** (`SignalRegion/python/plotLimits.py`, `plotImpacts.py`; `Common/Tools/plotter.py` GraphCanvas / ImpactCanvas, 2026-11-28): `SignalRegion/plots/AN/2024/limits/{brazil_Combined,brazil_SR1E2Mu,brazil_SR3Mu,channels,compare_B2G25013}.{png,pdf}`, `comparison.txt`; `impacts/MHc130_MA{30,60,90,110}[_noMCStat]`.
- **2024 vs B2G-25-013 (Run2+Run3 published expected, raw values):** ratio 2024/B2G-25-013 = 1.06-1.65 where B2G-25-013 used Baseline (typically 1.2-1.4), 1.64-1.81 in the ParticleNet window (MA85-95); at MA90 against the B2G-25-013 Baseline interp (4.894e-6) 1.18. The 2024 curve has bumps at MA25 (1.64e-6 vs 1.26 / 1.34 at 20 / 30) and MA40 (2.07e-6).
- **Impacts (Asimov):** nonprompt mu nuisance constrained to 0.57-0.77 (el 0.74 at MA90); the signal carries the tt cross-section lnN (1.044), top impact at MA30 (expected: B_sig is normalized through sigma(tt); state in the AN); signal QCD scale / PDF impacts negligible; MA30 has 47 MC-stat parameters (28-34 elsewhere). r interval +-0.6 at MA90, +-0.25 elsewhere.
- **Open (template construction):** MA30 SR1E2Mu core bin 30.29-30.86 GeV has a conversion contribution 4.64 +- 4.61 of a 9.9 background (single heavy-weight MC event; 1.8 / 2.5 in the neighbours); MA60 SR1E2Mu 2.24 +- 1.10 of 4.36 in one bin; MA30 SR1E2Mu binning at the 5-core-bin floor. Candidate cause of the MA25 / MA30 limit unevenness; next iteration.

## 2026-11-28 (comparison with B2G-25-013)

- **B_sig conversion for 2024 uses the 13.6 TeV sigma(tt) = 923.6 pb (user).** B_sig is a branching ratio and does not depend on the ttbar cross section used for the conversion: the 2024 limits and the published B2G-25-013 limits are compared directly, without rescaling (B2G-25-013 converted its combined r with its own reference, 833.9 pb).
- **Comparison plot (user):** one 1D plot vs mA at mH+ = 130 GeV, 2024 Baseline expected (median, +-1/2 sigma) with the B2G-25-013 Run2+Run3 published expected curve overlaid (ParticleNet in mA 82.5-97.5, Baseline elsewhere; `docs/previous_analysis/ChargedHiggsAnalysisV3/SignalRegionStudyV4/results/json/BR/All/`). The Run3-only previous limits exist only at MA90 and are not shown.

## 2026-11-28 (first Baseline expected limits, 2024)

- **Inputs:** TriLepton production `Run1E2Mu_Run3Mu_SRTree_RunSyst_BTagEffHists_HcToWABTagEff` (HcToWA b-tag map), SignalRegionStudy 307225c, output tag `HcToWABTagEff_v1` (/pnfs `SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v1/`, local copy `SKNanoOutput/SignalRegionStudy/2024/`). Binned shape method of SignalRegionStudyV4, Asimov data_obs (SR blinded), CMSSW_16_0_0 + Combine v11.1.0 on x86_64-v3+ workers. JSONs `SignalRegionStudy/results/json/BR/2024/limits.2024[.SR1E2Mu|.SR3Mu].Asymptotic.Baseline.json`, per point `results/json/points/Baseline/mc-signal/`.
- **Expected 95% CL upper limits on B_sig** (x 1e-6; B = r x 5 fb / (2 sigma(tt) x 0.5456), sigma(tt) = 923.6 pb, source TODO). Luminosity: placeholder `lumi_2024` lnN 1.020 in all datacards (`configs/systematics.2024.json`; corrected 2026-11-28 by the SystUnc check: an earlier version of this entry said none), value and structure pending (S6); signal tt cross-section lnN 1.044 (placeholder, source TODO).

| mA [GeV] | Combined exp | Combined +-1 sigma | SR1E2Mu exp | SR3Mu exp |
|---|---|---|---|---|
| 15 | 0.96 | 0.64 - 1.48 | 1.54 | 1.46 |
| 20 | 1.26 | 0.86 - 1.88 | 1.82 | 2.00 |
| 25 | 1.64 | 1.14 - 2.38 | 2.34 | 2.46 |
| 30 | 1.34 | 0.91 - 2.01 | 1.72 | 2.50 |
| 35 | 1.57 | 1.09 - 2.31 | 2.13 | 2.52 |
| 40 | 2.07 | 1.48 - 2.98 | 2.62 | 3.55 |
| 45 | 2.00 | 1.40 - 2.87 | 2.38 | 3.62 |
| 50 | 1.70 | 1.19 - 2.47 | 2.11 | 3.06 |
| 55 | 1.90 | 1.33 - 2.73 | 2.34 | 3.43 |
| 60 | 1.87 | 1.31 - 2.69 | 2.42 | 3.06 |
| 65 | 1.75 | 1.24 - 2.52 | 2.46 | 2.58 |
| 70 | 1.94 | 1.37 - 2.77 | 2.69 | 2.83 |
| 75 | 1.96 | 1.40 - 2.82 | 3.00 | 2.62 |
| 80 | 1.76 | 1.24 - 2.52 | 2.83 | 2.31 |
| 85 | 2.27 | 1.61 - 3.23 | 3.41 | 3.12 |
| 90 | 5.78 | 4.14 - 8.12 | 8.76 | 7.67 |
| 95 | 3.39 | 2.43 - 4.82 | 5.08 | 4.61 |
| 100 | 2.23 | 1.56 - 3.17 | 3.04 | 3.35 |
| 105 | 2.03 | 1.43 - 2.89 | 2.69 | 3.22 |
| 110 | 2.00 | 1.40 - 2.89 | 2.54 | 3.43 |
| 115 | 2.11 | 1.47 - 3.04 | 2.54 | 3.91 |
| 120 | 1.89 | 1.30 - 2.79 | 2.11 | 4.61 |
| 125 | 1.96 | 1.37 - 2.88 | 2.23 | 4.61 |

  Combined 0.96-2.3 x 1e-6 except on the Z peak (MA90 5.8, MA95 3.4); both channels contribute comparably.
- **Combine diagnostics (Asimov, r = 1), MA30, MA60, MA90, MA110:** impacts, GoF and FitDiagnostics submitted (`automize/submit.sh combine`). Leading impacts: MA30 signal tt xsec 0.044, nonprompt mu 0.040, MC stat bins ~0.03, b-tag bc correlated 0.029; MA90 nonprompt mu 0.18, SR3Mu MC stat bins 0.10-0.14, Norm_others 0.10, nonprompt el 0.10, b-tag 0.08, ttZ 0.08 (`results/json/impacts_asimov/mc-signal/`).
