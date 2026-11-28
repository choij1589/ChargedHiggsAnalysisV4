"""GPU-resident graphs and batch assembly of the 2024 ParticleNet (docs/PLAN_ParticleNet.md P2, P3, P10).

The node table (x [N_nodes, 9], etaphi [N_nodes, 2]) and the per-event offsets / counts live on the GPU
once; a batch is a set of (event, mA window) pairs: its nodes are gathered by index (an event replicated
in several windows shares its nodes), the graph feature is mA / mA_scale, and the first-layer edges are the
k nearest neighbours in Delta R = sqrt(d eta^2 + d phi^2) (phi wrapped) inside each graph, computed with a
padded [B, M, M] distance matrix (M = largest graph of the data set). Training augmentation: one random
rotation in phi per graph applied to (px, py) (previous ParticleNetMD apply_phi_rotation); Delta R is
rotation invariant, so the first-layer edges are unchanged.
"""
import math

import numpy as np
import torch


class GraphStore:
    def __init__(self, x, etaphi, counts, offsets, device, max_nodes=None):
        self.device = device
        self.x = torch.as_tensor(x, dtype=torch.float32, device=device)
        self.etaphi = torch.as_tensor(etaphi, dtype=torch.float32, device=device)
        self.counts = torch.as_tensor(np.asarray(counts, np.int64), device=device)
        self.offsets = torch.as_tensor(np.asarray(offsets, np.int64), device=device)
        self.M = int(max_nodes if max_nodes is not None else int(np.max(counts)))

    def batch(self, ev, mA_norm, k=4, rotate=False, generator=None):
        """Graphs of events `ev` (int64 tensor on device) with graph features mA_norm [B, 1].

        Returns x [n, 9], batch [n], edge_index0 [2, B k] (source = neighbour, target = centre), graph_x."""
        B = ev.shape[0]
        cnt = self.counts[ev]
        start = self.offsets[ev]
        gstart = torch.cumsum(cnt, 0) - cnt
        batch = torch.repeat_interleave(torch.arange(B, device=self.device), cnt)
        n = batch.shape[0]
        pos = torch.arange(n, device=self.device) - gstart[batch]
        nid = start[batch] + pos
        x = self.x[nid]
        if rotate:
            phi = torch.rand(B, device=self.device, generator=generator) * (2 * math.pi)
            c, s = torch.cos(phi)[batch], torch.sin(phi)[batch]
            px, py = x[:, 1], x[:, 2]
            x = torch.cat([x[:, :1], (px * c - py * s)[:, None], (px * s + py * c)[:, None], x[:, 3:]], 1)
        # Delta R k-NN inside each graph
        M = self.M
        ep = self.etaphi[nid]
        eta = torch.full((B, M), float("nan"), device=self.device)
        phi = torch.zeros((B, M), device=self.device)
        eta[batch, pos] = ep[:, 0]
        phi[batch, pos] = ep[:, 1]
        deta = eta[:, :, None] - eta[:, None, :]
        dphi = torch.remainder(phi[:, :, None] - phi[:, None, :] + math.pi, 2 * math.pi) - math.pi
        dr2 = deta * deta + dphi * dphi
        eye = torch.eye(M, dtype=torch.bool, device=self.device)[None]
        dr2 = torch.where(torch.isnan(dr2) | eye, torch.full_like(dr2, float("inf")), dr2)
        nb = torch.topk(dr2, k, dim=2, largest=False).indices  # [B, M, k] neighbour positions
        nb = nb[batch, pos]                                    # [n, k] for the real nodes
        src = (gstart[batch][:, None] + nb).reshape(-1)
        dst = torch.arange(n, device=self.device).repeat_interleave(k)
        edge_index0 = torch.stack([src, dst])
        return x, batch, edge_index0, mA_norm.view(B, 1)
