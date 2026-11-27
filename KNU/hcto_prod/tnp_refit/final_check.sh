#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
python3 /d0/scratch/choij/hcto_prod/tnp_refit/shifts.py
for d in results/HcToWA_Muon_2024/* results/HcToWA_Electron_2024/*; do python3 python/checkFitStatus.py $d > /d0/scratch/choij/hcto_prod/tnp_refit/final_$(basename $d).txt 2>&1; done
