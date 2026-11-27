# LOG: Dataset

Decisions and findings for the Dataset section of AN-26-267: samples, cross sections, normalization, luminosity, data periods. Newest entry first.


## 2026-11-27 (AN: Sections 1-2 and the Dataset appendix finalized)

- **Written** (an-writer) in `docs/AN-26-267/Sections/Dataset.tex`:
  - NanoAOD release `CMSSW_15_0_22` for data, background and signal (MetaData/ProcessHistory of one Muon0 C, one WZto3LNu and the MA-15/65/125 signal NanoAOD files; the earlier "not found in the file provenance" was wrong: the release is in the process history).
  - Trilepton skim efficiencies (data 0.0942 / 0.0942 / 0.2349; signal 0.84-0.91; WZ 0.135, ZZ 0.171, ttW 0.360, tt 2l 0.293) and a new paragraph on the fake-rate skim (`Skim_FakeRate.cc`: OR of Mu8, Mu17, Ele8/12/23 PFJet30 paths, >= 1 lepton with NanoAOD pT > 8 GeV; data 0.0164/0.0163/0.0079). Source `config/skims/skim_efficiency_2024.txt`.
  - Trigger table: `HLT_Ele8_CaloIdL_TrackIdL_IsoVL_PFJet30_v` added to the nonprompt-rate paths (used by `MeasFakeRate.cc:70` and `Skim_FakeRate.cc:9`, missing in the table carried over from AN-25-154).
  - QCD samples: all 12 pT-hat bins; muons MuEnriched, electrons EMEnriched + bcToE, disjoint (F8, `LOG_BkgEst.md` 2026-11-27).
  - Generators: POWHEG BOX V2 rev3987 (2022-06-22, `VERSION` in the WZ and TTto2L2Nu gridpacks); MG5_aMC 2.9.9-2.9.18 for most samples, 2.6.5 for tWZ and TZQB, 3.5.6 for TTLNu (`mgbasedir/VERSION` of 16 gridpacks: DYGto2LG MLL-50 2.9.18, DYto2L-2J MLL-50 2.9.9, DYto2L-4J MLL-50 2.9.13, s-channel 2.9.13, tHq 2.9.18, TTG 2.9.18, TTLL MLL-50 2.9.13, TTLNu 3.5.6, TTTT 2.9.13, tWZ 2.6.5, TZQB 2.6.5, WWW 2.9.13, WZ FxFx 2.9.18, WtoLNu-2J 2.9.9, ZH 2.9.18; the other MG gridpacks not opened); PYTHIA 8.309 (`pythia8.xml` of every GS release CMSSW_14_0_18-14_0_25); CP5 tune with NNPDF31_nnlo_as_0118 in all 120 fragments; ME PDF 325300 (WZ, ZZ, tt POWHEG; signal), 325500 (4FS FxFx WZ); mt = 172.5 GeV (tt POWHEG, MG customizecards with a top, tHq/tHW fragments).
  - Generator-level m_ll: WZto3LNu and ZZto4L POWHEG `mllmin 4d0`; FxFx WZ `mll_sf = 4.0` with l = e, mu, tau, i.e. the MATRIX phase space (closes the "WZ FxFx m_ll" open item).
  - Central releases (McM `cmssw_release`): GS 14_0_18-14_0_25, DRPremix 14_0_18-14_0_25, MiniAODv6 15_0_2-15_0_22.
  - Signal: MG5_aMC 2.9.18, model 2HDM_UFO-type1_5FS, lhaid 325300, mt 172.5 GeV, widths of H+ and A 1 MeV (gridpack cards of MA-15, 65, 125 in `/pnfs/.../choij/gridpacks/Run3/MHc130/`, built with CMSSW_13_2_9; the other 20 gridpacks not opened).
  - TODOs merged: one TODO each for DY MLL-10-50 and s-channel single top (in the cross-section paragraph); every remaining TODO starts with its category (user decision / later phase / not obtainable).
