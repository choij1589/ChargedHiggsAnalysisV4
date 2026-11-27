"""Evaluation of the MC closure (not an analyzer: it reads the outputs of the C++ ClosFakeRate analyzer) of the nonprompt method in tt (PLAN_BkgEst step 4, criterion F3 fixed by the user 2026-11-27).

  python MeasFakeRate/python/evalClosure.py [--style an|pw]

Input: SKNanoOutput/ClosFakeRate/Run1E2Mu_Run3Mu/2024/Skim_TriLep_{TTLL,TTLJ}_powheg.root (ClosFakeRate
analyzer, HcToWA_Analyzers): <CH>/SR/Observed/<var> (all leptons tight) and <CH>/SB/<rates>/<var>
(loose-not-tight leptons with the fake weight of the rate set), CH = 1E2MU, 3MU (pass/fail) and
3MU_onZ, 3MU_offZ (diagnostics).
Prediction for the test: the rates measured in QCD MC (MC_QCD). Rate uncertainty: the data-rate variations,
relative to the data-rate prediction (Central), applied to the MC_QCD prediction, per group:
Stat (Stat_Up/Down), PromptNorm, AwayJet (Up/Down), BTag (one-sided).
F3, both required in each channel (1E2MU, 3MU):
  (A) yield: r = N_obs / N_pred; pass if |r - 1| < sigma_r, sigma_r = r x [MC stat of both (+) rate groups,
      each the larger relative shift of up/down];
  (B) shape: chi2 of observed vs predicted in the fit variable (1E2MU m(mumu); 3MU both pair masses
      (lower and higher), each tested), bins of 4 GeV from 12 GeV merged left to right until the effective
      number of MC events of both observed and predicted is >= 10; covariance = MC statistics per bin +
      each rate group fully correlated over bins (signed half-difference of up and down; BTag one-sided);
      pass if p(chi2, ndf = number of bins) > 0.05.
Diagnostics: on-Z / off-Z, the prediction with the data rates and with the tt-MC rates, the share of the
prediction from events whose loose-not-tight lepton is prompt (eps_p = 1, F4), SR events with all leptons prompt.
Output: MeasFakeRate/results/2024/closure.{txt,json}; plots MeasFakeRate/plots/AN/2024/Closure/.
"""
import argparse
import array
import json
import math
import sys
from pathlib import Path

import numpy as np
import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
import plotter  # noqa: E402

ERA = "2024"
IN = REPO / "SKNanoOutput" / "ClosFakeRate" / "Run1E2Mu_Run3Mu" / ERA
SAMPLES = ["Skim_TriLep_TTLL_powheg", "Skim_TriLep_TTLJ_powheg"]
RES = REPO / "MeasFakeRate" / "results" / ERA
GROUPS = {"Stat": ("Stat_Up", "Stat_Down"), "PromptNorm": ("PromptNorm_Up", "PromptNorm_Down"),
          "AwayJet": ("AwayJet_Up", "AwayJet_Down"), "BTag": ("BTag", None)}
TESTS = {"1E2MU": ["pair_mass"], "3MU": ["pair_lowM_mass", "pair_highM_mass"]}
DIAG = {"3MU_onZ": ["pair_lowM_mass", "pair_highM_mass"], "3MU_offZ": ["pair_lowM_mass", "pair_highM_mass"]}
XT = {"pair_mass": "m(#mu^{+}#mu^{-}) [GeV]", "pair_lowM_mass": "m_{low}(#mu^{+}#mu^{-}) [GeV]",
      "pair_highM_mass": "m_{high}(#mu^{+}#mu^{-}) [GeV]", "muons_1_pt": "p_{T}^{corr}(#mu_{1}) [GeV]",
      "muons_2_pt": "p_{T}^{corr}(#mu_{2}) [GeV]", "muons_3_pt": "p_{T}^{corr}(#mu_{3}) [GeV]",
      "electrons_1_pt": "p_{T}^{corr}(e) [GeV]", "jets_size": "N_{jets}", "bjets_size": "N_{b jets}",
      "METv_pt": "p_{T}^{miss} [GeV]"}
CHLAB = {"1E2MU": "e#mu#mu", "3MU": "#mu#mu#mu", "3MU_onZ": "#mu#mu#mu, on-Z", "3MU_offZ": "#mu#mu#mu, off-Z"}


class Reader:
    def __init__(self):
        self.files = [ROOT.TFile.Open(str(IN / f"{s}.root")) for s in SAMPLES]
        for s, f in zip(SAMPLES, self.files):
            if not f or f.IsZombie():
                raise SystemExit(f"missing {IN / s}.root")

    def get(self, path):
        tot = None
        for f in self.files:
            h = f.Get(path)
            if not h:
                raise SystemExit(f"no {path}")
            if tot is None:
                tot = h.Clone(f"r{abs(hash(path))}")
                tot.SetDirectory(0)
            else:
                tot.Add(h)
        return tot


