# LOG: Trigger

Decisions and findings for the Trigger section of AN-26-267. Newest entry first.


## 2026-11-27 (AN: Section 4 and its appendix finalized)

- **Written** (an-writer) `AN-26-267/Sections/Trigger.tex`, `Appendix/Trigger.tex`:
  - Validation figure `fig:TrigSFEffect`: the copies in `Figures/DiLepton/2024/{DIMU,EMU}/` are md5-identical to the TrigDZ plots (`DiLepton/plots/AN/2024/`, 07:25). `%% src` lines now point to TrigDZ. The caption sentence "leg uncertainties only" is replaced by "legs and DZ filter". TODO closed. The quoted numbers match `corrections.txt` (TrigDZ): MC/MC(Central) 1.051 / 1.017, data/MC 0.944 -> 0.992, 0.941 -> 0.957. There is no `yields.txt`; `corrections.txt` and `cutflow.md` are the files. The per-bin ratios (0.938, 0.964, 6.3-7.1%, ...) were computed on TrigSF. The TrigDZ histograms are identical to TrigSF bin by bin (DIMU Central/DblMuTrigSF_NotImplemented muons/1/eta, muons/2/pt; EMU Central/EMuTrigSF_NotImplemented electrons/1/pt; all MC files, max relative difference 0).
  - Flagged dimuon-leg fits: the section text is corrected and the list is in the appendix (new `tab:app-TrigDblMuFlagged`, `fig:app-TrigDblMuFits`, subsections "Flagged dimuon-leg fits" and "Efficiencies in all bins"). Sources:
    - local `SKNanoOutput/TnP/2024/NUM_*Leg*/checkFitStatus.txt` (state after the refits, 9 + 3 fits);
    - `efficiency.root` per-member histograms;
    - bin index = i_eta + 4 i_pT (tnp_tamsa `tnpConfig.py`).
  - The flagged fits are:
    - Mu17 data |eta| 1.2-2.1, 14-16 GeV: nominal, tag iso 0.1, 40 mass bins, fit range 75-115;
    - Mu17 data 0-0.9 / 25-30: fit range 65-105;
    - Mu17 data 2.1-2.4 / 40-50: tag iso 0.1, 40 mass bins;
    - Mu17 data 2.1-2.4 / 100-200: tag iso 0.1;
    - Mu17 sim 2.1-2.4 / 50-100: tag iso 0.3 (efficiency error 4.6 x the gen-matched truth error);
    - Mu8 data 2.1-2.4 / 10-15 and 0.9-1.2 / 20-25: 160 mass bins;
    - Mu8 data 2.1-2.4 / 25-30: tag iso 0.3.
    
    All data fits are flagged for the signal-yield error (3.1-7.4 x sqrt(S+B)). Largest shift from the nominal: 9.7e-4 (Mu17 100-200 GeV, stat 1.6e-3). Leaving the flagged variations out changes the total uncertainty by at most 1.6e-4 (the sub-threshold bin, 0.00072 -> 0.00056). The fit plots of the still-flagged fits are the production plots (`refit_flagged.py` keeps the production fit when a refit is not accepted). Four of them are copied from KNU `tnp_tamsa/results/HcToWA_MuonTrig_2024/*/plots/data/` to `Figures/Trigger/2024/fits/`. In these four, the fitted and counted efficiencies agree within 4e-4.
  - Ele23 turn-on, quantified from existing histograms (no new measurement). Source: `SKNanoOutput/MeasTrigEff/.../ElLeg/os/ref/{cor,raw}/{num,den}_Ele23`, data Muon0/1 vs TTLL powheg, scratch computation that reproduces the corrected-pT SFs of `summary.txt`.
    - Half-plateau point, data - TT: corrected pT +0.13 / +0.39 / +0.39 / +0.21 GeV; uncorrected pT +0.10 / +0.17 / -0.22 / -0.76 GeV (|eta_SC| bins 0-0.8, 0.8-1.4442, 1.566-2.0, 2.0-2.5).
    - The data scale correction moves the data turn-on by 0.03-0.95 GeV, most in the endcaps.
    - SF at 22-24 GeV: 0.70-0.87 in corrected pT, 0.87-1.80 in uncorrected pT. SF at 24-26 GeV: 0.92-1.03 corrected, 0.98-1.10 uncorrected.
    
    TODO closed. The sentence "uncorrected-pT binning is not used since the offline thresholds are above the turn-ons" is replaced by a pointer to this comparison.
  - Remaining TODOs reworded with their reason in brackets: [later phase] gen-level signal pT (PLAN 4), trilepton thresholds (PLAN 1), trilepton SF variations and closure (PLAN 1; the two old TODOs merged into one, with prose sentences in the Uncertainties and Closure subsections); [later phase, not yet run] comparison with the pT-picked formula (PLAN 2.4); [user decision] C_data = C_MC, and the IsoMu24-subset pT trend / |eta| structure (PLAN 2.4).
  - Builds: `Sections/Trigger.tex` and `Appendix/Trigger.tex` (target builds) compile. Only undefined references to other sections remain. One overfull box of 6 pt is in the unchanged trigger-path paragraph (l.7, long path names). The new table needed `\tabcolsep` 4pt.
- **Findings / mismatches:**
  - Entry 2026-11-26 (steps 1 and 2) and the former AN text say "Mu17 bin 6 (all members ...)": only 4 of its 9 members are flagged (nominal, tag iso 0.1, 40 mass bins, fit range 75-115). Its tag iso 0.3, 160 mass bins, fit range 65-105, alt signal and alt background fits pass. AN corrected.
  - Ele23: the turn-on SF of the 22-24 GeV bin depends strongly on the pT definition. In the endcaps the uncorrected pT puts the data turn-on *before* the MC one, so the shift in corrected pT is not explained by the scale correction alone. Neither pT is the online pT.
  - The 24-26 GeV Ele23 bin contains the offline e threshold (25 GeV) of the Mu8_Ele23 part of the EMU selection (`DiLepton.cc:500`). The step-2 decision (1) ("offline pT cuts safely above the turn-ons") holds for Ele12 but not fully for Ele23. There the SF differs by up to 0.13 between the two pT definitions (|eta_SC| 2.0-2.5: 0.972 vs 1.100).
  - The e-mu leg plots still label DY as "alt. MC" (unchanged since 2026-11-26).
- **Open:**
  - User: whether the pT-definition dependence of the Ele23 turn-on SF (22-26 GeV) needs action (binning, uncertainty), given step-2 decision (1) (PLAN 2.4). Not written as an AN TODO; the AN states the numbers.
  - User: C_data = C_MC without a data check; study of the IsoMu24-subset pT trend and |eta| structure (PLAN 2.4).
  - Not yet run: comparison with the pT-picked B2G-25-013 formula (PLAN 2.4, T1 validation).
  - Later phase: trilepton SF variations and closure, signal per-event SFs (PLAN 1); trilepton offline thresholds (PLAN 1); generator-level signal pT (PLAN 4).


