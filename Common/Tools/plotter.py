"""Shared plotting library for the 2024 HcToWA analysis (docs/PLAN_Plotting.md).

Styles (one argument everywhere, ``--style {an,pw}``):
  an  "CMS" + "Work in progress" ("Simulation Work in progress" when no data is
      drawn), PNG, <module>/plots/AN/<era>/<channel>/<lane>/<key>.png
  pw  "Private work (CMS data)" / "(CMS simulation)", PDF,
      <module>/plots/PW/<era>/<channel>/<key>.pdf

Whether a plot is "data" or "simulation" is decided by the canvas (a data
histogram drawn or not); scripts never set label text. The cmsstyle globals are
set for every canvas and restored afterwards, so nothing leaks between plots.

Canvases: StackCanvas (data vs stacked prediction, band, ratio, optional signal
lines), ShapeCanvas (overlaid shapes, optional ratio to the first), Map2DCanvas.

Importing has no side effects; cmsstyle's style is applied when the first canvas
is built. The layout constants follow the V3 standard (V3 CLAUDE.md, "Plotting
Style"), with the logy bug of V3's ComparisonCanvas fixed.
"""
import json
import os
from pathlib import Path

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config" / "plotting"

# ---------------------------------------------------------------------------
# Constants (V3 standard)
PALETTE_LONG = ["#3f90da", "#ffa90e", "#bd1f01", "#94a4a2", "#832db6",
                "#a96b59", "#e76300", "#b9ac70", "#717581", "#92dadd"]
SIGNAL_COLORS = ["#d81b60", "#2ca02c", "#000000", "#0099b4"]
LEGEND_BOX = (0.650, 0.545, 0.970, 0.870)
LEGEND_TEXT = 0.036
SIGNAL_LEGEND_BOX = (0.650, 0.270, 0.970, 0.515)
SIGNAL_LEGEND_TEXT = 0.034
CAPTION_POS = (0.22, 0.75)
CAPTION_SIZE = 0.063
RATIO_TITLE = "Data / Pred."
BAND_LABEL = "Stat.+Syst."
HEADROOM = 1.6
HEADROOM_ETA = 1.4

STYLES = {
    "an": {"format": "png", "dir": "AN", "lanes_in_path": True},
    "pw": {"format": "pdf", "dir": "PW", "lanes_in_path": False},
}

_CMS = None


def cms():
    """cmsstyle, imported and applied on first use."""
    global _CMS
    if _CMS is None:
        import cmsstyle
        cmsstyle.setCMSStyle()
        _CMS = cmsstyle
    return _CMS


def color(hexstr):
    return ROOT.TColor.GetColor(hexstr)


def load_json(name):
    with open(CONFIG / name) as f:
        return json.load(f)


def era_info(era):
    eras = load_json("eras.json")
    if era not in eras:
        raise KeyError(f"era {era} not in {CONFIG / 'eras.json'}; known: {[e for e in eras if not e.startswith('_')]}")
    return eras[era]


# ---------------------------------------------------------------------------
# Labels
class _Label:
    """Sets cmsstyle's label and header globals for one canvas, restores them after."""

    def __init__(self, style, era, has_data, show_lumi=True):
        if style not in STYLES:
            raise ValueError(f"style must be one of {list(STYLES)}, got {style}")
        self.style, self.has_data = style, has_data
        info = era_info(era)
        self.lumi = info["lumi_fb"] if show_lumi else None
        self.energy = info["energy_TeV"]

    def __enter__(self):
        CMS = cms()
        if self.style == "an":
            CMS.SetCmsText("CMS", font=61, size=0.75)
            CMS.SetExtraText("Work in progress" if self.has_data else "Simulation Work in progress")
        else:
            what = "data" if self.has_data else "simulation"
            CMS.SetCmsText(f"Private work (CMS {what})", font=52, size=0.75 * 0.76)
            CMS.SetExtraText("")
        CMS.SetEnergy(self.energy)
        CMS.SetLumi(self.lumi, run="", round_lumi=1)
        return self

    def __exit__(self, *exc):
        CMS = cms()
        CMS.SetCmsText("CMS", font=61, size=0.75)
        CMS.SetExtraText("Preliminary")
        return False


