#!/usr/bin/env python3
"""Add the 2024 KNU samples to SKNano's CommonSampleInfo.json.

Existing entries are kept as they are (the file is shared with other analyses),
except for placeholders this analysis needs filled (see FIXES). New entries are
added for every RNTuplizer sample that has no entry yet: MC by PD, data by
primary dataset, signal by masspoint.

Cross sections come from the previous analysis (2022-2023 SKNano metadata,
data/Run3_v13_Run2_v9/2023/Sample/CommonSampleInfo.json) when the same process
was used there. A flavor-split 2024 sample gets the previous inclusive value /3
(lepton universality), a re-binned sample the sum of the previous bins. A sample
without such a source gets xsec = -1 (the repo's placeholder convention) and a
note; gate 0.3 of docs/PLAN.md requires that no -1 is left before analysis use.

nmc and sumW of new MC come from RNTuplizer (Runs genEventCount/genEventSumw,
validated against the RNTuples). sumsign, and sumW of the signal, are -1 until
GetEffLumi runs (sampleManager.py --updateMcInfo).

Usage:
  build_commonsampleinfo_2024.py --current CommonSampleInfo.json \
      --previous prev2023.json --rnt-mc overall_sknano.csv \
      --rnt-signal overall.csv --rnt-data-eras data_eras.txt \
      --out CommonSampleInfo.new.json --alias-map aliases.json
"""
import argparse
import csv
import json
import os
import re
import sys

PENDING = -1  # repo placeholder convention (see TTJJ_powheg before this script)

# Previous-analysis inclusive cross sections (pb), 13.6 TeV, from the 2023 json.
PREV = {
    "DYJets": 6345.99, "DYJets10to50": 19982.5, "WJets": 64481.58,
    "TTG_PTG10to100": 4.216, "TTG_PTG100to200": 0.4114, "TTG_PTG200toInf": 0.1284,
}

