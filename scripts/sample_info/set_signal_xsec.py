#!/usr/bin/env python3
"""Set the signal cross sections in a CommonSampleInfo.json: xsec = 5 fb x filterEff.

Convention (user, 2026-11-24): a signal strength r = 1 corresponds to
sigma_sig x B(WW -> non fully hadronic) = 5 fb before the generator filter; the
MultiLepFilter samples are therefore normalized to 0.005 pb x filterEff. No
13.6/13 TeV ttbar scaling and no later division are applied. `filterEff` (from the
RNTuplizer QC) is kept as information and must not be applied again downstream.

Usage: set_signal_xsec.py --json CommonSampleInfo.json [--out new.json] [--dry-run]
"""
import argparse
import json
import os
import sys

SIGMA_REF_PB = 0.005


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True)
    ap.add_argument("--out")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    info = json.load(open(args.json))
    sig = {a: e for a, e in info.items() if a.startswith("TTToHcToWAToMuMu-") and e.get("isMC")}
    if not sig:
        sys.exit("ERROR: no signal entries")
    errors = [a for a, e in sig.items() if not (0 < float(e.get("filterEff", 0)) <= 1)]
    if errors:
        sys.exit("ERROR: missing or invalid filterEff: " + ", ".join(errors))
    for a, e in sorted(sig.items()):
        eff = float(e["filterEff"])
        old = e.get("xsec")
        e["xsec_formula"] = f"{SIGMA_REF_PB}*{eff}"
        e["xsec"] = SIGMA_REF_PB * eff
        e["xsec_source"] = {"class": "convention", "order": "",
                            "note": "r = 1 <-> sigma_sig x B(WW -> non-had) = 5 fb before the generator filter; "
                                    "xsec = 0.005 pb x filterEff (RNTuplizer QC); filterEff already included, "
                                    "do not apply again (user decision, 2026-11-24)"}
        print(f"{a:34s} {old!s:>22} -> {e['xsec']:.6g}")
    if args.dry_run:
        return
    out = args.out or args.json
    tmp = f"{out}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(info, f, indent=4)
        f.write("\n")
    os.replace(tmp, out)
    print(f"{len(sig)} signal entries written to {out}")


if __name__ == "__main__":
    main()
