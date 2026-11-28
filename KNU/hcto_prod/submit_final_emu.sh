#!/bin/bash
# Retry of the DiLepton EMU part of submit_final_btageff.sh (08:55 attempt: FileNotFoundError writing job_1.cc in its new run dir).
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
cd /d0/scratch/choij/hcto_prod
DIL=$(grep -o "SKNano.py -a DiLepton -i [^ ]*" submit_trigdz.sh | head -1 | sed 's/.* -i //')
SKNano.py -a DiLepton -i $DIL -n -100 -e 2024 --userflags RunEMu,RunSyst,TrigDZ,HcToWABTagEff > final_emu2.log 2>&1; echo EMU_RC=$?
