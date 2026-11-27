"""Compare refits of the fit-tuning variants with the production fits, bin by bin:
pass/fail status, covQual, efficiency (NaN counted), |eff - production|."""
import sys, os
sys.path.insert(0, "/d0/scratch/choij/tnp_tamsa/python")
import checkFitStatus as cfs
W = "/d0/scratch/choij/hcto_prod/tnp_fittest"
P = "/d0/scratch/choij/tnp_tamsa/results"
env = dict(l.strip().split("=", 1) for l in open(W + "/bins.env") if "=" in l)
cases = [("muon data s0m0", "HcToWA_Muon_2024/NUM_HcToWATight_DEN_TrackerMuons_2024", "data", "s0m0", env["MU_DATA"], ["V0", "V1"]),
         ("muon sim s0m0", "HcToWA_Muon_2024/NUM_HcToWATight_DEN_TrackerMuons_2024", "sim", "s0m0", env["MU_SIM"], ["V0", "V1"]),
         ("electron data s1m0", "HcToWA_Electron_2024/NUM_wp90noiso_DEN_RecoElectrons_2024", "data", "s1m0", env["EL_DATA"], ["V0", "V1", "V2", "V3"]),
         ("electron sim s1m0", "HcToWA_Electron_2024/NUM_wp90noiso_DEN_RecoElectrons_2024", "sim", "s1m0", env["EL_SIM"], ["V0", "V1", "V2", "V3"])]
def good(r):
    return bool(r) and r.get("statusP") == 0 and r.get("statusF") == 0 and r.get("covQualP") == 3 and r.get("covQualF") == 3
for title, rel, kind, mem, bins, variants in cases:
    bins = [int(b) for b in bins.split(",")]
    prod = {b: cfs.read_bin("%s/%s/fits_%s.d/%s/bin%d.root" % (P, rel, kind, mem, b), mem) for b in bins}
    print("== %s (%d bins)" % (title, len(bins)))
    def summary(tag, res):
        ok = sum(good(res[b]) for b in bins); nan = sum(1 for b in bins if res[b] is None or res[b]["eff"] != res[b]["eff"])
        return "%-6s status 0 & covQual 3: %2d/%d   NaN/missing: %2d" % (tag, ok, len(bins), nan)
    print("   " + summary("prod", prod))
    for v in variants:
        res = {b: cfs.read_bin("%s/out/%s/%s/fits_%s.d/%s/bin%d.root" % (W, v, os.path.basename(rel), kind, mem, b), mem) for b in bins}
        d = [abs(res[b]["eff"] - prod[b]["eff"]) for b in bins if res[b] and prod[b] and res[b]["eff"] == res[b]["eff"] and prod[b]["eff"] == prod[b]["eff"]]
        pulls = [abs(res[b]["eff"] - prod[b]["eff"]) / prod[b]["eff_err"] for b in bins if res[b] and prod[b] and res[b]["eff"] == res[b]["eff"] and prod[b]["eff"] == prod[b]["eff"] and prod[b]["eff_err"] > 0]
        print("   " + summary(v, res) + "   |eff - prod|: max %.2g, median %.2g (max %.2f sigma)" % (max(d) if d else -1, sorted(d)[len(d) // 2] if d else -1, max(pulls) if pulls else -1))
# bins that moved by more than 0.005 between production and V1
print("== bins with |V1 - prod| > 0.005")
for title, rel, kind, mem, bins, variants in cases:
    for b in [int(x) for x in bins.split(",")]:
        p = cfs.read_bin("%s/%s/fits_%s.d/%s/bin%d.root" % (P, rel, kind, mem, b), mem)
        r = cfs.read_bin("%s/out/V1/%s/fits_%s.d/%s/bin%d.root" % (W, os.path.basename(rel), kind, mem, b), mem)
        if p and r and p["eff"] == p["eff"] and r["eff"] == r["eff"] and abs(p["eff"] - r["eff"]) > 0.005:
            print("   %s bin%d: prod %.4f+-%.4f (st %s/%s cq %s/%s)  V1 %.4f+-%.4f (st %s/%s cq %s/%s)  count %.4f" % (title, b, p["eff"], p["eff_err"], p["statusP"], p["statusF"], p["covQualP"], p["covQualF"], r["eff"], r["eff_err"], r["statusP"], r["statusF"], r["covQualP"], r["covQualF"], p.get("count_eff", -1)))
            for side in "PF":
                pp = {n: (v, e) for n, v, e, lo, hi in p["pars" + side] if n.startswith("n")}; rr = {n: (v, e) for n, v, e, lo, hi in r["pars" + side] if n.startswith("n")}
                print("      %s prod %s | V1 %s" % (side, " ".join("%s=%.4g+-%.3g" % (n, *pp[n]) for n in sorted(pp)), " ".join("%s=%.4g+-%.3g" % (n, *rr[n]) for n in sorted(rr))))
