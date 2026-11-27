#!/bin/bash
# PLAN_Signal step A validation (2026-11-28): TriLepton with SRTree,RunSyst,BTagEffHists (+ flag Val for a separate output dir)
# on MuonEG (all eras), WZto3LNu, DYto2Mu 2J MLL50, signal MHc130_MA90 -> histogram identity vs V2 and RNTuple checks;
# GetSignalSumW on the 23 signal samples; DiLepton MeasBTagEff on TTLL (b-tag efficiency maps, S1 (a)).
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
echo "proxy hours left: $(( $(voms-proxy-info -timeleft) / 3600 ))"
cd /d0/scratch/choij/hcto_prod
F=Run1E2Mu,Run3Mu,SRTree,RunSyst,BTagEffHists,Val
SKNano.py -a TriLepton -i Skim_TriLep_MuonEG -n -100 -e 2024 --userflags $F > srtree_val_data.log 2>&1; echo DATA_RC=$?
SKNano.py -a TriLepton -i Skim_TriLep_WZto3LNu,Skim_TriLep_DYto2Mu_2J_MLL50toInf,Skim_TriLep_TTToHcToWAToMuMu-MHc130_MA90 -n -100 -e 2024 --userflags $F > srtree_val_mc.log 2>&1; echo MC_RC=$?
SIG=$(for m in 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95 100 105 110 115 120 125; do printf "TTToHcToWAToMuMu-MHc130_MA%s," $m; done | sed 's/,$//')
SKNano.py -a GetSignalSumW -i $SIG -n -100 -e 2024 > sumw_signal.log 2>&1; echo SUMW_RC=$?
SKNano.py -a DiLepton -i TTLL_powheg -n -100 -e 2024 --userflags MeasBTagEff > measbtageff.log 2>&1; echo BTAG_RC=$?
echo SUBMITTED $(date)
