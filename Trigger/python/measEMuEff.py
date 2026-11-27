"""e-mu trigger legs and pairwise filters from the MeasTrigEff outputs (PLAN_Trigger step 2).

  python Trigger/python/measEMuEff.py [--style an|pw] [--no-plots]

Inputs: SKNanoOutput/MeasTrigEff/<flags>/2024/ (synced from /pnfs):
  electron legs  data Muon0/1 (MeasElLegs_MeasDblMuPair; IsoMu24 tag, T7)
  muon legs      data EGamma0/1 (MeasMuLegs; Ele30 tag, T7)
  e-mu DZ        data MuonEG (MeasEMuPair)
  dimuon DZ, DZ_Mass3p8  data Muon0/1 (MeasElLegs_MeasDblMuPair)
  MC             MeasElLegs_MeasMuLegs_MeasDblMuPair_MeasEMuPair: TTLL powheg (nominal),
                 DY 2J (ee + mumu + tautau, both mass bins; alternative MC, T2)
Legs: opposite-sign e-mu events, reference trigger required (MC too), corrected pT (T4);
electron legs bit 6 AND bit 0 with the denominator conditioned on the tag muon passing the
same path's muon leg (T5). Histograms are filled in |eta| (electrons |eta_SC|) x pT and
rebinned here to BINS (proposal, open in PLAN_Trigger step 2).
Uncertainties (T2): data Clopper-Pearson (68.3%), MC weighted binomial
  var = [(1 - 2 e) sum w2(pass) + e^2 sum w2(all)] / (sum w(all))^2,
alternative MC = |e(DY) - e(TTLL)| per bin. Checks (assigned only if significant):
  ss   data efficiency after subtracting same-sign events (non-prompt contamination)
  ref  MC efficiency without the reference trigger vs with it (reference-trigger bias)
  bit6 electron legs with bit 6 alone (B2G-25-013 definition), uncond: unconditioned den.
Pairwise filters (T6): inclusive path-decision ratios, data and MC (stat (+) alt MC),
and binned in the larger |eta| and in the leading pT as a flatness check (chi2 / ndf of the
binned data values against the inclusive one).
Outputs: Trigger/results/2024/emu_legs.root (per leg: data, sim, simalt, sf as TH2 with
stat errors; plus syst histograms), Trigger/results/2024/summary.txt (per-bin table,
checks, pairwise filters); plots in Trigger/plots/<STYLE>/2024/{legs,pair}/.
"""
import argparse
import glob
import math
import sys
from array import array
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
import plotter  # noqa: E402

ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

BASE = REPO / "SKNanoOutput" / "MeasTrigEff"
DATA = {
    "ElLeg": ("MeasElLegs_MeasDblMuPair", "Muon[01]_*.root"),
    "MuLeg": ("MeasMuLegs", "EGamma[01]_*.root"),
    "EMuPair": ("MeasEMuPair", "MuonEG_*.root"),
    "DblMuPair": ("MeasElLegs_MeasDblMuPair", "Muon[01]_*.root"),
}
MCDIR = "MeasElLegs_MeasMuLegs_MeasDblMuPair_MeasEMuPair"
MC_NOM = ["TTLL_powheg"]
MC_ALT = [f"DYto2{f}_2J_MLL{m}" for f in ("E", "Mu", "Tau") for m in ("10to50", "50toInf")]

