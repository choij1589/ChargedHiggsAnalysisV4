# LOG: TmpCnstrct

Decisions and findings for the Template construction section of AN-26-267 (signal modelling, binning, templates, mu mu mu A-candidate choice). Newest entry first.

## 2026-11-27 (method and mu mu mu A candidate, user)

- **Decided (user):** the limits use the binned shape method of B2G-25-013 `ChargedHiggsAnalysisV3/SignalRegionStudyV4` (`python/makeBinnedTemplates.py`, `binned_template_core.py`, `template_utils.py:298`): DCB fit of the signal per mass point -> x0, sigma_eff = sqrt((sigma_L^2 + sigma_R^2) / 2); window x0 +- 10 sigma_eff (lower edge >= 12 GeV); n_core uniform bins in +-5 sigma_eff plus one sideband bin on each side; n_core scanned 15 -> 5 until every background bin has n_eff = round(y^2 / sigma^2) >= 5 (autoMCStats rule). First with the Baseline selection (SR without ParticleNet), then the ParticleNet selection with the same templates.
- **Decided (user):** mu mu mu A candidate: nominal is the previous rule (`SignalRegionStudyV4/python/preprocess.py:327` `pairing_for`): the higher-mass opposite-sign pair iff mH+ >= 100 GeV and mA >= 60 GeV, else the lower-mass pair. Other options are studies only:
  - (1) per mass hypothesis, the pair inside the window x0 +- 10 sigma_eff, with a rule (closest to x0) or a separate category when both pairs are inside; every event enters once, so the Poisson likelihood stays valid;
  - (2) 2D (m_low, m_high) template, unrolled (equivalent to (1) plus the both-inside category, sparse);
  - (3) both candidates stacked in one template (user's idea): breaks the independence of the entries only for events with both pairs in the window; would need event-level toys to calibrate the test statistic; cross-check at most.
  - Inputs needed: per signal mass point and background, both pair masses per event (2D histogram or tree) and the generator-matched A pair, to get the fraction with both pairs in the window and the signal-efficiency gain over the nominal rule.
