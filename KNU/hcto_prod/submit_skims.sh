#!/bin/bash
# Skim_TriLep (TriLepton analysis, closure) and Skim_FakeRate (data + QCD only, F6) in parallel
# (user 2026-11-26). Outputs: /pnfs/.../SKNanoSkim/2024/{DATA,MC}/Skim/choij/Skim_<name>_<sample> (stage-out).
# Waits for the module build of trigsf_test.sh, since the generation snapshots the library.
cd /d0/scratch/choij/hcto_prod
for i in $(seq 1 120); do grep -q build_rc trigsf_test.log 2>/dev/null && break; sleep 30; done
grep build_rc trigsf_test.log || { echo "build not finished after 60 min, not submitting"; exit 1; }
grep -q "build_rc=0" trigsf_test.log || { echo "build failed, not submitting"; exit 1; }
cd /d0/scratch/choij/SKNanoAnalyzer
source setup.sh > /dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
echo "proxy hours left: $(( $(voms-proxy-info -timeleft) / 3600 ))"
# Skim_TriLep: as submit_skim_trilep.sh (2026-11-24)
TDATA="MuonEG,Muon0,Muon1"
TMC="WZto3LNu,ZZto4L,ttWtoLNu,ttZtoLL_MLL50toInf,ttZtoLL_MLL4to50,ttHtoNonbb_M125,tZq,tHq,tHW,tWZ_tlepWlep,tWZ_tlepWhad,tWZ_thadWlep"
TMC="$TMC,WWW,WWZ,WZZ,ZZZ,ggHtoZZto4L_M125,VBFHtoZZto4L_M125,WplusHtoNonbb_M125,WminusHtoNonbb_M125,ZHtoNonbb_M125,TTTT"
TMC="$TMC,DYto2E_2J_MLL50toInf,DYto2Mu_2J_MLL50toInf,DYto2Tau_2J_MLL50toInf,DYto2E_2J_MLL10to50,DYto2Mu_2J_MLL10to50,DYto2Tau_2J_MLL10to50"
TMC="$TMC,TTG_1J,TTG_1J_PTG100toInf,TTG_1J_PTG200toInf"
TMC="$TMC,DYGto2LG_1J_MLL4to50,DYGto2LG_1J_MLL50toInf,DYGto2LG_1J_MLL50_PTG100toInf,DYGto2LG_1J_MLL50_PTG200toInf,DYGto2LG_1J_MLL50_PTG400toInf,DYGto2LG_1J_MLL50_PTG600toInf"
TMC="$TMC,TTLL_powheg,TTLJ_powheg,WZto3LNu_1J_amcatnloFXFX"
for m in 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95 100 105 110 115 120 125; do TMC="$TMC,TTToHcToWAToMuMu-MHc130_MA$m"; done
# Skim_FakeRate: data PDs of the fake-rate paths and the QCD-enriched samples
FDATA="Muon0,Muon1,EGamma0,EGamma1"
FMC=""
for b in 15to20 20to30 30to50 50to80 80to120 120to170 170to300 300to470 470to600 600to800 800to1000 1000toInf; do
  for f in MuEnriched EMEnriched bcToE; do FMC="$FMC,QCD_PT${b}_${f}"; done
done
FMC=${FMC#,}
cd /d0/scratch/choij/hcto_prod
SKNano.py -a Skim_TriLep -i "$TDATA" -e 2024 -n -20 --skimming_mode > skim_trilep_data.log 2>&1 & p1=$!
sleep 10
SKNano.py -a Skim_TriLep -i "$TMC" -e 2024 -n -20 --skimming_mode > skim_trilep_mc.log 2>&1 & p2=$!
sleep 10
SKNano.py -a Skim_FakeRate -i "$FDATA" -e 2024 -n -20 --skimming_mode > skim_fr_data.log 2>&1 & p3=$!
sleep 10
SKNano.py -a Skim_FakeRate -i "$FMC" -e 2024 -n -20 --skimming_mode > skim_fr_mc.log 2>&1 & p4=$!
wait $p1; echo "TRILEP_DATA_RC=$?"
wait $p2; echo "TRILEP_MC_RC=$?"
wait $p3; echo "FR_DATA_RC=$?"
wait $p4; echo "FR_MC_RC=$?"
echo "SKIMS_SUBMITTED $(date)"
