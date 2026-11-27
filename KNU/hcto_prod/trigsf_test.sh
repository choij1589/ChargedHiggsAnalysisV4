#!/bin/bash
# rebuild, generate one-file DiLepton tests (TTLL, DY->mumu), run them on condor
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
./scripts/build.sh > /d0/scratch/choij/hcto_prod/build_trigsf2.log 2>&1; echo build_rc=$?
grep -ci "warning:" /d0/scratch/choij/hcto_prod/build_trigsf2.log
mkdir -p /d0/scratch/choij/hcto_prod/trigsf_test && cd /d0/scratch/choij/hcto_prod/trigsf_test
SKNano.py -a DiLepton -i TTLL_powheg,DYto2Mu_2J_MLL50toInf -n -100 -e 2024 --userflags RunDiMu,RunEMu,RunSyst,TrigSFTest --no_exec > gen.log 2>&1; echo gen_rc=$?
i=0; pids=""
for dir in $(ls -d /d0/scratch/choij/SKNanoRunlog/*TrigSFTest/2024/*); do
  i=$((i+1)); python3 ../fr_test/trim.py $dir 1 0
  printf '#!/bin/bash\ncd %s && bash run.sh 1\n' $dir > run_$i.sh
  SHELL=/bin/bash condor_run -a jobbatchname=trigsf_test -a x509userproxy=$(voms-proxy-info -path) bash $PWD/run_$i.sh > run_$i.log 2>&1 &
  pids="$pids $!"
done
for p in $pids; do wait $p; echo "job rc=$?"; done
echo TRIGSF_TEST_DONE
