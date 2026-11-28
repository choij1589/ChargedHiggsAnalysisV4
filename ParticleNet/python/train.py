"""Training of the 2024 parametric ParticleNet, 5-fold cross-training (docs/PLAN_ParticleNet.md step 3; P7, P8, P11).

Network j (--net j, or --net all for 0..4): test fold j (never seen), early-stopping fold (j + 1) % 5,
training on the other three (python/weights.py); training weights rescaled per (split, mA window, class)
(P11). Loss CE + 0.1 [dCor(s_sig, Delta_1) + dCor(s_sig, Delta_2 | mu mu mu)] over the background events
of each batch (python/losses.py). Fixed hyperparameters of configs/training.json (previous best model at
MHc130_MA90); FP32; optional torch.compile(dynamic=True) of the model (k-NN excluded from tracing).
Early stopping on the ES loss (patience 10), the best ES-loss state is kept.

Outputs in <out_dir>/net<j>/:
  model.pt      state_dict + model config + points / mA / mA_scale / classes (python/score.py reads it);
  history.json  per epoch: train / ES loss, CE, dCor_1, dCor_2, weighted accuracy, ES AUC, lr, times;
  weights.json  the rescaling table per split (target T_s, per-cell n, sum w, factor);
  scores.npz    softmax scores [n_pairs, 4] of every pair of the data set with the best state, the split
                of each pair for this network (0 train, 1 ES, 2 test) and the training weight;
  metrics.json  per split and window: AUC signal vs all background and vs each class (physical weights),
                KS train vs test of s_sig per class and window, dCor(s_sig, Delta_k) on background (ES),
                timing and GPU memory.
Plots are made elsewhere (Common/Tools/plotter.py in NanoV15) from these JSON / npz files.

Run: micromamba run -n PNet python ParticleNet/python/train.py --dataset DIR --out-dir DIR --net all
"""
import argparse
import copy
import json
import logging
import os
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
    nC, nW = mcfg["num_classes"], len(meta["points"])
    mA = np.asarray(meta["mA"], np.float64)

    # splits and P11 weights
    split = wmod.split_of(data["p_fold"], net, nf)
    wtrain, table = wmod.rescale(data["p_weight"], data["p_label"], data["p_win"], split, nC, nW)
    json.dump(table, open(os.path.join(odir, "weights.json"), "w"), indent=1)

    if data["counts"].min() < k + 1:
        raise ValueError(f"graphs with fewer than k + 1 = {k + 1} nodes")
    torch.cuda.reset_peak_memory_stats(device)
    store = GraphStore(data["x"], data["etaphi"], data["counts"], data["offsets"], device)
    T = lambda a, dt: torch.as_tensor(np.ascontiguousarray(a), dtype=dt, device=device)
    p_ev = T(data["p_ev"], torch.int64)
    p_mA = T(mA[data["p_win"]] / mcfg["mA_scale"], torch.float32)
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
        logging.info("net%d ep %3d train %.4f (ce %.4f dc %.3f/%.3f acc %.3f) es %.4f (acc %.3f auc %.4f) "
                     "lr %.1e %.1fs+%.1fs", net, ep, tr["loss"], tr["ce"], tr["dcor1"], tr["dcor2"], tr["acc"],
                     es["loss"], es["acc"], es.get("auc", float("nan")), rec["lr"], t1 - t0, t2 - t1)
        if es["loss"] < best:
            best, bad = es["loss"], 0
            best_state = copy.deepcopy({kk: v.detach().cpu() for kk, v in model.state_dict().items()})
            rec["best"] = True
        else:
            bad += 1
            if bad >= tcfg["patience"]:
                logging.info("net%d early stop at epoch %d", net, ep)
                break
    t_train = time.time() - t_start
    model.load_state_dict(best_state)
    ck = {"state_dict": best_state, "model": mcfg, "points": meta["points"], "mA": meta["mA"],
          "classes": meta["classes"], "net": net, "n_folds": nf, "best_es_loss": best,
          "epochs": len(hist), "windows_file": meta["windows_file"]}
    torch.save(ck, os.path.join(odir, "model.pt"))
    json.dump(hist, open(os.path.join(odir, "history.json"), "w"), indent=1)

    # scores of every pair with the best state (eager model: identical weights)
    t0 = time.time()
    probs = predict(model, store, p_ev, p_mA, k)
    t_pred = time.time() - t0
    np.savez(os.path.join(odir, "scores.npz"), probs=probs.astype(np.float32), split=split,
             wtrain=wtrain.astype(np.float32))
    metrics = evaluate(probs, split, wtrain, data, meta, tcfg)
    metrics.update({"net": net, "epochs": len(hist), "best_es_loss": best, "t_train_s": t_train,
                    "t_epoch_train_mean_s": float(np.mean([h["t_train"] for h in hist])),
                    "t_epoch_es_mean_s": float(np.mean([h["t_es"] for h in hist])),
                    "t_predict_all_s": t_pred, "n_pairs_split": [int((split == s).sum()) for s in range(3)],
                    "max_mem_MB": torch.cuda.max_memory_allocated(device) / 2 ** 20, "compiled": bool(use_compile)})
    json.dump(metrics, open(os.path.join(odir, "metrics.json"), "w"), indent=1)
    return model, metrics


