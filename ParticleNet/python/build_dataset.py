"""Dataset builder of the 2024 parametric ParticleNet (docs/PLAN_ParticleNet.md step 2; P1-P8, P11).

Reads the training RNTuples Train_<CH> (CH = 1E2MU, 3MU) of every sample of configs/classes.json from
<input_dir>/Skim_TriLep_<sample>.root (RNTuple or TTree, python/pnet_io.py), selects the events of each
class, builds the graph nodes and the (event, mA) training pairs, and writes <out_dir>/:
  dataset.npz  nodes x [N_nodes, 9], etaphi [N_nodes, 2], counts/offsets per event; event table ev_*
               (label, channel, sample, entry = index in the input RNTuple, run, lumi, event, fold = event % 5, mass1, mass2, weight = the
               physical weight, point = signal mass-point index or -1; (sample, channel, entry) identifies an event: (run,
               lumi, event) is not unique in the signal samples, run = lumi = 1 and event numbers repeat); pair table p_* (event index, window
               index, label, physical weight, Delta_1, Delta_2, is3mu, fold);
  meta.json    classes, samples, windows (the trained mass points), selection, input files;
  stats.json   per class / sample: entries read, selected, dropped (non-positive weight), weight sums,
               prescale; per window and class: pairs and weight sums per fold; replication factors.

Class selection (classes.json): signal = passSR of TTToHcToWAToMuMu-<point> for every point of
configs/windows.json with an input file (the trained windows are those points); nonprompt = not allTight
and nBJets >= 1 of TTLL / TTLJ / DY 2J, weight weight_genpu x weight_fake, events with weight <= 0 dropped
(P5); diboson = passSR of WZ / ZZ (P6, genuine b tags); ttX = passSR of ttZ / ttW / ttH / tZq. Physical
weight = weight_genpu (x weight_fake): it already includes the training prescale N (P11 (1)).
Pairs (P3): a signal event of point j -> window j (only if inside window j with signal_in_window);
a background event -> every window of its channel containing its A-candidate mass (template pairing).
The per-network class rescaling (P11 (2), per split and window) is done at training time
(python/weights.py), since the splits depend on the network (P8).

Run: micromamba run -n PNet python ParticleNet/python/build_dataset.py --input-dir DIR --out-dir DIR
"""
import argparse
import json
import logging
import os
import sys
import time

import numpy as np
import awkward as ak

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pnet_io  # noqa: E402
from windows import Windows  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(os.path.dirname(HERE), "configs")
N_FOLDS = 5


def select(arr, cls):
    sel = cls["selection"]
    if sel == "passSR":
        m = ak.to_numpy(arr["passSR"]).astype(bool)
    elif sel == "lnt_b":
        m = ~ak.to_numpy(arr["allTight"]).astype(bool) & (ak.to_numpy(arr["nBJets"]) >= 1)
    else:
        raise ValueError(f"unknown selection {sel}")
    if cls.get("categories") is not None:
        m &= np.isin(ak.to_numpy(arr["category"]), cls["categories"])
    return m


