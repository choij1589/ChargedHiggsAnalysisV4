# PLAN: HcToWA analyzer consolidation and efficiency (2026-11-28)

Two read-only reviews of `HcToWA_Analyzers` (SKNano `HcToWA_Run3` @ bcb270f, ~5.8k lines; subagents,
2026-11-28): redundancy across analyzers, and CPU / memory / output efficiency (with measurements on
the final TriLepton production). **Main results:** the duplicated physics logic is consistent (no
selection / SF / fake-rate / trigger / MET drift between analyzers); ~550 lines can be consolidated;
one memory risk for the next production; one large bit-identical CPU saving; ~3-4 GB of output
savings that change the stored format (user decisions). Nothing implemented yet.

## Tier 0 - before the next TriLepton production (11/30), no physics output change

| id | what | where | gain | risk |
|---|---|---|---|---|
| M1 | RNTuple writers buffer the whole output in RAM below 64 MB / cluster (Fast profile): with the new object fields the single-job tWZ samples (12.3M / 11.0M / 10.7M entries) project to ~2.5-3 GB, over the 2 GB request (jobs held and restarted). Use `RNTupleOutputProfile::Sparse` (4 MB) for SR_* / Train_* and/or split tWZ / ttZ / tZq (`-n -5`) | `TriLepton.cc:285,319,331,359`; `AnalyzerCoreOutput.cc:110-126`; submission | memory ~1.2 -> ~0.6 GB/job | values identical (more clusters) |
| C1 | TriLepton: lepton-count pre-check (ID bits and abs(eta) are lane independent) before PassEventFilters / PassJetVetoMap (full JEC/JER/JetID of every jet) and the 15 lanes; most skim events fail the counts | `TriLepton.cc:961-971` | plausibly 30-50% of TriLepton CPU | bit-identical (no fill for failing events; RNGs per event) |
| F1 | MeasFakeRate PU lanes: `w0 * pu[1]/pu[0]` gives NaN if pu[0] = 0 (w0 already has pu[0]) | `MeasFakeRate.cc:264,412` | latent NaN | none |
| F2 | ID SF / trigger-eff maps loaded for every MC analyzer (throwing loaders) incl. the analyzers that produce them (TnP, MeasTrigEff) and those that never use them: make it opt-in (DiLepton, TriLepton) | `HcToWABase.cc:37-40` | robustness | none |
| F3 | TrigSF "TrigClosure" term: loaded in try/catch (swallows errors), absent from the JSON (always 0), contradicts the user decision (LOG_Trigger): remove | `HcToWABase.cc:379-386,453`, `.h:113-114,138` | dead code / hidden errors | none |

## Tier 1 - bit-identical refactors (CPU and consolidation)

- **Per-lane redundancy in TriLepton** (A2): skip truth matching in variation lanes for non-conversion
  samples; per-event JetID seed list instead of a correctionlib JetID per jet per lane (also DiLepton,
  MeasFakeRate); cache MC weight factors (lepton / trigger SFs use nominal pT; PU lane independent;
  b-tag unchanged in non-jet lanes): ~380 of ~420 correctionlib calls per SR event are repeats;
  nominal MET propagation cached per event and LaneMET after the SR decision; trigger decision once per
  event (HLT scalar handles instead of RVec<TString> copies). Optional: staged Central result reused
  by lanes (DiLepton already does part of it). ~0.5-1 CPU-h over the production, mostly the tWZ jobs.
- **DiLepton** (A3): veto-map JetID computed twice (reuse); ComputeFactors per lane cached.
- **HcToWABase** (A4, A7): `TrigSFAll` (28 redundant trigger-efficiency calls per SR event);
  thread_local argument vectors for correctionlib calls; drop a redundant jet re-sort.
