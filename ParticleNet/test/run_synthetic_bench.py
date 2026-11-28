"""End-to-end synthetic bench of the 2024 ParticleNet chain (docs/PLAN_ParticleNet.md steps 2-4).

Runs on the local GPU (micromamba run -n PNet): synthetic trees (test/make_synthetic_trees.py) -> dataset
(python/build_dataset.py) -> 5-fold training for a few epochs (python/train.py) -> offline scoring of the
SR_ and Train_ RNTuples (python/score.py), and checks:
  C1 inputs: per class and sample the selected event counts / weight sums equal an independent uproot
     selection of the trees (passSR; not allTight and nBJets >= 1 with weight_genpu x weight_fake > 0);
     RNTuple and TTree inputs both read (ZZto4L is a TTree); fold = event % 5.
  C2 nodes: E, px, py, pz of every node recomputed from the tree fields; m(mu mu) from the first two lepton
     nodes = mass1 for 1E2MU; the 3MU OS-pair masses from the nodes = (mass1, mass2).
  C3 window assignment: every pair lies in its window (template pairing); every background event is in
     exactly the windows containing it; every signal event only in its own window (and inside it);
     Delta_1, Delta_2 recomputed.
  C4 weights (P11): for every network and split, every non-empty (window, class) cell sums to the same
     target T_s (signal = each background class in each window, every window equal), T_s x n_cells = N_s,
     the factor is constant inside a cell (physical weights kept), and the splits follow P8.
  C5 DisCo mask: the Delta_2 term is unchanged when the e mu mu Delta_2 values are replaced by noise, its
     gradient w.r.t. the e mu mu logits is zero, it equals the weighted dCor over the mu mu mu background
     events alone, and the Delta_1 term ignores the signal events.
  C6 torch.compile: compiled vs eager model outputs (eval) agree, a compiled training step runs, graph breaks.
  C7 scoring (score rows aligned with the input entries; the synthetic signal has run = lumi = 1 and
     repeated event numbers, as the 2024 signal, so the event key is not unique): every scored Train_ event
     (found by entry index) got, at every window containing it, the score of the network of its
     fold, equal to that network's held-out (test-split) score of the training job; a sample of SR events
     re-scored with all 5 networks matches only its own fold's network; score_mA = the grid windows
     containing the event; one row per input row in input order; data Nonprompt files scored.
  T  timing / memory: time per training step and per evaluation step at batch 512 (eager and compiled),
     peak GPU memory, epoch times of the bench training.
Results: <work_dir>/bench_results.json (and printed).

Run: micromamba run -n PNet python ParticleNet/test/run_synthetic_bench.py --work-dir DIR [--epochs 5]
"""
import argparse
import copy
import json
import os
import subprocess
import sys
import time

import awkward as ak
import numpy as np
import torch
import uproot

HERE = os.path.dirname(os.path.abspath(__file__))
PNET = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PNET, "python"))
import pnet_io  # noqa: E402
import weights as wmod  # noqa: E402
from gpu_data import GraphStore  # noqa: E402
from losses import DiscoLoss, distance_correlation  # noqa: E402
from metrics import dcor_np  # noqa: E402
from model import ParticleNet  # noqa: E402
from score import load_networks  # noqa: E402
from train import load_dataset, predict  # noqa: E402
from windows import Windows  # noqa: E402

POINTS = ["MHc130_MA15", "MHc130_MA30", "MHc130_MA55", "MHc130_MA65", "MHc130_MA90", "MHc130_MA120"]
RES = {"checks": {}}


def check(name, ok, **info):
    RES["checks"][name] = {"pass": bool(ok), **info}
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {json.dumps(info, default=float)[:400]}")


def sh(args):
    print("+", " ".join(args))
    t = time.time()
    subprocess.run([sys.executable] + args, check=True)
    return time.time() - t


