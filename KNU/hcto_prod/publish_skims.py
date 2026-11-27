#!/usr/bin/env python3
"""Copy finished skims from the /d0 staging area to /pnfs and repoint their metadata.

SKNano's skim writer cannot write to dCache directly (it reopens its output in
UPDATE mode), so skims are produced on /d0/scratch/choij/SKNanoSkim/ and published
here. For every per-sample skim JSON in the module metadata directory
(HcToWA_Analyzers/data/Skim/<era>/Skim_*.json, written by the post-processing job
when a sample is complete) whose files are still on /d0:

  1. copy each file to /pnfs/.../store/user/choij/SKNanoSkim/<same relative path>
     with xrdcp, adler32 checksum compared between source and destination;
  2. check that the Events RNTuple has the same number of entries in both copies
     (destination read over xrootd);
  3. rewrite the JSON 'path' list to the /pnfs paths (atomic replace);
  4. remove the /d0 files unless --keep-staging. Once no skim job is left in the
     queue, provenance.json files are copied too and empty staging directories removed.

A file already present on /pnfs with the same size and entry count is not copied
again, so the script can be rerun at any time. Nothing on /pnfs is ever deleted.

Checks: per file, checksum (xrdcp) and entry count; per sample, that the JSON
lists at least one file. Runs on a KNU login node with a valid CMS proxy, in the
NanoV15 environment (needs PyROOT); Python 3.9 compatible.

  python publish_skims.py [--era 2024] [--dry-run] [--keep-staging] [--loop MINUTES]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

STAGE = "/d0/scratch/choij/SKNanoSkim/"
PNFS = "/pnfs/knu.ac.kr/data/cms/store/user/choij/SKNanoSkim/"
XROOTD = "root://cluster142.knu.ac.kr//store/user/choij/SKNanoSkim/"
META = "/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/data/Skim"


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def entries(url):
    import ROOT
    reader = ROOT.RNTupleReader.Open("Events", url)
    return int(reader.GetNEntries())


def copy_one(src, dry):
    rel = os.path.relpath(src, STAGE)
    dst_pnfs, dst_url = PNFS + rel, XROOTD + rel
    n_src = entries(src)
    if os.path.exists(dst_pnfs) and os.path.getsize(dst_pnfs) == os.path.getsize(src):
        if entries(dst_url) == n_src:
            return dst_pnfs, n_src, "present"
    if dry:
        return dst_pnfs, n_src, "would copy"
    cmd = ["xrdcp", "--force", "--path", "--cksum", "adler32:source", "--nopbar", src, dst_url]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if res.returncode != 0:
        raise RuntimeError("xrdcp failed for %s: %s" % (src, res.stdout.strip()[-400:]))
    n_dst = entries(dst_url)
    if n_dst != n_src:
        raise RuntimeError("entry mismatch for %s: %d on /d0, %d on /pnfs" % (src, n_src, n_dst))
    return dst_pnfs, n_src, "copied"


def publish(js, dry, keep):
    with open(js) as f:
        info = json.load(f)
    paths = info.get("path", [])
    if not paths:
        log("WARNING %s lists no files; skipped" % os.path.basename(js))
        return False
    if all(p.startswith(PNFS) for p in paths):
        return False
    new_paths, total = [], 0
    for p in paths:
        if p.startswith(PNFS):
            new_paths.append(p)
            continue
        if not p.startswith(STAGE):
            raise RuntimeError("%s: unexpected path %s" % (js, p))
        dst, n, what = copy_one(p, dry)
        new_paths.append(dst)
        total += n
    log("%s: %d files, %d entries%s" % (info.get("name", js), len(paths), total, " (dry run)" if dry else ""))
    if dry:
        return True
    info["path"] = new_paths
    tmp = js + ".tmp"
    with open(tmp, "w") as f:
        json.dump(info, f, indent=4)
    os.replace(tmp, js)
    if not keep:
        for p in paths:
            if p.startswith(STAGE) and os.path.exists(p):
                os.remove(p)
                for side in (".errors.summary.json", ".performance.json"):
                    if os.path.exists(p + side):
                        os.remove(p + side)
    return True


def final_cleanup(era, dry):
    """After the last skim job: copy each provenance.json to /pnfs and remove empty
    staging directories. Not done earlier: SKNano creates the data target directory
    Skim_TriLep_<PD> at submission, and a later period's post-processing needs it
    to exist (otherwise its mv renames instead of nesting)."""
    for root in sorted(glob.glob(os.path.join(STAGE, era, "*", "Skim", "*", "Skim_*"))):
        has_root = any(f.endswith(".root") for _, _, fs in os.walk(root) for f in fs)
        prov = os.path.join(root, "provenance.json")
        if has_root or not os.path.exists(prov):
            continue
        if dry:
            log("would publish %s" % prov)
            continue
        rel = os.path.relpath(prov, STAGE)
        subprocess.run(["xrdcp", "--force", "--path", "--nopbar", prov, XROOTD + rel], check=True)
        os.remove(prov)
    if dry:
        return
    for d, _, _ in sorted(os.walk(os.path.join(STAGE, era)), key=lambda t: len(t[0]), reverse=True):
        if os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)


def one_pass(era, dry, keep):
    done = 0
    for js in sorted(glob.glob(os.path.join(META, era, "Skim_*.json"))):
        try:
            done += publish(js, dry, keep)
        except Exception as exc:  # report and continue with the other samples
            log("ERROR %s: %s" % (os.path.basename(js), exc))
    return done


def skim_jobs_running():
    res = subprocess.run(["condor_q", os.environ.get("USER", "choij"), "-af", "JobBatchName"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
    return any("Skim_TriLep" in line for line in res.stdout.splitlines())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--era", default="2024")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-staging", action="store_true")
    ap.add_argument("--loop", type=float, default=0, help="repeat every MINUTES until no skim job is left in the queue")
    args = ap.parse_args()
    while True:
        n = one_pass(args.era, args.dry_run, args.keep_staging)
        log("pass done: %d samples published" % n)
        if not args.loop or not skim_jobs_running():
            if args.loop:
                n = one_pass(args.era, args.dry_run, args.keep_staging)
                log("final pass: %d samples published" % n)
            if not skim_jobs_running() and not args.keep_staging:
                final_cleanup(args.era, args.dry_run)
                log("staging cleaned up")
            break
        time.sleep(60 * args.loop)


if __name__ == "__main__":
    sys.exit(main())
