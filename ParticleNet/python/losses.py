"""Loss of the 2024 parametric ParticleNet (docs/PLAN_ParticleNet.md P7).

loss = CE_w + lambda [dCor_w(s_sig, Delta_1) + dCor_w(s_sig, Delta_2)], lambda = 0.1, with
  CE_w     = sum_i w_i CE_i / sum_i |w_i| over the batch (previous WeightedCrossEntropyLoss),
  s_sig    = softmax(logits)[:, 0],
  dCor_w   = weighted distance correlation (previous WeightedLoss.distance_correlation, Kasieczka et al.)
             over the background events of the batch (label != 0) for Delta_1, and over the background
             mu mu mu events only for Delta_2 (the e mu mu events have no second OS pair: they are masked,
             not set to Delta_2 = 0, which would correlate the term with the channel).
The masks enter as zero weights in the weighted dCor (a zero-weight event drops out of every weighted
mean of the double centring and of dCov / dVar exactly), so the shapes stay static for torch.compile and
the Delta_2 values of masked events cannot matter (checked in test/run_synthetic_bench.py).
"""
import torch
import torch.nn.functional as F


def distance_correlation(x, y, w, eps: float = 1e-12):
    """Weighted distance correlation of 1-d tensors x, y with weights w (zero weight = excluded)."""
    wsum = w.sum()
    w = w / wsum.clamp(min=1e-12)
    a = (x[None, :] - x[:, None]).abs()
    b = (y[None, :] - y[:, None]).abs()
    ww = w[None, :] * w[:, None]
    A = a - (a * w[None, :]).sum(1, keepdim=True) - (a * w[:, None]).sum(0, keepdim=True) + (a * ww).sum()
    B = b - (b * w[None, :]).sum(1, keepdim=True) - (b * w[:, None]).sum(0, keepdim=True) + (b * ww).sum()
    dcov = (A * B * ww).sum()
    vx, vy = (A * A * ww).sum(), (B * B * ww).sum()
    return torch.sqrt((dcov.abs() / torch.sqrt((vx * vy).clamp(min=eps))).clamp(min=eps))


class DiscoLoss(torch.nn.Module):
    def __init__(self, disco_lambda=0.1):
        super().__init__()
        self.lam = disco_lambda

    def forward(self, logits, y, w, d1, d2, is3mu, return_parts=False):
        ce = (F.cross_entropy(logits, y, reduction="none") * w).sum() / w.abs().sum().clamp(min=1e-8)
        s = torch.softmax(logits, 1)[:, 0]
        bkg = (y != 0).to(w.dtype)
        w1 = w * bkg
        w2 = w * bkg * is3mu.to(w.dtype)
        dc1 = distance_correlation(s, d1, w1)
        dc2 = distance_correlation(s, d2, w2)
        loss = ce + self.lam * (dc1 + dc2)
        if return_parts:
            return loss, ce.detach(), dc1.detach(), dc2.detach()
        return loss
