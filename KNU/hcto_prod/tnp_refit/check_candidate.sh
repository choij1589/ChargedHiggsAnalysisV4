#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
for d in /d0/scratch/choij/hcto_prod/tnp_refit/candidate/*/*; do python3 python/checkFitStatus.py $d > /d0/scratch/choij/hcto_prod/tnp_refit/candidate_$(basename $d).txt 2>&1; done
