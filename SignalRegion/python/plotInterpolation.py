"""Signal mA interpolation at mH+ = 130 GeV (2024): shape parameters, yield model, LOO closure.

  python SignalRegion/python/plotInterpolation.py [--style an|pw]

Inputs (SignalRegionStudy/results/interpolation/):
  fits/MHc130/polynomials.json        per category (SR1E2Mu_2024, SR3Mu_lowM_2024, SR3Mu_highM_2024) and
                                      shape parameter: polynomial in mA (numpy order, coeffs/cov, chosen_order by
                                      the up-only F-test; fsig 'logitpoly'), points_used {mA, value, error} = the
                                      direct DCB fits used; nL/nR frozen (constant records)
  fits/MHc130/dcb_fits.json           direct fits (quality flags; non-good points are drawn as open markers)
  fits/MHc130/dcb_fits_floating.json  floating-n fits (the frozen nL/nR are their medians)
  fits/MHc130/yields/yields.json      per-point yields (sumw_total = full SR yield, sumw = window yield)
  fits/MHc130/yields/yield_model.json G (log total yield, polynomial in mA) per production channel
  closure/MHc130/yield_closure.json   window yield predicted by the model vs measured, per category
  closure/loo_uncertainties.json      leave-one-out residuals (point_detail: signed scale, res, norm) and the
                                      uncertainties (production_restricted = the datacard values; top level =
                                      all usable points)
The polynomials are evaluated with SignalRegionStudy's own functions (interpolation_config.eval_param,
fitInterpPolynomials.poly_band, fitInterpYieldModel.eval_rec / rec_band / inv_logit); nothing is refitted.
Outputs: SignalRegion/plots/<AN|PW>/2024/interpolation/
  params_<category>_<param>     direct fits (points), chosen polynomial (order in the legend) with its
                                +-1 sigma band from the fit covariance, pulls in the lower pad (x0 drawn as
                                x0 - mA); nL/nR: floating-n fits and the frozen median
  yield_G                       G = total SR yield vs mA, SR1E2Mu and SR3Mu, model and per-point yields
  yield_window_<category>       window yield: model prediction (band) vs measured per point, pulls
  loo_<scale|res|norm>_<category>  LOO residuals vs mA (filled: production pairing, open: other pairing),
                                band = production uncertainty, dashed = value over all usable points
Signal MC only: label "Simulation Work in progress".
"""
import argparse
import json

import numpy as np
import ROOT

import common
from common import plotter, CH_LABEL, MA_TITLE
import interpolation_config as ic
from fitInterpPolynomials import poly_band, form_label
from fitInterpYieldModel import eval_rec, rec_band, inv_logit

ROOT.gErrorIgnoreLevel = ROOT.kWarning
INTERP = common.SRS / "results" / "interpolation"
FITS = INTERP / "fits" / f"MHc{common.MHC}"
CATS = ["SR1E2Mu_2024", "SR3Mu_lowM_2024", "SR3Mu_highM_2024"]
PAR_TITLE = {"x0": "x_{0} #minus m_{A} [GeV]", "sigmaL": "#sigma_{L} [GeV]", "sigmaR": "#sigma_{R} [GeV]",
             "alphaL": "#alpha_{L}", "alphaR": "#alpha_{R}", "nL": "n_{L}", "nR": "n_{R}",
             "fsig": "f_{sig}", "c1": "c_{1}", "c2": "c_{2}"}
C_PTS, C_FIT, C_ALT = "#000000", plotter.PALETTE_LONG[0], plotter.PALETTE_LONG[2]
XGRID = np.linspace(15., 125., 221)
# mA range where a study channel is the production template (SR3Mu: higher-mass pair iff mA >= 60)
PROD_RANGE = {"SR1E2Mu": (15., 125.001), "SR3Mu_lowM": (15., 60.), "SR3Mu_highM": (60., 125.001)}
# two-pad canvases: the label sits lower in the upper pad's NDC
PULL_LAYOUT = {"captionPos": (0.19, 0.69), "legend": (0.58, 0.70, 0.93, 0.87)}