# (2024 PD on KNU) -> (alias, xsec or formula string or None, previous alias, note)
# None means: no source in the previous analysis -> PENDING.
MC = {
    # Drell-Yan, split by lepton flavor in 2024 (previous: DYJets/DYJets10to50, all flavors)
    **{f"DYto2{fl}-{nj}Jets_Bin-MLL-{m}_TuneCP5_13p6TeV_{gen}-pythia8":
       (f"DYto2{fl}_{nj}J_MLL{'10to50' if m == '10to50' else '50toInf'}",
        f"{PREV['DYJets10to50' if m == '10to50' else 'DYJets']}/3",
        "DYJets10to50" if m == "10to50" else "DYJets",
        "previous inclusive DY xsec / 3 (lepton universality)"
        + ("" if nj == "2" else "; MLM sample normalized to the same inclusive xsec as FxFx"))
       for fl in ("E", "Mu", "Tau") for nj, gen in (("2", "amcatnloFXFX"), ("4", "madgraphMLM"))
       for m in ("10to50", "50")},
    # W+jets, split by flavor (previous: WJets, all flavors)
    **{f"Wto{fl}Nu-{nj}Jets_TuneCP5_13p6TeV_{gen}-pythia8":
       (f"Wto{fl}Nu_{nj}J", f"{PREV['WJets']}/3", "WJets",
        "previous inclusive W xsec / 3 (lepton universality)"
        + ("" if nj == "2" else "; MLM sample normalized to the same inclusive xsec as FxFx"))
       for fl in ("E", "Mu", "Tau") for nj, gen in (("2", "amcatnloFXFX"), ("4", "madgraphMLM"))},
    # ttgamma, re-binned (previous: PTG 10-100, 100-200, >200)
    "TTG-1Jets_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8":
        ("TTG_1J", "4.216+0.4114+0.1284", "TTG_PTG*",
         "sum of previous PTG bins; assumes the same PTG>10 generator cut"),
    "TTG-1Jets_Bin-PTG-100_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8":
        ("TTG_1J_PTG100toInf", "0.4114+0.1284", "TTG_PTG100to200+TTG_PTG200toInf", "sum of previous PTG bins"),
    "TTG-1Jets_Bin-PTG-200_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8":
        ("TTG_1J_PTG200toInf", 0.1284, "TTG_PTG200toInf", ""),
    # same process as in the previous analysis
    "TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8": ("ttWtoLNu", 0.2502, "TTWToLNu", ""),
    "TTTT_TuneCP5_13p6TeV_amcatnlo-pythia8": ("TTTT", 0.009652, "TTTT", ""),
    "TZQB-Zto2L-4FS_Bin-MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8": ("tZq", 0.08, "tZq", ""),
    "TWZ-Tto2Q-WtoLNu-Zto2L-DR1_TuneCP5_13p6TeV_amcatnlo-pythia8":
        ("tWZ_thadWlep", 0.003338, "tWZ_thadWlep", "2022 value; the 2023 json has 0.00338 (typo)"),
    "TWZ-TtoLNu-Wto2Q-Zto2L-DR1_TuneCP5_13p6TeV_amcatnlo-pythia8": ("tWZ_tlepWhad", 0.003338, "tWZ_tlepWhad", ""),
    "TWZ-TtoLNu-WtoLNu-Zto2L-DR1_TuneCP5_13p6TeV_amcatnlo-pythia8": ("tWZ_tlepWlep", 0.001669, "tWZ_tlepWlep", ""),
    "THQ-4FS-ctcvcp_Par-M-125_TuneCP5_13p6TeV_madgraph-pythia8": ("tHq", 0.7445, "tHq", ""),
    "THW-5FS-ctcvcp_Par-M-125_TuneCP5_13p6TeV_madgraph-pythia8": ("tHW", 0.1331, "tHW", ""),
    "WWW-4F_TuneCP5_13p6TeV_amcatnlo-pythia8": ("WWW", 0.2328, "WWW", ""),
    "WWZ-4F_TuneCP5_13p6TeV_amcatnlo-pythia8": ("WWZ", 0.1851, "WWZ", ""),
    "WZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8": ("WZZ", 0.06206, "WZZ", ""),
    "ZZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8": ("ZZZ", 0.01591, "ZZZ", ""),
    "WW_TuneCP5_13p6TeV_pythia8": ("WW_pythia", 124.4, "WW_pythia", ""),
    "WZ_TuneCP5_13p6TeV_pythia8": ("WZ_pythia", 54.1, "WZ_pythia", ""),
    "ZZ_TuneCP5_13p6TeV_pythia8": ("ZZ_pythia", 17.6, "ZZ_pythia", ""),
    "GluGluH-Hto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8": ("ggHtoZZto4L_M125", 0.01434, "ggHToZZTo4L", ""),
    "VBFHto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8": ("VBFHtoZZto4L_M125", 0.00112, "VBFHToZZTo4L", ""),
    # no source in the previous analysis
    "WZto3LNu-1Jets-4FS_TuneCP5_13p6TeV_amcatnloFXFX-pythia8":
        ("WZto3LNu_1J_amcatnloFXFX", None, "", "FxFx WZ (forNextIteration N9); xsec from XSDB/MATRIX needed"),
    "WminusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8":
        ("WminusHtoNonbb_M125", None, "VHToNonbb", "previous VH was one sample; needs LHCHWG 13.6 TeV xsec x BR(non-bb)"),
    "WplusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8":
        ("WplusHtoNonbb_M125", None, "VHToNonbb", "previous VH was one sample; needs LHCHWG 13.6 TeV xsec x BR(non-bb)"),
    "ZH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8":
        ("ZHtoNonbb_M125", None, "VHToNonbb", "previous VH was one sample; needs LHCHWG 13.6 TeV xsec x BR(non-bb)"),
    "TTLL-AtLeastOneTtoL-CPV_TuneCP5_13p6TeV_madgraph-pythia8":
        ("TTLL_CPV_madgraph", None, "", "not used by B2G-25-013"),
}
# Z(ll)gamma: binning differs from the previous DYGTo2LG samples
for _bin, _alias in (("MLL-4to50", "MLL4to50"), ("MLL-50", "MLL50toInf"),
                     ("MLL-50-PTG-100", "MLL50_PTG100toInf"), ("MLL-50-PTG-200", "MLL50_PTG200toInf"),
                     ("MLL-50-PTG-400", "MLL50_PTG400toInf"), ("MLL-50-PTG-600", "MLL50_PTG600toInf")):
    MC[f"DYGto2LG-1Jets_Bin-{_bin}_TuneCP5_13p6TeV_amcatnloFXFX-pythia8"] = (
        f"DYGto2LG_1J_{_alias}", None, "DYGTo2LG_*",
        "binning differs from the previous DYGTo2LG samples; xsec from XSDB needed")
