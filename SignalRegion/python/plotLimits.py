"""Expected upper limits on B_sig at mH+ = 130 GeV vs mA, 2024 Baseline (Asimov, SR blinded).

  python SignalRegion/python/plotLimits.py [--style an|pw]

Inputs:
  2024: SignalRegionStudy/results/json/BR/2024/limits.2024[.SR1E2Mu|.SR3Mu].Asymptotic.Baseline.json
        (keys MHc130_MA15-125; exp-2/exp-1/exp0/exp+1/exp+2; B_sig = r x 5 fb / (2 x 923.6 pb x 0.5456),
        sigma(tt, 13.6 TeV) = 923.6 pb). "obs" is the Asimov value and is never read.
  B2G-25-013 (read-only, docs/previous_analysis/ChargedHiggsAnalysisV3/SignalRegionStudyV4/results/json/BR/All/):
        Run 2 + Run 3 published expected curve = limits.All.Asymptotic.ParticleNet.interp-signal.json
        for 82.5 <= mA <= 97.5 GeV and limits.All.Asymptotic.Baseline.interp-signal.json elsewhere
        (keys MHc130_MA<x>, 'p' = decimal point). Both curves are plotted as stored: B_sig is a
        branching fraction, no rescaling.
Outputs: SignalRegion/plots/<AN|PW>/2024/limits/
  brazil_{Combined,SR1E2Mu,SR3Mu}  median expected with the 68% / 95% bands (log y)
  compare_B2G25013                 2024 Combined (median + bands) with the B2G-25-013 Run 2 + Run 3
                                   published expected curve
  channels                         median expected of Combined, SR1E2Mu, SR3Mu
  comparison.txt                   mA, 2024 expected, B2G-25-013 expected at the same mA, ratio
"""
import argparse
import json

import ROOT

import common
from common import plotter, CH_LABEL, MA_TITLE
import srspaths

ROOT.gErrorIgnoreLevel = ROOT.kWarning
LIM = common.SRS / "results" / "json" / "BR" / common.ERA
PREV_ALL = common.PREV / "results" / "json" / "BR" / "All"
PNET_WINDOW = (82.5, 97.5)
QUANT = ["exp-2", "exp-1", "exp0", "exp+1", "exp+2"]
Y_TITLE = "95% CL upper limit on #it{B}_{sig} [10^{-6}]"
SCALE = 1e6  # plotted in units of 1e-6, linear (as B2G-25-013 Fig. limits)
TOP_TEXT = ["m_{H^{+}} = 130 GeV"]
# shared layout: CMS label top left, caption block under it, legend top right, notes at the bottom
LAYOUT = {"xTitle": MA_TITLE, "yTitle": Y_TITLE, "xRange": (15, 125), "logy": False, "yRange": (0., 14.), "yTitleSize": 0.042,
          "captionPos": (0.19, 0.765), "captionSize": 0.036, "legend_text": 0.033, "textSize": 0.027}


def load_2024(channel):
    suffix = "" if channel == "Combined" else f".{channel}"
    with open(LIM / f"limits.{common.ERA}{suffix}.Asymptotic.Baseline.json") as f:
        raw = json.load(f)
    out = {}
    for mp in (common.masspoint(m) for m in common.GRID_MA):
        if mp not in raw:
            raise SystemExit(f"{mp} missing in the 2024 {channel} limits")
        out[srspaths.masspoint_mhc_ma(mp)[1]] = {q: raw[mp][q] for q in QUANT}
    extra = sorted(set(raw) - {common.masspoint(m) for m in common.GRID_MA})
    if extra:
        print(f"warning: 2024 {channel} limits have keys outside the grid: {extra}")
    return out


def load_prev(method):
    with open(PREV_ALL / f"limits.All.Asymptotic.{method}.interp-signal.json") as f:
        raw = json.load(f)
    out = {}
    for key, rec in raw.items():
        mhc, ma = srspaths.masspoint_mhc_ma(key)
        if mhc == common.MHC:
            out[float(ma)] = rec["exp0"]
    return out


def published_curve():
    """B2G-25-013 published expected curve at mH+ = 130: ParticleNet inside the window, Baseline
    outside; the Baseline points at the window edges are kept so the line steps there."""
    base, pnet = load_prev("Baseline"), load_prev("ParticleNet")
    lo, hi = PNET_WINDOW
    if min(pnet) != lo or max(pnet) != hi:
        print(f"warning: ParticleNet interp-signal range {min(pnet)}-{max(pnet)} != {PNET_WINDOW}")
    pts = [(m, v, "Baseline") for m, v in sorted(base.items()) if m <= lo]
    pts += [(m, v, "ParticleNet") for m, v in sorted(pnet.items())]
    pts += [(m, v, "Baseline") for m, v in sorted(base.items()) if m >= hi]
    return pts


def at_ma(curve, ma):
    """Value of the published curve at a grid mA (ParticleNet wins inside the window)."""
    lo, hi = PNET_WINDOW
    want = "ParticleNet" if lo <= ma <= hi else "Baseline"
    for m, v, meth in curve:
        if abs(m - ma) < 1e-6 and meth == want:
            return v, meth
    raise KeyError(f"B2G-25-013 curve has no {want} point at mA = {ma}")