def weight(arr, cls):
    w = ak.to_numpy(arr["weight_genpu"]).astype(np.float64)
    if cls["weight"] == "genpu_fake":
        w = w * ak.to_numpy(arr["weight_fake"]).astype(np.float64)
    elif cls["weight"] != "genpu":
        raise ValueError(f"unknown weight {cls['weight']}")
    return w


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--classes", default=os.path.join(CFG, "classes.json"))
    ap.add_argument("--windows", default=os.path.join(CFG, "windows.json"))
    ap.add_argument("--points", nargs="*", default=None, help="restrict to these mass points")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    t0 = time.time()

    ccfg = json.load(open(args.classes))
    allwin = Windows(args.windows, args.points)
    fpat, npat = ccfg["file_pattern"], ccfg["ntuple_pattern"]
    path = lambda s: os.path.join(args.input_dir, fpat.format(sample=s))

    # trained windows = mass points with a signal input file
    sig_cls = [c for c in ccfg["classes"] if c["samples"] == "signal"]
    assert len(sig_cls) == 1 and sig_cls[0]["label"] == 0
    present = [p for p in allwin.names if os.path.exists(path(ccfg["signal_pattern"].format(masspoint=p)))]
    missing = sorted(set(allwin.names) - set(present))
    if missing:
        logging.warning("no signal input for %s: these windows are not trained", missing)
    win = Windows(args.windows, present)
    logging.info("trained windows: %s", win.names)

    jobs = []  # (class, sample, point index)
    for cls in ccfg["classes"]:
        if cls["samples"] == "signal":
            jobs += [(cls, ccfg["signal_pattern"].format(masspoint=p), i) for i, p in enumerate(win.names)]
        else:
            jobs += [(cls, s, -1) for s in cls["samples"]]

    fields = pnet_io.OBJ_FIELDS + pnet_io.EVT_FIELDS + pnet_io.TRAIN_FIELDS
    samples, cols, xs, eps, cnts = [], {k: [] for k in
            ("label", "channel", "sample", "entry", "run", "lumi", "event", "mass1", "mass2", "weight", "point")}, [], [], []
    stats = {"samples": {}, "windows": {}, "classes": {}}
    pairs = {k: [] for k in ("ev", "win", "d1", "d2")}
    n_ev = 0
    for cls, sample, ip in jobs:
        f = path(sample)
        st = {"class": cls["name"], "file": f, "channels": {}}
        if not os.path.exists(f):
            logging.warning("missing input %s (%s)", f, cls["name"])
            st["missing"] = True
            stats["samples"][sample] = st
            continue
        si = len(samples)
        samples.append(sample)
        for ch in ccfg["channels"]:
            name = npat.format(ch=ch)
            cst = {"read": 0, "selected": 0, "dropped_nonpositive": 0, "sumw": 0.0, "pairs": 0}
            st["channels"][ch] = cst
            if not pnet_io.has_ntuple(f, name):  # the producer skips empty RNTuples
                continue
            arr = pnet_io.read_ntuple(f, name, fields)
            cst["read"] = len(arr)
            if len(arr):
                pres = np.unique(ak.to_numpy(arr["prescale"]))
                cst["prescale"] = [int(v) for v in pres]
            m = select(arr, cls)
            w = weight(arr, cls)
            if cls.get("drop_nonpositive"):
                cst["dropped_nonpositive"] = int((m & (w <= 0)).sum())
                m &= w > 0
            entry = np.nonzero(m)[0]  # entry index in Train_<CH> (the event key is not unique)
            arr, w = arr[m], w[m]
            n = len(arr)
            cst["selected"], cst["sumw"] = n, float(w.sum())
            if n == 0:
                continue
            ec = pnet_io.event_columns(arr)
            # pairs
            if ip >= 0:
                e, wi = win.assign(ch, ec["mass1"], ec["mass2"], fixed=np.full(n, ip),
                                   require_in=ccfg.get("signal_in_window", True))
            else:
                e, wi = win.assign(ch, ec["mass1"], ec["mass2"])
            # keep only events with at least one pair
            keep = np.zeros(n, bool)
            keep[e] = True
            remap = np.cumsum(keep) - 1
            cst["in_any_window"] = int(keep.sum())
            cst["pairs"] = int(len(e))
            arr, w, entry = arr[keep], w[keep], entry[keep]
            ec = {k: v[keep] for k, v in ec.items()}
            e = remap[e]
            d1, d2 = win.deltas(ch, wi, ec["mass1"][e], ec["mass2"][e])
            x, ep, cnt = pnet_io.build_nodes(arr)
            xs.append(x), eps.append(ep), cnts.append(cnt)
            nk = len(w)
            cols["label"].append(np.full(nk, cls["label"], np.int8))
            cols["channel"].append(np.full(nk, pnet_io.CHANNEL_ID[ch], np.int8))
            cols["sample"].append(np.full(nk, si, np.int16))
            cols["point"].append(np.full(nk, ip, np.int16))
            cols["entry"].append(entry.astype(np.int64))
            cols["weight"].append(w)
            for k in ("run", "lumi", "event", "mass1", "mass2"):
                cols[k].append(ec[k])
            pairs["ev"].append(e + n_ev)
            pairs["win"].append(wi.astype(np.int16))
            pairs["d1"].append(d1)
            pairs["d2"].append(d2)
            n_ev += nk
        stats["samples"][sample] = st
        logging.info("%-40s %-9s %s", sample, cls["name"],
                     {c: (v["read"], v["selected"], v.get("pairs", 0)) for c, v in st["channels"].items()})

    ev = {k: np.concatenate(v) for k, v in cols.items()}
    x, ep, counts = np.concatenate(xs), np.concatenate(eps), np.concatenate(cnts)
    offsets = (np.cumsum(counts, dtype=np.int64) - counts).astype(np.int64)
    ev["fold"] = (ev["event"] % np.uint64(N_FOLDS)).astype(np.int8)
    p = {k: np.concatenate(v) for k, v in pairs.items()}
    p["label"] = ev["label"][p["ev"]]
    p["weight"] = ev["weight"][p["ev"]]
    p["is3mu"] = ev["channel"][p["ev"]] == pnet_io.CHANNEL_ID["3MU"]
    p["fold"] = ev["fold"][p["ev"]]

    # stats per window and class
    cnames = {c["label"]: c["name"] for c in ccfg["classes"]}
    for i, wn in enumerate(win.names):
        d = {}
        for lab, cn in cnames.items():
            m = (p["win"] == i) & (p["label"] == lab)
            d[cn] = {"pairs": int(m.sum()), "sumw": float(p["weight"][m].sum()),
                     "pairs_per_fold": [int((m & (p["fold"] == k)).sum()) for k in range(N_FOLDS)],
                     "sumw_per_fold": [float(p["weight"][m & (p["fold"] == k)].sum()) for k in range(N_FOLDS)]}
        stats["windows"][wn] = d
    for lab, cn in cnames.items():
        ne = int((ev["label"] == lab).sum())
        npairs = int((p["label"] == lab).sum())
        stats["classes"][cn] = {"events": ne, "pairs": npairs, "replication": npairs / ne if ne else 0.0,
                                "sumw": float(ev["weight"][ev["label"] == lab].sum())}
    stats["n_events"], stats["n_pairs"], stats["n_nodes"] = int(n_ev), int(len(p["ev"])), int(len(x))
    stats["max_nodes"] = int(counts.max())

    os.makedirs(args.out_dir, exist_ok=True)
    np.savez(os.path.join(args.out_dir, "dataset.npz"), x=x, etaphi=ep, counts=counts, offsets=offsets,
             **{f"ev_{k}": v for k, v in ev.items()}, **{f"p_{k}": v for k, v in p.items()})
    meta = {"classes": [c["name"] for c in sorted(ccfg["classes"], key=lambda c: c["label"])],
            "class_config": ccfg, "samples": samples, "windows_file": os.path.abspath(args.windows),
            "points": win.names, "mA": win.mA.tolist(), "input_dir": os.path.abspath(args.input_dir),
            "n_folds": N_FOLDS, "features": pnet_io.FEATURES, "channels": pnet_io.CHANNEL_ID}
    json.dump(meta, open(os.path.join(args.out_dir, "meta.json"), "w"), indent=1)
    json.dump(stats, open(os.path.join(args.out_dir, "stats.json"), "w"), indent=1)
    logging.info("events %d, pairs %d, nodes %d (max %d per graph); classes %s; %.1f s", n_ev, len(p["ev"]),
                 len(x), counts.max(), {k: (v["events"], v["pairs"], round(v["replication"], 2))
                                         for k, v in stats["classes"].items()}, time.time() - t0)


if __name__ == "__main__":
    main()