- **Written** in `docs/AN-26-267/Appendix/Dataset.tex`: private chain (SIM 14_0_19; HLT, RECO 14_0_21 with 140X_mcRun3_2024_realistic_v26; MINIAODv6 15_0_4 with 150X_mcRun3_2024_realistic_v2; NANO 15_0_22); skim-efficiency column in the signal table; new `appendix:SkimEfficiency` (data, 40 background MC, 36 QCD); validation subsection (no central 2024 signal in DAS; central 2022/23 MHc-130 samples at MA 15, 30, 55, 90, 100, 125); RNTuple QC subsection and table (from `RNTuplizer/results/REPORT_sknano.md`, `overall*.csv`, README; data 112,208 files / 8,631,289,945 events, MC 299,311 / 14,636,950,322, signal 2,141 / 7,176,252; all pass; removed: 3 EGamma0 I files replaced by the recovery task, 12 MC read errors (9 QCD 300-470 MuEnriched, 3 TTto2L2Nu), 23 signal files (10 incomplete, 13 io_timeout)).
- **Method (McM, public API, no login)**: `requests/produces/<NANOAODSIM path>` -> MiniAODv6 -> DRPremix request (or the MiniAODv6 request, when it has no input dataset); the GS prepid is in that request's `reqmgr_name` (`task_<PWG>-RunIII2024Summer24[wmLHE]GS-NNNNN`); `requests/get/<GS>` for the release and `requests/get_fragment/<GS>` for the fragment. GEN-SIM datasets are not in DAS. NANOAODSIM names from `dasgoclient` on knu1 (standard `150X_mcRun3_2024_realistic_v2[_extN]-vN` datasets; TTLNu is `mg35x_...`, TZQB `Madgraph_2_6_5_...`, their only MINIAODv6 datasets). Gridpacks read on knu1 from `/cvmfs/cms.cern.ch/phys_generator/gridpacks/` and `/cvmfs/cms-griddata.cern.ch/phys_generator/gridpacks_tarball/` (single files with `tar -xOf`).
- **GS prepids** (`<PWG>-<campaign suffix>GS-NNNNN` = `<PWG>-RunIII2024Summer24<suffix>GS-NNNNN`; `+` joins base and ext): DYGto2LG-1Jets_Bin-MLL-4to50 GEN-wmLHEGS-00500; DYGto2LG-1Jets_Bin-MLL-50-PTG-100 GEN-wmLHEGS-00501; DYGto2LG-1Jets_Bin-MLL-50-PTG-200 GEN-wmLHEGS-00502; DYGto2LG-1Jets_Bin-MLL-50-PTG-400 GEN-wmLHEGS-00503; DYGto2LG-1Jets_Bin-MLL-50-PTG-600 GEN-wmLHEGS-00504; DYGto2LG-1Jets_Bin-MLL-50 GEN-wmLHEGS-00499+GEN-wmLHEGS-00638; DYto2E-2Jets_Bin-MLL-10to50 GEN-wmLHEGS-00611; DYto2E-2Jets_Bin-MLL-50 GEN-wmLHEGS-00057; DYto2E-4Jets_Bin-MLL-10to50 GEN-wmLHEGS-00251; DYto2E-4Jets_Bin-MLL-50 GEN-wmLHEGS-00248+GEN-wmLHEGS-00668+GEN-wmLHEGS-00669; DYto2Mu-2Jets_Bin-MLL-10to50 GEN-wmLHEGS-00610; DYto2Mu-2Jets_Bin-MLL-50 GEN-wmLHEGS-00055; DYto2Mu-4Jets_Bin-MLL-10to50 GEN-wmLHEGS-00252; DYto2Mu-4Jets_Bin-MLL-50 GEN-wmLHEGS-00249+GEN-wmLHEGS-00670+GEN-wmLHEGS-00671; DYto2Tau-2Jets_Bin-MLL-10to50 GEN-wmLHEGS-00612; DYto2Tau-2Jets_Bin-MLL-50 GEN-wmLHEGS-00056; DYto2Tau-4Jets_Bin-MLL-10to50 GEN-wmLHEGS-00253; DYto2Tau-4Jets_Bin-MLL-50 GEN-wmLHEGS-00250+GEN-wmLHEGS-00673+GEN-wmLHEGS-00674; GluGluH-Hto2Zto4L_Par-M-125 HIG-wmLHEGS-00795; QCD_Bin-PT-1000_Fil-EMEnriched GEN-GS-00034; QCD_Bin-PT-1000_Fil-MuEnriched GEN-GS-00023; QCD_Bin-PT-1000_Fil-bcToE GEN-GS-00012; QCD_Bin-PT-120to170_Fil-EMEnriched GEN-GS-00028; QCD_Bin-PT-120to170_Fil-MuEnriched GEN-GS-00017; QCD_Bin-PT-120to170_Fil-bcToE GEN-GS-00006; QCD_Bin-PT-15to20_Fil-EMEnriched GEN-GS-00024; QCD_Bin-PT-15to20_Fil-MuEnriched GEN-GS-00013; QCD_Bin-PT-15to20_Fil-bcToE GEN-GS-00002; QCD_Bin-PT-170to300_Fil-EMEnriched GEN-GS-00029; QCD_Bin-PT-170to300_Fil-MuEnriched GEN-GS-00018; QCD_Bin-PT-170to300_Fil-bcToE GEN-GS-00007; QCD_Bin-PT-20to30_Fil-EMEnriched GEN-GS-00025; QCD_Bin-PT-20to30_Fil-MuEnriched GEN-GS-00014; QCD_Bin-PT-20to30_Fil-bcToE GEN-GS-00003; QCD_Bin-PT-300to470_Fil-EMEnriched GEN-GS-00030; QCD_Bin-PT-300to470_Fil-MuEnriched GEN-GS-00019; QCD_Bin-PT-300to470_Fil-bcToE GEN-GS-00008; QCD_Bin-PT-30to50_Fil-EMEnriched GEN-GS-00026; QCD_Bin-PT-30to50_Fil-MuEnriched GEN-GS-00015; QCD_Bin-PT-30to50_Fil-bcToE GEN-GS-00004; QCD_Bin-PT-470to600_Fil-EMEnriched GEN-GS-00031; QCD_Bin-PT-470to600_Fil-MuEnriched GEN-GS-00020; QCD_Bin-PT-470to600_Fil-bcToE GEN-GS-00009; QCD_Bin-PT-50to80_Fil-EMEnriched GEN-GS-00052; QCD_Bin-PT-50to80_Fil-MuEnriched GEN-GS-00049; QCD_Bin-PT-50to80_Fil-bcToE GEN-GS-00051; QCD_Bin-PT-600to800_Fil-EMEnriched GEN-GS-00032; QCD_Bin-PT-600to800_Fil-MuEnriched GEN-GS-00021; QCD_Bin-PT-600to800_Fil-bcToE GEN-GS-00010; QCD_Bin-PT-800to1000_Fil-EMEnriched GEN-GS-00033; QCD_Bin-PT-800to1000_Fil-MuEnriched GEN-GS-00022; QCD_Bin-PT-800to1000_Fil-bcToE GEN-GS-00011; QCD_Bin-PT-80to120_Fil-EMEnriched GEN-GS-00027; QCD_Bin-PT-80to120_Fil-MuEnriched GEN-GS-00016; QCD_Bin-PT-80to120_Fil-bcToE GEN-GS-00005; TBbarQto2Q-t-channel-4FS TOP-wmLHEGS-00004; TBbarQtoLNu-t-channel-4FS TOP-wmLHEGS-00002; TBbartoLplusNuBbar-s-channel-4FS GEN-wmLHEGS-00437; THQ-4FS-ctcvcp_Par-M-125 HIG-wmLHEGS-01894; THW-5FS-ctcvcp_Par-M-125 HIG-wmLHEGS-01895; TTG-1Jets_Bin-PTG-100 GEN-wmLHEGS-00601; TTG-1Jets_Bin-PTG-200 GEN-wmLHEGS-00600; TTG-1Jets GEN-wmLHEGS-00602; TTH-HtoNon2B_Par-M-125 HIG-wmLHEGS-00767; TTLL-AtLeastOneTtoL-CPV TOP-wmLHEGS-00043; TTLL_Bin-MLL-4to50 GEN-wmLHEGS-00365; TTLL_Bin-MLL-50 GEN-wmLHEGS-00366; TTLNu-1Jets TOP-wmLHEGS-00023; TTTT TOP-wmLHEGS-00032; TTto2L2Nu GEN-wmLHEGS-00006+GEN-wmLHEGS-00695; TTto4Q GEN-wmLHEGS-00004+GEN-wmLHEGS-00694+GEN-wmLHEGS-00697; TTtoLNu2Q GEN-wmLHEGS-00001+GEN-wmLHEGS-00693+GEN-wmLHEGS-00696; TWZ-Tto2Q-WtoLNu-Zto2L-DR1 TOP-wmLHEGS-00061; TWZ-TtoLNu-Wto2Q-Zto2L-DR1 TOP-wmLHEGS-00060; TWZ-TtoLNu-WtoLNu-Zto2L-DR1 TOP-wmLHEGS-00059; TWminusto2L2Nu GEN-wmLHEGS-00133; TWminustoLNu2Q GEN-wmLHEGS-00132+TOP-wmLHEGS-00253; TZQB-Zto2L-4FS_Bin-MLL-30 TOP-wmLHEGS-00028; TbarBQto2Q-t-channel-4FS TOP-wmLHEGS-00005; TbarBQtoLNu-t-channel-4FS TOP-wmLHEGS-00003; TbarBtoLminusNuB-s-channel-4FS GEN-wmLHEGS-00438; TbarWplusto2L2Nu GEN-wmLHEGS-00173; TbarWplustoLNu2Q GEN-wmLHEGS-00171+TOP-wmLHEGS-00252; VBFHto2Zto4L_Par-M-125 HIG-wmLHEGS-00911; WWW-4F HIG-wmLHEGS-00762; WWZ-4F HIG-wmLHEGS-00763; WW GEN-GS-00054+GEN-GS-00058; WZZ-5F HIG-wmLHEGS-00764; WZ GEN-GS-00055+GEN-GS-00059; WZto3LNu-1Jets-4FS GEN-wmLHEGS-00613; WZto3LNu GEN-wmLHEGS-00313; WminusH-HtoNon2B_Par-M-125 HIG-wmLHEGS-00792; WplusH-HtoNon2B_Par-M-125 HIG-wmLHEGS-00793; WtoENu-2Jets GEN-wmLHEGS-00070; WtoENu-4Jets GEN-wmLHEGS-00340; WtoMuNu-2Jets GEN-wmLHEGS-00072; WtoMuNu-4Jets GEN-wmLHEGS-00344; WtoTauNu-2Jets GEN-wmLHEGS-00074; WtoTauNu-4Jets GEN-wmLHEGS-00345; ZH-HtoNon2B_Par-M-125 HIG-wmLHEGS-00794; ZZZ-5F HIG-wmLHEGS-00765; ZZ GEN-GS-00056+GEN-GS-00060; ZZto4L GEN-wmLHEGS-00315.
- **Mismatches / findings**:
  - The signal NanoAOD ParameterSets hold only the GTs 140X_mcRun3_2024_realistic_v26 and 150X_mcRun3_2024_realistic_v2; the background NanoAOD (WZto3LNu powheg) also holds 150X_mcRun3_2024_realistic_v4. The NANO step of the signal may have run with the MINIAOD GT v2, contrary to the 2026-11-24 entry ("same as the central production, no check needed"). TODO in the appendix.
  - The signal MINIAOD step used CMSSW_15_0_4; the central MiniAODv6 releases range from 15_0_2 to 15_0_22 (15_0_4 is among them).
  - AN-25-154 quotes a single MG5_aMC version (2.9.18) for Run 3; the 2024 samples use 2.6.5, 2.9.9-2.9.18 and 3.5.6.
  - The trigger table lacked the Ele8 PFJet30 path that the fake-rate code uses.
  - `RNTuplizer/unfinished_tasks.txt` maps 20 of the 41 data CRAB tasks to their input datasets; all 20 agree with `tab:Datasets`.
