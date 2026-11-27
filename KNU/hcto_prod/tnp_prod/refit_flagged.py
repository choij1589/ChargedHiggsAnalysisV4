#!/usr/bin/env python3
"""Refit the bins flagged by tnp_tamsa's checkFitStatus.py and keep the refits that pass.

  refit_flagged.py --check-dir DIR [--configs NAME,...] [--apply]

For each production result tnp_tamsa/results/<settings>/<config> with a checker
report DIR/<config>.txt:
  1. the "DATA/SIM bins to refit" are refitted on condor with likelihood
     offsetting (TNP_ROOFIT_OFFSET=initial), into WORK/<settings>/<config>/
     (fits only; the production histograms are symlinked, the configs are the
     production ones through config/HcToWA_fittest.py with TNP_FITTEST_OUT);
  2. a candidate directory = copy of the production fit files with the refits
     swapped in is checked with checkFitStatus.py (on condor);
  3. a refit is accepted if its bin/member is no longer in the candidate's refit
     list; the rest keep the production fit and are reported.
  --apply: for accepted refits, the production bin file is moved to
  fits_<kind>.d.orig/<member>/ and replaced by the refit, then
  `tnp_tamsa.py --step sum` rebuilds efficiency.root (summary only, light).
Writes WORK/<config>.summary.txt. Orchestration only: fits and checks run on
condor; the login node only copies small files and waits.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

TNP = "/d0/scratch/choij/tnp_tamsa"
WORK = "/d0/scratch/choij/hcto_prod/tnp_refit"
SETTINGS = {"Muon": "HcToWA_Muon_2024", "Electron": "HcToWA_Electron_2024", "MuonTrig": "HcToWA_MuonTrig_2024"}
ENV = "cd {tnp} && export TNP_ENV=nanov15 && source setup.sh".format(tnp=TNP)


def settings_of(config):
    if "Leg" in config:  # dimuon trigger legs, e.g. NUM_Mu17Leg1_DEN_HcToWATight_2024
        return SETTINGS["MuonTrig"]
    return SETTINGS["Muon"] if "Muons" in config else SETTINGS["Electron"]


def parse_refit_list(report):
    """{(kind, member): [bins]} from a checkFitStatus report."""
    out, kind = {}, None
    for line in open(report):
        line = line.strip()
        if line.startswith("DATA bins to refit"):
            kind = "data"
        elif line.startswith("SIM bins to refit"):
            kind = "sim"
        elif kind and re.match(r"^bin\d+/s\d+m\d+$", line):
            b, m = line.split("/")
            out.setdefault((kind, m), []).append(int(b[3:]))
    return out


def run(cmd):
    print("+", cmd, flush=True)
    return subprocess.run(["bash", "-c", cmd]).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-dir", required=True)
    ap.add_argument("--configs", default="")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    reports = sorted(f for f in os.listdir(args.check_dir) if f.startswith("NUM_") and f.endswith(".txt"))
    configs = [f[:-4] for f in reports]
    if args.configs:
        configs = [c for c in configs if c in args.configs.split(",")]
    os.makedirs(WORK + "/logs", exist_ok=True)

    # 1. refit jobs
    jobs, todo = [], {}
    for c in configs:
        s = settings_of(c)
        flagged = parse_refit_list(os.path.join(args.check_dir, c + ".txt"))
        todo[c] = flagged
        out = os.path.join(WORK, "refit", s, c)
        if os.path.isdir(out):
            shutil.rmtree(out)
        os.makedirs(out)
        prod = os.path.join(TNP, "results", s, c)
        for h in os.listdir(prod):
            if h.startswith("hists_") and h.endswith(".root"):
                os.symlink(os.path.join(prod, h), os.path.join(out, h))
        for (kind, m), bins in sorted(flagged.items()):
            iset, imem = m[1:].split("m")
            jobs.append("{} {} {} {} {} {}".format(os.path.join(WORK, "refit", s), c, iset, imem, kind, ",".join(map(str, sorted(bins)))))
    if not jobs:
        print("nothing to refit")
        return
    script = os.path.join(WORK, "refit_job.sh")
    open(script, "w").write('''#!/bin/bash
# refit_job.sh OUTDIR CONFIG SET MEMBER KIND BINS
{env}
export TNP_FITTEST_OUT=$1 TNP_ROOFIT_OFFSET=initial
python3 tnp_tamsa.py config/HcToWA_fittest.py $2 --step fit --set $3 --member $4 --$5 --bin $6 --no-condor > /dev/null 2>&1
echo "rc=$?"
'''.format(env=ENV))
    os.chmod(script, 0o755)
    jds = os.path.join(WORK, "refit.jds")
    open(jds, "w").write("executable = {s}\noutput = {w}/logs/refit.$(ClusterId).$(ProcId).out\nerror = {w}/logs/refit.$(ClusterId).$(ProcId).err\nlog = {w}/logs/refit.log\nrequest_memory = 2000\njobbatchname = tnp_refit\nqueue arguments from (\n{j}\n)\n".format(s=script, w=WORK, j="\n".join(jobs)))
    if os.path.exists(WORK + "/logs/refit.log"):
        os.remove(WORK + "/logs/refit.log")
    if run("condor_submit {} && condor_wait {}/logs/refit.log".format(jds, WORK)) != 0:
        sys.exit("refit jobs failed to run")

    # 2. candidate directories and check
    cand_root = os.path.join(WORK, "candidate")
    if os.path.isdir(cand_root):
        shutil.rmtree(cand_root)
    for c in configs:
        s = settings_of(c)
        prod, ref, cand = [os.path.join(r, s, c) for r in (os.path.join(TNP, "results"), os.path.join(WORK, "refit"), cand_root)]
        os.makedirs(cand)
        for h in os.listdir(prod):
            if h.startswith("hists_") and h.endswith(".root"):
                os.symlink(os.path.join(prod, h), os.path.join(cand, h))
        for kind in ("data", "sim"):
            shutil.copytree(os.path.join(prod, "fits_%s.d" % kind), os.path.join(cand, "fits_%s.d" % kind),
                            ignore=shutil.ignore_patterns("*.out", "*.err", "*.log", "*.sh", "*.jds"))
        for (kind, m), bins in todo[c].items():
            for b in bins:
                src = os.path.join(ref, "fits_%s.d" % kind, m, "bin%d.root" % b)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(cand, "fits_%s.d" % kind, m, "bin%d.root" % b))
    chk = os.path.join(WORK, "check_candidate.sh")
    open(chk, "w").write('''#!/bin/bash
{env}
for d in {root}/*/*; do python3 python/checkFitStatus.py $d > {w}/candidate_$(basename $d).txt 2>&1; done
'''.format(env=ENV, root=cand_root, w=WORK))
    os.chmod(chk, 0o755)
    if run("cd {w} && env -i HOME=$HOME PATH=/usr/bin:/bin condor_run -a jobbatchname=tnp_refit_check {c}".format(w=WORK, c=chk)) != 0:
        sys.exit("candidate check failed")

    # 3. decide, 4. apply
    for c in configs:
        s = settings_of(c)
        still = parse_refit_list(os.path.join(WORK, "candidate_%s.txt" % c))
        still_set = {(k, m, b) for (k, m), bins in still.items() for b in bins}
        accepted, rejected = [], []
        for (kind, m), bins in sorted(todo[c].items()):
            for b in sorted(bins):
                ok = os.path.exists(os.path.join(WORK, "refit", s, c, "fits_%s.d" % kind, m, "bin%d.root" % b)) and (kind, m, b) not in still_set
                (accepted if ok else rejected).append((kind, m, b))
        new_flags = sorted(still_set - {(k, m, b) for (k, m), bins in todo[c].items() for b in bins})
        lines = ["{}: flagged {}, refit accepted {}, still flagged {}".format(c, len(accepted) + len(rejected), len(accepted), len(rejected))]
        lines += ["  accepted   {} bin{}/{}".format(k, b, m) for k, m, b in accepted]
        lines += ["  rejected   {} bin{}/{}".format(k, b, m) for k, m, b in rejected]
        lines += ["  NEW FLAG   {} bin{}/{} (not flagged before; check)".format(k, b, m) for k, m, b in new_flags]
        open(os.path.join(WORK, c + ".summary.txt"), "w").write("\n".join(lines) + "\n")
        print(lines[0], flush=True)
        if args.apply and accepted:
            prod = os.path.join(TNP, "results", s, c)
            for kind, m, b in accepted:
                orig_dir = os.path.join(prod, "fits_%s.d.orig" % kind, m)
                os.makedirs(orig_dir, exist_ok=True)
                f = os.path.join(prod, "fits_%s.d" % kind, m, "bin%d.root" % b)
                if not os.path.exists(os.path.join(orig_dir, "bin%d.root" % b)):
                    shutil.move(f, os.path.join(orig_dir, "bin%d.root" % b))
                shutil.copy(os.path.join(WORK, "refit", s, c, "fits_%s.d" % kind, m, "bin%d.root" % b), f)
            rc = run("{env} && python3 tnp_tamsa.py config/{s}.py {c} --step sum > {w}/sum_{c}.log 2>&1".format(env=ENV, s=s, c=c, w=WORK))
            print("  applied {} refits, sum rc={}".format(len(accepted), rc), flush=True)


if __name__ == "__main__":
    main()