## 2026-11-27 (AN: trigger-SF model without closure term; closure as a check)

- **Written** (an-writer) `AN-26-267/Sections/Trigger.tex`:
  - Pairwise filters: DZ uncertainty = stat (+) spread of the binned SF (bins with N_den >= 1000 in max|eta| and leading pT), DblMu +0.18 / -0.14%, EMu +0.31 / -1.55% (from `trigger_HcToWA.json#PairFilter`); bins recomputed from `summary.txt` as in `sf_spread`: DblMu up from max|eta| 0.9-1.2, down from lead pT 23-24 GeV (not 2.1-2.4: that bin gives -0.13%); EMu up from max|eta| < 0.9, down from 2.4-2.5. Old open TODO on the DZ eta/pT dependence removed (settled by the spread). `tab:TrigPairFilter` caption updated.
  - Uncertainties: from the measurements only; no closure term (old sentence removed). Fit nuisance: equation without c (`HcToWABase::TrigSF`, `trigClosure_` = 0 since the JSON has no `TrigClosure`). Effect on the MC yield from the TrigDZ lanes (`closure.txt`): DIMU DY +0.24 / -0.20%, tt +0.27 / -0.24%; EMU tt +0.61 / -1.85%. The old "expected +-0.9% / +-0.4%" and its TODO are gone.
  - MC closure rewritten as a pass/fail check: criterion as in `trigClosure.py`; dimuon on the IsoMu24 subset with C = eps(path)/eps(path | IsoMu24), C_data = C_MC assumed, no uncertainty; `tab:TrigClosureDiLep` now has inclusive, IsoMu24, L1-seed ratios, C_MC, SF uncertainty, result (all pass); 4-file L1/IsoMu24 test with the seed list (checked against `DiLepton.cc:979-983`); full-sample split (L1 condition removes 0.38% / 0.36% of the 0.73% / 0.90% gap); binned observations on the IsoMu24 subset (pT trend, |eta| structure 0.984-1.018) stated as observations. New `fig:TrigClosureIsoMu24`; closure figures refreshed to TrigDZ (`Figures/Trigger/2024/closure/`, 6 replaced, 3 added).
  - `fig:TrigSFEffect` caption: band has leg uncertainties only (TrigSF figures); TODO to switch to the TrigDZ DiLepton plots. `Sections/ObjectID.tex` caption of the DiLepton overview figure: "without the closure term" replaced by "leg uncertainties only, without the DZ filter uncertainty". `Appendix/Trigger.tex`: pairwise-filter caption states the spread enters the uncertainty.
  - Full build: 75 pages, no undefined references, no overfull boxes in the trigger section.
- **Findings / mismatches:**
  - The brief's "DIMU +0.24/-0.21%, EMU +0.62/-1.86%" are the expected legs + DZ values (TrigSF lanes + JSON DZ); the TrigDZ lanes give DY +0.24/-0.20, tt +0.27/-0.24, EMU +0.61/-1.85 (the AN quotes the lanes).
  - Entry 2026-11-26 says the DblMu -0.14% comes from max|eta| 2.1-2.4; it comes from the leading-pT 23-24 GeV bin (2.1-2.4 gives -0.13%).
  - Entry 2026-11-26 says Mu8Ele23 is "compatible" with the EMu spread; its max|eta| 2.4-2.5 bin (N_den 1106) is -2.7% from its inclusive SF, beyond -1.55% (about 1.7 sigma, stat ~0.6%). Not used (one value for both paths); the AN states it.
  - Entry 2026-11-27 (TrigDZ production) says the IsoMu24-subset ratio is "about 0.99 above 70 GeV": true for the subleading pT (0.986-0.994), not for the leading pT (0.996-1.005).
  - Observation (not interpreted): the step of the IsoMu24-subset closure in the subleading-muon pT lies between the 20-25 and 25-30 GeV bins, at the IsoMu24 threshold.
  - `HcToWABase.cc` still contains the closure-term mechanism (`trigClosure_`, hypot); dormant with the current JSON (md5 f6fbc637..., local = KNU).
  - The DiLepton figure copies in the AN (Trigger and ObjectID) are still from TrigSF; the TrigDZ plots (2026-11-27) differ only in the band.
- **Open:**
  - TrigDZ DiLepton figures into the AN (ObjectID and Trigger, one pass) (PLAN 2.2, 2.4).
  - Origin of the IsoMu24-subset pT trend and |eta| structure: reported, not assigned; whether to study is for the user (PLAN 2.4).
  - C_data = C_MC is an assumption without a data check (user decision 2026-11-26) (PLAN 2.4).
  - Trilepton closure (signal, WZ, ttZ) and trigger-SF variations in the trilepton regions (PLAN 1, 2.4).
  - Unchanged: flagged dimuon-leg fit list (PLAN 2.4 step 1), Ele23 turn-on shift, comparison with the pT-picked formula (PLAN 2.4).

## 2026-11-27 (TrigDZ production: closure check passes)

- **Production** `TrigDZ` complete (DIMU and EMU, MC, 877 + 877 nodes, both DAGs status 0, 2026-11-26 21:04). Synced to `SKNanoOutput/DiLepton/Run{DiMu,EMu}_RunSyst_TrigDZ/2024/` (MC files; data files are links to the LepIDSF data, as for TrigSF). ZEE was not rerun and stays on TrigSF.
- **Closure** (`Trigger/python/trigClosure.py`, default TrigDZ, no `--add-dz`; `Trigger/results/2024/closure.txt`, plots `Trigger/plots/AN/2024/closure/`):

  | | inclusive | IsoMu24 fired (check) | L1 seed fired | C_MC | sigma (lanes) | result |
  |---|---|---|---|---|---|---|
  | DIMU DY | 0.9914 | **0.9987** | 0.9952 | 0.9927 | +0.0024 / -0.0020 | PASS (0.0013) |
  | DIMU tt | 0.9928 | **1.0018** | 0.9964 | 0.9910 | +0.0027 / -0.0024 | PASS (0.0018) |
  | EMU tt | **0.9968** | - | - | - | +0.0061 / -0.0185 | PASS (0.0032) |

  Statistical errors < 1e-4 (EMU DY, reference only: 0.9828 +- 0.0011). The IsoMu24 fraction of the denominator is 0.956 (DY) and 0.967 (tt). The lane uncertainties agree with the expected legs + DZ values (DIMU +0.24/-0.21%, EMU +0.62/-1.86%); the full production confirms the 4-file test (1.0005 / 1.0027).
- **Binned (IsoMu24 subset):** a pT trend remains, 1.02 at the lowest leading and subleading pT bins (20-25 and 10-20 GeV), above 70 GeV 0.986-0.994 in subleading pT but 0.996-1.005 in leading pT (corrected after the an-writer check); in |eta| the structure within the leg bins (0.984-1.018) as before. Within the check criterion only for the integral; noted for the AN.
- **DiLepton plots** (`DiLepton/python/plot.py`: `PRODUCTION` per channel, DIMU and EMU TrigDZ, ZEE TrigSF): regenerated with `--all-lanes`; `corrections.txt` identical to TrigSF (same nominal SF), only the trigger-SF band changes.

