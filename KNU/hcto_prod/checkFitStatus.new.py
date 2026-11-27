#!/usr/bin/env python3
"""
Check the fits of a tnp_tamsa results directory and list the bins to refit.

  python3 python/checkFitStatus.py <results_directory> [--policy strict|original]
          [--sim-syst-tol 0.01] [--data-syst-tol 0.03]
          [--sim-count-tol 0.01] [--data-count-tol 0.10]

Reads every fits_{data,sim}.d/<sXmY>/bin<N>.root written by fitUtils.tnpFitter
and uses the numbers tnp_tamsa actually reports: the efficiency printed on the
bin canvas ("eff = ..."; the fit efficiency in the fit range, or the count
efficiency for non-fit bins), the count efficiency ("count_eff[...] = ..."),
the stored fit statuses and the RooFitResults (nSigP / nSigF and all floating
parameters).

Criteria (a bin/member failing one is listed under "bins to refit"):
  status     --policy strict (default): status 0 and covQual 3 (full accurate
             covariance) for every pass and fail fit.
             --policy original (the earlier tnp_tamsa rule): data nominal (s0m0)
             status 0; data systematics and sim status 0, 1 or 3; covQual not
             checked.
  limits     a floating shape parameter (anything but the yields nSig*/nBkg*)
             within 0.1% of the parameter range of a limit, or a yield at its
             upper limit.
  syst       |eff(member) - eff(s0m0)| above --sim-syst-tol (0.01) or
             --data-syst-tol (0.03).
  fit-count  sim: |fit eff - count eff| above --sim-count-tol (0.01); the sim
             histograms hold no background beyond non-matched pairs, so a fit
             that departs from the count is suspect.
  missing    a bin file or its fit objects are missing.
Reported as warnings only (not refitted):
  - a yield at its lower limit (e.g. background compatible with zero);
  - data: |fit eff - count eff| above --data-count-tol (0.10); the count
    includes background, so a difference is expected, a large one is worth a look.

The "DATA/SIM bins to refit" lists at the end are parsed by submitRefitJobs.py
(lines "bin<N>/s<X>m<Y>"); note that a refit with an unchanged config repeats
the same fit, so change the fit model or ranges for those bins first.

KNU 2026-11-25 (ChargedHiggsAnalysisV4): rewritten. The earlier version read
yields named numSignalPass/numSignalFail, which fitUtils does not write (it
writes nSigP/nSigF), so every efficiency was 0 and the systematic check never
fired; its printed thresholds (0.05/0.1) also differed from the ones applied
(0.01/0.03).
"""

import argparse
import glob
import os
import re
import sys
from collections import defaultdict

import ROOT as rt

rt.gROOT.SetBatch(True)
rt.gErrorIgnoreLevel = rt.kFatal   # submitRefitJobs.py treats any stderr output as an error

EFF_RE = re.compile(r"eff\s*=\s*([-0-9.eE+]+)\s*#pm\s*([-0-9.eE+]+)")
COUNT_RE = re.compile(r"count_eff\[[^\]]*\]\s*=\s*([-0-9.eE+]+)\s*#pm\s*([-0-9.eE+]+)")


def pave_lines(pave):
    if not pave:
        return []
    return [pave.GetLine(i).GetTitle() for i in range(pave.GetSize())]


