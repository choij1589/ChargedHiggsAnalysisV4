#!/bin/bash
# Production lepton ID efficiencies (2026-11-25): tnp_tamsa in NanoV15 (RDF hist step on the
# SKNano TnP RNTuples, legacy RooFit backend), all HcToWA configs in parallel. Only the
# orchestration runs here; hist and fit jobs go to condor (hist: 100 jobs per sample, fit: 20 per member).
cd /d0/scratch/choij/tnp_tamsa && export TNP_ENV=nanov15 && source setup.sh
L=/d0/scratch/choij/hcto_prod/tnp_prod
run() { python3 tnp_tamsa.py config/$1.py $2 --step hist,fit,sum --njob 100,20 --log > $L/$2.log 2>&1; echo "$2 rc=$? $(date)"; }
run HcToWA_Muon_2024 NUM_HcToWATight_DEN_TrackerMuons_2024 &
run HcToWA_Muon_2024 NUM_MediumID_DEN_TrackerMuons_2024 &
run HcToWA_Muon_2024 NUM_TightID_DEN_TrackerMuons_2024 &
run HcToWA_Electron_2024 NUM_HcToWATight_DEN_RecoElectrons_2024 &
run HcToWA_Electron_2024 NUM_wp90noiso_DEN_RecoElectrons_2024 &
run HcToWA_Electron_2024 NUM_cutBasedTight_DEN_RecoElectrons_2024 &
run HcToWA_Electron_2024 NUM_HcToWATight_DEN_RecoElectrons_2024_altMC &
wait; echo "ALL_TNP_DONE $(date)"
