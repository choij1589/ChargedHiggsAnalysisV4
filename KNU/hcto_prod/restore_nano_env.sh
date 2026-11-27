#!/bin/bash
# Restore SKNano's Nano environment after the KNU scratch purge of 2026-11-28 03:48 (python3.12 stdlib, bin/root and
# other files deleted; all TriLepton PreBTagEff jobs after 03:48 failed with exit 127). The environment is recreated at
# the same path from its own explicit lock (config/env/sknano_Nano_knu_explicit.txt of ChargedHiggsAnalysisV4, 432
# conda-forge packages, exported from this environment on 2026-11-24): same package set, no change of content.
# The damaged environment is moved aside (envs/Nano_purged_20261128), not deleted.
#   nohup setsid bash restore_nano_env.sh > restore_nano_env.log 2>&1 &
set -e
R=/d0/scratch/choij/micromamba_envs
M=/d0/scratch/choij/micromamba_bin/micromamba
LOCK=/d0/scratch/choij/hcto_prod/sknano_Nano_knu_explicit.txt
echo "START $(date)"
[ -d $R/envs/Nano_purged_20261128 ] || mv $R/envs/Nano $R/envs/Nano_purged_20261128
"$M" create -y -r $R -n Nano --file $LOCK
"$M" run -r $R -n Nano python -c "import ROOT, correctionlib, encodings; print('ROOT', ROOT.gROOT.GetVersion(), 'correctionlib', correctionlib.__version__)"
"$M" run -r $R -n Nano root-config --version
# installed set against the lock (package-version-build of each URL)
grep '^https' $LOCK | sed 's|.*/||; s|\.conda#.*||; s|\.tar\.bz2#.*||' | sort > /tmp/nano_lock_$$.txt
ls $R/envs/Nano/conda-meta/*.json | sed 's|.*/||; s|\.json$||' | sort > /tmp/nano_inst_$$.txt
echo "lock $(wc -l < /tmp/nano_lock_$$.txt) installed $(wc -l < /tmp/nano_inst_$$.txt) differ $(comm -3 /tmp/nano_lock_$$.txt /tmp/nano_inst_$$.txt | wc -l)"
comm -3 /tmp/nano_lock_$$.txt /tmp/nano_inst_$$.txt | head
rm -f /tmp/nano_lock_$$.txt /tmp/nano_inst_$$.txt
echo "RESTORE_DONE $(date)"
