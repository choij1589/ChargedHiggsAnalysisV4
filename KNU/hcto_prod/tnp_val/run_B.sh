#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh && export TNP_HIST_BACKEND=rdf
rm -rf /d0/scratch/choij/TnP/2024/validation/out/B
( time python3 /d0/scratch/choij/hcto_prod/tnp_val/validate_hist.py --kind tree --out /d0/scratch/choij/TnP/2024/validation/out/B ) 2>&1