def arrays(h, edges, overflow=True):
    """(sum w, sum w^2) per bin of `edges` from a histogram with 1 GeV (or finer) bins; the last bin includes
    the overflow if `overflow`."""
    v, e2 = [], []
    for k in range(len(edges) - 1):
        b1 = h.FindBin(edges[k] + 1e-6)
        b2 = h.FindBin(edges[k + 1] - 1e-6) if (k < len(edges) - 2 or not overflow) else h.GetNbinsX() + 1
        import ctypes
        err = ctypes.c_double(0.)
        v.append(h.IntegralAndError(b1, b2, err))
        e2.append(err.value ** 2)
    return np.array(v), np.array(e2)


def neff(v, e2):
    return np.where(e2 > 0, v * v / np.where(e2 > 0, e2, 1.), 0.)


def merged_edges(obs, pred, var):
    hi = 300. if var == "pair_highM_mass" else 200.
    edges = list(np.arange(12., hi + 1e-6, 4.))
    out = [edges[0]]
    so = sw2o = sp = sw2p = 0.
    for k in range(len(edges) - 1):
        last = k == len(edges) - 2
        o, o2 = arrays(obs, [edges[k], edges[k + 1]], overflow=last)
        p, p2 = arrays(pred, [edges[k], edges[k + 1]], overflow=last)
        so += o[0]; sw2o += o2[0]; sp += p[0]; sw2p += p2[0]
        if sw2o > 0 and sw2p > 0 and so * so / sw2o >= 10 and sp * sp / sw2p >= 10:
            out.append(edges[k + 1])
            so = sw2o = sp = sw2p = 0.
    if out[-1] != edges[-1]:
        if len(out) > 1:
            out[-1] = edges[-1]
        else:
            out.append(edges[-1])
    return out


def evaluate(rd, ch, var):
    obs_h = rd.get(f"{ch}/SR/Observed/{var}")
    pred_h = rd.get(f"{ch}/SB/MC_QCD/{var}")
    edges = merged_edges(obs_h, pred_h, var)
    o, o2 = arrays(obs_h, edges)
    p, p2 = arrays(pred_h, edges)
    c, _ = arrays(rd.get(f"{ch}/SB/Central/{var}"), edges)
    C = np.diag(o2 + p2)
    pvar = p2.copy()  # prediction-only variance (MC stat + rate groups), for the band
    rel_tot = {}
    for g, (up, dn) in GROUPS.items():
        u, _ = arrays(rd.get(f"{ch}/SB/{up}/{var}"), edges)
        if dn:
            d, _ = arrays(rd.get(f"{ch}/SB/{dn}/{var}"), edges)
            s = np.where(c != 0, (u - d) / (2 * np.where(c != 0, c, 1.)), 0.)
            U, D, Cs = u.sum(), d.sum(), c.sum()
            rel_tot[g] = max(abs(U / Cs - 1), abs(D / Cs - 1))
        else:
            s = np.where(c != 0, u / np.where(c != 0, c, 1.) - 1, 0.)
            rel_tot[g] = abs(u.sum() / c.sum() - 1)
        vg = p * s
        C += np.outer(vg, vg)
        pvar += vg * vg
    dvec = o - p
    chi2 = float(dvec @ np.linalg.solve(C, dvec))
    ndf = len(o)
    prob = ROOT.TMath.Prob(chi2, ndf)
    No, Np = o.sum(), p.sum()
    r = No / Np
    rel_rate = math.sqrt(sum(v * v for v in rel_tot.values()))
    sig_r = r * math.sqrt(o2.sum() / No ** 2 + p2.sum() / Np ** 2 + rel_rate ** 2)
    return {"edges": edges, "obs": o.tolist(), "pred": p.tolist(), "N_obs": No, "N_obs_err": math.sqrt(o2.sum()),
            "N_pred": Np, "N_pred_err": math.sqrt(p2.sum()), "rate_rel": rel_tot, "rate_rel_total": rel_rate,
            "ratio": r, "ratio_err": sig_r, "passA": abs(r - 1) < sig_r, "chi2": chi2, "ndf": ndf, "p": prob,
            "passB": prob > 0.05, "C": C, "pred_err": np.sqrt(pvar).tolist(), "pred_central": c.tolist()}