# Proposed binning (|eta| or |eta_SC|, corrected pT); edges must be edges of the analyzer's
# histograms (eta: 0, 0.8, 0.9, 1.2, 1.4442, 1.479, 1.566, 1.6, 2.0, 2.1, 2.4, 2.5;
# pT: 1 GeV steps 10-60, then 65, 70, 80, 90, 100, 120, 150, 200, 300, 500).
ETA_E = [0., 0.8, 1.4442, 1.566, 2.0, 2.5]
ETA_M = [0., 0.9, 1.2, 2.1, 2.4]
BINS = {
    "Ele12": (ETA_E, [15., 17., 20., 25., 30., 40., 50., 100., 500.]),
    "Ele23": (ETA_E, [15., 20., 22., 24., 26., 28., 30., 35., 40., 50., 100., 500.]),
    "Mu8": (ETA_M, [10., 12., 15., 20., 30., 50., 100., 500.]),
    "Mu23": (ETA_M, [10., 15., 20., 22., 24., 26., 28., 30., 35., 40., 50., 100., 500.]),
}
LEGS = {  # leg: (directory, numerator, denominator, lepton)
    "Ele12": ("ElLeg", "num_Ele12", "den_Ele12", "electron"),
    "Ele23": ("ElLeg", "num_Ele23", "den_Ele23", "electron"),
    "Mu8": ("MuLeg", "num_Mu8", "den", "muon"),
    "Mu23": ("MuLeg", "num_Mu23", "den", "muon"),
}
PAIRS = {  # name: (directory, numerator, data group)
    "DblMu_DZ": ("DblMuPair", "num_DZ", "DblMuPair"),
    "DblMu_DZ_Mass3p8": ("DblMuPair", "num_DZM", "DblMuPair"),
    "EMu_Mu23Ele12_DZ": ("EMuPair/Mu23Ele12", "num_DZ", "EMuPair"),
    "EMu_Mu8Ele23_DZ": ("EMuPair/Mu8Ele23", "num_DZ", "EMuPair"),
}
C_DATA, C_MC, C_ALT, C_SF = "#000000", "#3f90da", "#e42536", "#000000"


class Sum:
    """Sum of the same histogram over files (weights as stored: MCweight x lumi x PU)."""

    def __init__(self, files):
        self.files = [ROOT.TFile.Open(str(f)) for f in files]
        if not self.files:
            raise SystemExit("no input files")

    def get(self, path):
        out = None
        for f in self.files:
            h = f.Get(path)
            if not h:
                raise SystemExit(f"{f.GetName()}: {path} missing")
            if out is None:
                out = h.Clone(path.replace("/", "_") + "_sum")
                out.Sumw2()
            else:
                out.Add(h)
        return out


def data_files(group):
    d, pat = DATA[group]
    return sorted(glob.glob(str(BASE / d / "2024" / pat)))


def mc_files(samples):
    return [BASE / MCDIR / "2024" / f"{s}.root" for s in samples]


def rebin2(h, xe, ye):
    """Rebin a TH2 to the given edges (must coincide with existing edges); sums w and w2."""
    out = ROOT.TH2D(h.GetName() + "_rb", "", len(xe) - 1, array("d", xe), len(ye) - 1, array("d", ye))
    out.Sumw2()
    ax, ay = h.GetXaxis(), h.GetYaxis()
    for i in range(1, ax.GetNbins() + 1):
        xc = ax.GetBinCenter(i)
        if xc >= xe[-1]:
            continue
        for j in range(1, ay.GetNbins() + 2):  # include pT overflow in the last bin
            yc = ay.GetBinCenter(j) if j <= ay.GetNbins() else ye[-1] - 1e-3
            if yc < ye[0]:
                continue
            yc = min(yc, ye[-1] - 1e-3)
            b = out.FindBin(xc, yc)
            out.SetBinContent(b, out.GetBinContent(b) + h.GetBinContent(i, j))
            out.SetBinError(b, math.hypot(out.GetBinError(b), h.GetBinError(i, j)))
    for e in xe:
        if min(abs(e - ax.GetBinLowEdge(k)) for k in range(1, ax.GetNbins() + 2)) > 1e-4:
            raise SystemExit(f"eta edge {e} is not an edge of {h.GetName()}")
    for e in ye:
        if min(abs(e - ay.GetBinLowEdge(k)) for k in range(1, ay.GetNbins() + 2)) > 1e-4:
            raise SystemExit(f"pT edge {e} is not an edge of {h.GetName()}")
    return out


def eff_data(n, d):
    """Clopper-Pearson 68.3% (central value n/d); returns (eff, err_low, err_high)."""
    if d <= 0:
        return 0., 0., 0.
    n, d = int(round(n)), int(round(d))
    e = n / d
    lo = ROOT.TEfficiency.ClopperPearson(d, n, 0.682689, False)
    hi = ROOT.TEfficiency.ClopperPearson(d, n, 0.682689, True)
    return e, e - lo, hi - e


def eff_mc(wp, w2p, wa, w2a):
    """Weighted binomial (pass is a subset of all)."""
    if wa <= 0:
        return 0., 0.
    e = wp / wa
    var = ((1. - 2. * e) * w2p + e * e * w2a) / (wa * wa)
    return e, math.sqrt(max(var, 0.))


