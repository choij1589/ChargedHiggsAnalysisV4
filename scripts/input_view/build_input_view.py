#!/usr/bin/env python3
"""Build the SKNano input view of the KNU RNTuples (docs/PLAN.md, step 0.2).

SKNano resolves inputs below $SKNANO_INPUT_ROOT as (python/sample_paths.py)

    MC/signal: <era>/<PD>/**/*.root
    data:      <era>/<PD>/*_Run<era><X>_*/**/*.root   (+ "_vN" suffix = reprocessing)

while RNTuplizer writes flat /pnfs/.../RNTuple/<sample>/rntpl_NNN.root. This
script creates a tree of symlinks on /d0 in the SKNano layout, from RNTuplizer's
own records, without listing or reading /pnfs (a hard NFS mount that can hang):

    <root>/<era>/<sample>/rntpl_NNN.root                                   MC, signal
    <root>/<era>/<PD>/crab_DATA_<era>_<PD>_Run<era><X>_NANOv15[_sfx]/rntpl_NNN.root   data

An output is linked only if conversion.csv says ok and its latest
validation.csv row says ok. The data period comes from the CRAB task of
the output's single source file (groups.csv). The new tree is built next to the
old one and swapped in by rename; existing trees are kept as <root>.prev.

Runs with the system python3 (no ROOT needed).

Usage: build_input_view.py --results /d0/scratch/choij/RNTuplizer/results \
           --root /d0/scratch/choij/SKNanoInput/NanoAODv15_RNTuple --era 2024 [--dry-run]
"""
import argparse
import csv
import os
import re
import shutil
import sys
import time

DATA_TASK_RE = re.compile(r"crab_DATA_(\d{4})_(\w+?)_Run(\d{4})([A-Z])(?:_(\w+))?$")


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def sample_kind(sample, first_input):
    if "/SampleFactory/" in first_input:
        return "signal"
    task = first_input.split(f"/{sample}/", 1)[1].split("/", 1)[0]
    return "data" if task.startswith("crab_DATA_") else "mc"


def data_dir(sample, task, era):
    m = DATA_TASK_RE.match(task)
    if not m or m.group(2) != sample or m.group(1) != era or m.group(3) != era:
        raise ValueError(f"unexpected data CRAB task '{task}' for {sample}")
    suffix = f"_{m.group(5)}" if m.group(5) else ""
    return f"crab_DATA_{era}_{sample}_Run{era}{m.group(4)}_NANOv15{suffix}"


def plan_sample(results, sample, era, signal_root=None):
    """Return [(relative link path, target, kind)] for one sample, or raise.

    signal_root: the signal outputs were regrouped by hand on 2026-11-16 from
    RNTuple/<mp>/ to RNTuple/TTToHcToWA_AToMuMu/<mp>/ while RNTuplizer's records
    keep the old path; signal targets are rebased onto this root.
    """
    base = os.path.join(results, sample, "rntuple")
    conv = {r["output"]: r for r in read_rows(os.path.join(base, "conversion.csv"))}
    val = {}
    for r in read_rows(os.path.join(base, "validation.csv")):
        val[r["output"]] = r  # last row wins (latest validation run)
    groups = {}
    for r in read_rows(os.path.join(base, "groups.csv")):
        groups.setdefault(r["output"], []).append(r["input"])

    links = []
    for out, c in conv.items():
        # "superseded" names where an OLDER file was moved when this conversion
        # replaced it; the row itself describes the current output.
        if c["status"] != "ok":
            continue
        v = val.get(out)
        if v is None or v["ok"] != "1":
            raise ValueError(f"{out}: converted but not validated ok")
        inputs = groups.get(out)
        if not inputs:
            raise ValueError(f"{out}: no provenance in groups.csv")
        kind = sample_kind(sample, inputs[0])
        name = os.path.basename(out)
        if kind == "data":
            tasks = {i.split(f"/{sample}/", 1)[1].split("/", 1)[0] for i in inputs}
            if len(tasks) != 1:
                raise ValueError(f"{out}: sources from several CRAB tasks {sorted(tasks)}")
            rel = os.path.join(era, sample, data_dir(sample, tasks.pop(), era), name)
        else:
            rel = os.path.join(era, sample, name)
        target = out
        if kind == "signal" and signal_root:
            target = os.path.join(signal_root, sample, name)
        links.append((rel, target, kind))
    if not links:
        raise ValueError(f"{sample}: no converted outputs")
    if links[0][2] == "signal" and signal_root:
        # 23 small directories: listing them is cheap and catches a wrong rebase.
        present = set(os.listdir(os.path.join(signal_root, sample)))
        missing = [os.path.basename(t) for _, t, _ in links if os.path.basename(t) not in present]
        if missing or len(present) != len(links):
            raise ValueError(f"{sample}: {len(present)} files under signal root, "
                             f"{len(links)} recorded, missing {missing[:3]}")
    return links


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--era", required=True)
    ap.add_argument("--signal-root", default=None,
                    help="where the signal masspoint directories actually are "
                         "(e.g. /pnfs/.../RNTuple/TTToHcToWA_AToMuMu); default: RNTuplizer's recorded path")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    samples = sorted(d for d in os.listdir(args.results)
                     if os.path.isfile(os.path.join(args.results, d, "rntuple", "conversion.csv")))
    plan, errors, counts = [], [], {}
    for s in samples:
        try:
            links = plan_sample(args.results, s, args.era, args.signal_root)
        except (ValueError, KeyError, OSError) as e:
            errors.append(f"{s}: {e}")
            continue
        plan.extend(links)
        counts[s] = (links[0][2], len(links))
    if errors:
        sys.exit("ERROR, nothing written:\n  " + "\n  ".join(errors))

    rels = [r for r, _, _ in plan]
    if len(rels) != len(set(rels)):
        sys.exit("ERROR: duplicate link paths in the plan")
    by_kind = {}
    for kind, n in counts.values():
        by_kind[kind] = (by_kind.get(kind, (0, 0))[0] + 1, by_kind.get(kind, (0, 0))[1] + n)
    for kind, (ns, nf) in sorted(by_kind.items()):
        print(f"{kind:7s} {ns:4d} samples {nf:7d} files")
    if args.dry_run:
        for rel, tgt, _ in plan[:5]:
            print(f"  {rel} -> {tgt}")
        return

    root = os.path.abspath(args.root)
    stage = f"{root}.new.{time.strftime('%Y%m%d_%H%M%S')}"
    for rel, tgt, _ in plan:
        link = os.path.join(stage, rel)
        os.makedirs(os.path.dirname(link), exist_ok=True)
        os.symlink(tgt, link)
    if os.path.lexists(root):
        prev = f"{root}.prev"
        if os.path.lexists(prev):
            shutil.rmtree(prev)  # only ever a tree of symlinks built by this script
        os.rename(root, prev)
    os.rename(stage, root)
    print(f"view at {root} ({len(plan)} links)")


if __name__ == "__main__":
    main()