## 2026-11-26 (C_data = C_MC assumed)

- **Decided (user):** the event-level factor C = eps(path) / eps(path | IsoMu24) is assumed equal in data and MC, so it cancels in the SF (SF = eps_data / eps_MC from the legs, unchanged; no code change). Basis: the T1 prediction closes in MC under the TnP tag condition (entry below); the inclusive non-closure is the event-level correlation, about 0.7-0.9% in MC. The dimuon closure check is therefore made on the IsoMu24 subset (pass criterion as before); the inclusive closure and C_MC are reported. No extra uncertainty for C.
- **Production** `TrigDZ` (`hcto_prod/submit_trigdz.sh`, DIMU and EMU, MC only, 17:24): trigger-SF lanes with the DZ uncertainty of the JSON, closure subsets. `trigClosure.py` default production `TrigDZ`; the dimuon check uses the IsoMu24 subset when present and reports the inclusive closure, the L1-seed subset and C_MC (previous version in the session scratchpad; on TrigSF it reproduces the previous numbers).

## 2026-11-26 (dimuon closure: test of the tag-trigger conditioning)

- **Test** (`hcto_prod/l1test.sh`; condor, 4 files each of DYto2Mu 2J MLL50 and TTLL powheg, DIMU, no RunSyst). Code: `DiLepton::FillTrigClosure` fills the DIMU closure also for events with HLT_IsoMu24 fired (`TrigClosure/IsoMu24/`, the TnP tag condition) and with a candidate L1 seed of the dimuon path fired (`TrigClosure/L1Seed/`: L1_SingleMu22, L1_SingleMu25, L1_DoubleMu_15_7, L1_DoubleMu0_Upt15_Upt7, L1_DoubleMu4p5er2p0_SQ_OS_Mass_Min7, _Mass_7to18, L1_DoubleMu4_SQ_OS_dR_Max1p2, L1_DoubleMu4p5_SQ_OS_dR_Max1p2), plus `pathNoL1` (path fired, no candidate seed). The L1 bits and HLT_IsoMu24 are read through SKNano's `HLT_Path.json` (8 L1 entries added; local patch). Previous versions `hcto_prod/module_pre_l1test/`. Test histograms deleted from /d0 after the check.
- **Result** (obs/exp, stat error):

  | | all | IsoMu24 fired | L1 seed fired |
  |---|---|---|---|
  | DY | 0.9945 +- 0.0016 | **1.0005 +- 0.0016** | 0.9974 +- 0.0016 |
  | tt | 0.9943 +- 0.0020 | **1.0027 +- 0.0019** | 0.9986 +- 0.0020 |

  The seed list is complete: the path fires without a candidate seed in 5e-4 of the cases. (The 4-file non-closure, 0.55%, is smaller than in the full production, 0.86% / 0.72%.)
- **Finding:** the T1 prediction closes when the event satisfies the TnP tag condition (IsoMu24), so the leg efficiencies and the per-event formula are right for that condition. The inclusive non-closure is an event-level correlation of the dimuon path that the TnP legs do not see: about half of it comes from the L1 seed (event-level L1 decision), the rest from the HLT level (the tag condition also guarantees a reconstructed HLT muon in the event). In the |eta| bins the IsoMu24 subset still shows the structure within the leg bins (0.975-1.021).
- **Checked (open item of the an-writer entry below):** the `data`/`sim` errors of the dimuon-leg `efficiency.root` include the fit systematics (combined error > nominal fit error, e.g. Mu8 |eta| < 0.9, 10-15 GeV: 0.0007 vs 0.0005; largest set shifts 1e-4 to 6e-4). They are small because the probe is a tight, isolated muon (little background under the Z peak): 1-2e-4 on the plateau, 5-8e-4 at the turn-on and above 100 GeV. This is why the dimuon leg lanes move the MC yield by only +-0.06%.
- **Open (user):** how to treat the event-level factor C = eps(path) / eps(path | IsoMu24) (MC ~0.99-0.995): it enters the SF only as C_data / C_MC.

## 2026-11-26 (closure is a check; DZ uncertainty; dimuon closure fails)

- **Decided (user):** the MC closure is a check, not an uncertainty. The trigger-SF uncertainty comes from the measurements, including the DZ filters; the closure must pass within it. Supersedes the closure term of T3 (and the `TrigClosure` correction written earlier today, now removed from the JSON; the loader in HcToWABase treats it as absent = 0).
- **DZ uncertainty** (`makeTrigJson.py`): one inclusive number per trigger is used for all pT and eta, so its data uncertainty covers the binned values: effDataUp/Down = effData x (1 +- sqrt(stat^2 + spread^2)), spread = largest positive / negative deviation of the binned SF (data/TT; max|eta| and leading-pT bins with N_den >= 1000) from the inclusive SF. DblMu_DZ: SF 0.99533 +0.18% -0.14% (+ from max|eta| 0.9-1.2; - from leading pT 23-24 GeV, max|eta| 2.1-2.4 gives -0.13%: corrected 2026-11-27, an-writer check); EMu_DZ (Mu23Ele12 bins; Mu8Ele23 compatible): SF 0.99283 +0.31% -1.55% (the -1.55% from max|eta| 2.4-2.5, electron only, 1.4% of the e-mu DZ denominator). JSON copied to KNU (previous `hcto_prod/module_pre_trigsf/trigger_HcToWA.json.closureterm`).
- **Check** (`trigClosure.py --add-dz` -> `Trigger/results/2024/closure.txt`): sigma = trigger-SF lane variation of the TrigSF production (legs only: DIMU +-0.06%, EMU +-0.31%) + DZ uncertainty (linear, coherent as in `TrigSF`), in the direction of the non-closure, (+) stat.
  - DIMU: DY |obs/exp - 1| = 0.0086 vs 0.0021, tt 0.0072 vs 0.0025: **FAIL**.
  - EMU (tt): 0.0032 vs 0.0186: PASS (binned: 15-25 GeV down to 0.980, at the edge).
- **Hypothesis for the dimuon failure (not tested):** the dimuon legs come from tag and probe with an IsoMu24 tag, so the dimuon path's event-level L1 seed has (nearly) always fired in the measurement, while in the closure sample it can fail; per-object L1 matching is in the legs, the event-level seed is not. The non-closure is flat in pT, equal in DY and tt, and largest in the |eta| regions of L1 muon inefficiency (1.75-2.0), as expected for that. Test: closure on the subset with HLT_IsoMu24 fired (or with the path's L1 seeds fired; L1 bits are in our NanoAOD: L1_DoubleMu_15_7, ...), which should close if the hypothesis holds.
- Lanes: the `*TrigSF_Up/Down` lanes need a rerun to include the DZ uncertainty (none to include the closure term any more).

