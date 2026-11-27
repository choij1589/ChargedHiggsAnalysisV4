#!/usr/bin/env python3
"""Fill nmc/sumW/sumsign (MC) and NEvents (data) from GetEffLumi outputs.

A targeted replacement for `sampleManager.py --updateMcInfo`, which loops over
every alias in CommonSampleInfo.json and crashes on the first one without a
GetEffLumi output (the 2024 file also lists samples that exist only at SNU).

Only the given aliases are touched. Each one is cross-checked before writing:
  - MC (with --rnt-mc/--rnt-signal): nmc must equal RNTuplizer's validated
    event count of the same files exactly, and sumW its genEventSumw to --rtol
    (signal: count only). A mismatch is reported and nothing is written.
    A difference from the existing entry is only a warning: older entries may
    describe another site's production (tamsa TTLL_powheg: base dataset only,
    KNU: base + ext1, confirmed with DAS on 2026-11-24).
  - data NEvents per period must agree with the existing entry, if any
    (--allow-nevents-change turns this into a warning).
Placeholders (-1) are simply replaced. The "PENDING GetEffLumi" remark is
removed from the note of updated entries.

Run inside the SKNano environment (needs PyROOT):
  python3 update_from_getefflumi.py --era 2024 --aliases TTLL_powheg,Muon0 [--dry-run]
  python3 update_from_getefflumi.py --era 2024 --all-available [--dry-run]
"""
import argparse
import json
import math
import os
import re
import sys

PENDING = -1


def hist_values(path, names):
    import ROOT
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        raise FileNotFoundError(path)
    out = {}
    for n in names:
        h = f.Get(n)
        if not h:
            f.Close()
            raise KeyError(f"{path}: no histogram '{n}'")
        out[n] = (h.GetEntries(), h.GetBinContent(1))
    f.Close()
    return out


def clean_note(note):
    if not note:
        return note
    parts = [p.strip() for p in note.split(";")]
    parts = [re.sub(r"\s*sumsign PENDING GetEffLumi", "", p) for p in parts]
    parts = [p for p in parts if p and "PENDING GetEffLumi" not in p]
    return "; ".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--era", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--aliases", help="comma-separated aliases")
    g.add_argument("--all-available", action="store_true", help="every alias with a GetEffLumi output")
    ap.add_argument("--rtol", type=float, default=1e-6, help="relative tolerance for sumW")
    ap.add_argument("--allow-nevents-change", action="store_true",
                    help="data: replace NEvents that differ from the existing entry (e.g. entries "
                         "filled from another site's production) with a warning instead of an error")
    ap.add_argument("--rnt-mc", help="RNTuplizer results/overall_sknano_rntuple.csv (independent check)")
    ap.add_argument("--rnt-signal", help="RNTuplizer results/overall_rntuple.csv (independent check)")
    ap.add_argument("--accept-sumw-mismatch", default="",
                    help="comma-separated aliases whose sumW may differ from RNTuplizer's Runs-tree "
                         "genEventSumw (only after checking that the Events-tree count agrees)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    accept_sumw = {a.strip() for a in args.accept_sumw_mismatch.split(",") if a.strip()}

    import csv
    rnt = {}
    for path, key in ((args.rnt_mc, "sample"), (args.rnt_signal, "masspoint")):
        if not path:
            continue
        for r in csv.DictReader(open(path)):
            sw = r.get("genEventSumw_rntuple")
            rnt[r.get(key) or r.get("sample")] = {"events": float(r["events_rntuple"]),
                                                  "sumw": float(sw) if sw not in (None, "") else None}

    out_dir = os.path.join(os.environ["SKNANO_OUTPUT"], "GetEffLumi", args.era)
    json_path = os.path.join(os.environ["SKNANO_DATA"], args.era, "Sample", "CommonSampleInfo.json")
    info = json.load(open(json_path))

    if args.all_available:
        aliases = []
        for a, e in info.items():
            files = ([f"{a}.root"] if e.get("isMC") else [f"{a}_{p}.root" for p in e.get("periods", [])])
            if files and all(os.path.isfile(os.path.join(out_dir, f)) for f in files):
                aliases.append(a)
    else:
        aliases = [a.strip() for a in args.aliases.split(",") if a.strip()]

    errors, report = [], []
    for a in aliases:
        if a not in info:
            errors.append(f"{a}: not in {json_path}")
            continue
        e = info[a]
        try:
            if e.get("isMC"):
                h = hist_values(os.path.join(out_dir, f"{a}.root"), ["sumW", "sumSign"])
                nmc, sumw = h["sumW"]
                sumsign = h["sumSign"][1]
                old_nmc, old_sumw = e.get("nmc", PENDING), e.get("sumW", PENDING)
                ref = rnt.get(e.get("PD"))
                if ref is not None:
                    # Independent check on the same files: RNTuplizer's validated counts.
                    if int(ref["events"]) != int(nmc):
                        errors.append(f"{a}: nmc {nmc:.0f} != RNTuplizer events {ref['events']:.0f}")
                    if ref["sumw"] is not None and not math.isclose(ref["sumw"], sumw, rel_tol=args.rtol):
                        msg = f"{a}: sumW {sumw!r} != RNTuplizer genEventSumw {ref['sumw']!r}"
                        if a in accept_sumw:
                            # e.g. WZ_pythia: the Runs tree counts 42,050 events that are in no Events
                            # tree (no generator filter); the sum over the events present is correct.
                            print(f"WARNING {msg} (accepted: --accept-sumw-mismatch)")
                        else:
                            errors.append(msg)
                elif args.rnt_mc or args.rnt_signal:
                    errors.append(f"{a}: PD {e.get('PD')} not in the RNTuplizer rollups")
                if old_nmc != PENDING and int(old_nmc) != int(nmc):
                    # e.g. entries filled from another site's production (tamsa:
                    # base dataset only; KNU: base + ext)
                    print(f"WARNING {a}: nmc differs from the existing entry ({old_nmc:.0f} -> {nmc:.0f})")
                report.append(f"{a}: nmc {old_nmc} -> {nmc:.0f}, sumW {old_sumw} -> {sumw!r}, "
                              f"sumsign {e.get('sumsign')} -> {sumsign:.0f}")
                e.update({"nmc": float(nmc), "sumW": float(sumw), "sumsign": float(sumsign)})
            else:
                nevt = []
                for p in e["periods"]:
                    nevt.append(hist_values(os.path.join(out_dir, f"{a}_{p}.root"), ["NEvents"])["NEvents"][1])
                old = e.get("NEvents")
                if old and [int(x) for x in old] != [int(x) for x in nevt]:
                    msg = f"{a}: NEvents {nevt} != existing {old}"
                    if args.allow_nevents_change:
                        print(f"WARNING {msg}")
                    else:
                        errors.append(msg)
                report.append(f"{a}: NEvents {old} -> {nevt}")
                e["NEvents"] = [float(x) for x in nevt]
            if "note" in e:
                e["note"] = clean_note(e["note"])
                if not e["note"]:
                    del e["note"]
        except (FileNotFoundError, KeyError) as exc:
            errors.append(f"{a}: {exc}")

    for line in report:
        print(line)
    if errors:
        sys.exit("ERROR, nothing written:\n  " + "\n  ".join(errors))
    if args.dry_run:
        print(f"dry run: {len(report)} entries would be updated")
        return
    tmp = f"{json_path}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(info, f, indent=4)
        f.write("\n")
    os.replace(tmp, json_path)
    print(f"updated {len(report)} entries in {json_path}")


if __name__ == "__main__":
    main()
