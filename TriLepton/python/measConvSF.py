"""Conversion scale factor per channel in the Z gamma control region (docs/PLAN_ConvSF.md step 3,
decisions C1-C6 of 2026-11-27). Not an analyzer: it reads the outputs of the C++ TriLepton analyzer.

  python TriLepton/python/measConvSF.py [--style an|pw] [--no-plots]

Input: SKNanoOutput/TriLepton/<tag>/2024/<sample>.root (tag Run1E2Mu_Run3Mu_V2; Run1E2Mu_Run3Mu = first production
without the Z-candidate, non-Z lepton and leading-jet histograms), histogram <CH>/ZG/<lane>/trilep_mass
(CH = 1E2MU, 3MU). Data: MuonEG (1E2MU), Muon0/1 (3MU), lanes Central (all leptons tight) and
Nonprompt, Nonprompt_Up, Nonprompt_Down (loose-not-tight, fake weight with the rates Central,
Total_Up, Total_Down).
SF = (N_data - N_nonconv) / N_conv, yields = integrals of m(3l) (with the flow bins), N_nonconv =
nonprompt (data) + prompt MC (WZ, ZZ, ttX, others), N_conv = DY 2J + TTG (nominal, C1 (a));
cross-check C1 (b): DYGto2LG + TTG + DY 2J with the DYG phase space removed (lane DYGVeto).
Uncertainty (C4): stat (B2G formula: data (+) MC and nonprompt statistics in the numerator, conversion
MC statistics) (+) nonprompt (SF with Nonprompt_Up / _Down) (+) theory (each category diboson, ttX,
others shifted up and down coherently, each sample by its cross-section uncertainty); per component
the larger of |up - central| and |down - central|; total in quadrature, symmetric.
Theory fractions (C4): WZ 1.6% (MATRIX NNLO scale (+) PDF), ZZ 4.2% (MATRIX nNNLO), ttZ 7.5%,
ttW 12%, ttH 10%, tZq 3.5% (B2G Run 3 KFactors.json), all others 50% (B2G fallback).
Not used: WZto3LNu_1J_amcatnloFXFX (WZ cross-check, PLAN 3.5), TTLL/TTLJ (nonprompt from data), signal.
Output: TriLepton/results/2024/convsf.{txt,json}, correctionlib TriLepton/results/2024/convsf_HcToWA.json
(ConvSF: channel, syst); control-region summary TriLepton/results/2024/cr_summary.{txt,json} (WZ and
Z+fake CR yields after the SF, WZ ratio per N_jets, expected SR background without data); plots TriLepton/plots/<style>/2024/ConvSF/ (ZG CR before and after the SF;
WZ and Z+fake CRs after the SF, for information). The SR data are blinded: never read here.
"""
import argparse
import ctypes
import glob
import json
import math
import sys
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
import plotter  # noqa: E402