def evaluate(probs, split, wtrain, data, meta, tcfg):
    """Per split / window AUCs (physical weights), KS train vs test of s_sig per class, dCor on ES."""
    s = probs[:, 0]
    lab, win, wph = data["p_label"], data["p_win"], data["p_weight"]
    cls = meta["classes"]
    out = {"auc": {}, "ks_train_vs_test": {}, "dcor_es": {}}
    for sp, sn in enumerate(("train", "es", "test")):
        d = {}
        for i, wn in enumerate(meta["points"] + ["all"]):
            m = (split == sp) & ((win == i) if wn != "all" else True)
            e = {"all_bkg": weighted_auc(s[m], lab[m] == 0, wph[m])}
            for c in range(1, len(cls)):
                mm = m & ((lab == 0) | (lab == c))
                e[cls[c]] = weighted_auc(s[mm], lab[mm] == 0, wph[mm])
            d[wn] = e
        out["auc"][sn] = d
    for i, wn in enumerate(meta["points"]):
        d = {}
        for c, cn in enumerate(cls):
            a = (split == 0) & (win == i) & (lab == c)
            b = (split == 2) & (win == i) & (lab == c)
            ks, p = weighted_ks(s[a], np.abs(wph[a]), s[b], np.abs(wph[b]))
            d[cn] = {"ks": ks, "p": p, "n_train": int(a.sum()), "n_test": int(b.sum())}
        out["ks_train_vs_test"][wn] = d
        m = (split == 1) & (win == i) & (lab != 0)
        m3 = m & data["p_is3mu"]
        out["dcor_es"][wn] = {"delta1": dcor_np(s[m], data["p_d1"][m], np.abs(wtrain[m]), tcfg["monitor_dcor_max_events"]),
                              "delta2_3mu": dcor_np(s[m3], data["p_d2"][m3], np.abs(wtrain[m3]),
                                                    tcfg["monitor_dcor_max_events"]),
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
    data, meta = load_dataset(args.dataset)
    os.makedirs(args.out_dir, exist_ok=True)
    json.dump({"config": cfg, "dataset": os.path.abspath(args.dataset)},
              open(os.path.join(args.out_dir, "train_config.json"), "w"), indent=1)
    nets = range(cfg["training"]["n_folds"]) if args.net == "all" else [int(args.net)]
    for j in nets:
        train_one(j, data, meta, cfg, args.out_dir, torch.device(args.device), args.max_epochs,
                  False if args.no_compile else None)


if __name__ == "__main__":
    main()
