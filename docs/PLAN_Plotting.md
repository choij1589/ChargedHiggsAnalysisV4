# PLAN: plotting library and scripts (2024)

Goal: one shared plotting library, `Common/Tools/plotter.py` in this repository, used by every plotting script. It has two style modes, one for the AN and one for private talks, and is written for the single 2024 era. Written 2026-11-24 from a survey of every plotting script in ChargedHiggsAnalysisV3.

## 1. How V3 plots today (survey summary)

- **Scale:** 103 active plotting files plus 51 legacy ones. 71 import `Common/Tools/plotter.py` (ROOT + cmsstyle); the rest call cmsstyle or raw `TCanvas` directly, and a few use plain matplotlib. No mplhep.
- **Shared library:** `plotter.py` (1182 lines) provides `ComparisonCanvas` (stack + data + ratio + band + signals), `KinematicCanvas`, `KinematicCanvasWithRatio`, `FitCanvasWithRatio`, plus lumi/energy tables and palettes. `HistoUtils.py` provides config loading, the systematic envelope and `CorrelatedTotalBuilder`.
- **The declared standard** (V3 `CLAUDE.md`, "Plotting Style"; reference implementations `TriLepton/python/paper_plotting.py` and `DiLepton/python/plot.py --private-work`) is followed by only a handful of scripts.

**Where the settings diverge:**

| Setting | Divergence in V3 |
|---|---|
| Label modes | No common flag set: paper is the default with no flag; `--preliminary`, `--private-work`, `--work-in-progress` exist in some scripts only; ~50 hard-coded `SetExtraText` calls; `SetCmsText` is global state and only 3 scripts reset it |
| CMS mark | 4 positions/sizes ((0.20, 0.865, 0.070), (0.1992, ...), (0.170, 0.875, 0.058), cmsstyle iPos 11 or 0) |
| Lumi header | 5 forms for Run 2 + Run 3; 11 files read `Luminosity.json` themselves |
| Legend | 5 boxes and text sizes 0.023-0.050; two scripts pass a 5-tuple that the library cannot unpack |
| Colours | Role mapping (the standard), a 9-process mapping in SignalRegionStudy, and MeasFakeRateV4 with W and Z swapped against DiLepton; `PALETTE` copied in 7 files |
| Ratio | Titles "Data / Pred", "Data / Pred.", "Obs. / Pred.", "Obs / Exp", ...; band "Stat+Syst" vs "Stat.+Syst."; ranges [0.5, 1.5] to [0, 3.5]; the band builder re-implemented twice |
| Headroom | Library 2.0; scripts 1.2-2.0; DiLepton PW 2.0 against the declared 1.6 |
| Axis titles | "M(...)" vs "m(...)", "E_T^miss" vs "p_T^miss", "#mu1" vs "#mu_{1}" in the histkeys files |
| Outputs | `plots/{era}/...png`, `plots/PW/...pdf`, `results/paper/...`, suffixes `_preliminary`/`_wip`/`_pw`, some relative to the working directory |
| Duplication | MeasTrigEff's 4 scripts are near copies; V3/V4 `validateRunPeriodTemplates` and `plotPostfitMass` are forks; the legend-panel code exists 3 times; the envelope is re-implemented in SignalRegionStudy |

**Bugs and limitations to fix in the port:**
- `ComparisonCanvas` never calls `SetLogy`, so `logy` only changes the y range (and with two different factors, 1e3 and 1e2).
- `import plotter` has side effects: it calls `CMS.setCMSStyle()` and reads `Common/Data/Luminosity.json`, and fails if the file lacks the Run2/Run3/All keys.
- Nothing knows 2024. `LumiInfo["2024"]` raises `KeyError`, `get_CoM_energy`/`get_datastream` raise for unknown eras, and `load_era_configs` silently maps any non-Run-2 era to the Run 3 systematics.
- Configs are read relative to the working directory.
- `CONFIGURATION_REFERENCE.md` is stale.

## 2. Design

### 2.1 Layout in this repository

