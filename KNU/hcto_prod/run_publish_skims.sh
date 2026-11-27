#!/bin/bash
# Publish finished Skim_TriLep samples to /pnfs every 15 min until no skim job is left.
# --keep-staging overnight: nothing is deleted on /d0 until the user has checked the result.
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
PY=/d0/scratch/choij/micromamba_envs/envs/NanoV15/bin/python
exec $PY -u /d0/scratch/choij/hcto_prod/publish_skims.py --era 2024 --keep-staging --loop 15