def draw_caption(lines, pos=CAPTION_POS, size=CAPTION_SIZE):
    """Caption under the label: first line bold if more than one line is given."""
    CMS = cms()
    x, y = pos
    for i, text in enumerate(lines):
        font = 62 if (len(lines) > 1 and i == 0) else 42
        CMS.drawText(text, posX=x, posY=y - i * 1.15 * size, font=font, align=13, size=size)


# ---------------------------------------------------------------------------
# Histogram helpers
def prepare(hist, cfg):
    """Rebin (int or variable edges), restrict to xRange and fold the flow bins in."""
    h = hist.Clone(hist.GetName() + "_prep")
    h.SetDirectory(0)
    rebin = cfg.get("rebin")
    if isinstance(rebin, (list, tuple)):
        import array
        edges = array.array("d", rebin)
        h = h.Rebin(len(edges) - 1, h.GetName() + "_rb", edges)
    elif rebin and rebin > 1:
        h.Rebin(int(rebin))
    xr = cfg.get("xRange")
    if xr:
        lo = h.FindBin(xr[0] + 1e-9)
        hi = h.FindBin(xr[1] - 1e-9)
        edges = [h.GetXaxis().GetBinLowEdge(i) for i in range(lo, hi + 2)]
        import array
        out = ROOT.TH1D(h.GetName() + "_cut", h.GetTitle(), len(edges) - 1, array.array("d", edges))
        out.SetDirectory(0)
        out.Sumw2()
        for i in range(lo, hi + 1):
            out.SetBinContent(i - lo + 1, h.GetBinContent(i))
            out.SetBinError(i - lo + 1, h.GetBinError(i))
        if cfg.get("overflow", False):
            under = sum(h.GetBinContent(i) for i in range(0, lo))
            under_e = sum(h.GetBinError(i) ** 2 for i in range(0, lo))
            over = sum(h.GetBinContent(i) for i in range(hi + 1, h.GetNbinsX() + 2))
            over_e = sum(h.GetBinError(i) ** 2 for i in range(hi + 1, h.GetNbinsX() + 2))
            n = out.GetNbinsX()
            out.SetBinContent(1, out.GetBinContent(1) + under)
            out.SetBinError(1, (out.GetBinError(1) ** 2 + under_e) ** 0.5)
            out.SetBinContent(n, out.GetBinContent(n) + over)
            out.SetBinError(n, (out.GetBinError(n) ** 2 + over_e) ** 0.5)
        h = out
    return h


def y_title(cfg, hist):
    """'Events / <width> <unit>' for equal-width bins, 'Events / bin' otherwise."""
    if cfg.get("yTitle"):
        return cfg["yTitle"]
    if cfg.get("normalize"):
        return "Normalized"
    ax = hist.GetXaxis()
    widths = {round(ax.GetBinWidth(i), 6) for i in range(1, ax.GetNbins() + 1)}
    xt = cfg.get("xTitle", "")
    if xt.startswith("N_{") or xt.startswith("Number"):
        return "Events"
    if len(widths) != 1:
        return "Events / bin"
    w = widths.pop()
    unit = " GeV" if xt.endswith("[GeV]") else (" cm" if xt.endswith("[cm]") else "")
    return f"Events / {w:g}{unit}"


def ratio_hist(num, den, name):
    r = num.Clone(name)
    r.SetDirectory(0)
    for i in range(1, r.GetNbinsX() + 1):
        d = den.GetBinContent(i)
        r.SetBinContent(i, num.GetBinContent(i) / d if d > 0 else 0.)
        r.SetBinError(i, num.GetBinError(i) / d if d > 0 else 0.)
    return r