## 2026-11-26 (AN: trigger SF results written; DiLepton figures and tables to the TrigSF production)

- **Written** (an-writer) `AN-26-267/Sections/Trigger.tex` from "Dimuon legs" on: dimuon-leg results (fit check 52/36 flagged, 9/3 left; plateau SFs per |eta| bin; `fig:TrigDblMuLegs`), e-mu legs (final binning of `measEMuEff.py`, plateau SFs, Ele23 turn-on, the four checks with their sizes, none assigned; `fig:TrigEMuLegs`), pairwise filters (`tab:TrigPairFilter`, eta/pT dependence stated, one inclusive value each), uncertainties (dimuon legs stat (+) fit syst; e-mu stat only; DY reference only), per-event SF (T1 as coded in `HcToWABase::TrigEff`, clamp, ECAL-gap row, one e-mu DZ), fit nuisance with the closure term (equation as in `TrigSF`), MC closure (`tab:TrigClosureDiLep`, `fig:TrigClosure`, closure terms 0.0086 / 0.0032, binned behaviour), validation (`fig:TrigSFEffect`; ZEE statement fixed: our electron ID SF + EGM reco SF, proxy EGM trigger SF only). The two-file test numbers are gone. `Appendix/Trigger.tex`: dimuon-leg data/sim maps, all 16 e-mu leg plots, binned DZ plots.
- **ObjectID** (`Sections/ObjectID.tex`, `Appendix/ObjectID.tex`): weights/tests rows, trigger-SF paragraph and lane-chain explanation, `tab:DiLeptonYields` (data/MC 0.992 / 0.957 / 0.983, new rows without dimuon / e-mu trigger SF, chained No<ID> values), every "effect" paragraph (reco, ID, JEC, b tag, PU, top pT, Z peak DIMU row) recomputed from `Run*_RunSyst_TrigSF` (per-bin ratios with a scratch script mirroring `plot.py`; it reproduces the old LepIDSF numbers); ID-only effects quoted as ratios of the No<ID> and No<Trig> sets; cutflow table last row; two new appendix figures (Central vs NoDblMuTrigSF, NoEMuTrigSF). 38 DiLepton figure copies refreshed, 8 added (60 in total); Trigger figures in `Figures/Trigger/2024/`, dimuon-leg plots in `Figures/LeptonID/2024/NUM_*Leg*/`. Full build: 74 pages, no undefined references.
- **Sources:** `Trigger/results/2024/{summary,closure}.txt`, `Trigger/data/2024/trigger_HcToWA.json` (md5 equal to the KNU copy), `SKNanoOutput/TnP/2024/NUM_{Mu17Leg1,Mu8Leg2}_DEN_HcToWATight_2024/efficiency.root`, `DiLepton/plots/AN/2024/*/{corrections.txt,cutflow.md}`, `zpeak.txt`, KNU `HcToWABase.cc:293-390`, `DiLepton.cc:206-208,600-619,931-964` (read only).
- **Findings / mismatches:**
  - `corrections.txt` Central totals (first histogram, plot range) differ from `cutflow.md` by up to 0.15% (EMU MC 6.866e5 vs 6.876e5); the AN takes yields from the cutflow and ratios from corrections.txt (ratios agree).
  - Binned MC closure exceeds the inclusive closure term: DIMU max|eta| 0.973-1.012, EMU 0.980-0.990 between the offline thresholds and 25 GeV.
  - Data DZ efficiencies depend on max|eta| (dimuon SF 0.994-0.997, e-mu 0.977-0.996) and e-mu on pT; the inclusive values are used and the MC closure cannot see this.
  - DIMU muon eta dips at |eta| ~ 0.25 remain with the trigger SF (0.938, 0.964 vs ~1.00), as expected from a leg SF uniform in |eta| < 0.9.
  - e-mu leg plots label DY "alt. MC"; it is reference only (AN caption says so; plot label not changed).
  - Not verified: whether the error bars of `efficiency.root` `data`/`sim` histograms (<= 4e-3 on the plateau) already include the fit systematics, as `makeTrigJson.py` states.
- **Open:**
  - rerun of the DblMuTrigSF / EMuTrigSF Up/Down lanes with the closure term (next DiLepton production); AN quotes the expected +-0.9% / +-0.4% (PLAN 2.4 step 4);
  - trilepton closure (signal, WZ, ttZ) for the closure term (PLAN 1, 2.4);
  - user: whether the binned non-closure and the DZ eta/pT dependence enter the uncertainty beyond the inclusive closure term (PLAN 2.4);
  - list of the flagged dimuon-leg fits for the appendix (PLAN 2.4 step 1 review); Ele23 turn-on shift in corrected pT not quantified (PLAN 2.4); comparison with the pT-picked B2G-25-013 formula (PLAN 2.4);
  - origin of the muon eta dips (PLAN 2.4); EMU 4% deficit and ttbar modelling (PLAN 2.2, 2.5).

## 2026-11-26 (step 3: TrigSF production, MC closure, closure term in the JSON)

- **Production** `DiLepton/Run{DiMu,EMu,ZEE}_RunSyst_TrigSF/2024` (MC only): all DAGs status 0 (ZEE 09:34, EMU 12:08, DIMU 12:11); synced to `SKNanoOutput/DiLepton/*_TrigSF/2024/`, where the data files are links to the LepIDSF data files (data histograms unchanged).
- **MC closure** (`Trigger/python/trigClosure.py` -> `Trigger/results/2024/closure.txt`, plots `Trigger/plots/AN/2024/closure/{DIMU,EMU}_{pt1,pt2,maxeta}`; lepton-level selection without the trigger requirement, observed path decision / expected from the MC legs, T1):
  - DIMU: DY 0.9914, tt 0.9928 (statistical errors < 1e-4). Flat in both lepton pT within ~0.3% up to 150 GeV (0.98-0.99 above). In max|eta| the same pattern in DY and tt, 0.973-1.012 in 0.25-wide bins, alternating within the leg |eta| bins [0, 0.9, 1.2, 2.1, 2.4]: efficiency structure inside the coarse leg bins (wheel gaps), which averages out inclusively.
  - EMU: tt 0.9968; flat above 25 GeV, 0.980-0.988 at 15-25 GeV (near the leg thresholds; cause not studied); max|eta| 0.974-1.017. DY -> tau tau 0.9828 +- 0.0011 (reference only, user decision (3)).
  - **Closure term (T3, largest inclusive |obs/exp - 1|):** DblMu 0.0086 (DY and tt), EMu 0.0032 (tt only; DY for reference). Signal and WZ (T3 list) follow with the trilepton selection.
