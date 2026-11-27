"""MT and MET in the W-enriched region of the fake-rate measurement (PLAN_BkgEst step 2, F5 (b)).

  python MeasFakeRate/python/plotWRegion.py [--style an|pw]

W region: one loose lepton of the flavour, the path fired with its offline pT cut, away jet (Nom,
pT > 40 GeV), MT > 60 GeV (MeasFakeRate.cc). Histograms <top>/<path>/Control/W/<id>/<class>/{MT,MET}.
Data (prescaled) vs the prompt MC by group, scaled by the prompt scale s of the (path, ID) from the
Z window (results/2024/<flavour>/gate.json), with the QCD-enriched MC (same s) on top for comparison.
Output: MeasFakeRate/plots/AN/2024/WRegion/<path>_<id>_{MT,MET}.png (and .../Inc/ for the inclusive
single-lepton region, MT only, to show the W region in context).
"""
import argparse
import json
import sys
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
sys.path.insert(0, str(REPO / "MeasFakeRate" / "python"))
import plotter  # noqa: E402
import measFakeRate as M  # noqa: E402

GROUPS = [("VV", ["WW_pythia", "WZ_pythia", "ZZ_pythia"], "#94a4a2"),
          ("Single top", ["ST_tch_top_lep", "ST_tch_antitop_lep", "ST_tW_top_Lep", "ST_tW_antitop_Lep",
                          "ST_tW_top_Semilep", "ST_tW_antitop_Semilep", "ST_sch_top_Lep", "ST_sch_antitop_Lep"], "#832db6"),
          ("t#bar{t}", ["TTLL_powheg", "TTLJ_powheg"], "#bd1f01"),
          ("DY", [s for s in M.PROMPT if s.startswith("DY")], "#ffa90e"),
          ("W", ["WtoENu_2J", "WtoMuNu_2J", "WtoTauNu_2J"], "#3f90da")]
QCD_COLOR = "#b9ac70"
TITLES = {"MT": "m_{T} [GeV]", "MET": "p_{T}^{miss} [GeV]"}
LEP = {"mu": "#mu", "el": "e"}


def hsum(files, path):
    tot = None
    for f in files:
        tf = ROOT.TFile.Open(f)
        for cls in ("prompt", "nonprompt", "data"):
            h = tf.Get(path.format(cls=cls))
            if not h:
                continue
            if tot is None:
                tot = h.Clone(f"h{abs(hash((f, path)))}")
                tot.SetDirectory(0)
                tot.Reset()
            tot.Add(h)
        tf.Close()
    return tot


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    a = ap.parse_args()
    outdir = REPO / "MeasFakeRate" / "plots" / plotter.STYLES[a.style]["dir"] / M.ERA / "WRegion"
    lines = ["# W region (MT > 60 GeV), data / (s x prompt MC) and s x QCD MC / data, by MET (plotWRegion.py)"]
    for fl in ("mu", "el"):
        st = M.Store(fl)
        gate = json.loads((M.RES / fl / "gate.json").read_text())
        top = st.top
        pfile = lambda s: str(M.OUT / "MeasMuFR_MeasElFR" / M.ERA / f"{s}.root")
        for p in M.FLAV[fl]["paths"]:
            for idn in ("tight", "loose"):
                s = gate[p][idn]["s"]
                for region, var in (("W", "MT"), ("W", "MET"), ("Inc", "MT")):
                    rel = f"{top}/{p}/Control/{region}/{idn}/{{cls}}/{var}"
                    data = hsum(st.files["data"], rel)
                    stack = []
                    for lab, samples, col in GROUPS:
                        h = hsum([pfile(x) for x in samples], rel)
                        h.Scale(s)
                        stack.append((lab, h, col))
                    q = hsum(st.files["qcd"], rel)
                    q.Scale(s)
                    stack.append(("QCD (MC)", q, QCD_COLOR))
                    cfg = {"xTitle": TITLES[var], "xRange": [60., 150.] if (region == "W" and var == "MT") else [0., 150.],
                           "rebin": 2, "overflow": True, "rRange": [0., 3.] if fl == "el" else [0.5, 2.0],
                           "caption": [f"{p}, {idn} {LEP[fl]}", "W region" if region == "W" else "single lepton",
                                       f"MC #times s = {s:.3g}"],
                           "bandLabel": "MC stat."}
                    c = plotter.StackCanvas(data, stack, cfg, style=a.style).draw()
                    sub = "" if region == "W" else "Inc/"
                    path = outdir / f"{sub}{p}_{idn}_{var}.{plotter.STYLES[a.style]['format']}"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    c.save(str(path))
                    if region == "W" and var == "MET":
                        row = []
                        for lo, hi in ((0, 25), (25, 50), (50, 80), (80, 1e9)):
                            b1, b2 = data.FindBin(lo + 1e-3), data.FindBin(hi - 1e-3) if hi < 1e8 else data.GetNbinsX() + 1
                            d = data.Integral(b1, b2)
                            pr = sum(h.Integral(b1, b2) for lab, h, _ in stack if lab != "QCD (MC)")
                            row.append(f"{lo:.0f}-{hi:.0f}: {d / pr:.2f} (QCD/data {q.Integral(b1, b2) / d:.2f}, N {d:.0f})"
                                       if d > 0 and pr > 0 else f"{lo}-{hi}: -")
                        lines.append(f"{p} {idn}: " + "; ".join(row))
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