- **Luminosity check**: brilcalc is not available on knu1 (`which brilcalc` empty; `/cvmfs/cms-bril.cern.ch` has the brilconda environments and `cms-lumi-pog/Normtags/normtag_PHYSICS.json`, but `brilws` is not importable). What would be run once installed (e.g. `pip install --user brilws` in brilconda310, user decision): a JSON of the (run, lumi) pairs of the processed files per PD (from the RNTuples), intersected with the Golden JSON, then `brilcalc lumi -c web --normtag /cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_PHYSICS.json -u /fb -i <json>`; a short query, no condor needed.
- **Open**:
  - user decision: DY MLL-10-50 per-flavour cross section (PLAN 0.3); s-channel single top (PLAN 0.3); DYGto2LG in the conversion estimate (PLAN 3.4); gg->ZZ / gg->ZH samples for the full analysis (PLAN 0.3); brilws installation for the luminosity check (PLAN 0.3); GT of the signal NanoAOD step (PLAN 0.3); comparison of the private signal with central 2022/23 samples (PLAN 4.1).
  - later phase: prescales and nonprompt-rate paths after the fake-rate measurement (PLAN 2.4, 3.1); conversion-electron definition (PLAN 3.4); nPV mismatch after pileup reweighting (PLAN 2.2).
  - not obtainable from the outputs: input datasets of the other 21 data CRAB tasks (no input file names in the NanoAOD ParameterSets, no CRAB logs on /pnfs) (PLAN 0.3).

