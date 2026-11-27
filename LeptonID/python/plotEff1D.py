"""1D lepton ID efficiency and scale-factor plots (style of the V3 LeptonIDTest efficiency plots).

  python LeptonID/python/plotEff1D.py [--style an|pw] [--configs NAME,...]

For every config: efficiency vs pT in each eta bin, and vs eta in each pT bin.
Top pad: data (filled circles) and MC (filled squares) efficiencies of the nominal
fit, statistical errors. Bottom pad: SF with its total uncertainty (muons:
efficiency.root "sf", tnp_tamsa combination; electrons: sf_egm.root "sf", EGM rule).
For the POG working points the central POG results are overlaid with open markers,
slightly shifted in x: MUO (MediumID, TightID: data and MC efficiencies from the MUO
fit files, SF from muon_Z.json, total uncertainty) and EGM (cut-based Tight,
wp90noiso: effData, effMC with statistical errors, SF with sfup - sf); see
compareOfficialSF.py for the inputs.
Also the V3 "multi_eta" plot (MeasTrigEff/python/plotMuIDEff.py): data efficiency and
SF vs pT for all eta bins in one figure, linear pT axis.
Output: LeptonID/plots/<STYLE>/2024/<config>/eff1d/{vs_pt_eta_<lo>to<hi>,vs_eta_pt_<lo>to<hi>,vs_pt_multi_eta}.<ext>
"""
import argparse
import math
import sys
from array import array
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import correctionlib  # noqa: E402
import ROOT  # noqa: E402
import plotter  # noqa: E402
from compareOfficialSF import muo_effs  # noqa: E402
from plotSFMaps import TITLES  # noqa: E402

D = REPO / "SKNanoOutput" / "TnP" / "2024"
O = D / "official"
POG = {"NUM_MediumID_DEN_TrackerMuons_2024": ("MUO", "NUM_MediumID_DEN_TrackerMuons"),
       "NUM_TightID_DEN_TrackerMuons_2024": ("MUO", "NUM_TightID_DEN_TrackerMuons"),
       "NUM_cutBasedTight_DEN_RecoElectrons_2024": ("EGM", "Tight"),
       "NUM_wp90noiso_DEN_RecoElectrons_2024": ("EGM", "wp90noiso")}
C_DATA, C_MC = plotter.PALETTE_LONG[0], plotter.PALETTE_LONG[1]
C_SF = "#000000"
C_POG_DATA, C_POG_MC, C_POG_SF = plotter.PALETTE_LONG[2], plotter.PALETTE_LONG[4], plotter.PALETTE_LONG[3]


def load(config):
    f = ROOT.TFile.Open(str(D / config / "efficiency.root"))
    h = {"data": f.Get("data_s0m0"), "sim": f.Get("sim_s0m0"), "sf": f.Get("sf")}
    for v in h.values():
        v.SetDirectory(0)
    f.Close()
    if (D / config / "sf_egm.root").exists():
        g = ROOT.TFile.Open(str(D / config / "sf_egm.root"))
        h["sf"] = g.Get("sf")
        h["sf"].SetDirectory(0)
        g.Close()
    return h


def official(config, hist):
    """{(ix, iy): (data, data_err, mc, mc_err, sf, sf_err)} for the POG working points."""
    if config not in POG:
        return None
    pog, key = POG[config]
    out = {}
    ax, ay = hist.GetXaxis(), hist.GetYaxis()
    if pog == "EGM":
        ele = correctionlib.CorrectionSet.from_file(str(O / "electron.json.gz"))["Electron-ID-SF"]
    else:
        mu = correctionlib.CorrectionSet.from_file(str(O / "muon_Z.json.gz"))[key]
    for ix in range(1, ax.GetNbins() + 1):
        for iy in range(1, ay.GetNbins() + 1):
            if hist.GetBinContent(ix, iy) <= 0:
                continue
            x, y = ax.GetBinCenter(ix), ay.GetBinCenter(iy)
            if pog == "EGM":
                e = lambda k: ele.evaluate("2024Prompt", k, key, x, y)
                out[(ix, iy)] = (e("effData"), e("err_statData"), e("effMC"), e("err_statMC"), e("sf"), e("sfup") - e("sf"))
            else:
                d, de, m, me = muo_effs(key, ix, iy)
                sf = mu.evaluate(x, y, "nominal")
                out[(ix, iy)] = (d, de, m, me, sf, mu.evaluate(x, y, "systup") - sf)
    return out


