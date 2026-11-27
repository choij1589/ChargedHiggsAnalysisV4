"""EGM-model test: new altSig (s1m0) and altSigBkg (s4m0) data fits vs production nominal/altBkg/altMC."""
import sys, os, math, statistics as st
sys.path.insert(0, "/d0/scratch/choij/tnp_tamsa/python")
import checkFitStatus as cfs
P = "/d0/scratch/choij/tnp_tamsa/results/HcToWA_Electron_2024"; T = "/d0/scratch/choij/hcto_prod/tnp_fittest/out/EGM"
rows = {"10-20": range(0, 8), "35-50": range(16, 24), "100-200": range(40, 48)}
for cfg in ["NUM_wp90noiso_DEN_RecoElectrons_2024", "NUM_cutBasedTight_DEN_RecoElectrons_2024"]:
    print("== " + cfg)
    for label, bins in rows.items():
        stats, out = {"nan": 0, "bad": 0, "n": 0}, []
        for b in bins:
            g = lambda root, kind, m: cfs.read_bin("%s/%s/fits_%s.d/%s/bin%d.root" % (root, cfg, kind, m, b), m)
            nom, bkg = g(P, "data", "s0m0"), g(P, "data", "s2m0")
            sig, sb = g(T, "data", "s1m0"), g(T, "data", "s4m0")
            mc, mca = g(P, "sim", "s0m0"), g(P, "sim", "s3m0")
            for r in (sig, sb):
                stats["n"] += 1
                if r is None or r["eff"] != r["eff"]: stats["nan"] += 1
                elif not (r["statusP"] in (0, 1, 3) and r["statusF"] in (0, 1, 3) and r["covQualP"] > 0 and r["covQualF"] > 0): stats["bad"] += 1
            if None in (nom, bkg, sig, sb, mc) or any(r["eff"] != r["eff"] for r in (nom, bkg, sig, sb)): continue
            effs = [bkg["eff"], sig["eff"], sb["eff"], nom["eff"]]; mean = sum(effs) / 4
            fitsyst = math.sqrt(sum((e - mean) ** 2 for e in effs) / 3)
            altmc = mca["eff"] - mc["eff"] if mca else 0.
            if abs(altmc) < mc["eff_err"]: altmc = 0.
            tot = math.sqrt(fitsyst ** 2 / 4 + altmc ** 2 + nom["eff_err"] ** 2 + mc["eff_err"] ** 2)
            out.append((abs(sig["eff"] - nom["eff"]), abs(sb["eff"] - nom["eff"]), abs(bkg["eff"] - nom["eff"]), fitsyst / 2, tot / mc["eff"], mean / mc["eff"] - nom["eff"] / mc["eff"]))
        med = lambda i: st.median(o[i] for o in out) if out else float("nan")
        print("   pT %-8s fits %d, NaN %d, bad status %d | data |altSig-nom| %.4f |altSigBkg-nom| %.4f |altBkg-nom| %.4f | EGM fit-model unc. (spread/2) %.4f | EGM-rule SF total unc. %.4f | SF shift (mean - nominal) %+.4f" % (
            label, stats["n"], stats["nan"], stats["bad"], med(0), med(1), med(2), med(3), med(4), med(5)))
