#!/bin/bash
# 2026-11-28: something on /d0 (the scratch cleaner, still running after the 03:48 purge) removes empty
# directories: the empty output/ dirs of fresh SKNano run dirs vanished (TriLepton jobs: "cannot create
# partial output .../output/hists_0.root.partial", exit 6) and SKNano.py failed writing job_1.cc in its
# own new dir. This guard keeps output/ (with a .keep file; hadd reads only output/hists_*.root) in every
# sample dir of today's runs until 19:30.  nohup setsid bash guard_outdirs.sh > guard_outdirs.log 2>&1 &
end=$(date -d "today 19:30" +%s)
while [ $(date +%s) -lt $end ]; do
  for s in /d0/scratch/choij/SKNanoRunlog/2026_11_28_*/2024/*/ /d0/scratch/choij/SKNanoRunlog/2026_11_28_*/*/*/; do
    [ -f "$s/run.sh" ] || [ -f "$s/hadd.sh" ] || continue
    if [ ! -f "$s/output/.keep" ]; then mkdir -p "$s/output" && touch "$s/output/.keep" && echo "$(date +%T) restored $s"; fi
  done
  sleep 30
done
