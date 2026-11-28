#!/bin/bash
# 2026-11-28: resubmission of the samples missing from the final TriLepton production (nodes failed 3x with exit 6:
# output/ dir removed by the /d0 cleaner; guard_outdirs.sh now keeps them). Same flags and output tag.
#   bash submit_final_missing.sh data "Skim_TriLep_Muon0:H Skim_TriLep_Muon1:H,I_v2"
#   bash submit_final_missing.sh mc   "Skim_TriLep_ttWtoLNu,Skim_TriLep_tZq,..."
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
cd /d0/scratch/choij/hcto_prod
TRI_FLAGS=Run1E2Mu,Run3Mu,SRTree,RunSyst,BTagEffHists,HcToWABTagEff
if [ "$1" = data ]; then
  for sp in $2; do
    SKNano.py -a TriLepton -i ${sp%%:*} -p ${sp#*:} -n -100 -e 2024 --userflags $TRI_FLAGS > final_missing_${sp%%:*}.log 2>&1; echo "${sp} RC=$?"
    sleep 5
  done
else
  SKNano.py -a TriLepton -i $2 -n -100 -e 2024 --userflags $TRI_FLAGS > final_missing_mc.log 2>&1; echo "MC RC=$?"
fi