- **JSON:** `makeTrigJson.py` adds the correction `TrigClosure` (input `name`: DblMu, EMu; read from `closure.txt`); other corrections unchanged (checked). Copied to KNU `HcToWA_Analyzers/data/2024/Trigger/` (previous version `hcto_prod/module_pre_trigsf/trigger_HcToWA.json.noclosure`). Central is unchanged by the term; the `*TrigSF_Up/Down` lanes of the TrigSF production were made without it (+-0.1% DIMU, +-0.3% EMU; with it about +-0.87% and +-0.44%). **Open:** the Up/Down lanes need a rerun (DIMU, EMU MC) to include the term; to be combined with the next DiLepton production.
- **DiLepton with trigger SFs** (`plot.py --all-lanes`, `PRODUCTION = "TrigSF"`; band now includes `DblMuTrigSF` / `EMuTrigSF`, `config/plotting/systematics_DiLepton.json`, previous version in the session scratchpad): data/MC DIMU 0.944 -> **0.992**, EMU 0.941 -> **0.957**, ZEE 0.983 (unchanged: no trigger SF measured for ee). Effect of each correction (MC / MC(Central)): DIMU NoDblMuTrigSF 1.051, NoMuonIDSF 1.114 (ID x trigger), NoPileupReweight 1.010; EMU NoEMuTrigSF 1.017, NoElectronIDSF 1.081, NoElectronRecoSF 1.099, NoMuonIDSF 1.048, NoBtagSF 1.024, NoPU 1.015, TopPt applied 0.986 (data/MC 0.970); ZEE NoElectronIDSF 1.148 and NoElectronRecoSF 1.193 now include the proxy trigger SF (chain). Cutflows (final line) and PW plots regenerated; Z-peak table unchanged (normalized shapes).

## 2026-11-26 (step 3: per-event trigger SF implemented; lanes follow the SF chain)

- **JSON:** `Trigger/python/makeTrigJson.py` -> `Trigger/data/2024/trigger_HcToWA.json` (copied to `HcToWA_Analyzers/data/2024/Trigger/`): DblMu_Mu17Leg, DblMu_Mu8Leg (tnp_tamsa nominal fit, error = stat (+) syst), EMu_{Mu23,Mu8,Ele23,Ele12}Leg (statistical; ECAL-gap row = 0.8-1.4442 row), PairFilter {DblMu_DZ, EMu_DZ}; ValType effData/effMC with Up/Down; clamp flow.
- **Code** (`HcToWA_Analyzers`, previous version `hcto_prod/module_pre_trigsf/`): `HcToWABase::LoadTriggerEfficiencies`, `TrigEff` (T1: 3^N leg states, nesting per lepton, x pairwise filter), `TrigSF` (data/MC; var up = data up and MC down, plus the closure term from an optional "TrigClosure" correction in quadrature, T3). DiLepton: factors `kFDblMuTrig` (DIMU), `kFEMuTrig` (EMU), lanes `DblMuTrigSF_{Up,Down,NotImplemented}`, `EMuTrigSF_*`, weight histograms; MC closure histograms `<ch>/Central/TrigClosure/{incl,pt1,pt2,maxeta}_{den,obs,exp}` (lepton-level DIMU / EMU selection without the trigger requirement; EMU without jet cuts; weight MC x PU).
- **Decided (user):** a `<Factor>_NotImplemented` lane removes the factor and every SF measured on top of it, since the trigger legs are measured on tight-ID leptons (and the electron ID SF on reconstructed electrons): NoElectronRecoSF also drops the electron ID and trigger SFs; NoElectronIDSF the e-mu trigger SF and the ZEE proxy trigger SF; NoMuonIDSF the dimuon and e-mu trigger SFs. Implemented as a factor mask per lane (`WeightLane::removed`).
- Plot band label: "Stat." when no systematic band is drawn (No<Factor>, _Applied sets), "Stat.+Syst." for Central (`plotter.StackCanvas`).
- **Test** (condor, one file each, TTLL powheg and DYto2Mu 2J; `hcto_prod/trigsf_test.sh`): per-event SF mean DIMU 0.952 (DY) / 0.946 (TT), rms 0.02; EMU 0.984 (TT), rms 0.03. Lane chain: DIMU NoMuonIDSF / Central 1.114 = muon ID (1.061) x trigger (1.050); EMU NoElectronRecoSF 1.099, NoElectronIDSF 1.081, NoEMuTrigSF 1.016. Up/down (statistical only) +-0.1% (DIMU), +-0.3% (EMU). **MC closure** (lepton-level selection, observed path decision / expected): DIMU 0.988 (DY), 0.989 (TT); EMU 1.001 (TT): ~1.2% dimuon non-closure, the closure term of T3 (to be measured on the full production, also vs pT and |eta|).
- **Production** `hcto_prod/submit_trigsf.sh` (MC only, label `TrigSF`: `DiLepton/Run{DiMu,EMu,ZEE}_RunSyst_TrigSF/2024/`); data histograms do not change with this code (no weights, closure MC only), so the plots take data from the LepIDSF production.
## 2026-11-26 (step 2 decisions: binning, uncertainties, pairwise filters)

- **Decided (user):** (1) e-mu leg binning as proposed (`Trigger/python/measEMuEff.py` BINS); no check of the turn-on bins in uncorrected pT, since the offline pT cuts are safely above the turn-ons. (3) DY is not a meaningful alternative MC for the e-mu legs: kept for reference only, not an uncertainty; the e-mu leg uncertainty is statistical (data Clopper-Pearson, MC weighted binomial), plus the closure term (T3). Supersedes the alt-MC part of T2 for the e-mu legs and pairwise filters. (4) Pairwise filters: one inclusive number each, for all pT and eta (supersedes the binned option of T6): dimuon DZ (= DZ_Mass3p8) data 0.99461, TT 0.99928, SF 0.9953; e-mu DZ data 0.98867, TT 0.99581, SF 0.9928 (Mu23Ele12; Mu8Ele23 0.98911 / 0.99622 / 0.9929, the same within 4e-4), one value for both e-mu paths, statistical uncertainty.
- **(2) Same-sign check, user asked whether requiring Qe + Qmu = 0 solves it:** the nominal selection is already opposite sign; the check subtracts the same-sign yield from the opposite-sign one as an estimate of the non-prompt contamination remaining in the opposite-sign sample (shift up to +2.2% for endcap electrons at 15-25 GeV). Proceeding with opposite sign only and nothing assigned unless the user decides otherwise.
## 2026-11-26 (steps 1 and 2: results for review)

