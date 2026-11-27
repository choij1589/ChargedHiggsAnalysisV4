#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
python3 - <<'PY'
import sys, os
sys.path.insert(0, "python"); sys.path.insert(0, ".")
import checkFitStatus as cfs
import importlib
for c in ["NUM_cutBasedTight_DEN_RecoElectrons_2024", "NUM_wp90noiso_DEN_RecoElectrons_2024"]:
    rdir = "results/HcToWA_Electron_2024/" + c
    truth = cfs.make_truth(rdir)
    mod = importlib.import_module("config.HcToWA_Electron_2024"); cfg = mod.Configs[c]
    with open("/d0/scratch/choij/hcto_prod/tnp_refit/truth_%s.txt" % c, "w") as out:
        for ib, b in enumerate(cfg.bins):
            v = b["vars"]; t = truth("s0m0", ib, rdir)
            if t is None: continue
            out.write("%g %g %g %g %.6f %.6f\n" % (v["probe_sc_eta"]["min"], v["probe_sc_eta"]["max"], v["probe_pt_cor"]["min"], v["probe_pt_cor"]["max"], t[0], t[1]))
    print(c, "done")
PY
