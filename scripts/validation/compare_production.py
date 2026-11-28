#!/usr/bin/env python3
"""Compare two SKNano productions file by file, and their job performance (docs/PLAN_Optimization.md,
Validation: reference build vs new build on the same input files).

What it checks:

* Files: the ``*.root`` outputs of REF_DIR and NEW_DIR are matched by their path relative to the
  directory (``--recursive`` for the ``--no-hadd`` layout ``<sample>/hists_<i>.root``). Files present
  in one production only are differences.
* Contents: every matched pair goes through ``compare_outputs.py`` (same directory; histograms bin by
  bin, RNTuples entry by entry, the same tolerance options ``--tol-rel``, ``--allow`` ...). One summary
  row per file: status, histograms and RNTuples compared / different, RNTuple entries and on-disk MB
  REF vs NEW, compression of the RNTuple pages.
* Performance (information, not a difference): SKNano's per-job telemetry
  ``<job output>.performance.json`` (SKNanoCore/include/PerformanceTelemetry.h, written by every
  analyzer job next to its output ``hists_<i>.root``: in the run directory
  ``$SKNANO_RUNLOG/<run>/<era>/<sample>/output/`` for hadd runs, where the merge deletes only the ROOT
  shards; next to the published shards in ``$SKNANO_OUTPUT/.../<era>/<sample>/`` for ``--no-hadd`` runs).
  Fields used: ``cpu_seconds`` (std::clock of the job process), ``wall_seconds``, ``peak_rss_kib``
  (getrusage ru_maxrss), ``counters.events_processed``, ``phases.event_total`` / ``rntuple_fill`` /
  ``correction`` seconds. Searched recursively under ``--perf-ref`` / ``--perf-new`` (default REF_DIR /
  NEW_DIR); grouped by sample (the directory of the file, or its parent when that is ``output``) and
  reported per sample: jobs, events, CPU s (sum), CPU s / event, wall s (sum), peak RSS (max over jobs),
  NEW / REF ratios.

Exit code 0 only if every file has a partner and all pairs are identical within the tolerances.

Requires the NanoV15 environment (uproot, awkward, numpy). Comparing a whole production reads every
RNTuple: on KNU run it on a worker (condor_run), not on a login node; a few files on a login node are fine.

Usage:
    compare_production.py REF_DIR NEW_DIR [--pattern GLOB] [--recursive] [--jobs N] [--common-only]
                          [--perf-ref DIR] [--perf-new DIR] [--no-perf] [compare_outputs options]
                          [--json summary.json] [--details DIR]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_outputs as co  # noqa: E402


def find_files(root, pattern, recursive):
    out = {}
    if recursive:
        for d, _, files in os.walk(root):
            for f in files:
                if fnmatch.fnmatch(f, pattern):
                    p = os.path.join(d, f)
                    out[os.path.relpath(p, root)] = p
    else:
        for f in sorted(os.listdir(root)):
            p = os.path.join(root, f)
            if os.path.isfile(p) and fnmatch.fnmatch(f, pattern):
                out[f] = p
    return out


def _one(args):
    rel, ref, new, kw = args
    t0 = time.time()
    try:
        res = co.compare_files(ref, new, **kw)
    except Exception as exc:  # unreadable file etc.
        return rel, {"ref": ref, "new": new, "error": repr(exc), "identical": False, "n_different": 1,
                     "seconds": round(time.time() - t0, 2), "objects": {}, "summary": {},
                     "only_ref": [], "only_new": [], "class_mismatch": [], "dirs_only_ref": [],
                     "dirs_only_new": []}
    return rel, res


def file_row(rel, res):
    s = res.get("summary", {})
    h = s.get("histogram", {})
    r = s.get("rntuple", {})
    ent_r = ent_n = mb_r = mb_n = 0
    comp_r, comp_n = set(), set()
    for o in res.get("objects", {}).values():
        if o.get("type") == "rntuple":
            ent_r += o.get("entries_ref", 0)
            ent_n += o.get("entries_new", 0)
            if "storage_ref" in o:
                mb_r += o["storage_ref"]["bytes_on_disk"] / 1e6
                mb_n += o["storage_new"]["bytes_on_disk"] / 1e6
                comp_r.update(o["storage_ref"]["compression_names"])
                comp_n.update(o["storage_new"]["compression_names"])
    status = "ERROR" if "error" in res else ("same" if res["identical"] and not any(
        c.get("within_tolerance") for c in s.values() if isinstance(c, dict)) else
        ("tol" if res["identical"] else "DIFF"))
    return {"file": rel, "status": status, "hist": f"{h.get('different', 0)}/{h.get('compared', 0)}",
            "rnt": f"{r.get('different', 0)}/{r.get('compared', 0)}", "entries_ref": ent_r, "entries_new": ent_n,
            "mb_ref": mb_r, "mb_new": mb_n, "comp_ref": ",".join(sorted(comp_r)), "comp_new": ",".join(sorted(comp_n)),
            "extra": len(res.get("only_ref", [])) + len(res.get("only_new", [])) + len(res.get("class_mismatch", [])),
            "seconds": res.get("seconds", 0)}


# ----------------------------------------------------------------------------------------------
# performance telemetry
def find_perf(root):
    out = {}
    if not root or not os.path.isdir(root):
        return out
    for d, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".performance.json"):
                continue
            p = os.path.join(d, f)
            parent = os.path.basename(d)
            sample = os.path.basename(os.path.dirname(d)) if parent == "output" else parent
            try:
                with open(p) as fh:
                    j = json.load(fh)
            except (OSError, ValueError) as exc:
                print(f"warning: cannot read {p}: {exc}", file=sys.stderr)
                continue
            out.setdefault(sample, []).append((f, j))
    return out


def perf_summary(jobs):
    s = {"jobs": len(jobs), "events": 0.0, "cpu": 0.0, "wall": 0.0, "rss_max_mb": 0.0, "event_total": 0.0,
         "rntuple_fill": 0.0, "correction": 0.0, "rss_job": ""}
    for name, j in jobs:
        s["events"] += float(j.get("counters", {}).get("events_processed", 0))
        s["cpu"] += float(j.get("cpu_seconds", 0))
        s["wall"] += float(j.get("wall_seconds", 0))
        rss = float(j.get("peak_rss_kib", -1)) / 1024.0
        if rss > s["rss_max_mb"]:
            s["rss_max_mb"], s["rss_job"] = rss, name
        ph = j.get("phases", {})
        for k in ("event_total", "rntuple_fill", "correction"):
            s[k] += float(ph.get(k, {}).get("seconds", 0))
    s["cpu_per_event_ms"] = 1e3 * s["cpu"] / s["events"] if s["events"] else 0.0
    return s


def _ratio(a, b):
    return b / a if a else float("nan")


def print_perf(pr, pn, stream=sys.stdout):
    w = stream.write
    samples = sorted(set(pr) | set(pn))
    if not samples:
        w("performance: no *.performance.json found\n")
        return {}
    w("performance per sample (CPU and wall: sums over jobs; RSS: max over jobs):\n")
    w(f"  {'sample':44s} {'jobs R/N':>9s} {'events R':>11s} {'events N':>11s} {'CPU s R':>9s} {'CPU s N':>9s} "
      f"{'N/R':>6s} {'ms/ev R':>8s} {'ms/ev N':>8s} {'wall N/R':>8s} {'RSS MB R':>9s} {'RSS MB N':>9s}\n")
    out = {}
    tot = {"cpu_r": 0.0, "cpu_n": 0.0, "wall_r": 0.0, "wall_n": 0.0}
    for smp in samples:
        a = perf_summary(pr.get(smp, []))
        b = perf_summary(pn.get(smp, []))
        out[smp] = {"ref": a, "new": b}
        tot["cpu_r"] += a["cpu"]
        tot["cpu_n"] += b["cpu"]
        tot["wall_r"] += a["wall"]
        tot["wall_n"] += b["wall"]
        flag = " events differ" if a["jobs"] and b["jobs"] and a["events"] != b["events"] else ""
        w(f"  {smp[:44]:44s} {a['jobs']:>4d}/{b['jobs']:<4d} {a['events']:11.0f} {b['events']:11.0f} "
          f"{a['cpu']:9.1f} {b['cpu']:9.1f} {_ratio(a['cpu'], b['cpu']):6.3f} {a['cpu_per_event_ms']:8.3f} "
          f"{b['cpu_per_event_ms']:8.3f} {_ratio(a['wall'], b['wall']):8.3f} {a['rss_max_mb']:9.0f} "
          f"{b['rss_max_mb']:9.0f}{flag}\n")
    w(f"  {'total':44s} {'':9s} {'':11s} {'':11s} {tot['cpu_r']:9.1f} {tot['cpu_n']:9.1f} "
      f"{_ratio(tot['cpu_r'], tot['cpu_n']):6.3f} {'':8s} {'':8s} {_ratio(tot['wall_r'], tot['wall_n']):8.3f}\n")
    return out


# ----------------------------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ref_dir")
    p.add_argument("new_dir")
    p.add_argument("--pattern", default="*.root", help="file name glob (default *.root)")
    p.add_argument("--recursive", action="store_true", help="match files in subdirectories (--no-hadd layout)")
    p.add_argument("--jobs", type=int, default=1, help="files compared in parallel (default 1)")
    p.add_argument("--perf-ref", help="directory searched for REF *.performance.json (default REF_DIR)")
    p.add_argument("--perf-new", help="directory searched for NEW *.performance.json (default NEW_DIR)")
    p.add_argument("--no-perf", action="store_true", help="skip the performance telemetry")
    p.add_argument("--common-only", action="store_true",
                   help="files present in one directory only are listed but not counted as differences")
    p.add_argument("--no-contents", action="store_true", help="only the performance telemetry")
    p.add_argument("--json", help="write the summary (and the non-identical objects) as JSON")
    p.add_argument("--details", help="directory for one compare_outputs text report per differing file")
    co.add_common_args(p)
    a = p.parse_args(argv)

    rc = 0
    summary = {"ref_dir": a.ref_dir, "new_dir": a.new_dir, "files": {}, "only_ref": [], "only_new": []}
    if not a.no_contents:
        fr = find_files(a.ref_dir, a.pattern, a.recursive)
        fn = find_files(a.new_dir, a.pattern, a.recursive)
        summary["only_ref"] = sorted(set(fr) - set(fn))
        summary["only_new"] = sorted(set(fn) - set(fr))
        common = sorted(set(fr) & set(fn))
        kw = dict(tol_rel=a.tol_rel, tol_abs=a.tol_abs, allow=a.allow,
                  key=[k for k in a.key.split(",") if k], chunk_size=a.chunk_size, max_report=a.max_report,
                  only=a.only, skip=a.skip, tiebreak=a.tiebreak)
        tasks = [(rel, fr[rel], fn[rel], kw) for rel in common]
        results = {}
        t0 = time.time()
        if a.jobs > 1:
            with concurrent.futures.ProcessPoolExecutor(max_workers=a.jobs) as ex:
                for rel, res in ex.map(_one, tasks):
                    results[rel] = res
                    print(f"  done {rel}: {'identical' if res['identical'] else 'DIFFERENT'}", flush=True)
        else:
            for t in tasks:
                rel, res = _one(t)
                results[rel] = res
                print(f"  done {rel}: {'identical' if res['identical'] else 'DIFFERENT'}", flush=True)
        if a.details:
            os.makedirs(a.details, exist_ok=True)
        print(f"\nREF: {a.ref_dir}\nNEW: {a.new_dir}")
        for side, items in (("REF", summary["only_ref"]), ("NEW", summary["only_new"])):
            if items:
                rc = rc if a.common_only else 1
                print(f"[{'INFO' if a.common_only else 'DIFF'}] {len(items)} files only in {side}: {', '.join(items[:10])}{' ...' if len(items) > 10 else ''}")
        rows = [file_row(rel, results[rel]) for rel in common]
        print(f"{'file':56s} {'status':6s} {'hist d/n':>10s} {'rnt d/n':>8s} {'entries R':>10s} {'entries N':>10s} "
              f"{'MB R':>8s} {'MB N':>8s} {'comp R':>8s} {'comp N':>8s} {'s':>6s}")
        for r in rows:
            print(f"{r['file'][:56]:56s} {r['status']:6s} {r['hist']:>10s} {r['rnt']:>8s} {r['entries_ref']:10d} "
                  f"{r['entries_new']:10d} {r['mb_ref']:8.2f} {r['mb_new']:8.2f} {r['comp_ref']:>8s} {r['comp_new']:>8s} "
                  f"{r['seconds']:6.1f}" + (f"  +{r['extra']} objects only in one file" if r["extra"] else ""))
        mb_r = sum(r["mb_ref"] for r in rows)
        mb_n = sum(r["mb_new"] for r in rows)
        n_diff = sum(1 for r in rows if r["status"] in ("DIFF", "ERROR"))
        n_tol = sum(1 for r in rows if r["status"] == "tol")
        print(f"{len(rows)} files compared: {len(rows) - n_diff - n_tol} identical, {n_tol} within tolerance, "
              f"{n_diff} different; RNTuples on disk REF {mb_r:.1f} MB, NEW {mb_n:.1f} MB "
              f"(NEW/REF {mb_n / mb_r if mb_r else float('nan'):.3f}); {time.time() - t0:.1f} s")
        for rel in common:
            res = results[rel]
            if not res["identical"]:
                rc = 1
                if "error" in res:
                    print(f"[ERROR] {rel}: {res['error']}")
                if a.details:
                    path = os.path.join(a.details, rel.replace(os.sep, "__") + ".txt")
                    with open(path, "w") as fh:
                        co.print_report(res, a.quiet, a.max_report, stream=fh)
            slim = {k: v for k, v in res.items() if k != "objects"}
            slim["objects"] = {k: v for k, v in res.get("objects", {}).items() if v.get("status") != "identical"
                               or v.get("warnings")}
            slim["row"] = file_row(rel, res)
            summary["files"][rel] = slim
        if rc and a.details:
            print(f"reports of the differing files: {a.details}")
        elif rc:
            print("rerun compare_outputs.py on a differing file (or use --details DIR) for the full report")

    if not a.no_perf:
        print()
        pr = find_perf(a.perf_ref or a.ref_dir)
        pn = find_perf(a.perf_new or a.new_dir)
        summary["performance"] = print_perf(pr, pn)

    print(f"RESULT: {'IDENTICAL (within tolerances)' if rc == 0 else 'DIFFERENT'}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(co._clean_json(summary), fh, indent=1, default=co._json_default)
    return rc


if __name__ == "__main__":
    sys.exit(main())