def ratio_band(den, name):
    b = den.Clone(name)
    b.SetDirectory(0)
    for i in range(1, b.GetNbinsX() + 1):
        d = den.GetBinContent(i)
        b.SetBinContent(i, 1. if d > 0 else 0.)
        b.SetBinError(i, den.GetBinError(i) / d if d > 0 else 0.)
    return b


def _equal_width(h):
    ax = h.GetXaxis()
    w = [ax.GetBinWidth(i) for i in range(1, ax.GetNbins() + 1)]
    return max(w) - min(w) < 1e-6 * max(w)


def _log_range(hmax, hmin_pos, cfg):
    lo = hmin_pos * 0.5 if hmin_pos > 0 else 1e-2
    import math
    decades = math.log10(hmax / lo) if hmax > lo else 1.
    return lo, hmax * 10 ** (0.6 * decades + 0.5)


def _min_positive(*hists):
    vals = [h.GetBinContent(i) for h in hists for i in range(1, h.GetNbinsX() + 1) if h.GetBinContent(i) > 0]
    return min(vals) if vals else 0.


# ---------------------------------------------------------------------------
class StackCanvas:
    """Data vs stacked prediction with an uncertainty band and a ratio pad.

    data:    TH1 or None (None: no data points, simulation label, no ratio)
    stack:   list of (label, TH1, hex colour), bottom to top
    band:    TH1 in the drawn binning (already prepared with cfg) whose bin errors are
             the total uncertainty (contents ignored); default: the stack sum with
             its statistical errors
    signals: list of (label, TH1), drawn as lines
    cfg:     xTitle, yTitle, xRange, rebin, rRange, logy, yRange, yHeadroom, eta,
             caption (list of lines), overflow; optional dataLabel (legend label of the points,
             default "Data"), hasData (label choice, default: points drawn), rTitle (ratio axis)
    """

    def __init__(self, data, stack, cfg, style="an", era="2024", band=None, signals=None):
        self.cfg, self.style, self.era = cfg, style, era
        self.data = prepare(data, cfg) if data is not None else None
        self.stack = [(lab, prepare(h, cfg), col) for lab, h, col in stack]
        self.total = self.stack[0][1].Clone("total")
        self.total.SetDirectory(0)
        for _, h, _ in self.stack[1:]:
            self.total.Add(h)
        self.has_syst = band is not None
        if band is not None:
            # band is already in the drawn binning (histutils.band(..., prepare=...)):
            # the envelope must be taken after rebinning, not before.
            b = band
            if b.GetNbinsX() != self.total.GetNbinsX():
                raise ValueError(f"band has {b.GetNbinsX()} bins, the stack {self.total.GetNbinsX()}")
            for i in range(0, self.total.GetNbinsX() + 2):
                self.total.SetBinError(i, b.GetBinError(i))
        self.signals = [(lab, prepare(h, cfg)) for lab, h in (signals or [])]

    def draw(self):
        CMS, cfg = cms(), self.cfg
        with_ratio = self.data is not None and not cfg.get("no_ratio", False)
        hists = [self.total] + ([self.data] if self.data else []) + [h for _, h in self.signals]
        hmax = max(h.GetMaximum() for h in hists)
        if cfg.get("logy"):
            ymin, ymax = cfg.get("yRange") or _log_range(hmax, _min_positive(*hists), cfg)
        else:
            ymin, ymax = cfg.get("yRange") or (0., hmax * cfg.get("yHeadroom", HEADROOM_ETA if cfg.get("eta") else HEADROOM))
        ax = self.total.GetXaxis()
        xmin, xmax = ax.GetXmin(), ax.GetXmax()
        ytitle = y_title(cfg, self.total)
        with _Label(self.style, self.era, cfg.get("hasData", self.data is not None)):
            if with_ratio:
                rmin, rmax = cfg.get("rRange", [0.5, 1.5])
                self.canv = CMS.cmsDiCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax, rmin, rmax,
                                            cfg.get("xTitle", ""), ytitle, cfg.get("rTitle", RATIO_TITLE),
                                            square=True, iPos=11)
                self.pad = self.canv.cd(1)
            else:
                self.canv = CMS.cmsCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax,
                                          cfg.get("xTitle", ""), ytitle, square=True, iPos=11)
                self.pad = self.canv.cd()
        if cfg.get("logy"):
            self.pad.SetLogy()
        CMS.GetCmsCanvasHist(self.pad).GetYaxis().SetMaxDigits(3)

        self.leg = CMS.cmsLeg(*LEGEND_BOX, textSize=LEGEND_TEXT)
        hs = ROOT.THStack(f"hs_{id(self)}", "")
        for _, h, col in self.stack:
            h.SetFillColor(color(col))
            h.SetLineColor(color(col))
            h.SetLineWidth(0)
            hs.Add(h)
        self._keep = [hs]
        hs.Draw("HIST SAME")
        CMS.cmsObjectDraw(self.total, "E2", FillStyle=3004, FillColor=12, LineWidth=0, MarkerSize=0)
        x0 = "PE X0" if _equal_width(self.total) else "PE"
        if self.data is not None:
            CMS.cmsObjectDraw(self.data, x0, MarkerStyle=ROOT.kFullCircle, MarkerSize=1.0, MarkerColor=1, LineColor=1)
            CMS.addToLegend(self.leg, (self.data, cfg.get("dataLabel", "Data"), "PE" if "X0" in x0 else "PLE"))
        for lab, h, _ in reversed(self.stack):
            CMS.addToLegend(self.leg, (h, lab, "F"))
        # stat (+) syst only when a systematic band was given; otherwise MC statistics
        CMS.addToLegend(self.leg, (self.total, cfg.get("bandLabel", BAND_LABEL if self.has_syst else "Stat."), "F"))
        if self.signals:
            sleg = CMS.cmsLeg(*SIGNAL_LEGEND_BOX, textSize=SIGNAL_LEGEND_TEXT)
            if cfg.get("signalHeader"):
                sleg.SetHeader(cfg["signalHeader"], "")
            for i, (lab, h) in enumerate(self.signals):
                CMS.cmsObjectDraw(h, "HIST", LineColor=color(SIGNAL_COLORS[i % 4]), LineWidth=3, FillStyle=0)
                CMS.addToLegend(sleg, (h, lab, "L"))
            self._keep.append(sleg)
        if cfg.get("caption"):
            draw_caption(cfg["caption"])
        self.pad.RedrawAxis()

        if with_ratio:
            self.canv.cd(2)
            self.rband = ratio_band(self.total, f"rb_{id(self)}")
            self.ratio = ratio_hist(self.data, self.total, f"r_{id(self)}")
            CMS.cmsObjectDraw(self.rband, "E2", FillStyle=3004, FillColor=12, LineWidth=0, MarkerSize=0)
            CMS.cmsObjectDraw(self.ratio, x0, MarkerStyle=ROOT.kFullCircle, MarkerSize=1.0, MarkerColor=1, LineColor=1)
            line = ROOT.TLine(xmin, 1., xmax, 1.)
            line.SetLineStyle(ROOT.kDotted)
            line.Draw()
            self._keep.append(line)
            self.canv.cd(2).RedrawAxis()
        return self

    def save(self, path):
        save(self.canv, path)