def leg_tables(leg, dsum, mcsum, altsum):
    d, num, den, lep = LEGS[leg]
    xe, ye = BINS[leg]
    get = lambda s, sign, ref, name: rebin2(s.get(f"{d}/{sign}/{ref}/cor/{name}"), xe, ye)
    H = {
        "dn": get(dsum, "os", "ref", num), "dd": get(dsum, "os", "ref", den),
        "dns": get(dsum, "ss", "ref", num), "dds": get(dsum, "ss", "ref", den),
        "mn": get(mcsum, "os", "ref", num), "md": get(mcsum, "os", "ref", den),
        "mnr": get(mcsum, "os", "noref", num), "mdr": get(mcsum, "os", "noref", den),
        "an": get(altsum, "os", "ref", num), "ad": get(altsum, "os", "ref", den),
    }
    if lep == "electron":
        H["dn6"] = get(dsum, "os", "ref", num + "_bit6")
        H["dnu"], H["ddu"] = get(dsum, "os", "ref", num + "_uncond"), get(dsum, "os", "ref", "den_uncond")
        H["mn6"] = get(mcsum, "os", "ref", num + "_bit6")
    rows = []
    for i in range(1, len(xe)):
        for j in range(1, len(ye)):
            v = lambda k: H[k].GetBinContent(i, j)
            w2 = lambda k: H[k].GetBinError(i, j) ** 2
            if v("dd") <= 0 and v("md") <= 0:
                continue  # e.g. ECAL gap
            ed, edl, edh = eff_data(v("dn"), v("dd"))
            em, emerr = eff_mc(v("mn"), w2("mn"), v("md"), w2("md"))
            ea, eaerr = eff_mc(v("an"), w2("an"), v("ad"), w2("ad"))
            emr, _ = eff_mc(v("mnr"), w2("mnr"), v("mdr"), w2("mdr"))
            dss = v("dd") - v("dds")
            ess = (v("dn") - v("dns")) / dss if dss > 0 else 0.
            r = dict(i=i, j=j, eta=(xe[i - 1], xe[i]), pt=(ye[j - 1], ye[j]),
                     nden=v("dd"), npass=v("dn"), ed=ed, edl=edl, edh=edh,
                     em=em, emerr=emerr, ea=ea, eaerr=eaerr, alt=abs(ea - em) if v("ad") > 0 else 0.,
                     ss=ess - ed, ref=emr - em, mdeff=(v("md") ** 2 / w2("md")) if w2("md") > 0 else 0.)
            if lep == "electron":
                r["bit6"] = (v("dn6") / v("dd") if v("dd") > 0 else 0.) - ed
                r["uncond"] = (v("dnu") / v("ddu") if v("ddu") > 0 else 0.) - ed
            r["sf"] = ed / em if em > 0 else 0.
            serr = 0.5 * (edl + edh)
            r["sfstat"] = r["sf"] * math.hypot(serr / ed if ed > 0 else 0., emerr / em if em > 0 else 0.)
            r["sfalt"] = r["sf"] * (r["alt"] / em) if em > 0 else 0.
            r["sftot"] = math.hypot(r["sfstat"], r["sfalt"])
            rows.append(r)
    return rows, H


def leg_hists(leg, rows):
    xe, ye = BINS[leg]
    mk = lambda n: ROOT.TH2D(f"{leg}_{n}", "", len(xe) - 1, array("d", xe), len(ye) - 1, array("d", ye))
    out = {k: mk(k) for k in ("data", "sim", "simalt", "sf", "data_errlow", "data_errhigh", "sim_alt", "sf_stat", "sf_alt", "sf_tot")}
    for r in rows:
        i, j = r["i"], r["j"]
        out["data"].SetBinContent(i, j, r["ed"]); out["data"].SetBinError(i, j, 0.5 * (r["edl"] + r["edh"]))
        out["data_errlow"].SetBinContent(i, j, r["edl"]); out["data_errhigh"].SetBinContent(i, j, r["edh"])
        out["sim"].SetBinContent(i, j, r["em"]); out["sim"].SetBinError(i, j, r["emerr"])
        out["simalt"].SetBinContent(i, j, r["ea"]); out["simalt"].SetBinError(i, j, r["eaerr"])
        out["sim_alt"].SetBinContent(i, j, r["alt"])
        out["sf"].SetBinContent(i, j, r["sf"]); out["sf"].SetBinError(i, j, r["sftot"])
        out["sf_stat"].SetBinContent(i, j, r["sfstat"]); out["sf_alt"].SetBinContent(i, j, r["sfalt"])
        out["sf_tot"].SetBinContent(i, j, r["sftot"])
    return out


