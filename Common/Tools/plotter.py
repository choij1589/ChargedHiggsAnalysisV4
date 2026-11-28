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
lines), ShapeCanvas (overlaid shapes, optional ratio to the first), EffCanvas,
GraphCanvas (bands, lines and points vs one variable, e.g. expected limits or
fitted parameters vs mass, optional lower pad), ImpactCanvas (nuisance impacts on
the POI), Map2DCanvas.

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


TEXT_SIZE = 0.030


def _draw_text(cfg):
    """cfg['text']: free text lines (font 42) at cfg['textPos'] (NDC, top-left aligned), size cfg['textSize']."""
    lines = cfg.get("text") or []
    x, y = cfg.get("textPos", (0.60, 0.72))
    size = cfg.get("textSize", TEXT_SIZE)
    for i, t in enumerate(lines):
        cms().drawText(t, posX=x, posY=y - i * 1.5 * size, font=42, align=13, size=size)


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
    cfg:     xTitle, yTitle, xRange, rebin, rRange, logy, yRange, yHeadroom, eta, vlines (x of dashed lines),
             text, textPos, textSize (free text lines), signalLegend (box of the signal legend),
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
            sleg = CMS.cmsLeg(*cfg.get("signalLegend", SIGNAL_LEGEND_BOX), textSize=SIGNAL_LEGEND_TEXT)
            if cfg.get("signalHeader"):
                sleg.SetHeader(cfg["signalHeader"], "")
            for i, (lab, h) in enumerate(self.signals):
                CMS.cmsObjectDraw(h, "HIST", LineColor=color(SIGNAL_COLORS[i % 4]), LineWidth=3, FillStyle=0)
                CMS.addToLegend(sleg, (h, lab, "L"))
            self._keep.append(sleg)
        if cfg.get("caption"):
            draw_caption(cfg["caption"])
        # vlines: x positions of dashed vertical lines (e.g. template bin boundaries)
        for x in cfg.get("vlines", []):
            ln = ROOT.TLine(x, ymin, x, ymax)
            CMS.cmsDrawLine(ln, lcolor=color("#717581"), lstyle=ROOT.kDashed, lwidth=2)
            self._keep.append(ln)
        _draw_text(cfg)
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
    legend_order (indices into top, row by row, None = blank cell), no_rlegend (no legend in the lower pad),
    no_ratio (one pad, `bottom` ignored; e.g. MC-only efficiencies; yTitleOffset widens the left margin for
    long y labels), show_lumi (default True).
    """

    def __init__(self, top, bottom, cfg, style="an", era="2024", has_data=True):
        self.top, self.bottom, self.cfg, self.style, self.era, self.has_data = top, bottom, cfg, style, era, has_data

    def draw(self):
        CMS, cfg = cms(), self.cfg
        xmin, xmax = cfg["xRange"]
        ymin, ymax = cfg.get("yRange", (0., 1.2))
        rmin, rmax = cfg.get("rRange", (0.8, 1.2))
        single = cfg.get("no_ratio", False)
        with _Label(self.style, self.era, self.has_data, show_lumi=cfg.get("show_lumi", True)):
            if single:
                self.canv = CMS.cmsCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax, cfg.get("xTitle", ""),
                                          cfg.get("yTitle", "Efficiency"), square=True, iPos=11,
                                          yTitOffset=cfg.get("yTitleOffset"))
            else:
                self.canv = CMS.cmsDiCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax, rmin, rmax,
                                            cfg.get("xTitle", ""), cfg.get("yTitle", "Efficiency"),
                                            cfg.get("rTitle", "Data / MC"), square=True, iPos=11)
        pads = [self.canv.cd()] if single else [self.canv.cd(1), self.canv.cd(2)]
        if cfg.get("logx"):
            for p in pads:
                p.SetLogx()
                frame = CMS.GetCmsCanvasHist(p)
                frame.GetXaxis().SetMoreLogLabels()
                frame.GetXaxis().SetNoExponent()
                p.Update()
        pads[0].cd()
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
        if single:
            self._keep = []
            return self
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


LIMIT_68 = "#85D1FB"   # CMS expected-limit bands, CMS-logo set (cmsstyle kLimit68cms / kLimit95cms; user 2026-11-28)
LIMIT_95 = "#FFDF7F"


def _graph_points(g):
    """(x, y, ey_lo, ey_hi) lists of a TGraph / TGraphErrors / TGraphAsymmErrors."""
    out = []
    for i in range(g.GetN()):
        lo = g.GetErrorYlow(i) if hasattr(g, "GetErrorYlow") else 0.
        hi = g.GetErrorYhigh(i) if hasattr(g, "GetErrorYhigh") else 0.
        out.append((g.GetPointX(i), g.GetPointY(i), max(lo, 0.), max(hi, 0.)))
    return out


class GraphCanvas:
    """Graphs vs one variable (limits vs mass, fitted parameters vs mass, residuals), with an
    optional lower pad.

    top, bottom: lists of items, dicts with
      obj    TGraph / TGraphErrors / TGraphAsymmErrors
      kind   'band' (filled area between the y errors), 'line', 'points' (markers with error bars),
             'markers' (markers without error bars)
      color  hex colour; label: legend text (None or missing: not in the legend)
      optional: style (line style), width (line width), marker (ROOT marker), size (marker size),
                alpha (fill alpha of a band)
    Items are drawn in list order (bands first, lines on top); the legend follows `legend_order`
    (indices into `top`) when given, else the list order.
    cfg: xTitle, yTitle, xRange (default: span of the graphs), yRange, logy, yHeadroom (linear, 1.6),
         rTitle, rRange (lower pad), legend (x1, y1, x2, y2), legend_text, legend_columns,
         legend_header, legend_order, caption (lines), captionPos, captionSize, text (lines),
         textPos, textSize, hlines / rlines (y of dotted horizontal lines in the upper / lower pad),
         vlines (x of dotted vertical lines in both pads), show_lumi (default True)
    has_data: label choice (True: "Work in progress", False: "Simulation Work in progress").
    """

    def __init__(self, top, cfg, style="an", era="2024", has_data=True, bottom=None):
        self.top, self.bottom, self.cfg = top, bottom or [], cfg
        self.style, self.era, self.has_data = style, era, has_data

    def _ranges(self):
        cfg = self.cfg
        pts = [p for it in self.top for p in _graph_points(it["obj"])]
        if cfg.get("xRange"):
            xmin, xmax = cfg["xRange"]
        else:
            xs = [p[0] for p in pts]
            xmin, xmax = min(xs), max(xs)
        inx = [p for p in pts if xmin <= p[0] <= xmax] or pts
        if cfg.get("yRange"):
            ymin, ymax = cfg["yRange"]
        elif cfg.get("logy"):
            hmax = max(p[1] + p[3] for p in inx)
            pos = [p[1] - p[2] for p in inx if p[1] - p[2] > 0] or [p[1] for p in inx if p[1] > 0]
            ymin, ymax = _log_range(hmax, min(pos) if pos else 0., cfg)
        else:
            hi = max(p[1] + p[3] for p in inx)
            lo = min(p[1] - p[2] for p in inx)
            ymin = min(0., lo) if lo >= 0 else lo - 0.1 * (hi - lo)
            ymax = ymin + (hi - ymin) * cfg.get("yHeadroom", HEADROOM)
        return xmin, xmax, ymin, ymax

    @staticmethod
    def _draw_item(it):
        g, c = it["obj"], color(it.get("color", "#000000"))
        kind = it.get("kind", "line")
        if kind == "band":
            if it.get("alpha"):
                g.SetFillColorAlpha(c, it["alpha"])
            else:
                g.SetFillColor(c)
            g.SetFillStyle(it.get("fill", 1001))
            g.SetLineColor(c)
            g.SetLineWidth(0)
            g.Draw("3 SAME")
            return "F"
        g.SetLineColor(c)
        g.SetMarkerColor(c)
        g.SetLineStyle(it.get("style", ROOT.kSolid))
        g.SetLineWidth(it.get("width", 2))
        if kind == "line":
            g.Draw("LX SAME")
            return "L"
        g.SetMarkerStyle(it.get("marker", ROOT.kFullCircle))
        g.SetMarkerSize(it.get("size", 1.0))
        if kind == "markers":
            g.Draw("PX SAME")
            return "P"
        g.Draw("PZ SAME")
        return "PE"

    def draw(self):
        CMS, cfg = cms(), self.cfg
        xmin, xmax, ymin, ymax = self._ranges()
        with _Label(self.style, self.era, self.has_data, show_lumi=cfg.get("show_lumi", True)):
            if self.bottom:
                rmin, rmax = cfg.get("rRange", (-3., 3.))
                self.canv = CMS.cmsDiCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax, rmin, rmax,
                                            cfg.get("xTitle", ""), cfg.get("yTitle", ""),
                                            cfg.get("rTitle", "Pull"), square=True, iPos=11)
                self.pad = self.canv.cd(1)
            else:
                self.canv = CMS.cmsCanvas(f"c_{id(self)}", xmin, xmax, ymin, ymax,
                                          cfg.get("xTitle", ""), cfg.get("yTitle", ""), square=True, iPos=11)
                self.pad = self.canv.cd()
        if cfg.get("logy"):
            self.pad.SetLogy()
        else:
            CMS.GetCmsCanvasHist(self.pad).GetYaxis().SetMaxDigits(3)
        self._keep = []
        for y in cfg.get("hlines", []):
            ln = ROOT.TLine(xmin, y, xmax, y)
            CMS.cmsDrawLine(ln, lcolor=ROOT.kGray + 2, lstyle=ROOT.kDotted, lwidth=2)
            self._keep.append(ln)
        for x in cfg.get("vlines", []):
            ln = ROOT.TLine(x, ymin, x, ymax)
            CMS.cmsDrawLine(ln, lcolor=ROOT.kGray + 2, lstyle=ROOT.kDotted, lwidth=2)
            self._keep.append(ln)
        opts = [self._draw_item(it) for it in self.top]
        x1, y1, x2, y2 = cfg.get("legend", (0.50, 0.70, 0.93, 0.89))
        self.leg = CMS.cmsLeg(x1, y1, x2, y2, textSize=cfg.get("legend_text", LEGEND_TEXT),
                              columns=cfg.get("legend_columns", 1))
        if cfg.get("legend_header"):
            self.leg.SetHeader(cfg["legend_header"], "")
        for i in cfg.get("legend_order", range(len(self.top))):
            it = self.top[i]
            if it.get("label"):
                self.leg.AddEntry(it["obj"], it["label"], opts[i])
        if cfg.get("caption"):
            draw_caption(cfg["caption"], pos=cfg.get("captionPos", (0.19, 0.86)),
                         size=cfg.get("captionSize", 0.040))
        _draw_text(cfg)
        self.pad.RedrawAxis()
        if self.bottom:
            pad2 = self.canv.cd(2)
            rmin, rmax = cfg.get("rRange", (-3., 3.))
            for y in cfg.get("rlines", [0.]):
                ln = ROOT.TLine(xmin, y, xmax, y)
                CMS.cmsDrawLine(ln, lcolor=ROOT.kGray + 2, lstyle=ROOT.kDotted, lwidth=2)
                self._keep.append(ln)
            for x in cfg.get("vlines", []):
                ln = ROOT.TLine(x, rmin, x, rmax)
                CMS.cmsDrawLine(ln, lcolor=ROOT.kGray + 2, lstyle=ROOT.kDotted, lwidth=2)
                self._keep.append(ln)
            for it in self.bottom:
                self._draw_item(it)
            pad2.RedrawAxis()
        return self

    def save(self, path):
        save(self.canv, path)


class ImpactCanvas:
    """Nuisance-parameter impacts on the POI (rows of a combineTool impacts.json), two panels:
    left the post-fit value (theta_hat - theta_0) / Delta theta with its post-fit uncertainty (for
    an Asimov fit the values are 0 and the bars show the constraint), right the impact Delta r of
    the +1 sigma and -1 sigma post-fit shifts. Names are drawn as plain text (no TLatex).

    rows: list of dicts {label, pull, err_lo, err_hi, d_up, d_dn}, drawn top to bottom.
    cfg:  caption (one line above the left panel), poi_text (one line above the right panel),
          pullRange (default 2), impactRange (symmetric half-width, default 1.15 x max |Delta r|),
          pullTitle, impactTitle
    """

    W, ROW, TOP, HEAD, BOTTOM = 1000, 26, 42, 44, 120   # pixels
    SPLIT, LEFT_M = 0.62, 0.60                           # left-pad width, its left margin (fractions)

    def __init__(self, rows, cfg, style="an", era="2024", has_data=True):
        self.rows, self.cfg, self.style, self.era, self.has_data = rows, cfg, style, era, has_data

    def draw(self):
        CMS, cfg, rows = cms(), self.cfg, self.rows
        n = len(rows)
        H = self.TOP + self.HEAD + n * self.ROW + self.BOTTOM
        self.canv = ROOT.TCanvas(f"c_{id(self)}", "", self.W, H)
        self.canv.SetFillColor(0)
        tm, bm = (self.TOP + self.HEAD) / H, self.BOTTOM / H
        self._keep = []
        left = ROOT.TPad(f"pl_{id(self)}", "", 0., 0., self.SPLIT, 1.)
        right = ROOT.TPad(f"pr_{id(self)}", "", self.SPLIT, 0., 1., 1.)
        for p, lm, rm in ((left, self.LEFT_M, 0.02), (right, 0.07, 0.07)):
            p.SetTopMargin(tm)
            p.SetBottomMargin(bm)
            p.SetLeftMargin(lm)
            p.SetRightMargin(rm)
            p.SetFillStyle(4000)
            p.SetFrameFillStyle(4000)
            self.canv.cd()
            p.Draw()
            self._keep.append(p)

        def frame(pad, x0, x1, title):
            pad.cd()
            fr = pad.DrawFrame(x0, 0., x1, float(n))
            ax, ay = fr.GetXaxis(), fr.GetYaxis()
            ay.SetLabelSize(0)
            ay.SetTickLength(0)
            ay.SetNdivisions(0)
            for a in (ax,):
                a.SetLabelFont(43)
                a.SetLabelSize(17)
                a.SetTitleFont(43)
                a.SetTitleSize(20)
                a.SetTitleOffset(1.5)
                a.CenterTitle()
                a.SetNdivisions(505)
                a.SetTickLength(10. / H)
            ax.SetTitle(title)
            return fr

        # zebra rows across both panels
        def zebra(x0, x1):
            for i in range(0, n, 2):
                b = ROOT.TBox(x0, n - i - 1, x1, n - i)
                b.SetFillColorAlpha(ROOT.kGray, 0.35)
                b.SetLineWidth(0)
                b.Draw()
                self._keep.append(b)

        pr = cfg.get("pullRange", 2.)
        frame(left, -pr, pr, cfg.get("pullTitle", "(#hat{#theta} - #theta_{0}) / #Delta#theta"))
        zebra(-pr, pr)
        for x in (-1., 0., 1.):
            ln = ROOT.TLine(x, 0., x, float(n))
            CMS.cmsDrawLine(ln, lcolor=ROOT.kGray + 2, lstyle=ROOT.kDotted if x else ROOT.kDashed, lwidth=2)
            self._keep.append(ln)
        g = ROOT.TGraphAsymmErrors(n)
        for i, r in enumerate(rows):
            y = n - i - 0.5
            g.SetPoint(i, r["pull"], y)
            g.SetPointError(i, r["err_lo"], r["err_hi"], 0., 0.)
            t = ROOT.TText(-pr - 0.04 * 2 * pr, y, r["label"])
            t.SetTextAlign(32)
            t.SetTextFont(43)
            t.SetTextSize(15)
            t.Draw()
            self._keep.append(t)
        g.SetMarkerStyle(ROOT.kFullCircle)
        g.SetMarkerSize(0.9)
        g.SetLineWidth(2)
        g.Draw("PZ SAME")
        self._keep.append(g)
        left.RedrawAxis()

        dmax = max([abs(r["d_up"]) for r in rows] + [abs(r["d_dn"]) for r in rows] + [1e-6])
        ir = cfg.get("impactRange", 1.15 * dmax)
        frame(right, -ir, ir, cfg.get("impactTitle", "#Delta#hat{r}"))
        zebra(-ir, ir)
        ln = ROOT.TLine(0., 0., 0., float(n))
        CMS.cmsDrawLine(ln, lcolor=ROOT.kGray + 2, lstyle=ROOT.kDashed, lwidth=2)
        self._keep.append(ln)
        up_c, dn_c = color(PALETTE_LONG[2]), color(PALETTE_LONG[0])
        boxes = {}
        for i, r in enumerate(rows):
            y = n - i - 0.5
            for key, c in (("d_up", up_c), ("d_dn", dn_c)):
                b = ROOT.TBox(min(0., r[key]), y - 0.32, max(0., r[key]), y + 0.32)
                b.SetFillColorAlpha(c, 0.80)
                b.SetLineColor(c)
                b.SetLineWidth(1)
                b.Draw()
                boxes.setdefault(key, b)
                self._keep.append(b)
        right.RedrawAxis()

        # overlay for the CMS label, header, captions and legend
        over = ROOT.TPad(f"po_{id(self)}", "", 0., 0., 1., 1.)
        over.SetFillStyle(4000)
        over.SetFrameFillStyle(4000)
        over.SetFrameLineWidth(0)
        over.SetTopMargin(self.TOP / H)
        over.SetBottomMargin(bm)
        over.SetLeftMargin(self.SPLIT * self.LEFT_M)
        over.SetRightMargin((1 - self.SPLIT) * 0.07)
        self.canv.cd()
        over.Draw()
        self._keep.append(over)
        with _Label(self.style, self.era, self.has_data, show_lumi=cfg.get("show_lumi", True)):
            CMS.CMS_lumi(over, iPosX=0)
        over.cd()
        yhead = 1. - (self.TOP + 0.45 * self.HEAD) / H
        for text, x, align in ((cfg.get("caption", ""), self.SPLIT * self.LEFT_M, 12),
                               (cfg.get("poi_text", ""), 1. - (1 - self.SPLIT) * 0.07, 32)):
            if text:
                lt = ROOT.TLatex(x, yhead, text)
                lt.SetNDC()
                lt.SetTextFont(43)
                lt.SetTextSize(19)
                lt.SetTextAlign(align)
                lt.Draw()
                self._keep.append(lt)
        self.leg = ROOT.TLegend(0.35, 8. / H, 0.95, 40. / H)
        self.leg.SetNColumns(3)
        self.leg.SetBorderSize(0)
        self.leg.SetFillStyle(0)
        self.leg.SetTextFont(43)
        self.leg.SetTextSize(18)
        self.leg.AddEntry(g, "Post-fit #hat{#theta} #pm #sigma", "PE")
        self.leg.AddEntry(boxes["d_up"], "+1#sigma impact", "F")
        self.leg.AddEntry(boxes["d_dn"], "#minus1#sigma impact", "F")
        self.leg.Draw()
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
