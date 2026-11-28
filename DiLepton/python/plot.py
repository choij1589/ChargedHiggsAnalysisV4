"""DiLepton data/MC plots (step 6 of docs/PLAN_DiLepton.md).

  python DiLepton/python/plot.py --channel all --all-lanes      # the full set (layout below)
  python DiLepton/python/plot.py --channel DIMU [--style an|pw] [--keys pair/mass ...]   # Central only
  python DiLepton/python/plot.py --channel EMU --exclude BtagSF  # one correction removed
  python DiLepton/python/plot.py --channel EMU --lane TopPtReweight_Applied   # samples without the lane use Central

Input: the current production, SKNanoOutput/DiLepton/<flags>_<PRODUCTION>/2024/ (synced from
KNU); its Central lane has every correction applied. Data always uses Central.
Layout (user, 2026-11-26), DiLepton/plots/AN/2024/<channel>/:
  Central/          all corrections applied; band = MC stat (+) every systematic source of
                    config/plotting/systematics_DiLepton.json, each enveloped on the total
  No<Factor>/       MC from <Factor>_NotImplemented: the same with one correction removed
                    (e.g. NoMuonIDSF, NoPileupReweight, NoBtagSF); band = MC stat only
  <Factor>_Applied/ MC from an optional correction that Central does not apply
                    (TopPtReweight_Applied: tt powheg only, other samples Central)
  corrections.txt   total data/MC per directory (--all-lanes): the effect of each correction
Each directory has yields.txt (data, MC, data/MC per histogram). --all-lanes finds the
_NotImplemented and _Applied lanes in the production (reference MC file of the channel).
PW style (--style pw) makes Central plots only, in DiLepton/plots/PW/2024/<channel>/.
EMU uses the production with the HcToWA b-tag efficiency map since 2026-11-28 (PRODUCTION below);
the plots with the previous map are in DiLepton/plots/AN/2024/EMU_OldBTagMap/.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
import histutils  # noqa: E402
import plotter  # noqa: E402

ERA = "2024"
# Current production: all corrections in Central (lepton ID SFs and trigger SFs added 2026-11-26).
# TrigSF, TrigDZ and TrigDZ_HcToWABTagEff are MC only; their data files are links to the LepIDSF data
# (data histograms unchanged). TrigDZ (2026-11-26, DIMU and EMU only) adds the DZ uncertainty to the
# trigger-SF lanes and the closure subsets; ZEE stays on TrigSF.
# EMU -> TrigDZ_HcToWABTagEff (2026-11-28): the same EMU MC (flags RunEMu,RunSyst,TrigDZ + label
# HcToWABTagEff) with the b-tag SF weight computed from this analysis's own b-tag efficiency map
# (BTagEff/results/2024/btaggingEff_HcToWA.json, TTLL); the TrigDZ map was another analysis's. MuonEG
# files are links to RunEMu_RunSyst_LepIDSF, as in TrigDZ. The old-map EMU plots are kept in
# DiLepton/plots/AN/2024/EMU_OldBTagMap/.
PRODUCTION = {"DIMU": "TrigDZ", "EMU": "TrigDZ_HcToWABTagEff", "ZEE": "TrigSF"}
CHANNELS = {
    "DIMU": {"flags": f"RunDiMu_RunSyst_{PRODUCTION['DIMU']}", "pds": ["Muon0", "Muon1"], "caption": ["#mu#mu"],
             "ref": "TTLL_powheg"},
    "EMU": {"flags": f"RunEMu_RunSyst_{PRODUCTION['EMU']}", "pds": ["MuonEG"], "caption": ["e#mu"], "ref": "TTLL_powheg"},
    "ZEE": {"flags": f"RunZEE_RunSyst_{PRODUCTION['ZEE']}", "pds": ["EGamma0", "EGamma1"], "caption": ["ee"],
            "ref": "DYto2E_2J_MLL50toInf"},
}
SKIP_IN_CHANNEL = {"DIMU": ("electrons/", "bjets/"), "EMU": ("pair/", "muons/2/", "electrons/2/"),
                   "ZEE": ("muons/", "jets/", "bjets/", "METv")}


def key_config(histkeys, key, channel):
    cfg = {k: v for k, v in histkeys[key].items() if k != "channels"}
    cfg.update(histkeys[key].get("channels", {}).get(channel, {}))
    return cfg


def lanes_of(ch):
    """[(mc_lane, out_dir)] of the channel: Central, every _NotImplemented and _Applied lane."""
    c = CHANNELS[ch]
    f = ROOT.TFile.Open(str(REPO / "SKNanoOutput" / "DiLepton" / c["flags"] / ERA / f"{c['ref']}.root"))
    names = sorted(k.GetName() for k in f.Get(ch).GetListOfKeys())
    f.Close()
    out = [("Central", "Central")]
    out += [(n, "No" + n[:-len("_NotImplemented")]) for n in names if n.endswith("_NotImplemented")]
    out += [(n, n) for n in names if n.endswith("_Applied")]
    return out


def plot_set(ch, mc_lane, out_dir, args, histkeys, groups, systs_all):
    """Plots of one channel and MC lane into <channel>/<out_dir>/; returns the total data/MC."""
    c = CHANNELS[ch]
    src = histutils.Source("DiLepton", c["flags"], ERA)
    members = [m for gname in groups["order"] for m in groups["groups"][gname]["members"]]
    keys = args.keys or [k for k in histkeys if not k.startswith(SKIP_IN_CHANNEL[ch])]
    systs = systs_all[ch] if (mc_lane == "Central" and not args.no_syst) else {}
    lines, total = [], None
    for key in keys:
        if key not in histkeys:
            logging.error("%s not in histkeys.json", key)
            continue
        cfg = key_config(histkeys, key, ch)
        cfg["caption"] = c["caption"]
        data = histutils.data_hist(src, c["pds"], ch, key)
        stack = histutils.group_hists(src, groups["groups"], groups["order"], ch, key, mc_lane,
                                      fallback="Central" if mc_lane.endswith("_Applied") else None)
        if data is None or not stack:
            logging.warning("%s %s %s: no data or no MC, skipped", ch, mc_lane, key)
            continue
        stack = [(groups["groups"][g]["label"], h, groups["groups"][g]["color"]) for g, h in stack]
        band = None
        if systs:
            band, _ = histutils.band(src, members, ch, key, systs, prepare=lambda h: plotter.prepare(h, cfg))
        path = plotter.output_path(args.style, ERA, "DiLepton", ch, key, out_dir)
        canv = plotter.StackCanvas(data, stack, cfg, style=args.style, era=ERA, band=band).draw()
        ndata, nmc = canv.data.Integral(), canv.total.Integral()
        lines.append(f"{key:28s} data {ndata:14.1f}  MC {nmc:14.1f}  data/MC {ndata / nmc if nmc else 0:.3f}")
        if total is None:
            total = (ndata, nmc)
        canv.save(path)
    if lines:
        ypath = plotter.output_path(args.style, ERA, "DiLepton", ch, "yields", out_dir).with_suffix(".txt")
        ypath.write_text(f"# {ch} ({c['flags']}), MC lane {mc_lane}\n" + "\n".join(lines) + "\n")
        logging.info("%s/%s: %d plots", ch, out_dir, len(lines))
    if src.missing:
        miss = sorted(m for m in src.missing if mc_lane in m or "Central" in m)
        if miss:
            logging.warning("%s/%s: %d missing histograms, e.g. %s", ch, out_dir, len(miss), miss[:3])
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", required=True, choices=list(CHANNELS) + ["all"])
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--keys", nargs="*", help="histkeys (default: all for the channel)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--all-lanes", action="store_true", help="Central + No<Factor> + <Factor>_Applied, and corrections.txt")
    g.add_argument("--exclude", help="factor whose _NotImplemented lane is used for MC, e.g. PileupReweight")
    g.add_argument("--lane", help="MC lane to plot instead of Central, e.g. TopPtReweight_Applied")
    ap.add_argument("--no-syst", action="store_true", help="MC stat only in the band")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.style == "pw" and (args.exclude or args.lane or args.all_lanes):
        ap.error("--style pw makes Central plots only")

    histkeys = {k: v for k, v in json.load(open(REPO / "DiLepton/configs/histkeys.json")).items() if not k.startswith("_")}
    groups = plotter.load_json("groups.json")["DiLepton"]
    systs_all = plotter.load_json("systematics_DiLepton.json")
    for ch in (list(CHANNELS) if args.channel == "all" else [args.channel]):
        if args.all_lanes:
            sets = lanes_of(ch)
        elif args.exclude:
            sets = [(f"{args.exclude}_NotImplemented", f"No{args.exclude}")]
        elif args.lane:
            sets = [(args.lane, args.lane)]
        else:
            sets = [("Central", "Central")]
        totals = {out: plot_set(ch, lane, out, args, histkeys, groups, systs_all) for lane, out in sets}
        if args.all_lanes:
            rows = [f"# {ch} ({CHANNELS[ch]['flags']}): total yield (first histogram of each set), data/MC",
                    f"{'set':28s} {'data':>14s} {'MC':>14s} {'data/MC':>8s} {'MC/MC(Central)':>15s}"]
            mc0 = totals.get("Central", (0, 0))[1]
            for out, t in totals.items():
                if t:
                    rows.append(f"{out:28s} {t[0]:14.1f} {t[1]:14.1f} {t[0] / t[1]:8.3f} {t[1] / mc0 if mc0 else 0:15.3f}")
            p = plotter.plot_dir("DiLepton", args.style, ERA) / ch / "corrections.txt"
            p.write_text("\n".join(rows) + "\n")
            logging.info("%s: %s", ch, p)


if __name__ == "__main__":
    main()
