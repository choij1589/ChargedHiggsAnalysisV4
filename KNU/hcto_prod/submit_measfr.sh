#!/bin/bash
# MeasFakeRate production (PLAN_BkgEst step 2, 2026-11-27): on the Skim_FakeRate skims (data, QCD MC)
# and the unskimmed prompt MC (F6; the 22 DiLepton samples). Flags per input so that each output holds
# only the flavour it measures: Muon PDs and MuEnriched QCD -> MeasMuFR; EGamma PDs, EMEnriched and
# bcToE QCD (F8) -> MeasElFR; prompt MC -> both (Z/W-region normalization, systematic lanes automatic).
# Outputs: /pnfs/.../SKNanoOutput/MeasFakeRate/<flags>/2024/ (stage-out).
cd /d0/scratch/choij/SKNanoAnalyzer
source setup.sh > /dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
echo "proxy hours left: $(( $(voms-proxy-info -timeleft) / 3600 ))"
B="15to20 20to30 30to50 50to80 80to120 120to170 170to300 300to470 470to600 600to800 800to1000 1000toInf"
QMU=""; QEL=""
for b in $B; do QMU="$QMU,Skim_FakeRate_QCD_PT${b}_MuEnriched"; QEL="$QEL,Skim_FakeRate_QCD_PT${b}_EMEnriched,Skim_FakeRate_QCD_PT${b}_bcToE"; done
QMU=${QMU#,}; QEL=${QEL#,}
PROMPT="DYto2E_2J_MLL10to50,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL10to50,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL10to50,DYto2Tau_2J_MLL50toInf,TTLL_powheg,TTLJ_powheg,ST_tch_top_lep,ST_tch_antitop_lep,ST_tW_top_Lep,ST_tW_antitop_Lep,ST_tW_top_Semilep,ST_tW_antitop_Semilep,ST_sch_top_Lep,ST_sch_antitop_Lep,WW_pythia,WZ_pythia,ZZ_pythia,WtoENu_2J,WtoMuNu_2J,WtoTauNu_2J"
cd /d0/scratch/choij/hcto_prod
SKNano.py -a MeasFakeRate -i "Skim_FakeRate_Muon0,Skim_FakeRate_Muon1,$QMU" -n -100 -e 2024 --userflags MeasMuFR > measfr_mu.log 2>&1 & p1=$!
sleep 10
SKNano.py -a MeasFakeRate -i "Skim_FakeRate_EGamma0,Skim_FakeRate_EGamma1,$QEL" -n -100 -e 2024 --userflags MeasElFR > measfr_el.log 2>&1 & p2=$!
sleep 10
SKNano.py -a MeasFakeRate -i "$PROMPT" -n -100 -e 2024 --userflags MeasMuFR,MeasElFR > measfr_prompt.log 2>&1 & p3=$!
wait $p1; echo "MU_RC=$?"
wait $p2; echo "EL_RC=$?"
wait $p3; echo "PROMPT_RC=$?"
echo "MEASFR_SUBMITTED $(date)"