ROOT.gROOT.SetBatch(True)
ERA = "2024"
TAG = "Run1E2Mu_Run3Mu_V2"  # production with ZCand_mass, nonZLep_pt/eta, jets_1_pt/eta (2026-11-27); --tag to change
IN = REPO / "SKNanoOutput" / "TriLepton" / TAG / ERA
RES = REPO / "TriLepton" / "results" / ERA
CHANNELS = ["1E2MU", "3MU"]
DATA = {"1E2MU": ["MuonEG"], "3MU": ["Muon0", "Muon1"]}
DY2J = [f"DYto2{f}_2J_MLL{m}" for f in ("E", "Mu", "Tau") for m in ("10to50", "50toInf")]
TTG = ["TTG_1J", "TTG_1J_PTG100toInf", "TTG_1J_PTG200toInf"]
DYG = ["DYGto2LG_1J_MLL4to50", "DYGto2LG_1J_MLL50toInf"] + [f"DYGto2LG_1J_MLL50_PTG{p}toInf" for p in (100, 200, 400, 600)]
# prompt MC: sample -> (theory category, fractional cross-section uncertainty)
PROMPT = {
    "WZto3LNu": ("diboson", 0.016), "ZZto4L": ("diboson", 0.042),
    "ttWtoLNu": ("ttX", 0.12), "ttZtoLL_MLL4to50": ("ttX", 0.075), "ttZtoLL_MLL50toInf": ("ttX", 0.075),
    "ttHtoNonbb_M125": ("ttX", 0.10), "tZq": ("ttX", 0.035), "tWZ_tlepWlep": ("ttX", 0.5),
    "tWZ_tlepWhad": ("ttX", 0.5), "tWZ_thadWlep": ("ttX", 0.5), "tHq": ("ttX", 0.5), "tHW": ("ttX", 0.5),
    "TTTT": ("ttX", 0.5),
    "WWW": ("others", 0.5), "WWZ": ("others", 0.5), "WZZ": ("others", 0.5), "ZZZ": ("others", 0.5),
    "WplusHtoNonbb_M125": ("others", 0.5), "WminusHtoNonbb_M125": ("others", 0.5),
    "ZHtoNonbb_M125": ("others", 0.5), "ggHtoZZto4L_M125": ("others", 0.5), "VBFHtoZZto4L_M125": ("others", 0.5),
}
CATS = ["diboson", "ttX", "others"]
YVAR = "trilep_mass"
PLOTVARS = ["trilep_mass", "pair_mass", "pair_lowM_mass", "pair_highM_mass", "muons_1_pt", "muons_2_pt",
            "muons_3_pt", "muons_1_eta", "muons_2_eta", "muons_3_eta", "electrons_1_pt", "electrons_1_scEta",
            "jets_size", "bjets_size", "METv_pt", "ZCand_mass", "nonZLep_pt", "nonZLep_eta", "jets_1_pt", "jets_1_eta"]
NEWVARS = {"ZCand_mass", "nonZLep_pt", "nonZLep_eta", "jets_1_pt", "jets_1_eta"}  # not in the first production
XT = {"trilep_mass": "m(3l) [GeV]", "pair_mass": "m(#mu^{+}#mu^{-}) [GeV]",
      "pair_lowM_mass": "m_{low}(#mu^{+}#mu^{-}) [GeV]", "pair_highM_mass": "m_{high}(#mu^{+}#mu^{-}) [GeV]",
      "muons_1_pt": "p_{T}(#mu_{1}) [GeV]", "muons_2_pt": "p_{T}(#mu_{2}) [GeV]", "muons_3_pt": "p_{T}(#mu_{3}) [GeV]",
      "muons_1_eta": "#eta(#mu_{1})", "muons_2_eta": "#eta(#mu_{2})", "muons_3_eta": "#eta(#mu_{3})",
      "electrons_1_pt": "p_{T}(e) [GeV]", "electrons_1_scEta": "#eta_{SC}(e)", "jets_size": "N_{jets}",
      "bjets_size": "N_{b jets}", "METv_pt": "p_{T}^{miss} [GeV]",
      "ZCand_mass": "m(Z candidate) [GeV]", "nonZLep_pt": "p_{T}(l not from Z) [GeV]",
      "nonZLep_eta": "#eta(l not from Z)", "jets_1_pt": "p_{T}(j_{1}) [GeV]", "jets_1_eta": "#eta(j_{1})"}
CHLAB = {"1E2MU": "e#mu#mu", "3MU": "#mu#mu#mu"}
REGLAB = {"ZG": "Z#gamma CR", "WZ": "WZ CR", "ZFake": "Z+fake CR"}
COL = {"conv": "#5790fc", "nonprompt": "#f89c20", "WZ": "#e42536", "ZZ": "#964a8b", "ttX": "#9c9ca1", "others": "#7a21dd"}