- **Productions done:** MeasTrigEff data (Muon0/1, EGamma0/1, MuonEG) and MC (TTLL powheg, DY 2J) DAGs status 0; outputs synced to `SKNanoOutput/MeasTrigEff/`. Dimuon-leg fits done (`run_trig_legs.sh`, 00:16).
- **Step 1, dimuon legs:** fit check (`checkFitStatus.py`, pathologies policy) flagged 52 (Mu17) / 36 (Mu8) fit results; refits with likelihood offsetting (`hcto_prod/tnp_prod/refit_flagged.py`, extended to the trigger settings, previous version `refit_flagged.py.pre_trig`; `tnp_tamsa/config/HcToWA_fittest.py` imports `HcToWA_MuonTrig_2024`, previous `hcto_prod/tnp_prod/HcToWA_fittest.py.pre_trig`) accepted 43 / 33. Still flagged 9 / 3, among them Mu17 bin 6 (4 of its 9 fits: nominal, tag iso 0.1, 40 mass bins, fit range 75-115; corrected 2026-11-27 after the AN check, it said "all members"; ~700 passing probes, yield errors 3-7 x sqrt(S+B), background shape at its limit; a sub-threshold bin). Results copied to `SKNanoOutput/TnP/2024/NUM_{Mu17Leg1,Mu8Leg2}_DEN_HcToWATight_2024/`; maps and 1D plots with `LeptonID/python/plotSFMaps.py`, `plotEff1D.py` (configs added) in `LeptonID/plots/AN/2024/NUM_*Leg*/`. Plateau SF: Mu8 0.948-0.999 (median 0.969), Mu17 median 0.988; barrel data ~0.945 vs MC ~0.98. Sub-threshold Mu17 cells (pT < 16 GeV): efficiencies ~0, SF undefined (2.4 +- 4); the per-event formula uses the efficiencies, not the SF.
- **Step 2, e-mu legs and pairwise filters:** `Trigger/python/measEMuEff.py` -> `Trigger/results/2024/{emu_legs.root,summary.txt}`, plots `Trigger/plots/AN/2024/{legs,pair}/`. Proposed binning (open): electrons |eta_SC| [0, 0.8, 1.4442, 1.566, 2.0, 2.5], Ele12 pT [15, 17, 20, 25, 30, 40, 50, 100, 500], Ele23 [15, 20, 22, 24, 26, 28, 30, 35, 40, 50, 100, 500]; muons |eta| [0, 0.9, 1.2, 2.1, 2.4], Mu8 [10, 12, 15, 20, 30, 50, 100, 500], Mu23 [10, 15, 20, 22, ..., 500].
  - Mu8 / Mu23 plateau: data ~0.945 vs TT 0.973 in the barrel (SF ~0.97), as the Mu17 TnP leg (independent method, same muon filters); endcap SF 1.01-1.04.
  - Ele12: SF 0.92-0.97 at 15-20 GeV in the endcaps, ~1.0-1.05 in the barrel; Ele23 turn-on (22-26 GeV, corrected pT): data later than MC, SF 0.70-0.87 in 22-24 GeV (T4: scale correction of data +1.2% shifts the turn-on; uncorrected pT stored for comparison).
  - Checks (efficiency shifts): T5 conditioning (uncond) <= 3e-4: negligible; bit 6 alone +1 to +2.9% (bit 0 matters, T5); same-sign subtraction (ss) up to +2.2% for electrons at 15-25 GeV in the endcaps (several sigma; T2 says assign if significant: **to decide**); reference-trigger bias (ref) for the muon legs -4% at 10-20 GeV, -1.3% at 20-30, < 0.2% above: the e-mu muon-leg filter runs only after the e-mu L1 seed (Mu5_EG23 / Mu7_EG20 / Mu20_EG10 type), which a low-pT electron can miss without the Ele30 reference; for the Mu8 leg this matters only together with Ele23 (electron > 23 GeV), so the closure (step 3) should show whether it matters.
  - Alternative MC (DY 2J e-mu): statistically limited above 100 GeV (|DY - TT| up to 0.2 with DY errors of the same size): **proposed** count the alt difference only beyond its statistical error (as EGM's altMC rule) or merge the alt comparison above 50 GeV.
  - Pairwise filters: dimuon DZ data 0.99461 vs TT 0.99928 (SF 0.9953); Mass3p8 adds nothing (DZ_Mass3p8 = DZ to 4e-7 in MC, m > 50 GeV). Not flat in max|eta| (chi2 935/4: 0.9932-0.9967), flat in leading pT within ~5e-4. e-mu DZ SF 0.9928 (both paths), strongly eta dependent (data 0.9935 at |eta| < 0.9 to 0.965 at 2.4-2.5) and rising with pT: per T6 the binned values are used (max|eta|; pT dependence to decide).
- **Gates:** step 1 user review of the dimuon-leg maps; step 2 user review of the efficiencies and binning; then step 3 (JSONs, per-event SF, closure).
## 2026-11-26 (no trigger matching in the fake-rate measurement either)

- **Decided (user):** the fake-rate measurement is not trigger matched (muons and electrons alike), so no selection in the analysis uses trigger-object matching. Reason: NanoAODv15 keeps a muon trigger object only if it passes a quality bit, and no bit covers the final filters of Mu8/Mu17_TrkIsoVVL (`LOG_BkgEst.md` 2026-11-25, 2026-11-26). The trigger-leg efficiencies (TnP) still match to their own filters.
## 2026-11-25 (no trigger matching in the analysis)

- **Decided (user, from PLAN_BkgEst F9):** the analysis selections (SR, application region, control regions) do not require trigger-object matching; matching is used only in the fake-rate measurement and, as already, in the leg-efficiency measurements. The per-event trigger SF (T1) is therefore applied to events whose path may have been fired by objects other than the selected leptons; the MC closure of the trigger SF (step 3) covers this.

## 2026-11-25 (T3 revised: one nuisance per SF)

- **Decided (user):** each ID and trigger SF enters the fit as a single source, since these systematics are small compared to the others. Trigger: one nuisance for the dimuon SF and one for the e-mu SF (all legs and pairwise filters varied coherently, data up / MC down); the MC non-closure is added in quadrature event by event to the relative SF variation (our implementation of "single source"; replaces the four groups plus a flat closure term). AN `Sections/Trigger.tex` updated.

## 2026-11-25 (AN: Trigger section written)

- **Written** (an-writer) `docs/AN-26-267/Sections/Trigger.tex` (skeleton replaced): trigger selection (paths, reason, previous strategy studies not repeated); factorization into legs and pairwise filters; NanoAODv15 filter bits and new `tab:TrigLegDef`; dimuon legs (tnp_tamsa `HcToWA_MuonTrig_2024.py`: binning, softfit, systematic sets); e-mu legs (MeasTrigEff selection, IsoMu24 / Ele30 references, T5 conditioning, corrected pT, TTLL powheg); pairwise filters (path-decision ratios, selections, inclusive + binned check, T6); uncertainties (T2); per-event efficiency as the OR of the paths (T1, e-mu closed form, mu mu mu enumeration); fit nuisances (T3); MC closure (definition, samples); validation pointer. Results left as `XXX` (Fig./Table) with TODOs.
- **Numbers quoted**: only the two-file TTLL tests (Ele12 0.939 vs 0.949 with bit 6 alone; dimuon DZ = DZ_Mass3p8 = 0.9998; e-mu DZ 0.996-0.997), labelled as tests, and B2G-25-013's flat 2% / 3% and closure (0.1-2%, e-mu DY 3-5%) as the previous analysis.
- **Sources**: KNU `HcToWA_Analyzers/src/MeasTrigEff.cc` (bits, thresholds, selections, lines cited in the AN), `tnp_tamsa/config/HcToWA_MuonTrig_2024.py`, `2024/Trigger/HLT_Path.json`; `PLAN_Trigger.md`; entries below.
- **Status checked 2026-11-25**: `SKNanoOutput/MeasTrigEff/*/2024/` directories empty; dimuon-leg fits running.
- **Mismatches** (AN-25-154 vs 2024 code, written into the AN as method differences): e-mu electron leg = bit 6 AND bit 0 and conditioned on the muon leg (AN-25-154: bit 6, unconditioned); per-event efficiency = OR of the paths (AN-25-154 formula misses one mu mu mu case; its code picked legs by pT); pairwise efficiencies with uncertainty and from path decisions (AN-25-154 text: matched to filter objects; code: path decision, no uncertainty); muon-leg reference Ele30 (AN-25-154 text Ele32, code Ele30); no AltTag.
- **Open**:
  - how the two per-path e-mu DZ efficiencies enter the e-mu formula (one value or per term) (PLAN 2.4 step 3);
  - final eta / pT binning of the e-mu legs (PLAN 2.4 step 2);
  - offline pT thresholds of the trilepton selection (PLAN 1);
  - generator-level signal pT plots for 2024 (PLAN 4);
  - prescales of the reference paths (no local information) (PLAN 2.4);
  - merge `appendix:DiLeptonControlRegion` into `appendix:DiLeptonValidation` (AN structure, user) -- done 2026-11-26 (an-writer, `LOG_ObjectID.md`).

## 2026-11-25 (steps 1 and 2 launched)

- **Step 1, dimuon legs:** tnp_tamsa config `config/HcToWA_MuonTrig_2024.py` (KNU tnp_tamsa): the muon ID setup (`HcToWA_Muon_2024.py`: tag, ntuples, fit model, MC) with the probe required to pass our tight ID; numerators `probe_Mu17Leg1`, `probe_Mu8Leg2`; |eta| [0, 0.9, 1.2, 2.1, 2.4] x corrected pT (Mu17 [10, 14, 16, 18, 20, 25, 30, 40, 50, 100, 200], Mu8 [10, 15, 20, 25, 30, 40, 50, 100, 200]); method `softfit` (counting where a bin has < 100 effective pass or fail entries, e.g. below threshold); systematic sets as the ID SFs (tag iso, mass bins, fit range, alt signal MC, alt background), tag-iso expressions keeping the tight-probe requirement. Jobs on condor via `hcto_prod/tnp_prod/run_trig_legs.sh`.
- **Step 2, analyzer `MeasTrigEff`** (`HcToWA_Analyzers`, previous CMake/LinkDef in `hcto_prod/module_pre_trig/`), modes by user flag: `MeasElLegs` (Muon0/1), `MeasMuLegs` (EGamma0/1), `MeasDblMuPair` (Muon0/1), `MeasEMuPair` (MuonEG); MC (TTLL powheg, DY 2J to ee/mumu/tautau) with all modes. Leptons as DiLepton (our loose/tight IDs, corrected pT); e-mu = exactly one loose = tight muon and electron, dR > 0.4; dimuon pairs = two tight muons, no loose electron, OS, pT > 20/10, m > 50, dR > 0.3. Histograms (|eta| (electron |eta_SC|), pT), 1 GeV pT bins up to 60 GeV, for OS/SS, corrected/uncorrected pT, and in MC with and without the reference trigger; pairwise filters vs the larger |eta| and the leading pT. Implements T4-T7 (bit 6 AND bit 0 electron legs, bit-6-only and unconditioned variants stored).
- **Two-file tests (condor, `hcto_prod/trig_test/`):** run cleanly in data (Muon0 C/D/E) and MC (TTLL). TTLL, pT-integrated: Ele12 0.939 (bit 6 alone 0.949), Mu8 0.964, dimuon DZ = DZ_Mass3p8 = 0.9998, e-mu DZ 0.996-0.997. **Finding (T5):** the conditioned and unconditioned electron-leg denominators are identical in the tests: a tag muon passing IsoMu24 with pT > 26 GeV essentially always passes the e-mu muon leg, so the double counting B2G-25-013 risked is negligible in this tag setup; quantified with the full production. Bit 0 changes Ele12 by about -1% (MC), as expected from T5.
- **Finding (T2 alternative MC):** there is no tt dilepton amc@NLO sample in 2024 (`TTLL_Bin-MLL-*_amcatnlo` is tt + Z/gamma* -> ll; the TTto2L2Nu powheg tune / CR variants are not in our RNTuples), so the alternative MC for the e-mu legs and pairwise filters is DY 2J only, as in B2G-25-013. **To tell the user.**
- **Production** `hcto_prod/submit_trig.sh` (outputs `SKNanoOutput/MeasTrigEff/<flags>/2024/`), launched 16:5x; proxy 162 h.

## 2026-11-25 (T7: reference triggers)

- **Decided (user):** muon legs with `HLT_Ele30_WPTight_Gsf` (bit 18, offline e pT > 32 GeV), as in the B2G-25-013 code (its AN text said Ele32); electron legs with `HLT_IsoMu24` (bit 3, pT > 24; offline mu pT > 26 GeV). Ele30 gives more statistics, a path-specific matching bit, and is the trigger of our Z->ee region. All decisions T1-T7 of `PLAN_Trigger.md` settled.

## 2026-11-25 (T6: pairwise filters)

- **Decided (user):** inclusive efficiency per filter with statistical (+) alternative-MC uncertainty (B2G-25-013: one hardcoded number per era, no uncertainty), and binned in the larger |eta| of the pair (and pT) as a check; the binned values are used only if the inclusive one does not describe them within statistics. DZ (|dz| < 0.2 cm at HLT) is expected to lose efficiency mainly for forward / low-pT pairs; Mass3p8 is expected at ~1 for our selections (DiMu m > 50 GeV, signal m(mumu) >= ~12 GeV).

## 2026-11-25 (T5: electron-leg definition)

- **Decided (user):** electron leg = bit 6 AND bit 0 (+ pT threshold); B2G-25-013 used bit 6 alone, which an electron passing only the early filters of the leg also carries. Electron-leg denominator conditioned on the tag muon passing the same path's muon leg (bit 5, pT > 23 for Ele12, > 8 for Ele23): the e-mu electron-leg filters run only after the muon leg (HLT_2024v14 path sequences), so B2G-25-013's unconditioned electron-leg efficiency included the muon-leg inefficiency, which the per-event product then counted again. Both variants are stored to quantify the effects.

## 2026-11-25 (T4: probe pT)

- **Decided (user):** corrected pT for the trigger legs, consistent with the ID SFs (B2G-25-013 used `OriginalPt` for the muon legs). Noted: the HLT acts on online pT, closest to the uncorrected offline pT; with corrected pT the MC turn-on is broadened by the smearing and the data turn-on shifted by the scale, which can bias the SF within a bin near the thresholds; the uncorrected pT is stored too, and the closure test checks it.

## 2026-11-25 (T3: uncertainty in the fit)

- **Decided (user):** leg nuisances plus a closure term, instead of B2G-25-013's flat 2% / 3% (whose 2022-2023 e-mu DY closure was off by 3-5%, beyond the 3%). (a) Nuisances grouped as dimuon legs, e-mu muon legs, e-mu electron legs, pairwise filters (data up / MC down, coherent within a group); (b) per channel, a flat term = the largest MC non-closure |obs/exp - 1| over DY, tt, signal and WZ with the T1 formula.

## 2026-11-25 (T2: leg-efficiency uncertainties)

- **Decided (user):** e-mu legs = statistical (Clopper-Pearson for data; weighted binomial for MC; B2G-25-013 treated numerator and denominator as independent) (+) alternative MC (DY and TTLL amc@NLO vs TTLL powheg, the larger difference). AltTag dropped (Statistics Committee: no tag-selection variations); replaced by two checks assigned only if significant: same-sign subtraction of non-prompt contamination in data, and the reference-trigger bias in MC (leg efficiency without vs with the reference trigger). Dimuon legs: the ID-SF fit systematics. Pairwise filters: statistical (+) alternative MC.

## 2026-11-25 (T1: per-event efficiency)

- **Decided (user):** the per-event trigger efficiency is the true OR of the paths, built from per-object leg probabilities: nesting within an object (Mu23 => Mu8, Ele23 => Ele12, Mu17 => Mu8, exact for pT-threshold legs) and independence between objects (tested by the MC closure); enumeration of the 3^N object states; e-mu closed form eps = [M23 E12 + M8 E23 - M23 E23] x eps_DZ. Replaces B2G-25-013's pT-picked legs (which used El12 x Mu8 when both leptons were above 25 GeV, a combination no path requires) and covers the mu mu mu case missing from the AN-25-154 formula (mu1 passing only Mu8 with mu2 passing Mu17).

## 2026-11-25 (survey for phase 2.4; plan `PLAN_Trigger.md`)

- **Paths in 2024** (`SKNanoAnalyzer/data/Run3_v15_Run2_v15/2024/Trigger/HLT_Path.json`; datasets from cvmfs `CMSSW_15_0_2/src/HLTrigger/Configuration/python/HLT_2024v14_cff.py`, one menu version): Muon0/1: `IsoMu24`, `Mu17_TrkIsoVVL_Mu8_TrkIsoVVL`, `_DZ`, `_DZ_Mass3p8`; MuonEG: `Mu23_..._Ele12_..._DZ` and non-DZ, `Mu8_..._Ele23_..._DZ` and non-DZ; EGamma0/1: `Ele30_WPTight_Gsf`, `Ele32_WPTight_Gsf`. All HLT bits and all `TrigObj_*` branches are in our RNTuples. No prescale information for the reference paths (all entries carry the full 109.82 fb-1).
- **Filter bits, NanoAODv15** (`CMSSW_15_0_X PhysicsTools/NanoAOD/python/triggerObjects_cff.py`; identical in all 15_0_X for the bits used): muon (id 13) 0 TrkIsoVVL, 1 Iso, 3 1mu, 4 2mu (`hltDiMuon*Filtered*`), 5 1mu-1e; electron (id 11) 0 CaloIdL_TrackIdL_IsoVL (`*CaloIdLTrackIdLIsoVL*TrackIso*Filter`), 1 1e WPTight, 6 1e-1mu (bit 5 in NanoAODv12), 18 Ele30 only. Electron trigger objects require the pixel match. Consequences: Mu17 vs Mu8, Mu23 vs Mu8, Ele23 vs Ele12 only by the trigger-object pT; bit 4 matches the iso, DZ and Mass3p8 filters together and the Mu17/Mu8 pT filters match no bit; DZ and Mass3p8 only from path-decision ratios; e-mu electron filters run only after the muon leg, and the e-mu L1 seeds need an EG object, so e-mu legs need e-mu events with a single-lepton reference trigger.
- **Existing code:** DiLepton requires path decisions only (DIMU `Mu17_Mu8_DZ_Mass3p8`, EMU OR of the two DZ paths, ZEE `Ele30`) and has no dilepton trigger SF (proxy EGM `Ele30` SF in ZEE only). Our MuonTnPProducer stores `probe_Mu17Leg1`, `probe_Mu8Leg2` (bit 4, pT > 17 / 8), `probe_Mu23EMuLeg`, `probe_Mu8EMuLeg` (bit 5), `probe_IsoMu24`; ElectronTnPProducer stores `probe_Ele23EMuLeg`, `probe_Ele12EMuLeg` (bit 6), `probe_Ele32`; matching dR < 0.1. SKNano 2.0 has `TrigObjView::FilterBits()` and `MatchViewsToTrigObjs`, no named-bit API; POG trigger JSONs for 2024 cover IsoMu24/Mu50 only (MUO) and single-electron paths (EGM).
- **B2G-25-013 method** (AN-25-154 `Sections/Trigger.tex`, `Appendix/Trigger.tex`, `SystUnc.tex:54`; old SKNano `MeasTrigEff.cc`, `ClosDiLepTrigs.cc`, `MyCorrection.cc:667-866`; V3 `MeasTrigEff/python/{measEMuLegEff,measPairwiseEff,closTrigEff}.py`): dimuon legs by TnP fits (IsoMu24 tag, bit 4 + pT); e-mu legs by the reference-trigger method with cut and count (IsoMu24 tag for electron legs, Ele30 tag for muon legs; TTto2L2Nu MC; uncertainties: stat, AltTag, alternative MC DY); pairwise filters from path ratios, one number per era, hardcoded without uncertainty (e.g. Run 3 DZ_Mass3p8 SF 0.9993-0.9998); per-event efficiency from the AN formulas with "same object" leg correlation; in the fit a flat 2% (dimuon) / 3% (e-mu) by era from the MC closure. Closure: dimuon within ~0.1-2%; e-mu Run 3 DY off by 3.2-4.6% (2022EE-2023BPix).
- **AN vs code mismatches in B2G-25-013** (to avoid repeating): e-mu event efficiency picks legs by pT and uses El12 x Mu8 when both leptons are above 25 GeV (not the AN formula, not the OR of the paths); pairwise pass = path decision (AN: both muons matched to the filter objects); Run 3 muon-leg tag Ele30 in the code vs Ele32 in the AN; pairwise efficiencies without uncertainty; the AN's "statistical uncertainties" on the closure expectation are the propagated leg uncertainties.
