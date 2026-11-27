#!/bin/bash
# ClosFakeRate production (PLAN_BkgEst step 4, F3; 2026-11-27): Skim_TriLep TTLL and TTLJ powheg, e mu mu and mu mu mu.
# Output /pnfs/.../SKNanoOutput/ClosFakeRate/Run1E2Mu_Run3Mu/2024/ (stage-out). Rates: data/2024/FakeRate/fakerate_HcToWA.json.
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
echo "proxy hours left: $(( $(voms-proxy-info -timeleft) / 3600 ))"
cd /d0/scratch/choij/hcto_prod
SKNano.py -a ClosFakeRate -i Skim_TriLep_TTLL_powheg,Skim_TriLep_TTLJ_powheg -n -100 -e 2024 --userflags Run1E2Mu,Run3Mu > closfr.log 2>&1; echo CLOS_RC=$?
echo SUBMITTED $(date)