class Store:
    """Histogram sums over samples, cached."""

    def __init__(self):
        self.files = {}

    def _file(self, path):
        if path not in self.files:
            f = ROOT.TFile.Open(str(path))
            if not f or f.IsZombie():
                raise SystemExit(f"cannot open {path}")
            self.files[path] = f
        return self.files[path]

    def paths(self, sample):
        if sample in ("MuonEG", "Muon0", "Muon1"):
            ps = sorted(glob.glob(str(IN / f"Skim_TriLep_{sample}_*.root")))
            if not ps:
                raise SystemExit(f"no data files for {sample} in {IN}")
            return ps
        p = IN / f"Skim_TriLep_{sample}.root"
        if not p.exists():
            raise SystemExit(f"missing {p}")
        return [p]

    def hist(self, samples, path):
        out = None
        for s in samples:
            for p in self.paths(s):
                h = self._file(p).Get(path)
                if not h:
                    continue
                if out is None:
                    out = h.Clone(f"sum_{abs(hash((tuple(samples), path)))}")
                    out.SetDirectory(0)
                else:
                    out.Add(h)
        return out

    def yld(self, samples, path):
        h = self.hist(samples, path)
        if h is None:
            return 0., 0.
        err = ctypes.c_double(0.)
        v = h.IntegralAndError(0, h.GetNbinsX() + 1, err)
        return v, err.value


def components(st, ch, conv_set):
    """Yields (value, stat error) of each component in the ZG CR."""
    p = lambda lane: f"{ch}/ZG/{lane}/{YVAR}"
    c = {}
    c["data"] = st.yld(DATA[ch], p("Central"))
    for lane in ("Nonprompt", "Nonprompt_Up", "Nonprompt_Down"):
        c[lane] = st.yld(DATA[ch], p(lane))
    for s in PROMPT:
        c[s] = st.yld([s], p("Central"))
    if conv_set == "nominal":
        c["conv"] = st.yld(DY2J + TTG, p("Central"))
    else:
        a = st.yld(DYG + TTG, p("Central"))
        b = st.yld(DY2J, p("DYGVeto"))
        c["conv"] = (a[0] + b[0], math.hypot(a[1], b[1]))
    return c


def sf_of(c, nonprompt="Nonprompt", theory=None):
    """theory = (category, +1/-1) shifts the samples of the category by their fractions."""
    prompt, prompt_e2 = 0., 0.
    for s, (cat, frac) in PROMPT.items():
        v, e = c[s]
        k = 1. + (theory[1] * frac if theory and theory[0] == cat else 0.)
        prompt += k * v
        prompt_e2 += (k * e) ** 2
    np_v, np_e = c[nonprompt]
    d, de = c["data"]
    cv, ce = c["conv"]
    num = d - prompt - np_v
    num_e = math.sqrt(de ** 2 + prompt_e2 + np_e ** 2)
    sf = num / cv
    sf_e = abs(sf) * math.hypot(num_e / num, ce / cv) if num != 0 else 0.
    return sf, sf_e


def measure(st, ch, conv_set):
    c = components(st, ch, conv_set)
    sf, stat = sf_of(c)
    up, dn = sf_of(c, "Nonprompt_Up")[0], sf_of(c, "Nonprompt_Down")[0]
    npu = max(abs(up - sf), abs(dn - sf))
    th = {}
    for cat in CATS:
        u, d = sf_of(c, theory=(cat, +1))[0], sf_of(c, theory=(cat, -1))[0]
        th[cat] = {"up": u, "down": d, "unc": max(abs(u - sf), abs(d - sf))}
    thu = math.sqrt(sum(v["unc"] ** 2 for v in th.values()))
    tot = math.sqrt(stat ** 2 + npu ** 2 + thu ** 2)
    grp = {"WZ": c["WZto3LNu"][0], "ZZ": c["ZZto4L"][0],
           "ttX": sum(c[s][0] for s, (cat, _) in PROMPT.items() if cat == "ttX"),
           "others": sum(c[s][0] for s, (cat, _) in PROMPT.items() if cat == "others")}
    return {"sf": sf, "stat": stat, "nonprompt": npu, "nonprompt_up": up, "nonprompt_down": dn,
            "theory": thu, "theory_by_category": th, "total": tot,
            "yields": {"data": c["data"][0], "nonprompt": c["Nonprompt"][0], "conv": c["conv"][0],
                       "conv_stat": c["conv"][1], **grp}}