def c1_inputs(trees, data, meta, ccfg):
    ok, info = True, {}
    for si, s in enumerate(meta["samples"]):
        cls = next(c for c in ccfg["classes"] if (c["samples"] == "signal" and s.startswith("TTToHcToWA"))
                   or (isinstance(c["samples"], list) and s in c["samples"]))
        f = os.path.join(trees, f"Skim_TriLep_{s}.root")
        n_ref = sw_ref = 0
        with uproot.open(f) as fo:
            for ch in ("1E2MU", "3MU"):
                a = fo[f"Train_{ch}"].arrays(["passSR", "allTight", "nBJets", "weight_genpu", "weight_fake",
                                              "mass1", "mass2", "event"], library="np")
                if cls["selection"] == "passSR":
                    m = a["passSR"].astype(bool)
                    w = a["weight_genpu"].astype(np.float64)
                else:
                    w = a["weight_genpu"].astype(np.float64) * a["weight_fake"]
                    m = ~a["allTight"].astype(bool) & (a["nBJets"] >= 1) & (w > 0)
                if cls["samples"] == "signal":  # in own window (signal_in_window)
                    win = Windows(meta["windows_file"], meta["points"])
                    ip = meta["points"].index(s.split("-")[1])
                    m &= win.in_window(ch, ip, a["mass1"], a["mass2"])
                else:
                    win = Windows(meta["windows_file"], meta["points"])
                    anyw = np.zeros(len(m), bool)
                    for i in range(win.n):
                        anyw |= win.in_window(ch, i, a["mass1"], a["mass2"])
                    m &= anyw
                n_ref += int(m.sum())
                sw_ref += float(w[m].sum())
        sel = data["ev_sample"] == si
        n, sw = int(sel.sum()), float(data["ev_weight"][sel].sum())
        good = n == n_ref and abs(sw - sw_ref) <= 1e-6 * max(1.0, abs(sw_ref))
        ok &= good
        info[s] = [n, n_ref]
    folds_ok = np.array_equal(data["ev_fold"], (data["ev_event"] % np.uint64(5)).astype(np.int8))
    nonneg = bool((data["ev_weight"][data["ev_label"] == 1] > 0).all())
    check("C1_inputs", ok and folds_ok and nonneg, n_events_vs_reference=info, fold_rule=folds_ok,
          nonprompt_weights_positive=nonneg, ttree_sample="ZZto4L" in meta["samples"])


