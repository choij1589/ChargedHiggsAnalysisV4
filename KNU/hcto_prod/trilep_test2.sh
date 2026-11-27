#!/bin/bash
# TriLepton test of the new histograms (ZCand, nonZLep, jets_1) (PLAN_ConvSF, 2026-11-27): Skim_TriLep data and MC, job 1 trimmed to 3 files, on condor.
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
mkdir -p /d0/scratch/choij/hcto_prod/trilep_test2 && cd /d0/scratch/choij/hcto_prod/trilep_test2
MC=Skim_TriLep_WZto3LNu,Skim_TriLep_DYto2Mu_2J_MLL50toInf
SKNano.py -a TriLepton -i $MC -n -100 -e 2024 --userflags Run1E2Mu,Run3Mu,TriTestV2 --no_exec > gen_mc.log 2>&1; echo gen_mc_rc=$?
SKNano.py -a TriLepton -i Skim_TriLep_MuonEG -n -100 -e 2024 --userflags Run1E2Mu,Run3Mu,TriTestV2 --no_exec > gen_data.log 2>&1; echo gen_data_rc=$?
i=0; pids=""
for dir in $(ls -d /d0/scratch/choij/SKNanoRunlog/*_TriLepton_Run1E2Mu_Run3Mu_TriTestV2/2024/*); do
  i=$((i+1)); python3 ../fr_test/trim.py $dir 3 0
  printf '#!/bin/bash\ncd %s && bash run.sh 1\n' $dir > run_$i.sh
  SHELL=/bin/bash condor_run -a jobbatchname=trileptest -a x509userproxy=$(voms-proxy-info -path) bash $PWD/run_$i.sh > run_$i.log 2>&1 &
  pids="$pids $!"
done
for p in $pids; do wait $p; echo "job rc=$?"; done
echo TRILEP_TEST_DONE $(date)
