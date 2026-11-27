"""Apply the KNU stage-out patch to SKNano (run on knu1 in the SKNano checkout)."""
import re
def patch(path, subs):
    s = open(path).read()
    for old, new in subs:
        assert s.count(old) == 1, (path, old[:70])
        s = s.replace(old, new)
    open(path, "w").write(s)

# --- run.sh: jobs with an output on /pnfs write locally and stage out
patch("templates/run.sh", [(
'''cd "$run_dir"

root -l -b -q job_$1.cc
exit $?
''',
'''# Local patch (KNU, 2026-11-25): stage-out. A job whose output path is under
# SKNANO_STAGEOUT_PREFIX (/pnfs) writes it on the node's local disk and copies it
# there with scripts/sknano_stageout.sh at the end (dCache over NFS is write-once,
# and the skim writer reopens its output).
final_out=$(grep -o 'SetOutfilePath("[^"]*")' "$run_dir/job_$1.cc" | head -1 | sed 's/^SetOutfilePath("//; s/")$//')
stageout=""
if [[ -n "$final_out" && "$final_out" == "${SKNANO_STAGEOUT_PREFIX:-/pnfs/knu.ac.kr/data/cms/}"* ]]; then
    if [[ "$run_dir" != "$stage" ]]; then
        echo "run.sh: the output is on /pnfs but the local stage failed" >&2
        exit 1
    fi
    mkdir -p "$stage/out"
    local_out="$stage/out/$(basename "$final_out")"
    sed -i "s|SetOutfilePath(\\"$final_out\\")|SetOutfilePath(\\"$local_out\\")|" "$run_dir/job_$1.cc"
    stageout=1
fi

cd "$run_dir"

root -l -b -q job_$1.cc
rc=$?
if [[ $rc -eq 0 && -n "$stageout" ]]; then
    "$SKNANO_HOME/scripts/sknano_stageout.sh" "$local_out" "$final_out" || exit 1
    for side in .errors.summary.json .performance.json; do
        if [[ -f "$local_out$side" ]]; then
            "$SKNANO_HOME/scripts/sknano_stageout.sh" "$local_out$side" "$final_out$side" || exit 1
        fi
    done
fi
exit $rc
''')])

# --- hadd.sh: merge on the node, then stage out target and provenance
patch("templates/hadd.sh", [(
'''python3 "[SKNANO_HOME]/scripts/sknano_merge.py" \\
  --output [TARGET] --mode [MERGE_MODE] [MODE_ARGS] \\''',
'''# Local patch (KNU, 2026-11-25): merge into the node's local disk, then stage
# the result out to [TARGET] (scripts/sknano_stageout.sh).
local_dir="${_CONDOR_SCRATCH_DIR:-$(mktemp -d)}/sknano_merge_out"
mkdir -p "$local_dir"
local_target="$local_dir/$(basename [TARGET])"
python3 "[SKNANO_HOME]/scripts/sknano_merge.py" \\
  --output "$local_target" --mode [MERGE_MODE] [MODE_ARGS] \\'''),
('''cp [PROVENANCE] [TARGET_PROVENANCE]''',
'''"[SKNANO_HOME]/scripts/sknano_stageout.sh" "$local_target" [TARGET]
"[SKNANO_HOME]/scripts/sknano_stageout.sh" [PROVENANCE] [TARGET_PROVENANCE]''')])

# --- move.sh (--no-hadd): jobs already published to the target directory
open("templates/move.sh", "w").write('''#!/bin/bash
set -euo pipefail
# Local patch (KNU, 2026-11-25): with the stage-out patch the analyzer jobs of a
# --no-hadd run write their outputs directly to [TARGETDIR] (run.sh). This node
# stages out any output still in the run directory (older layout), checks that
# the target holds outputs, and publishes the provenance.

cd "[WORKDIR]"
shopt -s nullglob
for f in output/hists_*.root; do
  "[SKNANO_HOME]/scripts/sknano_stageout.sh" "$f" "[TARGETDIR]/$(basename "$f")"
  rm -f -- "$f"
done
published=("[TARGETDIR]"/hists_*.root)
if (( ${#published[@]} == 0 )); then
  echo "No analyzer outputs in [TARGETDIR]" >&2
  exit 1
fi
"[SKNANO_HOME]/scripts/sknano_stageout.sh" "[PROVENANCE]" "[TARGETDIR]/provenance.json"
''')

