#!/bin/bash
# Parallel RNTuple->TTree conversion (one process per sample); same arguments as
# submit_tnp.sh convert. Finished outputs are skipped by rntuple_to_ttree.py.
export MAMBA_ROOT_PREFIX=/d0/scratch/choij/micromamba_envs
eval "$(/d0/scratch/choij/micromamba_bin/micromamba shell hook -s bash)"
micromamba activate /d0/scratch/choij/micromamba_envs/envs/NanoV15
CONV=/d0/scratch/choij/TnP/scripts/rntuple_to_ttree.py
OUT=/d0/scratch/choij/SKNanoOutput
TNP=/d0/scratch/choij/TnP/2024
P=/d0/scratch/choij/hcto_prod/convlogs; mkdir -p $P
conv() { # lepton analyzer sample-glob outdir group
    local lep=$1 ana=$2 glob=$3 outdir=$4 group=$5 rc=0
    for d in $OUT/$ana/2024/$glob; do
        python $CONV --lepton $lep --outdir $TNP/$lep/$outdir --group $group \
            --prefix $(basename $d) "$d/hists_*.root" || rc=1
    done
    echo "== $outdir rc=$rc $(date)"
}
conv muon MuonTnPProducer DYto2Mu_4J_MLL50toInf DYto2Mu_4J_MLL50toInf 4 > $P/mu_dy4j.log 2>&1 &
conv muon MuonTnPProducer DYto2Mu_2J_MLL50toInf DYto2Mu_2J_MLL50toInf 4 > $P/mu_dy2j.log 2>&1 &
conv electron ElectronTnPProducer 'EGamma[01]_*' EGamma 10 > $P/el_data.log 2>&1 &
conv electron ElectronTnPProducer DYto2E_2J_MLL50toInf DYto2E_2J_MLL50toInf 6 > $P/el_dy2j.log 2>&1 &
conv electron ElectronTnPProducer DYto2E_4J_MLL50toInf DYto2E_4J_MLL50toInf 6 > $P/el_dy4j.log 2>&1 &
wait
grep -h "^== " $P/*.log
grep -h "rc=1" $P/*.log > /dev/null && echo "CONVERT FAILED" || echo "CONVERT ALL OK"
echo "convert end $(date)"