def cat_label(cat):
    return CH_LABEL[cat.rsplit("_", 1)[0]]


def graph(x, y, ey=None, ey_hi=None):
    n = len(x)
    g = ROOT.TGraphAsymmErrors(n)
    for i in range(n):
        g.SetPoint(i, float(x[i]), float(y[i]))
        lo = float(ey[i]) if ey is not None else 0.
        hi = float(ey_hi[i]) if ey_hi is not None else lo
        g.SetPointError(i, 0., 0., lo, hi)
    return g


def curve_band(x, lo, mid, hi):
    return graph(x, mid, np.asarray(mid) - np.asarray(lo), np.asarray(hi) - np.asarray(mid))


def base_cfg(ytitle, caption, **kw):
    cfg = {"xTitle": MA_TITLE, "yTitle": ytitle, "xRange": (10., 130.), "caption": caption,
           "captionPos": (0.19, 0.765), "captionSize": 0.034, "legend": (0.63, 0.74, 0.95, 0.87),
           "legend_text": 0.032, "show_lumi": False}
    cfg.update(kw)
    return cfg


def params_plots(style):
    with open(FITS / "polynomials.json") as f:
        polys = json.load(f)["polynomials"]
    with open(FITS / "dcb_fits.json") as f:
        direct = json.load(f)["results"]
    with open(FITS / "dcb_fits_floating.json") as f:
        floating = json.load(f)["results"]
    summary = []
    for cat in CATS:
        for par, rec in polys[cat].items():
            caption = [cat_label(cat), "m_{H^{+}} = 130 GeV"]
            if rec.get("frozen"):
                fl = floating[cat]
                mas = sorted(int(k.split("_MA")[1]) for k in fl)
                vals = [fl[common.masspoint(m)]["params"][par]["value"] for m in mas]
                errs = [min(fl[common.masspoint(m)]["params"][par]["error"], 1e3) for m in mas]
                frozen = float(ic.eval_param(rec, 0.))
                gl = graph([10., 130.], [frozen, frozen])
                items = [{"obj": graph(mas, vals, errs), "kind": "points", "color": C_PTS,
                          "label": "Floating-n DCB fits"},
                         {"obj": gl, "kind": "line", "color": C_FIT, "width": 3,
                          "label": f"Frozen: median = {frozen:.2f}"}]
                ymax = max(3. * frozen, 1.3 * max(vals))
                cfg = base_cfg(PAR_TITLE[par], caption, yRange=(0., ymax))
                c = plotter.GraphCanvas(items, cfg, style=style, has_data=False).draw()
                common.save(c, style, "interpolation", f"params_{cat}_{par}")
                continue
            pu = rec["points_used"]
            x, v, e = np.array(pu["mA"]), np.array(pu["value"]), np.array(pu["error"])
            shift_x = XGRID if par == "x0" else 0.
            shift_p = x if par == "x0" else 0.
            if rec.get("form") == "logitpoly":
                z = np.polyval(np.asarray(rec["coeffs"]), XGRID)
                sz = poly_band(rec["coeffs"], rec["cov"], XGRID)
                mid, lo, hi = inv_logit(z), inv_logit(z - sz), inv_logit(z + sz)
            else:
                mid = ic.eval_param(rec, XGRID)
                s = poly_band(rec["coeffs"], rec["cov"], XGRID)
                lo, hi = mid - s, mid + s
            pred_pts = ic.eval_param(rec, x)
            pulls = (v - pred_pts) / e
            items = [{"obj": curve_band(XGRID, lo - shift_x, mid - shift_x, hi - shift_x), "kind": "band",
                      "color": C_FIT, "alpha": 0.35, "label": "#pm1#sigma (fit covariance)"},
                     {"obj": graph(XGRID, mid - shift_x), "kind": "line", "color": C_FIT, "width": 3,
                      "label": f"{form_label(rec)}, #chi^{{2}}/ndf = {rec['chi2']:.1f}/{len(x) - len(rec['coeffs'])}"},
                     {"obj": graph(x, v - shift_p, e), "kind": "points", "color": C_PTS, "label": "Direct DCB fits"}]
            bad = [k for k, r in direct[cat].items() if r["quality"] != "good"]
            if bad:
                bx = [int(k.split("_MA")[1]) for k in bad]
                bv = [direct[cat][k]["params"][par]["value"] - (m if par == "x0" else 0.) for k, m in zip(bad, bx)]
                items.append({"obj": graph(bx, bv), "kind": "markers", "color": C_ALT, "marker": ROOT.kOpenCircle,
                              "size": 1.3, "label": "Not used (fit quality)"})
            ys = list(v - shift_p) + list(hi - shift_x) + list(lo - shift_x) + (bv if bad else [])
            ylo, yhi = min(ys), max(ys)
            span = yhi - ylo if yhi > ylo else 1.
            cfg = base_cfg(PAR_TITLE[par], caption, yRange=(ylo - 0.1 * span, yhi + 0.9 * span),
                           legend_order=[2, 1, 0] + ([3] if bad else []), rTitle="Pull",
                           rRange=(-3.5, 3.5), rlines=[0., -2., 2.], legend_text=0.029, **PULL_LAYOUT)
            bottom = [{"obj": graph(x, pulls), "kind": "markers", "color": C_PTS, "size": 0.9}]
            c = plotter.GraphCanvas(items, cfg, style=style, has_data=False, bottom=bottom).draw()
            common.save(c, style, "interpolation", f"params_{cat}_{par}")
            summary.append((cat, par, form_label(rec), rec["chi2"], len(x) - len(rec["coeffs"]),
                            float(np.max(np.abs(pulls)))))
    print(f"{'category':18s} {'param':7s} {'form':13s} {'chi2/ndf':>10s} {'max|pull|':>9s}")
    for cat, par, form, chi2, ndf, mp in summary:
        print(f"{cat:18s} {par:7s} {form:13s} {chi2:6.1f}/{ndf:<3d} {mp:9.2f}")