def graph(points, shift=0., logx=False):
    """points: list of (lo, hi, value, error) -> TGraphAsymmErrors at the bin centre
    (geometric centre on a log axis), x errors to the bin edges."""
    xs, ys, exl, exh, eyl, eyh = (array("d") for _ in range(6))
    for lo, hi, v, e in points:
        c = math.sqrt(lo * hi) if logx else 0.5 * (lo + hi)
        c = c * (1. + shift) if logx else c + shift
        xs.append(c)
        ys.append(v)
        exl.append(max(c - lo, 0.))
        exh.append(max(hi - c, 0.))
        eyl.append(e)
        eyh.append(e)
    return ROOT.TGraphAsymmErrors(len(xs), xs, ys, exl, exh, eyl, eyh)


def ranges(top, bottom):
    vals = [(v, e) for pts in top for _, _, v, e in pts]
    lo = min(v - e for v, e in vals)
    ymin = max(0., math.floor((lo - 0.05) * 20.) / 20.)
    ymax = 1. + (1. - ymin) * 0.55
    rv = [(v, e) for pts in bottom for _, _, v, e in pts]
    rlo, rhi = min(v - e for v, e in rv), max(v + e for v, e in rv)
    pad = max(0.2 * (rhi - rlo), 0.01)
    rmin, rmax = math.floor((rlo - pad) * 100.) / 100., math.ceil((rhi + pad) * 100.) / 100.
    rmax = max(rmax, 1.0 + pad)
    rmax += 0.45 * (rmax - rmin)  # room for the SF legend at the top of the lower pad
    return (ymin, ymax), (rmin, rmax)


def tag(lo, hi):
    return ("%gto%g" % (lo, hi)).replace("-", "m").replace(".", "p")


def plot_config(config, style):
    lepton, title = TITLES[config]
    h = load(config)
    off = official(config, h["sf"])
    pog = POG[config][0] if config in POG else None
    ax, ay = h["sf"].GetXaxis(), h["sf"].GetYaxis()
    eta_t = "#eta_{SC}" if lepton == "electron" else "#eta"
    outdir = plotter.plot_dir("LeptonID", style, "2024") / config / "eff1d"
    n = 0
    for mode in ("vs_pt", "vs_eta"):
        outer = ax if mode == "vs_pt" else ay
        inner = ay if mode == "vs_pt" else ax
        for io in range(1, outer.GetNbins() + 1):
            cells = [(io, ii) if mode == "vs_pt" else (ii, io) for ii in range(1, inner.GetNbins() + 1)]
            cells = [c for c in cells if h["sf"].GetBinContent(*c) > 0]
            if not cells:
                continue  # ECAL gap
            edges = lambda c: (ay.GetBinLowEdge(c[1]), ay.GetBinUpEdge(c[1])) if mode == "vs_pt" else (ax.GetBinLowEdge(c[0]), ax.GetBinUpEdge(c[0]))
            pts = {k: [(*edges(c), h[k].GetBinContent(*c), h[k].GetBinError(*c)) for c in cells] for k in ("data", "sim", "sf")}
            logx = mode == "vs_pt"
            top = [("Data", graph(pts["data"], 0., logx), C_DATA, ROOT.kFullCircle),
                   ("Simulation", graph(pts["sim"], 0., logx), C_MC, ROOT.kFullSquare)]
            bottom = [("This measurement", graph(pts["sf"], 0., logx), C_SF, ROOT.kFullCircle)]
            tops, bottoms = [pts["data"], pts["sim"]], [pts["sf"]]
            if off:
                o = {k: [(*edges(c), off[c][2 * i], off[c][2 * i + 1]) for c in cells] for i, k in enumerate(("data", "sim", "sf"))}
                sh = 0.06 if logx else 0.04
                top += [("Data (%s)" % pog, graph(o["data"], sh, logx), C_POG_DATA, ROOT.kOpenCircle),
                        ("Simulation (%s)" % pog, graph(o["sim"], sh, logx), C_POG_MC, ROOT.kOpenSquare)]
                bottom += [(pog, graph(o["sf"], sh, logx), C_POG_SF, ROOT.kOpenCircle)]
                tops += [o["data"], o["sim"]]
                bottoms += [o["sf"]]
            yr, rr = ranges(tops, bottoms)
            lo, hi = outer.GetBinLowEdge(io), outer.GetBinUpEdge(io)
            if mode == "vs_pt":
                cap = [title, "%.4g < %s < %.4g" % (lo, eta_t, hi)]
                xr, xt = (inner.GetXmin(), inner.GetXmax()), "p_{T} [GeV]"
            else:
                cap = [title, "%g < p_{T} < %g GeV" % (lo, hi)]
                xr, xt = (inner.GetXmin(), inner.GetXmax()), eta_t
            cfg = {"xRange": xr, "xTitle": xt, "yTitle": "Efficiency", "rTitle": "Data / MC", "yRange": yr, "rRange": rr,
                   "logx": logx, "caption": cap, "captionPos": (0.17, 0.74), "legend": (0.55, 0.62 if off else 0.74, 0.92, 0.88)}
            canv = plotter.EffCanvas(top, bottom, cfg, style=style, era="2024").draw()
            name = "%s_%s_%s.%s" % (mode, "eta" if mode == "vs_pt" else "pt", tag(lo, hi), plotter.STYLES[style]["format"])
            plotter.save(canv.canv, outdir / name)
            n += 1
    plot_multi_eta(config, h, lepton, title, eta_t, style, outdir)
    n += 1
    print("%s: %d plots in %s" % (config, n, outdir))


