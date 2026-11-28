"""Monitoring metrics of the 2024 ParticleNet (docs/PLAN_ParticleNet.md steps 3, P8 checks).

weighted_auc: area under the ROC of signal vs background for a score with event weights (ties shared,
negative weights allowed: the ROC is built from the weighted cumulative sums).
weighted_ks: Kolmogorov-Smirnov distance of two weighted samples (max |CDF_a - CDF_b|) and the asymptotic
p-value with the effective sizes (sum w)^2 / sum w^2.
dcor_np: weighted distance correlation of two 1-d arrays (numpy, O(n^2): subsampled to max_n events).
"""
import numpy as np


def weighted_auc(score, is_sig, w):
    score, is_sig, w = np.asarray(score, np.float64), np.asarray(is_sig, bool), np.asarray(w, np.float64)
    ws, wb = w[is_sig].sum(), w[~is_sig].sum()
    if ws == 0 or wb == 0:
        return float("nan")
    order = np.argsort(-score, kind="stable")
    s, sig, ww = score[order], is_sig[order], w[order]
    # group ties
    uniq, idx = np.unique(-s, return_index=True)
    sw = np.add.reduceat(np.where(sig, ww, 0.0), idx)
    bw = np.add.reduceat(np.where(~sig, ww, 0.0), idx)
    tpr = np.concatenate([[0.0], np.cumsum(sw)]) / ws
    fpr = np.concatenate([[0.0], np.cumsum(bw)]) / wb
    return float(np.trapezoid(tpr, fpr))


def weighted_ks(a, wa, b, wb):
    a, wa, b, wb = (np.asarray(v, np.float64) for v in (a, wa, b, wb))
    if len(a) == 0 or len(b) == 0 or wa.sum() == 0 or wb.sum() == 0:
        return float("nan"), float("nan")
    grid = np.sort(np.concatenate([a, b]))
    oa, ob = np.argsort(a), np.argsort(b)
    ca = np.concatenate([[0.0], np.cumsum(wa[oa])]) / wa.sum()
    cb = np.concatenate([[0.0], np.cumsum(wb[ob])]) / wb.sum()
    fa = ca[np.searchsorted(a[oa], grid, side="right")]
    fb = cb[np.searchsorted(b[ob], grid, side="right")]
    d = float(np.max(np.abs(fa - fb)))
    na = wa.sum() ** 2 / (wa ** 2).sum()
    nb = wb.sum() ** 2 / (wb ** 2).sum()
    lam = (np.sqrt(na * nb / (na + nb)) + 0.12 + 0.11 / np.sqrt(na * nb / (na + nb))) * d
    k = np.arange(1, 101)
    p = float(np.clip(2 * np.sum((-1) ** (k - 1) * np.exp(-2 * k * k * lam * lam)), 0, 1))
    return d, p


def dcor_np(x, y, w, max_n=4096, rng=None):
    x, y, w = (np.asarray(v, np.float64) for v in (x, y, w))
    if len(x) < 2 or w.sum() <= 0:
        return float("nan")
    if len(x) > max_n:
        rng = rng or np.random.default_rng(0)
        i = rng.choice(len(x), max_n, replace=False)
        x, y, w = x[i], y[i], w[i]
    w = w / w.sum()
    a, b = np.abs(x[None] - x[:, None]), np.abs(y[None] - y[:, None])
    ww = w[None] * w[:, None]
    A = a - (a * w[None]).sum(1, keepdims=True) - (a * w[:, None]).sum(0, keepdims=True) + (a * ww).sum()
    B = b - (b * w[None]).sum(1, keepdims=True) - (b * w[:, None]).sum(0, keepdims=True) + (b * ww).sum()
    dcov, vx, vy = (A * B * ww).sum(), (A * A * ww).sum(), (B * B * ww).sum()
    if vx <= 0 or vy <= 0:
        return float("nan")
    return float(np.sqrt(abs(dcov) / np.sqrt(vx * vy)))