## 2026-11-25 (AN: trigger table)

- **Written** (an-writer) in `docs/AN-26-267/Sections/Dataset.tex`: `tab:TriggerList` gets a "Role" column; the efficiency rows now list the 2024 paths actually used: `HLT_IsoMu24` (muon ID tag, electron-leg reference), `HLT_Ele30_WPTight_Gsf` (muon-leg reference, Z->ee check), the electron ID tag OR `Ele32_WPTight_Gsf` / `Ele115_CaloIdVT_GsfTrkIdT` / `Photon200`, and the non-DZ dimuon and e-mu paths plus `Mu17_Mu8_DZ` as pairwise-filter references. The analysis DZ paths are no longer listed as efficiency paths. The paragraph no longer calls the reference dilepton paths "prescaled".
- **Sources**: KNU `2024/Trigger/HLT_Path.json` (all 14 paths present), `tnp_tamsa/config/HcToWA_{Muon,Electron}_2024.py` (`expr`), `HcToWA_Analyzers/src/MeasTrigEff.cc:20-28`.
- **Mismatch**: the 2026-11-24 table (from AN-25-154) listed `Ele32_WPTight_Gsf` and the three analysis paths for the efficiency measurements; the 2024 code uses Ele30 for the muon legs (T7), the Ele32/Ele115/Photon200 OR for the electron ID tag, and the paths without pairwise filters as references.
- Rest of the section checked against `config/xsec_2024.csv` (unchanged since 2026-11-24) and `HLT_Path.json` (`Full` 109820 /pb): no change.
- **Open**:
  - prescales of the 2024 paths (HLT_Path.json gives the full luminosity for every path, including the prescaled single-lepton ones) (PLAN 2.4, 3.1);
  - nonprompt-rate paths still carried over from AN-25-154 (PLAN 3.1);
  - unchanged from earlier entries: DY MLL-10-50, s-channel single top, WZ FxFx m_ll cut, generator versions / PDF / mt, CMSSW release, skim efficiencies (PLAN 0.3, 2.1, 3.5).

