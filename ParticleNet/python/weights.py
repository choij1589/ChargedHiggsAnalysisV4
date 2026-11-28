"""Splits and training weights of the 5-fold cross-training (docs/PLAN_ParticleNet.md P8, P11).

Splits of network j (P8): test = fold j (never seen), early stopping (ES) = fold (j + 1) % 5, training =
the other three folds; fold = event % 5.

Training weights (P11): the physical weight of each pair (weight_genpu [x weight_fake], incl. the
prescale N) rescaled per (split, mA window, class) cell so that every cell of a split has the same total
T_s, i.e. in every window the signal and each background class have equal totals and every window has
the same total (P11 (2) (ii): the Z-peak windows have ~10x the background of the low-mA ones). Inside a
cell the relative weights stay physical (sample composition by xsec x acceptance, the background mix of
the window). T_s = N_s / n_cells_s (N_s pairs in the split, n_cells_s non-empty cells), so the mean
training weight per pair is ~1 (the loss is normalised by sum |w|, the scale only fixes the numerics).
Cells with no pairs or a non-positive weight sum get no weight (reported in the returned table).
"""
import numpy as np

SPLITS = ("train", "es", "test")


def split_of(fold, net, n_folds=5):
    """0 train, 1 early stopping, 2 test for network `net`."""
    fold = np.asarray(fold).astype(np.int64)
    s = np.zeros(fold.shape, np.int8)
    s[fold == (net + 1) % n_folds] = 1
    s[fold == net] = 2
    return s


def rescale(weight, label, win, split, n_classes, n_windows):
    """Training weights (float64) and the cell table {split: {"target", "cells": [[win, cls, n, sumw, f]]}}."""
    out = np.zeros(len(weight), np.float64)
    table = {}
    cell = (split.astype(np.int64) * n_windows + win.astype(np.int64)) * n_classes + label.astype(np.int64)
    ncell = 3 * n_windows * n_classes
    n = np.bincount(cell, minlength=ncell)
    sw = np.bincount(cell, weights=weight, minlength=ncell)
    for s, sname in enumerate(SPLITS):
        sl = slice(s * n_windows * n_classes, (s + 1) * n_windows * n_classes)
        ns, sws = n[sl], sw[sl]
        good = (ns > 0) & (sws > 0)
        target = (ns.sum() / good.sum()) if good.sum() else 0.0
        fac = np.where(good, target / np.where(good, sws, 1.0), 0.0)
        rows = []
        for k in range(n_windows * n_classes):
            if ns[k] or sws[k]:
                rows.append([k // n_classes, k % n_classes, int(ns[k]), float(sws[k]), float(fac[k])])
        table[sname] = {"target": float(target), "n_pairs": int(ns.sum()), "cells": rows,
                        "bad_cells": [[k // n_classes, k % n_classes, int(ns[k]), float(sws[k])]
                                      for k in range(n_windows * n_classes) if ns[k] and not good[k]]}
        m = split == s
        out[m] = weight[m] * fac[cell[m] - s * n_windows * n_classes]
    return out, table