# QCD enriched: pT binning differs from the previous samples
_QCD_RE = re.compile(r"QCD_Bin-PT-(\d+)(?:to(\d+))?_Fil-(EMEnriched|MuEnriched|bcToE)_TuneCP5_13p6TeV_pythia8")

# Previous-analysis aliases that already have a 2024 entry under another name.
EXISTING_ALIASES = {
    "TTLL_powheg": ["TTLL_powheg"], "TTLJ_powheg": ["TTLJ_powheg"], "TTJJ_powheg": ["TTJJ_powheg"],
    "TTZ_M4to50": ["ttZtoLL_MLL4to50"], "TTZ_M50": ["ttZtoLL_MLL50toInf"],
    "TTHToNonbb": ["ttHtoNonbb_M125"], "WZTo3LNu_powheg": ["WZto3LNu"], "ZZTo4L_powheg": ["ZZto4L"],
    "ST_sch_top_Lep": ["ST_sch_top_Lep"], "ST_sch_antitop_Lep": ["ST_sch_antitop_Lep"],
    "ST_tch_top": ["ST_tch_top_lep", "ST_tch_top_had"], "ST_tch_antitop": ["ST_tch_antitop_lep", "ST_tch_antitop_had"],
    "ST_tW_top_Lep": ["ST_tW_top_Lep"], "ST_tW_antitop_Lep": ["ST_tW_antitop_Lep"],
    "ST_tW_top_Semilep": ["ST_tW_top_Semilep"], "ST_tW_antitop_Semilep": ["ST_tW_antitop_Semilep"],
    "Muon": ["Muon0", "Muon1"], "EGamma": ["EGamma0", "EGamma1"],
}

# Placeholders in existing entries that this analysis needs filled.
FIXES = {
    "TTJJ_powheg": ("923.6*0.6741*0.6741", "previous analysis value 419.7 (sigma_tt x BR(W->qq)^2)"),
}

# Signal: previous convention, xsec = (923.6/831.76)*0.015 pb with filterEff kept separately.
SIGNAL_RE = re.compile(r"TTToHcToWA_AToMuMu_MHc-(\d+)_MA-(\d+)_MultiLepFilter_TuneCP5_cff")
SIGNAL_XSEC = "(923.6/831.76)*0.015"


def read_csv(path):
    with open(path, newline="") as f:
        return {r["sample"] if "sample" in r else r["masspoint"]: r for r in csv.DictReader(f)}


def resolve_xsec(value):
    """Return (xsec, formula) for a float, a formula string, or None."""
    if value is None:
        return PENDING, None
    if isinstance(value, str):
        return eval(value, {"__builtins__": {}}), value  # arithmetic literals only
    return float(value), None


