"""Training of the 2024 parametric ParticleNet: one network per mA band, 5-fold cross-training
(docs/PLAN_ParticleNet.md step 3; P7, P8, P11; user decisions 2026-11-28: bands, random background mA).

--dataset is a band data set (<build>/<band>) or the build directory with bands.json (then every band is
trained, models in <out_dir>/<band>/). Network j of a band (--net j or all): test fold j (never seen),
early-stopping fold (j + 1) % 5, training on the other three (python/weights.py); the training weights are
the physical weights rescaled per split and class so that signal and every background class have equal
totals (P11). Graph parameter: the entry's mA (signal generated, background drawn) / mA_scale. Loss CE +
0.1 [dCor(s_sig, Delta_1) + dCor(s_sig, Delta_2 | mu mu mu)] over the background of each batch
(python/losses.py). Fixed hyperparameters of configs/training.json; FP32; optional torch.compile.
Early stopping on the ES loss (patience 10), the best ES-loss state is kept.

Outputs in <out_dir>/net<j>/:
  model.pt        state_dict + model config + band (name, lo, hi), points / mA, classes (score.py reads it);
  history.json    per epoch: train / ES loss, CE, dCor_1, dCor_2, weighted accuracy, ES AUC, lr, times;
  weights.json    the rescaling table per split (target T_s, per-class n, sum w, factor);
  scores.npz      softmax scores of every training-table entry at its own mA, its split for this network
                  (0 train, 1 ES, 2 test) and its training weight;
  window_scores.npz  template-window evaluation: for every point i of the band, the entries of the window
                  of point i (template pairing; background and the signal of point i) scored at mA_i, as the
                  templates use them: ev (entry), point, probs, split;
  metrics.json    AUC on the training table per split; per point and split on the template windows: AUC
                  signal vs all background and vs each class (physical weights); KS train vs test of s_sig
                  per class and point; dCor(s_sig, Delta_k(mA_i)) of the ES background per point; timing, memory.
Plots are made elsewhere (Common/Tools/plotter.py in NanoV15) from these JSON / npz files.

Run: micromamba run -n PNet python ParticleNet/python/train.py --dataset DIR --out-dir DIR [--net all]
"""
import argparse
import copy
import json
import logging
import os
import shutil
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gpu_data import GraphStore  # noqa: E402
from losses import DiscoLoss  # noqa: E402
from metrics import dcor_np, weighted_auc, weighted_ks  # noqa: E402
from model import ParticleNet  # noqa: E402
import weights as wmod  # noqa: E402
from bands import Bands  # noqa: E402
from windows import Windows  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(os.path.dirname(HERE), "configs")


def load_dataset(d):
    data = dict(np.load(os.path.join(d, "dataset.npz")))
    meta = json.load(open(os.path.join(d, "meta.json")))
    return data, meta


@torch.no_grad()
def predict(model, store, ev, mA_norm, k, batch_size=4096):
    """Softmax scores (numpy [n, C]) of the graphs (events ev, parameters mA_norm) with `model` in eval mode."""
    model.eval()
    out = []
    for i in range(0, len(ev), batch_size):
        e = ev[i:i + batch_size]
        x, b, e0, gx = store.batch(e, mA_norm[i:i + batch_size], k=k)
        out.append(torch.softmax(model(x, b, e0, gx, int(e.shape[0])), 1))
    return torch.cat(out).cpu().numpy() if out else np.zeros((0, 4), np.float32)


def make_model(mcfg, device):
    return ParticleNet(**mcfg).to(device).float()


