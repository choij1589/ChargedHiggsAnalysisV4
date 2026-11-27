#!/bin/bash
# MeasTrigEff production (PLAN_Trigger step 2): one mode per data PD, all modes in MC.
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh > /dev/null 2>&1
cd /d0/scratch/choij/hcto_prod
MC=TTLL_powheg,DYto2Tau_2J_MLL10to50,DYto2Tau_2J_MLL50toInf,DYto2Mu_2J_MLL10to50,DYto2Mu_2J_MLL50toInf,DYto2E_2J_MLL10to50,DYto2E_2J_MLL50toInf
SKNano.py -a MeasTrigEff -i Muon0,Muon1 -n -100 -e 2024 --userflags MeasElLegs,MeasDblMuPair > submit_trig_muon.log 2>&1; echo "MUON_RC=$?" >> submit_trig_muon.log
SKNano.py -a MeasTrigEff -i EGamma0,EGamma1 -n -100 -e 2024 --userflags MeasMuLegs > submit_trig_egamma.log 2>&1; echo "EGAMMA_RC=$?" >> submit_trig_egamma.log
SKNano.py -a MeasTrigEff -i MuonEG -n -100 -e 2024 --userflags MeasEMuPair > submit_trig_muoneg.log 2>&1; echo "MUONEG_RC=$?" >> submit_trig_muoneg.log
SKNano.py -a MeasTrigEff -i $MC -n -100 -e 2024 --userflags MeasElLegs,MeasMuLegs,MeasDblMuPair,MeasEMuPair > submit_trig_mc.log 2>&1; echo "MC_RC=$?" >> submit_trig_mc.log
