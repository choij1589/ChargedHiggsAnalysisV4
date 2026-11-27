#!/bin/bash
# DiLepton with trigger SFs (DblMuTrigSF, EMuTrigSF) and the SF-chain No-lanes (2026-11-26); MC only: data histograms are unchanged, the plots take data from the LepIDSF production
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh > /dev/null 2>&1
cd /d0/scratch/choij/hcto_prod
SKNano.py -a DiLepton -i DYto2E_2J_MLL10to50,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL10to50,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL10to50,DYto2Tau_2J_MLL50toInf,TTLL_powheg,TTLJ_powheg,ST_tch_top_lep,ST_tch_antitop_lep,ST_tW_top_Lep,ST_tW_antitop_Lep,ST_tW_top_Semilep,ST_tW_antitop_Semilep,ST_sch_top_Lep,ST_sch_antitop_Lep,WW_pythia,WZ_pythia,ZZ_pythia,WtoENu_2J,WtoMuNu_2J,WtoTauNu_2J -n -100 -e 2024 --userflags RunDiMu,RunSyst,TrigSF > submit_dimu_trigsf.log 2>&1 &
p1=$!
sleep 5
SKNano.py -a DiLepton -i DYto2E_2J_MLL10to50,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL10to50,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL10to50,DYto2Tau_2J_MLL50toInf,TTLL_powheg,TTLJ_powheg,ST_tch_top_lep,ST_tch_antitop_lep,ST_tW_top_Lep,ST_tW_antitop_Lep,ST_tW_top_Semilep,ST_tW_antitop_Semilep,ST_sch_top_Lep,ST_sch_antitop_Lep,WW_pythia,WZ_pythia,ZZ_pythia,WtoENu_2J,WtoMuNu_2J,WtoTauNu_2J -n -100 -e 2024 --userflags RunEMu,RunSyst,TrigSF > submit_emu_trigsf.log 2>&1 &
p2=$!
wait $p1; echo "DIMU_RC=$?" >> submit_dimu_trigsf.log
wait $p2; echo "EMU_RC=$?" >> submit_emu_trigsf.log
SKNano.py -a DiLepton -i DYto2E_2J_MLL10to50,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL10to50,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL10to50,DYto2Tau_2J_MLL50toInf,TTLL_powheg,TTLJ_powheg,ST_tch_top_lep,ST_tch_antitop_lep,ST_tW_top_Lep,ST_tW_antitop_Lep,ST_tW_top_Semilep,ST_tW_antitop_Semilep,ST_sch_top_Lep,ST_sch_antitop_Lep,WW_pythia,WZ_pythia,ZZ_pythia,WtoENu_2J,WtoMuNu_2J,WtoTauNu_2J -n -100 -e 2024 --userflags RunZEE,RunSyst,TrigSF > submit_zee_trigsf.log 2>&1
echo "ZEE_RC=$?" >> submit_zee_trigsf.log
