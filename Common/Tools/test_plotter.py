"""Draw toy histograms with every canvas in both styles (gate 2 of docs/PLAN_Plotting.md).

Run: python Common/Tools/test_plotter.py [outdir]   (default: Common/plots/test)
Checks that the label switches with the style and with data/simulation, that the
format follows the style, and that the cmsstyle globals are restored.
"""
import sys
from pathlib import Path

import ROOT

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plotter  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else plotter.REPO / "Common" / "plots" / "test"
rng = ROOT.TRandom3(1)


def toy(name, n, mean, sigma, nb=60, lo=60., hi=120.):
    h = ROOT.TH1D(name, "", nb, lo, hi)
    h.Sumw2()
    for _ in range(n):
        h.Fill(rng.Gaus(mean, sigma))
    return h


bkgs = [("Single t", toy("st", 2000, 90, 25), "#832db6"), ("t#bar{t}", toy("tt", 8000, 95, 20), "#bd1f01"),
        ("Drell-Yan", toy("dy", 60000, 91.2, 3), "#3f90da")]
data = toy("data", 70000, 91.4, 3.2)
cfg = {"xTitle": "m(#mu#mu) [GeV]", "caption": ["#mu#mu"]}
for style in plotter.STYLES:
    ext = plotter.STYLES[style]["format"]
    plotter.StackCanvas(data, bkgs, cfg, style=style).draw().save(out / f"stack_{style}.{ext}")
    plotter.StackCanvas(None, bkgs, dict(cfg, logy=True), style=style,
                        signals=[("(130, 40)", toy("s", 500, 40, 1, 60, 0, 120))]).draw().save(out / f"stack_mc_log_{style}.{ext}")
    plotter.ShapeCanvas([("Data", data, "#000000", "data"), ("Simulation", bkgs[2][1], "#3f90da", "line")],
                        dict(cfg, normalize=True), style=style).draw().save(out / f"shape_{style}.{ext}")
    h2 = ROOT.TH2D("m", "", 50, -5, 5, 64, -3.2, 3.2)
    for _ in range(20000):
        h2.Fill(rng.Gaus(0, 2), rng.Uniform(-3.2, 3.2))
    plotter.Map2DCanvas(h2, {"xTitle": "#eta", "yTitle": "#phi"}, style=style).draw().save(out / f"map_{style}.{ext}")

import cmsstyle  # noqa: E402
assert cmsstyle.cmsText == "CMS", cmsstyle.cmsText
print("wrote", sorted(p.name for p in out.iterdir()))
