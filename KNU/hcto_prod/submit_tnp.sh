#!/bin/bash
# Tag-and-probe ntuple production for the 2024 lepton ID SFs (phase 2.3,
# ChargedHiggsAnalysisV4 docs/PLAN_LeptonID.md step 3). NOT YET RUN.
#
#   submit (default): SKNano.py jobs, one DAG per call, outputs kept per job
#                     (--no-hadd) in $SKNANO_OUTPUT/<Analyzer>/2024/<sample>/hists_*.root
#     MuonTnPProducer     Muon0, Muon1 (all periods), DYto2Mu_4J_MLL50toInf (nominal),
#                         DYto2Mu_2J_MLL50toInf (alternative)
#     ElectronTnPProducer EGamma0, EGamma1 (all periods), DYto2E_2J_MLL50toInf (nominal),
#                         DYto2E_4J_MLL50toInf (LO, alternative-MC cross-check; user
#                         decision 2026-11-24; WITH_DYTO2E_4J=0 to leave it out)
#   convert:          after all DAGs are done, RNTuple -> TTree into
#                     /d0/scratch/choij/TnP/2024/{muon,electron}/<sample dir>/ (tnp_tamsa samples)
#                     with scripts/tnp/rntuple_to_ttree.py (entry counts in = out)
#
# Launch detached on knu1, only after the Skim_TriLep production has left the queue:
#   nohup setsid /d0/scratch/choij/hcto_prod/submit_tnp.sh > /d0/scratch/choij/hcto_prod/submit_tnp.log 2>&1 < /dev/null &
#   nohup setsid /d0/scratch/choij/hcto_prod/submit_tnp.sh convert > /d0/scratch/choij/hcto_prod/convert_tnp.log 2>&1 < /dev/null &
#
# Job sizing (one-file and ten-file interactive tests, 2026-11-24): event loop
# ~93k (Muon) / 122k (EGamma) / 27k (DY mumu 4J) / 33k (DY ee 2J) events/s plus
# ~25 s start-up (3.5 min on workers); data -n -250, MC -n -100.
# no set -e: commands inside setup.sh fail by design and would end the script
MODE=${1:-submit}
WITH_DYTO2E_4J=${WITH_DYTO2E_4J:-1}
PROD=/d0/scratch/choij/hcto_prod

if [ "$MODE" = "submit" ]; then
    cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh > /dev/null 2>&1
    export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates
    cd $PROD
    if ! voms-proxy-info -exists -valid 48:00 > /dev/null 2>&1; then
        echo "no CMS proxy valid for 48 h: run voms-proxy-init --voms cms --valid 192:00"; exit 1
    fi
    if condor_q choij -af JobBatchName 2>/dev/null | grep -q '^Skim_TriLep'; then
        echo "Skim_TriLep jobs still in the queue: not submitting"; exit 1
    fi
    for s in Muon0 Muon1 EGamma0 EGamma1 DYto2Mu_4J_MLL50toInf DYto2Mu_2J_MLL50toInf DYto2E_2J_MLL50toInf DYto2E_4J_MLL50toInf; do
        python3 -c "import json,sys; d=json.load(open('$SKNANO_DATA/2024/Sample/CommonSampleInfo.json')); sys.exit(0 if '$s' in d else 1)" \
            || { echo "alias $s missing from CommonSampleInfo.json"; exit 1; }
    done
    echo "== MuonTnPProducer data $(date)"
    SKNano.py -a MuonTnPProducer -i Muon0,Muon1 -e 2024 -n -250 --no-hadd > submit_tnp_mu_data.log 2>&1
    echo "RC=$?"; sleep 5
    echo "== MuonTnPProducer MC $(date)"
    SKNano.py -a MuonTnPProducer -i DYto2Mu_4J_MLL50toInf,DYto2Mu_2J_MLL50toInf -e 2024 -n -100 --no-hadd > submit_tnp_mu_mc.log 2>&1
    echo "RC=$?"; sleep 5
    echo "== ElectronTnPProducer data $(date)"
    SKNano.py -a ElectronTnPProducer -i EGamma0,EGamma1 -e 2024 -n -250 --no-hadd > submit_tnp_el_data.log 2>&1
    echo "RC=$?"; sleep 5
    EL_MC=DYto2E_2J_MLL50toInf
    [ "$WITH_DYTO2E_4J" = "1" ] && EL_MC="$EL_MC,DYto2E_4J_MLL50toInf"
    echo "== ElectronTnPProducer MC ($EL_MC) $(date)"
    SKNano.py -a ElectronTnPProducer -i $EL_MC -e 2024 -n -100 --no-hadd > submit_tnp_el_mc.log 2>&1
    echo "RC=$?"
    echo "== submitted $(date)"

elif [ "$MODE" = "convert" ]; then
    export MAMBA_ROOT_PREFIX=/d0/scratch/choij/micromamba_envs
    eval "$(/d0/scratch/choij/micromamba_bin/micromamba shell hook -s bash)"
    micromamba activate /d0/scratch/choij/micromamba_envs/envs/NanoV15
    CONV=/d0/scratch/choij/TnP/scripts/rntuple_to_ttree.py
    OUT=/d0/scratch/choij/SKNanoOutput
    TNP=/d0/scratch/choij/TnP/2024
    rc=0
    conv() { # lepton analyzer sample-glob outdir group
        local lep=$1 ana=$2 glob=$3 outdir=$4 group=$5
        for d in $OUT/$ana/2024/$glob; do
            [ -d "$d" ] || { echo "missing $d"; rc=1; continue; }
            python $CONV --lepton $lep --outdir $TNP/$lep/$outdir --group $group \
                --prefix $(basename $d) "$d/hists_*.root" || rc=1
        done
    }
    conv muon MuonTnPProducer 'Muon[01]_*' Muon 10
    conv muon MuonTnPProducer DYto2Mu_4J_MLL50toInf DYto2Mu_4J_MLL50toInf 4
    conv muon MuonTnPProducer DYto2Mu_2J_MLL50toInf DYto2Mu_2J_MLL50toInf 4
    conv electron ElectronTnPProducer 'EGamma[01]_*' EGamma 10
    conv electron ElectronTnPProducer DYto2E_2J_MLL50toInf DYto2E_2J_MLL50toInf 6
    [ -d $OUT/ElectronTnPProducer/2024/DYto2E_4J_MLL50toInf ] && \
        conv electron ElectronTnPProducer DYto2E_4J_MLL50toInf DYto2E_4J_MLL50toInf 6
    echo "== convert done $(date) rc=$rc"
    exit $rc
else
    echo "usage: $0 [submit|convert]"; exit 1
fi