def pair_tables(name, dsum, mcsum, altsum):
    d, num, _ = PAIRS[name]
    res = {}
    for var in ("maxeta", "pt"):
        dn, dd = dsum.get(f"{d}/{num}_{var}"), dsum.get(f"{d}/den_{var}")
        mn, md = mcsum.get(f"{d}/{num}_{var}"), mcsum.get(f"{d}/den_{var}")
        an, ad = altsum.get(f"{d}/{num}_{var}"), altsum.get(f"{d}/den_{var}")
        if var == "maxeta":  # inclusive from the eta histograms (no under/overflow in |eta|)
            tot = lambda h: (h.Integral(0, h.GetNbinsX() + 1), sum(h.GetBinError(k) ** 2 for k in range(h.GetNbinsX() + 2)))
            (a, _), (b, _) = tot(dn), tot(dd)
            ed, edl, edh = eff_data(a, b)
            (mp, mp2), (ma, ma2) = tot(mn), tot(md)
            em, emerr = eff_mc(mp, mp2, ma, ma2)
            (ap, ap2), (aa, aa2) = tot(an), tot(ad)
            ea, eaerr = eff_mc(ap, ap2, aa, aa2)
            res["incl"] = dict(nden=b, ed=ed, edl=edl, edh=edh, em=em, emerr=emerr, ea=ea, eaerr=eaerr, alt=abs(ea - em))
        bins = []
        for k in range(1, dd.GetNbinsX() + 1):
            if dd.GetBinContent(k) <= 0:
                continue
            ed, edl, edh = eff_data(dn.GetBinContent(k), dd.GetBinContent(k))
            em, emerr = eff_mc(mn.GetBinContent(k), mn.GetBinError(k) ** 2, md.GetBinContent(k), md.GetBinError(k) ** 2)
            bins.append(dict(lo=dd.GetXaxis().GetBinLowEdge(k), hi=dd.GetXaxis().GetBinUpEdge(k), nden=dd.GetBinContent(k),
                             ed=ed, edl=edl, edh=edh, em=em, emerr=emerr))
        res[var] = bins
    inc = res["incl"]
    for var in ("maxeta", "pt"):
        chi2, ndf = 0., 0
        for b in res[var]:
            e = 0.5 * (b["edl"] + b["edh"])
            if e > 0 and b["nden"] >= 20:
                chi2 += ((b["ed"] - inc["ed"]) / e) ** 2
                ndf += 1
        inc[f"chi2_{var}"] = (chi2, ndf)
    return res


def fmt_leg(leg, rows):
    lep = LEGS[leg][3]
    eta_t = "|eta_SC|" if lep == "electron" else "|eta|"
    head = (f"{eta_t:>13s} {'pT':>11s} {'N_den':>9s} {'eff_data':>17s} {'eff_TT':>15s} {'eff_DY':>15s}"
            f" {'SF':>7s} {'stat':>6s} {'alt':>6s} {'tot':>6s} | {'ss':>7s} {'ref':>7s}")
    if lep == "electron":
        head += f" {'bit6':>7s} {'uncond':>7s}"
    lines = [f"## {leg}", head]
    for r in rows:
        s = (f"{r['eta'][0]:6.4g}-{r['eta'][1]:<6.4g} {r['pt'][0]:5.0f}-{r['pt'][1]:<5.0f} {r['nden']:9.0f}"
             f" {r['ed']:.4f}+{r['edh']:.4f}-{r['edl']:.4f} {r['em']:.4f}+-{r['emerr']:.4f} {r['ea']:.4f}+-{r['eaerr']:.4f}"
             f" {r['sf']:7.4f} {r['sfstat']:6.4f} {r['sfalt']:6.4f} {r['sftot']:6.4f} | {r['ss']:+7.4f} {r['ref']:+7.4f}")
        if lep == "electron":
            s += f" {r['bit6']:+7.4f} {r['uncond']:+7.4f}"
        lines.append(s)
    return lines


