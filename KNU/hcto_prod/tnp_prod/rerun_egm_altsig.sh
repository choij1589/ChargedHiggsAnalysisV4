#!/bin/bash
# Electron altSig (set 1) with the EGM model: fits, summary; then fit check and refits.
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
L=/d0/scratch/choij/hcto_prod/tnp_prod
run() { c=$1
  python3 tnp_tamsa.py config/HcToWA_Electron_2024.py $c --step fit --set 1 --njob 100,20 --log > $L/egmsig_fit_$c.log 2>&1 || { echo "$c fit failed"; return 1; }
  python3 tnp_tamsa.py config/HcToWA_Electron_2024.py $c --step sum > $L/egmsig_sum_$c.log 2>&1; echo "$c rc=$? $(date)"; }
for c in NUM_HcToWATight_DEN_RecoElectrons_2024 NUM_wp90noiso_DEN_RecoElectrons_2024 NUM_cutBasedTight_DEN_RecoElectrons_2024; do run $c & done
wait
mkdir -p $L/check_egm && rm -f $L/check_egm/*.txt
sed "s#check_altmc#check_egm#g" $L/check_altmc/check.sh > $L/check_egm/check.sh; chmod +x $L/check_egm/check.sh
cd $L/check_egm && env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnp_check ./check.sh
cd $L && python3 -u refit_flagged.py --check-dir $L/check_egm --apply
cd $L/check_egm && sed -i "s#/check_egm/#/check_egm/final_#" check.sh && env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnp_check ./check.sh
echo "EGMSIG_DONE $(date)"