def c2_nodes(trees, data, meta):
    """Recompute the nodes of every event of two samples (one RNTuple, one TTree) from the tree fields."""
    maxdiff, mdiff = 0.0, 0.0
    for s in ("WZto3LNu", "ZZto4L", "TTToHcToWAToMuMu-MHc130_MA90"):
        si = meta["samples"].index(s)
        with uproot.open(os.path.join(trees, f"Skim_TriLep_{s}.root")) as fo:
            for ch, cid in (("1E2MU", 0), ("3MU", 1)):
                a = fo[f"Train_{ch}"].arrays(pnet_io.OBJ_FIELDS + ["event", "mass1", "mass2"])
                idx = np.nonzero((data["ev_sample"] == si) & (data["ev_channel"] == cid))[0]
                for i in idx:
                    r = a[int(data["ev_entry"][i])]  # entry index (the event key is not unique for signal)
                    assert int(r["event"]) == int(data["ev_event"][i])
                    o, c = data["offsets"][i], data["counts"][i]
                    x = data["x"][o:o + c].astype(np.float64)
                    pt = np.concatenate([np.asarray(r["lep_pt"]), np.asarray(r["jet_pt"]), [r["MET_pt"]]])
                    eta = np.concatenate([np.asarray(r["lep_eta"]), np.asarray(r["jet_eta"]), [0.0]])
                    phi = np.concatenate([np.asarray(r["lep_phi"]), np.asarray(r["jet_phi"]), [r["MET_phi"]]])
                    m = np.concatenate([np.asarray(r["lep_mass"]), np.asarray(r["jet_mass"]), [0.0]])
                    px, py = pt * np.cos(phi), pt * np.sin(phi)
                    pz = np.where(np.arange(c) < c - 1, pt * np.sinh(eta), 0.0)
                    E = np.where(np.arange(c) < c - 1, np.sqrt(px ** 2 + py ** 2 + pz ** 2 + m ** 2), pt)
                    ref = np.stack([E, px, py, pz], 1)
                    maxdiff = max(maxdiff, float(np.max(np.abs(ref - x[:, :4]) / (1 + np.abs(ref)))))
                    flags = x[:, 4:]
                    nj = c - 4
                    # flags: charge, isMu, isE, isJet, isB
                    assert (flags[:3, 1] == np.asarray(r["lep_isMuon"])).all()
                    assert (flags[:3, 2] == ~np.asarray(r["lep_isMuon"])).all() and (flags[:3, 3:] == 0).all()
                    assert (flags[3:3 + nj, 3] == 1).all() and (flags[3:3 + nj, 1:3] == 0).all()
                    assert (flags[3:3 + nj, 4] == np.asarray(r["jet_isBtagged"])).all() and (flags[-1] == 0).all()
                    assert (flags[:3, 0] == np.asarray(r["lep_charge"])).all() and (flags[3:, 0] == 0).all()
                    mm = lambda u, v: np.sqrt(max((x[u, 0] + x[v, 0]) ** 2 - np.sum((x[u, 1:4] + x[v, 1:4]) ** 2), 0))
                    if ch == "1E2MU":
                        mdiff = max(mdiff, abs(mm(0, 1) - float(r["mass1"])) / float(r["mass1"]))
                    else:
                        q = flags[:3, 0]
                        os_ = int(np.nonzero(q != np.sign(q.sum()))[0][0])
                        ms = sorted(mm(os_, j) for j in range(3) if j != os_)
                        mdiff = max(mdiff, abs(ms[0] - float(r["mass1"])) / float(r["mass1"]),
                                    abs(ms[1] - float(r["mass2"])) / float(r["mass2"]))
    # first-layer edges: the k = 4 nearest neighbours in Delta R of every node (brute force, 300 graphs)
    dev = torch.device("cuda")
    store = GraphStore(data["x"], data["etaphi"], data["counts"], data["offsets"], dev)
    ev = torch.arange(300, device=dev)
    _, bt, e0, _ = store.batch(ev, torch.zeros(300, device=dev), k=4)
    src, dst = e0.cpu().numpy()
    gst = np.concatenate([[0], np.cumsum(data["counts"][:300])])
    knn_ok = True
    for g in range(300):
        o, c = data["offsets"][g], data["counts"][g]
        ep = data["etaphi"][o:o + c].astype(np.float64)
        dphi = np.remainder(ep[:, None, 1] - ep[None, :, 1] + np.pi, 2 * np.pi) - np.pi
        dr = np.sqrt((ep[:, None, 0] - ep[None, :, 0]) ** 2 + dphi ** 2)
        np.fill_diagonal(dr, np.inf)
        for i in range(c):
            got = set(src[dst == gst[g] + i] - gst[g])
            ref = np.sort(dr[i])[3]
            knn_ok &= len(got) == 4 and all(dr[i, j] <= ref + 1e-5 for j in got)
    check("C2_nodes", maxdiff < 1e-5 and mdiff < 1e-3 and knn_ok, first_layer_deltaR_knn=bool(knn_ok),  # float32 E^2 - p^2 cancellation at small m / p
          max_rel_diff_p4=maxdiff, max_rel_diff_pair_mass=mdiff)


