#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
python3 - <<'PY'
import sys, glob, os
sys.path.insert(0, "python"); import checkFitStatus as cfs
R = "results/HcToWA_Muon_2024/NUM_TightID_DEN_TrackerMuons_2024/fits_data.d"
for d in sorted(glob.glob(R + "/s*m*")):
    m = os.path.basename(d); r = cfs.read_bin(d + "/bin112.root", m)
    nb = {n: "%.4g+-%.3g" % (v, e) for n, v, e, lo, hi in r["parsF"] + r["parsP"] if n.startswith("n")}
    print("%s eff %.4f+-%.4f st %s/%s cq %s/%s count %.4f %s" % (m, r["eff"], r["eff_err"], r["statusP"], r["statusF"], r["covQualP"], r["covQualF"], r.get("count_eff", -1), nb))
o = cfs.read_bin(R + ".orig/s3m0/bin112.root", "s3m0")
print("orig s3m0 eff %.4f st %s/%s %s" % (o["eff"], o["statusP"], o["statusF"], {n: "%.4g+-%.3g" % (v, e) for n, v, e, lo, hi in o["parsF"] + o["parsP"] if n.startswith("n")}))
PY
