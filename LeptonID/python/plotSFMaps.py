"""Lepton ID efficiency and scale-factor maps from the tnp_tamsa results (phase 2.3).

  python LeptonID/python/plotSFMaps.py [--style an|pw] [--configs NAME,...]

Input: SKNanoOutput/TnP/2024/<config>/sf_egm.root for the electron configs combined
with EGM's rule (combineElectronEGM.py), otherwise <config>/efficiency.root (copied from the KNU
tnp_tamsa results; tnp_tamsa make_combined_hist: "<kind>" = nominal (s0m0)
with stat (+) systematic error, each systematic set contributing its largest
deviation from nominal; "<kind>_sys" = systematic only), and the fit-check
report checkFitStatus.txt next to it.
Output: LeptonID/plots/<STYLE>/2024/<config>/{sf,data,sim,sf_stat,sf_sys}.<ext>, with
the value (+- error) printed in every cell, pT on a log axis, and
LeptonID/plots/<STYLE>/2024/summary.txt (per config: SF range, median, largest
uncertainties, bins still flagged by the fit check).
"""
import argparse
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
import ROOT  # noqa: E402
import plotter  # noqa: E402

ERA = "2024"
INPUT = REPO / "SKNanoOutput" / "TnP" / ERA
TITLES = {
    "NUM_HcToWATight_DEN_TrackerMuons_2024": ("muon", "HcToWA tight / tracker muons"),
    "NUM_MediumID_DEN_TrackerMuons_2024": ("muon", "POG medium ID / tracker muons"),
    "NUM_TightID_DEN_TrackerMuons_2024": ("muon", "POG tight ID / tracker muons"),
    "NUM_HcToWATight_DEN_RecoElectrons_2024": ("electron", "HcToWA tight / reco electrons"),
    "NUM_HcToWATight_DEN_RecoElectrons_2024_altMC": ("electron", "HcToWA tight, LO DY MC (cross-check)"),
    "NUM_wp90noiso_DEN_RecoElectrons_2024": ("electron", "POG MVA noIso WP90 / reco electrons"),
    "NUM_cutBasedTight_DEN_RecoElectrons_2024": ("electron", "POG cut-based tight / reco electrons"),
    # dimuon trigger legs (PLAN_Trigger step 1; tnp_tamsa HcToWA_MuonTrig_2024, probe = HcToWA tight)
    "NUM_Mu17Leg1_DEN_HcToWATight_2024": ("muon", "Mu17 leg (DoubleMu) / HcToWA tight"),
    "NUM_Mu8Leg2_DEN_HcToWATight_2024": ("muon", "Mu8 leg (DoubleMu) / HcToWA tight"),
}


def stat_only(h_total, h_sys, name):
    """Nominal with the statistical error only: sqrt(total^2 - sys^2)."""
    h = h_total.Clone(name)
    for i in range(h.GetNcells()):
        t, s = h_total.GetBinError(i), h_sys.GetBinError(i)
        h.SetBinError(i, math.sqrt(max(t * t - s * s, 0.)))
    return h


def flagged_bins(report):
    if not report.exists():
        return []
    out, on = [], False
    for line in report.read_text().splitlines():
        if "bins to refit" in line:
            on = True
            continue
        if on and line.strip().startswith("bin"):
            out.append(line.strip())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--configs", default="")
    args = ap.parse_args()
    ROOT.gROOT.SetBatch(True)
    configs = [c for c in TITLES if (not args.configs or c in args.configs.split(",")) and (INPUT / c / "efficiency.root").exists()]
    summary = []
    for cfg_name in configs:
        lepton, title = TITLES[cfg_name]
        # electrons: SFs combined with EGM's rule (combineElectronEGM.py) when available
        src = INPUT / cfg_name / ("sf_egm.root" if (INPUT / cfg_name / "sf_egm.root").exists() else "efficiency.root")
        f = ROOT.TFile.Open(str(src))
        hs = {k: f.Get(k) for k in ("sf", "sf_sys", "data", "sim")}
        for h in hs.values():
            h.SetDirectory(0)
        hs["sf_stat"] = stat_only(hs["sf"], hs["sf_sys"], "sf_stat")
        f.Close()
        xt = "#eta_{SC}" if lepton == "electron" else "#eta"
        zt = {"sf": "SF (stat #oplus syst)", "sf_stat": "SF (stat)", "sf_sys": "SF (syst)",
              "data": "Data efficiency", "sim": "Simulation efficiency"}
        zr = {"sf": (0.75, 1.1), "sf_stat": (0.75, 1.1), "sf_sys": (0.75, 1.1), "data": (0.3, 1.0), "sim": (0.3, 1.0)}
        outdir = plotter.plot_dir("LeptonID", args.style, ERA) / cfg_name
        for key in ("sf", "sf_stat", "sf_sys", "data", "sim"):
            cfg = {"xTitle": xt, "yTitle": "p_{T} [GeV]", "zTitle": zt[key], "zRange": zr[key], "logy": True,
                   "text": "4.3f", "text_errors": True, "text_size": 0.55 if lepton == "muon" else 0.6,
                   "caption": [title], "show_lumi": key != "sim", "zTitleOffset": 1.35,
                   # frame extended above the last pT bin, so the caption does not cover the top row
                   "yRange": (hs[key].GetYaxis().GetXmin(), 2.5 * hs[key].GetYaxis().GetXmax())}
            canv = plotter.Map2DCanvas(hs[key], cfg, style=args.style, era=ERA, has_data=key != "sim").draw()
            plotter.save(canv.canv, outdir / f"{key}.{plotter.STYLES[args.style]['format']}")
        sf, sys_h = hs["sf"], hs["sf_sys"]
        vals = []
        for ix in range(1, sf.GetNbinsX() + 1):
            for iy in range(1, sf.GetNbinsY() + 1):
                v = sf.GetBinContent(ix, iy)
                if v == 0 or v != v:
                    continue
                vals.append((v, sf.GetBinError(ix, iy), sys_h.GetBinError(ix, iy),
                             "eta[%g,%g] pT[%g,%g]" % (sf.GetXaxis().GetBinLowEdge(ix), sf.GetXaxis().GetBinUpEdge(ix),
                                                       sf.GetYaxis().GetBinLowEdge(iy), sf.GetYaxis().GetBinUpEdge(iy))))
        vs = sorted(v[0] for v in vals)
        flags = flagged_bins(INPUT / cfg_name / "checkFitStatus.txt")
        summary.append("== %s (%s)" % (cfg_name, title))
        summary.append("   %d cells; SF min %.4f, median %.4f, max %.4f; NaN cells %d" % (
            len(vals), vs[0], vs[len(vs) // 2], vs[-1],
            sum(1 for ix in range(1, sf.GetNbinsX() + 1) for iy in range(1, sf.GetNbinsY() + 1) if sf.GetBinContent(ix, iy) != sf.GetBinContent(ix, iy))))
        for v, e, s, where in sorted(vals, key=lambda t: -t[1])[:3]:
            summary.append("   largest unc.: %s SF %.4f +- %.4f (syst %.4f)" % (where, v, e, s))
        summary.append("   fit results still flagged: %d %s" % (len(flags), " ".join(flags[:12]) + (" ..." if len(flags) > 12 else "")))
    out = plotter.plot_dir("LeptonID", args.style, ERA) / "summary.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(summary) + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
