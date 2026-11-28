# LOG: BkgEst

Decisions and findings for the Background estimation section of AN-26-267. Newest entry first.


## 2026-11-28 (ttZ CR as the final validation region, user; AN by an-writer)

- **Decided (user, 2026-11-28):** "We forgot tt+Z control region - it should be noted also in Background estimation section as a final validation region"; "ttZ region do not have to be blinded". Supersedes the 2026-11-27 entry below that stated the ttZ CR of the previous AN as not part of the study.
- **Definition** (AN-25-154 `Sections/EventSel.tex:12`, `tab:RegionComparison_ttZ` :72-95, `Sections/BkgEst.tex:4-11`, `ssec:TTZCR` :1093-1100; old `PromptAnalyzer.py:489-490, 596-627`): exactly 2 OS electrons + 1 muon tight, no additional loose lepton; pT(e) > 15 (10) GeV tight (loose), pT(mu) > 10 GeV; EMu triggers with trigger-safe pT; 60 < m(ee) < 120 GeV; N_j >= 2, N_b >= 1; no MET cut. Signal-depleted (A -> ee suppressed by (m_e/m_mu)^2 ~ 2e-5), composition similar to the SR, orthogonal to e mu mu / mu mu mu, not blinded.
- **Implementation checked against the code:** SKNano `HcToWA_Run3` commit 6b1a017 (local clone, 2026-11-28 21:20; compile check local, not yet on KNU): TriLepton channel `2E1MU`, region `TTZ`, flag `Run2E1Mu`; `HcToWABase::PassEEMuPlateau` (mu > 25 and e1, e2 > 15, or (e1 > 25 or e2 > 25) and mu > 10 GeV, raw pT); `SelectLane` is2E1Mu (1 loose muon, exactly 2 veto electrons, both loose with pT > 15); OS electrons and the m(ee) window on pT_corr four-vectors; `inReg[kTTZ]` = N_j >= 2, N_b >= 1; data tight filled (not blinded); nonprompt lanes with both flavours of fake rates; MC weights as e mu mu (EMu trigger SF over all three leptons); histograms only (no SR / Train RNTuple). The selection agrees with the AN-25-154 definition. The ConvSF is not applied in TriLepton (it is applied downstream, per channel e mu mu / mu mu mu).
- **AN** (`docs/AN-26-267/Sections/BkgEst.tex`): section intro (four CRs, ttZ CR item), `tab:TriLepRegions` (e e mu column and the ttZ CR row), new subsection `ssec:BkgEst_TTZCR` (definition, role, three properties, the chi2 procedure of AN-25-154 as the planned test, proposed measurement region of the B2G blinded GoF, not decided), implementation status (6b1a017, next production). Most of the text was written by the interrupted an-writer run (21:17); this run updated the stale "being implemented / not yet checked" statements and the TODO phase tags. Section builds (rc 0).
- **Open:**
  - next production (after 2026-11-30), PLAN 3: ttZ CR yields per process, data/prediction, data/MC distributions with chi2/ndf and p-value (TODO in `ssec:BkgEst_TTZCR`).
  - user decision, PLAN 3.4 / 3.6: uncertainties of the nonprompt and conversion estimates in the ttZ CR test (30% / 20% of AN-25-154, or the 2024 nuisances) and which ConvSF applies to e e mu (only e mu mu and mu mu mu measured).
  - user decision, PLAN 6.1: ttZ CR as the measurement region of the blinded GoF (proposed; also in `LOG_Result.md`).
  - later phase, PLAN 5.3: ParticleNet scores in the ttZ CR.

## 2026-11-28 (DY vs DYG overlap)

- **DY 2J vs DYGto2LG overlap**: moved to the next iteration of the analysis (user), together with the eps_p treatment, the prompt subtraction of the fake rates and the DYGto2LG comparison. The SR prediction and the b-tag cross-check use DY 2J without DYGto2LG for now.

## 2026-11-27 (nonprompt nuisances in the templates, user)

- **Decided (user), S5 of `PLAN_Signal.md`:** F1 implemented as decided: per-flavour shape nuisances (muon, electron) from Total_Up / Total_Down of one flavour at a time, shared by e mu mu and mu mu mu; TriLepton gets per-flavour nonprompt weight fields (tree mode) and histogram lanes (now only both flavours together: +22 / -20% e mu mu, +18 / -16% mu mu mu). No per-channel lnN.

## 2026-11-27 (eps_p: deferred to the next iteration, user)

- **Decided (user):** eps_p = 1 is kept for the feasibility study (F4 (a), quantified by the closure: prompt LNT share 1.4% e mu mu, < 0.1% mu mu mu, vs rate uncertainty 7.2% / 11.3%); the prompt-rate treatment goes to the next iteration after the final limits, with the prompt subtraction of the fake rates and the DYGto2LG comparison. AN `Sections/BkgEst.tex` (`sssec:BkgEst_FkPromptRate`): user-decision TODO replaced by the statement and a next-iteration TODO. No user decision is left open in the background estimation.

## 2026-11-27 (WZ normalization uncertainty: 12%, correlated)

- **Decided (user):** WZ normalization uncertainty 12%, one lnN fully correlated between e mu mu and mu mu mu. It is |1 - r| (+) sigma(r) of the WZ CR ratio at N_jets >= 2, 0.072 (+) 0.095 = 0.12 (e mu mu) and 0.061 (+) 0.093 = 0.11 (mu mu mu), the larger for both. Supersedes the 10% of the entry below (my "~10%" was a wrong rounding of the same sum). AN updated: `Sections/BkgEst.tex` (WZ CR decision paragraph and its later-phase TODO), `Sections/Dataset.tex` (WZ paragraph). Effect on the expected SR background: 0.8% (e mu mu), 0.9% (mu mu mu).

## 2026-11-27 (AN: background estimation finalized for the feasibility study, an-writer)

- **V2 figures (22:16 production `Run1E2Mu_Run3Mu_V2`; convsf.txt, cr_summary.txt, convsf_HcToWA.json byte-identical):** 40 PNG copied to `Figures/BkgEst/2024/{ZFakeCR,ZGCR,WZCR}/`, all files present, and the six V2 blocks switched on (`fig:ZFakeCR`, `fig:ZGCRConvLep`, `fig:WZCRMain`, `fig:app-{ZFakeCR,ZGCR,WZCR}V2`), referenced from the text. The e mu mu captions state that the eta of the non-Z lepton is the electron eta, not eta_SC. Src lines point to V2. No 10% WZ value is left: the text says 12%, correlated, as edited by the coordinator. Section and appendix build alone (rc 0).
- **Written** (`docs/AN-26-267/Sections/BkgEst.tex`, `Appendix/BkgEst.tex`), from `TriLepton/results/2024/{convsf,cr_summary}.{txt,json}` (measConvSF.py, 16:26, production `Run1E2Mu_Run3Mu`), `TriLepton/python/measConvSF.py`, the TriLepton / GenLeptonType code (local clone = `TriLepton/analyzer/` = knu1 by md5; the production ran `hcto_prod/module_pre_trilep_v2`, which differs only by the V2 histograms), and the plots `TriLepton/plots/AN/2024/ConvSF/`:
  - Section intro: expected SR background (`tab:BkgSRComposition`, no data: nonprompt 53 / 56%, ttX 31%, WZ 7 / 8%, conversion 4 / 1%, ZZ 4 / 3%), list of the three CRs with purpose, the ttZ CR of the previous AN stated as not part of the study, region table `tab:TriLepRegions` (common selection, SR, Z+nonprompt, ZG, WZ), MC weights (C5) and data lanes.
  - Nonprompt part: application regions of SR / CRs (old TODO line 59); closure TODO replaced by the user decision (e mu mu kept, margin failure 1.07 sigma, prompt subtraction revisited after the full limit calculation); SR nonprompt yield change with the Total_Up/Down rates (both flavours together): e mu mu +22 / -20%, mu mu mu +18 / -16% (read from the SR Nonprompt lanes of the local data outputs; agrees with cr_summary in the CRs); Z+nonprompt CR paragraph (`sssec:BkgEst_FkZFakeCR`) with selection, 0.990 / 1.001, composition, rate-variation effect, FxFx ratios; yields table `tab:CRYields` (Z+nonprompt and WZ).
  - Conversion subsection: samples and stitching (C1), generator filter with the veto and the GenLeptonType port with its two corrections (C2), ZG CR selection (C3), Eq. `eq:ConvSF` and the uncertainty model with the theory fractions (C4), results `tab:CvSF` (e mu mu 0.759 +- 0.078, mu mu mu 0.95 +- 0.13; components 3.7 / 9.6 / 0.4% and 8.5 / 9.5 / 3.6%), `fig:ZGCRMass`, accepted; DYG cross-check (0.567 / 0.436, conversion x1.34 / x2.17) deferred with the double-counting reason.
  - Prompt background: SR prompt composition (ttX 74 / 72%, WZ 16 / 18%, ZZ 9 / 8%, others 2%). WZ CR subsection renamed "WZ control region": selection, 0.916 / 0.922 (FxFx 0.880 / 0.883), `tab:WZNjets`, `fig:WZCRNjets`, decision (no N_jet SF, 10% lnN shared by the channels).
  - Appendix: `appendix:ZFakeCR`, `appendix:ZGCR` (pre/post SF), `appendix:WZCR` filled (8 figures); 66 PNG copied to `Figures/BkgEst/2024/{ZFakeCR,ZGCR,WZCR}/`.
  - V2 (pending) commented figure blocks (ZCand_mass, nonZLep_pt/eta, jets_1_pt/eta; names `Figures/BkgEst/2024/<CR>/<CH>_<REG>_<preSF|postSF>_<var>.png`): main text `fig:ZFakeCR`, `fig:ZGCRConvLep`, `fig:WZCRMain`; appendix `fig:app-ZFakeCRV2`, `fig:app-ZGCRV2`, `fig:app-WZCRV2`.
  - Section and appendix build alone (rc 0; only cross-file references undefined); temp dirs removed.
