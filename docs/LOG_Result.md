# LOG: Result

Decisions and findings for the Results section of AN-26-267 (expected limits, Combine diagnostics). Newest entry first.


## 2026-11-28 night (impacts and Asimov GoF on v2)

- Impacts (`runImpacts.sh`) and the saturated Asimov GoF (500 toys) rerun locally on the v2 datacards (lumi 1.016) at MA30/60/90/110 (~3 min per point; SRS results/json/{impacts_asimov,gof}). Leading impacts change by <= 1.1% vs v1 and the ranking is unchanged (MA30: tt cross section 0.0437 first, nonprompt_mu 0.0407; MA60/90/110: nonprompt_mu 0.072 / 0.182 / 0.059 first); GoF statistic 0, p = 1 (Asimov, technical). Impact plots regenerated (`SignalRegion/plots/AN/2024/impacts/`). The AN statement "impacts from the v1 datacards" is now outdated.

## 2026-11-28 night (AN Results updated, an-writer)
- **Follow-up (v2 impacts / GoF, an-writer):** `ssec:Impacts` now cites the v2 impacts and GoF (files 21:35): MA30 tt xsec 0.0437 > nonprompt_mu 0.0407, MA60/90/110 nonprompt_mu 0.0721 / 0.1821 / 0.0587 first; GoF obs 0, p = 1, toy medians 21.9 / 28.3 / 34.0 / 34.9 (MA110 was 34.8); bin counts from the v2 binning.json. The "first version of the datacards" sentence and the rerun TODO are removed. The Open item "impacts still from v1" is closed. Result builds (rc 0).