def write_correction(res):
    import correctionlib.schemav2 as cs
    content = []
    for ch in CHANNELS:
        r = res[ch]["nominal"]
        vals = {"Central": r["sf"], "Total_Up": r["sf"] + r["total"], "Total_Down": r["sf"] - r["total"],
                "Stat_Up": r["sf"] + r["stat"], "Stat_Down": r["sf"] - r["stat"],
                "Nonprompt_Up": r["sf"] + r["nonprompt"], "Nonprompt_Down": r["sf"] - r["nonprompt"],
                "Theory_Up": r["sf"] + r["theory"], "Theory_Down": r["sf"] - r["theory"]}
        content.append(cs.CategoryItem(key=ch, value=cs.Category(
            nodetype="category", input="syst",
            content=[cs.CategoryItem(key=k, value=float(v)) for k, v in vals.items()])))
    corr = cs.Correction(
        name="ConvSF", version=1,
        description="Conversion SF in the Z gamma CR, 2024 (ChargedHiggsAnalysisV4 TriLepton/python/measConvSF.py); "
                    "nominal conversion samples DY 2J + TTG; symmetric total = stat (+) nonprompt (+) theory",
        inputs=[cs.Variable(name="channel", type="string", description="1E2MU or 3MU"),
                cs.Variable(name="syst", type="string", description="Central, Total_Up/Down, Stat_Up/Down, Nonprompt_Up/Down, Theory_Up/Down")],
        output=cs.Variable(name="sf", type="real"),
        data=cs.Category(nodetype="category", input="channel", content=content))
    cset = cs.CorrectionSet(schema_version=2, corrections=[corr])
    (RES / "convsf_HcToWA.json").write_text(cset.model_dump_json(exclude_unset=True, indent=1))


def plot(st, ch, reg, var, sf, style, od, tag):
    p = lambda lane: f"{ch}/{reg}/{lane}/{var}"
    data = st.hist(DATA[ch], p("Central"))
    if data is None:
        return
    conv = st.hist(DY2J + TTG, p("Central"))
    groups = [("Nonprompt", st.hist(DATA[ch], p("Nonprompt")), COL["nonprompt"])]
    for g, sel in (("WZ", ["WZto3LNu"]), ("ZZ", ["ZZto4L"]),
                   ("ttX", [s for s, (c, _) in PROMPT.items() if c == "ttX"]),
                   ("Others", [s for s, (c, _) in PROMPT.items() if c == "others"])):
        h = st.hist(sel, p("Central"))
        if h is not None:
            groups.append((g, h, COL[g if g != "Others" else "others"]))
    if conv is not None:
        conv = conv.Clone(conv.GetName() + "_sf")
        conv.SetDirectory(0)
        conv.Scale(sf)
        groups.insert(0, ("Conversion" + (f" #times {sf:.2f}" if sf != 1. else ""), conv, COL["conv"]))
    groups = [g for g in groups if g[1] is not None]
    cfg = {"xTitle": XT.get(var, var), "overflow": True, "rRange": [0., 2.],
           "caption": [CHLAB[ch] + ", " + REGLAB[reg], "conversion SF applied" if sf != 1. else "before the conversion SF"]}
    if var == "ZCand_mass":
        cfg["xRange"] = [70., 110.] if reg != "ZG" else [0., 200.]
        cfg["rebin"] = 2 if reg != "ZG" else 5
    elif var == "jets_1_pt":
        cfg["rebin"] = 2
        cfg["xRange"] = [0., 300.]
    elif var == "trilep_mass":
        cfg["xRange"] = [50., 300.] if reg != "ZG" else [80., 104.]
        cfg["rebin"] = 2 if reg == "ZG" else 10
    elif var.endswith("eta") or var.endswith("scEta"):
        cfg["rebin"] = 2 if var.endswith("scEta") else 4
        cfg["eta"] = True
    elif var.startswith("jets") or var.startswith("bjets"):
        cfg["xRange"] = [0., 8.] if var.startswith("jets") else [0., 4.]
    elif var.endswith("_pt") and reg == "ZG":
        cfg["xRange"] = [0., 100.]  # soft conversion leptons: 5 GeV bins
    elif var.endswith("_pt"):
        cfg["rebin"] = 2
        cfg["xRange"] = [0., 200.]
    else:
        cfg["rebin"] = 4
        cfg["xRange"] = [0., 200.]
    c = plotter.StackCanvas(data, groups, cfg, style=style).draw()
    c.save(str(od / f"{ch}_{reg}_{tag}_{var}.{plotter.STYLES[style]['format']}"))


