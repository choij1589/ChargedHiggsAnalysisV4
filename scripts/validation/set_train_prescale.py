#!/usr/bin/env python3
"""Set the per-sample prescale N of the TriLepton training RNTuples Train_<CH> from a test production
(docs/PLAN_ParticleNet.md P11; docs/PLAN_Optimization.md "O4 replaced by a training-tree cap").

Definition (P11): within a class, N_s = round((n_s / Y_s) / min_s'(n_s' / Y_s')), at least 1 (samples with fewer than
``--min-n`` selected entries, default 100, are not used as the reference and keep N = 1), with
n_s = raw entries and Y_s = weighted yield of sample s in the selection that defines the class, summed
over the channels (one N per sample: TrainTreePrescale.yaml is per sample). Kept events are then
proportional to xsec x acceptance and the per-event weights (x N) about uniform within the class.

Classes (P4 four classes; P5 nonprompt source; P6 genuine diboson), default membership and selection:
    signal     TTToHcToWAToMuMu-MHc130_MA*                     passSR                     weight_genpu
    diboson    WZto3LNu, ZZto4L                                allTight & (nBJets >= 1)   weight_genpu
    ttX        ttZtoLL_MLL50toInf, ttZtoLL_MLL4to50, ttWtoLNu,
               ttHtoNonbb_M125, tZq                            allTight & (nBJets >= 1)   weight_genpu
    nonprompt  TTLL_powheg, TTLJ_powheg, DYto2E_2J_*,
               DYto2Mu_2J_*, DYto2Tau_2J_*                     ~allTight & (w > 0)        weight_genpu * weight_fake
(``w`` = the class weight; negative-weight nonprompt events are dropped from the training, P5). Other
samples keep the value of the template (1). ``--classes FILE.yaml`` replaces the table:
    classes:
      diboson: {samples: [WZto3LNu, ZZto4L], selection: "allTight & (nBJets >= 1)", weight: "weight_genpu"}
Selections and weights are numpy expressions of the scalar RNTuple fields (``&``, ``|``, ``~``, comparisons,
``w`` for the weight in selections, ``True`` for all entries).

Input: a production directory with one ``<sample>.root`` per sample (hadd layout; the ``Skim_TriLep_``
prefix is dropped for the keys) or ``<sample>/hists_*.root`` (``--no-hadd`` layout, summed). If the
input RNTuple has a ``prescale`` field N_old != 1, n_s is scaled up by N_old (estimate of the
unprescaled count; the weights already contain N_old).

Output (``--output``): the YAML of SKNano ``HcToWA_Analyzers/data/TrainTreePrescale.yaml`` (header
comment block, ``default: 1``, ``samples:`` with one ``  <sample>: N`` line per sample; keys = sample
names without ``Skim_TriLep_``, the form read by TriLepton::BookTrainTrees), starting from
``--template`` (default ``$SKNANO_HOME/HcToWA_Analyzers/data/TrainTreePrescale.yaml``). It never
writes into the SKNano tree unless ``--output`` points there.
Printed: per class and sample n, Y, n/Y, N, and the events kept by the analyzer rule (exact: an entry
is kept iff N == 1 or splitmix64(event) % N == 0, the TriLepton.cc SplitMix64), raw and weighted
(sum of w x N over the kept entries, to compare with Y), and the class totals.

Stand-in (``--stand-in``, before Train trees exist): reads ``SR_<CH>_Central`` (all tight, N_b >= 1)
with weight ``weight`` and selection ``True`` for every class (the nonprompt class is then not
meaningful: those trees hold only tight events). ``--rntuple``, ``--weight``, ``--selection`` override
the RNTuple name pattern ({CH} = channel), the weight and the selection of every class.

Usage:
    set_train_prescale.py --input PROD_DIR [--classes classes.yaml] [--channels 1E2MU,3MU]
                          [--rntuple 'Train_{CH}'] [--stand-in] [--weight EXPR] [--selection EXPR]
                          [--template TrainTreePrescale.yaml] [--output new.yaml] [--json out.json]
"""
from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import math
import os
import re
import sys

import numpy as np

try:
    import awkward as ak
    import uproot
except ImportError as exc:  # pragma: no cover
    sys.exit(f"set_train_prescale.py needs uproot and awkward (NanoV15 environment): {exc}")