- **Findings / mismatches:**
  - `Sections/Dataset.tex:290` still says the WZ normalization "is further corrected by the jet-multiplicity scale factors measured in the WZ control region": stale after the decision (no N_jet SF). `Dataset.tex:170` still carries the DYGto2LG `TODO: user decision`, settled by C1 (c). Not edited (other section).
  - `Sections/SystUnc.tex` `ssec:ConvSFSyst` and `ssec:WZSyst` are empty headers; the BkgEst text refers to them for the ConvSF lnN per channel and the 10% WZ lnN.
  - The 10% WZ uncertainty: |1 - r| (+) sigma(r) at N_jets >= 2 is 0.072 (+) 0.095 = 0.12 (e mu mu) and 0.061 (+) 0.093 = 0.11 (mu mu mu), not 10% as the decision entry states; the AN quotes 10% as decided, with "covers the deviation within its uncertainty". For the user.
  - The WZ N_jet ratio uses a flat 25% of the nonprompt yield as its nonprompt uncertainty (measConvSF.py:287), not the Total_Up/Down lanes (effect 16-26% of the nonprompt yield in the CRs); stated in the AN.
  - The Z+nonprompt CR is dominated by WZ (53-56% of the prediction; nonprompt 30-32%), so it tests the rates with limited purity; its >= 2-jet, MET > 40 GeV events are also in the WZ CR (the regions overlap, as in B2G-25-013).
  - Plots: the ZFake / WZ `trilep_mass` plots are drawn to 150 GeV with the overflow in the last bin, although the configured range is 50-300 GeV; the V2 `nonZLep_eta` of the electron is eta, not eta_SC (`pe[0].Eta()`, `TriLepton.cc:317`), unlike `electrons_1_scEta`.
  - `measConvSF.py` now defaults to the V2 tag (file 20:07); the results in the AN are from the first production (16:26).
- **Open:**
  - user decision: eps_p = 1 confirmation under F4 (prompt-LNT share 1.4% / < 0.1% vs 7.2% / 11.3%); `%% TODO (user decision)` kept (PLAN 3.2).
  - user: the 10% WZ value vs the quadrature sum 11-12% (PLAN 3.5, 3.6).
  - next iteration (after the final limits): prompt-subtraction method of the fake rates (closure, PLAN 3.1/3.3); DYGto2LG comparison with an overlap removal on the parent photon (C1 (b), PLAN 3.4).
  - ~~V2 production: switch on the six commented figure blocks~~ done (see below).
  - later phase: main simulated nonprompt sources in the SR (needs a nonprompt-MC mode; TTLL output not in the local copy, DY filtered to conversions) (PLAN 1, 3.3); nonprompt fraction on/off Z in the mu mu mu SR and composition after ParticleNet (PLAN 5.3, 6.1); ttX split in the SR; per-flavour effect of the nonprompt nuisances and their mmumu shape effect (PLAN 3.3, 6.1); correlation with 2022-2023 (PLAN 6.2); WZ in the SR after ParticleNet and the impact of the 10% nuisance (PLAN 3.5, 6.3); prompt-normalization m(ll) / nPV plots (appendix line 8, PLAN 3.1).
  - other sections: Dataset.tex:170 and :290 (above); SystUnc `ssec:ConvSFSyst`, `ssec:WZSyst` text.

## 2026-11-27 (WZ: no N_jet SF in 2024, normalization uncertainty instead)

- **Decided (user):** no WZ N_jet SF in the 2024 feasibility study; WZ (POWHEG, MATRIX NNLO normalization) gets a 10% normalization uncertainty, one lnN shared by e mu mu and mu mu mu, covering the WZ CR comparison at N_jets >= 2 (the SR jet multiplicity): (data - non-WZ) / WZ = 0.928 +- 0.050 (stat) +- 0.080 (nonprompt) (e mu mu), 0.939 +- 0.041 +- 0.084 (mu mu mu); |1 - 0.93| (+) its uncertainty ~ 10%. The 1-jet deficit (0.73 / 0.78) is outside the SR. Z+fake CR (>= 2 jets) closes at 0.99 / 1.00 without a correction. WZ is 7-8% of the expected SR background, so the nuisance moves the total by < 1%. Supersedes the B2G Run 3 WZ N_jet SF for this study (PLAN 3.5).

## 2026-11-27 (ConvSF accepted; DYG comparison deferred; WZ CR without the N_jet SF)

