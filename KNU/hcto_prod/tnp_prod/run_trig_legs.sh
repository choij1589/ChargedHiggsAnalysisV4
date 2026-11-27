#!/bin/bash
# Dimuon-trigger legs (PLAN_Trigger step 1): tnp_tamsa in NanoV15; hist and fit jobs on condor.
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
L=/d0/scratch/choij/hcto_prod/tnp_prod
run() { python3 tnp_tamsa.py config/HcToWA_MuonTrig_2024.py $1 --step hist,fit,sum --njob 100,20 --log > $L/$1.log 2>&1; echo "$1 rc=$? $(date)"; }
run NUM_Mu17Leg1_DEN_HcToWATight_2024 &
run NUM_Mu8Leg2_DEN_HcToWATight_2024 &
wait; echo "TRIGLEGS_DONE $(date)"
