#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
export TNP_FITTEST_OUT=/d0/scratch/choij/TnP/2024/validation/rawpt
python3 - <<'PY'
import sys, ctypes
sys.path.insert(0, "."); sys.path.insert(0, "python")
import ROOT, importlib
m = importlib.import_module("config.HcToWA_rawpt_test")
for name, cfg in m.Configs.items():
    c = cfg.clone(isSim=True)
    f = ROOT.TFile.Open("/d0/scratch/choij/TnP/2024/validation/rawpt/%s/%s" % (name, c.hist_file))
    with open("/d0/scratch/choij/hcto_prod/tnp_refit/rawpt_truth_%s.txt" % name, "w") as out:
        for ib, b in enumerate(c.bins):
            v = []
            for isPass in (True, False):
                h = f.Get(c.get_histname(ib, isPass, genmatching=True)); e = ctypes.c_double(0.)
                lo, hi = h.FindBin(c.fit_range[0] + 1e-6), h.FindBin(c.fit_range[1] - 1e-6)
                v.append((h.IntegralAndError(lo, hi, e), e.value))
            (p, ep), (q, eq) = v
            vv = b["vars"]
            out.write("%g %g %g %g %.6f %.6f\n" % (vv["probe_sc_eta"]["min"], vv["probe_sc_eta"]["max"], vv["probe_pt"]["min"], vv["probe_pt"]["max"], p / (p + q), ((ep * q) ** 2 + (eq * p) ** 2) ** 0.5 / (p + q) ** 2))
    print(name, "done")
PY