def c3_windows(data, meta):
    win = Windows(meta["windows_file"], meta["points"])
    chn = ("1E2MU", "3MU")
    pe, pw = data["p_ev"], data["p_win"].astype(np.int64)
    ch = data["ev_channel"][pe]
    m1, m2 = data["ev_mass1"][pe], data["ev_mass2"][pe]
    inside = np.zeros(len(pe), bool)
    for c in (0, 1):
        for i in range(win.n):
            s = (ch == c) & (pw == i)
            inside[s] = win.in_window(chn[c], i, m1[s], m2[s])
    # completeness for background, own window for signal
    nev = len(data["ev_label"])
    W = np.zeros((nev, win.n), bool)
    W[pe, pw] = True
    ref = np.zeros((nev, win.n), bool)
    for c in (0, 1):
        s = data["ev_channel"] == c
        for i in range(win.n):
            ref[s, i] = win.in_window(chn[c], i, data["ev_mass1"][s], data["ev_mass2"][s])
    bkg = data["ev_label"] != 0
    bkg_ok = np.array_equal(W[bkg], ref[bkg])
    sig = ~bkg
    own = np.zeros_like(ref)
    own[np.nonzero(sig)[0], data["ev_point"][sig]] = True
    sig_ok = np.array_equal(W[sig], own[sig]) and bool(ref[sig][own[sig]].all())
    dup = len(np.unique(pe * 100 + pw)) == len(pe)
    d1 = np.zeros(len(pe)); d2 = np.zeros(len(pe))
    for c in (0, 1):
        s = ch == c
        d1[s], d2[s] = win.deltas(chn[c], pw[s], m1[s], m2[s])
    dok = np.allclose(d1, data["p_d1"], atol=1e-5) and np.allclose(d2, data["p_d2"], atol=1e-5)
    dmask = bool((data["p_d2"][~data["p_is3mu"]] == 0).all())
    per_win = {wn: int((pw == i).sum()) for i, wn in enumerate(win.names)}
    check("C3_windows", bool(inside.all()) and bkg_ok and sig_ok and dup and dok and dmask,
          pairs_in_window=bool(inside.all()), background_complete=bkg_ok, signal_own_window=sig_ok,
          no_duplicate_pairs=dup, deltas=dok, delta2_zero_for_1e2mu=dmask, pairs_per_window=per_win,
          replication={n: float(((data["p_label"] == l).sum()) / max(1, (data["ev_label"] == l).sum()))
                       for l, n in enumerate(meta["classes"])})


def c4_weights(data, meta):
    nC, nW = 4, len(meta["points"])
    ok, info = True, {}
    for net in range(5):
        split = wmod.split_of(data["p_fold"], net)
        f = data["p_fold"].astype(int)
        sp_ok = bool((split[f == net] == 2).all() and (split[f == (net + 1) % 5] == 1).all()
                     and (split[(f != net) & (f != (net + 1) % 5)] == 0).all())
        wt, table = wmod.rescale(data["p_weight"], data["p_label"], data["p_win"], split, nC, nW)
        for s in range(3):
            m = split == s
            T = table[wmod.SPLITS[s]]["target"]
            tots, n_cells = [], 0
            for i in range(nW):
                for c in range(nC):
                    cm = m & (data["p_win"] == i) & (data["p_label"] == c)
                    if cm.sum() == 0:
                        continue
                    n_cells += 1
                    tots.append(wt[cm].sum())
                    r = wt[cm] / data["p_weight"][cm]
                    ok &= bool(np.allclose(r, r[0], rtol=1e-9))
            tots = np.array(tots)
            ok &= sp_ok and bool(np.allclose(tots, T, rtol=1e-9)) and abs(T * n_cells - m.sum()) < 1e-6 * m.sum()
            ok &= not table[wmod.SPLITS[s]]["bad_cells"]
            info[f"net{net}_{wmod.SPLITS[s]}"] = {"target": T, "n_cells": n_cells, "n_pairs": int(m.sum()),
                                                  "min_cell": float(tots.min()), "max_cell": float(tots.max())}
    check("C4_weights", ok, **{k: v for k, v in info.items() if k.startswith("net0")})


