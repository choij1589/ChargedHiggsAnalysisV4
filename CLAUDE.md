# CLAUDE.md

Orchestration repository for repeating B2G-25-013 (H+ -> W A, A -> mu mu, e mu mu / mu mu mu + jets) with 2024 data (NanoAODv15, RNTuple) and writing the new analysis note AN-26-267. Not a git repository: look before overwriting anything here.

## Machines

| Host | Role | Notes |
|---|---|---|
| local (`/home/choij/Sync/workspace/ChargedHiggsAnalysisV4`) | this repo, docs, scripts, AN writing | Fedora; no ROOT; scripts are copied to KNU to run |
| `knu1` = cms01.knu.ac.kr | **submission node**: HTCondor, CMS proxy | AlmaLinux 9; login shell zsh, so run multi-line logic as `ssh knu1 'bash -s' <<'EOF' ... EOF` |
| `knu`, `knu2` | other KNU login nodes | each has its own schedd and `/tmp`; knu2's queue is crowded |
| NERSC Perlmutter | ParticleNet training (later) | as in the previous analysis |

Environments:
- **`NanoV15`** (Python 3.14, ROOT 6.40.02): our scripts and analysis. Use the same environment locally (`~/micromamba/envs/NanoV15`) and on KNU (`/d0/scratch/choij/micromamba_envs/envs/NanoV15`), and add packages to both when they are needed.
- **`Nano`** (KNU): SKNano's own pinned environment. Do not modify it.
- Scripts that run on KNU login nodes outside an environment must also work with the system Python 3.9.

KNU paths (shared by all login nodes and the workers):
- `/d0/scratch/choij/SKNanoAnalyzer`: SKNano 2.0 (RNTuple/v15), container-less, with local uncommitted patches listed in `docs/LOG_Computing.md`. `source setup.sh` before use.
- `/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput/`: SKNano outputs (user, 2026-11-25; moved from `/d0/scratch/choij/SKNanoOutput`). `/d0/scratch/choij/SKNanoRunlog`: run directories.
- `/d0/scratch/choij/SKNanoInput/NanoAODv15_RNTuple`: symlink view of the inputs, built by `scripts/input_view/build_input_view.py`. Also holds the copies of our scripts and test benches.
- `/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoSkim/`: our skims (`Skim_TriLep_<sample>`).
- SKNano jobs write on the worker's local disk and copy their outputs to `/pnfs` with xrdcp at the end (local stage-out patch, 2026-11-25, `docs/LOG_Computing.md`): dCache over NFS is write-once, and SKNano's skim writer reopens its output.
- `/pnfs/knu.ac.kr/data/cms/store/user/choij/RNTuple/`: the RNTuples (signal in `TTToHcToWA_AToMuMu/<mp>/`). Jobs read them over xrootd (`root://cluster142.knu.ac.kr//store/user/choij/...`).
- `/d0/scratch/choij/RNTuplizer`: RNTuple production and QC, with its own `CLAUDE.md` and rules. Read its `results/`; do not run or edit it from here.

Rules on KNU:
- Remove condor jobs by cluster id only, never `condor_rm <user>`.
- Never run heavy work on a login node (user rule, 2026-11-25): conversions, ntuple or histogram loops over production samples, fits over many bins. They go to condor. The login nodes are for submission, builds, and short tests on a few files.
- `/d0/scratch` holds code, environments and configuration, not ROOT data files (user rule, 2026-11-25). Data products (SKNano outputs, skims, ntuples) live on `/pnfs`; anything produced on `/d0` (staging, short tests) is moved or deleted as soon as it is checked.
- Nothing is written or deleted under `/pnfs`, with two exceptions (user): our skims in `/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoSkim/` (2026-11-24) and our SKNano outputs in `/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput/` (2026-11-25), written over xrootd (dCache over NFS is write-once). Nothing else is written there, and nothing under `/pnfs` is deleted.
- Long submissions run detached (`nohup setsid ... &`) with a log.
- Jobs need a valid CMS proxy on knu1. The user runs `voms-proxy-init --voms cms --valid 192:00` there; check it with `voms-proxy-info` before submitting.

Analysis rules:
- The 2024 signal-region data stay blinded throughout the feasibility study (user, 2026-11-27): analyzers do not write data events with all leptons tight in the SR, and no plot or table shows them. Data in the nonprompt sideband (loose-not-tight) and in the control regions are used.

## Where things are written

- `docs/BOARD.md`: what is done, what is on-going, the next step, and the phase index. Keep it short and current.
- `docs/PLAN_<Milestone>.md`: the implementation plan of a milestone (what is reproduced, design, steps with gates, open decisions), e.g. `PLAN_DiLepton.md`.
- `docs/LOG_<Section>.md`: dated decision and finding logs, newest entry first, one file per AN section (`Dataset`, `ObjectID`, `Trigger`, `EventSel`, `BkgEst`, `TmpCnstrct`, `SystUnc`, `Result`), plus `LOG_Computing.md` for infrastructure. Every decision, number source and open item goes here when it happens.
- `docs/AN-26-267/`: the analysis note, a separate git repository (symlink to `~/Sync/Documents/AN/AN-26-267`) with its own `CLAUDE.md`. Scientific content is written by the `an-writer` agent; final edits are done in that repository.
- `docs/CMS/`: copies of CMS recommendation pages behind CERN login (JME noise filters, JetID13p6TeV, JERC jet veto maps, PdmV Run 3 analysis), and POG slides in `docs/CMS/{MUO,EGM}/` (each with a README of the setup). Cite them in the logs instead of re-fetching.
- `docs/previous_analysis/`: B2G-25-013 paper, AN-25-154, ChargedHiggsAnalysisV3, the old SKNanoAnalyzer. Read-only references.
- `scripts/`, `config/`: our tools (sample metadata, input view) and their outputs. Each script's docstring states what it checks.

## Agents and skills

- `/an-section-update <Section> [focus]` runs the `an-writer` agent (Opus 5.5, medium effort): check the AN section, then check the code and numbers, then update the section and `docs/LOG_<Section>.md`.

## Status

See `docs/BOARD.md` (done / on-going / next step). Update it at every checkpoint.
