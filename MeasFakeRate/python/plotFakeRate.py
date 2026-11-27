"""Fake-rate plots from measFakeRate.py --step rates (PLAN_BkgEst step 3).

  python MeasFakeRate/python/plotFakeRate.py [--style an|pw]

Input: MeasFakeRate/results/2024/<flavour>/rates.json (prompt scale from the bounded MT fit, user 2026-11-27).
Per flavour and |eta| row, versus pT_corr (log x):
  rates_<fl>_eta<i>:      data (error = bin-by-bin total: stat (+) the largest deviation of each variation
                          group: PromptNorm, away-jet pT (Away60 / Away20 mu, Away30 e), b tag; user
                          2026-11-27: bin-by-bin uncertainty), QCD MC and tt MC (nonprompt), MC / data below;
  variations_<fl>_eta<i>: data Central and each variation, variation / Central below;
  flavour_<fl>_eta<i>:    QCD and tt MC per class b, c, light (input to F2), tt / QCD below;
  map_<fl>:               2D map of the data rate with the total error.
Bins whose rate was replaced by the previous pT bin (negative or undefined) are drawn open.
The total uncertainty per bin is also written to results/2024/<fl>/rates_total.txt.
Output: MeasFakeRate/plots/AN/2024/FakeRate/.
"""
import argparse
import array
import json
import math
import sys
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
import plotter  # noqa: E402

ERA = "2024"
RES = REPO / "MeasFakeRate" / "results" / ERA
LEP = {"mu": "#mu", "el": "e"}
ETA = {"mu": "|#eta|", "el": "|#eta_{SC}|"}
AWAY = {"mu": ("Away60", "Away20"), "el": ("Away60", "Away30")}


def total_unc(r, fl, i):
    """Per bin: stat, and the largest |var - central| of each group; total in quadrature."""
    c = r["data"]["Central"][i]
    out = []
    for j, b in enumerate(c):
        f = b["f"]
        g = {"stat": b["err"]}
        g["PromptNorm"] = max(abs(r["data"][v][i][j]["f"] - f) for v in ("PromptNormUp", "PromptNormDown"))
        g["AwayJet"] = max(abs(r["data"][v][i][j]["f"] - f) for v in AWAY[fl])
        g["BTag"] = abs(r["data"]["BTag"][i][j]["f"] - f)
        g = {k: (v if not math.isnan(v) else 0.) for k, v in g.items()}
        g["total"] = math.sqrt(sum(v * v for v in g.values()))
        out.append(g)
    return out


def graph(ey, vals, errs, shift=0.):
    n = len(vals)
    x = array.array("d", [math.sqrt(ey[j] * ey[j + 1]) * (1 + shift) for j in range(n)])
    exl = array.array("d", [x[j] - ey[j] for j in range(n)])
    exh = array.array("d", [ey[j + 1] - x[j] for j in range(n)])
    y = array.array("d", [v if not math.isnan(v) else -1. for v in vals])
    e = array.array("d", [v if not math.isnan(v) else 0. for v in errs])
    return ROOT.TGraphAsymmErrors(n, x, y, exl, exh, e, e)


