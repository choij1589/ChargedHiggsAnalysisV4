"""Prompt scale from a template fit in the inclusive single-lepton region (proposal, user 2026-11-27).

  python MeasFakeRate/python/fitPromptScale.py [--var MT|MET] [--style an|pw]

Per (path, ID): extended binned maximum-likelihood fit (RooFit) of the data distribution of --var in the
inclusive single-lepton region (Control/Inc: one loose lepton, path fired with its offline pT cut, away jet
pT > 40 GeV, no MT or MET requirement) with two templates (RooHistPdf):
  prompt = the 22 prompt-MC samples (all classes), QCD = the QCD-enriched MC of the flavour (F8),
QCD yield free, prompt yield free (--mode free), fixed to s_Z (zfixed) or within s_Z (1 +- --bound)
(zbound, the adopted scale, user 2026-11-27). s_fit = N_prompt(fit) / N_prompt(MC), k_QCD = N_QCD(fit) / N_QCD(MC).
The template statistics are not in the likelihood (RooHistPdf); their effect is reported separately.
Check: Z window (OS, 76-106 GeV, Nom): data / (s_fit x prompt MC), with its statistical error, and the
Z-window scale s_Z of measFakeRate.py --step gate for comparison.
Output: MeasFakeRate/results/2024/<flavour>/promptfit_<var>.{txt,json};
        post-fit plots MeasFakeRate/plots/AN/2024/PromptFit/<path>_<id>_<var>.png.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
sys.path.insert(0, str(REPO / "MeasFakeRate" / "python"))
import plotter  # noqa: E402
import measFakeRate as M  # noqa: E402

ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)
TITLES = {"MT": "m_{T} [GeV]", "MET": "p_{T}^{miss} [GeV]"}
LEP = {"mu": "#mu", "el": "e"}


def fit_one(data_h, prompt_h, qcd_h, var, tag, s_z=None, mode="free", bound=0.3):
    """mode free: prompt and QCD yields free; zfixed: prompt scale fixed to s_z; zbound: prompt scale
    r x s_z with r in [1 - bound, 1 + bound] (user 2026-11-27). QCD yield always free."""
    x = ROOT.RooRealVar(f"x_{tag}", TITLES[var], data_h.GetXaxis().GetXmin(), data_h.GetXaxis().GetXmax())
    x.setBins(data_h.GetNbinsX())
    al = ROOT.RooArgList(x)
    dh = ROOT.RooDataHist(f"d_{tag}", "", al, data_h)
    ph = ROOT.RooDataHist(f"p_{tag}", "", al, prompt_h)
    qh = ROOT.RooDataHist(f"q_{tag}", "", al, qcd_h)
    pp = ROOT.RooHistPdf(f"pp_{tag}", "", ROOT.RooArgSet(x), ph)
    qp = ROOT.RooHistPdf(f"qp_{tag}", "", ROOT.RooArgSet(x), qh)
    nd = data_h.Integral()
    mp, mq = prompt_h.Integral(), qcd_h.Integral()
    keep = []
    if mode == "free":
        npr = ROOT.RooRealVar(f"np_{tag}", "", 0.7 * nd, 0., 3. * nd)
        rpar = None
    else:
        rpar = ROOT.RooRealVar(f"r_{tag}", "", 1., 1. - bound, 1. + bound)
        if mode == "zfixed":
            rpar.setConstant(True)
        npr = ROOT.RooFormulaVar(f"np_{tag}", f"@0*{s_z * mp!r}", ROOT.RooArgList(rpar))
        keep.append(rpar)
    nq = ROOT.RooRealVar(f"nq_{tag}", "", 0.3 * nd, 0., 3. * nd)
    model = ROOT.RooAddPdf(f"m_{tag}", "", ROOT.RooArgList(pp, qp), ROOT.RooArgList(npr, nq))
    res = model.fitTo(dh, ROOT.RooFit.Extended(True), ROOT.RooFit.Save(True), ROOT.RooFit.PrintLevel(-1),
                      ROOT.RooFit.Strategy(2))
    # chi2 / ndf of the post-fit prediction against data (data errors)
    chi2, ndf = 0., -(1 if mode == "zfixed" else 2)
    chi2_mc = 0.
    sp, sq = npr.getVal() / mp, nq.getVal() / mq
    for i in range(1, data_h.GetNbinsX() + 1):
        pred = sp * prompt_h.GetBinContent(i) + sq * qcd_h.GetBinContent(i)
        d = data_h.GetBinContent(i)
        if pred > 0 and d > 0:
            chi2 += (d - pred) ** 2 / d
            # with the template statistics (sum w^2 of the scaled MC) in the variance
            chi2_mc += (d - pred) ** 2 / (d + (sp * prompt_h.GetBinError(i)) ** 2 + (sq * qcd_h.GetBinError(i)) ** 2)
            ndf += 1
    if rpar is None:
        s_err, corr, at_bound = npr.getError() / mp, res.correlation(npr, nq), False
    else:
        s_err = rpar.getError() * s_z if mode == "zbound" else 0.
        corr = res.correlation(rpar, nq) if mode == "zbound" else 0.
        at_bound = mode == "zbound" and min(abs(rpar.getVal() - rpar.getMin()), abs(rpar.getVal() - rpar.getMax())) < 1e-3
    return {"status": res.status(), "covQual": res.covQual(), "corr": corr, "mode": mode, "at_bound": at_bound,
            "s_ratio": npr.getVal() / mp, "s_ratio_err": s_err,
            "k_qcd": nq.getVal() / mq, "k_qcd_err": nq.getError() / mq,
            "N_data": nd, "N_prompt_fit": npr.getVal(), "N_qcd_fit": nq.getVal(),
            "chi2": chi2, "chi2_mcstat": chi2_mc, "ndf": ndf}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--var", default="MT", choices=["MT", "MET"])
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--mode", default="free", choices=["free", "zfixed", "zbound"],
                    help="free: both yields free; zfixed: prompt scale = s_Z; zbound: s within s_Z (1 +- --bound)")
    ap.add_argument("--bound", type=float, default=0.3)
    a = ap.parse_args()
    tagm = "" if a.mode == "free" else f"_{a.mode}"
    pdir = REPO / "MeasFakeRate" / "plots" / plotter.STYLES[a.style]["dir"] / M.ERA / "PromptFit" / (a.mode if a.mode != "free" else "")
    pdir.mkdir(parents=True, exist_ok=True)
    for fl in ("mu", "el"):
        st = M.Store(fl)
        gate = json.loads((M.RES / fl / "gate.json").read_text())
        out, lines = {}, [f"# prompt scale from the {a.var} template fit, inclusive single-lepton region, {fl} (fitPromptScale.py)",
                          "# s_fit (prompt), k_QCD (QCD MC); Z check = data / (s_fit x MC) in the Z window; s_Z from the gate"]
        for p in M.FLAV[fl]["paths"]:
            out[p] = {}
            for idn in ("tight", "loose"):
                rel = f"{p}/Control/Inc/{idn}/{{cls}}/{a.var}"
                d = st.get("data", rel)
                pr = st.get("prompt", rel, ["prompt", "nonprompt"])
                q = st.get("qcd", rel, ["prompt", "nonprompt"])
                r = fit_one(d, pr, q, a.var, f"{fl}{p}{idn}{a.mode}", gate[p][idn]["s"], a.mode, a.bound)
                s = r["s_ratio"]
                zd, zde = M.zwin(st, "data", p, idn)
                zm, zme = M.zwin(st, "prompt", p, idn)
                zr = zd / (s * zm)
                zr_err = zr * math.hypot(zde / zd, zme / zm)
                r.update({"Z_data": zd, "Z_ratio": zr, "Z_ratio_err": zr_err, "s_Z": gate[p][idn]["s"],
                          "s_fit_over_s_Z": s / gate[p][idn]["s"]})
                out[p][idn] = r
                lines.append(f"## {p} {idn}: s_fit = {s:.4g} +- {r['s_ratio_err'] / s:.2%}, k_QCD = {r['k_qcd']:.3g} +- {r['k_qcd_err'] / r['k_qcd']:.1%}"
                             f"  (mode {a.mode}{' AT BOUND' if r['at_bound'] else ''}, fit status {r['status']}, covQual {r['covQual']}, corr {r['corr']:.2f}, chi2/ndf {r['chi2']:.0f}/{r['ndf']} (with MC stat {r['chi2_mcstat']:.0f}), N_data {r['N_data']:.0f})")
                lines.append(f"    Z check: data / (s_fit MC) = {zr:.3f} +- {zr_err:.3f} (N_data {zd:.0f});  s_fit / s_Z = {s / gate[p][idn]['s']:.3f}")
                # post-fit plot
                stack = []
                for lab, samples, col in [g for g in __import__("plotWRegion").GROUPS]:
                    h = __import__("plotWRegion").hsum([str(M.OUT / "MeasMuFR_MeasElFR" / M.ERA / f"{x}.root") for x in samples],
                                                       f"{st.top}/{rel}")
                    h.Scale(s)
                    stack.append((lab, h, col))
                qs = q.Clone(f"qs_{fl}{p}{idn}")
                qs.Scale(r["k_qcd"])
                stack.append(("QCD (MC)", qs, "#b9ac70"))
                cfg = {"xTitle": TITLES[a.var], "xRange": [0., 150.], "rebin": 2, "rRange": [0.5, 1.5],
                       "caption": [f"{p}, {idn} {LEP[fl]}", f"post-fit ({a.mode})", f"s = {s:.3g}, k_{{QCD}} = {r["k_qcd"]:.3g}"],
                       "bandLabel": "MC stat."}
                c = plotter.StackCanvas(d, stack, cfg, style=a.style).draw()
                c.save(str(pdir / f"{p}_{idn}_{a.var}.{plotter.STYLES[a.style]['format']}"))
        (M.RES / fl / f"promptfit_{a.var}{tagm}.json").write_text(json.dumps(out, indent=1))
        (M.RES / fl / f"promptfit_{a.var}{tagm}.txt").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))


if __name__ == "__main__":
    main()