## 2026-11-24 (AN: trilepton skim, pileup figure)

- **Written** (an-writer) in `docs/AN-26-267/Sections/Dataset.tex`, after the RNTuple paragraph: the trilepton skim (>= 3 muons |eta| < 2.4 or electrons |eta| < 2.5 with uncorrected NanoAOD pT > 8 GeV, leading > 15 GeV, no ID; all NanoAOD variables kept; data MuonEG/Muon0/Muon1, MC of `tab:MCSampleListSR`, TTLL/TTLJ powheg, WZ amc@NLO, the 23 signals; electrons extended from |eta| 2.4 to 2.5 w.r.t. B2G-25-013).
- **Sources**: KNU `HcToWA_Analyzers/src/Skim_TriLep.cc:14-31`, `include/HcToWA/Skim_TriLep.h:25-28`, `/d0/scratch/choij/hcto_prod/submit_skim_trilep.sh` (sample list), `LOG_Computing.md` (Skim_TriLep).
- **Difference from AN-25-154**: the old note says the signal samples were not skimmed; in 2024 they are.
- The pileup paragraph's "Fig. XXX" now points to `fig:app-DiLeptonPileup` and `ssec:EventWeights` (ObjectID); the PU mismatch stays open (`LOG_ObjectID.md`).
- **Open**: skim efficiency per sample once the production is complete (PLAN 2.1).

## 2026-11-24 (signal normalization, groups)

- **Signal normalization (user):** xsec = 5 fb x generator filter efficiency per mass point (`scripts/sample_info/set_signal_xsec.py`, written to the KNU json). It replaces (923.6/831.76) x 0.015 pb, the downstream /3 and the 13.6/13 TeV ttbar scaling, so the 831.76 vs 833.9 pb question is gone. The signal samples contain only non-fully-hadronic WW decays, so r = 1 corresponds to sigma_sig x B(WW -> non-had) = 5 fb before the filter (the definition of the old `collectLimits.py`); the AN text says so. `filterEff` is kept in the json but is already included: do not apply it again.
- **TTTT order:** NLO QCD (aMC@NLO sample, as AN-25-154). The XSDB record's "accuracy" field says LO; the table now overrides it.
- **Background groups (user):** the B2G-25-013 paper names: Nonprompt (data-driven), $\ttbar\mathrm{X}$, Diboson, Conversion, Other. Applied in the AN signal-region tables; the control-region groups (Z, W, TT, ST, VV) are unchanged.
- **AN layout (user):** appendices live in the top-level `docs/AN-26-267/Appendix/`, not under `Sections/`.

## 2026-11-24 (AN Dataset section drafted)

- **Written** (an-writer): `docs/AN-26-267/Sections/Dataset.tex` (data sets, triggers, NanoAODv15, MC tables SR/CR/QCD, generators, cross sections, conversions, signal, pileup) and the signal table in `Sections/Appendix/Dataset.tex`. RNTuple QC appendix left as a skeleton. No bib entries added.
- **Sources**: `config/xsec_2024.csv` (equal to the KNU `CommonSampleInfo.json` up to rounding), KNU `2024/LUM/Cert_Collisions2024_378981_386951_Golden.json`, `HLT_Path.json`, RNTuplizer `results/<signal>/pipeline.json` (filter efficiencies, events), `rnt_branches.py` (8 custom electron branches).
  - Global tags read from the NanoAOD `ParameterSets` of one data and one MC file: `150X_dataRun3_v2`, `150X_mcRun3_2024_realistic_v4`.
  - Data set names from DAS: each PD/era has exactly one `MINIv6NANOv15` MINIAOD data set (versions v1-v3); KNU NEvents are 0.89-0.99 of DAS, consistent with the Golden JSON mask.
  - All nine Run 3 trigger paths of AN-25-154 exist in the 2024 NanoAOD.