def c5_disco(data, meta, device):
    torch.manual_seed(0)
    nC, nW = 4, len(meta["points"])
    split = wmod.split_of(data["p_fold"], 0)
    wt, _ = wmod.rescale(data["p_weight"], data["p_label"], data["p_win"], split, nC, nW)
    rng = np.random.default_rng(1)
    idx = rng.choice(len(wt), 512, replace=False)
    T = lambda a, dt=torch.float32: torch.as_tensor(np.ascontiguousarray(a), dtype=dt, device=device)
    y, w = T(data["p_label"][idx], torch.int64), T(wt[idx])
    d1, d2, is3 = T(data["p_d1"][idx]), T(data["p_d2"][idx]), T(data["p_is3mu"][idx], torch.bool)
    logits = torch.randn(512, 4, device=device, requires_grad=True)
    lf = DiscoLoss(0.1)
    _, ce, a1, a2 = lf(logits, y, w, d1, d2, is3, return_parts=True)
    d2n = d2.clone()
    d2n[~is3] = torch.randn(int((~is3).sum()), device=device) * 100
    d1n = d1.clone()
    d1n[y == 0] = torch.randn(int((y == 0).sum()), device=device) * 100
    _, _, b1, b2 = lf(logits, y, w, d1n, d2n, is3, return_parts=True)
    s = torch.softmax(logits, 1)[:, 0]
    dc2 = distance_correlation(s, d2, w * (y != 0) * is3)
    dc2.backward()
    g_emm = float(logits.grad[~is3].abs().max())
    g_3mu = float(logits.grad[is3].abs().max())
    m = ((data["p_label"][idx] != 0) & data["p_is3mu"][idx])
    ref = dcor_np(s.detach().cpu().numpy()[m], data["p_d2"][idx][m], wt[idx][m], max_n=10 ** 6)
    m1 = data["p_label"][idx] != 0
    ref1 = dcor_np(s.detach().cpu().numpy()[m1], data["p_d1"][idx][m1], wt[idx][m1], max_n=10 ** 6)
    ok = (abs(float(a2 - b2)) < 1e-6 and g_emm == 0.0 and g_3mu > 0 and abs(float(a2) - ref) < 1e-4
          and abs(float(a1 - b1)) < 1e-6 and abs(float(a1) - ref1) < 1e-4)
    check("C5_disco_mask", ok, dcor2=float(a2), dcor2_emm_noise=float(b2), dcor2_numpy_3mu_bkg_only=ref,
          dcor1=float(a1), dcor1_signal_noise=float(b1), dcor1_numpy_bkg_only=ref1,
          max_grad_emm_logits=g_emm, max_grad_3mu_logits=g_3mu, n_emm=int((~is3).sum().item()),
          n_3mu_bkg=int(m.sum()))