def read_bin(path, member):
    """Everything checkFitStatus needs from one bin file, or None if unreadable."""
    if not os.path.exists(path):
        return None
    f = rt.TFile.Open(path)
    if not f or f.IsZombie():
        return None
    try:
        d = f.Get(member)
        if not d:
            return None
        out = {"isFit": False}
        for key in d.GetListOfKeys():
            name = key.GetName()
            if name.endswith("_Canv"):
                pad = key.ReadObj().GetPad(1)
                eff = [EFF_RE.search(l) for l in pave_lines(pad.GetPrimitive("efficiency"))]
                eff = [m for m in eff if m]
                cnt = [COUNT_RE.search(l) for l in pave_lines(pad.GetPrimitive("efficiencies"))]
                cnt = [m for m in cnt if m]
                if eff:
                    out["eff"], out["eff_err"] = float(eff[0].group(1)), float(eff[0].group(2))
                if cnt:
                    out["count_eff"], out["count_err"] = float(cnt[0].group(1)), float(cnt[0].group(2))
            elif name.endswith("_resP") or name.endswith("_resF"):
                res = key.ReadObj()
                side = name[-1]
                out["isFit"] = True
                out["status" + side] = res.status()
                out["covQual" + side] = res.covQual()
                pars = []
                for p in res.floatParsFinal():
                    pars.append((p.GetName(), p.getVal(), p.getError(), p.getMin(), p.getMax()))
                out["pars" + side] = pars
        if "eff" not in out:
            return None
        if out["isFit"] and not all(k in out for k in ("statusP", "statusF")):
            return None
        return out
    finally:
        f.Close()


def is_yield(name):
    return name.startswith("nSig") or name.startswith("nBkg")


def limit_problems(pars, rel=1e-3):
    """(problems, warnings) for parameters at a limit."""
    problems, warnings = [], []
    for name, val, err, lo, hi in pars:
        span = hi - lo
        if not (span > 0) or span > 1e30:
            continue
        at_lo = val - lo < rel * span
        at_hi = hi - val < rel * span
        if not (at_lo or at_hi):
            continue
        tag = "{}={:.4g}+-{:.3g} at {} limit [{:.4g},{:.4g}]".format(name, val, err, "lower" if at_lo else "upper", lo, hi)
        if is_yield(name) and at_lo:
            warnings.append(tag)
        else:
            problems.append(tag)
    return problems, warnings


def status_ok(r, side, policy, is_data, is_nominal):
    s, q = r["status" + side], r["covQual" + side]
    if policy == "strict":
        return s == 0 and q == 3
    if is_data and is_nominal:
        return s == 0
    return s in (0, 1, 3)