class ShapeCanvas:
    """Overlaid histograms (normalized to unit area if cfg['normalize']), ratio to the first.

    curves: list of (label, TH1, hex colour, kind) with kind 'data' (points) or 'line'.
    has_data: label choice; default True if any curve is of kind 'data'.
    """

    def __init__(self, curves, cfg, style="an", era="2024", has_data=None):
        self.cfg, self.style, self.era = cfg, style, era
        self.curves = []
        for lab, h, col, kind in curves:
            p = prepare(h, cfg)
            if cfg.get("normalize") and p.Integral() > 0:
                p.Scale(1. / p.Integral())
            self.curves.append((lab, p, col, kind))
        self.has_data = any(k == "data" for *_, k in curves) if has_data is None else has_data

    def draw(self):
        CMS, cfg = cms(), self.cfg
        hs = [h for _, h, _, _ in self.curves]
        hmax = max(h.GetMaximum() for h in hs)
        if cfg.get("logy"):
            ymin, ymax = cfg.get("yRange") or _log_range(hmax, _min_positive(*hs), cfg)
        else:
            ymin, ymax = cfg.get("yRange") or (0., hmax * cfg.get("yHeadroom", HEADROOM))
        ax = hs[0].GetXaxis()
        xmin, xmax = ax.GetXmin(), ax.GetXmax()
        with_ratio = len(hs) > 1 and not cfg.get("no_ratio", False)
        with _Label(self.style, self.era, self.has_data, show_lumi=not cfg.get("normalize")):
            if with_ratio:
                rmin, rmax = cfg.get("rRange", [0.8, 1.2])
                self.canv = CMS.cmsDiCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax, rmin, rmax,
                                            cfg.get("xTitle", ""), y_title(cfg, hs[0]),
                                            cfg.get("rTitle", "Ratio"), square=True, iPos=11)
                self.pad = self.canv.cd(1)
            else:
                self.canv = CMS.cmsCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax,
                                          cfg.get("xTitle", ""), y_title(cfg, hs[0]), square=True, iPos=11)
                self.pad = self.canv.cd()
        if cfg.get("logy"):
            self.pad.SetLogy()
        x1, _, x2, y2 = cfg.get("legend", LEGEND_BOX)
        self.leg = CMS.cmsLeg(x1, y2 - 0.055 * len(self.curves), x2, y2, textSize=LEGEND_TEXT)
        for lab, h, col, kind in self.curves:
            c = color(col)
            if kind == "data":
                CMS.cmsObjectDraw(h, "PE X0" if _equal_width(h) else "PE", MarkerStyle=ROOT.kFullCircle,
                                  MarkerSize=0.9, MarkerColor=c, LineColor=c)
                CMS.addToLegend(self.leg, (h, lab, "PE"))
            else:
                CMS.cmsObjectDraw(h, "HIST", LineColor=c, LineWidth=2, FillStyle=0)
                CMS.addToLegend(self.leg, (h, lab, "L"))
        if cfg.get("caption"):
            draw_caption(cfg["caption"])
        if cfg.get("text"):
            for i, t in enumerate(cfg["text"]):
                x, y = cfg.get("textPos", (0.60, 0.72))
                CMS.drawText(t, posX=x, posY=y - i * 0.045, font=42, align=13, size=0.030)
        self.pad.RedrawAxis()
        self._keep = []
        if with_ratio:
            self.canv.cd(2)
            ref = hs[0]
            for lab, h, col, kind in self.curves[1:]:
                r = ratio_hist(h, ref, f"r_{id(h)}")
                c = color(col)
                CMS.cmsObjectDraw(r, "PE X0" if _equal_width(r) else "PE", MarkerStyle=ROOT.kFullCircle,
                                  MarkerSize=0.8, MarkerColor=c, LineColor=c)
                self._keep.append(r)
            line = ROOT.TLine(xmin, 1., xmax, 1.)
            line.SetLineStyle(ROOT.kDotted)
            line.Draw()
            self._keep.append(line)
        return self

    def save(self, path):
        save(self.canv, path)