def fmt_pair(name, res):
    i = res["incl"]
    lines = [f"## {name}",
             f"  inclusive: N_den(data) {i['nden']:.0f}  data {i['ed']:.5f} +{i['edh']:.5f} -{i['edl']:.5f}"
             f"  TT {i['em']:.5f} +- {i['emerr']:.5f}  DY {i['ea']:.5f} +- {i['eaerr']:.5f}"
             f"  SF {i['ed'] / i['em'] if i['em'] else 0:.5f}  alt {i['alt']:.5f}",
             f"  flatness of data vs inclusive (bins with N_den >= 20): chi2/ndf max|eta| {i['chi2_maxeta'][0]:.1f}/{i['chi2_maxeta'][1]},"
             f" leading pT {i['chi2_pt'][0]:.1f}/{i['chi2_pt'][1]}"]
    for var, lab in (("maxeta", "max|eta|"), ("pt", "lead pT")):
        cells = [f"{b['lo']:g}-{b['hi']:g}: {b['ed']:.4f}/{b['em']:.4f} ({b['nden']:.0f})" for b in res[var] if b["nden"] >= 20]
        lines.append(f"  {lab} data/TT (N_den): " + "; ".join(cells))
    return lines


def graph(points, logx):
    xs, ys, exl, exh, eyl, eyh = (array("d") for _ in range(6))
    for lo, hi, v, el, eh in points:
        c = math.sqrt(lo * hi) if logx else 0.5 * (lo + hi)
        xs.append(c); ys.append(v); exl.append(c - lo); exh.append(hi - c); eyl.append(el); eyh.append(eh)
    return ROOT.TGraphAsymmErrors(len(xs), xs, ys, exl, exh, eyl, eyh)


def plot_leg(leg, rows, style):
    lep = LEGS[leg][3]
    xe, ye = BINS[leg]
    eta_t = "|#eta_{SC}|" if lep == "electron" else "|#eta|"
    outdir = plotter.plot_dir("Trigger", style, "2024") / "legs"
    for i in range(1, len(xe)):
        rs = [r for r in rows if r["i"] == i and r["nden"] > 0]
        if not rs:
            continue
        pd = [(r["pt"][0], min(r["pt"][1], 200.), r["ed"], r["edl"], r["edh"]) for r in rs]
        pm = [(r["pt"][0], min(r["pt"][1], 200.), r["em"], r["emerr"], r["emerr"]) for r in rs]
        pa = [(r["pt"][0], min(r["pt"][1], 200.), r["ea"], r["eaerr"], r["eaerr"]) for r in rs]
        ps = [(r["pt"][0], min(r["pt"][1], 200.), r["sf"], r["sftot"], r["sftot"]) for r in rs]
        lo = min(min(p[2] - p[3] for p in pd), min(p[2] for p in pm))
        ymin = max(0., math.floor((lo - 0.05) * 10.) / 10.)
        slo = min(p[2] - p[3] for p in ps); shi = max(p[2] + p[4] for p in ps)
        top = [("Data", graph(pd, True), C_DATA, ROOT.kFullCircle),
               ("t#bar{t} (powheg)", graph(pm, True), C_MC, ROOT.kFullSquare),
               ("DY (alt. MC)", graph(pa, True), C_ALT, ROOT.kOpenSquare)]
        bottom = [("Data / t#bar{t}", graph(ps, True), C_SF, ROOT.kFullCircle)]
        cfg = {"xRange": (ye[0], 200.), "xTitle": "p_{T} [GeV]", "yRange": (ymin, 1. + (1. - ymin) * 0.6),
               "rRange": (min(0.9, math.floor((slo - 0.02) * 50) / 50), max(1.1, math.ceil((shi + 0.02) * 50) / 50)),
               "logx": True, "caption": [f"{leg} leg (e#mu)", f"{xe[i - 1]:.4g} < {eta_t} < {xe[i]:.4g}"],
               "captionPos": (0.17, 0.74), "legend": (0.55, 0.66, 0.92, 0.88)}
        canv = plotter.EffCanvas(top, bottom, cfg, style=style, era="2024").draw()
        name = f"{leg}_eta{xe[i - 1]:g}to{xe[i]:g}".replace(".", "p") + "." + plotter.STYLES[style]["format"]
        plotter.save(canv.canv, outdir / name)


