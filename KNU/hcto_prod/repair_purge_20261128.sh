#!/bin/bash
# Repair after the KNU scratch purge of 2026-11-28 03:48 (user approval 2026-11-28; docs/LOG_Computing.md).
#  1. Nano    : recreated at the same path from its explicit lock (= the damaged env's conda-meta, 428 packages)
#  2. NanoV15 : recreated from a lock built from its own conda-meta (url#md5 of the 307 records)
#  3. SKNano external/libtorch: reinstalled by SKNano's scripts/install_libtorch.sh (pinned 2.9.0.dev20250630+cpu)
#  4. SKNano external/lhapdf/data: the two NNPDF31 sets of scripts/install_lhapdf.sh (the library is intact)
#  5. SKNano build (scripts/build.sh), once
# Damaged envs are moved to envs/<name>_purged_20261128 (removed after the checks pass).
#   nohup setsid bash repair_purge_20261128.sh > repair_purge_20261128.log 2>&1 &
set -eo pipefail
R=/d0/scratch/choij/micromamba_envs
M=/d0/scratch/choij/micromamba_bin/micromamba
H=/d0/scratch/choij/hcto_prod
# fresh package cache: the purge left partly deleted packages in pkgs/ (would be linked silently)
export CONDA_PKGS_DIRS=$R/pkgs_20261128
SK=/d0/scratch/choij/SKNanoAnalyzer
echo "START $(date)"

lock_from_meta() {  # conda-meta -> explicit lock
    python3 - "$1" <<'PYEOF'
import glob, json, sys
print("# explicit lock rebuilt from conda-meta of", sys.argv[1]); print("@EXPLICIT")
for f in sorted(glob.glob(sys.argv[1] + "/conda-meta/*.json")):
    d = json.load(open(f)); print(f"{d['url']}#{d['md5']}")
PYEOF
}
check_lock() {  # $1 env name, $2 lock
    grep '^https' "$2" | sed 's|.*/||; s|\.conda#.*||; s|\.tar\.bz2#.*||' | LC_ALL=C sort > /tmp/lock_$$.txt
    ls $R/envs/$1/conda-meta/*.json | sed 's|.*/||; s|\.json$||' | LC_ALL=C sort > /tmp/inst_$$.txt
    echo "$1: lock $(wc -l < /tmp/lock_$$.txt) installed $(wc -l < /tmp/inst_$$.txt) differ $(LC_ALL=C comm -3 /tmp/lock_$$.txt /tmp/inst_$$.txt | wc -l)"
    rm -f /tmp/lock_$$.txt /tmp/inst_$$.txt
}

# 1-2. environments
[ -d $R/envs/NanoV15_purged_20261128 ] || lock_from_meta $R/envs/NanoV15 > $H/NanoV15_knu_explicit.txt
for e in Nano NanoV15; do
    lock=$H/sknano_Nano_knu_explicit.txt; [ $e = NanoV15 ] && lock=$H/NanoV15_knu_explicit.txt
    [ -d $R/envs/${e}_purged_20261128 ] || mv $R/envs/$e $R/envs/${e}_purged_20261128
    [ -d $R/envs/$e ] || "$M" create -y -r $R -n $e --file $lock
    check_lock $e $lock
done
"$M" run -r $R -n Nano python -c "import ROOT, correctionlib; print('Nano ROOT', ROOT.gROOT.GetVersion())"
"$M" run -r $R -n Nano root-config --version
"$M" run -r $R -n NanoV15 python -c "import ROOT, uproot, numpy, correctionlib, yaml; print('NanoV15 ROOT', ROOT.gROOT.GetVersion(), 'uproot', uproot.__version__)"

# 3-4. SKNano externals
cd $SK && { set +e; source setup.sh > /dev/null 2>&1; set -e; }
export SKNANO_HOME=$SK
if [ ! -f external/libtorch/lib/libtorch.so ]; then
    rm -rf external/libtorch
    bash scripts/install_libtorch.sh
fi
ls -la external/libtorch/lib/libtorch.so external/libtorch/build-version
cat external/libtorch/build-version
cd $SK/external/lhapdf/data
for s in NNPDF31_nnlo_hessian_pdfas NNPDF31_nlo_hessian_pdfas; do
    if [ ! -f $s/$s.info ]; then
        rm -rf $s
        wget --no-verbose https://lhapdfsets.web.cern.ch/current/$s.tar.gz -O $s.tar.gz
        tar xf $s.tar.gz && rm -f $s.tar.gz
    fi
    echo "$s: $(ls $s | wc -l) files"
done

# 5. SKNano build
cd $SK
rc=0; ./scripts/build.sh > $H/build_repair.log 2>&1 || rc=$?
echo "BUILD_RC=$rc $(date)"
tail -3 $H/build_repair.log
echo "REPAIR_DONE $(date)"
