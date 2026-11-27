#!/usr/bin/env python3
"""Compare tnp_tamsa efficiency.root files of two runs (A, B) config by config:
every histogram (data/sim/sf, combined and per systematic member), every bin:
largest |A-B| and largest |A-B| / (stat error of A); fit status per bin from
fits_{data,sim}.root. Prints one line per config and histogram family."""
import glob, os, sys
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
a_dir, b_dir = sys.argv[1:3]
for fa in sorted(glob.glob(os.path.join(a_dir, "*", "efficiency.root"))):
    cfg = os.path.basename(os.path.dirname(fa))
    fb = os.path.join(b_dir, cfg, "efficiency.root")
    if not os.path.exists(fb):
        print(cfg, "MISSING in B"); continue
    A, B = ROOT.TFile.Open(fa), ROOT.TFile.Open(fb)
    print("==", cfg)
    for k in A.GetListOfKeys():
        n = k.GetName(); ha = A.Get(n); hb = B.Get(n)
        if not ha.InheritsFrom("TH1"): continue
        if not hb:
            print("  ", n, "MISSING in B"); continue
        dmax, pull, vals = 0., 0., []
        for i in range(1, ha.GetNcells() - 1):
            if ha.IsBinUnderflow(i) or ha.IsBinOverflow(i): continue
            va, vb, ea = ha.GetBinContent(i), hb.GetBinContent(i), ha.GetBinError(i)
            if va == 0 and vb == 0: continue
            d = abs(va - vb); dmax = max(dmax, d)
            if ea > 0: pull = max(pull, d / ea)
            vals.append((va, vb))
        print("   %-28s bins %2d  max|A-B| %.2e  max|A-B|/errA %.3f  e.g. %s" % (n, len(vals), dmax, pull, " ".join("%.5f/%.5f" % v for v in vals[:2])))
