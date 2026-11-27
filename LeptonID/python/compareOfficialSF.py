"""Validate our TnP measurement against the central POG 2024 results: data efficiency,
MC efficiency and scale factor, cell by cell.

  python LeptonID/python/compareOfficialSF.py [--style an|pw]

The same tnp_tamsa setup that measures our HcToWA tight IDs also measures POG
working points; these are compared with the central results at the centre of
each of our cells (same binning as the POG ones):
  electrons  NUM_{cutBasedTight,wp90noiso}_DEN_RecoElectrons_2024  vs  EGM
             electron.json "Electron-ID-SF" ("2024Prompt", Tight / wp90noiso):
             effData, effMC, sf, err_statData, err_statMC, sfup
  muons      NUM_{MediumID,TightID}_DEN_TrackerMuons_2024  vs  MUO:
             SF: muon_Z.json ("nominal", "stat"); data and MC efficiencies from
             the per-bin MUO fit files (muo_fits/<WP>/<WP>_eta_<i>_pt_<j>.root,
             linked from the MUO slides): data = the fitted efficiency printed on
             the fit canvas, MC = count of the stored MC pass/fail histograms in
             70-110 GeV. Their ratio reproduces muon_Z.json (checked here).
Ours: SKNanoOutput/TnP/2024/<config>/efficiency.root; data_s0m0 / sim_s0m0 /
sf_s0m0 (nominal fit, statistical error) for the pulls, "sf" (stat + syst) for
the SF pulls. Official files: SKNanoOutput/TnP/2024/official/ (SOURCE.txt).
Prints per working point and quantity: median and max |ours - official|, the
pull distribution (|pull| > 3 cells listed), and the cells below 20 GeV; draws
ours / official maps LeptonID/plots/<STYLE>/2024/validation/<config>_{data,sim,sf}.
"""
import argparse
import ctypes
import re
import sys
from pathlib import Path

import correctionlib
import ROOT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
import plotter  # noqa: E402

D = REPO / "SKNanoOutput" / "TnP" / "2024"
O = D / "official"


def ours(config):
    f = ROOT.TFile.Open(str(D / config / "efficiency.root"))
    hs = {k: f.Get(k) for k in ("data_s0m0", "sim_s0m0", "sf_s0m0", "sf")}
    for h in hs.values():
        h.SetDirectory(0)
    f.Close()
    egm = D / config / "sf_egm.root"
    if egm.exists():  # electrons: SF with EGM's uncertainty rule (combineElectronEGM.py)
        g = ROOT.TFile.Open(str(egm))
        hs["sf"] = g.Get("sf")
        hs["sf"].SetDirectory(0)
        g.Close()
    return hs


def cells(h):
    for ix in range(1, h.GetNbinsX() + 1):
        for iy in range(1, h.GetNbinsY() + 1):
            if h.GetBinContent(ix, iy) > 0:
                yield ix, iy, h.GetXaxis().GetBinCenter(ix), h.GetYaxis().GetBinCenter(iy)


def muo_effs(wp, ieta, ipt, lo=70., hi=110.):
    """MUO data efficiency (fit) and MC efficiency (count in [lo, hi]) for one bin.
    The MC histograms are read before the canvas: the canvas holds the data
    histograms under the same names."""
    path = O / "muo_fits" / wp / ("%s_eta_%d_pt_%d.root" % (wp, ieta, ipt))
    f = ROOT.TFile.Open(str(path))
    base = "%s_eta_%d_pt_%d" % (wp, ieta, ipt)
    vals = []
    for side in ("GenPass", "GenFail"):
        h = f.Get(base + "_" + side).Clone(side + "_%d_%d" % (ieta, ipt))
        h.SetDirectory(0)
        e = ctypes.c_double(0.)
        vals.append((h.IntegralAndError(h.FindBin(lo + 1e-6), h.FindBin(hi - 1e-6), e), e.value))
    (p, ep), (q, eq) = vals
    mc, mc_err = p / (p + q), ((ep * q) ** 2 + (eq * p) ** 2) ** 0.5 / (p + q) ** 2
    canv = f.Get(base + "_Canv").GetPrimitive("c_1")
    data = data_err = None
    for o in canv.GetListOfPrimitives():
        if o.InheritsFrom("TPave"):
            for line in o.GetListOfLines():
                m = re.search(r"eff = ([0-9.]+) #pm ([0-9.]+)", line.GetTitle())
                if m:
                    data, data_err = float(m.group(1)), float(m.group(2))
    f.Close()
    return data, data_err, mc, mc_err


