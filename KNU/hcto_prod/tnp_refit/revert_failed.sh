#!/bin/bash
# Re-check production; restore the original fit for every replaced bin that is flagged again; rebuild summaries.
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
W=/d0/scratch/choij/hcto_prod/tnp_refit
for d in results/HcToWA_Muon_2024/* results/HcToWA_Electron_2024/*; do
  c=$(basename $d); s=$(basename $(dirname $d))
  python3 python/checkFitStatus.py $d > $W/final_$c.txt 2>&1
  n=0
  for item in $(sed -n "/bins to refit/,\$p" $W/final_$c.txt | grep -E "^  bin[0-9]+/s[0-9]+m[0-9]+$"); do :; done
  for kind in data sim; do
    K=$(echo $kind | tr a-z A-Z)
    for item in $(sed -n "/^$K bins to refit/,/^\$/p" $W/final_$c.txt | grep -oE "bin[0-9]+/s[0-9]+m[0-9]+"); do
      b=${item%/*}; m=${item#*/}
      if [ -f $d/fits_$kind.d.orig/$m/$b.root ]; then
        cp $d/fits_$kind.d.orig/$m/$b.root $d/fits_$kind.d/$m/$b.root; rm $d/fits_$kind.d.orig/$m/$b.root; n=$((n+1)); echo "$c: reverted $kind $item"
      fi
    done
  done
  if [ $n -gt 0 ]; then python3 tnp_tamsa.py config/$s.py $c --step sum > $W/sum_revert_$c.log 2>&1; echo "$c: sum rc=$?"; python3 python/checkFitStatus.py $d > $W/final_$c.txt 2>&1; fi
done
