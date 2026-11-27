#!/bin/bash
# Electron altMC systematic (set 3): altsim histograms, set-3 fits, summary; then fit check and refits.
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
L=/d0/scratch/choij/hcto_prod/tnp_prod
run() {
  c=$1
  python3 tnp_tamsa.py config/HcToWA_Electron_2024.py $c --step hist --set 2 --njob 100,20 --log > $L/altmc_hist_$c.log 2>&1 || { echo "$c hist failed"; return 1; }
  python3 tnp_tamsa.py config/HcToWA_Electron_2024.py $c --step fit --set 3 --njob 100,20 --log > $L/altmc_fit_$c.log 2>&1 || { echo "$c fit failed"; return 1; }
  python3 tnp_tamsa.py config/HcToWA_Electron_2024.py $c --step sum > $L/altmc_sum_$c.log 2>&1; echo "$c rc=$? $(date)"
}
for c in NUM_HcToWATight_DEN_RecoElectrons_2024 NUM_wp90noiso_DEN_RecoElectrons_2024 NUM_cutBasedTight_DEN_RecoElectrons_2024; do run $c & done
wait
mkdir -p $L/check_altmc && rm -f $L/check_altmc/*.txt
cat > $L/check_altmc/check.sh <<'EOT'
#!/bin/bash
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
for c in NUM_HcToWATight_DEN_RecoElectrons_2024 NUM_wp90noiso_DEN_RecoElectrons_2024 NUM_cutBasedTight_DEN_RecoElectrons_2024; do
  python3 python/checkFitStatus.py results/HcToWA_Electron_2024/$c > /d0/scratch/choij/hcto_prod/tnp_prod/check_altmc/$c.txt 2>&1
done
EOT
chmod +x $L/check_altmc/check.sh; cd $L/check_altmc && env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnp_check ./check.sh
cd $L && python3 -u refit_flagged.py --check-dir $L/check_altmc --apply
echo "ALTMC_DONE $(date)"
