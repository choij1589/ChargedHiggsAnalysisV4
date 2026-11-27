"""Histogram loading, grouping and the uncertainty band for SKNano 2.0 outputs.

Layout: <SKNanoOutput>/<Analyzer>/<flags>/<era>/<sample>.root, histograms at
{channel}/{lane}/{histkey}. Data files are <PD>_<period>.root.

The band: for every systematic source, the up and down lanes are summed over
all samples (the source is correlated across samples), the per-bin envelope
max(|up - nom|, |down - nom|) of the total is taken, and the sources are added in
quadrature with the MC statistical uncertainty of the total.
"""
import glob
import logging
import os
from pathlib import Path

import ROOT

ROOT.TH1.AddDirectory(False)

REPO = Path(__file__).resolve().parents[2]
OUTPUT = Path(os.environ.get("SKNANO_OUTPUT_LOCAL", REPO / "SKNanoOutput"))
log = logging.getLogger("histutils")


class Source:
    """One analyzer output directory; keeps files open and caches histograms."""

    def __init__(self, analyzer, flags, era):
        self.dir = OUTPUT / analyzer / flags / era
        if not self.dir.is_dir():
            raise FileNotFoundError(self.dir)
        self._files = {}
        self.missing = set()

    def file(self, sample):
        if sample not in self._files:
            p = self.dir / f"{sample}.root"
            f = ROOT.TFile.Open(str(p)) if p.exists() else None
            if not f or f.IsZombie():
                raise FileNotFoundError(p)
            self._files[sample] = f
        return self._files[sample]

    def data_samples(self, pds):
        out = []
        for pd in pds:
            out += sorted(Path(p).stem for p in glob.glob(str(self.dir / f"{pd}_*.root")))
        if not out:
            raise FileNotFoundError(f"no data files for {pds} in {self.dir}")
        return out

    def get(self, sample, path):
        """Histogram clone or None (missing histograms are recorded, not fatal)."""
        h = self.file(sample).Get(path)
        if not h:
            self.missing.add(f"{sample}:{path}")
            return None
        h = h.Clone(f"{sample}__{path}")
        h.SetDirectory(0)
        return h


def add(hists, name):
    hists = [h for h in hists if h is not None]
    if not hists:
        return None
    out = hists[0].Clone(name)
    out.SetDirectory(0)
    for h in hists[1:]:
        out.Add(h)
    return out


def data_hist(src, pds, channel, key):
    return add([src.get(s, f"{channel}/Central/{key}") for s in src.data_samples(pds)], "data")


def get_lane(src, sample, channel, key, lane, fallback=None):
    """The lane's histogram; with fallback, samples that do not have the lane
    (e.g. TopPtReweight_Applied exists only for ttbar) use the fallback lane."""
    if fallback and not src.file(sample).GetDirectory(f"{channel}/{lane}"):
        lane = fallback
    return src.get(sample, f"{channel}/{lane}/{key}")


def group_hists(src, groups, order, channel, key, lane="Central", fallback=None):
    """[(group, TH1)] bottom to top; groups with no histogram are skipped."""
    out = []
    for g in order:
        h = add([get_lane(src, s, channel, key, lane, fallback) for s in groups[g]["members"]], f"{g}_{lane}")
        if h is not None:
            out.append((g, h))
    return out


def total(src, members, channel, key, lane):
    return add([src.get(s, f"{channel}/{lane}/{key}") for s in members], f"total_{lane}")


def band(src, members, channel, key, systs, prepare=None):
    """Total prediction with bin errors = stat (+) envelope of each source.

    prepare: optional callable applied to every total before the envelope
    (rebinning and range), so the band matches the drawn binning.
    Returns (band TH1, {source: per-bin max relative deviation}) .
    """
    p = prepare or (lambda h: h)
    nom = p(total(src, members, channel, key, "Central"))
    n = nom.GetNbinsX()
    var2 = [nom.GetBinError(i) ** 2 for i in range(n + 2)]
    summary = {}
    for name, (up, down) in systs.items():
        hu, hd = total(src, members, channel, key, up), total(src, members, channel, key, down)
        if hu is None or hd is None:
            log.warning("lane %s/%s missing for %s/%s", up, down, channel, key)
            continue
        hu, hd = p(hu), p(hd)
        rel = 0.
        for i in range(n + 2):
            c = nom.GetBinContent(i)
            d = max(abs(hu.GetBinContent(i) - c), abs(hd.GetBinContent(i) - c))
            var2[i] += d * d
            if c > 0 and 1 <= i <= n:
                rel = max(rel, d / c)
        summary[name] = rel
    for i in range(n + 2):
        nom.SetBinError(i, var2[i] ** 0.5)
    return nom, summary