- **Mismatches**:
  - Signal: SKNano normalizes to `(923.6/831.76)*0.015` pb (then /3 in `preprocess.py`), while AN-25-154 and `collectLimits.py` use σtt(13 TeV) = 833.9 pb (0.26%).
  - `xsec_2024.csv` labels TTTT "LO"; AN-25-154 says NLO QCD (amcatnlo sample, same XSDB value).
- **Open**:
  - Not verifiable from 2024 metadata, left as XXX in the AN: CMSSW release of the private NanoAOD; generator versions, PDF set, mt of the Summer24 samples; signal gridpack/MG version, mt and widths; OSSF m_ll cut of WZto3LNu/ZZto4L (PLAN 0.3, 3.5).
  - CRAB inputDataset of each data task to be confirmed (PLAN 0.3).
  - Role of the new DYGto2LG samples in the conversion estimate (PLAN 3.4).
  - Pileup reweighting and nPV plots for 2024 (PLAN 2.2); final trigger list (PLAN 2.4).
  - Still flagged (unchanged): DY MLL-10-50, s-channel single top; WZ FxFx m_ll cut.

## 2026-11-24 (flagged cross sections)

- **Decided (user)**:
  - WZ FxFx = MATRIX NNLO 5.32 pb; the POWHEG sample stays the default WZ.
  - W+jets (6 samples) = MATRIX NNLO 21216.7 pb per flavour.
  - tWZ (3 samples) = 2024 XSDB values.
- **Private signal global tag**: the same as the central production (user), so no check is needed.
- **DY MLL-10-50, 6 samples: XSDB is wrong for the per-flavour samples.**
  - The 2024 per-flavour records (21140 FxFx, 17230 MLM, "Automatically computed") equal the 2022 all-flavour DYto2L records (20950, 17380).
  - The MLL-50 per-flavour record was "Manually fixed" to 6688/3 = 2244; the 10-50 records lack that /3.
  - 21140/3 = 7047 pb (NLO), and our 6660.8 / 7047 = 0.945, the same NNLO/NLO ratio as for MLL-50 (0.943). The value used (AN-25-154 19982.5 / 3) is consistent.
  - W+jets shows the same pattern: the per-flavour records carry the all-flavour value.
  - Still flagged until confirmed by the user.
- **s-channel single top: AN-25-154's values do not match the reference AN-25-154 cites.**
  - LHC Top WG `SingleTopNNLORef` (NNLO QCD, Liu & Gao PRD 98 (2018) 071501, mt = 172.5 GeV, PDF4LHC21) at 13.6 TeV: top 7.244 (+0.124 -0.120) pb, antitop 4.534 (+0.076 -0.073) pb.
  - Times BR(W->lnu) = 3 x 0.1086 this gives 2.360 / 1.477 pb, exactly the existing 2024 entries, whose "NLO parametrization" label is wrong.
  - AN-25-154's 3.7 / 2.322 are 1.57 times higher. They entered the old SKNano json in commit 584eb8f without a formula, and their origin is unknown.
  - Proposed: 2.360 / 1.477. Still flagged with the AN values until the user decides; the published analysis used about 57% too much for this small background.
- **tWZ: no prediction beyond NLO QCD exists.**
  - CMS TOP-24-009 (arXiv:2510.19080, PRL 136 (2026) 081802) quotes 148 +10/-9 fb at 13.6 TeV (NLO QCD, MG5_aMC, DR1; 136 fb at 13 TeV). arXiv:2312.11668 and arXiv:2112.13282 likewise give NLO QCD only.
  - 148 fb x BR(Z->ll) x the W decays gives 3.28 / 3.28 / 1.59 fb for the three samples. The 2024 XSDB values used (2.964 / 2.964 / 1.392) are about 10% lower; the 2022 values in AN-25-154 (3.34 / 3.34 / 1.67) agree with 148 fb.

## 2026-11-24 (luminosity)

- **Decided (user): 2024 integrated luminosity = 109.82 /fb**, the PPD 2024 table (26 Jun 2025): Golden JSON per era, C 7.26 + D 7.98 + E 11.42 + F 28.04 + G 38.07 + H 5.49 + I 11.56.
- Set in the KNU SKNano `data/Run3_v15_Run2_v15/2024/Trigger/HLT_Path.json`: all 617 paths and `Full` go from 108950 to 109820 /pb (local, uncommitted).
- Caveat: some KNU data periods hold slightly fewer events than the older tamsa entries (e.g. Muon0 D, E, F, G, I_v2), so the lumi actually processed may be marginally below 109.82 /fb. A brilcalc check on the processed lumi sections remains possible later.