def train_one(net, data, meta, cfg, out_dir, device, max_epochs=None, compile_model=None):
    tcfg, mcfg = cfg["training"], cfg["model"]
    nf = tcfg["n_folds"]
    seed = tcfg["seed"] + net
    torch.manual_seed(seed)
    np.random.seed(seed)
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    odir = os.path.join(out_dir, f"net{net}")
    os.makedirs(odir, exist_ok=True)
    k, bs = mcfg["k"], tcfg["batch_size"]
    nC = mcfg["num_classes"]

    # splits and P11 weights
    split = wmod.split_of(data["p_fold"], net, nf)
    wtrain, table = wmod.rescale(data["p_weight"], data["p_label"], np.zeros(len(split), np.int64), split, nC, 1)
    json.dump(table, open(os.path.join(odir, "weights.json"), "w"), indent=1)

    if data["counts"].min() < k + 1:
        raise ValueError(f"graphs with fewer than k + 1 = {k + 1} nodes")
    torch.cuda.reset_peak_memory_stats(device)
    store = GraphStore(data["x"], data["etaphi"], data["counts"], data["offsets"], device)
    T = lambda a, dt: torch.as_tensor(np.ascontiguousarray(a), dtype=dt, device=device)
    p_ev = T(data["p_ev"], torch.int64)
    p_mA = T(data["p_mA"] / mcfg["mA_scale"], torch.float32)
    p_y = T(data["p_label"], torch.int64)
    p_w = T(wtrain, torch.float32)
    p_d1, p_d2 = T(data["p_d1"], torch.float32), T(data["p_d2"], torch.float32)
    p_3 = T(data["p_is3mu"], torch.bool)
    tr_idx = torch.nonzero(T(split == 0, torch.bool)).view(-1)
    es_idx = torch.nonzero(T(split == 1, torch.bool)).view(-1)

    model = make_model(mcfg, device)
    use_compile = tcfg["compile"] if compile_model is None else compile_model
    fwd = torch.compile(model, dynamic=True) if use_compile else model
    ocfg, scfg = cfg["optimizer"], cfg["scheduler"]
    assert ocfg["name"] == "Adam" and scfg["name"] == "ReduceLROnPlateau"
    opt = torch.optim.Adam(model.parameters(), lr=ocfg["initLR"], weight_decay=ocfg["weight_decay"])
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=scfg["factor"],
                                                       patience=scfg["patience"])
    lossfn = DiscoLoss(tcfg["disco_lambda"])

    def run(idx, train):
        """One pass over the pairs idx; returns (loss, ce, dc1, dc2, acc, auc, n_batches)."""
        fwd.train(train)
        if train:
            idx = idx[torch.randperm(len(idx), device=device, generator=gen)]
            B = tcfg["batch_size"]
        else:
            B = tcfg["eval_batch_size"]
        nb = len(idx) // B if (train and tcfg["drop_last"]) else (len(idx) + B - 1) // B
        acc = torch.zeros(6, device=device)  # loss, ce, dc1, dc2, correct w, sum w
        probs = []
        for b in range(nb):
            i = idx[b * B:(b + 1) * B]
            with torch.set_grad_enabled(train):
                x, bt, e0, gx = store.batch(p_ev[i], p_mA[i], k=k, rotate=train and tcfg["augment_phi_rotation"],
                                            generator=gen)
                logits = fwd(x, bt, e0, gx, int(i.shape[0]))
                loss, ce, d1, d2 = lossfn(logits, p_y[i], p_w[i], p_d1[i], p_d2[i], p_3[i], return_parts=True)
            if train:
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
            else:
                probs.append(torch.softmax(logits.detach(), 1)[:, 0])
            wi = p_w[i]
            acc += torch.stack([loss.detach(), ce, d1, d2,
                                ((logits.detach().argmax(1) == p_y[i]) * wi).sum(), wi.abs().sum()])
        a = (acc / max(nb, 1)).tolist()
        res = {"loss": a[0], "ce": a[1], "dcor1": a[2], "dcor2": a[3], "acc": a[4] / max(a[5], 1e-12),
               "n_batches": nb}
        if not train and probs:
            s = torch.cat(probs).cpu().numpy()
            ii = idx.cpu().numpy()
            res["auc"] = weighted_auc(s, data["p_label"][ii] == 0, wtrain[ii])
        return res

    hist, best, best_state, bad = [], float("inf"), None, 0
    nep = max_epochs or tcfg["max_epochs"]
    t_start = time.time()
    for ep in range(nep):
        torch.cuda.synchronize()
        t0 = time.time()
        tr = run(tr_idx, True)
        torch.cuda.synchronize()
        t1 = time.time()
        es = run(es_idx, False)
        torch.cuda.synchronize()
        t2 = time.time()
        sched.step(tr["loss"] if scfg.get("monitor", "train_loss") == "train_loss" else es["loss"])
        rec = {"epoch": ep, "train": tr, "es": es, "lr": opt.param_groups[0]["lr"], "t_train": t1 - t0,
               "t_es": t2 - t1, "max_mem_MB": torch.cuda.max_memory_allocated(device) / 2 ** 20}
        hist.append(rec)
        logging.info("%s net%d ep %3d train %.4f (ce %.4f dc %.3f/%.3f acc %.3f) es %.4f (acc %.3f auc %.4f) "
                     "lr %.1e %.1fs+%.1fs", meta["band"], net, ep, tr["loss"], tr["ce"], tr["dcor1"], tr["dcor2"], tr["acc"],
                     es["loss"], es["acc"], es.get("auc", float("nan")), rec["lr"], t1 - t0, t2 - t1)
        if es["loss"] < best:
            best, bad = es["loss"], 0
            best_state = copy.deepcopy({kk: v.detach().cpu() for kk, v in model.state_dict().items()})
            rec["best"] = True
        else:
            bad += 1
            if bad >= tcfg["patience"]:
                logging.info("%s net%d early stop at epoch %d", meta["band"], net, ep)
                break
    t_train = time.time() - t_start
    model.load_state_dict(best_state)
    ck = {"state_dict": best_state, "model": mcfg, "points": meta["points"], "mA": meta["mA"],
          "classes": meta["classes"], "net": net, "n_folds": nf, "best_es_loss": best,
          "epochs": len(hist), "windows_file": meta["windows_file"], "band": meta["band"],
          "band_lo": meta["band_lo"], "band_hi": meta["band_hi"]}
    torch.save(ck, os.path.join(odir, "model.pt"))
    json.dump(hist, open(os.path.join(odir, "history.json"), "w"), indent=1)

    # scores of every pair with the best state (eager model: identical weights)
    t0 = time.time()
    probs = predict(model, store, p_ev, p_mA, k)
    t_pred = time.time() - t0
    np.savez(os.path.join(odir, "scores.npz"), probs=probs.astype(np.float32), split=split,
             wtrain=wtrain.astype(np.float32))
    t1 = time.time()
    wev, wpt, wprobs = window_eval(model, store, data, meta, k, mcfg["mA_scale"], device)
    np.savez(os.path.join(odir, "window_scores.npz"), ev=wev, point=wpt, probs=wprobs.astype(np.float32),
             split=split[wev])
    t_pred += time.time() - t1
    metrics = evaluate(probs, split, wtrain, data, meta, tcfg, wev, wpt, wprobs)
    metrics.update({"net": net, "epochs": len(hist), "best_es_loss": best, "t_train_s": t_train,
                    "t_epoch_train_mean_s": float(np.mean([h["t_train"] for h in hist])),
                    "t_epoch_es_mean_s": float(np.mean([h["t_es"] for h in hist])),
                    "t_predict_all_s": t_pred, "n_pairs_split": [int((split == s).sum()) for s in range(3)],
                    "max_mem_MB": torch.cuda.max_memory_allocated(device) / 2 ** 20, "compiled": bool(use_compile)})
    json.dump(metrics, open(os.path.join(odir, "metrics.json"), "w"), indent=1)
    return model, metrics


