#!/bin/bash
export MAMBA_ROOT_PREFIX=/d0/scratch/choij/micromamba_envs; eval "$(/d0/scratch/choij/micromamba_bin/micromamba shell hook -s bash)"; micromamba activate /d0/scratch/choij/micromamba_envs/envs/NanoV15
echo "== A (CMSSW loop, TTree) vs B (NanoV15 RDF, TTree)"; python /d0/scratch/choij/hcto_prod/tnp_val/compare_hists.py /d0/scratch/choij/TnP/2024/validation/out/A /d0/scratch/choij/TnP/2024/validation/out/B
echo "== B (RDF, TTree) vs C (RDF, RNTuple)"; python /d0/scratch/choij/hcto_prod/tnp_val/compare_hists.py /d0/scratch/choij/TnP/2024/validation/out/B /d0/scratch/choij/TnP/2024/validation/out/C
