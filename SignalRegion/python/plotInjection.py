"""Signal-injection (bias) test plots of the 2024 Baseline datacards (B2G statistics recommendations).

  python SignalRegion/python/plotInjection.py [--style an|pw] [--bkg-scale 1|10]

Input: the toy fits of SignalRegionStudy/scripts/runSignalInjection.sh in the local template copy,
SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v2/templates/MHc130_MA<mA>/Baseline/mc-signal/2024/Combined/
combine_output/injection[_bkgx10]/fitDiagnostics.inj_<label>_s<seed>.root (tree_fit_sb), and the injected values
from SignalRegionStudy/results/json/injection[_bkgx10]/mc-signal/<mp>.Combined.injection.json (collectInjection.py).
Toys with fit_status != 0 are dropped (fraction printed and drawn). Per test: histogram of r - r_inj and of the
pull (r - r_inj) / r_err (r_err = rHiErr if r < r_inj else rLoErr) with a binned Gaussian likelihood fit.
Summary: pull mean (marker) and width (error bar) vs the injected r in units of the median expected limit, per
point. Outputs: SignalRegion/plots/<AN|PW>/2024/injection[_bkgx10]/{<mp>_<label>_{dr,pull},summary}.*
"""
import argparse
import glob
import json
import math
from array import array

import ROOT
import uproot
import numpy as np

import common
from common import plotter

ROOT.gErrorIgnoreLevel = ROOT.kWarning
POINTS = [30, 60, 90, 110]
LABELS = {"r0": "r_{inj} = 0", "m1": "r_{inj} = -1#sigma exp.", "med": "r_{inj} = median exp.",
          "p1": "r_{inj} = +1#sigma exp."}
COLORS = plotter.PALETTE_LONG
LAYOUT = {"captionPos": (0.19, 0.765), "captionSize": 0.034, "legend_text": 0.032, "textSize": 0.030,
          "show_lumi": False}


def toys(idir, label):
    arrs = [uproot.open(f)["tree_fit_sb"].arrays(["r", "rLoErr", "rHiErr", "fit_status"], library="np")
            for f in sorted(glob.glob(f"{idir}/fitDiagnostics.inj_{label}_s*.root"))]
    return {k: np.concatenate([a[k] for a in arrs]) for k in arrs[0]}