def window_eval(model, store, data, meta, k, scale, device):
    """Entries of every template window of the band's points (background + the signal of that point),
    scored at the point's mA: (entry, point, probs)."""
    win = Windows(meta["windows_file"], meta["points"])
    evs, pts = [], []
    for i in range(win.n):
        for ch, cid in meta["channels"].items():
            m = (data["ev_channel"] == cid) & ((data["ev_label"] != 0) | (data["ev_point"] == i))
            m &= win.in_window(ch, i, data["ev_mass1"], data["ev_mass2"])
            e = np.nonzero(m)[0]
            evs.append(e), pts.append(np.full(len(e), i, np.int16))
    ev, pt = np.concatenate(evs), np.concatenate(pts)
    probs = predict(model, store, torch.as_tensor(ev, device=device),
                    torch.as_tensor(win.mA[pt] / scale, dtype=torch.float32, device=device), k)
    return ev, pt, probs


def evaluate(probs, split, wtrain, data, meta, tcfg, wev, wpt, wprobs):
    """AUCs on the training table; per point on the template windows: AUCs (physical weights), KS train vs
    test of s_sig per class, dCor(s_sig, Delta_k(mA_i)) on the ES background."""
    cls = meta["classes"]
    lab, wph = data["p_label"], data["p_weight"]
    out = {"auc_table": {}, "auc_window": {}, "ks_train_vs_test": {}, "dcor_es": {}}
    s = probs[:, 0]
    for sp, sn in enumerate(("train", "es", "test")):
        m = split == sp
        out["auc_table"][sn] = weighted_auc(s[m], lab[m] == 0, wph[m])
    win = Windows(meta["windows_file"], meta["points"])
    ws, wl, wsp, ww = wprobs[:, 0], lab[wev], split[wev], wph[wev]
    for sp, sn in enumerate(("train", "es", "test")):
        d = {}
        for i, pn in enumerate(meta["points"]):
            m = (wsp == sp) & (wpt == i)
            e = {"all_bkg": weighted_auc(ws[m], wl[m] == 0, ww[m])}
            for c in range(1, len(cls)):
                mm = m & ((wl == 0) | (wl == c))
                e[cls[c]] = weighted_auc(ws[mm], wl[mm] == 0, ww[mm])
            d[pn] = e
        out["auc_window"][sn] = d
    for i, pn in enumerate(meta["points"]):
        d = {}
        for c, cn in enumerate(cls):
            a = (wsp == 0) & (wpt == i) & (wl == c)
            b = (wsp == 2) & (wpt == i) & (wl == c)
            ks, p = weighted_ks(ws[a], np.abs(ww[a]), ws[b], np.abs(ww[b]))
            d[cn] = {"ks": ks, "p": p, "n_train": int(a.sum()), "n_test": int(b.sum())}
        out["ks_train_vs_test"][pn] = d
        m = (wsp == 1) & (wpt == i) & (wl != 0)
        e = wev[m]
        dd = {}
        for ch, cid in meta["channels"].items():
            mc = data["ev_channel"][e] == cid
            d1, d2 = win.deltas(ch, win.mA[i], data["ev_mass1"][e[mc]], data["ev_mass2"][e[mc]])
            dd[ch] = (mc, d1, d2)
        d1 = np.zeros(len(e), np.float32)
        d2 = np.zeros(len(e), np.float32)
        for ch, (mc, a1, a2) in dd.items():
            d1[mc], d2[mc] = a1, a2
        m3 = data["p_is3mu"][e]
        w_ = np.abs(wtrain[e])
        mx = tcfg["monitor_dcor_max_events"]
        out["dcor_es"][pn] = {"delta1": dcor_np(ws[m], d1, w_, mx), "delta2_3mu": dcor_np(ws[m][m3], d2[m3], w_[m3], mx),
                              "n_bkg": int(m.sum()), "n_bkg_3mu": int(m3.sum())}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--config", default=os.path.join(CFG, "training.json"))
    ap.add_argument("--net", default="all", help="network index 0..4 or 'all'")
    ap.add_argument("--max-epochs", type=int, default=None, help="override (tests)")
    ap.add_argument("--no-compile", action="store_true")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = json.load(open(args.config))
    if os.path.exists(os.path.join(args.dataset, "bands.json")):  # build directory: every band
        os.makedirs(args.out_dir, exist_ok=True)
        shutil.copy(os.path.join(args.dataset, "bands.json"), os.path.join(args.out_dir, "bands.json"))
        jobs = [(os.path.join(args.dataset, b), os.path.join(args.out_dir, b))
                for b in Bands(os.path.join(args.dataset, "bands.json")).names
                if os.path.exists(os.path.join(args.dataset, b, "dataset.npz"))]
    else:
        jobs = [(args.dataset, args.out_dir)]
    nets = range(cfg["training"]["n_folds"]) if args.net == "all" else [int(args.net)]
    for dset, odir in jobs:
        data, meta = load_dataset(dset)
        os.makedirs(odir, exist_ok=True)
        json.dump({"config": cfg, "dataset": os.path.abspath(dset)},
                  open(os.path.join(odir, "train_config.json"), "w"), indent=1)
        for j in nets:
            logging.info("band %s network %d", meta["band"], j)
            train_one(j, data, meta, cfg, odir, torch.device(args.device), args.max_epochs,
                      False if args.no_compile else None)


if __name__ == "__main__":
    main()
