"""MC trigger closure: observed path decision vs expected from the legs (PLAN_Trigger step 3, T1/T3).

  python Trigger/python/trigClosure.py [--production TrigDZ] [--add-dz]

Input: DiLepton production SKNanoOutput/DiLepton/Run{DiMu,EMu}_RunSyst_<production>/2024/,
histograms <ch>/Central/TrigClosure/{incl,pt1,pt2,maxeta}_{den,obs,exp}: events passing the
lepton-level DIMU / EMU selection without the trigger requirement (EMU without the jet cuts),
weight MC x pileup; obs = path decision fired, exp = sum of the per-event T1 efficiency (MC legs).
Closure = obs/exp. The closure is a check, not an uncertainty (user 2026-11-26): it passes when
|obs/exp - 1| is within the trigger-SF uncertainty defined by the measurements (legs and pairwise
filters), sigma = relative variation of the MC yield in the <Trig>SF_Up/Down lanes of the
production (key muons/1/pt, the samples of the set), taken in the direction of the non-closure
(obs < exp: Down), with the statistical error in quadrature. --add-dz adds the relative DZ
uncertainty of the JSON (PairFilter effDataUp/Down) linearly, for productions whose lanes were
made before the DZ uncertainty existed (TrigSF, 2026-11-26). Checked on the dimuon set with DY
and tt, on the e-mu set with tt (DY -> tau tau for reference, user 2026-11-26). Uncertainty: binomial on obs, sqrt(eps (1 - eps) sum w^2(den)) / exp, with
eps = obs/den (exp treated as exact).
Dimuon: the legs are measured by tag and probe with an IsoMu24 tag, so the check is made on the events
with HLT_IsoMu24 fired (TrigClosure/IsoMu24/); the inclusive closure differs by the event-level factor
C = eps(path) / eps(path | IsoMu24), assumed equal in data and MC (user 2026-11-26), reported as C_MC
together with the subset with a candidate L1 seed of the path fired (TrigClosure/L1Seed/). Productions
without the subsets (TrigSF) fall back to the inclusive check.
Samples: DY (MLL 10-50 and 50-inf, the flavour of the channel) and tt (TTLL powheg).
Output: Trigger/results/2024/closure.txt (inclusive and binned tables, the check) and Trigger/plots/AN/2024/closure/*.png.
"""
import argparse
import math
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
ERA = "2024"
SETS = {
    "DIMU": {"flags": "RunDiMu", "trig": "DblMu",
             "samples": {"DY": ["DYto2Mu_2J_MLL10to50", "DYto2Mu_2J_MLL50toInf"], "tt": ["TTLL_powheg"]},
             "check": ["DY", "tt"], "dz": "DblMu_DZ", "subs": ["IsoMu24", "L1Seed"], "check_sub": "IsoMu24"},
    "EMU": {"flags": "RunEMu", "trig": "EMu",
            "samples": {"DY": ["DYto2Tau_2J_MLL10to50", "DYto2Tau_2J_MLL50toInf"], "tt": ["TTLL_powheg"]},
            "check": ["tt"], "dz": "EMu_DZ", "subs": [], "check_sub": None},  # e-mu: DY (tau tau) for reference only (user 2026-11-26)
}
# DIMU: pt1/pt2 = leading/subleading muon; EMU: pt1 = muon, pt2 = electron (DiLepton::FillTrigClosure)
VARS = {"DIMU": {"pt1": "leading-muon p_{T} [GeV]", "pt2": "subleading-muon p_{T} [GeV]", "maxeta": "max |#eta|"},
        "EMU": {"pt1": "muon p_{T} [GeV]", "pt2": "electron p_{T} [GeV]", "maxeta": "max |#eta|"}}
# coarse rebinning of the 5 GeV pT histograms for the tables and plots
PT_EDGES = [10, 15, 20, 25, 30, 40, 50, 70, 100, 150, 255]


def get(ch, prod, samples, name, sub=None, required=True):
    out = None
    path = f"{ch}/Central/TrigClosure/" + (f"{sub}/" if sub else "") + name
    for s in samples:
        f = ROOT.TFile.Open(str(REPO / "SKNanoOutput" / "DiLepton" / f"{SETS[ch]['flags']}_RunSyst_{prod}" / ERA / f"{s}.root"))
        h = f.Get(path)
        if not h:
            if not required:
                f.Close()
                return None
            raise SystemExit(f"{s}: {path} missing")
        h = h.Clone(f"{ch}_{s}_{name}")
        h.SetDirectory(0)
        f.Close()
        if out is None:
            out = h
        else:
            out.Add(h)
    return out