def plot_pair(name, res, style):
    outdir = plotter.plot_dir("Trigger", style, "2024") / "pair"
    for var, xt in (("maxeta", "max(|#eta_{1}|, |#eta_{2}|)"), ("pt", "leading p_{T} [GeV]")):
        bins = [b for b in res[var] if b["nden"] >= 20]
        if not bins:
            continue
        logx = var == "pt"
        top_hi = 200. if logx else bins[-1]["hi"]
        pd = [(b["lo"], min(b["hi"], top_hi), b["ed"], b["edl"], b["edh"]) for b in bins]
        pm = [(b["lo"], min(b["hi"], top_hi), b["em"], b["emerr"], b["emerr"]) for b in bins]
        ps = [(b["lo"], min(b["hi"], top_hi), b["ed"] / b["em"] if b["em"] else 0., b["edl"] / b["em"] if b["em"] else 0.,
               b["edh"] / b["em"] if b["em"] else 0.) for b in bins]
        lo = min(p[2] - p[3] for p in pd + pm)
        ymin = max(0., math.floor((lo - 0.02) * 50.) / 50.)
        top = [("Data", graph(pd, logx), C_DATA, ROOT.kFullCircle), ("t#bar{t} (powheg)", graph(pm, logx), C_MC, ROOT.kFullSquare)]
        bottom = [("Data / t#bar{t}", graph(ps, logx), C_SF, ROOT.kFullCircle)]
        cfg = {"xRange": (bins[0]["lo"], top_hi), "xTitle": xt, "yRange": (ymin, 1. + (1. - ymin) * 0.6), "rRange": (0.95, 1.05),
               "logx": logx, "caption": [name.replace("_", " ")], "captionPos": (0.17, 0.78), "legend": (0.55, 0.72, 0.92, 0.88)}
        canv = plotter.EffCanvas(top, bottom, cfg, style=style, era="2024").draw()
        plotter.save(canv.canv, outdir / f"{name}_{var}.{plotter.STYLES[style]['format']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--no-plots", action="store_true")
    args = ap.parse_args()

    mc, alt = Sum(mc_files(MC_NOM)), Sum(mc_files(MC_ALT))
    outdir = REPO / "Trigger" / "results" / "2024"
    outdir.mkdir(parents=True, exist_ok=True)
    fout = ROOT.TFile(str(outdir / "emu_legs.root"), "RECREATE")
    lines = ["# e-mu trigger legs and pairwise filters, 2024 (Trigger/python/measEMuEff.py)",
             "# legs: OS, reference trigger, corrected pT; eff_data Clopper-Pearson; MC weighted binomial;",
             "# SF stat / alt (|DY - TT|) / tot absolute; checks = shift of the efficiency (ss: data after",
             "# same-sign subtraction - data; ref: MC without - with the reference trigger;",
             "# bit6: bit 6 alone - nominal; uncond: unconditioned denominator - nominal)", ""]
    dsums = {}
    for leg in LEGS:
        g = LEGS[leg][0]
        dsums.setdefault(g, Sum(data_files(g)))
        rows, _ = leg_tables(leg, dsums[g], mc, alt)
        hs = leg_hists(leg, rows)
        fout.mkdir(leg).cd()
        for h in hs.values():
            h.Write()
        lines += fmt_leg(leg, rows) + [""]
        if not args.no_plots:
            plot_leg(leg, rows, args.style)
    for name in PAIRS:
        g = PAIRS[name][2]
        dsums.setdefault(g, Sum(data_files(g)))
        res = pair_tables(name, dsums[g], mc, alt)
        lines += fmt_pair(name, res) + [""]
        if not args.no_plots:
            plot_pair(name, res, args.style)
    fout.Close()
    (outdir / "summary.txt").write_text("\n".join(lines) + "\n")
    print(f"written {outdir / 'emu_legs.root'}, {outdir / 'summary.txt'}")


if __name__ == "__main__":
    main()
