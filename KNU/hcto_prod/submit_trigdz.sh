#!/bin/bash
# DiLepton DIMU + EMU, MC only (2026-11-26): trigger-SF lanes with the DZ uncertainty of the JSON (no closure term),
# dimuon closure also on the IsoMu24 / L1-seed subsets (C_data = C_MC, user). Data histograms unchanged (LepIDSF data).
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh > /dev/null 2>&1
cd /d0/scratch/choij/hcto_prod
SKNano.py -a DiLepton -i DYto2E_2J_MLL10to50,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL10to50,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL10to50,DYto2Tau_2J_MLL50toInf,TTLL_powheg,TTLJ_powheg,ST_tch_top_lep,ST_tch_antitop_lep,ST_tW_top_Lep,ST_tW_antitop_Lep,ST_tW_top_Semilep,ST_tW_antitop_Semilep,ST_sch_top_Lep,ST_sch_antitop_Lep,WW_pythia,WZ_pythia,ZZ_pythia,WtoENu_2J,WtoMuNu_2J,WtoTauNu_2J -n -100 -e 2024 --userflags RunDiMu,RunSyst,TrigDZ > submit_dimu_trigdz.log 2>&1 &
p1=$!
sleep 5
SKNano.py -a DiLepton -i DYto2E_2J_MLL10to50,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL10to50,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL10to50,DYto2Tau_2J_MLL50toInf,TTLL_powheg,TTLJ_powheg,ST_tch_top_lep,ST_tch_antitop_lep,ST_tW_top_Lep,ST_tW_antitop_Lep,ST_tW_top_Semilep,ST_tW_antitop_Semilep,ST_sch_top_Lep,ST_sch_antitop_Lep,WW_pythia,WZ_pythia,ZZ_pythia,WtoENu_2J,WtoMuNu_2J,WtoTauNu_2J -n -100 -e 2024 --userflags RunEMu,RunSyst,TrigDZ > submit_emu_trigdz.log 2>&1 &
p2=$!
wait $p1; echo "DIMU_RC=$?" >> submit_dimu_trigdz.log
wait $p2; echo "EMU_RC=$?" >> submit_emu_trigdz.log
