#!/bin/bash
# ClosFakeRate test (2026-11-27): Skim_TriLep TTLL/TTLJ powheg, job 1 trimmed to 4 files, on condor.
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
mkdir -p /d0/scratch/choij/hcto_prod/closfr_test && cd /d0/scratch/choij/hcto_prod/closfr_test
SKNano.py -a ClosFakeRate -i Skim_TriLep_TTLL_powheg,Skim_TriLep_TTLJ_powheg -n -100 -e 2024 --userflags Run1E2Mu,Run3Mu,ClosTest --no_exec > gen.log 2>&1; echo gen_rc=$?
i=0; pids=""
for dir in $(ls -d /d0/scratch/choij/SKNanoRunlog/*_ClosFakeRate_Run1E2Mu_Run3Mu_ClosTest/2024/*); do
  i=$((i+1)); python3 ../fr_test/trim.py $dir 4 0
  printf '#!/bin/bash\ncd %s && bash run.sh 1\n' $dir > run_$i.sh
  SHELL=/bin/bash condor_run -a jobbatchname=closfrtest -a x509userproxy=$(voms-proxy-info -path) bash $PWD/run_$i.sh > run_$i.log 2>&1 &
  pids="$pids $!"
done
for p in $pids; do wait $p; echo "job rc=$?"; done
echo CLOSFR_TEST_DONE