class EffCanvas:
    """Efficiencies (top pad) and scale factors (bottom pad) vs one variable, drawn as points
    with x and y errors (TGraphAsymmErrors), in the style of the V3 efficiency plots.

    top, bottom: lists of (label, graph, hex colour, ROOT marker style).
    cfg: xTitle, yTitle ("Efficiency"), rTitle ("Data / MC"), xRange, yRange, rRange, logx,
    caption (list of lines), legend (x1, y1, x2, y2), legend_columns, legend_header, legend_text,
    legend_order (indices into top, row by row, None = blank cell), no_rlegend (no legend in the lower pad).
    """

    def __init__(self, top, bottom, cfg, style="an", era="2024", has_data=True):
        self.top, self.bottom, self.cfg, self.style, self.era, self.has_data = top, bottom, cfg, style, era, has_data

    def draw(self):
        CMS, cfg = cms(), self.cfg
        xmin, xmax = cfg["xRange"]
        ymin, ymax = cfg.get("yRange", (0., 1.2))
        rmin, rmax = cfg.get("rRange", (0.8, 1.2))
        with _Label(self.style, self.era, self.has_data, show_lumi=True):
            self.canv = CMS.cmsDiCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax, rmin, rmax,
                                        cfg.get("xTitle", ""), cfg.get("yTitle", "Efficiency"),
                                        cfg.get("rTitle", "Data / MC"), square=True, iPos=11)
        pads = [self.canv.cd(1), self.canv.cd(2)]
        if cfg.get("logx"):
            for p in pads:
                p.SetLogx()
                frame = CMS.GetCmsCanvasHist(p)
                frame.GetXaxis().SetMoreLogLabels()
                frame.GetXaxis().SetNoExponent()
                p.Update()
        self.canv.cd(1)
        x1, y1, x2, y2 = cfg.get("legend", (0.45, 0.62, 0.92, 0.88))
        self.leg = CMS.cmsLeg(x1, y1, x2, y2, textSize=cfg.get("legend_text", LEGEND_TEXT), columns=cfg.get("legend_columns", 1))
        if cfg.get("legend_header"):
            self.leg.SetHeader(cfg["legend_header"])
        for lab, g, col, marker in self.top:
            c = color(col)
            g.SetMarkerStyle(marker)
            g.SetMarkerSize(1.0)
            g.SetMarkerColor(c)
            g.SetLineColor(c)
            g.Draw("PZ SAME")
            if "legend_order" not in cfg:
                self.leg.AddEntry(g, lab, "PE")
        # legend_order: indices into `top` in legend order (filled row by row), None = blank cell
        self._blank = []
        for i in cfg.get("legend_order", []):
            if i is None:
                self._blank.append(ROOT.TObject())
                self.leg.AddEntry(self._blank[-1], " ", "")
            else:
                self.leg.AddEntry(self.top[i][1], self.top[i][0], "PE")
        if cfg.get("caption"):
            draw_caption(cfg["caption"], pos=cfg.get("captionPos", (0.17, 0.74)), size=0.035)
        pads[0].RedrawAxis()
        self.canv.cd(2)
        line = ROOT.TLine(xmin, 1., xmax, 1.)
        line.SetLineStyle(ROOT.kDotted)
        line.Draw()
        self._keep = [line]
        for lab, g, col, marker in self.bottom:
            c = color(col)
            g.SetMarkerStyle(marker)
            g.SetMarkerSize(0.9)
            g.SetMarkerColor(c)
            g.SetLineColor(c)
            g.Draw("PZ SAME")
        if len(self.bottom) > 1 and not cfg.get("no_rlegend"):
            self.rleg = ROOT.TLegend(0.17, 0.80, 0.70, 0.95)
            self.rleg.SetNColumns(len(self.bottom))
            self.rleg.SetBorderSize(0)
            self.rleg.SetFillStyle(0)
            self.rleg.SetTextSize(0.075)
            for lab, g, _, _ in self.bottom:
                self.rleg.AddEntry(g, lab, "PE")
            self.rleg.Draw()
        pads[1].RedrawAxis()
        return self

    def save(self, path):
        save(self.canv, path)


