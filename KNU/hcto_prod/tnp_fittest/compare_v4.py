"""Fixed-tail CB (V4) vs production s1m0 and nominal s0m0, electron altsig bins."""
import sys, os, re
sys.path.insert(0, "/d0/scratch/choij/tnp_tamsa/python")
import checkFitStatus as cfs
W = "/d0/scratch/choij/hcto_prod/tnp_fittest"; P = "/d0/scratch/choij/tnp_tamsa/results/HcToWA_Electron_2024"
jds = open(W + "/fittest_cbfix.jds").read()
for line in re.findall(r"^V4 \S+ (\S+) 1 0 (\S+) (\S+)$", jds, re.M):
    cfg, kind, bins = line
    bins = [int(b) for b in bins.split(",")]
    rows, nanp, nanv, okv, okp, dp, dv = [], 0, 0, 0, 0, [], []
    for b in bins:
        nom = cfs.read_bin("%s/%s/fits_%s.d/s0m0/bin%d.root" % (P, cfg, kind, b), "s0m0")
        prod = cfs.read_bin("%s/%s/fits_%s.d/s1m0/bin%d.root" % (P, cfg, kind, b), "s1m0")
        v4 = cfs.read_bin("%s/out/V4/%s/fits_%s.d/s1m0/bin%d.root" % (W, cfg, kind, b), "s1m0")
        isnan = lambda r: r is None or r["eff"] != r["eff"]
        nanp += isnan(prod); nanv += isnan(v4)
        st = lambda r: (not isnan(r)) and r["statusP"] in (0, 1, 3) and r["statusF"] in (0, 1, 3) and r["covQualP"] > 0 and r["covQualF"] > 0
        okp += st(prod); okv += st(v4)
        if nom and not isnan(nom):
            if not isnan(prod): dp.append(abs(prod["eff"] - nom["eff"]))
            if not isnan(v4): dv.append(abs(v4["eff"] - nom["eff"]))
        rows.append("   bin%-3d nominal %s | prod s1m0 %s | V4 s1m0 %s" % (b,
            "%.4f" % nom["eff"] if nom and not isnan(nom) else "  nan ",
            "%.4f (st %s/%s)" % (prod["eff"], prod["statusP"], prod["statusF"]) if not isnan(prod) else "   nan        ",
            "%.4f (st %s/%s)" % (v4["eff"], v4["statusP"], v4["statusF"]) if not isnan(v4) else "   nan"))
    med = lambda d: sorted(d)[len(d) // 2] if d else float("nan")
    print("== %s %s: %d bins | NaN prod %d -> V4 %d | acceptable status prod %d -> V4 %d" % (cfg, kind, len(bins), nanp, nanv, okp, okv))
    print("   |s1m0 - s0m0|: prod median %.4f max %.4f (%d bins) | V4 median %.4f max %.4f (%d bins)" % (med(dp), max(dp) if dp else float("nan"), len(dp), med(dv), max(dv) if dv else float("nan"), len(dv)))
    for r in rows: print(r)