- **GenLeptonType** (A6): raw column pointers once per event.
- **Consolidation into HcToWABase** (redundancy B1-B12): module data path lookup (7 copies), EvtVar enum
  and lane helpers (3), lane MET (6 blocks), lepton collections (5; keep both electron sets: the
  "15 GeV" collection is tight in DiLepton / MeasTrigEff, loose in TriLepton / ClosFakeRate), per-event
  preamble and members (5), MC weight factors (2), b-tag lane mapping, trigger paths and plateaus
  (5 copies, identical today: drift protection), analysis jets (4) + framework JetsVetoLeptonInside,
  fake-rate load / lookup / weight / pT_corr, three-muon OS pairing, trilepton histogram sets, TnP common
  header (~100 lines), local DeltaR copies -> framework Geometry. Dead code: kZEEIDKey,
  kFEleIDProxy, unused FillVals fields, an if/else with identical branches; RunIDCheck block (+4
  electron columns required only by it) once its validation is closed. ~550 lines.
- Expected non-bit-identical deltas (rounding level only): MeasFakeRate MET (float vs double nominal
  pieces) and the last bit of the TriLepton SR `weight` if the factor order changes.

## Tier 2 - format / content changes (user decisions)

| id | what | saving | effect |
|---|---|---|---|
| O1 | Quantized (16-bit) or half-precision object eta / phi / mass in the SR RNTuples (pT, masses, weights stay float32) | ~2 GB (~25%) | stored values change at 1e-4; training reads float16 / quantized |
| O2 | ZSTD-5 instead of LZ4-1 for the analysis RNTuples (skims stay LZ4) | ~0.8-1 GB (10-13%) | none (content identical) |
| O3 | UnclusteredEn Up/Down lanes = Central except MET (the SR does not use MET): replace by MET fields in Central | ~1 GB + 2 lanes of CPU | format change (SignalRegionStudy, scoring) |
| O4 | tWZ is 49% of all SR entries: object lanes for this minor background? | 3-4 GB of the new format | physics decision |
| O5 | 3MU copies of `weight_Electron{ID,Reco}SF` (= weight); w_pdf truncation to NanoAOD precision | small | none / lossless |
| O6 | DiLepton: weight-lane histograms restricted to those used downstream; veto-map diagnostics behind a flag (allows a pre-check: 20-40% for DY jobs) | CPU | changes the diagnostic outputs |
| O7 | One DiLepton job for DIMU + EMU + ZEE on shared samples (inputs, filters, JEC, IDs once) | I/O + CPU | outputs identical (verify) |

## User decisions (2026-11-28)

- **Implement Tier 0, Tier 1 and O2** (local, one commit per step, compile check; validation on KNU after 11/30).
- **O1 as an option to compare:** TriLepton flag `QuantObj` (16-bit quantized / half-precision object eta, phi, mass); produce both after 11/30 and compare size and training.
- **O4 replaced by a training-tree cap:** deterministic per-sample prescale of Train_<CH> (hash of the event number decorrelated from the event % 5 folds; weight_genpu x N, `prescale` field), N per sample in `HcToWA_Analyzers/data/TrainTreePrescale.yaml` (defaults 1); values set from the per-sample Train counts of the first KNU test. SR_* never prescaled.
- O3, O5, O6, O7: not now.

## Status (2026-11-28 evening)