- **Interrupted run:** the previous an-writer run had rewritten `Sections/Result.tex` and `Appendix/Result.tex` (21:20-21:21) but not the logs. The appendix had shell-expansion damage (zsh unquoted heredoc: `$r`, `$(r - r_inj)`, `$+1` -> `0`, `$+0` -> `1`, `\\` -> `\`): the b-only pull column of `tab:app-FitDiagConstraints` showed 0.38 / 1.52 / 0.24 / 1.61 / 1.54 / 1.31 / 1.82 / 1.80 instead of +1.38 / +0.52 / +1.24 / +0.61 / +0.54 / +0.31 / +0.82 / +0.80, and several `$r ...$` were missing. Repaired from the fitdiag JSONs; all table numbers re-read.
- **Verified against the files (python3, 2026-11-28):** `tab:ExpLimits` = `limits.2024[.SR1E2Mu|.SR3Mu].Asymptotic.Baseline.json` (v2, lumi 1.016) at all 23 points; v2 vs v1 (`git show 186d5bd`): exp0 identical, edges <= 0.75 / 0.52 / 0.56 / 1.01%; fine grid 376 keys, interp/mc closure 0.949-1.051, median 0.992; fitdiag s+b status 0 / covQual 3, constraints nonprompt_mu 0.775 / 0.717 / 0.570 / 0.592, nonprompt_el 0.994 / 0.935 / 0.742 / 0.817, others >= 0.905 (pileup at MA60), mcstat < 0.9 11/39, 22/28, 13/34, 10/34; b-only pulls as above; injection: all 20 rows of `tab:app-Injection` match `tests.*.{r_inj,n_ok,r_minus_rinj_gauss,pull_gauss}`.
- **Edited this run:** `ssec:Limits` low-mA unevenness: cause stated (background-template fluctuations in the 0.4-0.6 GeV core bins; MA25 SR3Mu nonprompt 6.73 +- 2.21 in the peak bin vs 3.83 / 1.91; MA30 SR1E2Mu nonprompt 0.00 / 0.99 +- 0.74 under the peak vs 3.85 / 4.36, conversion 4.64 +- 4.61 from one event; read from v2 `shapes.root`), no smoothing in this round (user, `LOG_TmpCnstrct.md` 2026-11-28 evening), expected to shrink with 2025; the "not yet investigated" statement and TODO replaced by a later-phase smoothing TODO. `ssec:LimitsFineGrid`: same cause for the fine-grid wiggles. Appendix: table and caption repairs, `\resizebox` on `tab:app-Injection`, `\allowbreak` in the plot path.
- **Kept from the interrupted run (checked):** lumi 1.6% text, `ssec:LimitsFineGrid` with `fig:ExpLimitsFineGrid`, `ssec:Impacts` (impacts, pulls/constraints, injection, +-1 sigma templates, GoF with the ttZ CR proposed, F-test), appendix `ssec:appendix_pulls`, `ssec:appendix_injection`, `ssec:appendix_syst_templates` (5 template figures, 6 injection figures in `Figures/Result/2024/{injection,systematics}/`). No "FitDiagnostics pending" statement is left. Section and appendix build (rc 0; only cross-file references undefined; overfull 3 pt and 16 pt in the appendix).
- **Open:**
  - PLAN 6.1: impacts (and the Asimov GoF) are still from the v1 datacards (lumi 1.020; files 11:55-12:01); rerun on v2 (TODO in `ssec:Impacts` and `ssec:SystImpacts`).
  - user decision, PLAN 6.1: measurement region of the blinded GoF (proposal: ttZ CR, e e mu; needs its datacard and observable).
  - PLAN 6.1: bibliography entry for CMS-DP-2026-003 (not in `AN-26-267.bib`; the text cites the LumiRecommendationsRun3 TWiki).
  - PLAN 6.1: tZq SR1E2Mu MA60 pileup-down template (one bin x30) and low-statistics shape templates; F-test confirmation with the Combine contact.
  - later phase: smoothing of background templates after the 2025 extension (user); HybridNew; uncertainty breakdown (6.3).

## 2026-11-28 evening (B2G statistics tests, run locally during the KNU downtime)

User: "Do your work locally." Combine runs on the local host in the el9 container (`SignalRegionStudy/scripts/cmssw_local.sh`, CMSSW_16_0_0 + Combine v11.1.0) on the local copy of the v2 templates (`SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v2/`, lumi 1.016). Products in `SignalRegionStudy/results/json/{fitdiag,injection,injection_bkgx10}/mc-signal/` (SRS bc0d4f3); ROOT outputs under each point's `combine_output/` in the local copy (not on /pnfs).
- **FitDiagnostics (pulls) at MA30/60/90/110**, Asimov with r = 1 injected, `--robustFit 1`, strategy 0: **9 s per point** without `--saveShapes --saveWithUncertainties` (new option `--no-shapes` of `runFitDiagnostics.sh`). The hours on KNU were the shape saving (numerical Romberg integrals of every morphed shape), not the fit. All fits status 0, covQual 3. r = 1.00 -0.22/+0.24 (MA30), -0.25/+0.27 (MA60), -0.60/+0.62 (MA90), -0.25/+0.27 (MA110). s+b pulls 0 by construction (Asimov). **Constraints:** only the nonprompt shape nuisances are constrained by the SR itself, `nonprompt_mu` 0.77 / 0.72 / 0.57 / 0.59 and `nonprompt_el` - / 0.93 / 0.74 / 0.82 of the prefit width (MA30/60/90/110); every other nuisance >= 0.9 in the s+b fit. b-only fit on the r = 1 Asimov: the injected signal is absorbed by `nonprompt_mu` (+1.38 / +1.24 / +0.31 / +0.82 sigma) and, at MA60, `scale_j` (+0.61); expected, since r = 1 is 2.5-3.7 x the median expected limit. MC-statistics (BB-lite) parameters: 10-22 of 28-39 below 0.9 in the s+b fit (data-like Asimov statistics comparable to the MC statistics in low-yield bins). `collectFitDiag.py` -> `<mp>.Combined.fitdiag.json`; `diffNuisances.txt` next to the ROOT file.
- **Signal injection (bias), 4 points x 4 r_inj** (0, and the -1 sigma / median / +1 sigma expected r of `results/json/points`), 500 toys each, generated from the prefit model (`--toysFrequentist --bypassFrequentistFit`; our data_obs is the Asimov background, so the model is data-like by construction, as B2G requires), fitted with FitDiagnostics s+b, r in [-3, 3] ([-5, 5] at MA90), no toy at the boundary. Results (pull mean / width, Gaussian fit): all 16 tests within **mean -0.12 to +0.05 and width 0.95-1.07**; r - r_inj means <= 0.013 in r (<= 0.04 at MA90), i.e. < 8% of the r uncertainty. The largest offset is MA30 -1 sigma, pull mean -0.12 +- 0.05. **Fit failures (fit_status != 0):** 6.6% / 8.2% / 2.8% / 0.2% at r_inj = 0 (MA30/60/110/90), <= 2.6% otherwise; below the B2G 10% threshold. The failed fits sit at negative r (90-97% of them at MA30/60 r_inj = 0): the low-yield barrier described by B2G (negative total yield in signal-dominated bins).
- **B2G low-yield variant, backgrounds x 10** (rateParam frozen at 10; r_inj = 0; r in [-10, 10], [-25, 25] at MA90): failures drop to 0-1% (500/500, 496, 496, 495 converged), pull mean -0.07 / -0.06 / -0.01 / +0.02, width 0.98 / 0.99 / 1.07 / 1.04 (MA30/60/90/110). Confirms that the r_inj = 0 failures are the zero-yield barrier, not a model problem.
- **Plots** (plotter.py): `SignalRegion/plots/AN/2024/injection[_bkgx10]/` (per test r - r_inj and pull histograms with Gaussian fits, `summary`); **+-1 sigma templates of every shape nuisance** (B2G documentation item) `SignalRegion/plots/AN/2024/systematics/MHc130_MA{30,60,90,110}/` (1054 plots, `SignalRegion/python/plotSystShapes.py`) with `summary.txt` (normalization and shape-only change per entry). Findings from the summary: largest shape-only changes in tZq (MC statistics: SR1E2Mu MA30 `scale_j` up 1.9 in one bin, SR3Mu MA60 `pileup` down 1.8), the nonprompt shape nuisance +21% / -18% normalization at MA110 SR3Mu; 53 `shape?` entries have no templates (conversion in SR3Mu; no effect in Combine).
- **Still open:**
  - **Blinded GoF with a measurement region (user decision, PLAN 6.1).** The SR data are not written by the analyzers, so no SR-based GoF (sidebands of the windows included) is possible without changing the blinding. Options: (a) GoF of the same background model in the unblinded control regions (WZ CR, Z+fake CR), as separate datacards; (b) unblind the m(mu mu) sidebands outside the signal windows (analyzer and blinding-rule change); (c) keep only the Asimov technical GoF until unblinding. Proposal: (a).
  - **F-test (to the Combine contact):** our F-test chooses the polynomial orders of the signal-model interpolation in mA (DCB parameters and yields vs mA, orders 0-4, up-only ladder, `fit_surface_ftest`); there is no fitted background function. To be stated in the AN and asked at the object review whether a note suffices.
  - Post-fit shapes (`--saveShapes`) only when needed (unblinding); run them on condor then.

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
