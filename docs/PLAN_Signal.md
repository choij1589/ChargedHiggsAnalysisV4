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
- Previous chain: SignalRegionStudyV4 (preprocess -> binned templates -> datacard -> validation -> asymptotic limits), CMSSW_14_1_0_pre4 + Combine v10.5.1 + CombineHarvester v3.1.0 (ROOT 6.30; its notes say newer ROOT (6.36) segfaults template making). We move to CMSSW_16_0_0 + Combine v11.1.0 (S7).
- Previous systematics (`SignalRegionStudyV4/configs/systematics.2023.json`): lumi, pileup, muon scale and ID, electron scale, resolution, ID and reco, trigger, JES, JER, unclustered MET, b tagging (light / bc, correlated / uncorrelated), normalizations (nonprompt per channel, WZ N_jet SF shape, ZZ, ttW, ttZ, ttH, tZq, others, conversion per channel), signal theory (muF, muR, 100 PDF members, alpha_s, ISR, FSR).

## Steps and gates

### 1. b-tag efficiencies (phase 2.5)

1. Fill num / den histograms per flavour (0, 4, 5) in |eta| x pT for the jets of the S1 selection, in the key format of `makeTaggingEffJson.py`, as an option of DiLepton on TTLL (S1 (a)); the same histograms in the TriLepton tree production as the cross-check (S1 (b)).
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

