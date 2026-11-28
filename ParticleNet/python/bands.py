"""mA bands of the three ParticleNet networks (user decision 2026-11-28, docs/PLAN_ParticleNet.md).

Bands (configs/bands.json, as SignalRegionStudy interpolation_config.NORM_MA_BINS): belowZ [15, 80),
onZ [80, 100), aboveZ [100, 155] (lo <= mA < hi, the last band also includes hi). One network per band
(x 5 folds), parametric in mA; it is trained on the signal points of the band and scores every grid mA of
the band.

Band mass range of channel ch: the union of the template windows [x0 - 10 sigma_eff, x0 + 10 sigma_eff] of
the band's signal points, each window with its template pairing (1E2MU mass1; 3MU low / high OS pair,
configs/windows.json). A background event enters the band's training set (once) iff its A-candidate mass,
with the pairing of that window, lies in at least one of these windows. The ranges of neighbouring bands
overlap (e.g. the 75 GeV and 80 GeV windows), so a background event can enter two bands' training sets,
once each (allowed by the user decision). The union is not contiguous at low mA, where the windows are
narrower than the 5 GeV point spacing (intervals() lists the pieces).

Background mA (parametric training with a random mA): for every (event, band) a uniform number
u = splitmix64 hash of (crc32(sample), channel, entry index in its Train_ RNTuple, event number, band index)
/ 2^64 (deterministic, reproducible, independent of the fold and of the reading order), mapped by the
inverse CDF onto the signal points of the band with probabilities proportional to the total physical weight
of the band's selected signal events of each point in the same channel (= the signal training-weight totals,
since the class rescaling is uniform within the signal class). Signal events keep their generated mA.
"""
import json
import zlib

import numpy as np

M64 = np.uint64(0xFFFFFFFFFFFFFFFF)


def splitmix64(x):
    x = np.asarray(x, dtype=np.uint64)
    with np.errstate(over="ignore"):
        x = x + np.uint64(0x9E3779B97F4A7C15)
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return x ^ (x >> np.uint64(31))


def uniform_hash(sample, channel_id, entry, event, band_id):
    """Deterministic u in [0, 1) per (sample, channel, entry, event, band)."""
    with np.errstate(over="ignore"):
        h = splitmix64(np.uint64(zlib.crc32(sample.encode())) * np.uint64(1000003) + np.uint64(channel_id))
        h = splitmix64(h ^ np.asarray(entry, dtype=np.uint64))
        h = splitmix64(h ^ np.asarray(event, dtype=np.uint64))
        h = splitmix64(h ^ np.uint64(band_id + 1))
    return (h >> np.uint64(11)).astype(np.float64) / float(2 ** 53)


def draw_mA(u, mA_points, weights):
    """Inverse CDF: index into mA_points of each u for probabilities proportional to weights (> 0)."""
    w = np.asarray(weights, np.float64)
    if (w <= 0).any():
        raise ValueError(f"non-positive signal weight totals {w}")
    cdf = np.cumsum(w) / w.sum()
    return np.minimum(np.searchsorted(cdf, u, side="right"), len(w) - 1)


class Bands:
    def __init__(self, path):
        cfg = json.load(open(path))
        self.path = path
        self.cfg = cfg
        self.names = [b["name"] for b in cfg["bands"]]
        self.lo = np.array([b["lo"] for b in cfg["bands"]], np.float64)
        self.hi = np.array([b["hi"] for b in cfg["bands"]], np.float64)
        self.n = len(self.names)

    def band_of(self, mA):
        """Band index of each mA (-1 outside): lo <= mA < hi, the last band also includes hi."""
        mA = np.atleast_1d(np.asarray(mA, np.float64))
        out = np.full(mA.shape, -1, np.int64)
        for b in range(self.n):
            m = (mA >= self.lo[b]) & ((mA < self.hi[b]) | ((b == self.n - 1) & (mA == self.hi[b])))
            out[m] = b
        return out

    def points(self, win, b):
        """Indices of the points of Windows `win` in band b."""
        return np.nonzero(self.band_of(win.mA) == b)[0]

    def in_band(self, win, b, ch, mass1, mass2):
        m = np.zeros(len(mass1), bool)
        for i in self.points(win, b):
            m |= win.in_window(ch, i, mass1, mass2)
        return m

    def intervals(self, win, b, ch):
        """The band's mass range of channel ch as merged [lo, hi] intervals, with the pairing of each piece
        (3MU: the low-pair windows (mA < 60) and the high-pair windows are listed separately)."""
        out = {}
        for i in self.points(win, b):
            c = win.ch[ch]
            out.setdefault(c["pairing"][i], []).append([float(c["lo"][i]), float(c["hi"][i])])
        merged = {}
        for p, iv in out.items():
            iv.sort()
            mm = [iv[0]]
            for a, z in iv[1:]:
                if a <= mm[-1][1]:
                    mm[-1][1] = max(mm[-1][1], z)
                else:
                    mm.append([a, z])
            merged[p] = mm
        return merged