def brazil_items(lim, median_label="Expected"):
    mas = sorted(lim)
    n = len(mas)
    g95, g68, gmed = ROOT.TGraphAsymmErrors(n), ROOT.TGraphAsymmErrors(n), ROOT.TGraph(n)
    for i, m in enumerate(mas):
        q = lim[m]
        for g in (g95, g68):
            g.SetPoint(i, m, SCALE * q["exp0"])
        g95.SetPointError(i, 0, 0, SCALE * (q["exp0"] - q["exp-2"]), SCALE * (q["exp+2"] - q["exp0"]))
        g68.SetPointError(i, 0, 0, SCALE * (q["exp0"] - q["exp-1"]), SCALE * (q["exp+1"] - q["exp0"]))
        gmed.SetPoint(i, m, SCALE * q["exp0"])
    return [
        {"obj": g95, "kind": "band", "color": plotter.LIMIT_95, "label": "95% CL expected"},
        {"obj": g68, "kind": "band", "color": plotter.LIMIT_68, "label": "68% CL expected"},
        {"obj": gmed, "kind": "line", "color": "#000000", "style": ROOT.kDashed, "width": 3,
         "label": median_label},
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    a = ap.parse_args()

    lims = {ch: load_2024(ch) for ch in ("Combined", "SR1E2Mu", "SR3Mu")}

    # (a) Brazil plots per channel
    for ch, lim in lims.items():
        items = brazil_items(lim)
        cfg = dict(LAYOUT, caption=TOP_TEXT + [CH_LABEL[ch]], legend=(0.58, 0.69, 0.93, 0.86),
                   legend_order=[2, 1, 0])
        c = plotter.GraphCanvas(items, cfg, style=a.style).draw()
        common.save(c, a.style, "limits", f"brazil_{ch}")

    # (b) 2024 Combined vs the B2G-25-013 Run 2 + Run 3 published expected curve
    curve = published_curve()
    gprev = ROOT.TGraph(len(curve))
    for i, (m, v, _) in enumerate(curve):
        gprev.SetPoint(i, m, SCALE * v)
    items = brazil_items(lims["Combined"], "Expected (2024)")
    items.append({"obj": gprev, "kind": "line", "color": plotter.PALETTE_LONG[2], "width": 3,
                  "label": "B2G-25-013 expected"})
    cfg = dict(LAYOUT, caption=TOP_TEXT + [CH_LABEL["Combined"]], legend=(0.58, 0.65, 0.93, 0.86),
               legend_order=[2, 1, 0, 3],
               vlines=list(PNET_WINDOW), vlineColor="#000000", vlineStyle=ROOT.kDashed, vlineWidth=1)
    c = plotter.GraphCanvas(items, cfg, style=a.style).draw()
    common.save(c, a.style, "limits", "compare_B2G25013")

    # (c) channel comparison of the medians
    items = []
    for ch, col, sty in (("Combined", "#000000", ROOT.kSolid), ("SR1E2Mu", plotter.PALETTE_LONG[0], ROOT.kDashed),
                         ("SR3Mu", plotter.PALETTE_LONG[1], ROOT.kDashed)):
        g = ROOT.TGraph(len(lims[ch]))
        for i, m in enumerate(sorted(lims[ch])):
            g.SetPoint(i, m, SCALE * lims[ch][m]["exp0"])
        items.append({"obj": g, "kind": "line", "color": col, "style": sty, "width": 3,
                      "label": f"{CH_LABEL[ch]}"})
    cfg = dict(LAYOUT, caption=TOP_TEXT,
               captionSize=0.034, legend=(0.56, 0.69, 0.93, 0.86), legend_header="Median expected")
    c = plotter.GraphCanvas(items, cfg, style=a.style).draw()
    common.save(c, a.style, "limits", "channels")

    # comparison table
    lines = ["# Expected 95% CL upper limits on B_sig at mH+ = 130 GeV (median, Asimov).",
             "# 2024: Baseline, Combined (SignalRegionStudy/results/json/BR/2024/limits.2024.Asymptotic.Baseline.json),",
             "#       r converted with sigma(tt, 13.6 TeV) = 923.6 pb.",
             "# B2G-25-013: Run 2 + Run 3 published expected (All/limits.All.Asymptotic.{ParticleNet,Baseline}.interp-signal.json;",
             "#       ParticleNet for 82.5 <= mA <= 97.5 GeV, Baseline elsewhere). Values as stored, no rescaling.",
             f"{'mA':>5} {'2024_exp':>11} {'B2G25013_exp':>13} {'method':>12} {'ratio':>7}"]
    for m in common.GRID_MA:
        ours = lims["Combined"][m]["exp0"]
        prev, meth = at_ma(curve, m)
        lines.append(f"{m:5d} {ours:11.3e} {prev:13.3e} {meth:>12} {ours / prev:7.3f}")
    text = "\n".join(lines)
    print(text)
    out = common.outdir(a.style, "limits") / "comparison.txt"
    out.write_text(text + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