def rebin(h, var):
    if not var.startswith("pt"):
        return h
    import array
    return h.Rebin(len(PT_EDGES) - 1, h.GetName() + "_rb", array.array("d", PT_EDGES))


def ratio(den, obs, exp, i):
    d, o, e = den.GetBinContent(i), obs.GetBinContent(i), exp.GetBinContent(i)
    if d <= 0 or e <= 0:
        return None
    eps = min(max(o / d, 0.), 1.)
    err = math.sqrt(eps * (1 - eps) * den.GetSumw2().At(i)) / e if den.GetSumw2N() else 0.
    return o / e, err, o / d, e / d, d


def lane_sigma(ch, prod, samples):
    """Relative MC-yield variation (up, down) of the trigger-SF lanes, key muons/1/pt."""
    lane = f"{SETS[ch]['trig']}TrigSF"
    tot = {}
    for ln in ("Central", lane + "_Up", lane + "_Down"):
        tot[ln] = 0.
        for s in samples:
            f = ROOT.TFile.Open(str(REPO / "SKNanoOutput" / "DiLepton" / f"{SETS[ch]['flags']}_RunSyst_{prod}" / ERA / f"{s}.root"))
            h = f.Get(f"{ch}/{ln}/muons/1/pt")
            if not h:
                raise SystemExit(f"{s}: {ch}/{ln}/muons/1/pt missing")
            tot[ln] += h.Integral(0, h.GetNbinsX() + 1)
            f.Close()
    return tot[lane + "_Up"] / tot["Central"] - 1, 1 - tot[lane + "_Down"] / tot["Central"]


