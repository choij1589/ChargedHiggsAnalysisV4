"""b-tag efficiency maps for 2024 (docs/PLAN_Signal.md step 1, S1 (a), 2026-11-28).

  python BTagEff/python/makeBTagEff.py [--input SKNanoOutput/DiLepton/MeasBTagEff/2024/TTLL_powheg.root]
                                       [--crosscheck SKNanoOutput/TriLepton/<tag>/2024]

Input: the den / num histograms of DiLepton `MeasBTagEff` on TTLL (keys
`tagging#b##era#2024##flavor#F##systematic#central##den` and
`tagging#b##era#2024##tagger#<T>##working_point#M##flavor#F##systematic#central##num`, |eta| x pT,
F = 0, 4, 5). The JSON is made with SKNano's own converter functions (scripts/makeTaggingEffJson.py of the
SKNanoAnalyzer clone: makeTempEffHist, makingJson), with era 2024 instead of its hard-coded 2017.
Cross-check (S1 (b)): the same histograms of the TriLepton BTagEffHists production, all MC summed.
Output: BTagEff/results/2024/btaggingEff_HcToWA.json (correctionlib, as BTV/btaggingEff.json),
BTagEff/results/2024/efficiencies.txt, plots BTagEff/plots/AN/2024/eff_<b|c|light>_<TTLL|TriLepton>.png
(efficiency vs pT, one series per |eta| bin; --style pw: BTagEff/plots/PW/2024/*.pdf).
Plots are drawn with Common/Tools/plotter.py (EffCanvas, one pad; 2026-11-28, user rule: every plot with the
project's plotting library); the efficiency, its binomial error, the JSON and efficiencies.txt are unchanged.
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

import ROOT

ROOT.gROOT.SetBatch(True)
REPO = Path(__file__).resolve().parents[2]
SKNANO = Path(os.environ.get("SKNANO_CLONE", Path.home() / "Sync/workspace/SKNanoAnalyzer_Run3"))
RES = REPO / "BTagEff" / "results" / "2024"
FLAV = {0: "light", 4: "c", 5: "b"}


def load_converter():
    # import by its own name from its directory: the converter's process pool (forkserver in Python 3.14)
    # re-imports the module of the pickled functions in the workers
    sys.path.insert(0, str(SKNANO / "scripts"))
    import makeTaggingEffJson
    return makeTaggingEffJson


def keys(f, kind):
    return [k.GetName() for k in f.GetListOfKeys() if k.GetName().startswith("tagging#b") and k.GetName().endswith("##" + kind)]


def eff_hists(paths):
    """Sum den / num over files; returns {flav: (num, den)}."""
    out = {}
    for p in paths:
        f = ROOT.TFile.Open(str(p))
        for kd in keys(f, "den"):
            fl = int(kd.split("##flavor#")[1].split("##")[0])
            kn = [k for k in keys(f, "num") if f"##flavor#{fl}##" in k]
            if len(kn) != 1:
                continue
            d, n = f.Get(kd), f.Get(kn[0])
            if fl not in out:
                out[fl] = (n.Clone(f"num{fl}_{id(paths)}"), d.Clone(f"den{fl}_{id(paths)}"))
                out[fl][0].SetDirectory(0)
                out[fl][1].SetDirectory(0)
            else:
                out[fl][0].Add(n)
                out[fl][1].Add(d)
    return out


def table(effs, label):
    lines = [f"{label}: efficiency (num/den) per |eta| (x) and pT (y) bin"]
    for fl, (n, d) in sorted(effs.items()):
        lines.append(f"  flavour {fl} ({FLAV[fl]}):")
        for iy in range(1, d.GetNbinsY() + 1):
            row = []
            for ix in range(1, d.GetNbinsX() + 1):
                den = d.GetBinContent(ix, iy)
                row.append(f"{n.GetBinContent(ix, iy) / den:.3f}" if den > 0 else "  -  ")
            lines.append(f"    pT [{d.GetYaxis().GetBinLowEdge(iy):.0f},{d.GetYaxis().GetBinUpEdge(iy):.0f}]: " + " ".join(row))
    return lines


# plotting (user rule 2026-11-28: every plot with Common/Tools/plotter.py): one canvas per flavour and source,
# the |eta| bins as series (shifted in log pT so the error bars do not overlap), the legend in a region without
# points: below the points for b jets (fixed range), above them for c and light jets (range from the points)
ETA_STYLE = [("#3f90da", 20), ("#ffa90e", 21), ("#bd1f01", 22), ("#832db6", 33)]
B_RANGE = (0., 1.3)
LEGEND = {"low": (0.40, 0.21, 0.72, 0.43), "high": (0.655, 0.67, 0.95, 0.89)}
POINTS_BELOW = 0.6  # c, light: the highest point (with its error) at <= 60% of the frame, the legend above
SOURCE = {"TTLL": "t#bar{t}#rightarrow2l2#nu (TTLL)", "TriLepton": "3l preselection, all MC"}
TAGGER = "UParT, medium WP"


def nice_ceil(v):
    """Smallest of 1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8 x 10^k above v."""
    import math
    k = math.floor(math.log10(v))
    for m in (1., 1.2, 1.5, 2., 2.5, 3., 4., 5., 6., 8., 10.):
        if m * 10 ** k >= v:
            return m * 10 ** k


def eff_graphs(n, d, tag, fl):
    """[(|eta| label, TGraphAsymmErrors)] of num/den vs pT per |eta| bin; the efficiency and its error are
    those of TH1::Divide(num, den, 1, 1, "B") (weighted histograms: binomial errors)."""
    import array
    ax, ay = d.GetXaxis(), d.GetYaxis()
    nx, ny = d.GetNbinsX(), d.GetNbinsY()
    out = []
    for ix in range(1, nx + 1):
        pn = n.ProjectionY(f"pn{fl}{ix}{tag}", ix, ix)
        pd = d.ProjectionY(f"pd{fl}{ix}{tag}", ix, ix)
        e = pn.Clone(f"eff{fl}{ix}{tag}")
        e.Divide(pn, pd, 1., 1., "B")
        shift = 1. + 0.035 * (ix - (nx + 1) / 2.)
        x, exl, exh, y, ey = (array.array("d") for _ in range(5))
        for iy in range(1, ny + 1):
            if pd.GetBinContent(iy) <= 0:
                continue
            lo, hi = ay.GetBinLowEdge(iy), ay.GetBinUpEdge(iy)
            xc = (lo * hi) ** 0.5 * shift
            x.append(xc)
            exl.append(xc - lo)
            exh.append(hi - xc)
            y.append(e.GetBinContent(iy))
            ey.append(e.GetBinError(iy))
        g = ROOT.TGraphAsymmErrors(len(x), x, y, exl, exh, ey, ey)
        out.append((f"{ax.GetBinLowEdge(ix):.1f} < |#eta| < {ax.GetBinUpEdge(ix):.1f}", g))
    return out


def plot(effs, tag, style="an"):
    sys.path.insert(0, str(REPO / "Common" / "Tools"))
    import plotter
    fmt = plotter.STYLES[style]["format"]
    od = plotter.plot_dir("BTagEff", style, "2024")
    od.mkdir(parents=True, exist_ok=True)
    for fl, (n, d) in sorted(effs.items()):
        graphs = eff_graphs(n, d, tag, fl)
        top = [(lab, g, *ETA_STYLE[i % len(ETA_STYLE)]) for i, (lab, g) in enumerate(graphs)]
        ay = d.GetYaxis()
        if fl == 5:
            yrange, leg = B_RANGE, LEGEND["low"]
        else:
            top_y = max(g.GetPointY(i) + g.GetErrorYhigh(i) for _, g in graphs for i in range(g.GetN()))
            yrange, leg = (0., nice_ceil(top_y / POINTS_BELOW)), LEGEND["high"]
        cfg = {"xTitle": "p_{T} [GeV]", "yTitle": "Tagging efficiency", "xRange": (ay.GetXmin(), ay.GetXmax()),
               "logx": True, "yRange": yrange, "no_ratio": True, "show_lumi": False, "yTitleOffset": 1.45,
               "caption": [f"{FLAV[fl]} jets, {TAGGER}", SOURCE.get(tag, tag)], "captionPos": (0.205, 0.79),
               "legend": leg, "legend_text": 0.032}
        plotter.EffCanvas(top, [], cfg, style=style, era="2024", has_data=False).draw() \
            .save(str(od / f"eff_{FLAV[fl]}_{tag}.{fmt}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(REPO / "SKNanoOutput/DiLepton/MeasBTagEff/2024/TTLL_powheg.root"))
    ap.add_argument("--crosscheck", default=None, help="TriLepton production dir with BTagEffHists (all MC summed)")
    ap.add_argument("--style", default="an", choices=("an", "pw"), help="plot style (plotter.py): an = png, pw = pdf")
    a = ap.parse_args()
    RES.mkdir(parents=True, exist_ok=True)
    mk = load_converter()
    lines = []
    effs = eff_hists([a.input])
    lines += table(effs, f"TTLL (DiLepton MeasBTagEff, {a.input})")
    plot(effs, "TTLL", a.style)
    cwd = os.getcwd()
    tmp = RES / "_tmp"
    tmp.mkdir(exist_ok=True)
    os.chdir(tmp)
    try:
        f = ROOT.TFile.Open(a.input)
        mk.makeTempEffHist(f)
        f.Close()
        cj = mk.makingJson("2024", "b")
        (RES / "btaggingEff_HcToWA.json").write_text(json.dumps(cj, indent=1))
    finally:
        os.chdir(cwd)
        for p in tmp.glob("*"):
            p.unlink()
        tmp.rmdir()
    if a.crosscheck:
        # each process once (as the SR prediction): no data, no signal, no alternative WZ (FxFx) and no DYG
        # (overlaps DY 2J); found by the an-writer check 2026-11-28 (WZ was counted twice)
        skip = ("MuonEG", "_Muon0", "_Muon1", "TTToHcToWA", "WZto3LNu_1J_amcatnloFXFX", "DYGto2LG")
        mc = [p for p in glob.glob(os.path.join(a.crosscheck, "*.root"))
              if not any(s in os.path.basename(p) for s in skip)]
        effx = eff_hists(mc)
        lines += table(effx, f"cross-check: TriLepton preselection, {len(mc)} MC samples summed")
        plot(effx, "TriLepton", a.style)
    (RES / "efficiencies.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