- **Decided (user):** "Conversion looks fine": ConvSF e mu mu 0.759 +- 0.078, mu mu mu 0.947 +- 0.126 accepted (step-3 gate). `convsf_HcToWA.json` installed in `HcToWA_Analyzers/data/2024/ConvSF/` (md5 identical to `TriLepton/results/2024/`).
- **Open item, next iteration after the final limits (user):** the comparison with DYGto2LG (C1 (b)), including the fix of the DY overlap removal for internal conversions.
- **WZ CR in the SR jet multiplicity** (input to the user's question whether the WZ N_jet SF is needed): (data - non-WZ) / WZ (POWHEG) for N_jets >= 2 (the SR requires >= 2 jets): e mu mu 0.928 +- 0.050 (data stat) +- 0.080 (nonprompt, 25%), mu mu mu 0.939 +- 0.041 +- 0.084: compatible with 1. The low 1-jet bin (0.73 / 0.78) does not enter the SR. WZ is 7% (e mu mu) / 8% (mu mu mu) of the expected SR background (MC and nonprompt prediction only; nonprompt 53-56%, ttX 31%).

## 2026-11-27 (conversion SF measured; WZ CR first look)

- **Inputs:** TriLepton production (`SKNanoOutput/TriLepton/Run1E2Mu_Run3Mu/2024/`, 86 of 87 outputs; TTLL job 1 still running, not an input), `TriLepton/python/measConvSF.py` -> `TriLepton/results/2024/convsf.{txt,json}`, `convsf_HcToWA.json` (correctionlib `ConvSF`, not yet installed on KNU: step-3 gate), plots `TriLepton/plots/AN/2024/ConvSF/` (overviews `overview_ZG.png`, `overview_WZ.png`).
- **Result (ZG CR, nominal C1 (a): DY 2J + TTG):**

  | | data | nonprompt | conversion MC | ZZ | WZ | ttX + others | SF | stat | nonprompt | theory | total |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | e mu mu | 2783 | 726.9 | 2449.6 +- 53.1 | 166.6 | 24.5 | 4.7 | **0.759** | 0.028 | 0.073 | 0.003 | 0.078 (10.3%) |
  | mu mu mu | 1504 | 397.1 | 611.5 +- 26.4 | 485.6 | 37.2 | 4.7 | **0.947** | 0.080 | 0.090 | 0.035 | 0.126 (13.3%) |

  Within the B2G ranges (e mu mu 0.51-0.75, mu mu mu 0.53-1.13 per era). The nonprompt component (fake-rate Total variation, about +-25% of the nonprompt yield) dominates; theory is small (mu mu mu: ZZ 4.2%).
- **Cross-check C1 (b) does not hold as built:** DYGto2LG + TTG + DY 2J (DYGVeto) gives SF 0.567 (e mu mu) and 0.436 (mu mu mu): the conversion prediction is 34% (e mu mu) and 2.2x (mu mu mu) larger than with DY 2J. Likely cause: the DY overlap removal vetoes only DY events with a prompt status-1 photon (pT > 10 GeV, dR > 0.1), but DY internal conversions (gamma* -> l l in the shower) have no final-state photon, so they are kept in DY while DYGto2LG also contains them (type 5): double counting, strongest in mu mu mu (internal conversions only). A fix needs the veto on the parent photon of the conversion pair (analyzer change and rerun of DY 2J): open, not done (user: no new analyzer run now).
- **WZ CR (after the ConvSF, POWHEG WZ, no WZ N_jet SF):** data / prediction 0.916 (e mu mu: 3366 vs 3673) and 0.922 (mu mu mu: 5243 vs 5688); WZ 69% of the prediction, nonprompt 20-23% (its Total_Up shift +188 / +232 events, about 5% of the prediction). With the FxFx WZ sample instead: 0.880 / 0.883. Data / prediction falls with MET (about 1.0 at 40-60 GeV, 0.8 above 120 GeV) and with the electron pT (e mu mu). (data - non-WZ) / WZ (POWHEG) by N_jets: e mu mu 0.98 (0 jets), 0.73 (1), 0.80 (2), 1.22 (>= 3); mu mu mu 0.94, 0.78, 0.90, 1.02: the 1-jet bin is low in both channels, so the N_jet dependence that motivated the B2G WZ N_jet SF is still there in 2024 (to be looked at under PLAN 3.5).
- **Z+fake CR (>= 2 jets, 0 b, on-Z):** data / prediction 0.990 (e mu mu), 1.001 (mu mu mu) with POWHEG WZ.

## 2026-11-27 (TriLepton analyzer: step 1 of PLAN_ConvSF)

- **Code** (C++, `HcToWA_Analyzers`; local copies `TriLepton/analyzer/`; previous module files `hcto_prod/module_pre_trilep/`; builds `hcto_prod/build_trilep{,2}.log`, no errors or warnings):
  - `GenLeptonType.{h,cc}`: port of the B2G-25-013 lepton truth classification (old `AnalyzerCore.cc` GetLeptonType and helpers) to GenView. Two deviations from the old code, its intent: absolute PDG ids in IsFromHadron (the old signed comparison missed W-, anti-top, positive leptons and negative hadrons in the ancestry walk) and |dphi| in the same-supercluster search (old: signed DeltaPhi).
  - `TriLepton.{h,cc}`: SR (>= 2 jets, >= 1 b), ZFake (>= 2 jets, 0 b, on-Z), ZG and WZ CRs (B2G selections, C3) for e mu mu and mu mu mu; MC tight events with the C5 weights; data tight events in the CRs only (**SR blinded**: no histogram and no preselection cutflow bin for tight data events); data loose-not-tight events with the fake weight (Central, Total_Up, Total_Down) in all regions; conversion filter with the veto (C2) for DY 2J, DYGto2LG, TTG; TTG / DYG photon-pT stitching on the leading LHE photon (C1); DYGVeto lane for DY 2J; truth histograms (event category before the filter and per region, lepton types, electron type vs genPartFlav).
- **Test** (condor, 3 files per sample, 25 jobs, all rc 0, 6-90 s per job; `hcto_prod/trilep_test.sh`; run directories deleted after the check):
  - Lepton types in the ZG CR of the conversion samples: 2/3 type 1 and 1/3 conversion types, as expected for Z -> ll + conversion. Electrons of types -5/-6 all have `Electron_genPartFlav` 22, internal conversions (4) mostly genPartFlav 1 (NanoAOD counts them prompt): the classifier agrees with NanoAOD where it can.
  - Type 0 (GenPart pruning) negligible: < 0.5% of the events in WZ / ZZ.
  - Conversion filter (after the pair cuts, DYto2Mu 2J MLL50, 3 files): 68% kept in e mu mu, 22% in mu mu mu; the veto share comes from the production (`event_category_prefilter`, added after the test).
  - DYGto2LG LHE cuts (diag/): photon pT > 10 GeV (1.4% of the events below, LHE level), dR(gamma, l) > 0.1, no |eta| cut; the PTG100 sample starts at LHE pT = 100 GeV, so the stitching on the LHE photon matches the sample definition. The DY overlap removal uses the same cuts on the leading prompt status-1 generator photon.
  - **Correction of my C1 statement** ("for mu mu mu, (b) changes nothing"): DYGto2LG does populate the mu mu mu ZG CR, through type 5 (gamma* -> mu mu from the matrix-element photon in the shower), 1/3 of its leptons there.
  - Prompt MC: WZ and ZZ events >= 99% all-prompt in every region; TTG populates the SR (b jets), hardly the ZG CR.
  - Data: tight events only in ZFake / ZG / WZ, nonprompt lanes in all regions; Nonprompt_Up / _Down move the nonprompt yield by about +-20%.
- **Production** `hcto_prod/submit_trilep.sh` (14:14): all Skim_TriLep data (MuonEG, Muon0, Muon1) and the 63 MC skims (stage-out tests excluded), flags Run1E2Mu, Run3Mu -> `SKNanoOutput/TriLepton/Run1E2Mu_Run3Mu/2024/`.
- **Post-processing** `TriLepton/python/measConvSF.py` (SF, uncertainty components per C4, cross-check with DYG, correctionlib `ConvSF`, ZG / WZ / Z+fake CR plots).
- Leftovers seen in `/pnfs` (not touched): `SKNanoSkim/2024/{MC,DATA}/Skim/choij/Skim_TriLep_StageOutTest_*`, and an empty `SKNanoOutput/TriLepton/Run1E2Mu_Run3Mu_TriTest/2024/`.

## 2026-11-27 (conversion SF: C1-C6 decided)

- **C6 (user): (a)**, one C++ TriLepton analyzer for SR, ZG CR, WZ CR ("no reason to use python"); **SR data blinded throughout the feasibility study** (rule added to `CLAUDE.md`).
- **C5 (user): the DiLepton weights** (PU, electron reco SF, our ID SFs, T1 trigger SF, b-tag 1a); no top pT, no muon reco SF (MUO 2024: ~1, only for high-precision analyses, not in the 2024 jsonpog), no WZ N_jet SF. ZG CR theory for ZZ: MATRIX nNNLO scale (+) PDF 4.2% (user; B2G 6.4%).
- **C4 (user): stat (+) nonprompt (Total_Up/Down rates) (+) theory, larger of up/down per component**, one lnN per channel, channels uncorrelated. Theory from the B2G Run 3 xsecErr with the 50% fallback, but WZ takes its theory uncertainty, not 50% (user; B2G Run 3 fell back to 50% for WZ because `KFactors.json` has no WZTo3LNu_powheg entry, `measConvSF.py:60-70`): MATRIX NNLO QCD scale (+) PDF, weighted over the channels of our cross section = 1.6%. A WZ N_jet SF may not be used in 2024 (low-pT jet issue resolved in NanoAODv15, user, not decided).
- **C3 (user): the B2G ZG CR selection unchanged** (`PromptAnalyzer.py:684-772`: 3 tight leptons, no extra loose, MET < 40 GeV PUPPI Type-I, N_b = 0, off-Z pair(s), |m(3l) - 91.2| < 10 GeV, trigger-safe cuts), on the 2024 objects; no extra N_jet diagnostics ("conversion background is a small portion of the background").
- **C2 (user): GetLeptonType port with a veto**: >= 1 tight lepton of a conversion type (4, 5, -5, -6) and no other lepton of hadronic origin or unmatched (types -1 to -4), in SR and CR, for all conversion samples; prompt MC unfiltered. Differs from the B2G code (no veto) and follows the B2G AN text.
- **C1 (user): (c)**, DY 2J + TTG nominal (as B2G), DYGto2LG + TTG with a DY overlap removal as the cross-check of the SF. TTG stitched on the generator photon pT (inclusive < 100, PTG100 100-200, PTG200 > 200 GeV). Details and step-1 checks in `docs/PLAN_ConvSF.md` C1.

## 2026-11-27 (closure: e mu mu result kept for the feasibility study, user)

- **Decision (user):** the e mu mu yield test fails at the margin (1.084 +- 0.079, 1.07 sigma; shape test passes), so the closure is kept as it is for the feasibility study; no method revision now. The prompt subtraction method is an open item for the next revision round, after the full limit calculation ("estimate prompt subtraction method as open item"). This supersedes the plan rule "a failure leads to a method revision" for this round.
- **AN:** `Sections/BkgEst.tex:335` still carries `%% TODO (user decision)` for the revision choice; to be replaced by this decision in the next an-writer pass.

## 2026-11-27 (MC closure in tt: mu mu mu passes, e mu mu fails the yield test)

- **Analyzer** `ClosFakeRate` (C++, `HcToWA_Analyzers`, new; previous module files `hcto_prod/module_pre_closfr/`; local copy `MeasFakeRate/analyzer/`; build `hcto_prod/build_closfr.log`, no errors or warnings): B2G-25-013 ClosFakeRate/MatrixAnalyzer selections on the HcToWABase objects (e mu mu: 2 loose muons + 1 loose electron (veto 10 GeV), EMu paths, trigger-safe cuts, pT_corr scaling, OS muons m > 12 GeV; mu mu mu: 3 loose muons, DblMu path, 20/10/10 GeV, |sum q| = 1, both OS pairs > 12 GeV; >= 2 jets, >= 1 UParT medium b jet); SR = all tight, SB = >= 1 loose-not-tight with w = -prod(-f/(1-f)) for each rate set of `fakerate_HcToWA.json` (installed in `HcToWA_Analyzers/data/2024/FakeRate/`); MC weight MCweight x lumi x PU; generator splits for F4. 4-file condor test (run dirs deleted), production `hcto_prod/submit_closfr.sh` (11:27, 13 jobs, status 0) -> `SKNanoOutput/ClosFakeRate/Run1E2Mu_Run3Mu/2024/`. Evaluation `MeasFakeRate/python/evalClosure.py` (renamed from closFakeRate.py: not an analyzer) -> `MeasFakeRate/results/2024/closure.{txt,json}`, plots `MeasFakeRate/plots/AN/2024/Closure/`. `Common/Tools/plotter.py` StackCanvas: optional dataLabel, hasData, rTitle (defaults unchanged).
- **Result (F3, QCD-MC rates; TTLL + TTLJ powheg):**

  | | N_obs | N_pred | (A) ratio | (B) chi2 / ndf, p | verdict |
  |---|---|---|---|---|---|
  | e mu mu, m(mumu) | 574.0 +- 3.6 | 529.4 +- 2.4 | 1.084 +- 0.079 (FAIL, 1.06 sigma) | 57.7 / 47, 0.14 (PASS) | **FAIL** |
  | mu mu mu, m_low | 409.2 +- 3.0 | 427.7 +- 2.3 | 0.957 +- 0.109 (PASS) | 23.7 / 40, 0.98 (PASS) | |
  | mu mu mu, m_high | | | (same) | 64.8 / 71, 0.69 (PASS) | **PASS** |

  Rate uncertainty in the prediction (data-rate groups): e mu mu 7.2% (stat 4.6, PromptNorm 0.3, AwayJet 5.5, BTag 0.8%), mu mu mu 11.3% (3.9, 2.2, 7.5, 7.3%).
- **Diagnostics:** obs / pred with the data rates: e mu mu 0.968, mu mu mu 0.831; with the tt-MC rates: 1.142, 1.056. Prompt loose-not-tight share of the prediction (F4, eps_p = 1): 1.4% (e mu mu), < 0.1% (mu mu mu). Observed events with all leptons prompt (genPartFlav 1 or 15): 5.3% (e mu mu), 3.5% (mu mu mu). On-Z / off-Z (mu mu mu): 0.957 +- 0.118 / 0.957 +- 0.106, both shape tests pass. e mu mu: the excess grows with m(mumu) (obs/pred 1.2-1.4 above 120 GeV).
- **Open (user):** e mu mu fails the pre-fixed criterion (A) by 1.06 sigma; per the plan a failure leads to a method revision, not a larger uncertainty. No change made yet.
- **AN (an-writer, 2026-11-27):** closure written in `docs/AN-26-267/Sections/BkgEst.tex` (`sssec:BkgEst_FkClosure`: selection, weights, criterion with binning/covariance as in `evalClosure.py`, results `tab:FRClosure`, diagnostics `tab:FRClosureDiag`, `fig:FRClosureMass`; FAIL stated, revision as `%% TODO (user decision)`) and `sssec:BkgEst_FkPromptRate` (F4 by the closure only, TnP sentence and TODO removed; prompt-LNT share 1.4% / < 0.1% vs rate unc. 7.2% / 11.3%, `%% TODO (user decision)` to confirm eps_p = 1); `Appendix/BkgEst.tex` `appendix:FakeClosure` (`fig:FRClosureZ`, `fig:FRClosureKinEMuMu`, `fig:FRClosureKin3Mu`). 19 PNG copied to `Figures/BkgEst/2024/Closure/`. Section and appendix build alone (rc 0, only cross-file references undefined); temp dirs removed.
  - Checks: local `MeasFakeRate/analyzer/ClosFakeRate.{h,cc}` identical to knu1 (md5); MCweight() = sign(genWeight) x xsec / sumSign (`AnalyzerCoreWeights.cc:297`), so the weight is the sign of the generator weight, not the generator weight.
  - Corrections: (A) deviation of e mu mu is (1.08436 - 1) / 0.07872 = **1.07 sigma** (1.06 above is from the rounded values). "Excess 1.2-1.4 above 120 GeV": summed ratio 1.25 above 120 GeV (1.06 below), single 4 GeV bins 1.03-1.40 (three bins below 1.2: 1.13, 1.03, 1.11); 17% of the observed e mu mu events lie above 120 GeV.
  - Observations, no action: the observed sample includes the all-prompt events (5.3% e mu mu, 3.5% mu mu mu), which the method does not predict by construction, as F3 defines it; the non-mass closure plots carry a statistical band only; merged-bin plots show "Events / bin" (not divided by width); the m(mumu) plots' last bin holds the overflow (196-inf for e mu mu).

## 2026-11-27 (conversion SF: survey of B2G-25-013, plan)

- **Survey** (Explore agent, AN-25-154, B2G-25-013, V3 TriLepton, SKNanoAnalyzer PromptAnalyzer/MatrixAnalyzer/AnalyzerCore): definition, samples, truth matching, ZG CR, formula, uncertainty, numbers and use summarized with file:line in `docs/PLAN_ConvSF.md` section 1. Three mismatches between the old note and code found (CR filter only for DYJets/TTG; no veto on non-conversion leptons despite the AN text; only the up shift used for the nonprompt and theory components).
- **Plan** `docs/PLAN_ConvSF.md`: TriLepton analyzer port (CR part first, prompt-MC and nonprompt modes), production on the Skim_TriLep skims, measConvSF.py; decisions C1-C6 open (user).

## 2026-11-27 (AN: fake-rate part finalized, an-writer)

- **Written** (`docs/AN-26-267/Sections/BkgEst.tex`, nonprompt subsection; `Appendix/BkgEst.tex`), from the final results `MeasFakeRate/results/2024/{mu,el}/` (run_rates.sh, 10:59-11:00, after the tt rerun) and `fakerate_HcToWA.json`:
  - changes vs B2G-25-013 rewritten for F1-F4, fit-based prompt scale, no top pT weight;
  - path per pT_corr bin as implemented (`measFakeRate.py:74-75`), TODO removed; MC weight without the top pT weight (checked `MeasFakeRate.cc:264` on knu1, file 10:14), TODO removed;
  - binning: no negative or undefined data bin; pT_corr > 200 GeV takes the last bin (flow clamp); rates clipped to [0, 0.95];
  - prompt subtraction rewritten: s_Z and checks (Z stat 0.5-3.9%, SS <= 1.8% of OS, sidebands -19% / +21%, nPV 2.4-4.4% higher in data, object syst 3.3-5.0% as information), W-region finding (tight 1.19/1.13/1.76-1.82, loose 1.37-1.49/3.79-3.84), bounded MT fit and delta = |s/s_Z - 1|, fit quality, effect vs the Z scale; `tab:FRPromptScale` filled (s_Z, W ratio, s/s_Z, delta, chi2/ndf fixed and fitted, with template stat);
  - rates: uncertainty definition and sizes, `tab:FRRatesMu`, `tab:FRRatesEl` (central +- total, from `rates_total.txt`), `fig:FakeRateMu`, `fig:FakeRateEl` (rates plots + maps), description (muon high-pT rise, electron rise above 35 GeV, data vs QCD MC);
  - transfer (F2, no correction; tt/QCD ratios), prompt rate (F4 (a)), uncertainty (F1, one shape nuisance per flavour), closure criterion (F3; the DY-closure sentence of the draft removed, not in F3).
  - Appendix: `appendix:HLTNorm` retitled "Prompt normalization of the prescaled paths" (bounded fits tight and loose, W-region MT and MET tight); `appendix:FakeRatePlots` (variations, flavour). `appendix:ZFakeCR` unchanged (TODO).
  - Figures copied to `docs/AN-26-267/Figures/BkgEst/2024/{FakeRate,PromptFit,WRegion}/` (40 PNG). Section and appendix build alone (rc 0; only cross-file references undefined); temp dirs removed.
- **Numbers recomputed from the final files** that differ from the entries below (written before the tt rerun or rounded): muon QCD MC / data below 30 GeV 0.91-1.07 (log: within ~5%); tt / QCD muons below 50 GeV 0.86-1.03, b 0.80-1.00 (log: 0.86-0.97, 0.80-0.96); muon loose chi2/ndf with s = s_Z 50-55 (log 39-55: 39.6 is the bounded fit); muon 100-200 GeV total 24-31% (log 24-30%); Ele8 tight sideband data / (s MC) 0.81 (log: data above by 0-20%); post-fit muon MT (bounded plots): 0.85-0.97 at 30-60 GeV, up to 1.24 at the Jacobian peak (Mu8 loose), 0.83-0.95 above 115 GeV (log: 0.85-0.9 and 0.8-0.85).
- **Muon high-pT rise:** the 100-200 GeV rates exceed the 50-100 GeV ones by 1.3-1.8 times the combined bin-by-bin total uncertainty (not within 1 sigma); QCD MC 0.07-0.14 there. Written factually.
- **Script inconsistencies found:** `measFakeRate.py` docstring (line 10) still lists "x top pT" in the MC weight; `fitPromptScale.py` docstring says "both yields free" (only the free mode); `makeFakeRateJson.py` docstring says F1 "decided later"; the free-fit files are `promptfit_MT.*` (no `_free` suffix); `promptfit_MET.*` (09:53) predate the tt rerun and are not regenerated by `run_rates.sh`; the JSON is in `MeasFakeRate/results/2024/`, not yet in `HcToWA_Analyzers/data/2024/FakeRate/` (PLAN section 3). Plots: in the PromptFit plots the k_QCD caption overlaps the legend; in `map_<fl>` the y-axis title is clipped. `MeasFakeRate.cc` line numbers after 263 shifted by one with the top pT removal; the AN src lines updated.
- **Open:**
  - user confirmation: no per-path pileup reweighting (nPV mean 2.4-4.4% higher in data in the Z window for all paths alike; PLAN F5 says "per-path PU reweighting if needed"; no explicit decision recorded) (PLAN 3.1).
  - later phase: prompt loose-to-tight efficiency from TnP (F4, PLAN 3.2); closure (ClosFakeRate port, PLAN 1, 3.3); effect of the nonprompt nuisances on the SR templates (PLAN 1, 3.3); Z+nonprompt CR (PLAN 1, 3.3); Z-window m(ll) and nPV plots (no plot script yet, PLAN 3.1); nuisance correlation for a combination (PLAN 6.2).

## 2026-11-27 (F2 decided; no top pT weight; MT/MET shape closed)

- **Decided (user), F2:** in the feasibility study no transfer correction (no flavour-based rates); the measured data rates are used with the bin-by-bin uncertainty, which covers the source dependence through the b-tag and away-jet variations.
- **Decided (user): no top pT reweighting in the search analysis.** `MeasFakeRate.cc` applied `TopPtWeight()` to tt powheg in the nominal MC weight (an-writer finding); removed (previous `hcto_prod/module_pre_notoppt/MeasFakeRate.cc`), rebuilt (`build_notoppt.log`, no errors or warnings). The old TTLL/TTLJ outputs in `SKNanoOutput/MeasFakeRate/MeasMuFR_MeasElFR/2024/` (2 files + provenance) were removed over xrootd (user permission, `hcto_prod/skim_debug/removed_2026-11-27_measfr_tt.txt`) and tt rerun into the same directory (`hcto_prod/submit_measfr_tt.sh`, 10:17, run `2026_11_27_101634_MeasFakeRate_MeasMuFR_MeasElFR`, 243 jobs). The other 20 prompt-MC samples are unchanged (`TopPtWeight()` = 1 for them). A first attempt with a separate output label (`NoTopPt`) was stopped before submission.
- **Decided (user), F3:** closure criterion = (A) yield test and (B) shape test, both required per channel, with the QCD-MC rates; on-Z / off-Z, the generator-matched split and the data-rate prediction as diagnostics (PLAN_BkgEst F3). Fixed before the closure is run (needs the ClosFakeRate port and the trilepton selections, PLAN 1 / 3.3).
- **Decided (user), F1:** a single shape nuisance per lepton flavour (`CMS_..._nonprompt_mu/_el`), up/down templates from the rates central +- the bin-by-bin total, coherent over bins and shared by the channels (B2G-25-013: lnN per era and channel). JSON syst `Total_Up` / `Total_Down` added (`makeFakeRateJson.py`, from `plotFakeRate.total_unc`).
- **Decided (user), F4:** option (a): eps_p = 1, quantified with the generator-matched closure split and the prompt loose-to-tight efficiency from the TnP ntuples (to do).
- **Corrections to numbers above (an-writer check against the final files, after the tt rerun):** muon QCD MC / data below 30 GeV is 0.91-1.07 (not ~5%); muon tt/QCD 0.86-1.03 (b 0.80-1.00); muon loose chi2/ndf with s = s_Z 50-55; Ele8 tight sideband data/(s MC) 0.81 (data not always above); the muon high-pT rise (100-200 GeV) exceeds the 50-100 GeV bin by 1.3-1.8 x the combined total uncertainty, so it is not inside its uncertainty. Docstrings of measFakeRate.py, fitPromptScale.py, makeFakeRateJson.py updated (no top pT; fit modes; F1).
- **Decided (user): no per-path pileup reweighting** for the prescaled paths (nPV 2.4-4.4% higher in data in the Z region, alike for all paths; rates bin by bin).
- **Decided (user): F4 is quantified by the closure only** (generator-matched split of the prediction); no tag-and-probe measurement of the prompt loose-to-tight efficiency in the feasibility study.
- **Closed (user):** muon MT shape and MET modelling are not pursued for the fake rates, since the rates are measured bin by bin (they affect only the prompt-scale fit quality, whose deviation from the Z-window scale is the PromptNorm uncertainty).

## 2026-11-27 (rates script, step-2 gate, first rates; W region contaminated)

- **Script** `MeasFakeRate/python/measFakeRate.py` (`--step gate|rates`; results `MeasFakeRate/results/2024/{mu,el}/{gate,rates}.{txt,json}`): prompt scale s per (path, ID) = data / (all 22 prompt-MC samples, all classes) in the OS Z window (bins 76-106 GeV); delta per (path, flavour) from the tight lepton = (a) Z stat (+) (b) W-region |data/(s MC) - 1| (+) (c) lanes on R = QCD region / Z window (JES, JER, unclustered, lepton scale/resolution; pileup reported, not included). Rates rebinned to the F7 grid, one path per pT_corr bin (V4 mapping: mu Mu8 < 30 GeV, Mu17 above; e Ele8 < 20, Ele12 20-35, Ele23 above), variations Away20/30/60, BTag, PromptNorm; QCD and tt MC rates per class. Plots `MeasFakeRate/python/plotWRegion.py` -> `MeasFakeRate/plots/AN/2024/WRegion/` (MT, MET; tight, loose; overview_{tight,loose}.png).
- **Gate:** s (tight) Mu8 1.58e-4, Mu17 2.76e-3, Ele8 1.07e-4, Ele12 6.10e-4, Ele23 5.19e-4 (Z stat 0.6-3.9%); objects (c) 3.3-5.0%; nPV mean in the Z region data 36.3-37.2 vs MC 35.4-35.6. Same-sign and sideband checks: data above s MC by 0-20% (non-Z content small).
- **Finding: the W region (MT > 60 GeV only) is not prompt-pure.** Tight data / (s prompt MC): Mu8 1.20, Mu17 1.13, electrons ~1.8 (loose 1.4-3.8), concentrated at low MET (Mu17 1.31 at MET < 25 GeV, electrons 2.7) and ~1 above MET 80 GeV (0.92-1.08); QCD MC (same s) is 5-35% of the data there. With QCD MC in the prediction, muon MT agrees within ~5% below 100 GeV, but MET still shows a tilt (data/pred 1.2-1.3 below 30 GeV, ~0.8 above 100 GeV), electrons also an overall excess of ~15-20%. So (b) as defined measures contamination (delta 0.13/0.20 mu, 0.76-0.82 e); its definition is open (user).
- **First rates (Central):** muons 0.53-0.56 (10-12 GeV) to 0.14-0.23 (30-50 GeV), agreeing with QCD MC within ~0.05 up to 50 GeV; above 50 GeV the data rate rises (0.16-0.26, 0.35-0.60 at 100-200 GeV) where 70-80% of the tight sample is subtracted prompt MC (not yet trustworthy). Electrons 0.27-0.38 (15-17 GeV), ~0.19 (20-35 GeV), rising above 35 GeV (known isolation feature). No bin negative. tt / QCD (nonprompt): muons 0.86-0.97 below 50 GeV, b-jet muons 0.80-0.96; electrons mixed.
- **Proposal (user): prompt scale from a template fit** in the inclusive single-lepton region (no MT/MET cut), checked in the Z window. `MeasFakeRate/python/fitPromptScale.py` (RooFit, extended binned ML, RooHistPdf templates prompt MC and QCD MC, both yields free; template statistics not in the likelihood; results `results/2024/<fl>/promptfit_{MT,MET}.{txt,json}`, plots `plots/AN/2024/PromptFit/`).
  - MT, tight: s_fit / s_Z = 0.954 (Mu8), 0.991 (Mu17), 1.066 / 1.077 / 1.067 (Ele8/12/23); fit stat 0.2-1.6%; Z check data / (s_fit MC) = 1.048 +- 0.026, 1.009 +- 0.006, 0.938 +- 0.036, 0.928 +- 0.015, 0.937 +- 0.016. chi2/ndf poor for muons (849/58, 1566/58: MT shape around the Jacobian edge and above 110 GeV), fine for electrons (114-312/58).
  - MT, loose: prompt is ~10% of the sample, the fit lowers s (Z check 1.33, 1.18, 1.37, 1.10, 0.95): not usable alone.
  - MET: fails (prompt yield -> 0 for loose; Z check 1.6-4.8 for tight): MET does not separate prompt and QCD here, and the MET tilt of the W region is visible.
  - k_QCD / s_fit = 1.1-1.3: the QCD MC normalization is roughly right.
- **Fit-quality check (user):** (1) prompt scale fixed to the Z-window s_Z, QCD free; (2) prompt scale bounded to s_Z (1 +- 0.3), QCD free (`fitPromptScale.py --mode zfixed|zbound`; results `promptfit_MT_{zfixed,zbound}`; plots `PromptFit/{zfixed,zbound}/`, overviews `overview_MT_{zfixed,zbound}.png`). chi2 now also with the template statistics in the variance.
  - No bounded fit reaches the bound (closest: Mu8 loose 0.753, Ele8 loose 0.731); the bounded fit equals the free fit.
  - Electrons: with s = s_Z, chi2/ndf (with MC stat) 1.1-1.5 tight, 1.2-2.3 loose; bounded 0.9-1.1 tight. The Z scale describes the MT distribution; the QCD MC statistics dominate the variance (chi2 without MC stat 126-399/59).
  - Muons: chi2/ndf 11-18 tight, 39-55 loose with s = s_Z, hardly better when s floats (tight 11.2, 17.7; s moves by 1-5%). The misfit is in the shape: the QCD-dominated MT 30-70 GeV (data / pred 0.85-0.9, loose 0.8) and the MT tail above 110 GeV (0.8-0.85); not the prompt normalization.
- **Decided (user): prompt scale = the bounded MT fit** (s within s_Z (1 +- 0.3)), per (path, ID), loose and tight; **uncertainty delta = |s_fit / s_Z - 1|** per (path, ID) (PromptNorm variation, coherent over IDs). Reason (user): in the loose sample QCD dominates, so the loose scale propagates little to the rate. Implemented `measFakeRate.py --scale fit` (default; `--scale zwindow` keeps the Z-window version, `rates_zwindow.*`); selection variations use s_fit x s_Z(sel) / s_Z(Nom). Scales relative to s_Z: Mu8 0.753 / 0.954 (loose / tight), Mu17 0.847 / 0.991, Ele8 0.731 / 1.066, Ele12 0.911 / 1.077, Ele23 1.050 / 1.067.
  - Effect on the data rates vs the Z-window scale: < 0.2% below 30 GeV (mu) and < 1% below 25 GeV (e), where the prompt fraction of the loose sample is <= 2%. Muons (Mu17): -1% (30-50 GeV), -5 to -7% (50-100), -18% (100-200); PromptNorm uncertainty 0.6-1.1%, 4-6%, 17-18% there. Electrons: up to -6% (barrel, > 50 GeV), PromptNorm up to 8%.
  - The high-pT muon rise remains (100-200 GeV: 0.29-0.49 vs QCD MC 0.07-0.14): not explained by the prompt normalization; open.
- **Decided (user): a bin-by-bin rate uncertainty is acceptable**, also where it is large (high pT_corr): the nonprompt leptons of the signal region are dominated by soft leptons. (Part of F1; the shape/lnN treatment stays open.)
- **Plots and JSON** (step 3, for the user review): `MeasFakeRate/python/plotFakeRate.py` -> `MeasFakeRate/plots/AN/2024/FakeRate/` (rates_<fl>_eta<i>: data with the bin-by-bin total vs QCD and tt MC; variations_<fl>_eta<i>; flavour_<fl>_eta<i>: QCD vs tt per b/c/light; map_<fl>; overview_rates.png, overview_var_flavour.png), per-bin breakdown `results/2024/<fl>/rates_total.txt`. `makeFakeRateJson.py` -> `MeasFakeRate/results/2024/fakerate_HcToWA.json` (FakeRate_Muon, FakeRate_Electron; syst Central, Stat, PromptNorm, AwayJet (60 / 20 mu, 30 e GeV), BTag, MC_QCD, MC_TT and per class; flow clamp, rates clipped to [0, 0.95]).
  - Total per bin (stat, PromptNorm, AwayJet, BTag in quadrature): muons 7-14% below 30 GeV (away-jet pT dominates), 8-20% at 30-50, 25-43% at 50-100 (b tag), 24-30% at 100-200 (stat, PromptNorm); electrons 5-36%, the b-tag variation dominating in most bins (up to 36%).
  - Data vs MC: muons agree with QCD MC within ~5% below 30 GeV; electrons below 20 GeV the QCD MC is 20-50% above the data.
- **From the BkgEst draft (an-writer, entry below):** `MeasFakeRate.cc` applies `TopPtWeight()` to tt MC (DiLepton has it only as an alternative): open (user).

## 2026-11-27 (AN: nonprompt subsection drafted, an-writer)

- **Written** in `docs/AN-26-267/Sections/BkgEst.tex` (section builds alone, rc 0; appendix with `--appendix`, rc 0; temp dirs removed):
  - section intro (three background categories);
  - nonprompt subsection: method (weight w = -prod(-f/(1-f)) over LNT leptons, eps_p = 1, pTcorr), changes vs B2G-25-013 (closure as pass/fail, transfer effect F2, eps_p F4, measured prompt-norm uncertainty, no trigger matching), sideband, measurement (triggers table `tab:FRTriggers`, no matching F9, event/object selection, Z region, binning F7, variations, MC flavour classes, samples F6/F8), prompt subtraction F5 (scale, components, no floor, W and nPV checks; `tab:FRPromptScale` with XXX), measured rates (TODO), transfer F2 options (open), prompt rate F4 (planned), uncertainty F1 (planned), closure F3 (planned), Z+nonprompt CR (later);
  - conversion and WZ subsections: one planned-approach paragraph each.
  - `Appendix/BkgEst.tex`: HLTNorm, new `appendix:FakeRatePlots`, FakeClosure, ZFakeCR, ZGCR, WZCR as skeletons with TODOs.
- **Sources:** `MeasFakeRate.cc`, `MeasFakeRate.h`, `Skim_FakeRate.{h,cc}`, `HcToWABase.cc` (knu1, read 2026-11-27); `hcto_prod/submit_measfr.sh`; PLAN_BkgEst sections 1-5; this log; local `SKNanoOutput/MeasFakeRate/*/2024` (28, 40, 22 ROOT files); AN-25-154 `BkgEst.tex:299,312-323`; V3 `MeasFakeRateV4/python/measFakeRate.py:196-206` (pTcorr ranges per path).
- **Mismatches found:**
  - `MeasFakeRate` applies the top pT weight in the nominal MC weight (`MeasFakeRate.cc:263`, `w0 = ... * TopPtWeight()`, TT powheg only), while the ObjectID section (`ssec:EventWeights`) says it is not applied by default in 2024 (DiLepton keeps it as an alternative). It affects the TT prompt subtraction and the TT MC rates.
  - The prompt-MC lanes include pileup up/down (`MeasFakeRate.h:51-55`), not listed in F5 (c) (JES, JER, unclustered, lepton scales). Written in the AN as implemented.
  - PLAN section 1 says QCD Mu/EM/bcToE "13 pT bins each"; the samples used are 12 per filter (`submit_measfr.sh`, `tab:QCDSampleList`).
  - PLAN section 1 table, binning row, tags the electron 1.444/1.479 question as F2; it was decided as F7.
  - Header comment of `MeasFakeRate.h:17-19` dates the no-matching decision "user, 2026-11-25"; this log has it on 2026-11-26.
  - The Ele8 offline cut (10 GeV) is superseded by the single-electron pT > 15 GeV requirement (`MeasFakeRate.cc:311`); same as V4's electron pTcorr bins starting at 15, but AN-25-154 `tab:trigger_pt_cuts` lists Ele8 as pT > 10, pTcorr > 10.
  - The pTcorr range per path is assigned in the rates script (not written); the AN states the V4 ranges (PLAN section 1) as planned.
- **Open:**
  - user decision: top pT weight in MeasFakeRate vs the ObjectID statement (PLAN 2.2, 3.1); F1 uncertainty model (PLAN 3.1, 3.3); F2 transfer option (PLAN 3.1, after step 3); F3 closure criterion, before the closure (PLAN 3.3); F4 eps_p treatment (PLAN 3.2); DYGto2LG in the conversion estimate (PLAN 3.4).
  - numbers pending from the rates script (PLAN 3.1): pTcorr range per path confirmed; prompt scales and delta components per (path, WP) (`tab:FRPromptScale`); W-region ratios; non-Z content (SS, sidebands); nPV check and any per-path PU reweighting; negative bins; pTcorr > 200 GeV treatment; data and MC rates and plots; ttbar/QCD ratios per flavour; effect of each F1 source on the yield.
  - later phase: closure (ClosFakeRate port, PLAN 3.3); prompt loose-to-tight efficiencies from TnP (PLAN 3.2); Z+nonprompt CR and SR composition (TriLepton port, PLAN 1); ConvSF (PLAN 3.4); WZ FxFx and the single WZ normalization source (PLAN 3.5, 3.6); nonprompt nuisance correlation for a combination (PLAN 6.2).

## 2026-11-27 (measurement production submitted, PLAN step 2)

- `hcto_prod/submit_measfr.sh` (08:03, detached; all three submissions rc 0), `MeasFakeRate`, `-n -100`:
  - `MeasMuFR` (`SKNanoRunlog/2026_11_27_080239_MeasFakeRate_MeasMuFR`, 54 jobs): Skim_FakeRate Muon0, Muon1 and the 12 MuEnriched QCD skims;
  - `MeasElFR` (`2026_11_27_080248_MeasFakeRate_MeasElFR`, 62 jobs): Skim_FakeRate EGamma0, EGamma1 and the EMEnriched + bcToE QCD skims (F8);
  - `MeasMuFR,MeasElFR` (`2026_11_27_080258_MeasFakeRate_MeasMuFR_MeasElFR`, 855 jobs): prompt MC unskimmed (F6), the 22 DiLepton samples (DY 2J per flavour MLL 10-50 and 50-inf, TTLL/TTLJ powheg, single top t/tW/s lep, WW/WZ/ZZ pythia, W 2J per flavour); systematic lanes for the Z-region normalization run automatically on prompt MC.
  **Done 2026-11-27 09:03:** all three DAGs status 0 (MeasMuFR 08:20, MeasElFR 08:10, prompt MC 09:03); 90 output files as expected (MeasMuFR 28 = 16 data periods + 12 MuEnriched; MeasElFR 40 = 16 + 24 EM/bcToE; prompt 22), synced to `SKNanoOutput/MeasFakeRate/<flags>/2024/` locally.
  Flags per input, so each output holds only the flavour it measures. Outputs `/pnfs/.../SKNanoOutput/MeasFakeRate/<flags>/2024/` (new stage-out script). Empty test directories `MeasMuFR_MeasElFR_FRTest*` from 2026-11-25/26 are still there (nothing deleted).

## 2026-11-27 (F7 binning decided; F8: QCD EM and bcToE samples are disjoint)

- **Decided (user), F7:** the proposed bins: muons pTcorr {10,12,14,17,20,30,50,100,200} x |eta| {0,0.9,1.6,2.4}; electrons pTcorr {15,17,20,25,35,50,100,200} x |eta_SC| {0,0.8,1.444,2.5} (ID barrel/endcap boundary instead of V4's 1.479; `MeasFakeRate` fills finer |eta| edges including both, `kEtaEdges` in `src/MeasFakeRate.cc`, so the choice is made when the rates are built). **No merging of the highest-pT bins**: a pT bin whose rate goes negative after the prompt subtraction takes the rate of the previous (lower) pT bin of the same |eta| row (user 2026-11-27).
- **Found, F8:** in RunIII2024Summer24 the EMEnriched and bcToE QCD samples are disjoint by construction. GEN fragments from McM (public API; GS requests GEN-RunIII2024Summer24GS-00024..00034, 00052 for EMEnriched and 00002..00012, 00051 for bcToE; all 12 pT-hat bins 15-20 ... 1000-inf, same pT-hat ranges in both):
  - bcToE: `generator * genParticlesForFilter * bctoefilter` (BCToEFilter: electron from b/c hadron, ET > 5 GeV, |eta| < 3.05);
  - EMEnriched: `generator * (genParticlesForFilter + ~bctoefilter + emenriched)`: the same BCToEFilter, inverted, then EMEnrichingFilter (isolated EM deposit, ET > 20 GeV).
  The two samples add up (each weighted by its own cross section x filter efficiency) without double counting: their union is the QCD phase space passing bcToE or (EM-enriched and not bcToE). The McM `notes` of these requests ("muon preselection") are copied boilerplate, not the filter. Combination as in V4 is valid. **Decided (user), F8:** electrons EMEnriched + bcToE (added with their cross sections), muons MuEnriched only.

## 2026-11-26 (no trigger matching in the fake-rate measurement)

- **Decided (user):** for consistency between the flavours, no trigger-object matching for muons or electrons (follows the finding below that the muon legs have no trigger object in NanoAODv15). Supersedes the matching part of F5 and F9: no trigger matching anywhere in the analysis. The measured lepton (single) or the leading lepton (Z region) is above the path's offline pT cut, as V4.
- **Code:** all matching removed from `MeasFakeRate` (leg bits, `Matched`, `QCDUnmatched`, `Diag/match`, `Diag/toBits`, trigger-object read); rebuilt rc=0, 0 warnings. Matched version kept in the session scratchpad only.
- **Test** (condor, Muon0 4 files, EGamma0 2, TTLL 2): all ran; no `Diag` directories; QCD-region T/L in data Mu8 0.25 (4 entries), Mu17 0.35 (23), Ele12 0.30 (10); TTLL prompt T/L 0.90-0.93 for all five paths, nonprompt b 0.2-0.5 (few entries). Test run dirs deleted from /d0.

## 2026-11-25 (implementation tests; muons not trigger matched; skim data and QCD only)

- **Implemented** in `HcToWA_Analyzers` (KNU, built rc=0, 0 warnings; backups `hcto_prod/module_pre_fr/`): `MeasFakeRate` (flags `MeasMuFR`, `MeasElFR`) and `Skim_FakeRate`. Two-file condor tests per sample, all rc=0: 19-69 s per job, ~7k events/s.
- **Muon leg bit (user asked whether it is right): there is none.** NanoAODv15 stores a muon trigger object only if it passes one of its quality bits (`skipObjectsNotPassingQualityBits = True`, `PhysicsTools/NanoAOD/python/triggerObjects_cff.py`, CMSSW_15_0_19). The last filters of the paths (2024 menu, CMSSW_14_0_19 `HLT_FULL_cff.py`) are `hltL3fL1sMu5L1f0L2f5L3Filtered8TkIsoVVLFiltered` (Mu8) and `hltL3fL1sMu1lqL1f0L2f10L3Filtered17TkIsoVVLFiltered` (Mu17); bit 0 "TrkIsoVVL" needs `*RelTrkIsoVVLFiltered0p4` or `*RelTrkIsoVVLFiltered` (dimuon paths), and no other bit covers them. A muon that fired only Mu8/Mu17 therefore has no trigger object; the "any L3 object above the online pT" match of the first version succeeded only for muons that also passed another filter (bits 1 Iso, 3 1mu, 5 1mu-1e dominate in Muon0, i.e. mostly IsoMu24). This explains the tests: match efficiency in Muon0 0.19 (Mu8) and 0.78 (Mu17), QCD Mu 0.35 (Mu8), and the tight-to-loose ratio matched vs unmatched 0.40 vs 0.13 (data Mu17), 0.71 vs 0.27 (QCD Mu, Mu8): the match selected isolated muons and would bias the rates.
- **Changed:** muon paths are not trigger matched (F5 matching applies to electrons only); muons keep the offline pT cuts (10, 20 GeV) and the single-loose-muon requirement, as V4. Electrons keep bit 0 (`*CaloIdLTrackIdLIsoVL*TrackIso*Filter`, the leg filters of Ele8/12/23_CaloIdL_TrackIdL_IsoVL_PFJet30; match efficiency 0.97-1.0 in all samples) and the `QCDUnmatched` check. SKNano reads no L1 muons, so an L1 match is not available.
- **Check of the fix** (Muon0, 4 files, rebuilt library): the muon match and `QCDUnmatched` histograms are no longer booked; single-muon entries (inclusive, loose) 3 -> 23 (Mu8) and 92 -> 115 (Mu17) against the matched version; QCD-region T/L 0.25 (Mu8, 4 entries) and 0.35 (Mu17, 23), low statistics. Test run dirs deleted from /d0.
- **Other test results:** TT sanity: prompt T/L 0.80-0.96; nonprompt b muons 0.36 (10-15 GeV) to 0.02 (> 50 GeV). Skim efficiency (2 files): Muon0 1.7%, EGamma0 0.87%, QCD Mu 20-30 16%, TTLL 83%.
- **Decided (user):** skim only data and QCD MC; the prompt MC (TT, DY, W, ST, VV) runs on the unskimmed samples (the skim keeps ~80% of them, no gain). Updates F6.

## 2026-11-25 (F6: skim)

- **Decided (user):** skim the fake-rate inputs (`Skim_FakeRate`: one prescaled fake-rate path fired, >= 1 loose lepton) for data and MC, to /pnfs SKNanoSkim; the measurement runs on the skims.
- F5 (prompt normalization): the user asked for the details of the scale measurement and of the uncertainty envelope before deciding.

## 2026-11-25 (F9: trigger matching)

- **Decided (user):** trigger-object matching is required only in the fake-rate measurement (measurement and Z regions); the analysis selections are not trigger matched (proposal of event-level matching not taken). Also recorded in `LOG_Trigger.md`.

## 2026-11-25 (F5: prompt normalization)

- **Decided (user):** prompt scale per (path, ID) from the Z region; uncertainty = Z statistics (+) W-region transfer (MT > 60 GeV) (+) object systematics on the transfer ratio to the measurement corner, in the prompt MC only; **no 15% floor**; the measured lepton **matched to the path's leg trigger object** in the Z and measurement regions (V4 did not match). Details in PLAN_BkgEst F5.
- **Question (user):** should the analysis leptons be trigger matched too? Proposed F9: event-level matching (fired path satisfied by matched selected leptons, as in the leg-efficiency definitions), not per-lepton. Open.

## 2026-11-25 (plan for fake rates and closure)

- **Scope (user):** this round covers the fake-rate measurement and the closure test only (PLAN 3.1-3.3); conversions, WZ and normalization uncertainties later, since they depend on the lepton and trigger SFs and the trilepton skims. Plan: `docs/PLAN_BkgEst.md`, open decisions F1-F8.
- **StatComm comment (user pointed to it):** `~/Sync/Documents/Paper/B2G-25-013/Reviews/CWR/forNextIteration.md` item 7, from R07-010 (`comments/COMMENTS_08_SYSTUNC.md:38`): a closure test is pass/fail, the non-closure must not be the systematic uncertainty. B2G-25-013 kept the chi2-scan lnN (10-40%; option A, short reply). Related: item 8 (eps_p = 1, Greg R06-013), item 6 (electron `dr03TkSumPt` only above 35 GeV; kept as is, user 2026-11-24). Also Section 8 referee items 2 and 8 (rate-measurement uncertainty not propagated; revoked past the PAS stage).
- **Survey of the old code** (`docs/previous_analysis/`):
  - MeasFakeRateV4 is the final version (V3 `CLAUDE.md:32`); V1-V3 legacy.
  - Triggers and pT^corr ranges per AN-25-154 `tab:trigger_pt_cuts`; one trigger per pT^corr bin (`measFakeRate.py:196-206`).
  - Prescales: none used; MC x full luminosity, scaled per (trigger, ID) to the data Z yield (`MeasFakeRateV4.cc:315-320`, `measFakeRate.py:71-145`; `prompt_scale.json`). `PromptNorm.csv` is a summary not read by code.
  - Variations PromptNorm +-15% (hard-coded), away-jet pT 60 / 20 (mu) / 30 (e) GeV, RequireHeavyTag were computed, but `convertLeptonFakeRateToJson.py:160` keeps only the central data rate; the fit used only the closure lnN (`Common/Data/FakeNorm.json`). Converter pT capped at 100 GeV; `MyCorrection.cc:433` clamps Run 3 muon pT^corr at 49 GeV.
  - No prompt rate anywhere (`TriLeptonBase.cc:75-107`, `MatrixAnalyzer.py:421-440`).
  - Closure: `ClosFakeRate` on TTLL powheg skims, no gen matching; QCD-MC rates nominal; chi2 scan in 5% steps (`MeasFakeRateV4/docs/CLOSURETEST.md`).
- **Efficiency of MeasFakeRateV4** (user: it took a long time):
  - string-keyed `FillHist` (TString path built per fill, `std::map<string>` lookup, `AnalyzerCore.cc:1849`) with ~1-2k fills per selected MC event (per fired trigger x loose/tight x variation; inclusive, per (pT^corr, eta) bin, QCD/W subregions, x5 for mother-jet flavours), ~10^4 fine-binned histograms per job; the rates use only bin integrals (`parseIntegral.py`);
  - `MotherJetPt` and `RequireHeavyTag` re-run `defineObjects` (`evtLoopAgain`), for loose and tight separately, though they are cuts on the central objects;
  - loose and tight as two full passes;
  - trigger check after `GetAllJets`, noise filter, `GetAllMuons` and veto map (`executeEvent:65-83`);
  - object systematics (JES, JER, lepton scales, UE) repeat the selection ~12 times per MC event while affecting only the Z-region normalization;
  - no skim: every iteration reads the full PDs and QCD samples.
- **Survey of 2024 inputs:**
  - all candidate prescaled paths are in the RNTuples; muon paths fire in Muon0/1, electron paths in EGamma0/1 (one file each: e.g. Muon0 Mu8_TrkIsoVVL 524, Mu17_TrkIsoVVL 540 of 54,567; EGamma0 Ele8/12/23 IsoVL_PFJet30 366/586/109 of 48,230). No prescale fields; `HLT_Path.json` lists 109820 /pb for every path.
  - MC: QCD Mu/EM/bcToE-enriched (13 pT bins each), W 2J FxFx and 4J MLM per flavour, DY 2J/4J, TT powheg (2L2Nu, LNu2Q, 4Q), single top, WW/WZ/ZZ inclusive pythia, WZto3LNu, ZZto4L. No exclusive WW/WZ 2l samples, no QCD HT bins.
  - `HcToWA_Analyzers`: no fake-rate or closure analyzer yet; loose/tight bits exist in `HcToWABase` (muon loose SIP3D < 5, miniIso < 0.4; electron loose SIP3D < 6, miniIso < 0.4, WP90 or MVA-noIso > 0.8/0.5/-0.8).
- **Open:** F1-F8 (PLAN_BkgEst section 5).
