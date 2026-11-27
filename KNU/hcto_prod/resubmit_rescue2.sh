#!/bin/bash
# 2026-11-27: rescue of the skim DAGs with the environment of the original submission
# (submit_skims.sh: setup.sh, SKNANO_SKIM_METADATA_DIR, X509_CERT_DIR) passed the way SKNano.py
# does it (include_env = every variable except the Telegram secrets). The 18:48 and 07:23 rescues
# used condor_submit_dag -update_submit without it, so the post-processing nodes (getenv) failed.
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh > /dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
[[ -n "$SKNANO_PYTHON" && -d "$SKNANO_SKIM_METADATA_DIR" ]] || { echo "environment incomplete" >&2; exit 1; }
echo "SKNANO_PYTHON=$SKNANO_PYTHON SKNANO_SKIM_METADATA_DIR=$SKNANO_SKIM_METADATA_DIR"
envlist=$(env | cut -d= -f1 | grep -v -E '^(TOKEN_TELEGRAMBOT|USER_CHATID|BASH_FUNC_.*|_)$' | grep -E '^[A-Za-z_][A-Za-z0-9_]*$' | paste -sd,)
for r in "$@"; do
  cd /d0/scratch/choij/SKNanoRunlog/$r/dags || exit 1
  echo "== $r"; condor_submit_dag -update_submit -include_env "$envlist" finaldag.dag 2>&1 | tee resubmit_rescue_env.log | grep -E "submitted|rescue|ERROR"
done