def c6_compile_and_timing(data, meta, cfg, device, n_steps=200):
    import torch._dynamo as dyn
    mcfg = cfg["model"]
    k = mcfg["k"]
    store = GraphStore(data["x"], data["etaphi"], data["counts"], data["offsets"], device)
    split = wmod.split_of(data["p_fold"], 0)
    wt, _ = wmod.rescale(data["p_weight"], data["p_label"], data["p_win"], split, 4, len(meta["points"]))
    mA = np.asarray(meta["mA"])[data["p_win"]] / mcfg["mA_scale"]
    T = lambda a, dt=torch.float32: torch.as_tensor(np.ascontiguousarray(a), dtype=dt, device=device)
    p_ev, p_mA, p_y, p_w = T(data["p_ev"], torch.int64), T(mA), T(data["p_label"], torch.int64), T(wt)
    p_d1, p_d2, p_3 = T(data["p_d1"]), T(data["p_d2"]), T(data["p_is3mu"], torch.bool)
    lf = DiscoLoss(0.1)
    gen = torch.Generator(device=device)
    gen.manual_seed(3)
    out = {}
    torch.manual_seed(0)
    base = ParticleNet(**mcfg).to(device)
    for mode in ("eager", "compiled"):
        model = copy.deepcopy(base)
        fwd = torch.compile(model, dynamic=True) if mode == "compiled" else model
        opt = torch.optim.Adam(model.parameters(), lr=1e-4, weight_decay=3e-5)
        dyn.utils.counters.clear()
        torch.cuda.reset_peak_memory_stats(device)

        def step():
            i = torch.randint(0, len(p_ev), (512,), device=device, generator=gen)
            x, b, e0, gx = store.batch(p_ev[i], p_mA[i], k=k, rotate=True, generator=gen)
            loss = lf(fwd(x, b, e0, gx, 512), p_y[i], p_w[i], p_d1[i], p_d2[i], p_3[i])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            return loss

        fwd.train()
        torch.cuda.synchronize(); t = time.time()
        step(); torch.cuda.synchronize()
        t_first = time.time() - t
        for _ in range(10):
            step()
        torch.cuda.synchronize(); t = time.time()
        for _ in range(n_steps):
            step()
        torch.cuda.synchronize()
        t_step = (time.time() - t) / n_steps
        fwd.eval()
        with torch.no_grad():
            i = torch.arange(512, device=device)
            x, b, e0, gx = store.batch(p_ev[i], p_mA[i], k=k)
            fwd(x, b, e0, gx, 512)
            torch.cuda.synchronize(); t = time.time()
            for _ in range(n_steps):
                i = torch.randint(0, len(p_ev), (512,), device=device, generator=gen)
                x, b, e0, gx = store.batch(p_ev[i], p_mA[i], k=k)
                fwd(x, b, e0, gx, 512)
            torch.cuda.synchronize()
            t_eval = (time.time() - t) / n_steps
        out[mode] = {"t_first_step_s": t_first, "t_train_step_ms": 1e3 * t_step, "t_eval_step_ms": 1e3 * t_eval,
                     "max_mem_MB": torch.cuda.max_memory_allocated(device) / 2 ** 20,
                     "graph_breaks": {str(kk): v for kk, v in dyn.utils.counters["graph_break"].items()}}
        out[mode]["_model"] = model
        out[mode]["_fwd"] = fwd
    # eager vs compiled agreement on the same weights (eval)
    m_e = out["eager"]["_model"]
    m_c = copy.deepcopy(m_e)
    f_c = torch.compile(m_c, dynamic=True)
    m_e.eval(); f_c.eval()
    with torch.no_grad():
        i = torch.arange(0, min(2048, len(p_ev)), device=device)
        x, b, e0, gx = store.batch(p_ev[i], p_mA[i], k=k)
        ye = m_e(x, b, e0, gx, int(i.shape[0]))
        yc = f_c(x, b, e0, gx, int(i.shape[0]))
    diff = float((ye - yc).abs().max())
    for mode in out:
        out[mode].pop("_model"); out[mode].pop("_fwd")
    store_mb = (store.x.numel() + store.etaphi.numel()) * 4 / 2 ** 20
    nodes_per_graph = float(data["counts"].mean())
    check("C6_compile", diff < 1e-3, max_abs_logit_diff_eager_vs_compiled=diff,
          graph_breaks_compiled=out["compiled"]["graph_breaks"])
    RES["timing"] = {"batch_size": 512, "steps": n_steps, **out, "bench_store_MB": store_mb,
                     "mean_nodes_per_graph": nodes_per_graph, "num_hidden": mcfg["num_hidden"]}
    print(json.dumps(RES["timing"], indent=1, default=float))


