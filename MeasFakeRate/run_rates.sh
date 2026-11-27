#!/bin/bash
# Fake-rate post-processing chain (PLAN_BkgEst steps 2-3), local, NanoV15 environment.
#   bash MeasFakeRate/run_rates.sh
# 1. sync the MeasFakeRate outputs from /pnfs; 2. gate (Z-window scales, W region, objects, nPV);
# 3. prompt-scale fits (MT; free, Z-fixed, Z-bounded +-30% = the adopted scale, user 2026-11-27);
# 4. rates (fit scale = default; Z-window scale for comparison); 5. plots (W region, rates); 6. JSON.
set -e
cd "$(dirname "$0")/.."
PY=~/micromamba/envs/NanoV15/bin/python
for d in MeasMuFR MeasElFR MeasMuFR_MeasElFR; do
  mkdir -p SKNanoOutput/MeasFakeRate/$d/2024
  rsync -a knu1:/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput/MeasFakeRate/$d/2024/ SKNanoOutput/MeasFakeRate/$d/2024/
done
for fl in mu el; do $PY MeasFakeRate/python/measFakeRate.py --flavour $fl --step gate > /dev/null; done
for m in free zfixed zbound; do $PY MeasFakeRate/python/fitPromptScale.py --var MT --mode $m > /dev/null 2>&1; done
for fl in mu el; do
  $PY MeasFakeRate/python/measFakeRate.py --flavour $fl --step rates --scale fit > /dev/null
  $PY MeasFakeRate/python/measFakeRate.py --flavour $fl --step rates --scale zwindow > /dev/null
done
$PY MeasFakeRate/python/plotWRegion.py > /dev/null 2>&1
$PY MeasFakeRate/python/plotFakeRate.py > /dev/null 2>&1
$PY MeasFakeRate/python/makeFakeRateJson.py
# overview montages (ImageMagick)
P=MeasFakeRate/plots/AN/2024
for id in tight loose; do
  (cd $P/WRegion && montage Mu8_${id}_MT.png Mu17_${id}_MT.png Ele8_${id}_MT.png Ele12_${id}_MT.png Ele23_${id}_MT.png \
     Mu8_${id}_MET.png Mu17_${id}_MET.png Ele8_${id}_MET.png Ele12_${id}_MET.png Ele23_${id}_MET.png -tile 5x2 -geometry 520x+4+4 overview_${id}.png)
done
for m in zfixed zbound; do
  (cd $P/PromptFit && montage $m/Mu8_tight_MT.png $m/Mu17_tight_MT.png $m/Ele8_tight_MT.png $m/Ele12_tight_MT.png $m/Ele23_tight_MT.png \
     $m/Mu8_loose_MT.png $m/Mu17_loose_MT.png $m/Ele8_loose_MT.png $m/Ele12_loose_MT.png $m/Ele23_loose_MT.png -tile 5x2 -geometry 520x+4+4 overview_MT_$m.png)
done
(cd $P/FakeRate && montage rates_mu_eta0.png rates_mu_eta1.png rates_mu_eta2.png rates_el_eta0.png rates_el_eta1.png rates_el_eta2.png \
   -tile 3x2 -geometry 560x+4+4 overview_rates.png)
echo "run_rates.sh done $(date)"
