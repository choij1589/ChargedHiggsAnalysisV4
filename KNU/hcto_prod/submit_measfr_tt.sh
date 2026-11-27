#!/bin/bash
# 2026-11-27: MeasFakeRate tt (TTLL, TTLJ powheg) without the top pT weight (user: no top pT reweighting in the
# search analysis; MeasFakeRate.cc rebuilt, build_notoppt.log). The old tt outputs in MeasMuFR_MeasElFR were removed
# (user permission); the other 20 prompt-MC samples do not change (TopPtWeight() = 1 for them).
cd /d0/scratch/choij/SKNanoAnalyzer
source setup.sh > /dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
grep -q "w0 = MCweight() \* lumi_ \* pu_\[0\];" HcToWA_Analyzers/src/MeasFakeRate.cc || { echo "code not patched"; exit 1; }
cd /d0/scratch/choij/hcto_prod
SKNano.py -a MeasFakeRate -i TTLL_powheg,TTLJ_powheg -n -100 -e 2024 --userflags MeasMuFR,MeasElFR > measfr_tt_notoppt.log 2>&1; echo TT_RC=$?
echo SUBMITTED $(date)
