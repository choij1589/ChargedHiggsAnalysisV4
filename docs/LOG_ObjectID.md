# LOG: ObjectID

Decisions and findings for the ObjectID section of AN-26-267: lepton, jet, b-jet and missing-transverse-momentum definitions and their corrections. Newest entry first.



## 2026-11-28 (AN: TriLepton b-tag cross-check with each process once, 33 MC samples)

- **Written** (an-writer), `Appendix/ObjectID.tex` `appendix:BTaggingEfficiency`, TriLepton cross-check only:
  - Sample sentence: each process is taken once. The alternative WZ sample (`WZto3LNu_1J_amcatnloFXFX`) and all six `DYGto2LG` samples are excluded, which leaves 33 MC samples. The "WZ counted twice" caveat is removed.
  - Jet counts (den entries): b 4.8e6, c 2.0e6, light 1.5e7 (they were 4.8e6, 2.2e6, 1.7e7).
  - Ratios TriLepton / TTLL for pT < 300 GeV (28 bins): b median 0.99 (0.92-1.01, no bin beyond 3 sigma); light median 1.07 (0.57-1.69, 2 bins beyond +3 sigma); c median 0.77 (0.43-1.07, 5 bins below -3 sigma).
  - c-jet composition: WZ 56%, TTLL 7% (it was 65% from the two WZ samples and 4% TTLL). The b efficiency at 600-1000 GeV and |eta| 2.1-2.5 is still 0.065.
  - `fig:app-BTagEffTriLepton`: copied the regenerated `BTagEff/plots/AN/2024/eff_{b,c,light}_TriLepton.png`; the md5 of each copy matches its source. Caption: "each process once". The median in the PLAN 2.5 TODO changes from 0.75 to 0.77.
  - The appendix builds on its own; the only undefined references point to other sections.
- **Sources** (2026-11-28):
  - Sample selection: `BTagEff/python/makeBTagEff.py:130-136` (the skip list).
  - `BTagEff/results/2024/efficiencies.txt`, block "33 MC samples summed". The file is dated 13:01 (the task said 13:10).
  - Ratios, pulls, entries and composition: computed from the unrounded histograms with a scratch script that calls `makeBTagEff.eff_hists` on the same 33 files and on `SKNanoOutput/DiLepton/MeasBTagEff/2024/TTLL_powheg.root`.
  - The TTLL JSON and the TTLL plots are unchanged: md5 1a24e3c6, and the AN copies are identical.
- **Mismatches:**
  - The task statement quoted the ratios from the 3-decimal table: b 0.99 (0.92-1.01), c 0.77 (0.43-1.07), light 1.14 (0.60-1.69).
    - Recomputing from that table gives light median 1.127 (0.600-1.688), c 0.769 (0.426-1.074) and b 0.992 (0.920-1.013).
    - The light efficiencies are 0.003-0.03, so rounding to three decimals shifts their ratios. The unrounded light median is 1.069 and the minimum is 0.569.
    - The AN uses the unrounded values (light 1.07, 0.57-1.69), as the previous entry did. The b and c values agree with the task.
  - One sample, `DYto2Tau_2J_MLL50toInf`, has a negative c-jet sum of weights below 300 GeV. Its effect on the sum is small.
- **Open:**
  - user (PLAN 2.5): whether the c-jet sample dependence (median now 0.77, driven by WZ) becomes an additional b-tag efficiency uncertainty.
  - user / BkgEst: the exclusion removes all `DYGto2LG` samples. That includes `DYGto2LG_1J_MLL4to50`, which covers m_ll 4-10 GeV, below the DY 2J samples (MLL10to50). TTG is kept together with TTLL. The cross-check should follow the sample list of the SR prediction once the DY/DYG overlap is decided (`LOG_BkgEst.md`).
  - Still open from the entries below: the SR yield / N_b comparison (PLAN 2.5 step 3), the plot style, the UParT WP study, and keeping the EMU HcToWABTagEff plot set.

## 2026-11-28 (AN: b-tag check in e-mu with the HcToWA map; TriLepton cross-check in the appendix)

- **Written** (an-writer):
  - `Sections/ObjectID.tex` `ssec:BTagSFEffect`: numbers and the left panel of `fig:BTagSFEffect` now come from the HcToWA map. The DiLepton EMU MC production is `RunEMu_RunSyst_TrigDZ_HcToWABTagEff`; the data are the unchanged MuonEG files of `RunEMu_RunSyst_TrigDZ`, which are links to LepIDSF. Changes: the weight scales the simulated yield by 0.980 (approximate map: 0.976); data/MC goes 0.934 -> 0.953 (approximate map: 0.957); ratios for 1-4 b jets are 0.928, 0.959, 1.43, 1.61 (approximate map: 0.933, 0.961, 1.44, 1.61; without the weight: 0.977, 0.880, 1.36, 1.43, unchanged); the gap between the 1- and 2-b bins is 0.031 (approximate map: 0.028). The measured map raises the simulated yield by 0.4% and moves every 1-4 b-jet ratio by at most 0.005. The 2026-11-28 TODO is closed. The old numbers are kept in the text as the comparison.
  - `ssec:BJetID`: states that the control-region results use the approximate map, except `ssec:BTagSFEffect`. Closed the TODO "rebuild libHcToWA.so before c657425": all 855 EMU job logs print the HcToWA map, and the snapshot JSON has md5 1a24e3c6 (= `BTagEff/results/2024/btaggingEff_HcToWA.json`).
  - `Appendix/ObjectID.tex` `appendix:BTaggingEfficiency`: the TriLepton cross-check replaces the two TODOs. It gives the selection from `TriLepton.cc#SelectLane` (all-tight MC, trigger, lepton pT, OS muon pair(s) with m > 12 GeV, conversion filter, before jet requirements; Central lane; gen x norm x PU) and the jet counts (b 4.8e6, c 2.2e6, light 1.7e7 entries). Ratios to TTLL for pT < 300 GeV, 28 bins: b median 0.99 (0.91-1.01, no bin beyond 3 sigma); light 1.0 (0.61-1.37, 5 bins beyond 3 sigma); c 0.75 (0.52-1.00, 12 bins beyond 3 sigma). New figure `fig:app-BTagEffTriLepton` (copies of `BTagEff/plots/AN/2024/eff_*_TriLepton.png` in `Figures/BTagEff/2024/`). The SR-yield TODO is kept.
  - Figure files: new `Figures/DiLepton/2024/EMU_HcToWABTagEff/Central/bjets_size.png`. The right panel keeps `Figures/DiLepton/2024/EMU/NoBtagSF/bjets_size.png`, which is byte-identical to the new production's NoBtagSF plot.
  - Both files build alone; only cross-references to other sections are undefined.
- **Sources** (2026-11-28):
  - knu1 `/pnfs/.../SKNanoOutput/DiLepton/RunEMu_RunSyst_TrigDZ_HcToWABTagEff/2024/*.provenance.json`: commit c65742573ab9, userflags `RunEMu,RunSyst,TrigDZ,HcToWABTagEff`, 22 MC. Local copies: md5 equal for TTLL_powheg and WZ_pythia.
  - Run dir `knu1:/d0/scratch/choij/SKNanoRunlog/2026_11_28_090131_DiLepton_RunEMu_RunSyst_TrigDZ_HcToWABTagEff`.
  - Plots: `DiLepton/python/plot.py --channel EMU --all-lanes`, run on a scratch copy of plot.py / Common/Tools / config/plotting with `PRODUCTION["EMU"] = "TrigDZ_HcToWABTagEff"`, and a scratch SKNanoOutput view (new MC + TrigDZ MuonEG). Output: `corrections.txt` Central MC 689183.3, NoBtagSF 703281.3 (identical to TrigDZ).
  - Per-bin ratios: computed with ROOT from `EMU/{Central,BtagSF_NotImplemented}/bjets/size`. Recomputing the TrigDZ numbers this way reproduces the 2026-11-26 values exactly.
  - Cross-check: `makeBTagEff.eff_hists` on the 40 TriLepton background files, compared with the TTLL file, using the unrounded histograms. The range ends differ in the last digit from the entry below, which used the 3-decimal table (light 0.60-1.38 -> 0.61-1.37, c max 0.99 -> 1.00).
- **Findings / mismatches:**
  - The S1 (b) cross-check sums all 40 TriLepton background samples. That includes both WZ samples (nominal `WZto3LNu` powheg and the alternative `WZto3LNu_1J_amcatnloFXFX`), so WZ is counted twice; DY 2J and DYGto2LG are both included (their overlap is open in `LOG_BkgEst.md`). The c jets of the cross-check below 300 GeV are 65% WZ (33% + 32%), 4% TTLL. The c sample dependence is therefore WZ vs tt; the "ttV" contribution named in the entry below is minor (ttZ 5%). The AN text states the double counting.
  - Figures without a durable source: the new EMU plot set (all lanes) exists only in the scratch run and in the AN copy. `DiLepton/plots/AN/2024/EMU/` still holds the approximate-map production, which the rest of the AN uses. To regenerate: the same plot.py with the EMU production switched and the MuonEG data linked into the new production directory.
  - The appendix caption at `appendix:DiLeptonValidation` (EMU figure) points to `fig:BTagSFEffect` for the b-jet multiplicity, which now uses the other map. Harmless; not changed.
- **Open:**
  - user (PLAN 2.5): whether the c-jet sample dependence (median 0.75) becomes an additional b-tag efficiency uncertainty. If it is quantified, use the cross-check without the double-counted WZ sample.
  - user / orchestrator: persist the HcToWABTagEff EMU plot set (e.g. a production switch in `DiLepton/python/plot.py` plus data links in `SKNanoOutput/DiLepton/RunEMu_RunSyst_TrigDZ_HcToWABTagEff/2024/`). Not done here (outside the an-writer scope).
  - later phase (PLAN 2.5 step 3): SR yield / N_b comparison approximate vs measured map (gate: user review, PLAN_Signal step 1).
  - user: plot style of `BTagEff/plots/AN/2024/` (now also the TriLepton panels in the AN).
  - later phase (PLAN 2.5): UParT WP study (`appendix:BTaggingWP`).

## 2026-11-28 (b-tag cross-check with the final TriLepton production)

- **Cross-check (PLAN_Signal S1 (b))**: `BTagEff/python/makeBTagEff.py --crosscheck` on the final TriLepton production (`..._HcToWABTagEff`, BTagEffHists of the TriLepton preselection, 40 MC samples summed, signal and data excluded; gen x norm x PU), against the TTLL map, pT < 300 GeV (28 bins per flavour): b ratio TriLepton/TTLL median 0.99 (0.91-1.01); light median 1.00 (0.60-1.38, statistics); c median 0.75 (0.52-0.99): the c efficiency is sample dependent (c jets from W -> cs / gluon splitting in WZ, ttV vs tt). The map stays the TTLL one (S1 (a)); the c dependence is a candidate for an additional b-tag efficiency uncertainty (open, later phase). Table `BTagEff/results/2024/efficiencies.txt` (replaces the partial Val cross-check), plots `BTagEff/plots/AN/2024/eff_*_TriLepton.png`; the JSON is unchanged.

## 2026-11-28 (AN: b-tag efficiencies measured on TTLL, method 1a map)

- **Written** (an-writer) in `docs/AN-26-267/Sections/ObjectID.tex` (`ssec:BJetID`, `ssec:BTagSFEffect`) and `Appendix/ObjectID.tex` (`appendix:BTaggingEfficiency`):
  - `ssec:BJetID`: the efficiencies in simulation are measured in dileptonic tt (pointer to the appendix); the results shown up to `ssec:BTagSFEffect` still use the framework map (semileptonic tt, other jet selection). `ssec:BTagSFEffect`: numbers unchanged (approximate map), last sentence now states the direction of the change; TODO to rerun DiLepton EMU.
  - Appendix: selection (as old `MeasJetTagEff.cc` on our objects), weights (gen x norm x PU, no SFs), binning, flavour definition, conversion; jet counts; `tab:app-BTagEff` (108 values), `fig:app-BTagEff` (b, c, light; copies of `BTagEff/plots/AN/2024/eff_*_TTLL.png` in `Figures/BTagEff/2024/`); comparison with the approximate map. Section and appendix build alone (only undefined cross-references; remaining overfull boxes pre-existing).
