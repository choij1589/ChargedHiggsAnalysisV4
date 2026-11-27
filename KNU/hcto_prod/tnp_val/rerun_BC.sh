#!/bin/bash
cd /d0/scratch/choij/hcto_prod/tnp_val
for x in A B C; do grep -q VALIDATE_DONE run_$x.log && [ $x = A ] && continue
  env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnpval_$x -a request_memory=3000 ./run_$x.sh > run_$x.log 2>&1 & done
wait; for x in A B C; do echo "$x: $(grep -c VALIDATE_DONE run_$x.log) $(grep real run_$x.log)"; done
env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnpval_cmp ./compare.sh > compare.log 2>&1; echo "compare rc=$?"
cat compare.log; echo "VALIDATION END $(date)"
