"""DiLepton cutflow: data and MC per selection step, and data/MC.

  python DiLepton/python/cutflow.py [--channel DIMU|EMU|ZEE|all]

The cutflow histograms are weighted with the MC normalization only
(sign(genWeight) x xsec / sumSign x lumi): no PU weight and no SFs. The final
line repeats the yield with all weights (from nPVsGood), so the effect of the
weights can be separated from the selection.

Steps (DiLepton.cc): ALL 0 all events, 1 noise filters, 2 jet veto map;
channel 3 lepton multiplicity, 4 trigger, 5 lepton kinematics, 6 >= 2 jets (EMU),
7 >= 1 b jet (EMU), 8 final.
Writes DiLepton/plots/AN/2024/<channel>/cutflow.md.
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import histutils  # noqa: E402
import plotter  # noqa: E402
from plot import CHANNELS, ERA  # noqa: E402

STEPS = {0: "all events", 1: "noise filters", 2: "jet veto map", 3: "lepton multiplicity", 4: "trigger",
         5: "lepton kinematics", 6: ">= 2 jets", 7: ">= 1 b jet", 8: "final"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", default="all", choices=list(CHANNELS) + ["all"])
    args = ap.parse_args()
    groups = plotter.load_json("groups.json")["DiLepton"]
    for ch in (list(CHANNELS) if args.channel == "all" else [args.channel]):
        c = CHANNELS[ch]
        src = histutils.Source("DiLepton", c["flags"], ERA)
        datas = src.data_samples(c["pds"])
        order = list(reversed(groups["order"]))

        def row(path, binx):
            d = sum(src.get(s, path).GetBinContent(binx + 1) for s in datas)
            per = {g: sum(h.GetBinContent(binx + 1) for h in
                          [src.get(m, path) for m in groups["groups"][g]["members"]] if h) for g in order}
            return d, per

        steps = [("ALL/Central/cutflow", b) for b in (0, 1, 2)]
        steps += [(f"{ch}/Central/cutflow", b) for b in (3, 4, 5, 6, 7, 8) if not (ch != "EMU" and b in (6, 7))]
        hdr = "| step | data | MC | data/MC | " + " | ".join(groups["groups"][g]["label"] for g in order) + " |"
        out = [f"# {ch} cutflow (MC: normalization only, no PU weight or SFs)", "", hdr,
               "|" + "---|" * (4 + len(order))]
        for path, b in steps:
            d, per = row(path, b)
            mc = sum(per.values())
            out.append(f"| {b} {STEPS[b]} | {d:.4g} | {mc:.4g} | {d / mc if mc else 0:.3f} | "
                       + " | ".join(f"{per[g] / mc:.1%}" if mc else "-" for g in order) + " |")
        # all weights applied
        d = histutils.data_hist(src, c["pds"], ch, "nPVsGood").Integral(0, 10000)
        per = {g: h.Integral(0, 10000) for g, h in histutils.group_hists(src, groups["groups"], order, ch, "nPVsGood")}
        mc = sum(per.values())
        out.append(f"| final, all weights | {d:.4g} | {mc:.4g} | {d / mc:.3f} | "
                   + " | ".join(f"{per.get(g, 0) / mc:.1%}" for g in order) + " |")
        text = "\n".join(out) + "\n"
        path = plotter.plot_dir("DiLepton", "an", ERA) / ch / "cutflow.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(text)


if __name__ == "__main__":
    main()