def plot(rd, ch, var, res, style, od):
    edges = res["edges"] if res else None
    obs = rd.get(f"{ch}/SR/Observed/{var}")
    pp = rd.get(f"{ch}/SB_genPromptLNT/MC_QCD/{var}")
    pn = rd.get(f"{ch}/SB_genNonpromptLNT/MC_QCD/{var}")
    cfg = {"xTitle": XT.get(var, var), "dataLabel": "Observed (t#bar{t} MC)", "hasData": False,
           "rTitle": "Obs. / Pred.", "rRange": [0., 2.], "overflow": True,
           "caption": [CHLAB[ch], "rates: QCD MC"]}
    if edges:
        cfg["rebin"] = edges
        cfg["xRange"] = [edges[0], edges[-1]]
    elif var.startswith("jets") or var.startswith("bjets"):
        cfg["xRange"] = [0., 10.] if var.startswith("jets") else [0., 5.]
    else:
        cfg["rebin"] = 2
        cfg["xRange"] = [0., 200.]
    stack = [("Pred., prompt LNT", pp, "#94a4a2"), ("Pred., nonprompt LNT", pn, "#ffa90e")]
    band = None
    if res:
        # band = prediction uncertainty (MC stat of the prediction (+) rate groups, per bin)
        band = plotter.prepare(rd.get(f"{ch}/SB/MC_QCD/{var}"), cfg)
        for i in range(1, band.GetNbinsX() + 1):
            band.SetBinError(i, res["pred_err"][i - 1])
        cfg["bandLabel"] = "Pred. stat. #oplus rate unc."
    c = plotter.StackCanvas(obs, stack, cfg, style=style, band=band).draw()
    c.save(str(od / f"{ch}_{var}.{plotter.STYLES[style]['format']}"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    a = ap.parse_args()
    rd = Reader()
    od = REPO / "MeasFakeRate" / "plots" / plotter.STYLES[a.style]["dir"] / ERA / "Closure"
    od.mkdir(parents=True, exist_ok=True)
    out, lines = {}, ["# MC closure in tt (TTLL + TTLJ powheg skims), rates measured in QCD MC (F3, evalClosure.py)",
                      "# (A) |N_obs/N_pred - 1| < sigma (MC stat (+) rate groups); (B) chi2 p > 0.05 (bins n_eff >= 10)"]
    for ch, vars_ in list(TESTS.items()) + list(DIAG.items()):
        diag = ch in DIAG
        out[ch] = {}
        for var in vars_:
            r = evaluate(rd, ch, var)
            # diagnostics
            def tot(path):
                return rd.get(path).Integral(0, 100000)
            r["pred_data_rates"] = tot(f"{ch}/SB/Central/{var}")
            r["pred_tt_rates"] = tot(f"{ch}/SB/MC_TT/{var}")
            r["prompt_LNT_share"] = tot(f"{ch}/SB_genPromptLNT/MC_QCD/{var}") / r["N_pred"]
            r["obs_all_prompt_share"] = tot(f"{ch}/SR_genAllPrompt/Observed/{var}") / r["N_obs"]
            out[ch][var] = {k: v for k, v in r.items() if k != "C"}
            tag = " (diagnostic)" if diag else ""
            lines.append(f"## {ch} {var}{tag}")
            lines.append(f"  (A) N_obs {r['N_obs']:.2f} +- {r['N_obs_err']:.2f}, N_pred {r['N_pred']:.2f} +- {r['N_pred_err']:.2f}; "
                         f"ratio {r['ratio']:.3f} +- {r['ratio_err']:.3f} -> {'PASS' if r['passA'] else 'FAIL'}"
                         f"  (rate unc. {r['rate_rel_total']:.1%}: " + ", ".join(f"{g} {v:.1%}" for g, v in r["rate_rel"].items()) + ")")
            lines.append(f"  (B) chi2 {r['chi2']:.1f} / {r['ndf']}, p = {r['p']:.3f} -> {'PASS' if r['passB'] else 'FAIL'}; bins {[round(x) for x in r['edges']]}")
            lines.append(f"  diag: obs / pred(data rates) {r['N_obs'] / r['pred_data_rates']:.3f}, obs / pred(tt-MC rates) {r['N_obs'] / r['pred_tt_rates']:.3f}; "
                         f"prompt-LNT share of the prediction {r['prompt_LNT_share']:.3f}; all-prompt share of the observed {r['obs_all_prompt_share']:.3f}")
            plot(rd, ch, var, r, a.style, od)
        if not diag:
            ok = all(out[ch][v]["passA"] and out[ch][v]["passB"] for v in vars_)
            lines.append(f"# {ch}: {'PASS' if ok else 'FAIL'} (A and B in every tested distribution)")
    for ch in ("1E2MU", "3MU"):
        for var in ("muons_1_pt", "muons_2_pt", "METv_pt", "jets_size", "bjets_size") + (("electrons_1_pt",) if ch == "1E2MU" else ("muons_3_pt",)):
            plot(rd, ch, var, None, a.style, od)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "closure.json").write_text(json.dumps(out, indent=1, default=float))
    (RES / "closure.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
