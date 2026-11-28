"""Prefit binned templates of the 2024 Baseline datacards: stacked backgrounds with the signal (r = 1).

  python SignalRegion/python/plotTemplates.py [--style an|pw] [--points 30,60,90,110]

Input: SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v2/templates/MHc130_MA<mA>/Baseline/mc-signal/2024/
<SR1E2Mu|SR3Mu>/ (local copy of the /pnfs products): shapes.root (directory <channel>_2024, histograms
<process>_2024 and <process>_2024_<syst>Up/Down), datacard.txt (lnN rates), binning.json (window, core bins,
pairing). data_obs is the Asimov background sum (SR blinded): it is only checked against the stack sum,
never drawn.
Groups (paper names, PLAN_Plotting colours): Nonprompt, Diboson (WZ, ZZ), ttX (ttW, ttZ, ttH, tZq),
Conversion, Other. Band (prefit, backgrounds): per bin, template statistics (+) for every nuisance the
envelope max(|up - nom|, |down - nom|) of the background sum, shape nuisances from the Up/Down templates
and lnN nuisances as (kappa - 1) x nominal, correlated across processes, added in quadrature.
The window edges are the first and last bin edges; dashed lines mark the core region (the uniform bins
of width sigma_eff x step between the two side bins). y axis: events per GeV (contents and errors divided by
the bin width, CMS convention for variable bins; the fit uses the per-bin counts, printed in the table).
Outputs: SignalRegion/plots/<AN|PW>/2024/templates/<SR1E2Mu|SR3Mu>_MHc130_MA<mA>.{png,pdf}; a yield
table per point is printed.
"""
import argparse
import json

import ROOT

import common
from common import plotter, CH_LABEL

ROOT.gErrorIgnoreLevel = ROOT.kWarning
PREFIX = "Baseline/mc-signal/2024"
# bottom to top of the stack: (label, processes, colour)
GROUPS = [("Other", ["others"], plotter.PALETTE_LONG[4]),
          ("Conversion", ["conversion"], plotter.PALETTE_LONG[3]),
          ("t#bar{t}X", ["ttW", "ttZ", "ttH", "tZq"], plotter.PALETTE_LONG[2]),
          ("Diboson", ["WZ", "ZZ"], plotter.PALETTE_LONG[1]),
          ("Nonprompt", ["nonprompt"], plotter.PALETTE_LONG[0])]
XTITLE = {"mass1": "m(#mu^{+}#mu^{-}) [GeV]", "lowM": "m_{low}(#mu^{+}#mu^{-}) [GeV]",
          "highM": "m_{high}(#mu^{+}#mu^{-}) [GeV]"}


def lnn_table(card):
    """{nuisance: {process: (kappa_down, kappa_up)}} from the lnN lines of a one-bin datacard."""
    procs, out = None, {}
    for line in card.read_text().splitlines():
        w = line.split()
        if not w:
            continue
        if w[0] == "process" and procs is None:
            procs = w[1:]
        elif len(w) > 2 and w[1] == "lnN" and procs is not None:
            for p, v in zip(procs, w[2:]):
                if v == "-":
                    continue
                if "/" in v:
                    lo, hi = (float(x) for x in v.split("/"))
                else:
                    hi = float(v)
                    lo = 1. / hi
                out.setdefault(w[0], {})[p] = (lo, hi)
    return out


def band(d, bkgs, nom, lnn):
    """Total background with the prefit uncertainty as bin errors."""
    tot = nom.Clone("band")
    tot.SetDirectory(0)
    nb = tot.GetNbinsX()
    var = [tot.GetBinError(i) ** 2 for i in range(nb + 2)]
    names = {k.GetName() for k in d.GetListOfKeys()}
    shape_systs = sorted({n[len(p) + 1:-2] for p in bkgs for n in names if n.startswith(p + "_") and n.endswith("Up")})
    for s in shape_systs:
        up, dn = [0.] * (nb + 2), [0.] * (nb + 2)
        for p in bkgs:
            h0 = d.Get(p)
            hu, hd = d.Get(f"{p}_{s}Up"), d.Get(f"{p}_{s}Down")
            if not hu or not hd:
                continue
            for i in range(1, nb + 1):
                up[i] += hu.GetBinContent(i) - h0.GetBinContent(i)
                dn[i] += hd.GetBinContent(i) - h0.GetBinContent(i)
        for i in range(1, nb + 1):
            var[i] += max(abs(up[i]), abs(dn[i])) ** 2
    for name, per in lnn.items():
        up, dn = [0.] * (nb + 2), [0.] * (nb + 2)
        for p, (klo, khi) in per.items():
            if p not in bkgs:
                continue
            h0 = d.Get(p)
            for i in range(1, nb + 1):
                up[i] += (khi - 1.) * h0.GetBinContent(i)
                dn[i] += (klo - 1.) * h0.GetBinContent(i)
        for i in range(1, nb + 1):
            var[i] += max(abs(up[i]), abs(dn[i])) ** 2
    for i in range(1, nb + 1):
        tot.SetBinError(i, var[i] ** 0.5)
    return tot, shape_systs


