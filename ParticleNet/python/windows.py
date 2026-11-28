"""mA windows of the parametric ParticleNet (docs/PLAN_ParticleNet.md P3, P7, P9).

Window i of channel ch: [lo, hi] = [x0 - 10 sigma_eff, x0 + 10 sigma_eff] (configs/windows.json, built by
make_windows_config.py from the SignalRegionStudy binning). The A-candidate mass of window i is the
template pairing: 1E2MU mass1; 3MU "low" = mass1 (lower OS pair), "high" = mass2 (higher OS pair)
(analyzer: mass1 <= mass2; np.minimum / np.maximum as SignalRegionStudy sample_reader.select_mass).

Scoring (P9): an event is scored at grid point i iff window i of its channel contains its A-candidate
mass (assign). Training membership of the band networks: python/bands.py (union of the band's windows).
DisCo position (P7, user decision 2026-11-28): Delta_k = (m_k - mA) / sigma_eff(mA) for the two OS pairs
k = 1, 2 (mass1, mass2) with the event's mA (signal: generated; background: the drawn mA), sigma_eff of the
channel interpolated linearly in mA between the points of this Windows object (constant beyond the ends);
Delta_2 is undefined (0, masked in the loss) for 1E2MU.
A windows config may hold interpolated grid points (make_windows_config.py --grid).
"""
import json

import numpy as np

CHANNELS = ("1E2MU", "3MU")


class Windows:
    def __init__(self, path, points=None):
        cfg = json.load(open(path))
        pts = cfg["points"]
        if points is not None:
            want = set(points)
            pts = [p for p in pts if p["name"] in want]
            miss = want - {p["name"] for p in pts}
            if miss:
                raise KeyError(f"mass points not in {path}: {sorted(miss)}")
        self.path = path
        self.names = [p["name"] for p in pts]
        self.mA = np.array([p["mA"] for p in pts], dtype=np.float64)
        self.n = len(pts)
        self.ch = {}
        for ch in CHANNELS:
            c = [p["channels"][ch] for p in pts]
            self.ch[ch] = {"x0": np.array([q["x0"] for q in c]), "sigma": np.array([q["sigma_eff"] for q in c]),
                           "lo": np.array([q["lo"] for q in c]), "hi": np.array([q["hi"] for q in c]),
                           "pairing": [q["pairing"] for q in c]}

    def index(self, name):
        return self.names.index(name)

    @staticmethod
    def a_mass(mass1, mass2, pairing):
        if pairing == "mass1":
            return mass1
        if pairing == "low":
            return np.minimum(mass1, mass2)
        if pairing == "high":
            return np.maximum(mass1, mass2)
        raise ValueError(pairing)

    def in_window(self, ch, i, mass1, mass2):
        c = self.ch[ch]
        m = self.a_mass(mass1, mass2, c["pairing"][i])
        return (m >= c["lo"][i]) & (m <= c["hi"][i])

    def assign(self, ch, mass1, mass2, fixed=None, require_in=True):
        """(event index, window index) pairs of the events of channel `ch`.

        fixed: None (every window containing the event) or an int array of the window of each event
        (signal: its own point; -1 = no window); with require_in the event must lie in that window."""
        n = len(mass1)
        evs, wins = [], []
        if fixed is None:
            for i in range(self.n):
                sel = np.nonzero(self.in_window(ch, i, mass1, mass2))[0]
                evs.append(sel)
                wins.append(np.full(len(sel), i, dtype=np.int32))
        else:
            fixed = np.asarray(fixed)
            for i in range(self.n):
                sel = fixed == i
                if require_in:
                    sel &= self.in_window(ch, i, mass1, mass2)
                sel = np.nonzero(sel)[0]
                evs.append(sel)
                wins.append(np.full(len(sel), i, dtype=np.int32))
        ev = np.concatenate(evs) if evs else np.zeros(0, np.int64)
        w = np.concatenate(wins) if wins else np.zeros(0, np.int32)
        order = np.lexsort((w, ev))  # by event, then window
        assert len(ev) == 0 or ev.max() < n
        return ev[order].astype(np.int64), w[order]

    def sigma_at(self, ch, mA):
        """sigma_eff of channel ch at mA, linear in mA between the points (sorted by mA)."""
        o = np.argsort(self.mA)
        return np.interp(np.asarray(mA, np.float64), self.mA[o], self.ch[ch]["sigma"][o])

    def deltas(self, ch, mA, mass1, mass2):
        """Delta_1, Delta_2 (P7) of events with parameter mA and OS-pair masses mass1, mass2."""
        sg = self.sigma_at(ch, mA)
        d1 = (np.asarray(mass1, np.float64) - mA) / sg
        d2 = (np.asarray(mass2, np.float64) - mA) / sg if ch == "3MU" else np.zeros_like(d1)
        return d1.astype(np.float32), d2.astype(np.float32)
