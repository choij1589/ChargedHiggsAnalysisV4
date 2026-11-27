"""Validation of the TriLepton SR tree mode (docs/PLAN_Signal.md step A, 2026-11-28).

  python TriLepton/python/checkSRTree.py --val <tag> [--ref Run1E2Mu_Run3Mu_V2]

1. Histogram identity: every histogram of the reference production (V2) is compared bin by bin (content and
   error, relative tolerance 1e-5) with the same histogram in the validation production (flags SRTree, RunSyst,
   BTagEffHists); histograms only in the validation file are listed (expected: Nonprompt_{Mu,El}_{Up,Down} lanes and
   the tagging#... b-tag efficiency histograms).
2. RNTuples SR_<CH>_<lane>: entries per lane; sum of `weight` of SR_<CH>_Central (MC) and SR_<CH>_Nonprompt (data)
   against the integral of the SR trilep_mass histogram of the same lane; ratio weight_<S>/weight per weight field
   (mean, min, max); signal: matchedPair fractions, lengths of w_scale, w_pdf, w_ps.
3. Blinding: no data RNTuple other than SR_<CH>_Nonprompt.
Input: SKNanoOutput/TriLepton/<tag>/2024/*.root (local copy of /pnfs). Prints a report; exit code 1 on a mismatch.
"""
import argparse
import glob
import os
import sys
from pathlib import Path

import ROOT

ROOT.gROOT.SetBatch(True)
REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "SKNanoOutput" / "TriLepton"
CHS = ["1E2MU", "3MU"]


def walk(d, prefix=""):
    for k in d.GetListOfKeys():
        cls = ROOT.TClass.GetClass(k.GetClassName())
        if not cls:  # ROOT::RNTuple anchors and other non-TObject keys
            continue
        name = f"{prefix}{k.GetName()}"
        if cls.InheritsFrom("TDirectory"):
            yield from walk(k.ReadObj(), name + "/")
        elif cls.InheritsFrom("TH1"):
            yield name, k.ReadObj()


def compare_hists(ref, val, rtol=1e-5):
    fr, fv = ROOT.TFile.Open(str(ref)), ROOT.TFile.Open(str(val))
    hr = dict(walk(fr))
    hv = dict(walk(fv))
    bad, missing = [], [k for k in hr if k not in hv]
    for k, h in hr.items():
        if k not in hv:
            continue
        g = hv[k]
        if h.GetNcells() != g.GetNcells():
            bad.append(f"{k}: ncells {h.GetNcells()} vs {g.GetNcells()}")
            continue
        for i in range(h.GetNcells()):
            a, b = h.GetBinContent(i), g.GetBinContent(i)
            ea, eb = h.GetBinError(i), g.GetBinError(i)
            if abs(a - b) > rtol * max(abs(a), abs(b), 1e-12) or abs(ea - eb) > rtol * max(ea, eb, 1e-12):
                bad.append(f"{k} bin {i}: {a:.6g} +- {ea:.3g} vs {b:.6g} +- {eb:.3g}")
                break
    extra = sorted({k.split("/")[2] if k.count("/") >= 2 else k for k in hv if k not in hr})
    return len(hr), bad, missing, extra


def rntuples(path):
    f = ROOT.TFile.Open(str(path))
    return [k.GetName() for k in f.GetListOfKeys() if k.GetClassName() == "ROOT::RNTuple"]


def check_rntuple(path, name, is_data, hist_integral):
    df = ROOT.RDataFrame(name, str(path))
    cols = [str(c) for c in df.GetColumnNames()]
    n = df.Count().GetValue()
    out = [f"    {name}: {n} entries"]
    if n == 0:
        return out, True
    sw = df.Sum("weight").GetValue()
    ok = hist_integral is None or abs(sw - hist_integral) <= 1e-4 * max(abs(sw), abs(hist_integral), 1e-9)
    out.append(f"      sum(weight) {sw:.6g}" + (f" vs SR hist {hist_integral:.6g} {'OK' if ok else 'MISMATCH'}" if hist_integral is not None else ""))
    wf = [c for c in cols if c.startswith("weight_")]
    for c in wf:
        d = df.Filter("weight != 0").Define("r", f"{c} / weight")
        out.append(f"      {c}/weight: mean {d.Mean('r').GetValue():.4f} min {d.Min('r').GetValue():.4f} max {d.Max('r').GetValue():.4f}")
    if "matchedPair" in cols:
        tot = n
        fr = {v: df.Filter(f"matchedPair == {v}").Count().GetValue() / tot for v in (0, 1, 2)}
        out.append("      matchedPair fractions " + ", ".join(f"{k}: {v:.3f}" for k, v in fr.items()))
    for c in ("w_scale", "w_pdf", "w_ps"):
        if c in cols:
            d = df.Define("len_", f"static_cast<int>({c}.size())")
            out.append(f"      {c} length min {d.Min('len_').GetValue()} max {d.Max('len_').GetValue()}")
    m = df.Filter("mass1 > 0")
    out.append(f"      mass1 mean {m.Mean('mass1').GetValue():.2f}; nJets min {df.Min('nJets').GetValue()} ; nBJets min {df.Min('nBJets').GetValue()}")
    return out, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val", required=True)
    ap.add_argument("--ref", default="Run1E2Mu_Run3Mu_V2")
    a = ap.parse_args()
    vdir, rdir = BASE / a.val / "2024", BASE / a.ref / "2024"
    fail = False
    for v in sorted(glob.glob(str(vdir / "*.root"))):
        name = os.path.basename(v)
        r = rdir / name
        is_data = "MuonEG" in name or "_Muon0" in name or "_Muon1" in name
        print("=" * 10, name)
        if r.exists():
            n, bad, missing, extra = compare_hists(r, v)
            print(f"  histograms: {n} in the reference, {len(bad)} differ, {len(missing)} missing in val; new in val: {extra[:12]}")
            for b in bad[:10]:
                print("   DIFF", b)
            for m in missing[:5]:
                print("   MISSING", m)
            fail = fail or bool(bad) or bool(missing)
        else:
            print("  no reference file")
        names = rntuples(v)
        if is_data and any(not n_.endswith("_Nonprompt") for n_ in names):
            print("  BLINDING VIOLATION: data RNTuples", names)
            fail = True
        print(f"  RNTuples: {names}")
        fv = ROOT.TFile.Open(v)
        for nt in names:
            ch, lane = nt.split("_")[1], "_".join(nt.split("_")[2:])
            hint = None
            if lane in ("Central", "Nonprompt"):
                h = fv.Get(f"{ch}/SR/{lane}/trilep_mass")
                hint = h.Integral(0, h.GetNbinsX() + 1) if h else None
            lines, ok = check_rntuple(v, nt, is_data, hint)
            print("\n".join(lines))
            fail = fail or not ok
    print("RESULT:", "FAIL" if fail else "OK")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