## 2026-11-24 (cross sections)

- **Decision (user):** everything stays local. The SKNano `CommonSampleInfo.json` on KNU is not sent upstream.
- **XSDB access**: `POST https://xsecdb-xsdb-official.app.cern.ch/api/search` with `{"search": {"process_name": <PD>}, "pagination": {...}, "orderBy": {}}`, authenticated with a browser `_oauth2_proxy` cookie (`~/.cache/xsdb/oauth2_proxy`). Raw results for every 2024 MC PD are in `config/xsdb_2024_raw_20261124.json`. 183 of 184 PDs have a record, not always from the 2024 campaign.
- **Scheme (user):** one cross-section table, `config/xsec_2024.csv`, built by `scripts/sample_info/make_xsec_table_2024.py`. Values and K-factors follow AN-25-154 (Dataset.tex, Run 3 table and K-factor paragraph). Classes:
  - `HO`: a higher-order calculation for the same phase space, used directly (FEWZ, MATRIX, LHC Top WG, LHCHWG). The generator value never enters the normalization (`xsec*lumi*w/sumW`).
  - `HO*K`: inclusive calculation, cut sample: generator value x K (ttZ x 1.164, ttW x 1.15).
  - `GEN`: XSDB generator value, preferring the 2024 record.
  - `PENDING`: value still missing.

  The XSDB value is kept as a cross-check column. The downstream `KFactors.json` of the previous analysis is not used, so no K-factor is applied twice.
- **XSDB caveat**: for decay-specific samples XSDB often gives the production cross section without the branching ratio: ttbar 762.1 pb for all TTto*, tW 35.99 pb, ggH 23.16 pb, VBF H 4.224 pb, W+jets about 68k pb per flavour.
- **Decided (user)**:
  - **WZto3LNu (POWHEG) = 5.32 pb**: MATRIX NNLO QCD for m_OSSF>4 GeV, l=e,mu,tau. The Run 3 WZ normalization is corrected again by the Nj SF. AN-25-154 used 5.315 x 1.10 = 5.847 pb, where 5.315 is XSDB's value for the FxFx sample and already equals the NNLO value (+10%; relevant to forNextIteration N10).
  - **ZZto4L = 1.674 pb** (superseded 1.61 pb, see below).
  - **W+H, W-H, ZH**: LHCHWG 13.6 TeV interim recommendations, arXiv:2402.09955 (LHCHWG-2024-001), mH = 125 GeV, NNLO QCD + NLO EW: W+H 0.8889, W-H 0.5677 (Table 3), ZH 0.9439 pb including gg->ZH 0.1360 (Table 4), each x BR(H->non-bb).
  - **BR(H->bb) = 0.5824** (YR4) for all Higgs samples. ttH = 0.5700 x (1-0.5824) = 0.2380 pb (arXiv:2402.09955 Table 5), replacing AN-25-154's 0.24111, which implied BR(bb) ~ 0.577.
  - **gg-initiated contributions (feasibility study): no gg samples. The qqbar samples are normalized to qqbar + gg.**
    - ZZto4L = 1.674 pb: MATRIX nNNLO QCD, with gg->ZZ at NLO.
      - Correction: MATRIX's NNLO 1.61 pb already contains gg->ZZ at LO (27.3 / 7.6 fb per channel), so it was not qqbar-only as first stated.
      - qqbar alone is 1.50 pb.
    - ZH = 0.9439 x (1-0.5824) = 0.3942 pb (qqbar 85.6%, gg 14.4%).
- **Written** into the KNU `CommonSampleInfo.json` by `scripts/sample_info/apply_xsec_table.py`: `xsec_source` recorded per entry, stale `xsec_formula` removed.
- **nmc/sumW/sumsign and data NEvents from GetEffLumi** (4,361 DAG nodes, 0 failed) written by `update_from_getefflumi.py`. All 127 KNU MC entries (104 background, 23 signal) are complete, with no -1 left.
  - Checks: nmc equals RNTuplizer's event count for every sample; sumW agrees with genEventSumw to 1e-6, except for WZ_pythia.
  - **WZ_pythia**: the Runs tree reports 30,589,150 events against 30,547,100 in the Events tree and in the generator-filter counts (no filter). The sum over the events present is used (`--accept-sumw-mismatch WZ_pythia`).
  - Data NEvents now describe the KNU files.
  - Differences from the old entries (tamsa) are expected: TT samples now include the ext datasets (e.g. TTJJ 472.5M -> 873.0M events, TTLJ 484.5M -> 683.8M), and other samples differ by small numbers of files.
