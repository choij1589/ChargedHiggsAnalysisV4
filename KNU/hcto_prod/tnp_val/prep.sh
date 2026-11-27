#!/bin/bash
export MAMBA_ROOT_PREFIX=/d0/scratch/choij/micromamba_envs; eval "$(/d0/scratch/choij/micromamba_bin/micromamba shell hook -s bash)"; micromamba activate /d0/scratch/choij/micromamba_envs/envs/NanoV15
C=/d0/scratch/choij/TnP/scripts/rntuple_to_ttree.py
for l in muon electron; do for k in data sim; do
  for f in /d0/scratch/choij/TnP/2024/validation/rntuple/$l/$k/*.root; do python $C --lepton $l --force --out /d0/scratch/choij/TnP/2024/validation/tree/$l/$k/$(basename $f) $f || exit 1; done
done; done
