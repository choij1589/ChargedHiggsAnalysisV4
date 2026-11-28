# Validation of the optimized HcToWA analyzers (KNU, after the 11/30 downtime)

Reference build **bcb270f** (SKNano `HcToWA_Run3`, before the optimization) against the new build
**f45096c** (`78d0ac2` Tier 0, `58158f5` ZSTD-5, `4447fa3` CPU caches, `cdc519f` consolidation, `513d070`
QuantObj option, `f45096c` Train prescale), same input files, entry by entry and bin by bin
(`docs/PLAN_Optimization.md`, Validation). Then the Train prescales from the first Train test.

| script | what |
|---|---|
| `compare_outputs.py REF.root NEW.root` | one file pair: histograms bin by bin, RNTuples entry by entry, RNTuple sizes / compression |
| `compare_production.py REF_DIR NEW_DIR` | all matching files of two productions + summary table + `.performance.json` (CPU, RSS) |
| `set_train_prescale.py --input DIR` | per-sample N of `TrainTreePrescale.yaml` from the Train_<CH> counts (P11) |

All three run in NanoV15 (uproot, awkward, numpy; no ROOT), on KNU:
`export MAMBA_ROOT_PREFIX=/d0/scratch/choij/micromamba_envs; eval "$(/d0/scratch/choij/micromamba_bin/micromamba shell hook -s bash)"; micromamba activate /d0/scratch/choij/micromamba_envs/envs/NanoV15`
(as `hcto_prod/submit_tnp.sh convert`); copy the three scripts together (`compare_production.py` imports
`compare_outputs.py` from its own directory).
They read whole productions: run them on a worker (`condor_run`), a few files on knu1 are fine.
Timing (local, NVMe): the largest SR file (tWZ_thadWlep, 244 MB, 30 RNTuples, 12.3M entries, 195
histograms) against itself in 6 s, peak RSS 0.5 GB; key-matched mode (reordered 442k entries) 2.5 s.

## 1. Builds: sequential in the one checkout

* `setup.sh` fixes `SKNANO_BUILDDIR=$SKNANO_HOME/build/redhat`, `SKNANO_INSTALLDIR=$SKNANO_HOME/install/redhat`;
  `scripts/build.sh` uses those variables. One checkout = one build at a time (knu1, knu, knu2 share it).
* **A run is self-contained once generated:** `SKNano.py` copies `$SKNANO_INSTALLDIR` (lib, include)
  into the run directory and snapshots the source (incl. `HcToWA_Analyzers/data`) into
  `<run>/source_snapshot`; `run.sh` points `SKNANO_HOME` at that snapshot, so `ModuleDataPath` reads the
  data files of the run's own commit. The hadd / move nodes use the live `$SKNANO_HOME/scripts`
  (`sknano_merge.py`, `sknano_stageout.sh`), which bcb270f..f45096c do not touch
  (`git diff --stat bcb270f f45096c -- python templates scripts` is empty).
* So: build REF, generate the REF runs, **wait until SKNano.py has returned** (the copy of the install
  dir), then build NEW and generate the NEW runs. REF and NEW jobs can then sit in the queue together.
* A second build directory (`export SKNANO_BUILDDIR=... SKNANO_INSTALLDIR=... SKNANO_LIB=...` after
  `source setup.sh`) would only keep the production build untouched; the source tree is still one
  checkout, so the builds stay sequential, and `LD_LIBRARY_PATH` keeps the old `SKNANO_LIB`. Not worth it.
  A second checkout (`git worktree`) would need its own externals (libtorch, lhapdf, RoccoR,
  CMS_corrections), `config/config.choij` and the local data / framework patches: avoid.

```bash
ssh knu1 'bash -s' <<'EOF'
cd /d0/scratch/choij/SKNanoAnalyzer && git status --short     # only the known local files?
git fetch && git checkout bcb270f                                # detached HEAD
source setup.sh >/dev/null 2>&1
nohup setsid bash -c './scripts/build.sh > /d0/scratch/choij/hcto_prod/build_val_ref.log 2>&1; echo BUILD_RC=$? >> /d0/scratch/choij/hcto_prod/build_val_ref.log' >/dev/null 2>&1 &
EOF
# ... BUILD_RC=0, then generate/submit the REF runs (section 2), then:
#   git checkout HcToWA_Run3 && git pull   (f45096c) ; build again (build_val_new.log) ; NEW runs
```

If `git status` lists modified tracked files (local KNU patches), `git checkout` carries them over or
refuses: decide before switching (they must be the same in both builds).

