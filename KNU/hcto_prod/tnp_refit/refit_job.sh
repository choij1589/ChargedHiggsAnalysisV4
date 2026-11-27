#!/bin/bash
# refit_job.sh OUTDIR CONFIG SET MEMBER KIND BINS
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
export TNP_FITTEST_OUT=$1 TNP_ROOFIT_OFFSET=initial
python3 tnp_tamsa.py config/HcToWA_fittest.py $2 --step fit --set $3 --member $4 --$5 --bin $6 --no-condor > /dev/null 2>&1
echo "rc=$?"
