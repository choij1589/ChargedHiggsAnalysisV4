#!/bin/bash
# tnp_tamsa orchestration only (hist and fit jobs on condor; sum is light)
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
[ nanov15 = cmssw ] && export TNP_HIST_BACKEND=loop
export TNP_VAL_OUT=/d0/scratch/choij/TnP/2024/validation/fit_nanov15
rm -rf $TNP_VAL_OUT
for c in TEST_NUM_HcToWATight_DEN_TrackerMuons_2024 TEST_NUM_HcToWATight_DEN_RecoElectrons_2024 TEST_GAP_NUM_HcToWATight_DEN_RecoElectrons_2024; do
  python3 tnp_tamsa.py config/HcToWA_val_fit.py $c --step hist,fit,sum --njob 2,4 --nmax 20 > /d0/scratch/choij/hcto_prod/tnp_val/fit_nanov15_$c.log 2>&1
  echo "$c rc=$?"
done
echo "FIT_DONE nanov15 $(date)"
