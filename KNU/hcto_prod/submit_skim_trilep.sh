#!/bin/bash
# Skim_TriLep production for the 2024 TriLepton regions (docs/LOG_Computing.md).
# Samples: data PDs of the SR triggers; MC of AN tab:MCSampleListSR, TTLL/TTLJ
# (nonprompt closure), WZ amc@NLO (alternative), all signal mass points.
# no set -e: commands inside setup.sh fail by design and would end the script
cd /d0/scratch/choij/SKNanoAnalyzer
source setup.sh > /dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
echo "RUN3_NANOAODPATH=$SKNANO_RUN3_NANOAODPATH META=$SKNANO_SKIM_METADATA_DIR"
DATA="MuonEG,Muon0,Muon1"
MC="WZto3LNu,ZZto4L,ttWtoLNu,ttZtoLL_MLL50toInf,ttZtoLL_MLL4to50,ttHtoNonbb_M125,tZq,tHq,tHW,tWZ_tlepWlep,tWZ_tlepWhad,tWZ_thadWlep"
MC="$MC,WWW,WWZ,WZZ,ZZZ,ggHtoZZto4L_M125,VBFHtoZZto4L_M125,WplusHtoNonbb_M125,WminusHtoNonbb_M125,ZHtoNonbb_M125,TTTT"
MC="$MC,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL50toInf,DYto2E_2J_MLL10to50,DYto2Mu_2J_MLL10to50,DYto2Tau_2J_MLL10to50"
MC="$MC,TTG_1J,TTG_1J_PTG100toInf,TTG_1J_PTG200toInf"
MC="$MC,DYGto2LG_1J_MLL4to50,DYGto2LG_1J_MLL50toInf,DYGto2LG_1J_MLL50_PTG100toInf,DYGto2LG_1J_MLL50_PTG200toInf,DYGto2LG_1J_MLL50_PTG400toInf,DYGto2LG_1J_MLL50_PTG600toInf"
MC="$MC,TTLL_powheg,TTLJ_powheg,WZto3LNu_1J_amcatnloFXFX"
for m in 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95 100 105 110 115 120 125; do MC="$MC,TTToHcToWAToMuMu-MHc130_MA$m"; done
echo "== data"; SKNano.py -a Skim_TriLep -i "$DATA" -e 2024 -n -20 --skimming_mode
echo "== mc";   SKNano.py -a Skim_TriLep -i "$MC"   -e 2024 -n -20 --skimming_mode
echo "== submitted $(date)"
