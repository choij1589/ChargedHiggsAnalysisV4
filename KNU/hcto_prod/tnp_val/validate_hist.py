#!/usr/bin/env python3
"""Fill the tnp_tamsa pass/fail histograms of every HcToWA config with the
backend selected by TNP_HIST_BACKEND (loop | rdf), on the validation samples
VAL/<kind>/<lepton>/{data,sim} (every data set -> data, every sim set -> sim).
Output: OUT/<module>/<config>/<hist_file .d>/job0.root. Python 3.9 compatible.
  validate_hist.py --kind tree|rntuple --out DIR"""
import argparse, importlib, os, sys
TNP = os.environ["TNP_BASE"]
sys.path.insert(0, TNP)
sys.path.insert(0, TNP + "/python")
os.chdir(TNP)
import histUtils

VAL = "/d0/scratch/choij/TnP/2024/validation"
ap = argparse.ArgumentParser()
ap.add_argument("--kind", required=True, choices=["tree", "rntuple"])
ap.add_argument("--out", required=True)
args = ap.parse_args()
print("backend:", os.getenv("TNP_HIST_BACKEND", "rdf"))
for mod, lep in [("config.HcToWA_Muon_2024", "muon"), ("config.HcToWA_Electron_2024", "electron")]:
    m = importlib.import_module(mod)
    for name in sorted(m.Configs):
        for hc in m.Configs[name].make_hist_configs():
            sample = "{}/{}/{}/{}".format(VAL, args.kind, lep, "sim" if hc[0].isSim else "data")
            path = "{}/{}/{}".format(args.out, mod.split(".")[1], name)
            for member in hc:
                member.sample = sample
                member.path = path
            print("==", name, hc[0].hist_file, len(hc), "configs")
            sys.stdout.flush()
            histUtils.makePassFailHistograms(hc, 1, 0)
print("VALIDATE_DONE")