SKIM_PREFIX = "Skim_TriLep_"
DEFAULT_CLASSES = {
    "signal": {"samples": ["TTToHcToWAToMuMu-MHc130_MA*"], "selection": "passSR", "weight": "weight_genpu"},
    "diboson": {"samples": ["WZto3LNu", "ZZto4L"], "selection": "allTight & (nBJets >= 1)",
                "weight": "weight_genpu"},
    "ttX": {"samples": ["ttZtoLL_MLL50toInf", "ttZtoLL_MLL4to50", "ttWtoLNu", "ttHtoNonbb_M125", "tZq"],
            "selection": "allTight & (nBJets >= 1)", "weight": "weight_genpu"},
    "nonprompt": {"samples": ["TTLL_powheg", "TTLJ_powheg", "DYto2E_2J_*", "DYto2Mu_2J_*", "DYto2Tau_2J_*"],
                  "selection": "~allTight & (w > 0)", "weight": "weight_genpu * weight_fake"},
}


def splitmix64(x):
    """TriLepton.cc SplitMix64 (splitmix64 finalizer), vectorized on uint64."""
    x = np.asarray(x, dtype=np.uint64)
    with np.errstate(over="ignore"):
        x = x + np.uint64(0x9E3779B97F4A7C15)
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return x ^ (x >> np.uint64(31))


def kept_mask(event, n):
    if n == 1:
        return np.ones(len(event), dtype=bool)
    return splitmix64(event) % np.uint64(n) == 0


def names_in(expr):
    return {n for n in compile(expr, "<expr>", "eval").co_names if n not in ("True", "False", "np", "w", "abs")}


def evaluate(expr, arrays, n, w=None):
    ns = dict(arrays)
    ns["np"] = np
    ns["abs"] = np.abs
    if w is not None:
        ns["w"] = w
    val = eval(compile(expr, "<expr>", "eval"), {"__builtins__": {}}, ns)
    val = np.asarray(val)
    if val.ndim == 0:
        val = np.full(n, val.item())
    return val


def find_samples(indir):
    """{sample key (no Skim_TriLep_): [files]} for both the hadd and the --no-hadd layout."""
    out = {}
    for p in sorted(glob.glob(os.path.join(indir, "*.root"))):
        name = os.path.basename(p)[:-5]
        out.setdefault(name[len(SKIM_PREFIX):] if name.startswith(SKIM_PREFIX) else name, []).append(p)
    for d in sorted(glob.glob(os.path.join(indir, "*", ""))):
        files = sorted(glob.glob(os.path.join(d, "hists_*.root")))
        if files:
            name = os.path.basename(os.path.dirname(d))
            out.setdefault(name[len(SKIM_PREFIX):] if name.startswith(SKIM_PREFIX) else name, []).extend(files)
    return out


def class_of(sample, classes):
    for cname, c in classes.items():
        if any(fnmatch.fnmatchcase(sample, pat) for pat in c["samples"]):
            return cname
    return None


def measure(files, channels, rnt_pattern, selection, weight):
    """n, Y, kept counts for prescales computed later: returns per-channel arrays of (event, w) of the
    selected entries plus the old prescale."""
    events, weights, n_old = [], [], set()
    per_ch = {}
    need = names_in(selection) | names_in(weight) | {"event"}
    for f in files:
        with uproot.open(f) as fh:
            for ch in channels:
                name = rnt_pattern.format(CH=ch)
                if name not in fh:
                    continue
                o = fh[name]
                fields = set(o.keys())
                missing = need - fields
                if missing:
                    raise KeyError(f"{f}:{name} lacks the fields {sorted(missing)}")
                read = sorted(need | ({"prescale"} & fields))
                arr = o.arrays(read)
                cols = {k: ak.to_numpy(arr[k]) for k in read}
                n = len(arr)
                w = evaluate(weight, cols, n).astype(np.float64)
                sel = evaluate(selection, cols, n, w).astype(bool)
                if "prescale" in cols and n:
                    n_old.update(np.unique(cols["prescale"]).tolist())
                events.append(cols["event"][sel].astype(np.uint64))
                weights.append(w[sel])
                c = per_ch.setdefault(ch, [0, 0.0])
                c[0] += int(sel.sum())
                c[1] += float(w[sel].sum())
    ev = np.concatenate(events) if events else np.zeros(0, dtype=np.uint64)
    ww = np.concatenate(weights) if weights else np.zeros(0)
    return ev, ww, n_old, per_ch


