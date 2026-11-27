#!/bin/bash
# Productions with the HcToWA b-tag efficiency map (user approval 2026-11-28; SKNano c657425, map in
# HcToWA_Analyzers/data/2024/BTagEff). Label flag HcToWABTagEff (no analyzer effect) gives new output tags
# (/pnfs is write-once):
#  1. TriLepton SR trees, all Skim_TriLep data + MC (replaces the PreBTagEff production lost to the purge):
#     SKNanoOutput/TriLepton/Run1E2Mu_Run3Mu_SRTree_RunSyst_BTagEffHists_HcToWABTagEff/2024/
#  2. DiLepton EMU, MC only (b-tag check of AN ssec:BTagSFEffect; data histograms unchanged):
#     SKNanoOutput/DiLepton/RunEMu_RunSyst_TrigDZ_HcToWABTagEff/2024/
#   nohup setsid bash submit_final_btageff.sh > submit_final_btageff.log 2>&1 &
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh >/dev/null 2>&1
export SKNANO_SKIM_METADATA_DIR=/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
echo "proxy hours left: $(( $(voms-proxy-info -timeleft) / 3600 ))"
cd /d0/scratch/choij/hcto_prod
TRI_FLAGS=Run1E2Mu,Run3Mu,SRTree,RunSyst,BTagEffHists,HcToWABTagEff
SKNano.py -a TriLepton -i Skim_TriLep_MuonEG,Skim_TriLep_Muon0,Skim_TriLep_Muon1 -n -100 -e 2024 --userflags $TRI_FLAGS > final_tri_data.log 2>&1; echo TRI_DATA_RC=$?
MC=$(grep -o "SKNano.py -a TriLepton -i Skim_TriLep_DYGto2LG[^ ]*" submit_srtree_pre.sh | sed 's/.* -i //')
SKNano.py -a TriLepton -i $MC -n -100 -e 2024 --userflags $TRI_FLAGS > final_tri_mc.log 2>&1; echo TRI_MC_RC=$?
DIL=$(grep -o "SKNano.py -a DiLepton -i [^ ]*" submit_trigdz.sh | head -1 | sed 's/.* -i //')
SKNano.py -a DiLepton -i $DIL -n -100 -e 2024 --userflags RunEMu,RunSyst,TrigDZ,HcToWABTagEff > final_emu.log 2>&1; echo EMU_RC=$?
echo SUBMITTED $(date)