- **Sources** (2026-11-28): `BTagEff/results/2024/efficiencies.txt`; `SKNanoOutput/DiLepton/MeasBTagEff/2024/TTLL_powheg.root` (den / num entries: b 146539120 / 125138899, c 6897400 / 903401, light 103729472 / 1614309; statistical uncertainties sqrt(e(1-e)/n_eff), n_eff = den^2/sumw2: max 0.0020 / 0.0030 / 0.0003 (b / c / light) below 300 GeV, 0.0073 / 0.0050 / 0.0005 at 300-600, 0.060 / 0.038 / 0.0039 at 600-1000 GeV); code `DiLepton.cc#FillBTagEff` (947-970, after noise filters and jet veto map), `HcToWABase.cc#BookBTagEffHists,FillBTagEffHists` (274-310, commit 086164e), `#LoadBTagCorrections` (commit c657425: `data/2024/BTagEff/btaggingEff_HcToWA.json` unless flag `PreBTagEff`). The installed JSON is byte-identical to `BTagEff/results/2024/btaggingEff_HcToWA.json` (md5 1a24e3c6..., local and knu1). User approval of the map 2026-11-28 (task statement and the c657425 code comment; no earlier log entry recorded it).
- **Comparison with the approximate map** (`2024/BTV/btaggingEff.json`, md5 f023c1dc..., same on knu1; "HadronAnalyzer jet selection ... TTLJ_powheg_CustomBPH", |eta| 0/0.8/1.6/2.4, pT from 25 GeV, clamp), correctionlib ratios measured / approximate at |eta| 0.4, 1.2, 1.85, 2.3 and pT 25-800 GeV: b 0.983-1.014 (pT < 300, |eta| < 2.1), 0.946-0.982 (|eta| 2.3), 0.865-0.992 (> 300 GeV); light 0.34-0.77 (pT < 200, |eta| < 2.1), 0.62-1.21 (|eta| 2.3), 1.47-1.71 (800 GeV); c 0.99-1.68. `LOG_Computing.md` 2026-11-28 summary ("b within ~2%, light up to 3x lower, c higher by 30-50%") holds for b only below 300 GeV and |eta| < 2.1; c reaches +68%.
- **Mismatches / findings:**
  - knu1 `install/redhat/lib/libHcToWA.so` built 2026-11-28 00:22, before c657425 (08:00): the map is in the source tree on knu1 but the library still loads the era-config map. A rebuild is needed before any production meant to use it (blocked by the scratch purge of the Nano env).
  - Selection vs old `MeasJetTagEff.cc`: same lepton / jet requirements, except the jet cleaning uses loose electrons with pT > 10 GeV (old: 15 GeV); the triggers are our three paths (Section `sec:Trigger`). AN-25-154's text ("at least one electron and one muon") is less precise than its code (exactly one tight electron; the dimuon branch vetoes tight electrons); the AN-26-267 text follows the code.
  - The cross-check in `efficiencies.txt` ("TriLepton preselection, 2 MC samples") is the Val production (DYto2Mu 2J MLL50 + WZto3LNu only), not the planned S1 (b) cross-check with all MC (failed with the purge); efficiencies above 1 in some b bins (negative weights, few jets). Not shown in the AN.
  - Plots are plain ROOT style (not `plotter.py` "an"); the light-flavour legend covers the 200-600 GeV points.
- **Open:**
  - later phase (PLAN 2.5 step 3, blocked by the purge): rebuild on knu1; rerun DiLepton EMU and TriLepton without `PreBTagEff`; update `ssec:BTagSFEffect` numbers and `fig:BTagSFEffect`; SR yield / N_b comparison (gate: user review of the change of the SR prediction, PLAN_Signal step 1).
  - later phase (PLAN 2.5): S1 (b) cross-check with all MC from the TriLepton BTagEffHists production.
  - user: plot style of `BTagEff/plots/AN/2024/` (regenerate with `plotter.py`?).
  - later phase (PLAN 2.5): UParT WP study (`appendix:BTaggingWP`).

## 2026-11-27 (b-tag efficiencies: selection decided, user)

- **Decided (user), S1 of `PLAN_Signal.md`: (a)**, the previous method (`docs/previous_analysis/SKNanoAnalyzer/Analyzers/src/MeasJetTagEff.cc`): dilepton tt selection (tight e mu or >= 2 tight mu with the B2G triggers and pT cuts, >= 2 lepton-cleaned tight jets, pT > 20, |eta| < 2.5), hadron flavour, weight gen x norm x PU, previous |eta| x pT binning, UParT Medium, on TTLL; implemented as an option of DiLepton. Reason: the previous analysis did so, most statistics, and the SR is tt-like (signal, ttX and nonprompt about 90% of the expected SR background). Cross-check: the trilepton loose preselection, all MC, from the TriLepton tree production (option (b)). Replaces the approximate `2024/BTV/btaggingEff.json` after the user review (PLAN 2.5).

## 2026-11-27 (AN: ObjectID section and appendix finalized up to the open decisions)

- **Written** (an-writer) in `docs/AN-26-267/Sections/ObjectID.tex` and `Appendix/ObjectID.tex`:
  - New appendix section `appendix:LeptonIDFits` ("Lepton identification fits still flagged"): `tab:app-MuonIDFlaggedFits` (all 23 muon HcToWATight fit results still flagged: bin, variation, eta, pT, flag factor, dSF, largest dSF of the source, SF stat/total), electron paragraph (11 sim fits), `fig:app-MuonIDFlaggedFits`, `fig:app-ElectronIDFlaggedFits` (4 fit canvases copied from knu1 `tnp_tamsa/results/.../plots/` to `Figures/ObjectID/TnP/`). Section `ssec:LeptonIDSF` paragraph on the fit checks now points to it and states the effect.
  - MET (`ssec:MET`): what the jet term does and that it does not follow the Type-I definition; TODO kept, reworded.
  - Effective areas: origin (2016 HLT menu, smallest values, per AN-25-154 footnote; code values identical, `HcToWABase.cc:87-88,94-95`) stated; TODO reworded as information not in our inputs.
  - DiLepton figures: captions and `%% src` lines for DIMU / EMU moved to the TrigDZ production; `fig:DiLeptonOverview` caption now says the trigger-SF band contains the leg and DZ uncertainties. ZEE stays TrigSF.
  - Jet-veto fraction (88.7% / 93.0%) re-read from the TrigDZ DIMU histograms (data 0.8870, simulation 0.9297; was the 2026-11-24 print).
  - TODOs reworded with their type (user decision / user review / later phase / not in our inputs); duplicates removed: the three b-tagging TODOs of the section are merged into the two appendix TODOs (PLAN 2.5); the EMU TODO no longer repeats the top-pT and b-tag items. "Skeleton: to be written" replaced by a sentence.
  - Section and appendix build alone (temp dirs removed); only undefined cross-references to other sections; the overfull boxes are in unchanged paragraphs (l. 68-76, 159, 571 top-pT formula).
- **Numbers and checks** (2026-11-27):
  - Muon flagged fits (`SKNanoOutput/TnP/2024/NUM_HcToWATight_DEN_TrackerMuons_2024/checkFitStatus.txt`, `efficiency.root`; bin = 13 x pT index + eta index, checked on the knu1 plot names): 12 data (signal-yield error 3.2-6.7 x sqrt(N)), 11 sim (efficiency error 3.2-11 x count error; 10 of them the NLO-sim set s4m0). Two nominal fits (data bin 103, eta 2.1-2.4, 60-120 GeV; sim bin 78, eta -2.4..-2.1, 50-60 GeV): SF stat 0.0019 / 0.0018 vs 0.0012 / 0.0007 in the mirrored bins. 21 variations: |dSF| <= 0.0051; 16 of them define their source's systematic (tag iso / mass bins / fit range <= 0.0014; NLO sim 0.0008-0.0051). No central SF depends on a flagged fit.
  - Electron flagged fits (`.../NUM_HcToWATight_DEN_RecoElectrons_2024/checkFitStatus.txt`, `config.txt` bin_map): 6 alt-signal sim fits at 10-20 GeV (all eta_SC bins except |eta_SC| < 0.8; +0.017 to +0.021 vs the gen-matched count), 5 alt-MC (LO DY) sim fits at 200-300 GeV (0.010-0.021). Neither enters `combineElectronEGM.py` (inputs data_s0m0, data_s1m0, data_s2m0, sim_s0m0): no effect.
  - TrigDZ vs TrigSF: 244 histograms used by the AN numbers (DIMU, EMU; Central, MuonIDSF / DblMuTrigSF / PileupReweight / BtagSF / ElectronIDSF / EMuTrigSF NotImplemented, TopPtReweight_Applied) are bit-identical in every MC file; `corrections.txt` of DIMU / EMU equal to the TrigSF values; the AN figure copies are identical to `DiLepton/plots/AN/2024/` (55 files). No number in the text changes.
  - MET code (knu1, read only): `PropagateJetSystToMET` (`AnalyzerCoreJets.cc:557-597`) loops over `GetAllJetViews()` (all NanoAOD jets) and subtracts sum(pT_smeared/corrected - pT_NanoAOD) with no pT, EM-fraction or muon-subtraction requirement and no lepton cleaning; `DiLepton::LaneMET` adds the muon and electron terms. The Type-I criteria (15 GeV, EM < 0.9, muons subtracted) come from the Run 2 MET TWiki, not copied into `docs/CMS` (only referenced by `JME_JetVetoMaps.md:31`).
  - Jet-ID variable distributions: no energy-fraction or multiplicity histograms in the DiLepton outputs (`EMU/Central/jets/1` has eta, mass, originalPt, phi, pt, rawPt): stays PLAN 2.6.
- **Mismatches / findings:**
  - `LeptonID/plots/AN/2024/summary.txt` was overwritten on 2026-11-26 by the trigger-leg configs (Mu17Leg1, Mu8Leg2 only); the AN cited it for the ID SF ranges and the flagged-fit counts. Re-read from `efficiency.root` / `sf_egm.root` / `checkFitStatus.txt`: same values (electron median 0.9496, quoted 0.950).
  - The muon fit plots on knu1 date from the production (10:41-10:45, 2026-11-25); the accepted refits have no new plots. The flagged fits were kept as produced, so their plots are the ones used.
  - The jet term of the MET does not follow the Type-I definition (see above); size not evaluated.
- **Open:**
  - user decision / review: SF map review (PLAN 2.3 step 5); final ID-SF check in DiLepton (PLAN 2.3 step 6); electron SF uncertainty above 300 GeV; EMU normalization (PLAN 2.2); top pT reweighting (PLAN 2.2); pileup recommendation and nPV shift (PLAN 2.2); whether to study the muon eta dips (PLAN 2.4).
  - later phase: b-tag WP study and efficiencies, repeat of the b-tag check (PLAN 2.5); PUPPI / jet requirements and jet-ID distributions (PLAN 2.6); MET jet term vs Type-I (PLAN 2.6); trilepton lepton thresholds (PLAN 1).
  - not in our inputs: 2024 online effective areas (2024 HLT menu, ConfDB) (PLAN 2.4); JME Type-I recommendation for PUPPI ptmiss in Run 3 (to be copied into `docs/CMS`).
  - computing: pin the cvmfs snapshots before the final results (`LOG_Computing.md`).

## 2026-11-26 (AN: ObjectID numbers and figures moved to the TrigSF production)