def read_template(path):
    header, values, default = [], {}, 1
    with open(path) as fh:
        lines = fh.read().splitlines()
    in_samples = False
    for line in lines:
        if not in_samples:
            m = re.match(r"^default:\s*(\d+)\s*$", line)
            if m:
                default = int(m.group(1))
                continue
            if re.match(r"^samples:\s*$", line):
                in_samples = True
                continue
            if line.startswith("#") or not line.strip():
                header.append(line)
                continue
            raise ValueError(f"unexpected line in {path}: {line!r}")
        else:
            m = re.match(r"^\s+([^:#\s]+):\s*(\d+)\s*(#.*)?$", line)
            if m:
                values[m.group(1)] = int(m.group(2))
            elif line.strip() and not line.strip().startswith("#"):
                raise ValueError(f"unexpected line in {path}: {line!r}")
    while header and not header[-1].strip():
        header.pop()
    return header, default, values


def write_yaml(path, header, default, values, note):
    lines = list(header)
    if note:
        lines.append(f"# {note}")
    lines.append(f"default: {default}")
    lines.append("samples:")
    for k in sorted(values):
        lines.append(f"  {k}: {values[k]}")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="production directory (TriLepton outputs with TrainTree)")
    p.add_argument("--classes", help="YAML class membership / selection / weight (default: P4-P6 table)")
    p.add_argument("--channels", default="1E2MU,3MU")
    p.add_argument("--rntuple", default=None, help="RNTuple name pattern (default Train_{CH})")
    p.add_argument("--stand-in", action="store_true",
                   help="SR_{CH}_Central, weight 'weight', selection True (before Train trees exist)")
    p.add_argument("--weight", help="weight expression for every class (overrides the class weights)")
    p.add_argument("--selection", help="selection expression for every class (overrides the class selections)")
    p.add_argument("--template", default=None,
                   help="TrainTreePrescale.yaml to start from (default $SKNANO_HOME/HcToWA_Analyzers/data/...)")
    p.add_argument("--output", help="write the new TrainTreePrescale.yaml here")
    p.add_argument("--min-n", type=int, default=100,
                   help="samples with fewer selected raw entries are not the class reference and keep N = 1 "
                        "(default 100: one low-statistics sample would otherwise set N for the whole class)")
    p.add_argument("--reset-others", action="store_true", help="samples outside the classes: N = 1")
    p.add_argument("--json", help="write the table as JSON")
    a = p.parse_args(argv)

    classes = DEFAULT_CLASSES
    if a.classes:
        import yaml
        with open(a.classes) as fh:
            classes = yaml.safe_load(fh)["classes"]
    rnt = a.rntuple or ("SR_{CH}_Central" if a.stand_in else "Train_{CH}")
    weight_all = a.weight or ("weight" if a.stand_in else None)
    sel_all = a.selection or ("True" if a.stand_in else None)
    channels = [c for c in a.channels.split(",") if c]

    samples = find_samples(a.input)
    if not samples:
        sys.exit(f"no outputs in {a.input}")
    table = {}
    for s, files in samples.items():
        c = class_of(s, classes)
        if c is None:
            continue
        sel = sel_all or classes[c]["selection"]
        w = weight_all or classes[c]["weight"]
        ev, ww, n_old, per_ch = measure(files, channels, rnt, sel, w)
        nold = 1
        if n_old - {1}:
            if len(n_old) > 1:
                print(f"warning: {s}: several prescale values {sorted(n_old)} in the input", file=sys.stderr)
            nold = max(n_old)
        table[s] = {"class": c, "files": len(files), "n_read": int(ev.size), "n_old": nold,
                    "n": int(ev.size) * nold, "Y": float(ww.sum()), "per_channel": per_ch,
                    "_ev": ev, "_w": ww, "selection": sel, "weight": w}

    missing = {c: [pat for pat in cl["samples"] if not any(fnmatch.fnmatchcase(s, pat) for s in samples)]
               for c, cl in classes.items()}
    for c, pats in missing.items():
        if pats:
            print(f"warning: class {c}: no input for {', '.join(pats)}", file=sys.stderr)

    # prescales
    for c in classes:
        rows = {s: t for s, t in table.items() if t["class"] == c}
        ratios = [t["n"] / t["Y"] for t in rows.values() if t["n"] >= a.min_n and t["Y"] > 0]
        rmin = min(ratios) if ratios else None
        for s, t in rows.items():
            if rmin and t["n"] >= a.min_n and t["Y"] > 0:
                t["ratio"] = t["n"] / t["Y"]
                t["N"] = max(1, int(math.floor(t["ratio"] / rmin + 0.5)))
            else:
                t["ratio"] = float("nan")
                t["N"] = 1
            # kept by the analyzer rule. Input without prescale: exact. Input prescaled with N_old (its
            # entries have splitmix64(event) % N_old == 0, weights x N_old): exact if N_old divides N
            # (nested sets), otherwise an estimate n x N_old / N (flagged).
            nold = t["n_old"]
            t["kept_exact"] = nold == 1 or t["N"] % nold == 0
            if t["kept_exact"]:
                keep = kept_mask(t["_ev"], t["N"])
                t["kept"] = int(keep.sum())
                t["kept_w"] = float((t["_w"][keep] / nold * t["N"]).sum())
            else:
                t["kept"] = int(round(t["n_read"] * nold / t["N"]))
                t["kept_w"] = t["Y"]

    # print
    print(f"input: {a.input}  RNTuples: {rnt}  channels: {', '.join(channels)}"
          + ("  (STAND-IN: SR trees, weight 'weight', all entries)" if a.stand_in else ""))
    js = {}
    for c, cl in classes.items():
        rows = sorted(((s, t) for s, t in table.items() if t["class"] == c), key=lambda kv: kv[0])
        if not rows:
            continue
        sel = sel_all or cl["selection"]
        w = weight_all or cl["weight"]
        print(f"\nclass {c}: selection [{sel}], weight [{w}]")
        print(f"  {'sample':36s} {'n (raw)':>10s} {'Y':>11s} {'n/Y':>11s} {'N':>4s} {'kept':>10s} "
              f"{'kept w x N':>11s} {'kept/n':>7s}   (n, Y: selected entries of Train_<CH>, all channels)")
        tn = tk = 0
        ty = tkw = 0.0
        for s, t in rows:
            tn += t["n"]
            tk += t["kept"]
            ty += t["Y"]
            tkw += t["kept_w"]
            frac = t["kept"] / t["n"] if t["n"] else float("nan")
            low = "  (< --min-n: N = 1)" if 0 < t["n"] < a.min_n else ""
            print(f"  {s[:36]:36s} {t['n']:10d} {t['Y']:11.4g} {t['ratio']:11.5g} {t['N']:4d} {t['kept']:10d} "
                  f"{t['kept_w']:11.4g} {frac:7.3f}" + low + (f"  (input prescale {t['n_old']}" + ("" if t["kept_exact"] else "; kept estimated") + ")"
                     if t["n_old"] != 1 else ""))
            js[s] = {k: v for k, v in t.items() if not k.startswith("_")}
        print(f"  {'total':36s} {tn:10d} {ty:11.4g} {'':11s} {'':4s} {tk:10d} {tkw:11.4g} "
              f"{(tk / tn if tn else float('nan')):7.3f}")

    # yaml
    tmpl = a.template or (os.path.join(os.environ["SKNANO_HOME"], "HcToWA_Analyzers", "data", "TrainTreePrescale.yaml")
                          if os.environ.get("SKNANO_HOME") else None)
    if a.output:
        if not tmpl or not os.path.isfile(tmpl):
            sys.exit("--output needs --template (or $SKNANO_HOME) for the TrainTreePrescale.yaml format")
        header, default, values = read_template(tmpl)
        if a.reset_others:
            values = {k: 1 for k in values}
        for s, t in table.items():
            values[s] = t["N"]
        note = (f"Values set by ChargedHiggsAnalysisV4 scripts/validation/set_train_prescale.py from {a.input}"
                + (" (stand-in SR trees)" if a.stand_in else ""))
        write_yaml(a.output, header, default, values, note)
        changed = {s: t["N"] for s, t in table.items() if t["N"] != 1}
        print(f"\nwrote {a.output} ({len(values)} samples; N > 1: "
              + (", ".join(f"{k} {v}" for k, v in sorted(changed.items())) or "none") + ")")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(js, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