1. Port the V4 chain into its own repository (user, 2026-11-27): `github.com/choij1589/SignalRegionStudy` (`main`), a git submodule `SignalRegionStudy/` of this repository locally, cloned directly on KNU (`/d0/scratch/choij/SignalRegionStudy`). CMSSW_16_0_0 with Combine v11.1.0 (S7) lives inside it on KNU (`SignalRegionStudy/CMSSW_16_0_0`, git-ignored, rebuilt by a setup script); locally in `~/local/workspace/CMSSW_16_0_0`, symlinked as `ChargedHiggsAnalysisV4/Common/CMSSW_16_0_0` (git-ignored). `env.sh` looks for `$SRS_CMSSW_BASE`, then `<module>/CMSSW_16_0_0`, then `<module>/../Common/CMSSW_16_0_0`. One era 2024, channels SR1E2Mu, SR3Mu, Combined; it reads the TriLepton trees directly (the preprocess step becomes a reader).
   - Outputs (user: option (a)): condor jobs work on the worker's disk and copy templates, datacards, workspaces and Combine outputs to `/pnfs/.../SKNanoOutput/SignalRegionStudy/2024/` (xrdcp, as SKNano); limit JSONs are pushed to git.
   - Plots (user): made locally in ChargedHiggsAnalysisV4 with `Common/Tools/plotter.py`, from the outputs copied from /pnfs; no plotting code in SignalRegionStudy and no plotting on KNU.
   - Code check: locally in the el9 container (`/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el9:x86_64`, apptainer with `--no-mount bind-paths`, since the host's `/etc/vomses` bind fails).
   - **Gates before use:** (G1) ROOT 6.36.07 reads a TriLepton RNTuple (S3); (G2) the ported template step under CMSSW_16_0_0 on one previous input (MHc130_MA90 Run3 from `/pnfs/.../SignalRegionStudyV4/samples`) reproduces the frozen previous `binning.json` and `shapes.root` (the previous notes say ROOT 6.36 segfaults template making, cause not recorded); (G3) Combine v11.1.0 AsymptoticLimits on one previous datacard agrees with the v10.5.1 result.
2. Templates, datacards, validation, asymptotic expected limits (blind) per mass point; impacts on Asimov.
3. Compare with the 2022-2023 expected limits of B2G-25-013 as they are (no luminosity scaling, user 2026-11-27).

Gate: user review; then the feasibility verdict inputs (phase 6.4) and ParticleNet (phase 5).

## Open decisions

- **S1 b-tag efficiency selection (decided, user 2026-11-27): (a), the previous method** (`previous_analysis/SKNanoAnalyzer/Analyzers/src/MeasJetTagEff.cc`): tight e mu (EMu triggers; mu > 25 & e > 15 or mu > 10 & e > 25 GeV) or >= 2 tight mu (DblMu; 20 / 10 GeV), >= 2 jets (tight ID, pT > 20, |eta| < 2.5, dR > 0.4 to loose leptons); hadron flavour; weight gen x norm x PU; |eta| {0, 0.8, 1.6, 2.1, 2.5} x pT {20, 30, 50, 70, 100, 140, 200, 300, 600, 1000}; UParT Medium only; TTLL; an efficiency-histogram option in our DiLepton analyzer; converted with `makeTaggingEffJson.py`. Cross-check (b): Skim_TriLep loose preselection, all MC, from the TriLepton tree production.
- **S2 mass points (decided, user 2026-11-27): (b), the mA interpolation of the previous study** (`SignalRegionStudyV4/docs/interpolation/WORKFLOW.md`, frozen model of 2026-08-12) on the 23 generated points MHc130_MA15-125 (5 GeV steps): per-point DCB fits (floating, then frozen median tails), shape parameters and yield model vs mA, shape-systematic deltas (dm, dsig, dN), LOO closure and interpolation uncertainties (scale, resolution, norm), banded grid (0.1 / 0.25 / 0.5 / 1.0 GeV steps), seeds sharing the background templates, no extrapolation. Adaptation (user): one mH+ only, so the (mH+, mA) surfaces become fits in mA at mH+ = 130 GeV (as the early per-mHc experiments S1-S9), same model choices (SR1E2Mu and SR3Mu_lowM pure DCB, SR3Mu_highM DCB + Chebychev2, frozen tails); the uncertainty rule keeps only the within-study RMS. **Gate (user):** look at the interpolation (modelling) uncertainties first; if they are large, the limits stay on the simulated mass points only until the full simulation is available. **Gate passed (user, 2026-11-28):** LOO uncertainties norm 1-4%, peak 0.03-0.04 sigma, width 1.5-2.1% (`LOG_TmpCnstrct.md`); interp-signal templates after 11/30.
- **S3 producer and format (decided, user 2026-11-27):** tree mode in TriLepton (flag `SRTree`; one SR definition for histograms and templates), SKNano RNTuple output (`BookRNTuple`), one RNTuple per systematic with the previous fields (`mass`, `mass1`, `mass2`, `pT`, `weight`; signal adds the matched A pair); the chain reads the RNTuples directly with ROOT 6.36 (CMSSW_16_0_0), no TTree conversion. Gate in step 3.1: ROOT 6.36.07 reads a TriLepton RNTuple written by 6.40.02 (half-precision fields included) with identical values.
- **S4 systematics (decided, user 2026-11-27): the full previous list where 2024 inputs exist**, reusing the DiLepton lanes (`data/DiLeptonSystematics.yaml`): PileupReweight, MuonEn, MuonRes (new), MuonIDSF, ElectronEn, ElectronRes, ElectronIDSF, ElectronRecoSF, trigger SFs as shape (EMuTrigSF e mu mu, DblMuTrigSF mu mu mu; previous flat 3% / 2%), JetEn (total), JetRes, UnclusteredEn, BtagSF_{HF,LF}{corr,uncorr}; lnN: lumi (S6), nonprompt (S5), conversion 10.3% / 13.3% (ConvSF total), WZ 12% correlated, ZZ 4.2%, ttW 12%, ttZ 7.5%, ttH 10%, tZq 3.5%, others 50%; autoMCStats; no top pT. Storage: separate RNTuples only for the event-loop (object) variations (7 sources x up/down); weight-only variations as extra weight fields of the Central RNTuple, mapped to the nuisance names by the reader.
- **Signal normalization and theory (decided, user 2026-11-27):** limits on B_sig only (signal yield = 2 sigma(tt) x B_sig x acceptance); lnN on the signal with the tt cross-section uncertainty (923.6 pb NNLO+NNLL, TOP recommendation; scale and PDF+alpha_s values to be taken from the source and logged). Signal muF, muR (LHEScaleWeight), 100 PDF members + alpha_s (LHEPdfWeight), ISR / FSR (PSWeight) as shape nuisances with the inclusive normalization preserved: each variation scaled by sum(w_nom) / sum(w_var) over all generated events of the sample (acceptance effect kept, inclusive cross-section effect removed, covered by the tt lnN). Needs the per-sample sums from the full signal RNTuples (short condor job, step A). No limit in cross-section units for now (it would need the tt lnN frozen).
- **S5 nonprompt nuisances (decided, user 2026-11-27): F1 as decided** (`PLAN_BkgEst.md` F1): one shape nuisance per lepton flavour (`CMS_..._nonprompt_mu`, `_el`), shared by the channels, up/down from that flavour's rates at Total_Up / Total_Down (coherent over the rate bins), the other flavour nominal. Implementation: weight fields `weight_NonpromptMu_{Up,Down}`, `weight_NonpromptEl_{Up,Down}` in the nonprompt RNTuple, and the same per-flavour split in the histogram lanes (per-flavour effect for the AN). No extra lnN.
- **S6 2024 luminosity uncertainty:** value and correlation scheme (LUM POG 2024 recommendation).
- **S7 chain environment (decided, user 2026-11-27, Combine recommendation):** CMSSW_16_0_0 (el9_amd64_gcc13, ROOT 6.36.07) + Combine v11.1.0 (`git clone --depth 1 --branch v11.1.0`, `scramv1 b clean; scramv1 b -j$(nproc --ignore=2)`, always a clean build). No CombineHarvester: `combineTool.py` and `plotImpacts.py` are part of Combine since v10. Replaces CMSSW_14_1_0_pre4 + Combine v10.5.1 + CombineHarvester v3.1.0 of the previous chain.
- **S8 signal normalization:** settled with S4 (B_sig limits only, tt lnN, theory normalized at generator level).
