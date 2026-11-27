#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=cmssw && source setup.sh && export TNP_HIST_BACKEND=loop
rm -rf /d0/scratch/choij/TnP/2024/validation/out/A
( time python3 /d0/scratch/choij/hcto_prod/tnp_val/validate_hist.py --kind tree --out /d0/scratch/choij/TnP/2024/validation/out/A ) 2>&1
