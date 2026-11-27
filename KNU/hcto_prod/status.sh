#!/bin/bash
# status.sh: one-line status per DiLepton production DAG
for d in /d0/scratch/choij/SKNanoRunlog/2026_11_24_152208_DiLepton_RunDiMu_RunSyst /d0/scratch/choij/SKNanoRunlog/2026_11_24_152213_DiLepton_RunEMu_RunSyst $(ls -d /d0/scratch/choij/SKNanoRunlog/*_DiLepton_RunZEE_RunSyst 2>/dev/null); do
  o=$d/dags/dagfile.dag.dagman.out
  [ -f $o ] || { echo "$(basename $d): no dagman.out"; continue; }
  line=$(grep -A2 "Done     Pre   Queued    Post   Ready   Un-Ready   Failed" $o | tail -1)
  ex=$(grep -c "EXITING WITH STATUS" $o)
  echo "$(basename $d): $line exited=$ex"
done
condor_q choij -totals 2>/dev/null | grep "Total for choij"