p = "python/SKNano.py"
patch(p, [
 # skims: write straight into the final directory (no Temp_ and no mv on /pnfs)
 ('''    suffix = f"Temp_Skim_{skim_suffix}_{sample if isMC else sample.replace(f'_{period}','')}"''',
  '''    # Local patch (KNU, 2026-11-25): written directly into the final Skim_ directory
    # (stage-out to /pnfs; no Temp_ directory renamed on dCache).
    suffix = f"Skim_{skim_suffix}_{sample if isMC else sample.replace(f'_{period}','')}"'''),
 # --no-hadd: jobs publish directly into the sample directory
 ('''        os.makedirs(os.path.join(working_dir,"output"))
        out_base = os.path.join(working_dir,"output","hists.root")''',
  '''        os.makedirs(os.path.join(working_dir,"output"))
        out_base = os.path.join(working_dir,"output","hists.root")
        # Local patch (KNU, 2026-11-25): with --no-hadd each job stages its output out
        # directly to the sample directory under SKNANO_OUTPUT (run.sh).
        if getattr(argparse, 'no_hadd', False):
            out_base = getFinalOutputPath(era, sample, argparse, userflags).replace('hists_*.root', 'hists.root')
            os.makedirs(os.path.dirname(out_base), exist_ok=True)'''),
 # move.sh needs SKNANO_HOME
 ('''    move_content = move_content.replace("[WORKDIR]", working_dir)''',
  '''    move_content = move_content.replace("[WORKDIR]", working_dir)
    move_content = move_content.replace("[SKNANO_HOME]", SKNANO_HOME)'''),
])
# skim post-processing: provenance via stage-out, no mv/rmdir
s = open(p).read()
i = s.index("def makeSkimPostProcsJobs(")
j = s.index("    job_dict = {}", i)
new_body = '''def makeSkimPostProcsJobs(working_dir,sample, argparser,era):
    # Local patch (KNU, 2026-11-25): the skim jobs write into the final Skim_
    # directory on /pnfs (stage-out), so this node only publishes the provenance
    # and writes the skim metadata JSON.
    AnalyzerName = argparser.Analyzer
    userflags = getUserFlagsList(argparser.Userflags)
    skim_suffix = AnalyzerName.replace('Skim_','')
    if len(userflags) > 0:
        skim_suffix += f"_{'_'.join(userflags)}"
    isMC, period = isMCandGetPeriod(sample)
    out_base, suffix = getSkimmingOutBaseAndSuffix(era, sample, AnalyzerName, userflags)
    out_base = os.path.dirname(out_base)
    manifest_path = os.path.join(os.path.dirname(os.path.dirname(working_dir)), RUN_MANIFEST_NAME)
    target_dir = out_base if isMC else os.path.dirname(out_base)
    stageout = os.path.join(SKNANO_HOME, "scripts", "sknano_stageout.sh")
    with open(os.path.join(working_dir,"postproc.sh"),'w') as f:
        f.writelines("#!/bin/bash\\n")
        f.writelines("set -e\\n")
        f.writelines(f"{stageout} {manifest_path} {os.path.join(target_dir, 'provenance.json')}\\n")
        f.writelines(f"cd $SKNANO_PYTHON\\n")
        f.writelines(f"python3 sampleManager.py --era {era} --makeSkimTreeInfo --skimTreeFolder {os.path.dirname(target_dir)} --skimTreeSuffix {skim_suffix} --skimTreeOrigPD {sample}\\n")

'''
s = s[:i] + new_body + s[j:]
open(p, "w").write(s)

# --- proxy for every job type (outputs are written over xrootd)
patch("templates/job_dict.py", [(
"""if 'root://' in os.environ.get('SKNANO_INPUT_URL_MAP', ''):
    main_job['use_x509userproxy'] = 'true'""",
"""if 'root://' in os.environ.get('SKNANO_INPUT_URL_MAP', ''):
    main_job['use_x509userproxy'] = 'true'

# Local patch (KNU, 2026-11-25): outputs under /pnfs are staged out over xrootd
# (scripts/sknano_stageout.sh) by the analyzer, merge, move and skim
# post-processing jobs, which all need the proxy.
_stageout_prefix = os.environ.get('SKNANO_STAGEOUT_PREFIX', '/pnfs/knu.ac.kr/data/cms/')
if any(os.environ.get(k, '').startswith(_stageout_prefix)
       for k in ('SKNANO_OUTPUT', 'SKNANO_RUN3_NANOAODPATH', 'SKNANO_RUN2_NANOAODPATH')):
    for _job in (main_job, hadd_job, partial_merge_job):
        _job['use_x509userproxy'] = 'true'""")])
s = open(p).read()
old = "    job_dict['when_to_transfer_output'] = \"ON_EXIT\"\n\n    return job_dict\n"
assert s.count(old) == 1
s = s.replace(old, "    job_dict['when_to_transfer_output'] = \"ON_EXIT\"\n    job_dict['use_x509userproxy'] = 'true'  # Local patch (KNU): stage-out of provenance\n\n    return job_dict\n")
open(p, "w").write(s)

# --- config: outputs and skims on /pnfs
c = "config/config.choij"
s = open(c).read()
s = re.sub(r"^\[SKNANO_OUTPUT\].*$", "[SKNANO_OUTPUT] /pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoOutput", s, flags=re.M)
s = re.sub(r"^\[SKNANO_RUN3_NANOAODPATH\].*$", "[SKNANO_RUN3_NANOAODPATH] /pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoSkim/", s, flags=re.M)
s = re.sub(r"^\[SKNANO_RUN2_NANOAODPATH\].*$", "[SKNANO_RUN2_NANOAODPATH] /pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoSkim/", s, flags=re.M)
open(c, "w").write(s)
print("stage-out patch applied")
