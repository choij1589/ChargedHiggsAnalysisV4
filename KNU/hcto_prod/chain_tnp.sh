#!/bin/bash
# TnP ntuple production, then RNTuple->TTree conversion (user order 2026-11-25:
# TnP first, skims after the measurement). Conversion only if all four TnP DAGs exit 0.
PROD=/d0/scratch/choij/hcto_prod
q() { condor_q choij -af JobBatchName 2>/dev/null | grep -cE "$1"; }
echo "chain start $(date)"
$PROD/submit_tnp.sh > $PROD/submit_tnp.log 2>&1; echo "submit rc=$? $(date)"
sleep 120
while [ "$(q 'TnPProducer')" -gt 0 ]; do sleep 300; done
echo "TnP jobs left the queue $(date)"
ok=1
for d in $(ls -d /d0/scratch/choij/SKNanoRunlog/*TnPProducer 2>/dev/null | sort | tail -4); do
    s=$(grep "EXITING WITH STATUS" $d/dags/dagfile.dag.dagman.out 2>/dev/null | tail -1 | sed 's/.*STATUS //')
    echo "$d status=${s:-none}"; [ "$s" = "0" ] || ok=0
done
if [ $ok = 1 ]; then
    $PROD/submit_tnp.sh convert > $PROD/convert_tnp.log 2>&1; echo "convert rc=$? $(date)"
else
    echo "a TnP DAG failed: conversion not started"
fi
echo "chain end $(date)"
