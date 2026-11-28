# LOG: Result

Decisions and findings for the Results section of AN-26-267 (expected limits, Combine diagnostics). Newest entry first.

## 2026-11-28 (first Baseline expected limits, 2024)

- **Inputs:** TriLepton production `Run1E2Mu_Run3Mu_SRTree_RunSyst_BTagEffHists_HcToWABTagEff` (HcToWA b-tag map), SignalRegionStudy 307225c, output tag `HcToWABTagEff_v1` (/pnfs `SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v1/`, local copy `SKNanoOutput/SignalRegionStudy/2024/`). Binned shape method of SignalRegionStudyV4, Asimov data_obs (SR blinded), CMSSW_16_0_0 + Combine v11.1.0 on x86_64-v3+ workers. JSONs `SignalRegionStudy/results/json/BR/2024/limits.2024[.SR1E2Mu|.SR3Mu].Asymptotic.Baseline.json`, per point `results/json/points/Baseline/mc-signal/`.
- **Expected 95% CL upper limits on B_sig** (x 1e-6; B = r x 5 fb / (2 sigma(tt) x 0.5456), sigma(tt) = 923.6 pb, source TODO). No luminosity uncertainty yet (S6 open, TWiki down); signal tt cross-section lnN 1.044 (placeholder, source TODO).

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
