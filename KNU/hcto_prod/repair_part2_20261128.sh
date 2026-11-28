#!/bin/bash
# Stage 2 of the purge repair (2026-11-28 08:15; KNU downtime from 20:00, user: wrap up before 18:00).
# repair_purge_20261128.sh is stopped after its Nano install (the running micromamba create finishes); this
# stage reorders the rest so the production starts as early as possible:
#   wait for Nano -> check it -> libtorch, NNPDF31 sets -> SKNano build -> submit_final_btageff.sh -> NanoV15.
#   nohup setsid bash repair_part2_20261128.sh > repair_part2_20261128.log 2>&1 &
set -eo pipefail
R=/d0/scratch/choij/micromamba_envs
M=/d0/scratch/choij/micromamba_bin/micromamba
H=/d0/scratch/choij/hcto_prod
SK=/d0/scratch/choij/SKNanoAnalyzer
export CONDA_PKGS_DIRS=$R/pkgs_20261128
echo "START $(date)"
while pgrep -u choij -f "[m]icromamba create -y -r $R -n Nano " > /dev/null; do sleep 20; done
echo "Nano create finished $(date)"
lockn=$(grep -c '^https' $H/sknano_Nano_knu_explicit.txt); inst=$(ls $R/envs/Nano/conda-meta/*.json | wc -l)
echo "Nano: lock $lockn installed $inst"
[ "$lockn" = "$inst" ] || { echo "ERROR: Nano incomplete"; exit 1; }
"$M" run -r $R -n Nano python -c "import ROOT, correctionlib, encodings; print('Nano ROOT', ROOT.gROOT.GetVersion())"
"$M" run -r $R -n Nano root-config --version

cd $SK && { set +e; source setup.sh > /dev/null 2>&1; set -e; }
export SKNANO_HOME=$SK
if [ ! -f external/libtorch/lib/libtorch.so ]; then
    rm -rf external/libtorch
    bash scripts/install_libtorch.sh
fi
ls -la external/libtorch/lib/libtorch.so; cat external/libtorch/build-version
cd $SK/external/lhapdf/data
for s in NNPDF31_nnlo_hessian_pdfas NNPDF31_nlo_hessian_pdfas; do
    if [ ! -f $s/$s.info ]; then
        rm -rf $s
        wget --no-verbose https://lhapdfsets.web.cern.ch/current/$s.tar.gz -O $s.tar.gz
        tar xf $s.tar.gz && rm -f $s.tar.gz
    fi
    echo "$s: $(ls $s | wc -l) files"
done
cd $SK
rc=0; ./scripts/build.sh > $H/build_repair.log 2>&1 || rc=$?
echo "BUILD_RC=$rc $(date)"; tail -3 $H/build_repair.log
[ $rc = 0 ] || exit 1
git -C $SK log --oneline -1

cd $H && bash submit_final_btageff.sh > submit_final_btageff.log 2>&1
echo "SUBMIT_DONE $(date)"; cat submit_final_btageff.log

# NanoV15 (our scripts; not needed by the SKNano jobs)
[ -d $R/envs/NanoV15_purged_20261128 ] || { python3 - $R/envs/NanoV15 > $H/NanoV15_knu_explicit.txt <<'PYEOF'
import glob, json, sys
print("# explicit lock rebuilt from conda-meta of", sys.argv[1]); print("@EXPLICIT")
for f in sorted(glob.glob(sys.argv[1] + "/conda-meta/*.json")):
    d = json.load(open(f)); print(f"{d['url']}#{d['md5']}")
PYEOF
mv $R/envs/NanoV15 $R/envs/NanoV15_purged_20261128; }
[ -d $R/envs/NanoV15 ] || "$M" create -y -r $R -n NanoV15 --file $H/NanoV15_knu_explicit.txt > $H/nanov15_create.log 2>&1
echo "NanoV15: lock $(grep -c '^https' $H/NanoV15_knu_explicit.txt) installed $(ls $R/envs/NanoV15/conda-meta/*.json | wc -l)"
"$M" run -r $R -n NanoV15 python -c "import ROOT, uproot, numpy, correctionlib, yaml; print('NanoV15 ROOT', ROOT.gROOT.GetVersion(), 'uproot', uproot.__version__)"
echo "REPAIR2_DONE $(date)"