def dz_sigma(name):
    import correctionlib
    pf = correctionlib.CorrectionSet.from_file(str(REPO / "Trigger" / "data" / ERA / "trigger_HcToWA.json"))["PairFilter"]
    d = pf.evaluate(name, "effData")
    return pf.evaluate(name, "effDataUp") / d - 1, 1 - pf.evaluate(name, "effDataDown") / d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--production", default="TrigDZ")
    ap.add_argument("--add-dz", action="store_true", help="add the DZ uncertainty of the JSON to the lane variation")
    args = ap.parse_args()
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    pdir = REPO / "Trigger" / "plots" / "AN" / ERA / "closure"
    pdir.mkdir(parents=True, exist_ok=True)
    lines = [f"# MC trigger closure, production {args.production} (Trigger/python/trigClosure.py)",
             "# obs/exp = path decision / expected from the MC legs (T1); eff = obs/den, exp/den", ""]
    verdicts = []
    for ch, c in SETS.items():
        lines.append(f"## {ch} ({c['trig']})")
        incl = {}
        for tag, samples in c["samples"].items():
            h = {k: get(ch, args.production, samples, f"incl_{k}") for k in ("den", "obs", "exp")}
            r = ratio(h["den"], h["obs"], h["exp"], 1)
            incl[tag] = r
            lines.append(f"  {tag:3s} inclusive: obs/exp {r[0]:.4f} +- {r[1]:.4f}   eff obs {r[2]:.4f} exp {r[3]:.4f}   N_den(w) {r[4]:.4g}")
            for sub in c["subs"]:
                hs = {k: get(ch, args.production, samples, f"incl_{k}", sub, required=False) for k in ("den", "obs", "exp")}
                if hs["den"] is None:
                    continue
                rs = ratio(hs["den"], hs["obs"], hs["exp"], 1)
                incl[(tag, sub)] = rs
                lines.append(f"      {sub:8s}: obs/exp {rs[0]:.4f} +- {rs[1]:.4f}   eff obs {rs[2]:.4f} exp {rs[3]:.4f}   fraction of den {rs[4] / r[4]:.3f}"
                             + (f"   C_MC = incl / {sub} = {r[0] / rs[0]:.4f}" if sub == c["check_sub"] else ""))
        sig = {}
        for tag in c["check"]:
            up, dn = lane_sigma(ch, args.production, c["samples"][tag])
            if args.add_dz:
                zu, zd = dz_sigma(c["dz"])
                up, dn = up + zu, dn + zd
            sig[tag] = (up, dn)
        lines.append("  SF uncertainty (lanes" + (" + DZ" if args.add_dz else "") + "): "
                     + ", ".join(f"{t} +{u:.4f} -{d:.4f}" for t, (u, d) in sig.items()))
        for tag in c["check"]:
            sub = c["check_sub"] if (tag, c["check_sub"]) in incl else None
            r = incl[(tag, sub)] if sub else incl[tag]
            s_ = math.hypot(sig[tag][1] if r[0] < 1 else sig[tag][0], r[1])
            ok = abs(r[0] - 1) <= s_
            verdicts.append(f"{ch} {tag}{' (' + sub + ')' if sub else ' (inclusive)'}: |obs/exp - 1| = {abs(r[0] - 1):.4f} vs sigma {s_:.4f} -> {'PASS' if ok else 'FAIL'}")
            lines.append("  check: " + verdicts[-1])
        for sub in [None] + ([c["check_sub"]] if c["check_sub"] else []):
            suffix = f"_{sub}" if sub else ""
            for var, title in VARS[ch].items():
                lines.append(f"  -- {var}" + (f" ({sub} fired)" if sub else ""))
                graphs = []
                for tag, samples in c["samples"].items():
                    h = {k: get(ch, args.production, samples, f"{var}_{k}", sub, required=sub is None) for k in ("den", "obs", "exp")}
                    if h["den"] is None:
                        break
                    h = {k: rebin(v, var) for k, v in h.items()}
                    g = ROOT.TGraphErrors()
                    ax = h["den"].GetXaxis()
                    row = []
                    for i in range(1, ax.GetNbins() + 1):
                        r = ratio(h["den"], h["obs"], h["exp"], i)
                        if r is None or r[4] < 1e-3 * h["den"].Integral():
                            continue
                        g.SetPoint(g.GetN(), ax.GetBinCenter(i), r[0])
                        g.SetPointError(g.GetN() - 1, ax.GetBinWidth(i) / 2, r[1])
                        row.append(f"[{ax.GetBinLowEdge(i):g},{ax.GetBinUpEdge(i):g}] {r[0]:.3f}+-{r[1]:.3f}")
                    lines.append(f"    {tag:3s} " + "  ".join(row))
                    graphs.append((tag, g))
                if not graphs:
                    lines.pop()
                    continue
                canv = ROOT.TCanvas(f"c_{ch}_{var}_{sub}", "", 800, 600)
                canv.SetLeftMargin(0.13)
                lo, hi = (PT_EDGES[0], PT_EDGES[-1]) if var.startswith("pt") else (0., 2.5)
                frame = canv.DrawFrame(lo, 0.9, hi, 1.1, f";{title};observed / expected")
                if var.startswith("pt"):
                    canv.SetLogx()
                    frame.GetXaxis().SetMoreLogLabels()
                leg = ROOT.TLegend(0.65, 0.75, 0.88, 0.88)
                leg.SetBorderSize(0)
                for (tag, g), col, mk in zip(graphs, (ROOT.kAzure + 1, ROOT.kRed + 1), (20, 21)):
                    g.SetMarkerColor(col)
                    g.SetLineColor(col)
                    g.SetMarkerStyle(mk)
                    g.Draw("P same")
                    leg.AddEntry(g, tag, "lp")
                line = ROOT.TLine(lo, 1., hi, 1.)
                line.SetLineStyle(2)
                line.Draw()
                leg.Draw()
                txt = ROOT.TLatex()
                txt.SetNDC()
                txt.SetTextSize(0.04)
                txt.DrawLatex(0.15, 0.85, f"{ch}: {c['trig']} trigger, MC closure" + (f", {sub} fired" if sub else ""))
                canv.SaveAs(str(pdir / f"{ch}_{var}{suffix}.png"))
                canv.SaveAs(str(pdir / f"{ch}_{var}{suffix}.pdf"))
        lines.append("")
    lines.append("# closure check: " + "; ".join(verdicts))
    out = REPO / "Trigger" / "results" / ERA / "closure.txt"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