def ratio(num, den, nerr):
    return [n / d if d > 0 else float("nan") for n, d in zip(num, den)], \
           [e / d if d > 0 else 0. for e, d in zip(nerr, den)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    a = ap.parse_args()
    fmt = plotter.STYLES[a.style]["format"]
    od = REPO / "MeasFakeRate" / "plots" / plotter.STYLES[a.style]["dir"] / ERA / "FakeRate"
    od.mkdir(parents=True, exist_ok=True)
    for fl in ("mu", "el"):
        r = json.loads((RES / fl / "rates.json").read_text())
        ex, ey = r["eta"], r["pt"]
        lines = [f"# data fake rate, {fl}: central +- total (stat, PromptNorm, AwayJet, BTag) per bin (plotFakeRate.py)"]
        hmap = ROOT.TH2D(f"map_{fl}", "", len(ex) - 1, array.array("d", ex), len(ey) - 1, array.array("d", ey))
        for i in range(len(ex) - 1):
            si = str(i)
            c = r["data"]["Central"][si]
            tu = total_unc(r, fl, si)
            f = [b["f"] for b in c]
            ft = [t["total"] for t in tu]
            for j in range(len(f)):
                hmap.SetBinContent(i + 1, j + 1, f[j])
                hmap.SetBinError(i + 1, j + 1, ft[j])
            lines.append(f"## {ETA[fl]} {ex[i]}-{ex[i + 1]}")
            for j, (b, t) in enumerate(zip(c, tu)):
                lines.append(f"  pT {ey[j]:.0f}-{ey[j + 1]:.0f} ({b['path']}): {b['f']:.4f} +- {t['total']:.4f} ({t['total'] / b['f']:.1%}; "
                             + ", ".join(f"{k} {v / b['f']:.1%}" for k, v in t.items() if k != "total") + ")"
                             + ("  [replaced]" if b.get("replaced") else ""))
            cap = [f"{LEP[fl]}, {ex[i]:g} < {ETA[fl]} < {ex[i + 1]:g}"]
            base = {"xTitle": "p_{T}^{corr} [GeV]", "yTitle": "Fake rate", "xRange": [ey[0], ey[-1]], "logx": True,
                    "yRange": [0., 1.0], "caption": cap, "legend": (0.50, 0.66, 0.92, 0.88)}
            # 1. data vs MC
            qcd = r["mc"]["qcd"]["nonprompt"][si]
            tt = r["mc"]["tt"]["nonprompt"][si]
            gd = graph(ey, f, ft)
            gq = graph(ey, [b["f"] for b in qcd], [b["err"] for b in qcd], 0.04)
            gt = graph(ey, [b["f"] for b in tt], [b["err"] for b in tt], -0.04)
            rq = graph(ey, *ratio([b["f"] for b in qcd], f, [b["err"] for b in qcd]), 0.04)
            rt = graph(ey, *ratio([b["f"] for b in tt], f, [b["err"] for b in tt]), -0.04)
            rd = graph(ey, [1.] * len(f), [t / v if v > 0 else 0. for t, v in zip(ft, f)])
            cfg = dict(base, rTitle="MC / data", rRange=(0., 2.))
            plotter.EffCanvas([("Data (total unc.)", gd, "#000000", 20), ("QCD MC", gq, "#3f90da", 21),
                               ("t#bar{t} MC", gt, "#bd1f01", 22)],
                              [("Data unc.", rd, "#000000", 1), ("QCD", rq, "#3f90da", 21), ("t#bar{t}", rt, "#bd1f01", 22)],
                              cfg, style=a.style).draw().save(str(od / f"rates_{fl}_eta{i}.{fmt}"))
            # 2. variations
            top, bot = [("Central", graph(ey, f, [b["err"] for b in c]), "#000000", 20)], []
            cols = {"PromptNormUp": "#3f90da", "PromptNormDown": "#92dadd", "Away20": "#ffa90e", "Away30": "#e76300",
                    "Away60": "#bd1f01", "BTag": "#832db6"}
            k = 0
            for v, col in cols.items():
                if v not in r["data"]:
                    continue
                k += 1
                vv = [b["f"] for b in r["data"][v][si]]
                sh = 0.025 * (k - 3.5)
                top.append((v, graph(ey, vv, [0.] * len(vv), sh), col, 20 + k))
                bot.append((v, graph(ey, [x / y if y > 0 else float("nan") for x, y in zip(vv, f)], [0.] * len(vv), sh), col, 20 + k))
            cfg = dict(base, rTitle="Var. / Central", rRange=(0.5, 1.5), legend=(0.45, 0.60, 0.92, 0.88), legend_columns=2,
                       no_rlegend=True)
            plotter.EffCanvas(top, bot, cfg, style=a.style).draw().save(str(od / f"variations_{fl}_eta{i}.{fmt}"))
            # 3. flavour split (F2)
            top, bot = [], []
            for cl, col in (("b", "#bd1f01"), ("c", "#ffa90e"), ("light", "#3f90da")):
                q = r["mc"]["qcd"][cl][si]
                t = r["mc"]["tt"][cl][si]
                top.append((f"QCD {cl}", graph(ey, [b["f"] for b in q], [b["err"] for b in q], 0.03), col, 20))
                top.append((f"t#bar{{t}} {cl}", graph(ey, [b["f"] for b in t], [b["err"] for b in t], -0.03), col, 24))
                rr, re = ratio([b["f"] for b in t], [b["f"] for b in q], [b["err"] for b in t])
                bot.append((cl, graph(ey, rr, re), col, 24))
            cfg = dict(base, rTitle="t#bar{t} / QCD", rRange=(0., 2.), legend=(0.45, 0.62, 0.92, 0.88), legend_columns=2,
                       no_rlegend=True)
            plotter.EffCanvas(top, bot, cfg, style=a.style, has_data=False).draw().save(str(od / f"flavour_{fl}_eta{i}.{fmt}"))
        cfg = {"xTitle": ETA[fl], "yTitle": "p_{T}^{corr} [GeV]", "zTitle": "Fake rate", "logy": True,
               "text": "4.3f", "text_errors": True, "zRange": (0., 0.7), "caption": [f"{LEP[fl]}, data"]}
        plotter.Map2DCanvas(hmap, cfg, style=a.style).draw().save(str(od / f"map_{fl}.{fmt}"))
        (RES / fl / "rates_total.txt").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))


if __name__ == "__main__":
    main()