def plot_multi_eta(config, h, lepton, title, eta_t, style, outdir):
    """V3 'multi_eta' plot (MeasTrigEff/python/plotMuIDEff.py): data efficiency vs pT for
    every eta bin (top) and the SF vs pT for every eta bin (bottom), linear pT axis."""
    ax, ay = h["sf"].GetXaxis(), h["sf"].GetYaxis()
    top, bottom, sfpts = [], [], []
    # colour by |eta| bin, filled markers for eta > 0 and open markers for eta < 0
    abs_bins = sorted({round(abs(0.5 * (ax.GetBinLowEdge(i) + ax.GetBinUpEdge(i))), 4) for i in range(1, ax.GetNbins() + 1)})
    for ix in range(1, ax.GetNbins() + 1):
        cells = [(ix, iy) for iy in range(1, ay.GetNbins() + 1) if h["sf"].GetBinContent(ix, iy) > 0]
        if not cells:
            continue  # ECAL gap
        centre = 0.5 * (ax.GetBinLowEdge(ix) + ax.GetBinUpEdge(ix))
        col = plotter.PALETTE_LONG[abs_bins.index(round(abs(centre), 4)) % len(plotter.PALETTE_LONG)]
        marker = ROOT.kOpenCircle if centre < 0 else ROOT.kFullCircle
        pts = {key: [(ay.GetBinLowEdge(c[1]), ay.GetBinUpEdge(c[1]), h[key].GetBinContent(*c), h[key].GetBinError(*c)) for c in cells] for key in ("data", "sf")}
        lab = "%.3f < %s < %.3f" % (ax.GetBinLowEdge(ix), eta_t, ax.GetBinUpEdge(ix))
        top.append((lab, graph(pts["data"]), col, marker))
        bottom.append((lab, graph(pts["sf"]), col, marker))
        sfpts += pts["sf"]
    rlo, rhi = min(v - e for _, _, v, e in sfpts), max(v + e for _, _, v, e in sfpts)
    pad = max(0.15 * (rhi - rlo), 0.01)
    rr = (math.floor((rlo - pad) * 50.) / 50., math.ceil((max(rhi, 1.) + pad) * 50.) / 50.)
    # legend: one row per |eta| bin, eta < 0 in the left column (increasing eta), its
    # mirror bin in the right column; a bin across eta = 0 (filled marker) gets a row of its
    # own in the right column, so the left column holds only the open (eta < 0) markers
    centres = [0.5 * (float(lab.split(" < ")[0]) + float(lab.split(" < ")[-1])) for lab, *_ in top]
    neg = [i for i, c in enumerate(centres) if c < -1e-6]
    order = []
    for i in neg:
        mirror = [j for j, c in enumerate(centres) if abs(c + centres[i]) < 1e-4]
        order += [i, mirror[0] if mirror else None]
    order += [x for i, c in enumerate(centres) if abs(c) < 1e-6 for x in (None, i)]
    order += [i for i in range(len(top)) if i not in order]
    nrow = (len(order) + 1) // 2
    cfg = {"xRange": (ay.GetXmin(), ay.GetXmax()), "xTitle": "p_{T} [GeV]", "yTitle": "Efficiency", "rTitle": "Scale Factor",
           "yRange": (0., 1.2), "rRange": rr, "logx": False, "caption": [title], "captionPos": (0.50, 0.86),
           "legend": (0.30, 0.10, 0.93, 0.10 + 0.05 * (nrow + 1)), "legend_columns": 2, "legend_header": "Data Efficiency",
           "legend_text": 0.032, "no_rlegend": True, "legend_order": order}
    canv = plotter.EffCanvas(top, bottom, cfg, style=style, era="2024").draw()
    plotter.save(canv.canv, outdir / ("vs_pt_multi_eta.%s" % plotter.STYLES[style]["format"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--configs", default="")
    args = ap.parse_args()
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    for c in TITLES:
        if (not args.configs or c in args.configs.split(",")) and (D / c / "efficiency.root").exists():
            plot_config(c, args.style)
