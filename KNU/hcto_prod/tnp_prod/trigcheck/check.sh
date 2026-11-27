#!/bin/bash
export MAMBA_ROOT_PREFIX=/d0/scratch/choij/micromamba_envs; eval "$(/d0/scratch/choij/micromamba_bin/micromamba shell hook -s bash)"; micromamba activate NanoV15
cd /d0/scratch/choij/tnp_tamsa; export TNP_BASE=$PWD
for c in NUM_Mu17Leg1_DEN_HcToWATight_2024 NUM_Mu8Leg2_DEN_HcToWATight_2024; do
  python3 python/checkFitStatus.py results/HcToWA_MuonTrig_2024/$c > results/HcToWA_MuonTrig_2024/$c/checkFitStatus.txt 2>&1; echo "$c rc=$?"
done
