#!/bin/bash
# Skim_TriLep MC only (the 01:24 submission collided with the data one on the run-directory name)
cd /d0/scratch/choij/SKNanoAnalyzer
source setup.sh > /dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
TMC="WZto3LNu,ZZto4L,ttWtoLNu,ttZtoLL_MLL50toInf,ttZtoLL_MLL4to50,ttHtoNonbb_M125,tZq,tHq,tHW,tWZ_tlepWlep,tWZ_tlepWhad,tWZ_thadWlep"
TMC="$TMC,WWW,WWZ,WZZ,ZZZ,ggHtoZZto4L_M125,VBFHtoZZto4L_M125,WplusHtoNonbb_M125,WminusHtoNonbb_M125,ZHtoNonbb_M125,TTTT"
TMC="$TMC,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL50toInf,DYto2E_2J_MLL10to50,DYto2Mu_2J_MLL10to50,DYto2Tau_2J_MLL10to50"
TMC="$TMC,TTG_1J,TTG_1J_PTG100toInf,TTG_1J_PTG200toInf"
TMC="$TMC,DYGto2LG_1J_MLL4to50,DYGto2LG_1J_MLL50toInf,DYGto2LG_1J_MLL50_PTG100toInf,DYGto2LG_1J_MLL50_PTG200toInf,DYGto2LG_1J_MLL50_PTG400toInf,DYGto2LG_1J_MLL50_PTG600toInf"
TMC="$TMC,TTLL_powheg,TTLJ_powheg,WZto3LNu_1J_amcatnloFXFX"
for m in 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95 100 105 110 115 120 125; do TMC="$TMC,TTToHcToWAToMuMu-MHc130_MA$m"; done
cd /d0/scratch/choij/hcto_prod
SKNano.py -a Skim_TriLep -i "$TMC" -e 2024 -n -20 --skimming_mode > skim_trilep_mc2.log 2>&1
echo "TRILEP_MC_RC=$?"
