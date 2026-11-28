"""End-to-end synthetic bench of the 2024 ParticleNet chain: three band networks x 5 folds
(docs/PLAN_ParticleNet.md steps 2-4; user decisions 2026-11-28).

Runs on the local GPU (micromamba run -n PNet): synthetic trees with signal points in all three bands
(test/make_synthetic_trees.py; signal with run = lumi = 1 and repeated event numbers) -> band data sets
(python/build_dataset.py, twice for the reproducibility check) -> 5-fold training of every band for a few
epochs (python/train.py) -> offline scoring of the SR_ and Train_ RNTuples at the MC grid and at a few
interpolated grid points (python/score.py), and checks:
  C1 inputs: per band and sample the entries / weight sums equal an independent selection of the trees
     (signal: passSR of the band's points; background: the class selection and the A-candidate mass in one of
     the band's windows); RNTuple and TTree inputs; fold = event % 5; nonprompt weights > 0.
  C2 nodes (onZ band): E, px, py, pz recomputed from the tree fields, the flags, the pair masses from the
     nodes = mass1 / mass2; first-layer edges = brute-force Delta R 4-NN.
  C3 band membership: every background entry lies in the union of its band's windows, every selected
     background event in that union is present once per band; the events in two bands are exactly the
     band-a entries inside band b's union (per channel; 3MU can be in belowZ and aboveZ through its two
     pairings, 1E2MU not when the ranges are disjoint); every signal
     event of the band's points present once with its generated mA; drawn mA only at the band's points.
  C3b random mA: a second build gives identical drawn mA and uniforms; the uniforms equal an independent
     recomputation of the hash; the drawn-mA fractions per channel agree with the draw probabilities
     (signal weight totals per point) within 4 sigma; Delta_k = (m_k - mA) / sigma_eff(mA) recomputed with an
     independent linear interpolation; Delta_2 = 0 for 1E2MU.
  C4 weights (P11): for every band, network and split the four class totals are equal (T_s), T_s x n_cells =
     N_s, the factor is constant within a class (physical weights kept), the splits follow P8.
  C5 DisCo mask: the Delta_2 term is unchanged when the e mu mu Delta_2 values are replaced by noise, its
     gradient w.r.t. the e mu mu logits is zero, it equals the weighted dCor over the mu mu mu background
     alone; the Delta_1 term ignores the signal events.
  C6 torch.compile: compiled vs eager outputs agree, graph breaks; timing (T).
  C7a scoring vs training: every template-window entry of every band (window_scores.npz of the training,
     background + the point's signal at mA_i) is found by entry index in the Train_ score files at mA_i with
     the score of the network of its band and fold, which is that network's held-out (test) score; score rows
     aligned with the input entries; signal keys repeated.
  C7b SR lanes: rows and order, score_mA = the grid windows containing the event, re-scoring with all 15
     networks matches only the network of (band of the grid mA, fold).
  C7c interpolated grid (configs/windows_grid.json, points across the band edges): band routing as C7b.
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
from bands import Bands, uniform_hash  # noqa: E402

POINTS = ["MHc130_MA15", "MHc130_MA30", "MHc130_MA55", "MHc130_MA65", "MHc130_MA85", "MHc130_MA90",
          "MHc130_MA105", "MHc130_MA120"]
GRID_EXTRA = ["MHc130_MA17p5", "MHc130_MA62p5", "MHc130_MA79p5", "MHc130_MA80", "MHc130_MA99p5", "MHc130_MA100",
              "MHc130_MA122"]
BANDS = ("belowZ", "onZ", "aboveZ")
RES = {"checks": {}}


def check(name, ok, **info):
    RES["checks"][name] = {"pass": bool(ok), **info}
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {json.dumps(info, default=float)[:400]}")


def sh(args):
    print("+", " ".join(args))
    t = time.time()
    subprocess.run([sys.executable] + args, check=True)
    return time.time() - t


def c1_inputs(trees, D, ccfg):
    ok, info = True, {}
    for bn, (data, meta) in D.items():
        win = Windows(meta["windows_file"], meta["points"])  # the band's points
        for si, s in enumerate(meta["samples"]):
            cls = next(c for c in ccfg["classes"] if (c["samples"] == "signal" and s.startswith("TTToHcToWA"))
                       or (isinstance(c["samples"], list) and s in c["samples"]))
            if cls["samples"] == "signal" and s.split("-")[1] not in meta["points"]:
                ref_n = ref_w = 0
            else:
                ref_n = ref_w = 0
                with uproot.open(os.path.join(trees, f"Skim_TriLep_{s}.root")) as fo:
                    for ch in ("1E2MU", "3MU"):
                        a = fo[f"Train_{ch}"].arrays(["passSR", "allTight", "nBJets", "weight_genpu", "weight_fake",
                                                      "mass1", "mass2"], library="np")
                        if cls["selection"] == "passSR":
                            m, w = a["passSR"].astype(bool), a["weight_genpu"].astype(np.float64)
                        else:
                            w = a["weight_genpu"].astype(np.float64) * a["weight_fake"]
                            m = ~a["allTight"].astype(bool) & (a["nBJets"] >= 1) & (w > 0)
                        if cls["samples"] != "signal":
                            inb = np.zeros(len(m), bool)
                            for i in range(win.n):
                                inb |= win.in_window(ch, i, a["mass1"], a["mass2"])
                            m &= inb
                        ref_n += int(m.sum()); ref_w += float(w[m].sum())
            sel = data["ev_sample"] == si
            n, sw = int(sel.sum()), float(data["ev_weight"][sel].sum())
            ok &= n == ref_n and abs(sw - ref_w) <= 1e-6 * max(1.0, abs(ref_w))
            info.setdefault(bn, {})[s] = [n, ref_n]
        ok &= np.array_equal(data["ev_fold"], (data["ev_event"] % np.uint64(5)).astype(np.int8))
        ok &= bool((data["ev_weight"][data["ev_label"] == 1] > 0).all())
    check("C1_inputs", ok, entries_vs_reference=info, ttree_sample="ZZto4L")

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


def c3_bands(D, D2, meta_all):
    chn = {0: "1E2MU", 1: "3MU"}
    ok, info, keysets = True, {}, {}
    for bn, (data, meta) in D.items():
        win = Windows(meta["windows_file"], meta["points"])
        bkg = data["ev_label"] != 0
        inb = np.zeros(len(bkg), bool)
        for c, ch in chn.items():
            sc = data["ev_channel"] == c
            for i in range(win.n):
                inb[sc] |= win.in_window(ch, i, data["ev_mass1"][sc], data["ev_mass2"][sc])
        in_union = bool(inb[bkg].all())
        keys = data["ev_sample"].astype(np.int64) * 10 ** 12 + data["ev_channel"].astype(np.int64) * 10 ** 11 \
            + data["ev_entry"]
        once = len(np.unique(keys)) == len(keys)
        keysets[bn] = set(keys[bkg].tolist())
        sig = ~bkg
        sig_mA = bool(np.allclose(data["p_mA"][sig], win.mA[data["ev_point"][sig]]))
        drawn_ok = bool(np.isin(np.round(data["p_mA"][bkg], 4), np.round(win.mA, 4)).all())
        ok &= in_union and once and sig_mA and drawn_ok
        info[bn] = {"bkg_in_union": in_union, "one_entry_per_event": once, "signal_generated_mA": sig_mA,
                    "drawn_mA_at_band_points": drawn_ok, "entries": int(len(keys)), "bkg": int(bkg.sum())}
    # two-band events: the background entries of band a whose masses also lie in band b's union must be exactly
    # the events present in both data sets (the 3MU low / high pairings allow belowZ & aboveZ events; for 1E2MU
    # (one pairing) none when the two ranges are disjoint)
    def union(data, meta_b, sel):
        wb = Windows(meta_b["windows_file"], meta_b["points"])
        m = np.zeros(len(sel), bool)
        for c, ch in chn.items():
            sc = sel & (data["ev_channel"] == c)
            for i in range(wb.n):
                m[sc] |= wb.in_window(ch, i, data["ev_mass1"][sc], data["ev_mass2"][sc])
        return m
    two, two_ok = {}, True
    for a, b in (("belowZ", "onZ"), ("onZ", "aboveZ"), ("belowZ", "aboveZ")):
        da, ma = D[a]
        keys_a = da["ev_sample"].astype(np.int64) * 10 ** 12 + da["ev_channel"].astype(np.int64) * 10 ** 11 \
            + da["ev_entry"]
        exp = union(da, D[b][1], da["ev_label"] != 0)
        got = keysets[a] & keysets[b]
        two_ok &= set(keys_a[exp].tolist()) == got
        two[f"{a}&{b}"] = {ch: int((exp & (da["ev_channel"] == c)).sum()) for c, ch in chn.items()}
    wb_lo, wb_hi = (Windows(D[x][1]["windows_file"], D[x][1]["points"]) for x in ("belowZ", "aboveZ"))
    disjoint_1e2mu = wb_lo.ch["1E2MU"]["hi"].max() < wb_hi.ch["1E2MU"]["lo"].min()
    if disjoint_1e2mu:
        two_ok &= two["belowZ&aboveZ"]["1E2MU"] == 0
    info["bkg_events_in_two_bands"] = two
    info["two_band_sets_equal_independent_union"] = bool(two_ok)
    info["1E2MU_belowZ_aboveZ_ranges_disjoint"] = bool(disjoint_1e2mu)
    ok &= two_ok and two["belowZ&onZ"]["1E2MU"] + two["belowZ&onZ"]["3MU"] > 0
    check("C3_band_membership", ok, **info)
    # random mA: reproducibility, hash, fractions, deltas
    rep, hashok, frac_ok, dok, dmask, fr = True, True, True, True, True, {}
    for b, (bn, (data, meta)) in enumerate(D.items()):
        d2 = D2[bn][0]
        rep &= np.array_equal(data["p_mA"], d2["p_mA"]) and np.array_equal(data["ev_u"], d2["ev_u"])
        bkg = data["ev_label"] != 0
        bi = Bands(meta["bands_file"]).names.index(bn)
        for si, sname in enumerate(meta["samples"]):
            for c in (0, 1):
                m = bkg & (data["ev_sample"] == si) & (data["ev_channel"] == c)
                if m.any():
                    u = uniform_hash(sname, c, data["ev_entry"][m], data["ev_event"][m], bi)
                    hashok &= np.array_equal(u, data["ev_u"][m])
        win = Windows(meta["windows_file"], meta["points"])
        for c, ch in chn.items():
            m = bkg & (data["ev_channel"] == c)
            prob = np.asarray(meta["draw_prob"][ch])
            f = np.array([np.isclose(data["p_mA"][m], v).mean() for v in win.mA])
            tol = 4 * np.sqrt(prob * (1 - prob) / max(1, m.sum())) + 1e-9
            frac_ok &= bool((np.abs(f - prob) <= tol).all())
            fr[f"{bn}_{ch}"] = {"n": int(m.sum()), "prob": [round(x, 3) for x in prob], "frac": [round(x, 3) for x in f]}
            # deltas, independent interpolation (sorted points)
            sc = data["ev_channel"] == c
            xs, ys = Windows(meta["windows_file"]).mA, Windows(meta["windows_file"]).ch[ch]["sigma"]
            o = np.argsort(xs)
            sg = np.interp(data["p_mA"][sc].astype(np.float64), xs[o], ys[o])
            r1 = (data["ev_mass1"][sc] - data["p_mA"][sc].astype(np.float64)) / sg
            dok &= bool(np.allclose(r1, data["p_d1"][sc], rtol=1e-5, atol=1e-4))
            if ch == "3MU":
                r2 = (data["ev_mass2"][sc] - data["p_mA"][sc].astype(np.float64)) / sg
                dok &= bool(np.allclose(r2, data["p_d2"][sc], rtol=1e-5, atol=1e-4))
            else:
                dmask &= bool((data["p_d2"][sc] == 0).all())
    check("C3b_random_mA", rep and hashok and frac_ok and dok and dmask, reproducible_rebuild=rep,
          hash_recomputed=hashok, fractions_within_4sigma=frac_ok, deltas=dok, delta2_zero_for_1e2mu=dmask,
          fractions=fr)

def c4_weights(D):
    ok, info = True, {}
    for bn, (data, meta) in D.items():
        for net in range(5):
            split = wmod.split_of(data["p_fold"], net)
            f = data["p_fold"].astype(int)
            ok &= bool((split[f == net] == 2).all() and (split[f == (net + 1) % 5] == 1).all()
                       and (split[(f != net) & (f != (net + 1) % 5)] == 0).all())
            wt, table = wmod.rescale(data["p_weight"], data["p_label"], np.zeros(len(split), np.int64), split, 4, 1)
            for s in range(3):
                m = split == s
                T = table[wmod.SPLITS[s]]["target"]
                tots = []
                for c in range(4):
                    cm = m & (data["p_label"] == c)
                    if cm.sum() == 0:
                        continue
                    tots.append(wt[cm].sum())
                    r = wt[cm] / data["p_weight"][cm]
                    ok &= bool(np.allclose(r, r[0], rtol=1e-9))
                tots = np.array(tots)
                ok &= bool(np.allclose(tots, T, rtol=1e-9)) and abs(T * len(tots) - m.sum()) < 1e-6 * m.sum()
                ok &= len(tots) == 4 and not table[wmod.SPLITS[s]]["bad_cells"]
                if net == 0:
                    info[f"{bn}_net0_{wmod.SPLITS[s]}"] = {"target": T, "class_totals": tots.tolist(),
                                                          "n": int(m.sum())}
    check("C4_weights", ok, **info)

def c5_disco(data, meta, device):
    torch.manual_seed(0)
    split = wmod.split_of(data["p_fold"], 0)
    wt, _ = wmod.rescale(data["p_weight"], data["p_label"], np.zeros(len(split), np.int64), split, 4, 1)
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
    wt, _ = wmod.rescale(data["p_weight"], data["p_label"], np.zeros(len(split), np.int64), split, 4, 1)
    mA = data["p_mA"] / mcfg["mA_scale"]
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


def _scores_row(a, row):
    mAs = np.asarray(a["score_mA"][row])
    sco = np.stack([np.asarray(a[f][row]) for f in ("score_signal", "score_nonprompt", "score_diboson", "score_ttX")], 1)
    return mAs, sco


def c7_scores(trees, D, model_dir, score_dir, device):
    nets, bands, ck = load_networks(model_dir, device)
    # (a) template-window entries of the training jobs vs the Train_ score files (by entry index)
    maxd, n_cmp, own_test, key_ok, dup = 0.0, 0, True, True, {}
    cache = {}
    for bn, (data, meta) in D.items():
        win = Windows(meta["windows_file"], meta["points"])
        ws = [dict(np.load(os.path.join(model_dir, bn, f"net{j}", "window_scores.npz"))) for j in range(5)]
        assert all(np.array_equal(ws[0]["ev"], w["ev"]) and np.array_equal(ws[0]["point"], w["point"]) for w in ws)
        ev, pt = ws[0]["ev"], ws[0]["point"]
        for q in range(len(ev)):
            e = ev[q]
            s = meta["samples"][data["ev_sample"][e]]
            ch = "1E2MU" if data["ev_channel"][e] == 0 else "3MU"
            if (s, ch) not in cache:
                with uproot.open(os.path.join(score_dir, f"Skim_TriLep_{s}.root")) as fo:
                    a = fo[f"Train_{ch}"].arrays()
                with uproot.open(os.path.join(trees, f"Skim_TriLep_{s}.root")) as fi:
                    a_in = fi[f"Train_{ch}"].arrays(["run", "lumi", "event"], library="np")
                key_ok &= len(a) == len(a_in["event"]) and all(
                    np.array_equal(ak.to_numpy(a[f]), a_in[f]) for f in ("run", "lumi", "event"))
                if s.startswith("TTToHcToWA"):
                    keys = np.stack([a_in[f].astype(np.int64) for f in ("run", "lumi", "event")], 1)
                    dup[f"{s.split('-')[1]}_{ch}"] = [int(len(keys)), int(len(np.unique(keys, axis=0)))]
                cache[(s, ch)] = a
            a = cache[(s, ch)]
            row = int(data["ev_entry"][e])
            assert int(a["event"][row]) == int(data["ev_event"][e])
            fold = int(data["ev_fold"][e])
            mAs, sco = _scores_row(a, row)
            j = int(np.nonzero(np.isclose(mAs, win.mA[pt[q]]))[0][0])
            own_test &= bool(ws[fold]["split"][q] == 2)
            maxd = max(maxd, float(np.abs(sco[j] - ws[fold]["probs"][q]).max()))
            n_cmp += 1
    has_dup = bool(dup) and all(v[1] < v[0] for v in dup.values())
    check("C7a_scores_vs_training_heldout", maxd < 1e-4 and own_test and key_ok and has_dup and n_cmp > 0,
          max_abs_diff=maxd, window_entries_compared=n_cmp, all_from_test_split=own_test,
          rows_aligned_with_input_entries=key_ok, signal_entries_vs_distinct_keys=dict(list(dup.items())[:6]))


def rescore_check(name, trees, score_dir, windows_file, grid, model_dir, device, files=None):
    """Rows, order, score_mA = windows, and only the (band, fold) network reproduces the stored scores."""
    nets, bands, ck = load_networks(model_dir, device)
    win = Windows(windows_file, grid)
    gband = bands.band_of(win.mA)
    rows_ok, mA_ok, only_own, n_ev, min_other, n_ambig, max_own, routed = True, True, True, 0, [], 0, 0.0, {}
    files = files or sorted(f for f in os.listdir(trees) if f.endswith(".root"))
    for fn in files:
        fi, fs = os.path.join(trees, fn), os.path.join(score_dir, fn)
        for nm in pnet_io.list_ntuples(fi, "SR_"):
            a_in = pnet_io.read_ntuple(fi, nm, pnet_io.OBJ_FIELDS + pnet_io.EVT_FIELDS)
            with uproot.open(fs) as fo:
                a_out = fo[nm].arrays()
            rows_ok &= len(a_in) == len(a_out) and np.array_equal(ak.to_numpy(a_in["event"]), ak.to_numpy(a_out["event"]))
            ch = nm.split("_")[1]
            m1, m2 = ak.to_numpy(a_in["mass1"]), ak.to_numpy(a_in["mass2"])
            inw = np.stack([win.in_window(ch, i, m1, m2) for i in range(win.n)], 1)
            mA_ok &= all(np.allclose(np.asarray(a_out["score_mA"][r]), win.mA[inw[r]]) for r in range(len(a_in)))
            x, ep, cnt = pnet_io.build_nodes(a_in)
            store = GraphStore(x, ep, cnt, np.cumsum(cnt, dtype=np.int64) - cnt, device)
            take = [r for r in range(len(a_in)) if inw[r].any()][:25]
            for r in take:
                gi = np.nonzero(inw[r])[0]
                mAs, got = _scores_row(a_out, r)
                fold = int(a_out["fold"][r])
                for q, g in enumerate(gi):
                    ev_t = torch.full((1,), r, dtype=torch.int64, device=device)
                    mA_t = torch.as_tensor([win.mA[g] / ck["model"]["mA_scale"]], dtype=torch.float32, device=device)
                    d = {(b, j): float(np.abs(predict(n, store, ev_t, mA_t, ck["model"]["k"])[0] - got[q]).max())
                         for b, lst in nets.items() for j, n in enumerate(lst)}
                    own = (int(gband[g]), fold)
                    only_own &= d[own] < 2e-6
                    max_own = max(max_own, d[own])
                    mo = min(v for kk, v in d.items() if kk != own)
                    min_other.append(mo)
                    n_ambig += mo < 2e-6
                    routed[win.names[g]] = bands.names[gband[g]]
                n_ev += 1
    check(name, rows_ok and mA_ok and only_own and n_ambig == 0 and n_ev > 0,
          rows_and_order=rows_ok, score_mA_equals_windows=mA_ok, own_band_fold_network_matches=only_own,
          max_abs_diff_own=max_own, min_abs_diff_other_14_networks=float(np.min(min_other)),
          median_abs_diff_other=float(np.median(min_other)), n_other_within_2em6=n_ambig,
          events_rescored=n_ev, grid_routing=routed)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=1e-3, help="bench learning rate (production: configs/training.json)")
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()
    device = torch.device("cuda")
    wd = args.work_dir
    trees, dset, dset2, mdir, sdir, sdir2 = (os.path.join(wd, d) for d in
                                             ("trees", "dataset", "dataset_rebuild", "train", "scores", "scores_grid"))
    py = os.path.join(PNET, "python")
    RES["times_s"] = {}
    RES["times_s"]["make_trees"] = sh([os.path.join(HERE, "make_synthetic_trees.py"), "--out-dir", trees,
                                       "--points", *POINTS])
    RES["times_s"]["build"] = sh([os.path.join(py, "build_dataset.py"), "--input-dir", trees, "--out-dir", dset,
                                  "--points", *POINTS])
    sh([os.path.join(py, "build_dataset.py"), "--input-dir", trees, "--out-dir", dset2, "--points", *POINTS])
    D = {b: load_dataset(os.path.join(dset, b)) for b in BANDS}
    D2 = {b: load_dataset(os.path.join(dset2, b)) for b in BANDS}
    ccfg = json.load(open(os.path.join(PNET, "configs", "classes.json")))
    RES["dataset"] = json.load(open(os.path.join(dset, "summary.json")))
    c1_inputs(trees, D, ccfg)
    c2_nodes(trees, *D["onZ"])
    c3_bands(D, D2, None)
    c4_weights(D)
    c5_disco(*D["onZ"], device)
    cfg = json.load(open(os.path.join(PNET, "configs", "training.json")))
    c6_compile_and_timing(*D["onZ"], cfg, device)
    bcfg = copy.deepcopy(cfg)
    bcfg["optimizer"]["initLR"] = args.lr
    os.makedirs(wd, exist_ok=True)
    cpath = os.path.join(wd, "training_bench.json")
    json.dump(bcfg, open(cpath, "w"), indent=1)
    if not args.skip_train:
        RES["times_s"]["train_15nets"] = sh([os.path.join(py, "train.py"), "--dataset", dset, "--out-dir", mdir,
                                             "--config", cpath, "--net", "all", "--max-epochs", str(args.epochs)])
    files = sorted(os.path.join(trees, f) for f in os.listdir(trees) if f.endswith(".root"))
    RES["times_s"]["score_mc_grid"] = sh([os.path.join(py, "score.py"), "--model-dir", mdir, "--out-dir", sdir,
                                          "--prefixes", "SR_", "Train_", "--", *files])
    gfile = os.path.join(PNET, "configs", "windows_grid.json")
    few = [f for f in files if os.path.basename(f) in ("Skim_TriLep_WZto3LNu.root", "Skim_TriLep_TTLL_powheg.root",
                                                       "Skim_TriLep_Muon0_C.root")]
    RES["times_s"]["score_interp_grid"] = sh([os.path.join(py, "score.py"), "--model-dir", mdir, "--out-dir", sdir2,
                                              "--windows", gfile, "--grid", *GRID_EXTRA, "--", *few])
    c7_scores(trees, D, mdir, sdir, device)
    rescore_check("C7b_scores_sr_lanes_mc_grid", trees, sdir, os.path.join(PNET, "configs", "windows.json"), None,
                  mdir, device)
    rescore_check("C7c_scores_interpolated_grid", trees, sdir2, gfile, GRID_EXTRA, mdir, device,
                  [os.path.basename(f) for f in few])
    tr = {}
    for bn in BANDS:
        for j in range(5):
            mt = json.load(open(os.path.join(mdir, bn, f"net{j}", "metrics.json")))
            tr[f"{bn}_net{j}"] = {"epochs": mt["epochs"], "t_epoch_train_s": mt["t_epoch_train_mean_s"],
                                  "t_epoch_es_s": mt["t_epoch_es_mean_s"], "max_mem_MB": mt["max_mem_MB"],
                                  "n_split": mt["n_pairs_split"], "auc_table_test": mt["auc_table"]["test"],
                                  "auc_window_test": {w: v["all_bkg"] for w, v in mt["auc_window"]["test"].items()}}
    RES["training"] = tr
    RES["all_pass"] = all(v["pass"] for v in RES["checks"].values())
    json.dump(RES, open(os.path.join(wd, "bench_results.json"), "w"), indent=1, default=float)
    print("ALL PASS" if RES["all_pass"] else "SOME CHECKS FAILED",
          {k: v["pass"] for k, v in RES["checks"].items()})


if __name__ == "__main__":
    main()