```
Common/Tools/plotter.py      styles, era registry, canvases, colours, output paths
Common/Tools/histutils.py    loading, grouping, systematic envelope, correlated total (port of HistoUtils)
Common/Tools/test_plotter.py toy histograms drawn in every canvas and style
config/plotting/eras.json    era -> lumi (/fb), CoM (TeV), data streams; 2024 only for now
config/plotting/groups.json  group -> member aliases, colour, legend label, stack position
config/plotting/systematics_<Analyzer>.json  lanes per channel, (up, down), shape or rate
<Module>/configs/histkeys.json  per-histogram axis titles, ranges, rebinning, log scale
<Module>/python/plot*.py     thin scripts: parse arguments, load, call one canvas
```

The modules follow the analyzers: `DiLepton/` first, later `MeasTrigEff/`, `MeasFakeRate/`, `TriLepton/`, `SignalRegionStudy/`. Paths are resolved from the repository root (found from `plotter.py`'s location), never from the working directory.

### 2.2 Style modes

One argument everywhere, `--style {an,pw}` (default `an`). The canvas decides "data" vs "simulation" from whether a data histogram is drawn, so no script sets label text.

| | `an` (analysis note) | `pw` (private talks) |
|---|---|---|
| Mark | "CMS" (font 61) | "Private work" + "(CMS data)" / "(CMS simulation)" (font 52), no CMS logo text |
| Extra text | "Work in progress"; simulation-only plots: "Simulation Work in progress" | none |
| Header | "109.8 fb^{-1} (13.6 TeV)"; shape-only plots: "(13.6 TeV)" | same |
| Format | PNG | PDF |
| Output | `<Module>/plots/AN/2024/<channel>/<lane>/<histkey>.png` | `<Module>/plots/PW/2024/<channel>/<histkey>.pdf` (Central only) |

- The label is set on every draw, and `SetCmsText` is restored afterwards, so no global state leaks between plots.
- Placement follows the V3 standard: iPos 11 for both modes (the custom `cmsPosX/Y` was only for the paper mark).
- `paper` and `preliminary` presets can be added later with one table entry each; they are not needed for the feasibility study.

### 2.3 One layout (from the V3 standard, applied to both modes)

- Legend `(0.650, 0.545, 0.970, 0.870)`, text 0.036; signal legend `(0.650, 0.270, 0.970, 0.515)`, text 0.034, header "(m_{H^{+}}, m_{A}) [GeV]", colours `#d81b60, #2ca02c, #000000, #0099b4`, width 3.
- Caption: bold region over the lepton flavours, size 0.063 at (0.22, 0.75).
- Ratio: "Data / Pred.", band "Stat.+Syst." (hatch 3004, colour 12), range [0.5, 1.5] unless the histkey says otherwise.
- Headroom 1.6 (×1.4 for η plots, as in V3); `logy` really sets the log scale.
- Data points: `dataErrorX0` for equal-width bins, `maxDigits = 3`.
- Axis titles follow one convention: `m(...)`, `p_{T}^{miss}`, `#mu_{1}`.

### 2.4 Colours and stack order by group

One table in `config/plotting/groups.json`, so the role mapping cannot drift between scripts:

| Group | Colour (`PALETTE_LONG`) | Used in |
|---|---|---|
| Nonprompt / DY (Z) | [0] blue, top of the stack | SR / DiLepton |
| Diboson (VV) | [1] orange | both |
| $\ttbar$X / $\ttbar$ (TT) | [2] red | both |
| Conversion / W | [3] grey | SR / DiLepton |
| Other / single t (ST) | [4] purple, bottom | SR / DiLepton |

Stack order (bottom to top) and legend order come from the same table. The paper group names (Diboson, $\ttbar$X, Nonprompt, Conversion, Other) are the SR labels; the DiLepton CR keeps Z, W, TT, ST, VV.

### 2.5 Canvases

| Canvas | For | Notes |
|---|---|---|
| `StackCanvas` | data vs stacked prediction + signals, ratio, band | port of `ComparisonCanvas`, logy fixed |
| `ShapeCanvas` | normalized shapes with optional ratio to a reference | port of `KinematicCanvas(WithRatio)`; the corrected vs uncorrected and with/without-correction comparisons (Z->ee peak, top pT, `_NotImplemented` lanes) |
| `Map2DCanvas` | 2D maps | jet eta-phi before/after the veto map (JERC asks for these in the AN), later efficiency and SF maps |
| `EfficiencyCanvas` | TGraphAsymmErrors with data/MC ratio | trigger and ID efficiencies (phases 2.3, 2.4); replaces the 4 MeasTrigEff copies |
| `FitCanvas` | fit + components | ported when the signal-shape fits start (phase 4) |

### 2.6 Inputs

- **Source:** SKNano 2.0 outputs, `<output>/<Analyzer>/<flags>/2024/<sample>.root`, histograms at `{channel}/{lane}/{histkey}`. The data file naming is checked on the DiLepton production before the loader is written.
- **Where plots run:** locally, in `NanoV15`. The histogram files are synced from KNU `/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput/` (on /d0 until 2026-11-25) to the local `SKNanoOutput/` (a local disk, `/mnt/SKNanoOutput_Run3`), so the AN figures are made next to the AN. Only histogram files are synced.
- **Samples to groups:** aliases from `config/sample_aliases_2024.json` and groups from `config/plotting/groups.json`.
- **Systematics:** the envelope (per bin, max(|up|, |down|), added in quadrature to stat) and the correlated total, ported from `HistoUtils`, with one era. `_NotImplemented` lanes are read like any other lane.

## 3. Steps and gates

1. **Environment.** Install `cmsstyle` in `NanoV15` locally and on KNU (it is missing in both). **Gate:** `import cmsstyle` works in both.
2. **Library.** `plotter.py`, `histutils.py`, the three config files, and `test_plotter.py` drawing toy histograms in every canvas and both styles. **Gate:** the toy plots look like the V3 reference outputs (`TriLepton/plots/PW/All/SR1E2Mu/pair_mass.pdf`, `electrons_1_eta.pdf`) apart from the label and header.
3. **DiLepton** (first user, step 6 of `PLAN_DiLepton.md`). `DiLepton/python/plot.py` (stack per channel and lane), `plotCorrections.py` (with/without each correction, raw vs corrected pT), `plotJetVetoMap.py` (eta-phi before/after), and the Z->ee shape comparison. **Gate:** user review before any AN figure is made.
4. **Later modules** port as their phases start: MeasTrigEff (2.4), lepton ID SFs (2.3), MeasFakeRate (3.x), TriLepton and SignalRegionStudy (4-6).

## 3b. Status (2026-11-24)

- Step 1 done: `cmsstyle` 0.5.0 in `NanoV15` locally and on KNU.
- Step 2 done: `Common/Tools/plotter.py` (StackCanvas, ShapeCanvas, Map2DCanvas; styles `an`/`pw`), `Common/Tools/histutils.py` (Source, group sums, correlated band), `Common/Tools/test_plotter.py`, `config/plotting/{eras,groups,systematics_DiLepton}.json`. EfficiencyCanvas and FitCanvas come with their phases.
- Step 3 done: `DiLepton/python/plot.py` (`--exclude <factor>`, `--lane <lane>`; samples without the lane fall back to Central), `cutflow.py`, `plotZPeak.py`, `plotJetVetoMap.py`, `DiLepton/configs/histkeys.json`. 573 PNG (AN) and 156 PDF (PW) plots. Waiting for user review.
- **Layout revised (user, 2026-11-26):** `DiLepton/plots/AN/2024/<channel>/Central/` = the current production (`PRODUCTION` in `plot.py`, now `_LepIDSF`) with every correction applied, full band; `<channel>/No<Factor>/` = one correction removed (`<Factor>_NotImplemented`: NoMuonIDSF, NoElectronIDSF, NoElectronRecoSF, NoBtagSF, NoPileupReweight, NoElectronTrigSFProxy), MC stat band; `<channel>/TopPtReweight_Applied/` (optional correction not in Central); `<channel>/corrections.txt` = total data/MC per set. `plot.py --channel all --all-lanes` finds the lanes in the production. Purpose: the AN defines the dilepton control regions first and shows in each object section what its correction does. Old plots (proxy-SF production, `<channel>_LepIDSF/` sets) removed from the repository.
- Overflow is not folded by default (V3 behaviour); a histkey can ask for it with `"overflow": true`.

## 4. Decisions

- **P1 (decided):** AN-mode simulation-only plots are labelled "CMS Simulation Work in progress".
- **P2 (decided):** plots run locally in `NanoV15`, on histogram files synced from KNU into the local `SKNanoOutput/`.
- **P3 (decided):** ratio title "Data / Pred." in both styles, as in the V3 paper-style plots (`TriLepton/python/paper_plotting.py:64`); V3's private-work "Obs. / Pred." is not used.
