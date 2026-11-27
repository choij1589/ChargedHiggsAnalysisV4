"""Combination rules on the EGM-model test rows: SF uncertainty with (a) EGM master rule
(mean of 4 data effs, spread/2, + altMC + stat), (b) tnp_tamsa rule (nominal; per set the
SF deviation of the member, in quadrature, + stat), (c) = (b) symmetrized in |eta| (max of
the two cells), compared with EGM's published sfup - sf."""
import sys, math, statistics as st
sys.path.insert(0, "/d0/scratch/choij/tnp_tamsa/python")
import checkFitStatus as cfs
import correctionlib
ele = correctionlib.CorrectionSet.from_file("/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/latest/electron.json.gz")["Electron-ID-SF"]
P = "/d0/scratch/choij/tnp_tamsa/results/HcToWA_Electron_2024"; T = "/d0/scratch/choij/hcto_prod/tnp_fittest/out/EGM"
ETA = [(-2.5, -2.0), (-2.0, -1.566), (-1.4442, -0.8), (-0.8, 0.0), (0.0, 0.8), (0.8, 1.4442), (1.566, 2.0), (2.0, 2.5)]
rows = {"10-20": (range(0, 8), 15.0), "35-50": (range(16, 24), 42.5), "100-200": (range(40, 48), 150.0)}
for cfg, wp in [("NUM_wp90noiso_DEN_RecoElectrons_2024", "wp90noiso"), ("NUM_cutBasedTight_DEN_RecoElectrons_2024", "Tight")]:
    print("== %s   SF uncertainty per eta_SC cell: (a) EGM master rule | (b) full deviations | (c) (b) symmetrized in |eta| | EGM published" % cfg)
    for label, (bins, y) in rows.items():
        a, b, dv, ev = [], [], [], []
        for k, ib in enumerate(bins):
            g = lambda root, kind, m: cfs.read_bin("%s/%s/fits_%s.d/%s/bin%d.root" % (root, cfg, kind, m, ib), m)
            d = {m: g(P, "data", m) for m in ("s0m0", "s2m0", "s3m0")}; s = {m: g(P, "sim", m) for m in ("s0m0", "s2m0", "s3m0")}
            d["s1m0"], d["s4m0"] = g(T, "data", "s1m0"), g(T, "data", "s4m0"); s["s1m0"], s["s4m0"] = g(T, "sim", "s1m0"), g(T, "sim", "s4m0")
            sf = {m: d[m]["eff"] / s[m]["eff"] for m in d}
            stat = sf["s0m0"] * math.hypot(d["s0m0"]["eff_err"] / d["s0m0"]["eff"], s["s0m0"]["eff_err"] / s["s0m0"]["eff"])
            effs = [d[m]["eff"] for m in ("s0m0", "s1m0", "s2m0", "s4m0")]; mean = sum(effs) / 4
            fit = math.sqrt(sum((e - mean) ** 2 for e in effs) / 3) / 2
            amc = s["s3m0"]["eff"] - s["s0m0"]["eff"]; amc = 0. if abs(amc) < s["s0m0"]["eff_err"] else amc
            a.append(math.sqrt(fit ** 2 + amc ** 2 + d["s0m0"]["eff_err"] ** 2 + s["s0m0"]["eff_err"] ** 2) / s["s0m0"]["eff"])
            b.append(math.sqrt(stat ** 2 + sum((sf[m] - sf["s0m0"]) ** 2 for m in ("s1m0", "s2m0", "s3m0", "s4m0"))))
            dd_ = [(d[m]["eff"] - d["s0m0"]["eff"]) / s["s0m0"]["eff"] for m in ("s1m0", "s2m0")]
            dv.append(math.sqrt(stat ** 2 + sum(x * x for x in dd_)))
            ev.append(math.sqrt(stat ** 2 + sum(x * x for x in dd_) + ((d["s4m0"]["eff"] - d["s0m0"]["eff"]) / s["s0m0"]["eff"]) ** 2))
        c = [max(b[k], b[len(b) - 1 - k]) for k in range(len(b))]
        dd = [max(dv[k], dv[len(dv) - 1 - k]) for k in range(len(dv))]
        ee = [max(ev[k], ev[len(ev) - 1 - k]) for k in range(len(ev))]
        egm = [ele.evaluate("2024Prompt", "sfup", wp, 0.5 * (e[0] + e[1]), y) - ele.evaluate("2024Prompt", "sf", wp, 0.5 * (e[0] + e[1]), y) for e in ETA]
        print("   pT %-8s (a) %s\n                (c) %s\n                (d) %s\n                (e) %s\n              EGM %s" % (label, " ".join("%.4f" % v for v in a), " ".join("%.4f" % v for v in c), " ".join("%.4f" % v for v in dd), " ".join("%.4f" % v for v in ee), " ".join("%.4f" % v for v in egm)))
