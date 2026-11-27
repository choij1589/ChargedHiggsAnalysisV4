#!/bin/bash
cd /d0/scratch/choij/SKNanoAnalyzer && source setup.sh > /dev/null 2>&1
./scripts/build.sh > /d0/scratch/choij/hcto_prod/build_trilep3.log 2>&1
echo "BUILD_RC=$? $(date)" >> /d0/scratch/choij/hcto_prod/build_trilep3.log