def check_kind(results_dir, kind, args, problems, warnings, refit):
    fit_dir = os.path.join(results_dir, "fits_{}.d".format(kind))
    if not os.path.isdir(fit_dir):
        return 0
    is_data = kind == "data"
    members = sorted(d for d in os.listdir(fit_dir) if re.match(r"^s\d+m\d+$", d) and os.path.isdir(os.path.join(fit_dir, d)))
    results = {}
    for m in members:
        for path in glob.glob(os.path.join(fit_dir, m, "bin*.root")):
            b = os.path.basename(path)[:-5]
            results[(m, b)] = read_bin(path, m)
    bins = sorted({b for (_, b) in results}, key=lambda b: int(b[3:]))
    syst_tol = args.data_syst_tol if is_data else args.sim_syst_tol
    nfits = 0
    for m in members:
        for b in bins:
            item = "{}/{}".format(b, m)
            r = results.get((m, b))
            if r is None:
                problems[kind + " missing"].append(item)
                refit[kind].add(item)
                continue
            if r["isFit"]:
                nfits += 1
                for side in "PF":
                    if not status_ok(r, side, args.policy, is_data, m == "s0m0"):
                        problems[kind + " status"].append("{} ({}: status {}, covQual {})".format(item, "pass" if side == "P" else "fail", r["status" + side], r["covQual" + side]))
                        refit[kind].add(item)
                    p, w = limit_problems(r["pars" + side])
                    for x in p:
                        problems[kind + " parameter at limit"].append("{} ({})".format(item, x))
                        refit[kind].add(item)
                    for x in w:
                        warnings[kind + " yield at lower limit"].append("{} ({})".format(item, x))
                if "count_eff" in r:
                    diff = abs(r["eff"] - r["count_eff"])
                    if is_data and diff > args.data_count_tol:
                        warnings["data fit vs count"].append("{} (fit {:.4f}, count {:.4f}, diff {:.4f})".format(item, r["eff"], r["count_eff"], diff))
                    if not is_data and diff > args.sim_count_tol:
                        problems["sim fit vs count"].append("{} (fit {:.4f}, count {:.4f}, diff {:.4f})".format(item, r["eff"], r["count_eff"], diff))
                        refit[kind].add(item)
            nom = results.get(("s0m0", b))
            if m != "s0m0" and nom is not None:
                diff = abs(r["eff"] - nom["eff"])
                if diff > syst_tol:
                    problems[kind + " systematic vs nominal"].append("{} (eff {:.4f}, nominal {:.4f}, diff {:.4f} > {})".format(item, r["eff"], nom["eff"], diff, syst_tol))
                    refit[kind].add(item)
    print("{}: {} members x {} bins, {} fitted bin/members".format(kind.upper(), len(members), len(bins), nfits))
    return nfits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("results_dir")
    ap.add_argument("--policy", choices=["strict", "original"], default="strict")
    ap.add_argument("--sim-syst-tol", type=float, default=0.01)
    ap.add_argument("--data-syst-tol", type=float, default=0.03)
    ap.add_argument("--sim-count-tol", type=float, default=0.01)
    ap.add_argument("--data-count-tol", type=float, default=0.10)
    args = ap.parse_args()
    if not os.path.isdir(args.results_dir):
        print("Directory {} does not exist!".format(args.results_dir))
        sys.exit(1)

    print("Checking fit status in: {}".format(args.results_dir))
    print("=" * 60)
    print("CRITERIA (policy {}):".format(args.policy))
    if args.policy == "strict":
        print("  status: 0 and covQual 3 for every pass and fail fit")
    else:
        print("  status: data nominal 0; data systematics and sim 0, 1 or 3")
    print("  parameters: no shape parameter (or yield) at its upper/lower limit; yields at the lower limit are warnings")
    print("  systematics: |eff - eff(s0m0)| <= {} (sim), {} (data)".format(args.sim_syst_tol, args.data_syst_tol))
    print("  fit vs count: <= {} (sim, refit); > {} (data) is a warning".format(args.sim_count_tol, args.data_count_tol))
    print("=" * 60)

    problems, warnings, refit = defaultdict(list), defaultdict(list), {"data": set(), "sim": set()}
    for kind in ("data", "sim"):
        check_kind(args.results_dir, kind, args, problems, warnings, refit)

    def by_bin(s):
        return (int(s.split("/")[0][3:]), s)

    print("=" * 60)
    print("PROBLEMS")
    print("=" * 60)
    if not problems:
        print("None: all fits pass the criteria.")
    for cat in sorted(problems):
        print("{} ({}):".format(cat.upper(), len(problems[cat])))
        for x in sorted(problems[cat], key=by_bin):
            print("  - " + x)
    print("=" * 60)
    print("WARNINGS (not refitted)")
    print("=" * 60)
    if not warnings:
        print("None.")
    for cat in sorted(warnings):
        print("{} ({}):".format(cat.upper(), len(warnings[cat])))
        for x in sorted(warnings[cat], key=by_bin):
            print("  - " + x)

    print("=" * 60)
    print("Bins to be re-checked and refitted:")
    print("=" * 60)
    total = len(refit["data"]) + len(refit["sim"])
    if total == 0:
        print("No bins need to be refitted.")
        return
    print("Total unique bins to recheck: {}".format(total))
    if refit["data"]:
        print("\nDATA bins to refit ({} bins):".format(len(refit["data"])))
        for x in sorted(refit["data"], key=by_bin):
            print("  " + x)
    if refit["sim"]:
        print("\nSIM bins to refit ({} bins):".format(len(refit["sim"])))
        for x in sorted(refit["sim"], key=by_bin):
            print("  " + x)


if __name__ == "__main__":
    main()