def summarize(label, rows, low_pt=20.):
    """rows: (x, y, ours, ours_err, official, official_err)"""
    diffs = sorted(abs(r[2] - r[4]) for r in rows)
    pulls = [((r[2] - r[4]) / (r[3] ** 2 + r[5] ** 2) ** 0.5 if r[3] ** 2 + r[5] ** 2 > 0 else 0., r) for r in rows]
    ap = sorted(abs(p) for p, _ in pulls)
    print("   %-9s |ours - official| median %.4f, max %.4f | |pull| median %.2f, >2: %d, >3: %d of %d" % (
        label, diffs[len(diffs) // 2], diffs[-1], ap[len(ap) // 2], sum(p > 2 for p in ap), sum(p > 3 for p in ap), len(ap)))
    for p, r in sorted(pulls, key=lambda t: -abs(t[0])):
        if abs(p) > 3:
            print("       pull %+5.1f at eta %+.2f pT %5.1f: ours %.4f+-%.4f official %.4f+-%.4f" % (p, r[0], r[1], r[2], r[3], r[4], r[5]))
    return pulls


def ratio_map(template, rows, name):
    h = template.Clone(name)
    h.Reset()
    for x, y, a, ea, b, eb in rows:
        ib = h.FindBin(x, y)
        if b > 0:
            h.SetBinContent(ib, a / b)
            h.SetBinError(ib, ((ea / b) ** 2 + (a * eb / b ** 2) ** 2) ** 0.5)
    return h


def draw(h, config, kind, lepton, style, zr):
    cfg = {"xTitle": "#eta_{SC}" if lepton == "electron" else "#eta", "yTitle": "p_{T} [GeV]",
           "zTitle": {"data": "Data eff.", "sim": "MC eff.", "sf": "SF"}[kind] + " ours / POG", "zRange": zr, "logy": True,
           "text": "5.3f", "text_errors": False, "text_size": 0.7, "caption": [config.replace("_2024", "")]}
    canv = plotter.Map2DCanvas(h, cfg, style=style, era="2024", has_data=kind != "sim").draw()
    out = plotter.plot_dir("LeptonID", style, "2024") / "validation" / ("%s_%s.%s" % (config, kind, plotter.STYLES[style]["format"]))
    plotter.save(canv.canv, out)


def electrons(style):
    ele = correctionlib.CorrectionSet.from_file(str(O / "electron.json.gz"))["Electron-ID-SF"]
    for config, wp in [("NUM_cutBasedTight_DEN_RecoElectrons_2024", "Tight"), ("NUM_wp90noiso_DEN_RecoElectrons_2024", "wp90noiso")]:
        hs = ours(config)
        rows = {"data": [], "sim": [], "sf": []}
        low = []
        for ix, iy, x, y in cells(hs["sf"]):
            ev = lambda k: ele.evaluate("2024Prompt", k, wp, x, y)
            rows["data"].append((x, y, hs["data_s0m0"].GetBinContent(ix, iy), hs["data_s0m0"].GetBinError(ix, iy), ev("effData"), ev("err_statData")))
            rows["sim"].append((x, y, hs["sim_s0m0"].GetBinContent(ix, iy), hs["sim_s0m0"].GetBinError(ix, iy), ev("effMC"), ev("err_statMC")))
            rows["sf"].append((x, y, hs["sf"].GetBinContent(ix, iy), hs["sf"].GetBinError(ix, iy), ev("sf"), ev("sfup") - ev("sf")))
            if y < 20:
                low.append(len(rows["sf"]) - 1)
        print("== %s vs EGM %s (electron.json; data/MC: statistical errors, SF: total)" % (config, wp))
        for k in ("data", "sim", "sf"):
            summarize(k, rows[k])
            draw(ratio_map(hs["sf"], rows[k], "%s_%s_ratio" % (config, k)), config, k, "electron", style, (0.95, 1.05) if k != "sf" else (0.9, 1.1))
        print("   10-20 GeV:      data ours / EGM       MC ours / EGM        SF ours / EGM")
        for i in low:
            d, s, f = rows["data"][i], rows["sim"][i], rows["sf"][i]
            print("     eta %+.2f   %.3f / %.3f (%+.1f)   %.3f / %.3f (%+.1f)   %.3f+-%.3f / %.3f+-%.3f" % (
                d[0], d[2], d[4], (d[2] - d[4]) / (d[3] ** 2 + d[5] ** 2) ** 0.5, s[2], s[4], (s[2] - s[4]) / (s[3] ** 2 + s[5] ** 2) ** 0.5, f[2], f[3], f[4], f[5]))


def muons(style):
    mu = correctionlib.CorrectionSet.from_file(str(O / "muon_Z.json.gz"))
    for config, wp in [("NUM_MediumID_DEN_TrackerMuons_2024", "NUM_MediumID_DEN_TrackerMuons"), ("NUM_TightID_DEN_TrackerMuons_2024", "NUM_TightID_DEN_TrackerMuons")]:
        hs = ours(config)
        rows = {"data": [], "sim": [], "sf": []}
        repro = []
        for ix, iy, x, y in cells(hs["sf"]):
            d, de, m, me = muo_effs(wp, ix, iy)
            sf, sfst = mu[wp].evaluate(x, y, "nominal"), mu[wp].evaluate(x, y, "stat")
            sfup = mu[wp].evaluate(x, y, "systup")
            repro.append(abs(d / m - sf))
            rows["data"].append((x, y, hs["data_s0m0"].GetBinContent(ix, iy), hs["data_s0m0"].GetBinError(ix, iy), d, de))
            rows["sim"].append((x, y, hs["sim_s0m0"].GetBinContent(ix, iy), hs["sim_s0m0"].GetBinError(ix, iy), m, me))
            rows["sf"].append((x, y, hs["sf"].GetBinContent(ix, iy), hs["sf"].GetBinError(ix, iy), sf, sfup - sf))
        repro.sort()
        print("== %s vs MUO %s (data: MUO fit, MC: MUO count 70-110 GeV, statistical errors; SF: muon_Z.json, total)" % (config, wp))
        print("   check: MUO data/MC reproduces muon_Z.json SF to median %.1e, max %.1e" % (repro[len(repro) // 2], repro[-1]))
        for k in ("data", "sim", "sf"):
            summarize(k, rows[k])
            draw(ratio_map(hs["sf"], rows[k], "%s_%s_ratio" % (config, k)), config, k, "muon", style, (0.98, 1.02))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    args = ap.parse_args()
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    electrons(args.style)
    muons(args.style)