def yield_plots(style):
    with open(FITS / "yields" / "yield_model.json") as f:
        model = json.load(f)["model"]
    with open(INTERP / "closure" / f"MHc{common.MHC}" / "yield_closure.json") as f:
        clos = json.load(f)["closure"]
    tots = model["totals"][common.ERA]
    items, bottom, order = [], [], []
    for i, (ch, col) in enumerate((("SR1E2Mu", plotter.PALETTE_LONG[0]), ("SR3Mu", plotter.PALETTE_LONG[1]))):
        g = tots[ch]["G"]
        pu = g["points_used"]
        x, ly, le = np.array(pu["x"]), np.array(pu["y"]), np.array(pu["err"])
        lz = eval_rec(g, XGRID)
        s = rec_band(g, XGRID)
        items.append({"obj": curve_band(XGRID, np.exp(lz - s), np.exp(lz), np.exp(lz + s)), "kind": "band",
                      "color": col, "alpha": 0.35})
        items.append({"obj": graph(XGRID, np.exp(lz)), "kind": "line", "color": col, "width": 3,
                      "label": f"{CH_LABEL[ch]}: G (log-pol{g['chosen_order']})"})
        y = np.exp(ly)
        items.append({"obj": graph(x, y, y * (1 - np.exp(-le)), y * (np.exp(le) - 1)), "kind": "points",
                      "color": col, "marker": [ROOT.kFullCircle, ROOT.kFullSquare][i],
                      "label": f"{CH_LABEL[ch]}: total yield (#pm8%)"})
        bottom.append({"obj": graph(x, (ly - eval_rec(g, x)) / le), "kind": "markers", "color": col,
                       "marker": [ROOT.kFullCircle, ROOT.kFullSquare][i], "size": 0.9})
        order += [len(items) - 1, len(items) - 2]
    cfg = base_cfg("Signal yield (r = 1)", ["m_{H^{+}} = 130 GeV", "Yield model G(m_{A})"],
                   yRange=(0., 90.), legend=(0.58, 0.64, 0.93, 0.87), legend_order=order, legend_text=0.029,
                   rTitle="Pull", rRange=(-3.5, 3.5), rlines=[0., -2., 2.], show_lumi=True,
                   captionPos=(0.19, 0.69))
    c = plotter.GraphCanvas(items, cfg, style=style, has_data=False, bottom=bottom).draw()
    common.save(c, style, "interpolation", "yield_G")

    # window yields: model prediction vs measured (in-sample closure of the full model)
    for cat in ("SR1E2Mu", "SR3Mu_lowM", "SR3Mu_highM"):
        recs = sorted((r["mA"], r["scalar"][cat][common.ERA]) for r in clos.values()
                      if cat in r["scalar"] and common.ERA in r["scalar"][cat])
        x = np.array([m for m, _ in recs], float)
        npred = np.array([r["n_pred"] for _, r in recs])
        epred = np.array([r["err_pred"] for _, r in recs])
        nmeas = np.array([r["n_meas"] for _, r in recs])
        emeas = np.array([r["err_meas"] for _, r in recs])
        pull = np.array([r["pull"] for _, r in recs])
        items = [{"obj": graph(x, npred, epred), "kind": "band", "color": C_FIT, "alpha": 0.35,
                  "label": "Yield model #pm1#sigma"},
                 {"obj": graph(x, npred), "kind": "line", "color": C_FIT, "width": 3, "label": "Yield model"},
                 {"obj": graph(x, nmeas, emeas), "kind": "points", "color": C_PTS, "label": "Measured (MC)"}]
        ymax = 1.6 * max(nmeas.max(), (npred + epred).max())
        cfg = base_cfg("Window yield (r = 1)", [CH_LABEL[cat], "m_{H^{+}} = 130 GeV"], yRange=(0., ymax),
                       legend_order=[2, 1, 0], rTitle="Pull", rRange=(-3.5, 3.5), rlines=[0., -2., 2.],
                       show_lumi=True, **PULL_LAYOUT)
        bottom = [{"obj": graph(x, pull), "kind": "markers", "color": C_PTS, "size": 0.9}]
        c = plotter.GraphCanvas(items, cfg, style=style, has_data=False, bottom=bottom).draw()
        common.save(c, style, "interpolation", f"yield_window_{cat}")
        print(f"window yield {cat:12s}: max |pull| {np.max(np.abs(pull)):.2f}, "
              f"max |rel| {max(abs(r['rel']) for _, r in recs):.3f}")


