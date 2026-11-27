#!/bin/bash
# orchestration only: tnp_tamsa submits the hist jobs to condor
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
export TNP_FITTEST_OUT=/d0/scratch/choij/TnP/2024/validation/rawpt
rm -rf $TNP_FITTEST_OUT
for c in NUM_cutBasedTight_DEN_RecoElectrons_2024 NUM_wp90noiso_DEN_RecoElectrons_2024; do
  python3 tnp_tamsa.py config/HcToWA_rawpt_test.py $c --step hist --njob 50,1 > /d0/scratch/choij/hcto_prod/tnp_refit/rawpt_$c.log 2>&1; echo "$c rc=$?"
done
echo RAWPT_DONE