## 2. Samples, flags, invocation

Common: `cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh`; for skims
`export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim`;
`export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates`; proxy check
`voms-proxy-info -timeleft`; long submissions `nohup setsid ... &` with a log (as `hcto_prod/submit_*.sh`).
Output tags: /pnfs is write-once, so REF and NEW get a label flag (no analyzer effect, like `Val`,
`HcToWABTagEff`): `ValRef` / `ValNew` (+ `ValNewQ` for QuantObj). Same `-n` and sample list for REF and
NEW (identical job split, so the `hists_<i>` and `.performance.json` match job by job).

**Use `--no-hadd` for the TriLepton validation** (see "Conflicts" below): the job shards are published
as written (the merge's `hadd -fk404` re-compresses every RNTuple to LZ4-4, which hides O2 and fails
on QuantObj columns), and the `.performance.json` side files are staged out next to them
(`$SKNANO_OUTPUT/TriLepton/<flags>/2024/<sample>/hists_<i>.root[.performance.json]`). Compare with
`compare_production.py ... --recursive`. Run one NEW sample (WZ) also with the default merge, to check
the hadd path of the new build.

| analyzer | inputs | flags (REF and NEW) | `-n` | notes |
|---|---|---|---|---|
| TriLepton MC | `Skim_TriLep_TTLL_powheg, Skim_TriLep_WZto3LNu, Skim_TriLep_DYto2Mu_2J_MLL50toInf, Skim_TriLep_TTToHcToWAToMuMu-MHc130_MA90, Skim_TriLep_tWZ_tlepWlep` | `Run1E2Mu,Run3Mu,SRTree,RunSyst,BTagEffHists,TrainTree,ValRef` | -100 | tWZ: single-job 12M-entry sample for M1 (peak RSS); TTLL/DY: nonprompt Train; MA90: signal fields |
| TriLepton MC, QuantObj (NEW only) | same | `...,TrainTree,QuantObj,ValNewQ` | -100 | O1: compare with ValNew (tolerances below) and sizes |
| TriLepton data | `Skim_TriLep_MuonEG -p G`, `Skim_TriLep_Muon0 -p G` | `Run1E2Mu,Run3Mu,SRTree,RunSyst,BTagEffHists,ValRef` | -100 | **no TrainTree on data** (ConfigError); blinding: only `SR_<CH>_Nonprompt` |
| DiLepton | `DYto2Mu_2J_MLL50toInf,TTLL_powheg,WZ_pythia` (+ `DYto2E_2J_MLL50toInf` for ZEE) | `RunDiMu,RunSyst,TrigDZ,ValRef`; `RunEMu,RunSyst,TrigDZ,ValRef`; `RunZEE,RunSyst,TrigSF,ValRef` | -100 | unskimmed NanoAOD: trimmed test jobs (below) |
| MeasFakeRate | `Skim_FakeRate_Muon0 -p G,Skim_FakeRate_QCD_PT20to30_MuEnriched` (MeasMuFR); `Skim_FakeRate_EGamma0 -p G,Skim_FakeRate_QCD_PT30to50_EMEnriched` (MeasElFR); `DYto2Mu_2J_MLL50toInf,TTLL_powheg` (MeasMuFR,MeasElFR) | as `hcto_prod/submit_measfr.sh` + `ValRef` | -100 | prompt MC: trimmed jobs |
| ClosFakeRate | `Skim_TriLep_TTLL_powheg,Skim_TriLep_TTLJ_powheg` | `Run1E2Mu,Run3Mu,ValRef` | -100 | |
| MeasTrigEff | `Muon0 -p G` (MeasElLegs,MeasDblMuPair), `EGamma0 -p G` (MeasMuLegs), `MuonEG -p G` (MeasEMuPair), `TTLL_powheg,DYto2Mu_2J_MLL50toInf` (all four) | as `hcto_prod/submit_trig.sh` + `ValRef` | -100 | unskimmed: trimmed jobs |
| MuonTnPProducer | `Muon0 -p G`, `DYto2Mu_4J_MLL50toInf` | label only (`--userflags ValRef`) | -250 / -100 | `--no-hadd` always (as `submit_tnp.sh`); RNTuples: ZSTD-5 in NEW |
| ElectronTnPProducer | `EGamma0 -p G`, `DYto2E_2J_MLL50toInf` | label only | -250 / -100 | same |

