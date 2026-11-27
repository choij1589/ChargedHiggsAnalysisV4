#!/bin/bash
cd $TNP_BASE
python3 tnp_tamsa.py config/HcToWA_val_fit.py TEST_GAP_NUM_HcToWATight_DEN_RecoElectrons_2024 --step fit --set 0 --member 0 --data --bin $1 --no-condor
exit $?