def hist_fit(vals, name, nbins=30):
    med, std = float(np.median(vals)), float(np.std(vals))
    lo, hi = med - 4 * std, med + 4 * std
    h = ROOT.TH1D(name, "", nbins, lo, hi)
    h.SetDirectory(0)
    for v in vals:
        h.Fill(float(v))
    f = ROOT.TF1(name + "_f", "gaus", lo, hi)
    f.SetParameters(len(vals) * (hi - lo) / nbins / (std * math.sqrt(2 * math.pi)), med, std)
    h.Fit(f, "QLS0")
    xs = array("d", [h.GetBinCenter(i) for i in range(1, nbins + 1)])
    ys = array("d", [h.GetBinContent(i) for i in range(1, nbins + 1)])
    ex = array("d", [0.] * nbins)
    ey = array("d", [math.sqrt(y) for y in ys])
    g = ROOT.TGraphErrors(nbins, xs, ys, ex, ey)
    fx = array("d", [lo + (hi - lo) * i / 200 for i in range(201)])
    gf = ROOT.TGraph(201, fx, array("d", [f.Eval(x) for x in fx]))
    return g, gf, (f.GetParameter(1), f.GetParError(1), abs(f.GetParameter(2)), f.GetParError(2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--bkg-scale", default="1")
    a = ap.parse_args()
    sub = "injection" if a.bkg_scale == "1" else f"injection_bkgx{a.bkg_scale}"
    summary = []
    print(f"{'point':12s} {'test':4s} {'r_inj':>7s} {'ok/all':>8s} {'d mean':>8s} {'d sigma':>8s} "
          f"{'pull mean':>10s} {'pull sigma':>10s}")
    for ma in POINTS:
        mp = common.masspoint(ma)
        info = json.load(open(common.SRS / "results" / "json" / sub / "mc-signal" / f"{mp}.Combined.injection.json"))
        idir = common.TEMPLATES / mp / "Baseline/mc-signal/2024/Combined/combine_output" / sub
        pts = json.load(open(common.SRS / "results" / "json" / "points" / "Baseline" / "mc-signal" / f"{mp}.json"))
        r_med = pts["channels"]["Combined"]["r"]["exp0"]
        for label, test in info["tests"].items():
            r_inj = test["r_inj"]
            t = toys(idir, label)
            ok = t["fit_status"] == 0
            r, lo, hi = t["r"][ok], t["rLoErr"][ok], t["rHiErr"][ok]
            d = r - r_inj
            err = np.where(r < r_inj, hi, lo)
            pull = d[err > 0] / err[err > 0]
            res = {}
            for key, vals, xt in (("dr", d, "r - r_{inj}"), ("pull", pull, "(r - r_{inj}) / #sigma_{r}")):
                g, gf, (m, me, s, se) = hist_fit(vals, f"{mp}_{label}_{key}")
                res[key] = (m, me, s, se)
                cfg = {**LAYOUT, "xTitle": xt, "yTitle": "Toys", "yHeadroom": 1.8,
                       "legend": (0.63, 0.77, 0.94, 0.87),
                       "caption": [f"m_{{H^{{+}}}} = {common.MHC} GeV, m_{{A}} = {ma} GeV", LABELS[label]],
                       "text": [f"Mean {m:+.3f} #pm {me:.3f}", f"Width {s:.3f} #pm {se:.3f}",
                                f"Converged {ok.sum()}/{len(ok)}"] +
                               ([f"Backgrounds #times {a.bkg_scale}"] if a.bkg_scale != "1" else []),
                       "textPos": (0.63, 0.73)}
                items = [{"obj": g, "kind": "points", "color": "#000000", "label": "Toys"},
                         {"obj": gf, "kind": "line", "color": COLORS[2], "label": "Gaussian fit"}]
                c = plotter.GraphCanvas(items, cfg, style=a.style, era=common.ERA, has_data=False).draw()
                common.save(c, a.style, sub, f"{mp}_{label}_{key}")
            print(f"{mp:12s} {label:4s} {r_inj:7.4f} {ok.sum():4d}/{len(ok):3d} {res['dr'][0]:+8.4f} "
                  f"{res['dr'][2]:8.4f} {res['pull'][0]:+10.3f} {res['pull'][2]:10.3f}")
            summary.append((ma, r_inj / r_med, res["pull"][0], res["pull"][2]))
    items = []
    for i, ma in enumerate(POINTS):
        rows = [s for s in summary if s[0] == ma]
        n = len(rows)
        g = ROOT.TGraphErrors(n, array("d", [x + 0.03 * (i - 1.5) for _, x, _, _ in rows]),
                              array("d", [m for *_, m, _ in rows]), array("d", [0.] * n),
                              array("d", [s for *_, s in rows]))
        items.append({"obj": g, "kind": "points", "color": COLORS[i], "label": f"m_{{A}} = {ma} GeV"})
    cfg = {**LAYOUT, "xTitle": "r_{inj} / median expected limit", "yTitle": "Pull mean #pm width", "yRange": [-2.5, 3.5],
           "xRange": [-0.2, 1.8], "hlines": [0., -1., 1.],
           "caption": [f"m_{{H^{{+}}}} = {common.MHC} GeV"] +
                      ([f"Backgrounds #times {a.bkg_scale}"] if a.bkg_scale != "1" else []),
           "legend": (0.63, 0.70, 0.94, 0.87)}
    c = plotter.GraphCanvas(items, cfg, style=a.style, era=common.ERA, has_data=False).draw()
    common.save(c, a.style, sub, "summary")


if __name__ == "__main__":
    main()