- **Open**:
  - **gg-initiated samples for the full analysis** (not produced for the feasibility study):
    - gg->ZZ: MCFM continuum `GluGlu2Zto{4E,4Mu,4Tau,2E2Mu,2E2Tau,2Mu2Tau}_TuneCP5_13p6TeV_mcfm-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM`. Not the `Par-M-125` variants, which contain the Higgs already in GluGluH-Hto2Zto4L. With them, ZZto4L would go back to qqbar only (1.50 pb).
    - gg->ZH: only decay-exclusive samples exist (`GluGluZH-Zto2L-Hto{2Wto2L2Nu,2WtoLNu2Q,2Mu,...}`).
  - **s-channel single top**: AN-25-154 3.7 / 2.322 pb vs the 2024 shared entries 2.36 / 1.477 pb and XSDB LO 2.28 / 1.43 pb.
  - **DY 10-50 and W+jets**: 2024 XSDB per-flavour values are about 3 times the per-flavour expectation. Check the generator cuts.
  - **tWZ**: the 2024 XSDB values are 11-17% below AN-25-154 (2022 samples).
  - **WZ FxFx**: does its generator m_ll cut match m_OSSF>4 GeV?

## 2026-11-24

- **2024 inputs on KNU** (RNTuplizer, all QC'd and validated):
  - data: 5 PDs (Muon0, Muon1, MuonEG, EGamma0, EGamma1), Run2024C-I. Both prompt versions I and I_v2 are present, plus EGamma0 `I_recovery` (3 files); no duplicate lumis.
  - MC: 103 RunIII2024Summer24 datasets.
  - signal: 23 private points, MHc-130 only, MA 15-125 in steps of 5 GeV.
- **PPD 2024 table (26 Jun 2025)**:
  - Golden lumi per era C-I sums to 109.82 /fb. SKNano's `HLT_Path.json` says 108.95 /fb and the Lumi POG value quoted in the AN-25-154 docs is 110.11 /fb. **Open**: pin one value and its source, then use brilcalc on the lumi sections actually processed.
  - Use the highest version of reprocessed C-E and every prompt version of F-I.
  - NANO v15 GT `150X_dataRun3_v2` / `150X_mcRun3_2024_realistic_v4`. **Open**: the GT of the private production is not yet checked.
- **CommonSampleInfo.json (2024)**: `scripts/sample_info/build_commonsampleinfo_2024.py` added 109 entries (85 MC, 23 signal, MuonEG). The old→new alias map is `config/sample_aliases_2024.json`. Cross-section sources:
  - same process as the previous analysis: the 2022/2023 value;
  - DY and W split by lepton flavour in 2024: the previous inclusive value / 3 (lepton universality); 4-jet MLM samples are normalized to the same value;
  - TTG re-binned (inclusive, PTG>100, PTG>200): sums of the previous PTG bins, assuming the same PTG>10 generator cut;
  - signal: previous convention, `(923.6/831.76)*0.015` pb with `filterEff` kept separately (filter efficiency from RNTuplizer QC);
  - `TTJJ_powheg` placeholder -1 replaced by 419.7 pb (`923.6*0.6741^2`).
  - **Open**: 47 entries keep `xsec = -1` (no source in the previous analysis): QCD pT-binned EM/Mu/bcToE (new binning), DYGto2LG, VH (W+H, W-H, ZH), WZto3LNu-1Jets-4FS FxFx, TTLL-CPV. They need XSDB / MATRIX / LHCHWG values.
  - **Not changed**: existing 2024 entries whose xsec differs from the previous analysis, because the file is shared with other analyses. Examples: WZto3LNu 5.24 vs 5.315 pb, ZZto4L 1.47 vs 1.529 pb, ST s-channel 2.36 vs 3.7 pb, ttH 0.238 vs 0.241 pb. To be decided per process.
- **nmc/sumW/sumsign from GetEffLumi** (TTLL_powheg checked):
  - nmc equals RNTuplizer's event count exactly, and sumW agrees with genEventSumw to 4e-8.
  - The existing entry (tamsa) has 470.1M events = the base dataset only. KNU has base `v2-v3` (470,080,053 in DAS) + `ext1-v2` (198,944,999), less 3 files = 668,765,792.
  - The "duplicate lumis" RNTuplizer reports for this sample are the ext restarting at lumi 1, not double counting.
  - Updater: `scripts/sample_info/update_from_getefflumi.py`. It checks against RNTuplizer and only warns on a difference from the existing entry.
- **Data NEvents**: the existing Muon0/Muon1/EGamma0/EGamma1 entries do not match the KNU files. For Muon0, eras C, H and I match; D, E, F, G and I_v2 are short by 25k-273k events on KNU. To be replaced by GetEffLumi values (`--allow-nevents-change`).