Implemented locally, one commit per step, compile check only (SKNano `HcToWA_Run3`, bcb270f..f45096c):
`78d0ac2` Tier 0 (Sparse SR/Train writers, TriLepton lepton pre-check, MeasFakeRate PU NaN, opt-in SF
maps, no TrigClosure); `58158f5` O2 (per-RNTuple ZSTD-5 via a framework SetCompression patch; skims
were already ZSTD-5); `4447fa3` Tier 1 CPU (per-event caches: PU, lepton SFs, trigger SF with one nominal
evaluation, b-tag weight; JetID seed list; trigger once per event; truth per lepton; nominal MET once;
GenLeptonType raw pointers); `cdc519f` consolidation (into HcToWABase + TriLepHists.h / TnPCommon.h;
electron sets named elLoosePt15 / elTightPt15; dead code removed; only expected delta: MeasFakeRate MET /
MT / QCD region at rounding level); `513d070` QuantObj (16-bit eta / phi, half-precision masses; framework
SetQuantized patch); `f45096c` Train prescale (`data/TrainTreePrescale.yaml`, all N = 1; splitmix64;
`prescale` field; weight_genpu x N). Module 5767 -> 5983 lines (consolidation -241; caches and two
documented headers added). Not done: HLT scalar handles (would bypass the framework trigger map;
decision cached per event instead), TVector2 DeltaR in TriLepton / GenLeptonType kept (not bit-identical
to the framework version; one shared copy), the staged Central-result reuse, RunIDCheck untouched.
Validation: reference build bcb270f vs f45096c on the same files, bisect by commit on any difference
(checklist in the agent report, `LOG_Computing.md`).

## Validation tooling and findings (2026-11-28 evening, local)

Tools in `scripts/validation/` (`compare_outputs.py`, `compare_production.py`, `set_train_prescale.py`, `README.md`
with the KNU procedure; tested locally on the final TriLepton / DiLepton outputs and perturbed copies). Findings:
- **The SKNano merge undoes O2.** `scripts/sknano_merge.py` runs `hadd -fk404` and checks that the result is LZ4-4
  (lines 290, 368, 559): every merged RNTuple is rewritten as LZ4-4 (the published SR files are LZ4-4 although the
  jobs wrote LZ4-1). The ZSTD-5 gain appears only with `--no-hadd` / index-mode outputs. **User decision:** keep
  LZ4-4 for merged outputs (O2 without effect), or patch the merge to keep the input compression (`-fk`, with the
  404 check relaxed) for the analysis RNTuples.
- **QuantObj outputs do not merge** with ROOT 6.40.02: hadd aborts (`R__unzip_header: error in header`, "Could NOT
  merge RNTuples") when it recompresses a 16-bit quantized column (scalar and vector, LZ4 and ZSTD inputs); half-
  precision columns merge. **User decision** for the O1 comparison: run QuantObj with `--no-hadd`, or keep only the
  half-precision columns, or write at 404 so hadd does not recompress (to be tested).
- Half-precision masses differ by up to 4.9e-4 relative (eta / phi 16-bit: <= 4.8e-5 absolute), not 1e-4 as above.
- No field or histogram renamed between bcb270f and f45096c: a straight comparison should differ only in
  `Train_*:prescale`, the MeasFakeRate MET rounding (which also moves events across the QCD / W region cuts: whole
  region histograms can differ) and the QuantObj option.
- **(run, lumi, event) is not unique in the signal samples** (run = lumi = 1, event numbers repeat across generation
  files; MA90 SR_3MU_Central 42,379 entries, 4,999 keys): the comparison matches by key + rank; ParticleNet score
  files are row-aligned with the SR RNTuples instead of joined on the event key (PLAN_ParticleNet P9).
- Builds: SKNano.py copies the install and a source snapshot into each run directory, so REF and NEW runs can be
  generated sequentially (build bcb270f, generate, build f45096c, generate) and queued together.
- Stand-in prescales (SR trees, all tight) reproduce the P11 preview (diboson WZ 1 / ZZ 3, 125k kept; ttX 1/2/2/6/3,
  287k; signal 1, 1.39M); a `--min-n 100` guard keeps tiny samples at N = 1 and out of the class reference.

## Validation (on KNU after 11/30)

Entry-by-entry comparison of every SR_* RNTuple and bin-by-bin histograms against the previous
build on the same files (TriLepton: TTLL, WZ, DY 2J, MA90, a MuonEG and a Muon0 era; DiLepton TrigDZ
test files; MeasFakeRate test files), with the expected rounding-level exceptions above; peak RSS from
`.performance.json` for M1.