def c7_scores(trees, data, meta, model_dir, score_dir, device):
    win = Windows(meta["windows_file"], meta["points"])
    nets, ck = load_networks(model_dir, device)
    sc = [dict(np.load(os.path.join(model_dir, f"net{j}", "scores.npz"))) for j in range(5)]
    # (1) Train_ trees: score files vs held-out scores of the training jobs
    maxd, n_cmp, own_test, key_ok = 0.0, 0, True, True
    dup = {}  # signal: entries sharing a (run, lumi, event) key
    for si, s in enumerate(meta["samples"]):
        fs = os.path.join(score_dir, f"Skim_TriLep_{s}.root")
        with uproot.open(fs) as fo:
            for ch, cid in (("1E2MU", 0), ("3MU", 1)):
                a = fo[f"Train_{ch}"].arrays()
                with uproot.open(os.path.join(trees, f"Skim_TriLep_{s}.root")) as fi:
                    a_in = fi[f"Train_{ch}"].arrays(["run", "lumi", "event"], library="np")
                # score rows are aligned with the input entries (friend by entry index)
                key_ok &= len(a) == len(a_in["event"]) and all(
                    np.array_equal(ak.to_numpy(a[f]), a_in[f]) for f in ("run", "lumi", "event"))
                keys = np.stack([a_in["run"].astype(np.int64), a_in["lumi"].astype(np.int64),
                                 a_in["event"].astype(np.int64)], 1)
                nuniq = len(np.unique(keys, axis=0))
                if s.startswith("TTToHcToWA"):
                    dup[f"{s.split('-')[1]}_{ch}"] = [int(len(keys)), int(nuniq)]
                ev = np.nonzero((data["ev_sample"] == si) & (data["ev_channel"] == cid))[0]
                for e in ev:
                    row = int(data["ev_entry"][e])
                    assert int(a["event"][row]) == int(data["ev_event"][e])
                    fold = int(data["ev_fold"][e])
                    assert int(a["fold"][row]) == fold
                    pi = np.nonzero(data["p_ev"] == e)[0]
                    mAs = np.asarray(a["score_mA"][row])
                    sco = np.stack([np.asarray(a[f][row]) for f in
                                    ("score_signal", "score_nonprompt", "score_diboson", "score_ttX")], 1)
                    for p in pi:
                        j = int(np.nonzero(np.isclose(mAs, win.mA[data["p_win"][p]]))[0][0])
                        own_test &= bool(sc[fold]["split"][p] == 2)
                        maxd = max(maxd, float(np.abs(sco[j] - sc[fold]["probs"][p]).max()))
                        n_cmp += 1
    has_dup = all(v[1] < v[0] for v in dup.values())
    check("C7a_scores_own_fold_heldout", maxd < 1e-4 and own_test and n_cmp == len(data["p_ev"]) and key_ok
          and has_dup, max_abs_diff_vs_training_heldout=maxd, pairs_compared=n_cmp, n_pairs=int(len(data["p_ev"])),
          all_from_test_split=own_test, rows_aligned_with_input_entries=key_ok,
          signal_entries_vs_distinct_keys=dup)
    # (2) SR lanes: rows, order, windows, and re-scoring with every network
    rows_ok, mA_ok, only_own, n_ev, min_other, n_ambig, max_own = True, True, True, 0, [], 0, 0.0
    files = sorted(f for f in os.listdir(trees) if f.endswith(".root"))
    for fn in files:
        fi, fs = os.path.join(trees, fn), os.path.join(score_dir, fn)
        for nm in pnet_io.list_ntuples(fi, "SR_"):
            a_in = pnet_io.read_ntuple(fi, nm, pnet_io.OBJ_FIELDS + pnet_io.EVT_FIELDS)
            with uproot.open(fs) as fo:
                a_out = fo[nm].arrays()
            rows_ok &= len(a_in) == len(a_out) and np.array_equal(ak.to_numpy(a_in["event"]), ak.to_numpy(a_out["event"]))
            ch = nm.split("_")[1]
            m1, m2 = ak.to_numpy(a_in["mass1"]), ak.to_numpy(a_in["mass2"])
            ref = [win.mA[[i for i in range(win.n) if win.in_window(ch, i, m1[r:r + 1], m2[r:r + 1])[0]]]
                   for r in range(len(a_in))]
            mA_ok &= all(np.allclose(np.asarray(a_out["score_mA"][r]), ref[r]) for r in range(len(a_in)))
            # re-score 40 events with every network
            x, ep, cnt = pnet_io.build_nodes(a_in)
            store = GraphStore(x, ep, cnt, np.cumsum(cnt, dtype=np.int64) - cnt, device)
            take = [r for r in range(len(a_in)) if len(ref[r])][:40]
            for r in take:
                ev_t = torch.full((len(ref[r]),), r, dtype=torch.int64, device=device)
                mA_t = torch.as_tensor(ref[r] / ck["model"]["mA_scale"], dtype=torch.float32, device=device)
                got = np.stack([np.asarray(a_out[f][r]) for f in
                                ("score_signal", "score_nonprompt", "score_diboson", "score_ttX")], 1)
                fold = int(a_out["fold"][r])
                d = [float(np.abs(predict(net, store, ev_t, mA_t, ck["model"]["k"]) - got).max()) for net in nets]
                only_own &= d[fold] < 2e-6
                max_own = max(max_own, d[fold])
                mo = min(d[j] for j in range(5) if j != fold)
                min_other.append(mo)
                n_ambig += mo < 2e-6  # another network reproduces the stored scores as well
                n_ev += 1
    check("C7b_scores_sr_lanes", rows_ok and mA_ok and only_own and n_ambig == 0,
          rows_and_order=rows_ok, score_mA_equals_windows=mA_ok, own_fold_network_matches=only_own,
          max_abs_diff_own_network=max_own, min_abs_diff_other_networks=float(np.min(min_other)),
          median_abs_diff_other_networks=float(np.median(min_other)), n_events_other_network_within_2em6=n_ambig,
          events_rescored=n_ev,
          data_nonprompt_scored=[f for f in files if f.startswith("Skim_TriLep_Muon")])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=1e-3, help="bench learning rate (production: configs/training.json)")
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()
    device = torch.device("cuda")
    wd = args.work_dir
    trees, dset, mdir, sdir = (os.path.join(wd, d) for d in ("trees", "dataset", "train", "scores"))
    py = os.path.join(PNET, "python")
    RES["times_s"] = {}
    RES["times_s"]["make_trees"] = sh([os.path.join(HERE, "make_synthetic_trees.py"), "--out-dir", trees,
                                       "--points", *POINTS])
    RES["times_s"]["build"] = sh([os.path.join(py, "build_dataset.py"), "--input-dir", trees, "--out-dir", dset,
                                  "--points", *POINTS])
    data, meta = load_dataset(dset)
    ccfg = json.load(open(os.path.join(PNET, "configs", "classes.json")))
    RES["dataset"] = json.load(open(os.path.join(dset, "stats.json")))["classes"]
    c1_inputs(trees, data, meta, ccfg)
    c2_nodes(trees, data, meta)
    c3_windows(data, meta)
    c4_weights(data, meta)
    c5_disco(data, meta, device)
    cfg = json.load(open(os.path.join(PNET, "configs", "training.json")))
    c6_compile_and_timing(data, meta, cfg, device)
    bcfg = copy.deepcopy(cfg)
    bcfg["optimizer"]["initLR"] = args.lr
    os.makedirs(wd, exist_ok=True)
    cpath = os.path.join(wd, "training_bench.json")
    json.dump(bcfg, open(cpath, "w"), indent=1)
    if not args.skip_train:
        RES["times_s"]["train_5nets"] = sh([os.path.join(py, "train.py"), "--dataset", dset, "--out-dir", mdir,
                                            "--config", cpath, "--net", "all", "--max-epochs", str(args.epochs)])
    files = sorted(os.path.join(trees, f) for f in os.listdir(trees) if f.endswith(".root"))
    RES["times_s"]["score"] = sh([os.path.join(py, "score.py"), "--model-dir", mdir, "--out-dir", sdir,
                                  "--prefixes", "SR_", "Train_", "--", *files])
    c7_scores(trees, data, meta, mdir, sdir, device)
    tr = []
    for j in range(5):
        mt = json.load(open(os.path.join(mdir, f"net{j}", "metrics.json")))
        tr.append({"net": j, "epochs": mt["epochs"], "t_epoch_train_s": mt["t_epoch_train_mean_s"],
                   "t_epoch_es_s": mt["t_epoch_es_mean_s"], "max_mem_MB": mt["max_mem_MB"],
                   "n_pairs_split": mt["n_pairs_split"], "auc_test_all": mt["auc"]["test"]["all"]["all_bkg"],
                   "auc_test_per_window": {w: v["all_bkg"] for w, v in mt["auc"]["test"].items()},
                   "dcor_es": mt["dcor_es"]})
    RES["training"] = tr
    RES["all_pass"] = all(v["pass"] for v in RES["checks"].values())
    json.dump(RES, open(os.path.join(wd, "bench_results.json"), "w"), indent=1, default=float)
    print("ALL PASS" if RES["all_pass"] else "SOME CHECKS FAILED",
          {k: v["pass"] for k, v in RES["checks"].items()})


if __name__ == "__main__":
    main()
