#!/bin/bash
# fit_job.sh VARIANT SETTINGS CONFIG SET MEMBER KIND BINS
V=$1; S=$2; C=$3; SET=$4; MEM=$5; K=$6; B=$7
W=/d0/scratch/choij/hcto_prod/tnp_fittest
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
export TNP_FITTEST_OUT=$W/out/$V
case $V in V1|V3) export TNP_ROOFIT_OFFSET=initial ;; esac
case $V in V2|V3) export TNP_FITTEST_ALPHA12=1 ;; esac
case $V in V4) export TNP_FITTEST_CBFIX=1 ;; esac
case $V in EGM) : ;; esac
python3 tnp_tamsa.py config/HcToWA_fittest.py $C --step fit --set $SET --member $MEM --$K --bin $B --no-condor > /dev/null 2>&1
echo "rc=$?"