def qcd_entry(pd):
    m = _QCD_RE.fullmatch(pd)
    if not m:
        return None
    lo, hi, fil = m.groups()
    alias = f"QCD_PT{lo}to{hi or 'Inf'}_{fil}"
    return alias, None, "QCD_Pt-*", "pT binning differs from the previous QCD samples; xsec from XSDB needed"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--current", required=True)
    ap.add_argument("--rnt-mc", required=True, help="RNTuplizer results/overall_sknano.csv")
    ap.add_argument("--rnt-signal", required=True, help="RNTuplizer results/overall.csv")
    ap.add_argument("--rnt-data-eras", required=True,
                    help="'| PD | PD_Run2024X | events |' rows from REPORT_sknano.md")
    ap.add_argument("--out", required=True)
    ap.add_argument("--alias-map", required=True)
    args = ap.parse_args()

    info = json.load(open(args.current))
    mc_rows = read_csv(args.rnt_mc)
    sig_rows = read_csv(args.rnt_signal)
    known_pds = {v.get("PD") for v in info.values()}
    aliases = {k: list(v) for k, v in EXISTING_ALIASES.items()}
    errors_missing = [a for v in EXISTING_ALIASES.values() for a in v if a not in info]
    added, pending = [], []
    errors = [f"EXISTING_ALIASES names a missing entry: {a}" for a in errors_missing]

    def add(alias, entry, src_alias):
        if alias in info:
            errors.append(f"alias collision: {alias}")
            return
        info[alias] = entry
        added.append(alias)
        if src_alias:
            aliases.setdefault(src_alias, []).append(alias)
        if entry.get("xsec") == PENDING or entry.get("sumW") == PENDING or entry.get("sumsign") == PENDING:
            pending.append(alias)

    # background MC
    for pd, row in sorted(mc_rows.items()):
        if row["kind"] != "mc" or pd in known_pds:
            continue
        spec = MC.get(pd) or qcd_entry(pd)
        if spec is None:
            errors.append(f"no mapping for MC dataset {pd}")
            continue
        alias, xs, src, note = spec
        xsec, formula = resolve_xsec(xs)
        entry = {"isMC": 1, "PD": pd, "xsec": xsec}
        if formula:
            entry["xsec_formula"] = formula
        entry.update({"nmc": float(row["genEventCount"]), "sumsign": PENDING,
                      "sumW": float(row["genEventSumw"])})
        notes = [n for n in (note, "xsec PENDING" if xsec == PENDING else "",
                             "nmc/sumW from RNTuplizer; sumsign PENDING GetEffLumi") if n]
        entry["note"] = "; ".join(notes)
        add(alias, entry, src)

    # signal
    for mp, row in sorted(sig_rows.items()):
        m = SIGNAL_RE.fullmatch(mp)
        if not m:
            errors.append(f"unexpected signal masspoint name {mp}")
            continue
        alias = f"TTToHcToWAToMuMu-MHc{m.group(1)}_MA{m.group(2)}"
        xsec, formula = resolve_xsec(SIGNAL_XSEC)
        add(alias, {"isMC": 1, "PD": mp, "xsec": xsec, "xsec_formula": formula,
                    "nmc": float(row["n_events_clean"]), "sumsign": PENDING, "sumW": PENDING,
                    "filterEff": float(row["filter_efficiency"]),
                    "note": "private 2024 signal; previous convention (15 fb at 13 TeV scaled to 13.6 TeV, "
                            "filterEff separate); filterEff from RNTuplizer QC; sumW/sumsign PENDING GetEffLumi"},
            alias)

    # data: add primary datasets with no entry (periods from the CRAB tasks on KNU)
    eras = {}
    for line in open(args.rnt_data_eras):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        pd, task, events = cells[0], cells[1], int(cells[2].replace(",", ""))
        period = task.split("_Run2024", 1)[1]
        if period.endswith("_recovery"):  # sample_paths.py folds it into the base period
            period = period[: -len("_recovery")]
        eras.setdefault(pd, {}).setdefault(period, 0)
        eras[pd][period] += events
    for pd, per in sorted(eras.items()):
        if pd in info:
            continue
        periods = sorted(per, key=lambda p: (p[0], p))
        add(pd, {"isMC": 0, "periods": periods, "NEvents": [float(per[p]) for p in periods],
                 "note": "NEvents = events in the KNU RNTuples (RNTuplizer QC)"}, pd)

    # placeholders needed by this analysis
    for alias, (formula, note) in FIXES.items():
        e = info[alias]
        if e.get("xsec") != PENDING:
            errors.append(f"{alias}: expected placeholder xsec, found {e.get('xsec')}")
            continue
        e["xsec"], e["xsec_formula"] = resolve_xsec(formula)
        e["note"] = "; ".join(x for x in (e.get("note"), note) if x)

    if errors:
        sys.exit("ERROR:\n  " + "\n  ".join(errors))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(info, f, indent=4)
        f.write("\n")
    with open(args.alias_map, "w") as f:
        json.dump(dict(sorted(aliases.items())), f, indent=2)
        f.write("\n")
    print(f"added {len(added)} entries, fixed {len(FIXES)}; {len(pending)} with PENDING values")
    for a in pending:
        print(f"  PENDING {a}: {info[a]['note']}")


if __name__ == "__main__":
    main()