def per_gev(h):
    out = h.Clone(h.GetName() + "_perGeV")
    out.SetDirectory(0)
    for i in range(1, out.GetNbinsX() + 1):
        w = out.GetXaxis().GetBinWidth(i)
        out.SetBinContent(i, h.GetBinContent(i) / w)
        out.SetBinError(i, h.GetBinError(i) / w)
    return out


def conv_note(nom, conv):
    """Core bin with the largest conversion share: '<lo>-<hi> GeV: conv x of bkg y'."""
    best = max(range(2, nom.GetNbinsX()), key=lambda i: conv.GetBinContent(i) / max(nom.GetBinContent(i), 1e-9))
    ax = nom.GetXaxis()
    return (f"{ax.GetBinLowEdge(best):.2f}-{ax.GetBinUpEdge(best):.2f} GeV: conversion "
            f"{conv.GetBinContent(best):.2f} +- {conv.GetBinError(best):.2f} of bkg {nom.GetBinContent(best):.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--points", default="30,60,90,110")
    a = ap.parse_args()

    print(f"{'point':13s} {'channel':8s} {'bins':>4s} {'core':>4s} {'window [GeV]':>16s} {'sig_eff':>7s} "
          f"{'bkg':>8s} {'signal':>7s} {'data_obs-bkg':>12s}  core bin with max conversion share")
    for ma in [int(x) for x in a.points.split(",")]:
        mp = common.masspoint(ma)
        for ch in ("SR1E2Mu", "SR3Mu"):
            base = common.TEMPLATES / mp / PREFIX / ch
            cat = f"{ch}_{common.ERA}"
            with open(base / "binning.json") as f:
                binfo = json.load(f)["categories"][cat]
            f = ROOT.TFile.Open(str(base / "shapes.root"))
            d = f.Get(cat)
            sfx = f"_{common.ERA}"
            stack, bkgs, nom = [], [], None
            for label, procs, col in GROUPS:
                h = None
                for p in procs:
                    hp = d.Get(p + sfx)
                    if not hp:
                        raise SystemExit(f"{mp} {cat}: missing {p + sfx}")
                    bkgs.append(p + sfx)
                    if h is None:
                        h = hp.Clone(f"g_{label}_{ch}_{ma}")
                        h.SetDirectory(0)
                    else:
                        h.Add(hp)
                    if nom is None:
                        nom = hp.Clone("nom")
                        nom.SetDirectory(0)
                    else:
                        nom.Add(hp)
                stack.append((label, h, col))
            sig = d.Get("signal" + sfx).Clone(f"sig_{ch}_{ma}")
            sig.SetDirectory(0)
            obs = d.Get("data_obs")
            asimov_diff = obs.Integral() - nom.Integral()
            tot, _ = band(d, bkgs, nom, lnn_table(base / "datacard.txt"))
            edges = binfo["bin_edges"]
            core = edges[1:-1] if len(edges) > 3 else []
            width = (core[-1] - core[0]) / (len(core) - 1) if len(core) > 1 else 0.
            print(f"{mp:13s} {ch:8s} {binfo['nbins']:4d} {binfo['n_core_bins']:4d} "
                  f"{binfo['mass_min']:7.2f}-{binfo['mass_max']:7.2f} {binfo['sigma_eff']:7.3f} "
                  f"{nom.Integral():8.1f} {sig.Integral():7.2f} {asimov_diff:12.2e}  {conv_note(nom, stack[1][1])}")
            cfg = {"xTitle": XTITLE.get(binfo["pairing"], "m(#mu^{+}#mu^{-}) [GeV]"), "yTitle": "Events / GeV",
                   "caption": [CH_LABEL[ch]], "yHeadroom": 2.6, "bandLabel": "Stat.+Syst. (prefit)",
                   "signalHeader": "(m_{H^{+}}, m_{A}) [GeV]", "hasData": True,
                   "vlines": [core[0], core[-1]] if core else [],
                   "text": [f"Window {binfo['mass_min']:.1f}-{binfo['mass_max']:.1f} GeV",
                            f"{binfo['n_core_bins']} core bins of {width:.2f} GeV, #sigma_{{eff}} = {binfo['sigma_eff']:.2f} GeV"],
                   "textPos": (0.21, 0.66), "textSize": 0.026, "signalLegend": (0.20, 0.465, 0.55, 0.575)}
            c = plotter.StackCanvas(None, [(lab, per_gev(h), col) for lab, h, col in stack], cfg, style=a.style,
                                    band=per_gev(tot), signals=[(f"(130, {ma}), r = 1", per_gev(sig))]).draw()
            common.save(c, a.style, "templates", f"{ch}_{mp}")
            f.Close()


if __name__ == "__main__":
    main()
