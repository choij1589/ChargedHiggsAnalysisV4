---
name: an-section-update
description: Bring one section of the AN-26-267 analysis note in line with the analysis code and outputs. The workflow is check the AN section, then check the code and numbers in the analysis repositories, then update the document and the section's decision log. Use with a section name, e.g. /an-section-update Dataset, or /an-section-update BkgEst fake rates.
argument-hint: "<Section> [focus]"
context: fork
agent: an-writer
background: false
---

Update section **$ARGUMENTS** of AN-26-267. The first word is the section name (`Introduction`, `Dataset`, `ObjectID`, `Trigger`, `EventSel`, `BkgEst`, `TmpCnstrct`, `SystUnc`, `Result`, `Conclusion`, `Appendix`). Any further words narrow the focus.

## 1. Check the AN

- Read `docs/AN-26-267/AN-26-267.tex` (macros, `\input{}` list), `docs/AN-26-267/Sections/<Section>.tex` and its appendix `docs/AN-26-267/Appendix/<Section>.tex` (top level, not under `Sections/`). If the file does not exist, plan it from the same section of AN-25-154.
- Read the same section of AN-25-154: `docs/previous_analysis/AN-25-154/Sections/<Section>.tex`, and its appendix if relevant. List every item it covers: definitions, selections, samples, tables, figures, numbers.
- Read `docs/LOG_<Section>.md` and `docs/BOARD.md` (state and phase index).
- Write down the checklist: each item the section must contain, its state in AN-26-267 (missing / present / stale), and the source expected to provide it.

## 2. Check the code and numbers

For each checklist item, find the authoritative source and read the value. Where the sources are:

| Section | Sources (local = this repo or docs/previous_analysis; knu1 = /d0/scratch/choij/...) |
|---|---|
| Dataset | knu1 `SKNanoAnalyzer/data/Run3_v15_Run2_v15/2024/Sample/CommonSampleInfo.json`, `.../2024/Trigger/HLT_Path.json`, `.../2024/LUM/`; local `config/sample_aliases_2024.json`, `scripts/sample_info/`; knu1 `RNTuplizer/results/REPORT_sknano.md`, `results/overall*.csv`; `docs/LOG_Dataset.md` |
| ObjectID | knu1 `SKNanoAnalyzer/.../2024/Correction/era_config.yml`, POG files under `SKNanoAnalyzer/CMS_corrections`, the HcToWA analysis module (PLAN phase 1, once ported); the old definitions in `docs/previous_analysis/SKNanoAnalyzer/DataFormats/src/{Muon,Electron,Jet}.cc` |
| Trigger | `.../2024/Trigger/HLT_Path.json`, MeasTrigEff outputs (PLAN phase 2.4); old `ChargedHiggsAnalysisV3/MeasTrigEff` |
| EventSel | HcToWA module (TriLeptonBase / PromptAnalyzer port), ParticleNet training outputs (PLAN phase 5); old `ChargedHiggsAnalysisV3/{TriLepton,ParticleNetMD}` |
| BkgEst | fake rate, ConvSF and WZ outputs (PLAN phase 3); old `ChargedHiggsAnalysisV3/{MeasFakeRateV4,TriLepton}` |
| TmpCnstrct, SystUnc, Result | SignalRegionStudy port (PLAN phase 6), systematics configs; old `ChargedHiggsAnalysisV3/SignalRegionStudyV4` |
| all | `$SKNANO_OUTPUT` on knu1 (`/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput/<Analyzer>/<flags>/2024/`) for produced histograms |

- Read values from files with a command, not by eye. Use `python3 -c` or `jq` on JSON/CSV and ROOT for histograms; on knu1, source `/d0/scratch/choij/SKNanoAnalyzer/setup.sh` first. Record host, path, key/line and date for each value.
- Compare with AN-25-154. A different value is expected for a new data set. A different *method* or *definition* is a finding.
- Items whose 2024 step has not been run yet: note the phase (BOARD.md index) and leave a placeholder. Never fill them from the old analysis.

## 3. Update the document

- Edit `docs/AN-26-267/Sections/<Section>.tex`. Follow the structure and level of detail of AN-25-154, the local macros, and the label prefixes in `docs/AN-26-267/CLAUDE.md`. Add a `%% src:` comment line above every number, table and figure. Use `XXX` plus `%% TODO: <what> (PLAN <phase>)` for anything pending.
- For a new section, add `\input{Sections/<Section>.tex}` to `docs/AN-26-267/AN-26-267.tex` in the AN-25-154 order.
- Check that the section compiles: `cd docs/AN-26-267 && python3 .claude/skills/an-reviewer/scripts/build_target_tex.py Sections/<Section>.tex`. Undefined references to other sections are expected. Do not run the full build.
- Add a dated entry at the top of `docs/LOG_<Section>.md` (create it if missing, same layout as `docs/LOG_Dataset.md`): what was updated, the sources used, mismatches, and an **Open** list.
- Return the report described in the agent instructions.
