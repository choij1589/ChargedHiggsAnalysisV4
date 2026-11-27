#!/usr/bin/env python3
"""Write the cross sections of config/xsec_2024.csv into a CommonSampleInfo.json.

For every alias in the table:
  - `xsec` is set to the table value;
  - `xsec_formula` is set to the table formula, or removed when the table has none.
    `sampleManager.py --updateXsec` recomputes xsec from xsec_formula, so a stale
    formula would silently bring back the old value;
  - `xsec_source` records class, order, reference, K-factor, flag, note and the table;
  - remarks about the cross section are dropped from `note`, keeping the remarks
    about event counts.
Aliases not in the table (signal, data, samples not on KNU) are left untouched.
Rows of class PENDING keep xsec = -1.

Usage: apply_xsec_table.py --table config/xsec_2024.csv --json CommonSampleInfo.json [--out new.json] [--dry-run]
"""
import argparse
import csv
import json
import os
import sys

KEEP_NOTE = ("nmc", "sumW", "sumsign", "NEvents", "GetEffLumi")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", help="default: overwrite --json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    info = json.load(open(args.json))
    rows = list(csv.DictReader(open(args.table)))
    table_name = os.path.basename(args.table)
    errors, changes = [], []
    for r in rows:
        a = r["alias"]
        if a not in info:
            errors.append(f"{a}: not in {args.json}")
            continue
        e = info[a]
        if e.get("PD") != r["PD"]:
            errors.append(f"{a}: PD mismatch ({e.get('PD')} vs {r['PD']})")
            continue
        new = -1.0 if r["class"] == "PENDING" else float(r["xsec_pb"])
        if r["formula"]:
            val = eval(r["formula"], {"__builtins__": {}})
            if abs(val - new) > 1e-5 * max(abs(new), 1e-12):
                errors.append(f"{a}: formula {r['formula']} = {val} != xsec {new}")
                continue
            e["xsec_formula"] = r["formula"]
            new = val
        else:
            e.pop("xsec_formula", None)
        old = e.get("xsec")
        e["xsec"] = new
        e["xsec_source"] = {k: r[k] for k in ("class", "order", "ref", "kfactor", "generator_xsec",
                                               "xsdb_xsec", "an25154_xsec", "flag", "note") if r.get(k)}
        e["xsec_source"]["table"] = table_name
        if "note" in e:
            kept = [p.strip() for p in e["note"].split(";") if any(k in p for k in KEEP_NOTE)]
            if kept:
                e["note"] = "; ".join(kept)
            else:
                del e["note"]
        if old != new:
            changes.append((a, old, new, r["class"], r["flag"]))
    if errors:
        sys.exit("ERROR, nothing written:\n  " + "\n  ".join(errors))
    for a, old, new, cls, flag in changes:
        print(f"{a:32s} {old!s:>12.10} -> {new:<12.6g} {cls:5s} {flag}")
    print(f"{len(rows)} table rows, {len(changes)} xsec values changed")
    if args.dry_run:
        return
    out = args.out or args.json
    tmp = f"{out}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(info, f, indent=4)
        f.write("\n")
    os.replace(tmp, out)
    print(f"written {out}")


if __name__ == "__main__":
    main()