Unskimmed inputs (thousands of files): generate with `--no_exec --no-hadd`, keep the first K files of
job 1 with `hcto_prod/fr_test/trim.py <sampledir> K 0` (refuses to run if fewer files; local copy in
`KNU/hcto_prod/fr_test/trim.py`), run it with
`SHELL=/bin/bash condor_run -a jobbatchname=valtest -a x509userproxy=$(voms-proxy-info -path) bash run_i.sh`
where `run_i.sh` is `cd <sampledir> && bash run.sh 1` (the pattern of `hcto_prod/trilep_test2.sh`,
`closfr_test.sh`). With `--no-hadd` the job stages its output and side files out to /pnfs, so nothing is
left on /d0 except the run directory. Use the same K for REF and NEW. Never run a job on the login node.

## 3. Comparison and the expected differences

```bash
P=/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput/TriLepton
python compare_production.py $P/<flags>_ValRef/2024 $P/<flags>_ValNew/2024 --recursive --jobs 4 \
    --allow 'Train_*:prescale=ignore' --details /tmp/$USER/val_trilep --json /tmp/$USER/val_trilep.json
```

Run exact first; every difference outside this table means a bisect (section 4).

| what | where | expected delta | rule |
|---|---|---|---|
| `prescale` field (f45096c) | `Train_<CH>` NEW only | new field (= 1) | `--allow 'Train_*:prescale=ignore'` |
| MeasFakeRate MET in double (cdc519f) | MET, MT histograms; QCD (MET < 25, MT < 25) and W (MT > 60) regions incl. `Control/QCD`, `Control/W`, `Lanes/*/QCD_ptcorr_abseta` | rounding; single events can migrate across the 25 / 60 GeV cuts | `--allow '*FR/*/QCD/*=rel:1e-2' --allow '*FR/*/W/*=rel:1e-2' --allow '*/MET=rel:1e-2' --allow '*/MT=rel:1e-2' --allow '*/QCD_ptcorr_abseta=rel:1e-2'`; check that the differing bins are few and the integrals agree |
| MeasFakeRate PU lanes (78d0ac2) | `*/Lanes/Pileup*` | events with nominal PU weight 0 were NaN (none in the current production: no NaN bin in any MeasFakeRate output) | NaN vs number is reported as a difference: inspect |
| TriLepton SR weight factor order (4447fa3) | `SR_*:weight*`, the SR histograms | possibly the last float bit | if only these differ: `--allow 'SR_*:weight*=rel:5e-7' --allow '*/SR/*=rel:1e-6'` |
| QuantObj (513d070, ValNew vs ValNewQ) | `lep_eta, jet_eta` (16 bit in [-2.5, 2.5]: step 7.6e-5); `lep_phi, jet_phi, MET_phi` (16 bit in [-pi, pi]: step 9.6e-5); `lep_mass, jet_mass` (half precision) | abs <= 3.9e-5 (eta), <= 4.8e-5 (phi); **relative <= 4.9e-4 (masses; not 1e-4)** | `--allow '*:*_eta=abs:4e-5' --allow '*:*_phi=abs:5e-5' --allow '*:*_mass=rel:5e-4'` (`mass1/mass2`, `pT1/2`, `*_pt` and the weights stay float32 and exact) |
| ZSTD-5 (58158f5), Sparse clusters (78d0ac2) | SR_*, Train_*, TnP RNTuples | storage only (pages `ZSTD-5` instead of `LZ4-1`, more clusters) | none: printed in the storage table |

Data must stay identical (no MC-only code touched it). `compare_outputs.py` also lists RNTuple sizes,
compression and column encodings (e.g. `lep_eta: SplitReal32 -> Real32Quant(16)`), and key-matches the
entries if the order changed.

Performance: `compare_production.py` reads the `.performance.json` of both sides (with `--no-hadd`
they are next to the outputs; for hadd runs pass `--perf-ref/--perf-new <run dir>`, where the files
stay in `<run>/2024/<sample>/output/`). Expect: C1 (TriLepton pre-check) and the Tier 1 caches lower
CPU s / event; M1 (Sparse) lowers the peak RSS of the tWZ jobs (production ~1.2 GB, target ~0.6 GB).

## 4. Bisect on a difference