def cr_summary(st, res):
    """Yields in the WZ and Z+fake CRs after the ConvSF, and the WZ ratio per N_jets (WZ CR)."""
    ttx = [s for s, (c, _) in PROMPT.items() if c == "ttX"]
    oth = [s for s, (c, _) in PROMPT.items() if c == "others"]
    out, lines = {}, ["Control regions after the ConvSF (POWHEG WZ, no WZ N_jet SF), 2024", ""]
    for reg in ("WZ", "ZFake"):
        for ch in CHANNELS:
            sf = res[ch]["nominal"]["sf"]
            p = lambda lane, v=YVAR: f"{ch}/{reg}/{lane}/{v}"
            y = {"data": st.yld(DATA[ch], p("Central"))[0], "nonprompt": st.yld(DATA[ch], p("Nonprompt"))[0],
                 "nonprompt_up": st.yld(DATA[ch], p("Nonprompt_Up"))[0], "nonprompt_down": st.yld(DATA[ch], p("Nonprompt_Down"))[0],
                 "conv": sf * st.yld(DY2J + TTG, p("Central"))[0], "WZ": st.yld(["WZto3LNu"], p("Central"))[0],
                 "WZ_FxFx": st.yld(["WZto3LNu_1J_amcatnloFXFX"], p("Central"))[0], "ZZ": st.yld(["ZZto4L"], p("Central"))[0],
                 "ttX": st.yld(ttx, p("Central"))[0], "others": st.yld(oth, p("Central"))[0]}
            pred = sum(y[k] for k in ("nonprompt", "conv", "WZ", "ZZ", "ttX", "others"))
            y["pred"], y["ratio"] = pred, y["data"] / pred
            y["ratio_FxFx"] = y["data"] / (pred - y["WZ"] + y["WZ_FxFx"])
            lines.append(f"{reg} {ch}: data {y['data']:.0f}, pred {pred:.1f}, data/pred {y['ratio']:.3f} (FxFx WZ {y['ratio_FxFx']:.3f}); "
                         + ", ".join(f"{k} {y[k]:.1f}" for k in ("nonprompt", "conv", "WZ", "ZZ", "ttX", "others"))
                         + f"; nonprompt Total_Up/Down {y['nonprompt_up']:.1f}/{y['nonprompt_down']:.1f}")
            if reg == "WZ":
                H = lambda smp, lane: st.hist(smp, p(lane, "jets_size"))
                hs = {"d": H(DATA[ch], "Central"), "np": H(DATA[ch], "Nonprompt"), "cv": H(DY2J + TTG, "Central"),
                      "wz": H(["WZto3LNu"], "Central"), "zz": H(["ZZto4L"], "Central"), "tx": H(ttx, "Central"), "ot": H(oth, "Central")}
                y["njets"] = {}
                for lab, (lo, hi) in (("0", (1, 1)), ("1", (2, 2)), ("2", (3, 3)), (">=3", (4, 16)), (">=2", (3, 16))):
                    I = lambda k: hs[k].Integral(lo, hi)
                    err = ctypes.c_double(0.)
                    hs["d"].IntegralAndError(lo, hi, err)
                    rest = I("np") + sf * I("cv") + I("zz") + I("tx") + I("ot")
                    r = (I("d") - rest) / I("wz")
                    y["njets"][lab] = {"data": I("d"), "WZ": I("wz"), "rest": rest, "ratio": r, "stat": err.value / I("wz"),
                                       "nonprompt25": 0.25 * I("np") / I("wz")}
                lines.append("    (data - non-WZ) / WZ by N_jets: " + "; ".join(
                    f"{k}: {v['ratio']:.3f} +- {v['stat']:.3f} (stat) +- {v['nonprompt25']:.3f} (nonprompt 25%)" for k, v in y["njets"].items()))
            out[f"{reg}_{ch}"] = y
    for ch in CHANNELS:  # expected SR background (no SR data: blinded)
        sf = res[ch]["nominal"]["sf"]
        p = lambda lane: f"{ch}/SR/{lane}/{YVAR}"
        y = {"nonprompt": st.yld(DATA[ch], p("Nonprompt"))[0], "conv": sf * st.yld(DY2J + TTG, p("Central"))[0],
             "WZ": st.yld(["WZto3LNu"], p("Central"))[0], "ZZ": st.yld(["ZZto4L"], p("Central"))[0],
             "ttX": st.yld(ttx, p("Central"))[0], "others": st.yld(oth, p("Central"))[0]}
        tot = sum(y.values())
        lines.append(f"SR {ch} expected background (no data, blinded): total {tot:.1f}; "
                     + ", ".join(f"{k} {v:.1f} ({100 * v / tot:.0f}%)" for k, v in y.items()))
        out[f"SR_{ch}"] = y
    txt = "\n".join(lines)
    print(txt)
    (RES / "cr_summary.txt").write_text(txt + "\n")
    (RES / "cr_summary.json").write_text(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--tag", default=TAG, help="production directory under SKNanoOutput/TriLepton")
    a = ap.parse_args()
    global IN
    IN = REPO / "SKNanoOutput" / "TriLepton" / a.tag / ERA
    RES.mkdir(parents=True, exist_ok=True)
    st = Store()
    res = {ch: {cs_: measure(st, ch, cs_) for cs_ in ("nominal", "DYG")} for ch in CHANNELS}
    lines = ["Conversion SF, Z gamma CR, 2024 (TriLepton/python/measConvSF.py)", ""]
    for ch in CHANNELS:
        for cs_ in ("nominal", "DYG"):
            r = res[ch][cs_]
            y = r["yields"]
            lines.append(f"{ch} [{cs_}]: SF = {r['sf']:.3f} +- {r['total']:.3f} ({100 * r['total'] / r['sf']:.1f}%): "
                         f"stat {r['stat']:.3f}, nonprompt {r['nonprompt']:.3f}, theory {r['theory']:.3f} "
                         f"(" + ", ".join(f"{k} {v['unc']:.3f}" for k, v in r["theory_by_category"].items()) + ")")
            lines.append(f"    yields: data {y['data']:.1f}, nonprompt {y['nonprompt']:.2f}, conv {y['conv']:.2f} +- {y['conv_stat']:.2f}, "
                         f"WZ {y['WZ']:.2f}, ZZ {y['ZZ']:.2f}, ttX {y['ttX']:.2f}, others {y['others']:.2f}")
    txt = "\n".join(lines)
    print(txt)
    (RES / "convsf.txt").write_text(txt + "\n")
    (RES / "convsf.json").write_text(json.dumps(res, indent=1))
    write_correction(res)
    cr_summary(st, res)
    if a.no_plots:
        return
    od = REPO / "TriLepton" / "plots" / plotter.STYLES[a.style]["dir"] / ERA / "ConvSF"
    od.mkdir(parents=True, exist_ok=True)
    for ch in CHANNELS:
        vars_ = [v for v in PLOTVARS if not (ch == "1E2MU" and (v.startswith("pair_") and v != "pair_mass" or v.startswith("muons_3")))
                 and not (ch == "3MU" and (v == "pair_mass" or v.startswith("electrons")))]
        sf = res[ch]["nominal"]["sf"]
        if a.tag == "Run1E2Mu_Run3Mu":
            vars_ = [v for v in vars_ if v not in NEWVARS]
        for var in vars_:
            plot(st, ch, "ZG", var, 1., a.style, od, "preSF")
            plot(st, ch, "ZG", var, sf, a.style, od, "postSF")
            for reg in ("WZ", "ZFake"):
                plot(st, ch, reg, var, sf, a.style, od, "postSF")


if __name__ == "__main__":
    main()
