#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /cvmfs/cms.cern.ch/el9_amd64_gcc12/cms/cmssw/CMSSW_13_3_1/src
eval `scramv1 runtime -sh`
cd - > /dev/null

# KNU (2026-11-24): TNP_BASE follows the checkout instead of the tamsa path
# (/data9/Users/choij/Sync/workspace/tnp_tamsa).
export TNP_BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH=$TNP_BASE/python:$PATH
export PYTHONPATH=$TNP_BASE/python${PYTHONPATH:+:$PYTHONPATH}
#export PYTHONPATH=${PYTHONPATH}:$TNP_BASE/tdr-style
# KNU: condor_run (hadd of the hist step) writes its job wrapper with $SHELL as
# interpreter; the login shell is zsh, which the workers do not have.
export SHELL=/bin/bash