Content suspects: `78d0ac2` (pre-check before the filters, opt-in SF maps), `4447fa3` (caches),
`cdc519f` (consolidation). `58158f5` changes only the compression, `513d070` acts only with QuantObj,
`f45096c` only adds `prescale` (N = 1). Build 4447fa3 first: identical to REF -> culprit cdc519f (or
later); different -> build 78d0ac2. Per step: build (one at a time, ~20 s incremental locally, minutes to
40 min on /d0), generate the failing sample with `--no_exec --no-hadd` and a new label (e.g. `ValB4447`),
trim job 1 to the few files that showed the difference (the report gives the entry and event key),
`condor_run`, `compare_outputs.py`. `git bisect start f45096c bcb270f` / `git bisect good|bad` keeps the
bookkeeping. Return the checkout to `HcToWA_Run3` and rebuild at the end.

If MC jet- or lepton-smeared quantities differ in every event while data agree, check the RNG order
first (78d0ac2 moved the leptons before the event filters; the JER draws reseed per event from
PuppiMET_pt and the electron smearing is counter-based, so this is not expected).

## 5. Train prescales (after the NEW Train test)

```bash
python set_train_prescale.py --input $P/<flags>_ValNew/2024 \
    --template $SKNANO_HOME/HcToWA_Analyzers/data/TrainTreePrescale.yaml --output /tmp/$USER/TrainTreePrescale.yaml
```

Classes as P4-P6 (`--classes` to change them): signal `passSR`; diboson WZto3LNu + ZZto4L and ttX
(ttZ x2, ttW, ttH, tZq) `allTight & nBJets >= 1`; nonprompt TTLL, TTLJ, DY 2J `~allTight & w > 0` with
`w = weight_genpu * weight_fake`. Needs Train for all class samples (23 signal points, WZ, ZZ, 5 ttX,
TTLL, TTLJ, 6 DY 2J), i.e. a Train run beyond the validation samples. Samples below `--min-n` (100)
selected entries keep N = 1 and are not the class reference. Review the printed table (kept events per
sample: exact, from the analyzer's splitmix64 rule), copy the YAML into the local clone, commit, push,
pull and build on knu1.

Stand-in test on the final production's SR trees (2026-11-28, `--stand-in`): diboson WZ 1 / ZZ 3
(125164 kept), ttX ttZ(>50) 1, ttZ(4-50) 2, ttW 2, ttH 6, tZq 3 (287168 kept), signal 1 everywhere
(1387580): the P11 preview numbers.

## Conflicts with the validation plan found while writing these tools

1. **The merge undoes O2.** `scripts/sknano_merge.py` merges with `hadd -fk404`; ROOT 6.40.02's
   RNTupleMerger then rewrites every RNTuple page with LZ4-4 (404). The final production's SR RNTuples
   are 404 although the jobs wrote LZ4-1 (401); a ZSTD-5 job file merged this way is 404 too (local test,
   ROOT 6.40.02, content identical). O2's size gain therefore appears only in `--no-hadd` / index-mode
   outputs.
2. **The merge fails on QuantObj.** The same merger cannot re-compress `Real32Quant` columns: `hadd
   -fk404` (and `-f404`, `-f505`) on a file with a 16-bit quantized float field aborts with
   `R__unzip_header: error in header` / "Could NOT merge RNTuples" (local, ROOT 6.40.02, both for a scalar
   and a vector<float> field, LZ4 and ZSTD inputs); half precision (Real16) merges fine; it works only
   when no re-compression is needed (`-fk` alone, or `-fk401` on a 401 input). A QuantObj production with
   the default merge will fail at the hadd node. Options (user): `--no-hadd` / `--merge-mode index`,
   or the merge with `hadd -fk` (then `_validate_output`'s 404 check must change), or SR/Train written at 404.
3. **(run, lumi, event) is not unique in the signal samples:** all 23 TTToHcToWAToMuMu points have
   run = 1, lumi = 1 and repeat event numbers across files (MA90 `SR_1E2MU_Central`: 26842 entries with
   4978 distinct keys; `SR_3MU_Central`: 42379 with 4999; the other 22 points alike). `compare_outputs.py` handles it (entries sharing
   a key are matched by their rank in the first three float fields), but a join of score friend
   RNTuples on the event key (PLAN_ParticleNet P9) would mix events; the background samples checked
   are unique.
4. No field or histogram renames: the string literals of `HcToWA_Analyzers` differ between bcb270f and
   f45096c only in log / error messages, data-file paths, `prescale`, `QuantObj` and the removed dead
   names (`TrigClosure` correction lookup, `ElectronIDSFProxy`); the DiLepton `Central/TrigClosure/*`
   diagnostic histograms are still booked. A naive comparison therefore fails only on Train's
   `prescale` (and on QuantObj / MeasFakeRate as expected).