- `Sections/ObjectID.tex` / `Appendix/ObjectID.tex` updated with the trigger section (details, sources and open items in `LOG_Trigger.md` 2026-11-26 "AN: trigger SF results written"): `tab:DiLeptonYields`, effect paragraphs, Z-peak DIMU row (MC 90.722 / 3.180, uncorrected 90.675 / 3.150, shift -0.047), figure copies. The ZEE-statement mismatch noted below is fixed in `Sections/Trigger.tex`.

## 2026-11-26 (DiLepton plots now from the TrigSF production)

- `DiLepton/plots/AN/2024/` regenerated from `Run*_RunSyst_TrigSF` (ID SFs and trigger SFs in Central; details and the per-correction table in `LOG_Trigger.md` 2026-11-26): data/MC DIMU 0.992, EMU 0.957, ZEE 0.983. New directories `DIMU/NoDblMuTrigSF`, `EMU/NoEMuTrigSF`; the No<ID> directories drop the trigger SFs too (chain). Previous corrections tables and cutflows (LepIDSF) kept in the session scratchpad only; the numbers are in the LepIDSF entry below. The AN figures (`Figures/DiLepton/2024/`) and `tab:DiLeptonYields` still show LepIDSF: to update with the trigger section.

## 2026-11-26 (AN: ObjectID restructured around the dilepton control regions)

- **Written** (an-writer, user decision of 2026-11-26 "define the control regions first and show how the corrections take effect") in `docs/AN-26-267/Sections/ObjectID.tex`:
  - new `ssec:DiLeptonValidation` "Dilepton control regions" right after the correction-file table (label kept, so Trigger.tex and the jet-veto table still resolve): purpose of DIMU / EMU / ZEE, `tab:DiLeptonRegions` with the weights now applied (DIMU: PU, muon ID; EMU: PU, ele reco, ele + mu ID, b tag; ZEE: PU, ele reco, ele ID, proxy trigger SF) and a new "Tests" row, proxy-trigger-SF paragraph (proxy ID SF removed: not used since the LepIDSF production), `tab:DiLeptonYields` rebuilt from the LepIDSF production (Central and one row per removed correction), `fig:DiLeptonOverview` (Central), trigger-SF TODO (PLAN 2.4).
  - "Effect ... in the control regions" subsubsections: electrons (`ssec:ElectronCorrEffect`: Z peak, `tab:ZPeak`, `fig:ZPeakEle`, reco SF yields), muons (`ssec:MuonCorrEffect`: `fig:ZPeakMu`), lepton ID SFs (`ssec:LeptonIDSFEffect`: `fig:MuonIDSFEffect` DIMU muon eta Central | NoMuonIDSF, `fig:ElectronIDSFEffect` ZEE eta_SC Central | NoElectronIDSF; results stated, user check pending), jets (`ssec:JECEffect`, raw vs corrected pT), b tagging (`ssec:BTagSFEffect`, `fig:BTagSFEffect` EMU N_b Central | NoBtagSF), event weights (`ssec:EventWeightEffect`, `fig:PileupEffect` DIMU nPV Central | NoPileupReweight; top-pT optional, numbers only).
  - old subsubsections "Scale factors in the validation regions" (`ssec:ZeeValidation`), "Event yields", "Lepton momentum scale and resolution", "Pileup", "Jets" removed; content moved as above.
- `Appendix/ObjectID.tex`: `appendix:DiLeptonValidation` reorganised by channel (dimuon, electron-muon, Z->ee, pileup + jet veto map) with Central plots and Central | No<Factor> pairs; new cutflow table `tab:app-DiLeptonCutflow`; `fig:app-DiLeptonWeights` replaced by `fig:app-DiLeptonTopPt` and `fig:app-DiLeptonEMuSF`; `fig:app-DiLeptonPileup` now EMU + ZEE (label kept, cited in Dataset.tex). `appendix:DiLeptonControlRegion` (`Appendix/Trigger.tex`) merged into it (open item of `LOG_Trigger.md`); TODO comment in `Sections/Trigger.tex` updated.
- Figures: every `docs/AN-26-267/Figures/DiLepton/2024/` copy refreshed from `DiLepton/plots/AN/2024/` (LepIDSF production; the previous copies were the 2026-11-24 proxy-SF plots); 16 added (NoMuonIDSF, NoElectronIDSF, NoElectronRecoSF, NoElectronTrigSFProxy, ZEE NoPileupReweight, TopPtReweight_Applied/electrons_1_pt, a few Central). AN builds, 63 pages, no undefined references.
- **Numbers** (2026-11-26): `corrections.txt`, `cutflow.md`, `zpeak.txt` of `DiLepton/plots/AN/2024/`; per-bin ratios computed locally from `SKNanoOutput/DiLepton/Run*_RunSyst_LepIDSF/2024` with `histutils` as in `plot.py` (Central vs `<Factor>_NotImplemented`, `_Applied` with Central fallback):
  - DIMU nPVsGood mean: data 36.8, MC 35.5 (PU weight) / 32.5 (none); ratio with weight 0.76-0.84 at 5-35, 1.01 at 40-45, 1.6 at 50-55.
  - DIMU leading-muon eta: muon ID SF raises the ratio by 5-9% per bin; Central 0.90-0.98; the dips at -0.3..-0.2 (0.883) and 0.2..0.3 (0.907) keep the same relative depth without the SF (0.835, 0.859).
  - DIMU subleading-muon pT 10-15 -> 70-75 GeV: 0.863 -> 0.919 without, 0.931 -> 0.968 with the ID SF.
  - ZEE leading eta_SC (0.5 bins): Central 0.956-1.013, no ele ID SF 0.818-0.895, no reco SF 0.915-0.977.
  - EMU N_b: Central 0.918 / 0.945 / 1.41 / 1.58 (1-4 b), no b-tag SF 0.961 / 0.866 / 1.34 / 1.41.
  - EMU leading-jet pT (20 GeV bins): raw 1.12 (20-40) -> 0.87-0.90 (100-200); corrected 0.92-0.95 (20-200); with top-pT weight 0.92 -> 0.98. Electron pT (25 GeV bins) 0.972 (25-50) -> 0.845 (150-175), with top pT 0.978 -> 0.885.
  - Z peak (zpeak.txt regenerated): DIMU shift +0.013 (was +0.016), MiniAOD -0.048 (was -0.045); ZEE -0.012 / -0.482.