class Map2DCanvas:
    """2D map (e.g. jet eta-phi), colour axis on the right."""

    def __init__(self, hist, cfg, style="an", era="2024", has_data=True):
        self.h, self.cfg, self.style, self.era, self.has_data = hist, cfg, style, era, has_data

    def draw(self):
        CMS, cfg, h = cms(), self.cfg, self.h
        if cfg.get("rebin"):
            h = h.Clone(h.GetName() + "_rb")
            h.Rebin2D(*cfg["rebin"])
        self.h = h
        ax, ay = h.GetXaxis(), h.GetYaxis()
        with _Label(self.style, self.era, self.has_data, show_lumi=cfg.get("show_lumi", True)):
            # "yRange" overrides the frame (e.g. room above the map for the caption)
            y0, y1 = cfg.get("yRange", (ay.GetXmin(), ay.GetXmax()))
            self.canv = CMS.cmsCanvas(f"c_{id(self)}", ax.GetXmin(), ax.GetXmax(), y0, y1,
                                      cfg.get("xTitle", ""), cfg.get("yTitle", ""), square=True, iPos=0,
                                      with_z_axis=True, scaleLumi=0.75)
        h.GetZaxis().SetTitle(cfg.get("zTitle", "Jets"))
        h.GetZaxis().SetMaxDigits(3)
        if cfg.get("logz"):
            self.canv.SetLogz()
        if cfg.get("logx"):
            self.canv.SetLogx()
        if cfg.get("logy"):
            self.canv.SetLogy()
            frame = CMS.GetCmsCanvasHist(self.canv)
            frame.GetYaxis().SetMoreLogLabels()
            frame.GetYaxis().SetNoExponent()
            # log labels (e.g. 300, 400) are wider than the default exponent labels
            frame.GetYaxis().SetTitleOffset(frame.GetYaxis().GetTitleOffset() * 1.08)
        if cfg.get("zRange"):
            h.SetMinimum(cfg["zRange"][0])
            h.SetMaximum(cfg["zRange"][1])
        CMS.SetCMSPalette()
        if cfg.get("text"):
            # cell values (and errors with "text_errors") printed on the map, e.g. text="4.3f"
            import ROOT
            ROOT.gStyle.SetPaintTextFormat(cfg["text"])
            h.SetMarkerSize(cfg.get("text_size", 0.6))
            h.Draw("COLZ TEXTE SAME" if cfg.get("text_errors") else "COLZ TEXT SAME")
        else:
            h.Draw("COLZ SAME")
        rm = self.canv.GetRightMargin()
        CMS.UpdatePalettePosition(h, self.canv, X1=1 - rm * 0.95, X2=1 - rm * 0.80)
        h.GetZaxis().SetLabelSize(0.035)
        h.GetZaxis().SetTitleSize(0.040)
        h.GetZaxis().SetTitleOffset(cfg.get("zTitleOffset", 1.15))
        if cfg.get("caption"):
            draw_caption(cfg["caption"], pos=(0.16, 0.87), size=0.035)
        self.canv.RedrawAxis()
        return self

    def save(self, path):
        save(self.canv, path)


# ---------------------------------------------------------------------------
def plot_dir(module, style, era):
    """<module>/plots/<AN|PW>/<era>: every module keeps its own plots (V3 layout)."""
    return REPO / module / "plots" / STYLES[style]["dir"] / era


def output_path(style, era, module, channel, key, lane="Central"):
    """<module>/plots/AN/<era>/<channel>/<lane>/<key>.png or <module>/plots/PW/<era>/<channel>/<key>.pdf"""
    s = STYLES[style]
    parts = [plot_dir(module, style, era), channel]
    if s["lanes_in_path"]:
        parts.append(lane)
    return Path(*map(str, parts)) / f"{key.replace('/', '_')}.{s['format']}"


def save(canv, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    canv.SaveAs(str(path))
    canv.Close()
