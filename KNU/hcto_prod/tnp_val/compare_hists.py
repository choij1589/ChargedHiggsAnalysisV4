#!/usr/bin/env python3
"""Compare the histograms of two validate_hist.py outputs (same file layout):
bin contents and errors (all bins incl. under/overflow), entries and effective
entries. Prints the largest relative differences; exit 1 if any histogram is
missing or differs by more than --tol (relative to the histogram's largest bin)."""
import argparse, glob, os, sys
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
ap = argparse.ArgumentParser()
ap.add_argument("a"); ap.add_argument("b")
ap.add_argument("--tol", type=float, default=1e-9)
args = ap.parse_args()

def hists(path):
    out = {}
    f = ROOT.TFile.Open(path)
    def walk(d, prefix):
        for k in d.GetListOfKeys():
            o = k.ReadObj()
            if o.InheritsFrom("TDirectory"):
                walk(o, prefix + k.GetName() + "/")
            elif o.InheritsFrom("TH1"):
                o.SetDirectory(0); out[prefix + k.GetName()] = o
    walk(f, ""); f.Close()
    return out

bad, nh, nfiles = 0, 0, 0
worst = {"content": 0., "error": 0., "entries": 0., "neff": 0.}
for fa in sorted(glob.glob(os.path.join(args.a, "**", "job0.root"), recursive=True)):
    rel = os.path.relpath(fa, args.a); fb = os.path.join(args.b, rel)
    if not os.path.exists(fb):
        print("MISSING file", rel); bad += 1; continue
    nfiles += 1
    ha, hb = hists(fa), hists(fb)
    for n in sorted(set(ha) | set(hb)):
        if n not in ha or n not in hb:
            print("MISSING hist", rel, n); bad += 1; continue
        x, y = ha[n], hb[n]; nh += 1
        scale = max(1e-300, max(abs(x.GetBinContent(i)) for i in range(x.GetNbinsX() + 2)))
        dc = max(abs(x.GetBinContent(i) - y.GetBinContent(i)) for i in range(x.GetNbinsX() + 2)) / scale
        de = max(abs(x.GetBinError(i) - y.GetBinError(i)) for i in range(x.GetNbinsX() + 2)) / scale
        dn = abs(x.GetEntries() - y.GetEntries()) / max(1., abs(x.GetEntries()))
        dneff = abs(x.GetEffectiveEntries() - y.GetEffectiveEntries()) / max(1., abs(x.GetEffectiveEntries()))
        for key, v in (("content", dc), ("error", de), ("entries", dn), ("neff", dneff)):
            worst[key] = max(worst[key], v)
        if max(dc, de, dn, dneff) > args.tol:
            bad += 1
            if bad <= 10:
                print("DIFF", rel, n, "content %.3g error %.3g entries %g/%g neff %.6g/%.6g" % (dc, de, x.GetEntries(), y.GetEntries(), x.GetEffectiveEntries(), y.GetEffectiveEntries()))
print("compared %d files, %d histograms; worst relative differences: %s" % (nfiles, nh, ", ".join("%s %.2g" % kv for kv in worst.items())))
print("RESULT", "OK" if bad == 0 else "FAIL (%d)" % bad)
sys.exit(0 if bad == 0 else 1)
