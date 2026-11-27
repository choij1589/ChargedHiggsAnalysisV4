#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
for c in NUM_HcToWATight_DEN_RecoElectrons_2024 NUM_wp90noiso_DEN_RecoElectrons_2024 NUM_cutBasedTight_DEN_RecoElectrons_2024; do python3 python/checkFitStatus.py results/HcToWA_Electron_2024/$c > /d0/scratch/choij/hcto_prod/tnp_refit/final_$c.txt 2>&1; done
