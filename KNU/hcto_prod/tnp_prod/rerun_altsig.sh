#!/bin/bash
# Rerun the electron alternative-signal fits (set 1) with the fixed-tail CB, then the summary.
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
L=/d0/scratch/choij/hcto_prod/tnp_prod
run() { python3 tnp_tamsa.py config/HcToWA_Electron_2024.py $1 --step fit --set 1 --njob 100,20 --log > $L/altsig_$1.log 2>&1 && \
        python3 tnp_tamsa.py config/HcToWA_Electron_2024.py $1 --step sum > $L/altsig_sum_$1.log 2>&1; echo "$1 rc=$? $(date)"; }
for c in NUM_HcToWATight_DEN_RecoElectrons_2024 NUM_wp90noiso_DEN_RecoElectrons_2024 NUM_cutBasedTight_DEN_RecoElectrons_2024; do run $c & done
wait; echo "ALTSIG_DONE $(date)"
