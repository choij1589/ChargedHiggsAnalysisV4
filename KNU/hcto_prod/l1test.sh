#!/bin/bash
# rebuild, generate DIMU DiLepton tests (TTLL, DY->mumu; 4 files of job 1 each), run them on condor:
# closure subsets IsoMu24 / L1Seed (LOG_Trigger 2026-11-26)
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
./scripts/build.sh > /d0/scratch/choij/hcto_prod/build_l1test.log 2>&1; echo build_rc=$?
grep -ci "error" /d0/scratch/choij/hcto_prod/build_l1test.log
mkdir -p /d0/scratch/choij/hcto_prod/l1test && cd /d0/scratch/choij/hcto_prod/l1test
SKNano.py -a DiLepton -i TTLL_powheg,DYto2Mu_2J_MLL50toInf -n -100 -e 2024 --userflags RunDiMu,L1Test --no_exec > gen.log 2>&1; echo gen_rc=$?
i=0; pids=""
for dir in $(ls -d /d0/scratch/choij/SKNanoRunlog/*_DiLepton_RunDiMu_L1Test/2024/*); do
  i=$((i+1)); python3 ../fr_test/trim.py $dir 4 0
  printf '#!/bin/bash\ncd %s && bash run.sh 1\n' $dir > run_$i.sh
  SHELL=/bin/bash condor_run -a jobbatchname=l1test -a x509userproxy=$(voms-proxy-info -path) bash $PWD/run_$i.sh > run_$i.log 2>&1 &
  pids="$pids $!"
done
for p in $pids; do wait $p; echo "job rc=$?"; done
echo L1TEST_DONE
