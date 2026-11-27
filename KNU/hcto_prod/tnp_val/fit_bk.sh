#!/bin/bash
# one-bin refit of the muon test config (data and sim, s0m0, bin 0) with the legacy and the cpu RooFit backend
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
V=/d0/scratch/choij/TnP/2024/validation; C=TEST_NUM_HcToWATight_DEN_TrackerMuons_2024
for b in legacy cpu; do
  export TNP_ROOFIT_BACKEND=$b TNP_VAL_OUT=$V/fit_bk/$b
  for k in --data --sim; do python3 tnp_tamsa.py config/HcToWA_val_fit.py $C --step fit --set 0 --member 0 $k --bin 0 --no-condor > /dev/null 2>&1 || echo "fit $b $k failed"; done
done
python3 - <<'PY'
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
V = "/d0/scratch/choij/TnP/2024/validation"; C = "TEST_NUM_HcToWATight_DEN_TrackerMuons_2024"
def eff(path, kind):
    f = ROOT.TFile.Open("%s/%s/fits_%s.d/s0m0/bin0.root" % (path, C, kind))
    c = [k.ReadObj() for k in f.Get("s0m0").GetListOfKeys() if k.GetName().endswith("_Canv")][0]
    t = c.GetPrimitive("efficiency") or c.GetPad(1).GetPrimitive("efficiency")
    return t.GetLine(0).GetTitle()
for kind in ("data", "sim"):
    print(kind, "| CMSSW 6.26:", eff(V + "/fit_cmssw", kind), "| 6.40 default:", eff(V + "/fit_nanov15", kind),
          "| 6.40 legacy:", eff(V + "/fit_bk/legacy", kind), "| 6.40 cpu:", eff(V + "/fit_bk/cpu", kind))
PY
