"""+-1 sigma templates of every shape nuisance of the 2024 Baseline datacards (B2G statistics checklist:
"+-1 sigma plots of all shape uncertainties").

  python SignalRegion/python/plotSystShapes.py [--style an|pw] [--points 30,60,90,110]

Input: SKNanoOutput/SignalRegionStudy/2024/HcToWABTagEff_v2/templates/MHc130_MA<mA>/Baseline/mc-signal/2024/
<SR1E2Mu|SR3Mu>/: datacard.txt (which process carries which nuisance as `shape`; nuisances turned into lnN by
the shape? pruning are not shapes and are skipped) and shapes.root (<process>_2024, <process>_2024_<syst>Up/Down).
One plot per (point, channel, process, nuisance): nominal, +1 sigma, -1 sigma (events per GeV) and the ratio to
the nominal. Outputs: SignalRegion/plots/<AN|PW>/2024/systematics/MHc130_MA<mA>/<channel>_<process>_<syst>.*
and systematics/summary.txt: per entry the normalization change (Up/Down integral / nominal - 1) and the largest
per-bin |ratio - 1| of the shape (after removing the normalization change), for the AN tables.
"""
import argparse

import ROOT

import common
from common import plotter, CH_LABEL
from plotTemplates import per_gev

ROOT.gErrorIgnoreLevel = ROOT.kWarning
PREFIX = "Baseline/mc-signal/2024"
XTITLE = {"SR1E2Mu": "m(#mu^{+}#mu^{-}) [GeV]", "SR3Mu": "m(#mu^{+}#mu^{-}) [GeV]"}
PROC_LABEL = {"signal": "Signal", "nonprompt": "Nonprompt", "conversion": "Conversion", "others": "Other",
              "WZ": "WZ", "ZZ": "ZZ", "ttW": "t#bar{t}W", "ttZ": "t#bar{t}Z", "ttH": "t#bar{t}H", "tZq": "tZq"}


def shape_entries(card):
    """[(process, nuisance, type)] of the shape lines of a one-bin datacard (value != '-')."""
    procs, out = None, []
    for line in card.read_text().splitlines():
        w = line.split()
        if not w:
            continue
        if w[0] == "process" and procs is None:
            procs = w[1:]
        elif len(w) > 2 and w[1] in ("shape", "shape?") and procs is not None:
            out += [(p, w[0], w[1]) for p, v in zip(procs, w[2:]) if v != "-"]
    return out


def no_errors(h):
    """Bin errors set to 0: the variations are fully correlated with the nominal, a ratio error would mislead."""
    for i in range(h.GetNbinsX() + 2):
        h.SetBinError(i, 0.)
    return h


def shape_dev(h, h0):
    """Largest per-bin |h/h0 - 1| after normalizing h to the integral of h0 (shape-only)."""
    if h.Integral() <= 0 or h0.Integral() <= 0:
        return 0.
    s = h0.Integral() / h.Integral()
    return max((abs(h.GetBinContent(i) * s / h0.GetBinContent(i) - 1.)
                for i in range(1, h0.GetNbinsX() + 1) if h0.GetBinContent(i) > 0), default=0.)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--points", default="30,60,90,110")
    a = ap.parse_args()
    rows = [f"{'point':12s} {'channel':8s} {'process':11s} {'nuisance':52s} {'norm Up':>8s} {'norm Dn':>8s} "
            f"{'shape Up':>8s} {'shape Dn':>8s}"]
    n, skipped = 0, []
    for ma in [int(x) for x in a.points.split(",")]:
        mp = common.masspoint(ma)
        for ch in ("SR1E2Mu", "SR3Mu"):
            base = common.TEMPLATES / mp / PREFIX / ch
            cat, sfx = f"{ch}_{common.ERA}", f"_{common.ERA}"
            f = ROOT.TFile.Open(str(base / "shapes.root"))
            d = f.Get(cat)
            for card_proc, syst, kind in shape_entries(base / "datacard.txt"):
                proc = card_proc[:-len(sfx)] if card_proc.endswith(sfx) else card_proc
                h0, hu, hd = (d.Get(f"{card_proc}{t}") for t in ("", f"_{syst}Up", f"_{syst}Down"))
                if not (h0 and hu and hd) and kind == "shape?":
                    skipped.append(f"{mp} {cat} {card_proc} {syst}")   # shape? without templates: no effect in Combine
                    continue
                if not (h0 and hu and hd):
                    raise SystemExit(f"{mp} {cat}: missing templates of {card_proc} / {syst}")
                if h0.Integral() <= 0:
                    continue
                nu, nd = hu.Integral() / h0.Integral() - 1., hd.Integral() / h0.Integral() - 1.
                su, sd = shape_dev(hu, h0), shape_dev(hd, h0)
                rows.append(f"{mp:12s} {ch:8s} {proc:11s} {syst:52s} {nu:+8.4f} {nd:+8.4f} {su:8.4f} {sd:8.4f}")
                curves = [(PROC_LABEL.get(proc, proc), no_errors(per_gev(h0)), "#000000", "line"),
                          ("+1#sigma", no_errors(per_gev(hu)), plotter.PALETTE_LONG[2], "line"),
                          ("-1#sigma", no_errors(per_gev(hd)), plotter.PALETTE_LONG[0], "line")]
                variations = (hu, hd)
                dev = max((abs(hv.GetBinContent(i) / h0.GetBinContent(i) - 1.)
                           for hv in variations for i in range(1, h0.GetNbinsX() + 1) if h0.GetBinContent(i) > 0),
                          default=0.)
                span = min(1.0, max(0.02, 1.3 * dev))
                cfg = {"xTitle": XTITLE[ch], "yTitle": "Events / GeV", "rTitle": "Var. / Nom.",
                       "rRange": [1. - span, 1. + span],
                       "caption": [f"m_{{H^{{+}}}} = {common.MHC} GeV", f"m_{{A}} = {ma} GeV, {CH_LABEL[ch]}"],
                       "yHeadroom": 1.9,
                       "text": [syst.replace("_", " ")], "textPos": (0.22, 0.60)}
                c = plotter.ShapeCanvas(curves, cfg, style=a.style, era=common.ERA, has_data=False).draw()
                common.save(c, a.style, f"systematics/{mp}", f"{ch}_{proc}_{syst}")
                n += 1
            f.Close()
    out = common.outdir(a.style, "systematics") / "summary.txt"
    rows += ["", "shape? entries without templates (no effect in Combine):"] + skipped
    out.write_text("\n".join(rows) + "\n")
    print(f"{n} plots, {len(skipped)} shape? entries without templates; summary {out}")


if __name__ == "__main__":
    main()
