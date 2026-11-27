#!/bin/bash
# Local compile check of SKNanoAnalyzer (branch HcToWA_Run3) with the HcToWA analysis module,
# without the KNU /d0 filesystem. It checks that the framework and the analyzers compile and that
# the ROOT dictionaries generate; the libraries the condor jobs use are still built on knu1
# (they carry the KNU environment paths).
#
#   bash scripts/sknano_check_build.sh [--clean] [--jobs N]
#
# Pieces (set up 2026-11-27):
#   - environment ~/micromamba/envs/SKNanoCheck = exact mirror of the KNU SKNano "Nano" environment
#     (config/env/sknano_Nano_knu_explicit.txt; ROOT 6.40.02, GCC 13.3, correctionlib 2.6.4,
#     onnxruntime 1.19.2). Recreate with
#       ~/micromamba/bin/micromamba create -y -p ~/micromamba/envs/SKNanoCheck -f config/env/sknano_Nano_knu_explicit.txt
#   - source: the git clone ~/Sync/workspace/SKNanoAnalyzer_Run3 (branch HcToWA_Run3 of
#     github.com/choij1589/SKNanoAnalyzer); edit HcToWA_Analyzers there, check here, push, then
#     `git pull` on knu1 and build there once.
#   - build, install and the large externals live in ~/.cache/sknano_check (not synced):
#     external/libtorch (2.9.0.dev20250630+cpu, as on KNU), external/RoccoR (sources copied from
#     KNU: the submodule is on CERN GitLab), external/lhapdf/redhat (LHAPDF 6.5.5 built from source
#     with the environment's g++, --disable-python, no PDF sets: not needed to compile).
set -eo pipefail
SRC="${SKNANO_CHECK_SRC:-$HOME/Sync/workspace/SKNanoAnalyzer_Run3}"
WORK="${SKNANO_CHECK_WORK:-$HOME/.cache/sknano_check}"
ENV="${SKNANO_CHECK_ENV:-$HOME/micromamba/envs/SKNanoCheck}"
clean=0
jobs=$(nproc)
while [[ $# -gt 0 ]]; do
    case "$1" in
        --clean) clean=1 ;;
        --jobs) shift; jobs="$1" ;;
        *) echo "unknown option $1" >&2; exit 1 ;;
    esac
    shift
done
[[ -d "$SRC/.git" ]] || { echo "no SKNanoAnalyzer clone at $SRC" >&2; exit 1; }
[[ -x "$ENV/bin/root-config" ]] || { echo "no environment at $ENV" >&2; exit 1; }
[[ -d "$WORK/external/libtorch" && -d "$WORK/external/RoccoR" && -d "$WORK/external/lhapdf/redhat/lib" ]] || { echo "externals missing in $WORK/external" >&2; exit 1; }

eval "$("$HOME/micromamba/bin/micromamba" shell hook -s bash)"
micromamba activate "$ENV"

export SYSTEM=redhat
export SKNANO_HOME="$SRC"
export SKNANO_VERSION="Run3_v15_Run2_v15"
export SKNANO_DATA="$SRC/data/$SKNANO_VERSION"
export SKNANO_PYTHON="$SRC/python"
export SKNANO_BUILDDIR="$WORK/build"
export SKNANO_INSTALLDIR="$WORK/install"
export SKNANO_LIB="$WORK/install/lib"
export SKNANO_ANALYSIS_MODULE_DIRS="$SRC/HcToWA_Analyzers"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$SKNANO_LIB"

# externals: libtorch by symlink; RoccoR copied into the (uninitialized) submodule directory
[[ -e "$SRC/external/libtorch" ]] || ln -s "$WORK/external/libtorch" "$SRC/external/libtorch"
if [[ ! -f "$SRC/external/RoccoR/RoccoR.cc" ]]; then
    cp -a "$WORK/external/RoccoR/." "$SRC/external/RoccoR/"
fi
for f in CMakeLists.txt RoccoR_LinkDef.hpp; do
    [[ -f "$SRC/templates/RoccoR/$f" ]] && cp "$SRC/templates/RoccoR/$f" "$SRC/external/RoccoR/$f"
done
export ROCCOR_PATH="$SRC/external/RoccoR"
export LHAPDF_INCLUDE_DIR="$WORK/external/lhapdf/redhat/include"
export LHAPDF_LIB_DIR="$WORK/external/lhapdf/redhat/lib"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$LHAPDF_LIB_DIR"
export LIBTORCH_INSTALL_DIR="$SRC/external/libtorch"
export LIBTORCH_INCLUDE_DIR="$LIBTORCH_INSTALL_DIR/include"
export LIBTORCH_LIB_DIR="$LIBTORCH_INSTALL_DIR/lib"
export CORRECTION_INCLUDE_DIR="$(correction config --incdir)"
export CORRECTION_LIB_DIR="$(correction config --libdir)"
export JSONPOG_REPO_PATH="$SRC/CMS_corrections"
export ONNXRUNTIME_INCLUDE_DIR="$CONDA_PREFIX/include/onnxruntime/core/session"
export ONNXRUNTIME_LIB_DIR="$CONDA_PREFIX/lib"

cd "$SRC"
args=()
[[ $clean -eq 1 ]] && args+=(--clean)
start=$(date +%s)
BUILD_JOBS="$jobs" ./scripts/build.sh "${args[@]}"
echo "sknano_check_build: OK in $(( $(date +%s) - start )) s ($(git -C "$SRC" log --oneline -1))"