- **Mismatches / findings:**
  - The AN text of 2026-11-24 said the muon eta dips at |eta| ~ 0.25 are "expected to be absorbed" by the ID SFs in signed-eta bins: they are not (same relative depth with and without the SFs); origin open.
  - `No<Factor>` plots carry the legend "Stat.+Syst." although their band is MC stat only (`plot.py` / `plotter.py` label); AN captions state the band correctly. Plot fix not done (outside the an-writer scope).
  - `Sections/Trigger.tex` `ssec:TriggerValidation` still says the Z->ee region uses official EGM "trigger, ID, and reconstruction SFs" as a proxy; since the LepIDSF production only the trigger SF is a proxy (the reco SF is the POG SF, used in EMU as well). Not changed (other section's content).
  - The jet-veto statement "88.7% of the jets ... 93.0% in simulation" still cites the 2026-11-24 print of `plotJetVetoMap.py`; data are unchanged, simulation weights changed with the ID SFs; not re-read.
- **Open:**
  - effect of the trigger SFs in DIMU / EMU (Table and plots; TODOs in place) (PLAN 2.4 step 4);
  - final user check of the ID SFs in the DiLepton regions (PLAN 2.3 step 6);
  - origin of the DIMU muon eta dips at |eta| ~ 0.25 (trigger or reconstruction) (PLAN 2.4);
  - EMU ttbar normalization and the electron-pT slope; whether top-pT reweighting enters (PLAN 2.2 / SystUnc);
  - pileup: data remain shifted to higher nPV after the weight (PLAN 2.2);
  - b-tag effect to repeat with the measured efficiencies (PLAN 2.5); N_b = 3, 4: data exceed the simulation by 41% and 58% (3% of the data).

## 2026-11-26 (DiLepton plot layout: Central with all corrections, one directory per removed correction)

- **Decided (user):** `DiLepton/plots/AN/2024/<channel>/Central` has every correction applied; `<channel>/No<Factor>` removes one (e.g. NoMuonIDSF, NoPileupReweight, NoBtagSF); the AN defines the control regions first and shows in each object section how its correction acts. `plot.py --all-lanes` (layout in `PLAN_Plotting.md`); cutflow, Z peak and jet-veto-map outputs regenerated from the LepIDSF production (AN and PW styles).
- **Effect of each correction on the total MC yield** (`<channel>/corrections.txt`; MC with / without, data/MC with all corrections DIMU 0.944, EMU 0.941, ZEE 0.983):
  - DIMU: muon ID SF 0.94 (without: data/MC 0.890), PU 0.99 (0.935), top pT (optional) 1.000.
  - EMU: electron ID SF 0.94 (0.885), muon ID SF 0.97 (0.913), b-tag SF 0.98 (0.919), PU 0.985 (0.928), electron reco SF 0.98 (0.926); top pT applied: data/MC 0.955 (MC x 0.986).
  - ZEE: electron ID SF 0.88 (0.869), electron reco SF 0.96 (0.946), PU 0.98 (0.967), proxy trigger SF 0.985 (0.969).
- Z peak (`zpeak.txt`): corrected pT, data - MC mean of m(ll) +0.013 GeV (DIMU), -0.012 GeV (ZEE); without the corrections -0.048 / -0.482 GeV.
## 2026-11-26 (lepton ID SFs in DiLepton: LepIDSF production)

- **Production done:** `DiLepton/Run{DiMu,EMu,ZEE}_RunSyst_LepIDSF/2024/` (DAGs status 0; 38 / 30 / 38 outputs), synced to the local `SKNanoOutput/DiLepton/`.
- **Plots:** `DiLepton/python/plot.py` now reads the LepIDSF production (layout revised the same day, see the entry below and `PLAN_Plotting.md`); band adds `MuonIDSF` (DIMU, EMU) and `ElectronIDSF` (EMU, ZEE) in `config/plotting/systematics_DiLepton.json` (lanes missing in a production are skipped).
- **Data/MC (total yield):** DIMU 0.890 -> 0.944, EMU 0.859 -> 0.941, ZEE 0.964 -> 0.983 (proxy ID SF -> measured). Remaining DIMU / EMU deficit before trigger SFs (none applied in DIMU / EMU yet; ZEE keeps the proxy trigger SF) and PU modelling (open).
- **Pending:** user review of the `_LepIDSF` plots (final check of the ID SFs, PLAN_LeptonID step 6); then the tnp_tamsa results move to /pnfs SKNanoOutput/TnP/2024/.
## 2026-11-25 (ID SFs in the fit)

- **Decided (user):** one nuisance per ID SF (muon, electron), total uncertainty varied coherently in all bins, no statistical/systematic split: these uncertainties are small compared to the other systematics. Already so in DiLepton (`MuonIDSF`, `ElectronIDSF` lanes); AN TODO removed.

## 2026-11-25 (ID SF maps regenerated)

- `LeptonID/python/plotSFMaps.py`: colour scale of the SF maps from 0.75 (was 0.8; the electron 10-20 GeV, 0 < eta_SC < 0.8 cell, SF 0.7878, was drawn blank), frame extended above the last pT bin so the caption does not cover the top row, no luminosity label on the simulation maps, readable log pT labels (`Common/Tools/plotter.py` Map2DCanvas: `yRange`, `zTitleOffset`, log-y labels). Copied to `docs/AN-26-267/Figures/LeptonID/2024/`; the blank-cell remarks removed from the AN captions. Note: `vs_pt_multi_eta` shows data efficiencies and SFs only (not the simulation efficiency); the AN caption says so.

## 2026-11-25 (AN: lepton ID SF figures)

- **Written** (an-writer) in `docs/AN-26-267/Sections/ObjectID.tex`, `ssec:LeptonIDSF`: `fig:MuonIDSF`, `fig:ElectronIDSF` (SF map + `vs_pt_multi_eta`), `fig:MuonIDEff`, `fig:ElectronIDEff` (data / sim efficiency maps), `fig:LeptonIDSFStatSyst` (stat / syst maps; no lepton-ID part in `Appendix/ObjectID.tex`), from `Figures/LeptonID/2024/NUM_HcToWATight_DEN_{TrackerMuons,RecoElectrons}_2024/` (copies of `LeptonID/plots/AN/2024/`); figure TODO removed, user-review TODO kept. Plot issues found (not regenerated): electron 10-20 GeV, 0 < eta_SC < 0.8 SF 0.7878 is below the 0.8 colour-scale minimum of `plotSFMaps.py` and drawn blank (stated in the captions); `vs_pt_multi_eta` top panel shows data efficiency only (no simulation); `sim.png` header "Simulation Work in progress" overlaps the lumi label; the muon map caption overlaps the top-row values.

## 2026-11-25 (AN: lepton ID SF subsection updated)

- **Written** (an-writer) in `docs/AN-26-267/Sections/ObjectID.tex`, `ssec:LeptonIDSF`: corrected pT and corrected pair mass (L4 revised; the 2026-11-24 text said uncorrected pT); muon (tnp_tamsa largest deviation per set) and electron (EGM rule (d)) uncertainty rules; `tab:LeptonTnP` updated (electron tag gap veto, gap bins skipped, fit 60-120 GeV with 60 bins, EGM altSig/altBkg models, LO DY as cross-check only; muon alt-signal swaps the whole simulation); fit-acceptance checks and refits (23 muon / 11 electron fit results still flagged, from `summary.txt`); POG-WP validation (from `compareOfficialSF.txt`); new `tab:LeptonIDSFSummary` (per pT row: SF range, median, median and max total uncertainty, computed from `LeptonID/data/2024/*_ID_HcToWA.json`); application (corrected pT, clamps, electron > 300 GeV rule) and the statement that the DiLepton validation shown predates the SFs. `ssec:ZeeValidation`: first sentence updated, TODO that the LepIDSF production replaces the proxy ID SF.
- **Numbers** (all from `LeptonID/data/2024/*.json`, 2026-11-25): muon SF 0.908-1.007 (median 0.968), median total unc. per pT row 0.0009-0.0067, max 0.017; electron SF 0.788-1.122 (median 0.950), median unc. 0.049 (10-20 GeV), 0.023 (20-35), 0.0052-0.024 above 35 GeV, max 0.052 (10-20 GeV) / 0.033 (200-300 GeV). POG-WP SF differences: muons median 0.0002 / 0.0003 (Medium / Tight), max 0.0068, no cell > 3 sigma; electrons median 0.0093 / 0.0050 (cut-based Tight / wp90noiso), |pull| median 0.48 / 0.43, 2 / 0 of 56 cells > 3 sigma.
- **Not done**: SF figures not copied into `docs/AN-26-267/Figures/` (outside the an-writer edit scope); the text points to `Fig. XXX` with a TODO naming `LeptonID/plots/AN/2024/.../{sf,data,sim}.png` and `eff1d/vs_pt_multi_eta.png`.
- **Mismatch**: AN text of 2026-11-24 (uncorrected-pT binning, "no lepton ID SF is applied", EGM fit details missing) vs the code and configs of 2026-11-25; corrected. LOG 2026-11-25 (first results) quotes 1 electron HcToWATight fit still flagged, `summary.txt` (14:34, after the set-1 rerun) 11; the AN uses 11.
- **Open**:
  - user review of the SF maps (PLAN 2.3 step 5); the AN numbers follow it;
  - electron SF uncertainty above 300 GeV: linear growth pT/300 up to 1 TeV, "to confirm (user)";
  - whether the SF uncertainty enters the fit as one nuisance per flavour or split into statistical and systematic parts (SystUnc);
  - DiLepton yields with the measured SFs (LepIDSF production running: 17 / 29 / 2 samples present in DIMU / EMU / ZEE on 2026-11-25) (PLAN 2.3 step 6);
  - figure copy into the AN repository (user or a figure step).

## 2026-11-25 (lepton ID SFs: application in DiLepton, PLAN_LeptonID step 6)

- **User:** partial approval of the ID SFs; the final check is done in the DiLepton regions. The tnp_tamsa results stay on /d0 until that check (copying to /pnfs is irreversible).
- **JSON:** `LeptonID/python/makeSFJson.py` -> `LeptonID/data/2024/{muon,electron}_ID_HcToWA.json` (corrections `HcToWATight_Muon_ID` (eta, pt, ValType), `HcToWATight_Electron_ID` (sceta, pt, ValType); ValType sf, sfup, sfdown (total), sfstat, sfsyst, effData, effMC; corrected pT; clamp flow); read back at every cell (max difference 2e-16). Electron gap cells sf = 1. Above 300 GeV: the 200-300 GeV electron SF with its total uncertainty scaled by pT / 300 up to 1 TeV, constant above (our reading of EGM's "growing linearly to 1 TeV"; **to confirm (user)**). Muons above 200 GeV use the 120-200 bin.
- **Analyzer** (`HcToWA_Analyzers`, previous version `hcto_prod/module_pre_idsf/`): JSONs in `data/2024/LeptonID/`, loaded by `HcToWABase::LoadIDScaleFactors` (MC; jobs read them from the run's source snapshot); `MuonIDSF(eta, pt, var)`, `ElectronIDSF(sceta, pt, var)`. DiLepton factors `kFMuID` (DIMU, EMU), `kFEleID` (EMU, ZEE), product over tight leptons, lanes `MuonIDSF_{Up,Down,NotImplemented}`, `ElectronIDSF_{...}`, weight histograms `weights/{muIDSF,eleIDSF}`. In ZEE our electron ID SF replaces the EGM proxy ID SF (`ElectronIDSFProxy` removed from `DiLeptonSystematics.yaml`; the proxy trigger SF stays until phase 2.4).
- Test (one DY->mumu file, condor): DIMU per-event muon SF mean 0.942 (rms 0.017); MuonIDSF_NotImplemented / Central = 1.061 = 1/0.942; up/down +-0.4%.
- **Production** `hcto_prod/submit_idsf.sh` (data + MC as on 2026-11-24, flags + `LepIDSF` as an output label: `DiLepton/Run{DiMu,EMu,ZEE}_RunSyst_LepIDSF/2024/` on /pnfs), launched 16:0x.

## 2026-11-25 (lepton ID SFs: EGM alternative fits and combination)

- **EGM framework** (`cms-egamma/egm_tnp_analysis`, master, last update 2024-05; `etc/config/settings_ele_Run3.py`, `libPython/fitUtils.py`, `libCpp/histFitter.C`, `libPython/efficiencyUtils.py`; whether EGM's 2024 measurement used exactly this branch is not stated in its slides):
  - fit 60-120 GeV, histograms 50-130 GeV; nominal = reco MC template (truth-matched) x Gaussian + RooCMSShape;
  - altSig = generator-level Z line shape (`etc/inputs/ZeeGenLevel.root`, one inclusive histogram) x `RooCBExGaussShapeTNP` (Gaussian core with widths sqrt(sigma^2+sos^2), CB-type tail on the low-mass side below 35 GeV, on the high-mass side above), + RooCMSShape; n, alpha, sigma, sigma_2 fixed from the MC altSig fit (MC: sos and background fixed to 0), mean and sos float in data;
  - altBkg = nominal signal + exponential; altSigBkg = altSig signal + exponential;
  - combination: central value = mean of the four data efficiencies (nominal, altSig, altBkg, altSigBkg); fit-model uncertainty = sqrt(sum of squared deviations from the mean / 3) / 2; total = that (+) altMC (MC-efficiency difference, set to 0 below the MC statistical error) (+) data and MC statistics; SF = mean / effMC. altMC and altTag are commented out in the Run 3 settings.
  - Our previous altsig (reco template x fixed-tail CB) was close to the nominal fit by construction, hence the small low-pT uncertainty.
- **Decided (user):** electron altSig = EGM's model, plus EGM's altSigBkg set; electron uncertainties combined with EGM's rule (altMC kept, user decision earlier). Muons keep tnp_tamsa's rule (nominal central value, each set's largest deviation in quadrature) and MUO's sets.
- Implementation: `etc/RooCBExGaussShapeTNP/` (EGM source, unchanged, ACLiC build); `fitUtils.py` commands `@<var><op><value>: <line>` (per-bin lines, lower bin edge), `SetValue`, `SetFloat`; electron config sets: s1 altsig (EGM), s2 altbkg, s3 altmc, s4 altsigbkg (EGM); previous config `hcto_prod/HcToWA_Electron_2024.py.pre_egmaltsig`. Difference to EGM: per-bin gen-level line shape from our gen-matched `pair_gen_mass` histograms instead of one inclusive histogram; sos range [0, 5] (EGM [0.5, 5]) so that sos = 0 is allowed in the MC fit. Test on three pT rows (10-20, 35-50, 100-200 GeV) of the POG working points: 96 fits, no NaN, all acceptable status; data |altSig - nominal| 0.028-0.030 at 10-20 GeV (previous altsig ~0.006), 0.0015-0.0025 at 35-50, 0.003-0.004 at 100-200; altSigBkg 0.016 / 0.004-0.005 / 0.010-0.013; altBkg <= 0.002.
- **Which combination reproduces EGM's published 2024 uncertainties** (electron.json `sfup - sf`; its systematic part is identical for +eta and -eta cells, its statistical part not): (a) master-branch rule (mean of 4, spread/2, + altMC + stat): 0.010-0.018 at 10-20 GeV vs EGM 0.038-0.082, too small; (b, c) full SF deviations including each member's own sim fit (+/- |eta| symmetrization): too small at low pT, too large above 35 GeV; **(d) data-efficiency deviations of altSig and altBkg / nominal MC efficiency, in quadrature with the statistical error, systematic symmetrized in |eta|: WP90 10-20 GeV 0.040-0.050 vs EGM 0.038-0.055, 35-50 GeV 0.0015-0.0046 vs 0.0017-0.0036; Tight 10-20 GeV 0.046-0.060 vs 0.042-0.082, 35-50 GeV 0.003-0.007 vs 0.002-0.008**; at 100-200 GeV (d) is about twice EGM's (EGM's statistical errors there are 0: different high-pT treatment); (e) = (d) + altSigBkg overshoots above 35 GeV.
- **Decided (user): electron SF uncertainty = rule (d), exactly as EGM** (supersedes the master-branch rule chosen earlier the same day): no altMC (set 3 kept in the results as a cross-check), no altSigBkg (set removed from the config). `LeptonID/python/combineElectronEGM.py` -> `SKNanoOutput/TnP/2024/<config>/sf_egm.root` (sf, sf_stat, sf_sys, data, sim, dAltSig, dAltBkg); `plotSFMaps.py` and `compareOfficialSF.py` use it for the electron configs. Production: set 1 (EGM altSig) rerun for HcToWATight, wp90noiso, cutBasedTight (`hcto_prod/tnp_prod/rerun_egm_altsig.sh`), then fit check and refits.
- **Result** (set 1 rerun 14:29; 1 refit accepted): remaining flags do not touch the inputs of rule (d) for HcToWATight: alternative-signal sim fits 0.017-0.029 above the gen-matched truth at 10-20 GeV (the EGM model describes low-pT MC less well, which is what makes its data deviation large; rule (d) does not use the alternative sim fits), alternative-signal data deviations > 0.03 (the systematic itself; wp90 bins 0,2,5,6, Tight bins 2,6), altMC sim fits at 200-300 GeV (not used), and for the POG reference cutBasedTight one altMC Hesse failure (bin 38) and a nominal data fit with an inflated yield error (bin 14). Total SF uncertainty (median over eta_SC) ours / EGM published: Tight 10-20 GeV 0.052 / 0.052, 20-35 0.027 / 0.041, 35-50 0.0045 / 0.0029, 50-70 0.014 / 0.013, 70-100 0.015 / 0.011, 100-200 0.007 / 0.004, 200-300 0.022 / 0.012; wp90noiso 0.045 / 0.053, 0.018 / 0.031, 0.0018 / 0.0020, 0.008 / 0.004, 0.011 / 0.009, 0.007 / 0.003, 0.020 / 0.010. SF ours vs EGM with total errors: median pull 0.48 / 0.43, beyond 3 sigma in 2 / 0 cells. HcToWATight: 0.049, 0.023, 0.005, 0.017, 0.012, 0.010, 0.024 for the same rows; no empty or NaN cell.
- **1D plots** (user request, style of V3 `LeptonIDTest/python/plot_efficiency.py` / `plotIDEff.py`): `LeptonID/python/plotEff1D.py` with `plotter.EffCanvas` (new): per config, efficiency vs pT in each eta bin and vs eta in each pT bin; top pad data and MC efficiencies (nominal fits, statistical errors), lower pad SF with total uncertainty (electrons: EGM rule); for MediumID, TightID, cut-based Tight and wp90noiso the MUO / EGM data, MC and SF overlaid as open markers. 126 plots in `LeptonID/plots/AN/2024/<config>/eff1d/`. Plus the V3 'multi_eta' plot (`MeasTrigEff/python/plotMuIDEff.py`), `eff1d/vs_pt_multi_eta.png` per config: data efficiency and SF vs pT for all eta bins, linear pT axis, colour by |eta| bin (filled eta > 0, open eta < 0); legend rows pair each eta < 0 bin (left column) with its mirror bin (right column).

## 2026-11-25 (lepton ID SFs: electron alternative-MC systematic)

- **Decided (user):** the MadGraph LO DYto2E 4J sample becomes an electron systematic (set 3, `altmc`: alternative MC efficiency and signal templates) in the HcToWATight, wp90noiso and cutBasedTight configs, as in the EGM measurement; it was a separate cross-check config before (that config is kept). No tag-selection variation: not recommended by the Statistics Committee, even though MUO uses one. Our muon configs follow MUO and include the tag-isolation variation (set 1: tag iso < 0.3 / < 0.1); **decided (user): kept as is.** Next (user): look at how EGM builds its alternative signal and background fits, since our electron uncertainty below 35 GeV stays 3-6 times smaller than EGM's after adding altMC.
- Implementation: `HcToWA_Electron_2024.py` systematic list (previous version `hcto_prod/HcToWA_Electron_2024.py.pre_altmc`); run `hcto_prod/tnp_prod/add_altmc.sh`: altsim histograms (hist set 2), set-3 fits, summary, fit check and refits; nominal and sets 1-2 unchanged. Fit check: 30 flagged, 15 refits accepted; still flagged 6 / 4 / 5 (HcToWATight / wp90noiso / cutBasedTight), mostly LO-DY sim fits vs their gen-matched truth at 200-300 GeV. Nominal SFs unchanged (one cell 0.003 from an accepted nominal refit).
- **Effect** (median over eta; previous results kept locally as `SKNanoOutput/TnP/2024/<config>.pre_altmc/`):

  | pT [GeV] | altMC shift, HcToWATight | total unc. HcToWATight before -> after | cutBasedTight after / EGM Tight | wp90noiso after / EGM |
  |---|---|---|---|---|
  | 10-20 | 0.010 | 0.009 -> 0.014 | 0.013 / 0.052 | 0.008 / 0.053 |
  | 20-35 | 0.004 | 0.008 -> 0.009 | 0.008 / 0.041 | 0.006 / 0.031 |
  | 35-50 | 0.001 | 0.001 -> 0.001 | 0.003 / 0.003 | 0.001 / 0.002 |
  | 50-100 | 0.002 | 0.002-0.004 -> 0.003-0.005 | 0.003-0.004 / 0.011-0.013 | 0.001-0.004 / 0.004-0.009 |
  | 100-200 | 0.004 | 0.004 -> 0.007 | 0.005 / 0.004 | 0.004 / 0.003 |
  | 200-300 | 0.012 | 0.016 -> 0.025 | 0.016 / 0.012 | 0.014 / 0.010 |

  Above 35 GeV our uncertainties now match or exceed EGM's; below 35 GeV they stay 3-6 times smaller (EGM's low-pT uncertainty must come mostly from its alternative signal/background models). SF vs EGM with total errors: median pull 0.77 / 0.76, beyond 3 sigma in 4 / 3 cells (100-200 GeV barrel).

## 2026-11-25 (lepton ID SFs: first results, validation against the official 2024 SFs)

- **Fit status after refits:** the flagged fits were refitted with likelihood offsetting and a refit kept only if it passes every check (`hcto_prod/tnp_prod/refit_flagged.py`; originals kept in `fits_*.d.orig/`): 245 of 312 accepted, shifts median 1e-6 - 1e-3; the accepted refits that moved most repaired fits that disagreed with the gen-matched truth (electron sim bin 24 s1m0 0.849 -> 0.774, bin 28 s0m0 0.903 -> 0.885, truth 0.885). One accepted refit was a fit stuck at its start values (muon TightID data bin 112 s3m0: nSigP = nBkgP = 27000, eff 0.946 vs 0.972 for every other member); new check rule (nSig = nBkg within 0.1%), refit reverted. Still flagged (production fit kept): muon 23 / 20 / 14 of 2106 per config (HcToWATight / MediumID / TightID; mostly data signal-yield errors > 3 sqrt(S+B) and sim errors > 3 x truth error), electron 1 / 5 / 2 / 3 (HcToWATight / altMC / cutBasedTight / wp90noiso).
- **SF maps:** `LeptonID/python/plotSFMaps.py` -> `LeptonID/plots/AN/2024/<config>/{sf,sf_stat,sf_sys,data,sim}.png`, `summary.txt`. Results copied to `SKNanoOutput/TnP/2024/<config>/` (efficiency.root, config.txt, checkFitStatus.txt).
  - HcToWA tight muons: SF 0.91-1.01 (median ~0.97). HcToWA tight electrons: SF 0.79-1.12, median 0.950; the 10-20 GeV row departs most (endcaps 1.08-1.12, central barrel 0.79-0.80).
- **Validation against the official 2024 SFs** (`LeptonID/python/compareOfficialSF.py`, output `LeptonID/plots/AN/2024/compareOfficialSF.txt`; official files from cvmfs cms-griddata Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15 latest, copies in `SKNanoOutput/TnP/2024/official/`):
  - Muons: MediumID and TightID / TrackerMuons agree with MUO `muon_Z.json`: |SF ours - MUO| median 0.0002 / 0.0003, max 0.005 / 0.007 (120-200 GeV); no cell beyond 3 sigma of our uncertainty.
  - Electrons: cut-based tight and MVA noIso WP90 agree with EGM `electron.json`: median |SF ours - EGM| 0.009 / 0.005, |pull| median 0.8; data and MC efficiencies agree cell by cell. EGM also has SF 1.11-1.16 (Tight) in the 10-20 GeV endcap cells, so the large low-pT endcap SFs are not a fit artifact.
  - **Open (user):** below 20 GeV our electron SF uncertainty (~0.01) is 4-8 times smaller than EGM's (0.04-0.08); EGM includes alternative-MC and tag-selection systematics, our electron systematics are the alternative signal (small with the fixed CB tail) and background only. Four cells beyond 3 sigma, all at 35-50 GeV where both uncertainties are 0.002-0.004.
- `correctionlib` 2.9.0 added to NanoV15 (local and KNU).
- **Data and MC efficiencies vs the central POG results** (user request; `LeptonID/python/compareOfficialSF.py`, output `LeptonID/plots/AN/2024/compareOfficialSF.txt`, ours/POG maps in `LeptonID/plots/AN/2024/validation/`):
  - Muons: MUO's correction file has SFs only; the data and MC efficiencies come from MUO's per-bin fit files (`.../sblancof/MuonPOG/Run2024_ReRecoCDE_PromptFGHI/fits/<WP>/`, linked from the slides; copies in `SKNanoOutput/TnP/2024/official/muo_fits/`): data = fitted efficiency on the fit canvas, MC = count of the stored MC pass/fail histograms in 70-110 GeV; their ratio reproduces `muon_Z.json` to 4e-5 (median). MediumID / TightID: data |ours - MUO| median 0.0002 / 0.0003 (max 0.006), MC 0.0001 / 0.0002 (max 0.002 / 0.008), SF 0.0002 / 0.0003 with no cell beyond 3 sigma; the few data/MC cells beyond 3 sigma (stat. only, errors ~1e-4) are mostly at 15-20 GeV with differences <= 0.003. Also, the MUO `.pre-SF` JSON on the same site holds SFs only.
  - Electrons (EGM `effData`, `effMC` with `err_statData`, `err_statMC`): SF agrees (median pull 0.8), the efficiencies separately do not fully. (1) MC lower than EGM: 10-20 GeV -0.009 (Tight) / -0.018 (wp90noiso), 20-35 GeV +0.005 / -0.004, above 35 GeV -0.002 to -0.004 (medians over eta). Not the fit (our MC fit = our gen-matched count to 0.001), not the binning variable (gen-matched count binned in uncorrected pT: same), not a wider count window (54-126 GeV makes it larger at 10-20 GeV: -0.024 / -0.029); left: EGM's MC definition (window, gen matching, weights), sample or selection details. (2) Above 100 GeV data and MC both lower by 0.01-0.03; EGM's statistical errors there are exactly 0 (not a per-bin fit), so the comparison there is weak; our SF is 0.015-0.02 lower at 100-200 GeV in the barrel. (3) Data at 10-20 GeV: central barrel 0.02-0.03 below EGM, endcaps 0.02-0.05 above (background-dominated fits).

## 2026-11-25 (lepton ID SFs: fit acceptance and electron alternative signal)

- **Production fits** (all 7 configs, NanoV15, legacy RooFit backend) finished 11:23. At full statistics most fits end with Minuit status 3 (EDM above tolerance) or covQual 2 (covariance forced positive-definite): e.g. muon HcToWATight, 73 of 117 data and 142 of 234 sim nominal fits. Test refits with likelihood offsetting (`TNP_ROOFIT_OFFSET=initial`) on 25+25 muon nominal bins reached status 0 & covQual 3 in 12 (data) / 16 (sim) bins with efficiencies changed by a median 4e-5 (max 0.0017, 0.7 sigma): those fits were at the right minimum. Offsetting also produced a degenerate minimum (muon sim bin 7: nSigP = nBkgP, eff 0.632 vs 0.774, count 0.771), so it is not used in production.
- **Decided (user): fit acceptance = pathologies only** (`checkFitStatus.py --policy pathologies`, default): refit a NaN efficiency, a status other than 0/1/3 (e.g. 302, Hesse failed) or covQual <= 0, a yield at its upper limit, a data signal-yield error > 3 x sqrt(nSig + nBkg), a sim efficiency more than 0.01 from the gen-matched count or with an error > 3 x its error, a data systematic member more than 0.03 from nominal. Status 1/3 and covQual 1-2 are warnings. The sim fits of all muon configs agree with the gen-matched truth to 0.01 in every bin. Refit lists after the first pass: muon 71-109 of 2106 fit results per config, electron 13-46.
- **Electron alternative signal (s1m0: MC template x Crystal Ball):** unstable at full statistics: the tail parameter n runs to its limits, NaN efficiencies in 10-17 bins per config (tnp_tamsa writes them into efficiency.root without warning), and converged fits differ by 0.05-0.15 between minimizer settings. Restricting alpha to >= 1.2 (most tnp_tamsa configs) does not cure it. Reason: the CB smears the gen-matched MC template, so on MC itself the tail is undetermined. **Decided (user):** fix the CB tail and let only mean and width float; since a fit to MC cannot determine the tail for this model, it is fixed at the config's starting values (alpha 2.0, n 3.0). Test on every flagged s1m0 bin of HcToWATight and wp90noiso plus clean bins (copies of the production histograms): NaN 12/17/13/10 -> 0 (wp90 data/sim, HcToWATight data/sim), acceptable status 22/17/14/19 -> 33/34/29/29, |s1m0 - s0m0| in data median 1e-4, max 0.0035 (production up to 0.14-0.23); one sim fit off (HcToWATight bin 24, 0.849 vs nominal 0.774), left to the refit step. Applied to `HcToWA_Electron_2024.py` (`fit_altsig`; previous version in `hcto_prod/HcToWA_Electron_2024.py.pre_cbfix`); set 1 rerun for HcToWATight, wp90noiso, cutBasedTight (the altMC config has no altsig set).

## 2026-11-25 (lepton ID SFs: corrected pT, L4 revised)

- **Decided (user), L4 revised:** the ID efficiencies are measured on top of the lepton scale and smearing corrections: tnp_tamsa bins and cuts on `probe_pt_cor` / `tag_pt_cor` and fits `pair_mass_cor` (configs `HcToWA_{Muon,Electron}_2024.py`; pre-change copies in `hcto_prod/*.pre_cor`). Supersedes the 2026-11-24 L4 (uncorrected NanoAOD pT). The SFs are therefore applied in the corrected pT.
- **Size of the corrections in the TnP ntuples** (test files, mean corrected/raw pT; mass shift of the pair): EGamma data +1.2%, +0.88 GeV; DY->ee MC 1.000 with 2.2% RMS smearing, -0.01 GeV; Muon data +0.13%, +0.13 GeV; DY->mumu MC 0.76% RMS, +0.06 GeV.
- **Producer preselection** changed so the ntuples serve both choices: tag and probe pT thresholds pass if either the raw or the corrected pT passes, and the 50-130 GeV pair window passes on either mass. Before, the raw-pT preselection removed electron probes just below 10 GeV raw that are above 10 GeV corrected (test: 13 of 29763 DY->ee pairs, 6 of 1907 EGamma0 H pairs now recovered; none for muons in the test files).
- The first TnP production (submitted 00:23, uncorrected-pT preselection) was removed by cluster id after a few minutes, with no output; resubmitted with the patched producers.

## 2026-11-24 (lepton ID SFs: TnP open questions)

- **Decided (user):** electron gap bins (1.4442 < |eta_SC| < 1.566) are skipped (no fits; our ID rejects the gap).
- **Decided (user):** the electron tag is vetoed in the ECAL gap, as in B2G-25-013 (overrides the EGM default, which allows it).
- **Decided (user):** DYto2E_4J_MLL50toInf (madgraphMLM, LO) is our LO DY sample for electrons; it is produced with the TnP ntuples and used as an alternative-MC cross-check, reported separately (not in the nominal EGM systematic set unless decided later).
- **Decided (user):** the muon alternative signal template follows tnp_tamsa (the whole simulation is swapped, template and MC efficiency, as B2G-25-013's altmc), not MUO's template-only variation.
- Implemented (TnP agent): gap bins removed via a tnpConfig subclass (56 of 70 electron bins fitted; gap cells are 0 +- 0 in efficiency.root and become 1 +- 0 in the correctionlib JSON); the tag gap veto removes 2.4-2.6% of the pairs; `NUM_HcToWATight_DEN_RecoElectrons_2024_altMC` holds the LO cross-check; DYto2E_4J is in the production by default (~864 jobs).

## 2026-11-24 (lepton ID SFs: TnP producers and chain built, phase 2.3 steps 1-2)

Built and validated; the production is not launched (it waits for Skim_TriLep). Details of the code in `LOG_Computing.md`.

- **Producers** in `HcToWA_Analyzers` (both derive from `HcToWABase`; one entry per tag-probe pair, opposite charge, 50 < m < 130 GeV; pT = uncorrected NanoAOD pT (L4), `*_cor` = corrected):
  - `MuonTnPProducer` (port of the old one, branch names kept). Tag preselection: POG tight, pT > 26, |eta| < 2.4, |dxy| < 0.2, |dz| < 0.5, pfRelIso04 < 0.3 (nominal 0.2 is cut in the config), `HLT_IsoMu24` fired and matched (dR < 0.1) to a muon TrigObj with bit 3 and pT > 24. Probe: tracker muon, pT > 10, |eta| < 2.4, same IP cuts.
  - `ElectronTnPProducer` (new). Tag: cut-based tight, pT > 35, |eta_SC| < 2.5, matched (dR < 0.1) to an e/gamma TrigObj of a fired path of the OR Ele32_WPTight (id 11 bit 1, pT > 32), Ele115_CaloIdVT_GsfTrkIdT (id 11 bit 12, pT > 115), Photon200 (id 11 bit 14 or id 22 bit 7, pT > 200). Probe: pT > 10, |eta_SC| < 2.5, dR(tag, probe) > 0.1. No gap veto on the tag in the producer; the veto is applied in the config expr (superseded: tag vetoed in the gap, user decision in the entry above).
  - Numerators: `probe_isHcToWATight` from `HcToWABase::EvaluateMuonIDs` / `EvaluateElectronIDs`, i.e. the analysis ID itself (electrons incl. the trigger emulation on the v15 custom branches); every ID input is stored too. POG flags for the validation: muons Medium, Tight; electrons MVA (no)iso WP80/WP90, cut-based.
  - **TrigObj bits**: NanoAOD v15 = CMSSW_15_0_X `PhysicsTools/NanoAOD/python/triggerObjects_cff.py` (the field descriptions are not in the RNTuples). Muons: 0 TrkIsoVVL, 1 Iso, 3 "1mu" (`hltL3crIsoL1*SingleMu*IsoFiltered*`, IsoMu24), 4 "2mu" (`hltDiMuon*Filtered*`), 5 "1mu-1e". Electrons: 1 `hltEle*WPTight*TrackIsoFilter*`, 6 "1e-1mu" (`hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*`), 12 CaloIdVT_GsfTrkIdT, 14 Photon175/200; photons (id 22) 7 `hltEG200HEFilter`. On one Muon0 file, 99.9% of the HLT_IsoMu24 events with a tag-like muon have a bit-3 match (22776 / 22797).
  - **Trigger legs for phase 2.4** (stored per probe, with the closest TrigObj's bits and pT): muons Mu17 / Mu8 (bit 4, pT > 17 / 8, as in the old producer), Mu23 / Mu8 e-mu legs (bit 5), IsoMu24; electrons Ele23 / Ele12 e-mu legs (bit 6), Ele32. The e-mu electron legs are present for only 0.2% of the Z->ee probes (the e-mu paths stop before their electron filters without a muon), so they cannot be measured in this sample.
  - **`probe_isDuplicated`**: MUO's 2024 tag cut "!probe_isDuplicated" comes from their NanoAOD TnP (`rbhattacharya04/Muon_POG_Nano_TNP`, `getDuplicatedProbes`): a probe that appears in more than one tag-probe pair. Implemented as "paired with more than one nominal tag (iso < 0.2)", with `probe_nTagsIso0p{1,2,3}` for the tag-iso variations. It is not "a probe sharing a track with another muon" (not derivable from NanoAOD). Rare: 2 of 452k DY pairs, 0 of 25k data pairs. `pair_probeMultiplicity` = number of probes of the tag in the mass window (old producer: all opposite-sign muons with m > 50).
  - **MC**: gen matching to prompt status-1 leptons of the same flavour (dR < 0.2, smallest |pT_reco/pT_gen - 1|, each gen lepton once, leading first), `pair_gen_mass` from the two matched gen leptons; `genWeight`, `PUweight` (+up/down), `weight = genWeight x PUweight x sumSign/sumW` (L3, normalised so that tnp_tamsa's fit ranges and the 1e5 weight clip stay sensible).
- **Validation** (one file and ten files per sample, Muon0 / EGamma0 Run2024H, DYto2Mu 4J, DYto2E 2J; `/d0/scratch/choij/tnp_test/check/`):

  | | Muon0 H | DYto2Mu 4J | EGamma0 H | DYto2E 2J |
  |---|---|---|---|---|
  | events (1 file) | 68,363 | 32,405 | 62,763 | 48,502 |
  | HLT / >= 1 tag / >= 1 pair | 30,050 / 9,290 / 1,753 | 20,140 / 14,913 / 13,508 | 17,616 / 1,681 / 725 | 21,527 / 15,121 / 13,285 |
  | pairs | 2,775 | 22,646 | 933 | 17,796 |
  | m(ll) mode (uncorr. pT) | 91.75 | 91.25 | 89.75 | 90.25 |
  | gen-matched pairs | | 99.8% | | 97.6% |

  - Every stored column is filled: no -999 or NaN (gen columns checked where matched).
  - The stored tight-ID boolean equals the ID re-derived from the stored inputs in every pair (muons 2413 / 20984, electrons 548 / 13023, data / DY).
  - Passing fractions, nominal tag selection, counting in the fit window (data incl. background): muons (70-110 GeV) our tight 0.886 data / 0.931 DY, POG Medium 0.982 / 0.993, POG Tight 0.970 / 0.981; electrons (60-120 GeV) our tight 0.604 / 0.738, MVA noIso WP90 0.751 / 0.888, cut-based tight 0.641 / 0.736, trigger emulation 0.787 / 0.847.
- **tnp_tamsa chain** on these ntuples (4 coarse bins, for the chain only): muons hist+fit+sum on condor with three systematic sets, 16 jobs, 7.5 min; data fits converge, 5 of 20 MC fits have a non-zero status (high-statistics pass histograms; the production needs the refit step of the plan). SF 0.971-0.986 for our tight ID (Run2024H, 11 files). Electrons: hist and two fits without condor, all converged; data/MC 0.679 / 0.752 (20-50 GeV, eta_SC > 0).
- Configs: `tnp_tamsa/config/HcToWA_Muon_2024.py` (`NUM_HcToWATight_DEN_TrackerMuons_2024`, POG `NUM_{Medium,Tight}ID_DEN_TrackerMuons_2024`), `HcToWA_Electron_2024.py` (`NUM_HcToWATight_DEN_RecoElectrons_2024`, POG `NUM_wp90noiso_...`, `NUM_cutBasedTight_...`, optional `..._altMC` with DYto2E 4J). Systematic sets as in `PLAN_LeptonID.md` 2b; the muon tag-iso variants also swap `!probe_isDuplicated` for `probe_nTagsIso0p{3,1} < 2`; mass bins via the histogram range 65-115 GeV (100 / 200 / 50 bins = 80 / 160 / 40 in 70-110).
- **Open:**
  - the muon "alternative signal template" in tnp_tamsa swaps the whole simulation (template and MC efficiency), as B2G-25-013's "altmc"; MUO may change the data template only;
  - the electron eta_SC gap bins have no passing probes for our ID (the trigger emulation rejects 1.444 < |eta_SC| < 1.566), so their fits fail; harmless for the analysis (no gap electrons) but they must be skipped or set by hand; **resolved:** skipped (entry above);
  - electron tag in the gap: **resolved:** vetoed (entry above).

## 2026-11-24 (AN ObjectID section written)

- **Written** (an-writer): `docs/AN-26-267/Sections/ObjectID.tex` (correction-file table; electron and muon IDs with tables; trk-iso caveat; lepton ID SF method with the tag-and-probe setup table and `XXX`/`%% TODO` result placeholders; jets incl. JEC/JER, jet ID, veto map with efficiency table and eta-phi maps; UParT b tagging; PUPPI MET and noise filters; event weights (PU, top pT lane); DiLepton validation: regions, proxy-SF statement, yields with per-weight ratios, Z-peak table and figure, PU and jet raw/corrected discussion). `Appendix/ObjectID.tex`: new section `appendix:DiLeptonValidation` (7 figures); old skeleton subsections kept with TODOs. `Sections/Trigger.tex`: the Z->ee TODO replaced by a cross-reference to `ssec:DiLeptonValidation`. Three bib entries added (`JetID13p6TeV`, `MUO2024MediumPtSF`, `EGM2024EleIDSF`).
- **Figures**: 38 PNGs copied from `DiLepton/plots/AN/2024/` to `docs/AN-26-267/Figures/DiLepton/2024/<channel>/<lane>/` (same relative paths). Full build: 47 pages, no undefined references.
- **Sources**: KNU `HcToWA_Analyzers/src/{HcToWABase,DiLepton}.cc`, framework `AnalyzerCoreJets.cc` (JEC, JER hybrid, veto map, MET propagation), `AnalyzerCoreObjects.cc`, `AnalyzerCore.h` (noise filters), `2024/Correction/era_config.yml`, BTV `btagging.json.gz` (`UParTAK4_wp_values` M = 0.1272, checked), DiLepton `cutflow.md`, `*/yields.txt`, `zpeak.txt`, `PLAN_LeptonID.md`, `docs/CMS/`.
- **Numbers derived here** (from `cutflow.md`, rows 1 and 2): event fraction kept by the jet veto map: Muon 0.930, MuonEG 0.896, EGamma 0.924, all MC 0.960. The earlier entry's "removes 7-9% of data events" is 7.0% / 10.4% / 7.6% in the full production (MuonEG is above 9%).
- **Mismatches found**:
  - AN-25-154 `tab:ElectronID` gives the Run 3 (and Run 2) loose-electron SIP3D < 8; the old code `Electron.cc` `Pass_HcToWALooseRun3` uses < 6 (Run 2: < 8), and the 2024 code uses < 6. The AN now quotes 6.
  - AN-25-154 places the electron barrel/endcap boundary at 1.479; the code (old and new) uses |eta_SC| = 1.444 / 1.566 (gap) and 0.8 for the MVA-score regions.
  - MET: `PropagateJetSystToMET` sums (smeared - NanoAOD) pT over **all** jets, with no pT > 15 GeV, EM-fraction or muon-subtraction requirement, unlike the standard Type-I definition. Written as is in the AN with a TODO.
  - `PLAN_DiLepton.md` section 2 still names the module `ChargedHiggs_Analyzers`; the module is `HcToWA_Analyzers` (D6).
- **Not carried over** (not verifiable for NanoAODv15): the AN-25-154 mini-isolation effective-area tables; the AN says the NanoAOD `miniPFRelIso_all` is used.
- **Open**:
  - Lepton ID SF results (figures, uncertainty ranges, POG-WP validation) and the electron fit range/alternative models (PLAN 2.3).
  - PU: data ~3 vertices above the reweighted simulation (PLAN 2.2).
  - Top pT reweighting: correction, uncertainty or neither (PLAN 2.2 / SystUnc).
  - PUPPI MET jet term definition (PLAN 2.6); PUPPI tune / jet requirements with the PUPPI fix (N5, PLAN 2.6).
  - b-tag efficiencies for our selection and the UParT WP study (PLAN 2.5).
  - Electron trigger-emulation effective areas for the 2024 HLT menu (PLAN 2.4).
  - Pin the correction snapshots (LOG_Computing).
  - `appendix:DiLeptonControlRegion` (in `Appendix/Trigger.tex`, empty) and the new `appendix:DiLeptonValidation` overlap; merge when the Trigger section is written.

## 2026-11-24 (electron ID SFs above 100 GeV)

- **Decided (user), L8:** electron pT bins up to 300 GeV ([..., 70, 100, 200, 300]) from the inclusive DYto2E 2Jets MLL-50 sample; above 300 GeV the 200-300 SF with an uncertainty growing linearly to 1 TeV, as EGM proposes for 2024.
- Basis (DiLepton outputs, 2024): Z->ee region (two tight electrons, Ele30, |m-91| < 30) has 608k / 40k / 9k leading electrons in 100-200 / 200-300 / >300 GeV, with the DY sample at about half in effective events; the e-mu region has 11.3% / 0.86% / 0.14% of its electrons in these bins.
- B2G-25-013 Run 3 evaluated the electron SF at min(pT, 99 GeV), i.e. it never used bins above 100 GeV (the 2022 high-pT bins were empty or NaN).
- All phase 2.3 decisions (L1-L8) are now settled.

## 2026-11-24 (lepton ID SFs: weights and pT variable)

- **Decided (user), L3:** the tag-and-probe MC is weighted with genWeight x PU weight for both leptons.
- **Decided (user), L4 (superseded 2026-11-25: corrected pT):** the ID SFs are binned in the uncorrected NanoAOD pT, both when measured and when applied (muons `MiniAODPt()`, electrons the NanoAOD pT before the EGM scale/smearing).
- Remaining open: L8 (electron bins above 100 GeV).

## 2026-11-24 (electron ID SFs: EGM 2024 setup)

- **Decided (user):** the electron tight-ID measurement follows the EGM 2024 electron ID SFs (M. A. Shahzad et al., 4 July 2025; `docs/CMS/EGM/`): tag = OR of Ele32 WPTight / Ele115 / Photon200 with cut-based tight ID, pT > 35 GeV; probe pT > 10 GeV, |eta| < 2.5, dR > 0.1; eta_SC 10 bins x pT [10, 20, 35, 50, 70, 100, ...]; MC DYto2E 2Jets MLL-50 amc@NLO; systematics alternative signal and background fits.
- All three tag triggers are in the 2024 files (RNTuplizer `branch_selection.csv`, `HLT_Path.json`). EGM's pT(ll)-binned high-pT DY samples are not converted at KNU: open L8 in `PLAN_LeptonID.md`.
- Both POG measurements use NanoAOD v14 as input, like our NanoAOD-based ntuples.

## 2026-11-24 (lepton ID SFs: follow the POG 2024 central setups)

- **Decided (user):** the tight-ID measurements follow the POG 2024 central setups. Muons: MUO medium-pT SFs with the 2024 dataset (S. Blanco Fernandez, M. Caserta, 19 May 2025; `docs/CMS/MUO/`), i.e. signed-eta binning (13 x 9 bins), MadGraph LO nominal template with amc@NLO as the alternative signal, 70-110 GeV with 80 bins, systematics tag iso 0.1/0.3, mass bins 40/160, range 65-105/75-115, exponential background; tag adds !probe_isDuplicated. Electrons: EGM 2024 setup, slides pending (`docs/CMS/EGM/`).
- The MUO 2024 eta-phi RECO maps show localized inefficiencies in 2024 D-F (DT theta superlayer off, DT chamber off, chimneys); relevant if our muon SFs show eta structure.

## 2026-11-24 (lepton ID SFs: how B2G-25-013 did it, and the 2024 approach)

- **B2G-25-013** measured only the tight-ID SFs ("TopHNT", one step: ID + iso + IP), with the private RooFit framework tnp_tamsa (`choij1589/tnp_tamsa`; copy on KNU `/d0/scratch/choij/tnp_tamsa`). Configs `TopHNT_Muon_Run3_v0.py` (ntuples from SKNano `MuonTnPProducer`, NanoAOD v12/13) and `TopHNT_Electron_Run3_v1.py` (EGM TnPTreeProducer ntuples, MiniAOD). Details in `PLAN_LeptonID.md` section 1.
- The deployed Run 3 electron SFs carried 5 systematic sets (incl. tag pT > 37 and fit window +-3 GeV); tnp_tamsa commit `ba69b07` later reduced them to 3. The muon fit details in AN-25-154 (`ObjectID.tex:207-209`: 80 mass bins, +-7 GeV window) differ from the Run 3 config (100 bins, 70-110 GeV).
- **Decided (user): ntuples from our 2024 NanoAODv15 RNTuples with SKNano 2.0 producers** (port of the old `MuonTnPProducer.cc`, new `ElectronTnPProducer`), so the numerator is exactly the analysis ID (incl. the NanoAOD `dr03TkSumPt` behaviour below 35 GeV). SKNano 2.0 writes RNTuples only, so a conversion to TTree sits before tnp_tamsa.
- SKNano 2.0 has no tag-and-probe analyzer; the 2024 era config can read local correctionlib files (e.g. `MUO/muon_trig.json`), so our SF JSONs go into the data directory and are read by `HcToWABase`.

## 2026-11-24 (DiLepton plots: first look)

Plots in `DiLepton/plots/AN/2024/` (and `DiLepton/plots/PW/2024/`), made with `DiLepton/python/{plot,cutflow,plotZPeak,plotJetVetoMap}.py`.

- **Data/MC yields** (all weights; cutflow with normalization only in brackets): DIMU 0.890 (0.881), EMU 0.859 (0.812), ZEE 0.964 (0.810).
  - ZEE has the proxy EGM SFs: without the ID SF 0.869, without the trigger SF 0.950, without RECO 0.928, without PU 0.948. With the official SFs the electron channel closes to 4%.
  - DIMU: the deficit appears at the lepton-multiplicity step (0.883) and is flat in m(mumu), muon pT and eta, as expected from the missing muon ID/iso and trigger SFs (phases 2.3, 2.4).
  - EMU: the ratio falls with the jet requirements (0.885 at the lepton kinematics, 0.842 with >= 2 jets, 0.812 with >= 1 b jet), i.e. the ttbar prediction is high; flat in N_jets. b-tag weight 0.838 -> 0.859, top pT reweighting 0.859 -> 0.871.
- **Z peak** (81-101 GeV, normalized; mean data - MC): muons corrected +0.016 GeV (MiniAOD -0.045), RMS 3.178 / 3.180; electrons corrected -0.014 GeV (MiniAOD -0.484, RMS 3.608 / 3.418 -> 3.591 / 3.588). The muon and electron scale/smearing corrections close the peak position and width.
- **Pileup:** the PU weight moves N_PV^good towards data but not enough (data still ~3 vertices higher); it barely changes the normalization (DIMU 0.881 -> 0.890). **Open:** check the 2024 PU recommendation (min-bias cross section / profile) before the AN.
- **Jet veto map:** keeps 88.7% of data jets and 93.0% of simulated jets (veto-map jet selection, DIMU production); the event veto removes 7-9% of data events.
- Muon eta shows the usual data dips at |eta| ~ 0.25 (DT wheel boundaries), to be absorbed by the muon ID SFs.

## 2026-11-24 (DiLepton analyzer: implementation and first results)

Module `HcToWA_Analyzers` (knu1, `/d0/scratch/choij/SKNanoAnalyzer`, branch `HcToWA_Run3`, uncommitted): `HcToWABase` + `DiLepton`, channels DIMU, EMU, ZEE.

- **IDs** are our own (built-in HcToWA IDs unused). Electron trigger emulation reads the v15 custom branches: deltaEtaInSC -> `Electron_DeltaEtaInSC`, deltaPhiInSeed -> `Electron_DeltaPhiInSeed`, ecal/hcalPFClusterIso -> `Electron_{ecal,hcal}PFClusIso`, scEta -> `Electron_superclusterEta`. Relative cuts use the MiniAOD pT; old effective areas kept (AN-25-154: "maintained up to Run3 2023"). `ElectronView::deltaEtaInSC()` returns NanoAOD `Electron_deltaEtaSC`, a different quantity, so it is not used.
- **ID check** (TTLL `rntpl_000`, 86,420 events): analyzer counts equal a raw-branch scan exactly; no -999 values. Muons (pT > 10): loose 67.2%, tight 61.4%. Electrons: trigger emulation 56.7%, loose 49.3%, tight 43.7%.
- **b tagging:** UParT Medium = 0.1272; method 1a with `UParTAK4_mujets` (b, c) and `UParTAK4_light`, correlated/uncorrelated variations. |eta| clamped to 2.4999 (the maps end at 2.5 with flow=error). Efficiencies from the era file `2024/BTV/btaggingEff.json`, made for another analysis's selection: **approximate until phase 2.5**.
- **Top pT:** the old analytic function (old `MyCorrection.cc:1366-1394`); SKNano 2.0 has only a 13 TeV ONNX model. Central without it; lane `TopPtReweight_Applied` for TT powheg.
- **Z->ee proxy SFs** (ZEE only): EGM ID `wp90noiso`; trigger from `electronHlt` `HLT_SF_Ele30_MVAiso90ID` (2024 HLT SFs exist only for ID+iso probes), event SF from the data/MC efficiencies of both electrons; standard RECO SF.
- **Z peaks** (subset, mean in 60-120 GeV): mumu data 90.08 / DY MC 89.95; ee data 90.32 corrected (89.64 with MiniAOD pT) / DY MC 90.35. The EGM scale moves the data ee peak by +0.7 GeV onto the MC.
- **Jet veto map** removes 7-9% of data and 13% of TTLL events (subset). Full production (cutflow "noise filters" -> "jet veto map"): 7.0% (Muon), 10.4% (MuonEG), 7.6% (EGamma), 4.0% (all MC).
- Data/MC after the full selection: see the next entry (the 0.81 first quoted for ZEE was the cutflow, which has no PU weight or SFs; with all weights ZEE is 0.964). Data completeness: RNTuplizer QC shows every data file converted and validated (events and lumis match), with lumi sums of 107.4-107.6 /fb against the 109.82 /fb used (about 2%).

## 2026-11-24 (electron track isolation below 35 GeV)

- **Finding:** in the 2024 NanoAODv15 files, `Electron_dr03TkSumPt` and `Electron_dr03TkSumPtHEEP` are still **not filled below pT = 35 GeV**.
  - Measured on 100k events of `TTto2L2Nu` 2024 (`rntpl_000`), electrons with pT > 10 GeV and |eta| < 2.5: both branches are exactly 0 for every electron with pT < 35 GeV (45.8k electrons). Above 35 GeV, 55-63% are 0 and the mean is 5-8 GeV.
  - The PF charged isolation (`pfRelIso03_chg * pt`) is filled at all pT (22-41% zero, mean 6-13 GeV), so the zeros below 35 GeV are not physical.
  - The field descriptions are not stored in the RNTuples, so this was checked from the values only.
- **Consequence:** the trigger-emulation cut `dr03TkSumPt < 0.2 * pT` (old `Electron.cc:134,143`) always passes below 35 GeV, i.e. it is applied only to electrons with pT >= 35 GeV.
- **Decided (user):** keep the cut as is, i.e. effectively applied only for pT >= 35 GeV (as in B2G-25-013, which read the same NanoAOD branch). No PF-based substitute and no new branch.

## 2026-11-24 (Z->ee check)

- **Decided (user):** test the electron energy scale and smearing with a Z->ee region, not a full dielectron control region (that would need dielectron trigger SFs).
  - Select with the single-electron trigger `HLT_Ele30_WPTight_Gsf` (EGamma0/1 data): two opposite-sign electrons.
  - Compare m(ee) and electron pT/eta, uncorrected vs corrected, as normalized shapes.
  - Normalization uses the **official (central) EGM scale factors as a proxy**: single-electron trigger (`electronHlt.json`), ID (the EGM working point closest to our tight ID) and reconstruction. These SFs are not used anywhere in the trilepton analysis, and **the AN must say so** (`%% TODO` in `Sections/Trigger.tex`, validation subsection).
  - Analyzer flag `RunZEE`, run after the main DiLepton production.

## 2026-11-24 (JME and PdmV recommendations)

Sources, provided by the user (behind CERN login): `docs/CMS/JME_NoiseFilters.md`, `docs/CMS/JME_JetID13p6TeV.md`, `docs/CMS/PdmV_Run3Analysis.md`.

- **Noise filters** (JME): apply the era's individual `Flag_*` branches to data and simulation, in every analysis.
  - Do not use `Flag_METFilters` (discontinued in NanoAODv15). HBHE filters are not required in Run 3.
  - The 2022-2023 prompt-reco bad-ECAL-crystal veto (runs 362433-367144, data only) does not concern 2024 (2024 runs start at 378971). SKNano 2.0 applies it by run range, so it is inactive for 2024.
  - **Run 3 list** (table transcribed into `docs/CMS/JME_NoiseFilters.md`): goodVertices, globalSuperTightHalo2016Filter, EcalDeadCellTriggerPrimitiveFilter, BadPFMuonFilter, BadPFMuonDzFilter, hfNoisyHitsFilter, eeBadScFilter, and **ecalBadCalibFilter: "2024: use the stored flag"**.
  - All are present in the 2024 data and MC files (RNTuplizer `branch_selection.csv`).
  - SKNano 2.0's Run 3 list (`AnalyzerCore.h:874-880`) omits `Flag_ecalBadCalibFilter`, which it applies only for 2017/2018. **Our module adds it for 2024, in data and simulation.**
- **Jet ID** (JME): NanoV15 has no `Jet_jetId`; it must be computed from the energy fractions and multiplicities (correctionlib `jetid.json`, or the twiki pseudocode).
  - The 2024 criteria are the ones for "2022 re-reco CDE, 2022 FG, 2023 BCD, and 2024 FG" (preliminary for 2024, to be tested on the 2024 re-reco CDE). For |eta| <= 2.6: NHF < 0.99, NEMF < 0.9, constituents > 1, CHF > 0.01, CHM > 0; TightLepVeto adds MUF < 0.8 and CEMF < 0.8.
  - This is what the 2024 `jetid.json` (AK4PUPPI_Tight, AK4PUPPI_TightLeptonVeto) implements.
  - JME "generally recommend[s] ... including those marked as for LepVeto for all analyses"; analyses with their own jet-lepton cleaning may apply the ID without the lepton veto. **Decided (user): Tight** for the analysis jets, with the dR > 0.4 cleaning against loose leptons (as B2G-25-013).
- **Jet veto map** (JERC, `docs/CMS/JME_JetVetoMaps.md`; PdmV): mandatory in Run 3.
  - "Reject an event if any jet passing the minimum selection lies within a vetoed region", with map `jetvetomap` of `Summer24Prompt24_V1` for 2024, applied to data and MC alike.
  - Minimum selection: jet pT above a threshold (the number is lost in the text copy; 15 GeV in SKNano 2.0 and in B2G-25-013), **tightLepVeto** jet ID, and chEmEF + neEmEF < 0.9.
  - The Run 3 list has **no PF-muon overlap step**; that step belongs to the Run 2 "loose selection".
  - SKNano 2.0's `PassJetVetoMap` (TIGHTLEPVETO, pT > 15, |eta| < 5, EM fraction <= 0.9, no muon overlap) matches the Run 3 recommendation, so it is used as is. B2G-25-013's dR > 0.2 muon overlap was the Run 2 recipe and is dropped.
  - The veto uses tightLepVeto even though the analysis jets use Tight, as JERC specifies.
  - JERC asks to validate with jet eta-phi maps before and after the veto and to document the impact in the AN; the DiLepton output keeps those histograms.
- **Luminosity cross-check** (PdmV DATA table): Golden JSON per era C 7.26, D 7.98, E 11.42, F 28.04, G 38.07, H 5.49, I 11.56 /fb, consistent with the PPD value 109.82 /fb (the 109.95 total includes era B, 0.13 /fb, which we do not use).

## 2026-11-24 (DiLepton plan decisions)

- **MC normalization (user):** `sign(genWeight) x xsec / sumSign`, as in B2G-25-013.
- **Golden JSON:** already applied when the 2024 NanoAODv15 data were produced (user), so no lumi mask in the analyzer.
- **Top pT reweighting (user):** compare the ttbar data/MC agreement with and without it, as an explicit check in the DiLepton step.
- **JME recommendations: the twiki and JERC pages need CERN SSO and could not be read by script.** From the 2024 correction files on cvmfs (`JME/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15`):
  - `jetvetomaps.json.gz` names `jetvetomap` (`Summer24Prompt24_RunBCDEFGHI_V1`) as the map to apply to data and MC. It does not say whether to veto events or jets, or which jet selection to use.
  - `jetid.json.gz` describes its criteria as "for Run3 Rereco2022CDE" (twiki `JetID13p6TeV` rev. 18): the 2024 campaign ships the 2022 jet ID.
  - **Open:** `Flag_ecalBadCalibFilter` for 2024, the jet selection for the veto map (incl. the PF-muon overlap), and whether the 2022 jet ID is the 2024 recommendation. To be read from the JME twikis with CERN login.

## 2026-11-24

- **2024 corrections available in SKNano 2.0** (`data/Run3_v15_Run2_v15/2024/Correction/era_config.yml`, campaign `Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15`, POG files from `/cvmfs/cms-griddata.cern.ch/cat/metadata/<POG>/`):

  | Object | Corrections |
  |---|---|
  | Jets | JME `jetid.json.gz` (required), `jet_jerc.json.gz`, `jetvetomaps.json.gz` |
  | Muons | MUO `muon_Z.json.gz` (POG ID/ISO and trigger SFs), `muon_scalesmearing.json.gz` (replaces Rochester), plus local `MUO/2024_Z/` SFs and `efficiency_IsoMu24` |
  | Electrons | EGM `electron.json.gz`, `electronSS_EtDependent.json.gz` (scale and smearing), `electronHlt.json.gz` |
  | Pileup | LUM `puWeights_BCDEFGHI.json.gz` |
  | b tagging | BTV `btagging.json.gz` and local `BTV/btaggingEff.json` |

- **b tagging: BTV provides only UParTAK4 for 2024** (`UParTAK4_wp_values`, `UParTAK4_comb`, `UParTAK4_mujets`, `UParTAK4_light`; snapshot 2026-10-20). There are no DeepJet scale factors. **Decided (user):** switch from DeepJet (B2G-25-013) to UParT, **Medium** WP (`UParTAK4_wp_values`).
- **Jet ID**: `Jet_jetId` is removed in NanoAODv15. **Decided (user):** use the JME `jetid.json.gz` recipe, which SKNano 2.0 marks as required.
- **Lepton ID scale factors (decided, user):** our custom HcToWA IDs get no official POG ID/ISO SFs as substitutes. The ID SF stays empty (weight 1) until our own measurement (phase 2.3). POG corrections that do not depend on our ID (muon scale/smearing, electron scale/smearing, reconstruction, pileup, jets, b tagging) are applied.
- **Muon IDs in B2G-25-013** (old SKNano `DataFormats/src/Muon.cc:179-204`, AN-25-154 ObjectID.tex:179-184), with pT > 10 GeV and |eta| < 2.4 applied in the analyzers (`PromptAnalyzer.py:395`, `DiLepton.py:120`):

  | Requirement | Tight | Loose (Run 2) | Loose (Run 3) |
  |---|---|---|---|
  | POG Medium ID | yes | yes | yes |
  | |dz| (cm) | < 0.1 | < 0.1 | < 0.1 |
  | SIP3D | < 3 | < 5 | < 8 |
  | mini-isolation (rel.) | < 0.1 | < 0.6 | < 0.4 |
  | tracker isolation R03 (rel., trigger emulation) | < 0.4 | < 0.4 | < 0.4 |

  **Decided (user):** for 2024 the loose muon ID is the Run 3 one with **SIP3D < 5** instead of < 8 (mini-isolation < 0.4 unchanged). To be implemented in the phase 1 port.
- **Not available, measured by us** (as in AN-25-154): scale factors for the HcToWA lepton IDs (tight/loose; phase 2.3), the dilepton trigger legs and the DZ/Mass3p8 filters (phase 2.4), and b-tagging efficiencies for our selection (phase 2.5).
