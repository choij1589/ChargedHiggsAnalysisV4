#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
python3 /d0/scratch/choij/hcto_prod/tnp_fittest/compare_v4.py
