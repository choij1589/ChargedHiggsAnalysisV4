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
BTagEff/results/2024/efficiencies.txt, plots BTagEff/plots/AN/2024/ (efficiency vs pT per |eta| bin and
flavour, TTLL and the cross-check).
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
PLOTS = REPO / "BTagEff" / "plots" / "AN" / "2024"
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


def plot(effs, tag):
    PLOTS.mkdir(parents=True, exist_ok=True)
    for fl, (n, d) in sorted(effs.items()):
        c = ROOT.TCanvas(f"c{fl}{tag}", "", 800, 600)
        c.SetLogx()
        leg = ROOT.TLegend(0.6, 0.15, 0.88, 0.4)
        keep = []
        for ix in range(1, d.GetNbinsX() + 1):
            pn = n.ProjectionY(f"pn{fl}{ix}{tag}", ix, ix)
            pd = d.ProjectionY(f"pd{fl}{ix}{tag}", ix, ix)
            g = pn.Clone(f"eff{fl}{ix}{tag}")
            g.Divide(pn, pd, 1., 1., "B")  # weighted histograms: binomial errors
            g.SetStats(0)
            g.SetLineColor(ix)
            g.SetMarkerColor(ix)
            g.SetMarkerStyle(20)
            g.SetTitle(f"{FLAV[fl]} jets ({tag});p_{{T}} [GeV];tagging efficiency (UParT M)")
            g.Draw("PE" if ix == 1 else "PE SAME")
            g.GetYaxis().SetRangeUser(0., 1.05 if fl == 5 else (0.4 if fl == 4 else 0.06))
            leg.AddEntry(g, f"|#eta| {d.GetXaxis().GetBinLowEdge(ix):.1f}-{d.GetXaxis().GetBinUpEdge(ix):.1f}", "pe")
            keep.append(g)
        leg.Draw()
        c.SaveAs(str(PLOTS / f"eff_{FLAV[fl]}_{tag}.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(REPO / "SKNanoOutput/DiLepton/MeasBTagEff/2024/TTLL_powheg.root"))
    ap.add_argument("--crosscheck", default=None, help="TriLepton production dir with BTagEffHists (all MC summed)")
    a = ap.parse_args()
    RES.mkdir(parents=True, exist_ok=True)
    mk = load_converter()
    lines = []
    effs = eff_hists([a.input])
    lines += table(effs, f"TTLL (DiLepton MeasBTagEff, {a.input})")
    plot(effs, "TTLL")
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
        mc = [p for p in glob.glob(os.path.join(a.crosscheck, "*.root"))
              if not any(s in os.path.basename(p) for s in ("MuonEG", "_Muon0", "_Muon1", "TTToHcToWA"))]
        effx = eff_hists(mc)
        lines += table(effx, f"cross-check: TriLepton preselection, {len(mc)} MC samples summed")
        plot(effx, "TriLepton")
    (RES / "efficiencies.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