def loo_plots(style):
    with open(INTERP / "closure" / "loo_uncertainties.json") as f:
        loo = json.load(f)
    pd, prod = loo["point_detail"], loo["production_restricted"]
    bins = loo["meta"]["norm_ma_bins"]
    # scale = (x0_interp - x0_fit) / sigma_eff, res = sigma_eff_interp / sigma_eff_fit - 1,
    # norm = N_interp / N_MC - 1 (LOO: the point left out of the fits)
    titles = {"scale": "#Deltax_{0} / #sigma_{eff}", "res": "#Delta#sigma_{eff} / #sigma_{eff}",
              "norm": "#DeltaN / N"}
    print("LOO uncertainties (production / all usable points):")
    for q in ("scale", "res", "norm"):
        for cat in ("SR1E2Mu", "SR3Mu_lowM", "SR3Mu_highM"):
            if q == "norm":
                pts = [p for b, *_ in bins for p in pd[q][f"{cat}/{common.ERA}/{b}"]]
                prod_val = {b: prod[q][cat][common.ERA].get(b) for b, *_ in bins}
                prod_val = {b: (v - 1. if v is not None else None) for b, v in prod_val.items()}
                all_val = {b: loo[q][cat][common.ERA][b] - 1. for b, *_ in bins}
            else:
                pts = pd[q][f"{cat}/{common.ERA}"]
                prod_val = {b: prod[q][cat][common.ERA] for b, *_ in bins}
                all_val = {b: loo[q][cat][common.ERA] for b, *_ in bins}
            used = [p for p in pts if p.get("excluded") is None and p.get("signed") is not None]
            filled = [p for p in used if p["production_pairing"]]
            opened = [p for p in used if not p["production_pairing"]]
            items = []
            # bands per mA bin, clipped to the grid
            xb, lo_b, hi_b = [], [], []
            plo, phi = PROD_RANGE[cat]
            for b, lo, hi in bins:
                v = prod_val[b]
                if v is None or max(lo, plo) >= min(hi, phi):
                    continue
                for xx in (max(lo, plo), min(hi, phi) - 1e-3):
                    xb.append(xx)
                    lo_b.append(-v)
                    hi_b.append(v)
            if xb:
                items.append({"obj": curve_band(xb, lo_b, [0.] * len(xb), hi_b), "kind": "band",
                              "color": C_FIT, "alpha": 0.35, "label": "Datacard uncertainty"})
            xa, ya = [], []
            for b, lo, hi in bins:
                for xx in (max(lo, 15.), min(hi, 125.) - 1e-3):
                    xa.append(xx)
                    ya.append(all_val[b])
            items.append({"obj": graph(xa, ya), "kind": "line", "color": C_FIT, "style": ROOT.kDashed,
                          "width": 2, "label": "#pm rms, all usable points"})
            items.append({"obj": graph(xa, [-y for y in ya]), "kind": "line", "color": C_FIT,
                          "style": ROOT.kDashed, "width": 2})
            if filled:
                items.append({"obj": graph([p["mA"] for p in filled], [p["signed"] for p in filled]),
                              "kind": "markers", "color": C_PTS, "label": "LOO, production pairing"})
            if opened:
                items.append({"obj": graph([p["mA"] for p in opened], [p["signed"] for p in opened]),
                              "kind": "markers", "color": C_ALT, "marker": ROOT.kOpenCircle, "size": 1.2,
                              "label": "LOO, other pairing"})
            vals = [abs(p["signed"]) for p in used] + [abs(v) for v in all_val.values()] + \
                   [abs(v) for v in prod_val.values() if v is not None]
            ym = max(vals) if vals else 0.1
            n_lab = sum(1 for it in items if it.get("label"))
            cfg = base_cfg(titles[q], [CH_LABEL[cat], "m_{H^{+}} = 130 GeV, leave-one-out"],
                           yRange=(-1.3 * ym, 2.8 * ym), hlines=[0.], legend=(0.63, 0.87 - 0.05 * n_lab, 0.95, 0.87),
                           legend_text=0.029,
                           vlines=[80., 100.] if q == "norm" else [])
            c = plotter.GraphCanvas(items, cfg, style=style, has_data=False).draw()
            common.save(c, style, "interpolation", f"loo_{q}_{cat}")
            pv = ", ".join(f"{b} {v:.3f}" if v is not None else f"{b} -" for b, v in prod_val.items()) \
                if q == "norm" else f"{prod_val['belowZ']:.3f}"
            av = ", ".join(f"{b} {v:.3f}" for b, v in all_val.items()) if q == "norm" else f"{all_val['belowZ']:.3f}"
            print(f"  {q:5s} {cat:12s} production: {pv} | all: {av} | points {len(filled)} prod + {len(opened)} other")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    a = ap.parse_args()
    params_plots(a.style)
    yield_plots(a.style)
    loo_plots(a.style)


if __name__ == "__main__":
    main()
