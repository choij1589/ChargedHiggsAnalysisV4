"""Nuisance impacts on r for the Asimov fits (r = 1) of the 2024 Baseline Combined datacards.

  python SignalRegion/python/plotImpacts.py [--style an|pw] [--top 25] [--points 30,60,90,110]

Input: SignalRegionStudy/results/json/impacts_asimov/mc-signal/MHc130_MA<mA>.Combined.impacts.json
(combineTool format: POIs [{name, fit [lo, best, hi]}], params [{name, fit [lo, best, hi],
prefit [lo, central, hi], r [r(-1 sigma), r(best), r(+1 sigma)], impact_r}]).
Per point the top N nuisances by |impact_r| are drawn: left the post-fit value
(theta_hat - theta_0) / Delta theta_prefit with its post-fit uncertainty (Asimov: the value is 0
and the bars show the constraint), right Delta r for the +1 sigma and -1 sigma post-fit shifts.
Two versions: all nuisances (including the autoMCStats prop_bin* parameters), and without the
autoMCStats parameters (_noMCStat; the selection of filterImpacts.py).
Outputs: SignalRegion/plots/<AN|PW>/2024/impacts/MHc130_MA<mA>[_noMCStat].{png,pdf}; a summary
table (r interval, top 5 nuisances, nuisances constrained below 0.8) is printed.
"""
import argparse
import json
import re

import ROOT

import common
from common import plotter

ROOT.gErrorIgnoreLevel = ROOT.kWarning
IMP = common.SRS / "results" / "json" / "impacts_asimov" / "mc-signal"
MCSTAT = re.compile(r"^(prop_bin|autoMCStat)")


def rows_of(params, top):
    rows = []
    for p in sorted(params, key=lambda p: -abs(p["impact_r"]))[:top]:
        lo, best, hi = p["fit"]
        plo, pc, phi = p["prefit"]
        sig = 0.5 * (phi - plo) if phi > plo else 1.
        rows.append({"label": p["name"], "pull": (best - pc) / sig, "err_lo": (best - lo) / sig,
                     "err_hi": (hi - best) / sig, "d_up": p["r"][2] - p["r"][1], "d_dn": p["r"][0] - p["r"][1]})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--points", default="30,60,90,110")
    a = ap.parse_args()

    for ma in [int(x) for x in a.points.split(",")]:
        mp = common.masspoint(ma)
        with open(IMP / f"{mp}.Combined.impacts.json") as f:
            d = json.load(f)
        poi = next(p for p in d["POIs"] if p["name"] == "r")
        rlo, r0, rhi = poi["fit"]
        poi_text = f"#hat{{r}} = {r0:.2f}^{{#plus{rhi - r0:.2f}}}_{{#minus{r0 - rlo:.2f}}}"
        caption = f"m_{{H^{{+}}}} = 130 GeV, m_{{A}} = {ma} GeV, e#mu#mu + #mu#mu#mu, Asimov (r = 1)"
        params = d["params"]
        nomc = [p for p in params if not MCSTAT.search(p["name"])]
        for tag, sel in (("", params), ("_noMCStat", nomc)):
            rows = rows_of(sel, a.top)
            cfg = {"caption": caption, "poi_text": poi_text}
            c = plotter.ImpactCanvas(rows, cfg, style=a.style).draw()
            common.save(c, a.style, "impacts", f"{mp}{tag}")
        constrained = sorted((p for p in nomc), key=lambda p: (p["fit"][2] - p["fit"][0]) / 2)
        constrained = [p for p in constrained if (p["fit"][2] - p["fit"][0]) / 2 < 0.8]
        print(f"{mp}: r = {r0:.3f} +{rhi - r0:.3f} -{r0 - rlo:.3f}; {len(params)} params "
              f"({len(params) - len(nomc)} autoMCStats)")
        for p in sorted(params, key=lambda p: -abs(p["impact_r"]))[:5]:
            print(f"    {p['name']:45s} impact {p['impact_r']:.4f}")
        for p in constrained:
            print(f"    constrained: {p['name']:40s} post-fit sigma {(p['fit'][2] - p['fit'][0]) / 2:.3f}")


if __name__ == "__main__":
    main()
