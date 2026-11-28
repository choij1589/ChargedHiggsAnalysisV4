"""Dataset builder of the 2024 parametric ParticleNet, one data set per mA band (docs/PLAN_ParticleNet.md step 2;
P1-P8, P11; user decisions 2026-11-28: three band networks, random background mA).

Reads the training RNTuples Train_<CH> (CH = 1E2MU, 3MU) of every sample of configs/classes.json from
<input_dir>/Skim_TriLep_<sample>.root (RNTuple or TTree, python/pnet_io.py) once, selects the events of each
class and writes, for every band of configs/bands.json (belowZ, onZ, aboveZ), <out_dir>/<band>/:
  dataset.npz  nodes x [N_nodes, 9], etaphi [N_nodes, 2], counts / offsets per entry; per entry (one graph
               each; the p_* arrays are the training table, p_ev = the entry):
               ev_label, ev_channel, ev_sample, ev_entry (index in the input Train_<CH>: (sample, channel,
               entry) identifies an event, (run, lumi, event) is not unique in the signal samples), ev_run,
               ev_lumi, ev_event, ev_fold (= event % 5), ev_mass1, ev_mass2, ev_weight (physical), ev_point
               (index of the signal point in the band's points, -1 background), ev_u (the uniform of the
               background mA draw, -1 signal); p_mA (signal: generated mA; background: drawn mA),
               p_d1, p_d2 (Delta_k = (m_k - mA) / sigma_eff(mA)), p_is3mu, p_label, p_weight, p_fold;
  meta.json    band, its points / mA, the windows file, classes, samples, the draw probabilities per channel;
  stats.json   per class / sample: entries read, selected, in the band; per channel the band mass range
               (merged window intervals), per class the entries, weight sums, per-fold counts; the drawn-mA
               counts per class and point.
<out_dir>/bands.json (copy of the band config) and <out_dir>/summary.json (per band and class: entries;
background events in two bands).

Class selection (classes.json): signal = passSR of TTToHcToWAToMuMu-<point>, all events of the band's points
(no window requirement), mA = the generated value; nonprompt = not allTight and nBJets >= 1 of TTLL / TTLJ /
DY 2J, weight weight_genpu x weight_fake, events with weight <= 0 dropped (P5); diboson = passSR of WZ / ZZ
(P6); ttX = passSR of ttZ / ttW / ttH / tZq. Physical weight = weight_genpu (x weight_fake), already
including the prescale N (P11 (1)).
Background band membership and mA draw: python/bands.py (union of the band's template windows with their
pairing; once per band, an event may enter two bands; mA drawn from the band's signal points with
probabilities proportional to the per-channel signal weight totals, by a hash of (sample, channel, entry,
event, band)). The class rescaling per network and split (P11 (2)) is done at training time (weights.py).

Run: micromamba run -n PNet python ParticleNet/python/build_dataset.py --input-dir DIR --out-dir DIR
"""
import argparse
import json
import logging
import os
import shutil
import sys
import time

import numpy as np
import awkward as ak

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pnet_io  # noqa: E402
from bands import Bands, draw_mA, uniform_hash  # noqa: E402
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
    ap.add_argument("--bands", default=os.path.join(CFG, "bands.json"))
    ap.add_argument("--points", nargs="*", default=None, help="restrict to these mass points")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    t0 = time.time()

    ccfg = json.load(open(args.classes))
    bands = Bands(args.bands)
    allwin = Windows(args.windows, args.points)
    fpat, npat = ccfg["file_pattern"], ccfg["ntuple_pattern"]
    path = lambda s: os.path.join(args.input_dir, fpat.format(sample=s))
    sig_cls = [c for c in ccfg["classes"] if c["samples"] == "signal"]
    assert len(sig_cls) == 1 and sig_cls[0]["label"] == 0
    present = [p for p in allwin.names if os.path.exists(path(ccfg["signal_pattern"].format(masspoint=p)))]
    if sorted(set(allwin.names) - set(present)):
        logging.warning("no signal input for %s", sorted(set(allwin.names) - set(present)))
    win = Windows(args.windows, present)  # the trained points (sorted by mA)
    band_of_point = bands.band_of(win.mA)

    # ---- read every sample once
    fields = pnet_io.OBJ_FIELDS + pnet_io.EVT_FIELDS + pnet_io.TRAIN_FIELDS
    jobs = []
    for cls in ccfg["classes"]:
        if cls["samples"] == "signal":
            jobs += [(cls, ccfg["signal_pattern"].format(masspoint=p), i) for i, p in enumerate(win.names)]
        else:
            jobs += [(cls, s, -1) for s in cls["samples"]]
    blocks, samples, sstats = [], [], {}
    for cls, sample, ip in jobs:
        f = path(sample)
        st = {"class": cls["name"], "file": f, "channels": {}}
        sstats[sample] = st
        if not os.path.exists(f):
            logging.warning("missing input %s (%s)", f, cls["name"])
            st["missing"] = True
            continue
        si = len(samples)
        samples.append(sample)
        for ch in ccfg["channels"]:
            name = npat.format(ch=ch)
            cst = {"read": 0, "selected": 0, "dropped_nonpositive": 0, "sumw": 0.0}
            st["channels"][ch] = cst
            if not pnet_io.has_ntuple(f, name):  # the producer skips empty RNTuples
                continue
            arr = pnet_io.read_ntuple(f, name, fields)
            cst["read"] = len(arr)
            if len(arr):
                cst["prescale"] = [int(v) for v in np.unique(ak.to_numpy(arr["prescale"]))]
            m = select(arr, cls)
            w = weight(arr, cls)
            if cls.get("drop_nonpositive"):
                cst["dropped_nonpositive"] = int((m & (w <= 0)).sum())
                m &= w > 0
            entry = np.nonzero(m)[0]
            arr, w = arr[m], w[m]
            cst["selected"], cst["sumw"] = len(arr), float(w.sum())
            if len(arr):
                blocks.append({"cls": cls, "sample": sample, "si": si, "ip": ip, "ch": ch, "arr": arr, "w": w,
                               "entry": entry, "ec": pnet_io.event_columns(arr)})

    # ---- per band
    os.makedirs(args.out_dir, exist_ok=True)
    shutil.copy(args.bands, os.path.join(args.out_dir, "bands.json"))
    summary = {"bands": {}, "input_dir": os.path.abspath(args.input_dir)}
    member = {}  # (sample, ch) -> [n_events, in band 0, 1, 2] for the background two-band count
    cnames = {c["label"]: c["name"] for c in sorted(ccfg["classes"], key=lambda c: c["label"])}
    for b, bname in enumerate(bands.names):
        bpts = np.nonzero(band_of_point == b)[0]
        if len(bpts) == 0:
            logging.warning("band %s has no signal point: skipped", bname)
            continue
        bwin = Windows(args.windows, [win.names[i] for i in bpts])
        # draw probabilities per channel: physical signal weight totals per point
        prob = {}
        for ch in ccfg["channels"]:
            tot = np.zeros(len(bpts))
            for bl in blocks:
                if bl["ip"] >= 0 and bl["ch"] == ch and band_of_point[bl["ip"]] == b:
                    tot[list(bpts).index(bl["ip"])] += bl["w"].sum()
            prob[ch] = tot
        cols = {k: [] for k in ("label", "channel", "sample", "entry", "run", "lumi", "event", "mass1", "mass2",
                                "weight", "point", "u", "mA", "d1", "d2")}
        xs, eps, cnts = [], [], []
        bst = {"samples": {}}
        for bl in blocks:
            cls, ch, arr, ec = bl["cls"], bl["ch"], bl["arr"], bl["ec"]
            if bl["ip"] >= 0:
                if band_of_point[bl["ip"]] != b:
                    continue
                keep = np.ones(len(arr), bool)
                mA = np.full(len(arr), win.mA[bl["ip"]])
                u = np.full(len(arr), -1.0)
                pt = np.full(len(arr), list(bpts).index(bl["ip"]), np.int16)
            else:
                keep = bands.in_band(win, b, ch, ec["mass1"], ec["mass2"])
                key = (bl["sample"], ch)
                member.setdefault(key, np.zeros((len(arr), bands.n), bool))[:, b] = keep
                u = uniform_hash(bl["sample"], pnet_io.CHANNEL_ID[ch], bl["entry"], ec["event"], b)
                mA = bwin.mA[draw_mA(u, bwin.mA, prob[ch])]
                pt = np.full(len(arr), -1, np.int16)
            n = int(keep.sum())
            bst["samples"].setdefault(bl["sample"], {})[ch] = n
            if n == 0:
                continue
            sub = arr[keep]
            ecs = {k: v[keep] for k, v in ec.items()}
            d1, d2 = win.deltas(ch, mA[keep], ecs["mass1"], ecs["mass2"])
            x, ep, cnt = pnet_io.build_nodes(sub)
            xs.append(x), eps.append(ep), cnts.append(cnt)
            cols["label"].append(np.full(n, cls["label"], np.int8))
            cols["channel"].append(np.full(n, pnet_io.CHANNEL_ID[ch], np.int8))
            cols["sample"].append(np.full(n, bl["si"], np.int16))
            cols["entry"].append(bl["entry"][keep].astype(np.int64))
            for k in ("run", "lumi", "event", "mass1", "mass2"):
                cols[k].append(ecs[k])
            cols["weight"].append(bl["w"][keep])
            cols["point"].append(pt[keep])
            cols["u"].append(u[keep])
            cols["mA"].append(mA[keep].astype(np.float32))
            cols["d1"].append(d1), cols["d2"].append(d2)
        ev = {k: np.concatenate(v) for k, v in cols.items()}
        x, ep, counts = np.concatenate(xs), np.concatenate(eps), np.concatenate(cnts)
        offsets = (np.cumsum(counts, dtype=np.int64) - counts).astype(np.int64)
        ev["fold"] = (ev["event"] % np.uint64(N_FOLDS)).astype(np.int8)
        n_ev = len(ev["label"])
        p = {"ev": np.arange(n_ev, dtype=np.int64), "mA": ev.pop("mA"), "d1": ev.pop("d1"), "d2": ev.pop("d2"),
             "label": ev["label"], "weight": ev["weight"], "fold": ev["fold"],
             "is3mu": ev["channel"] == pnet_io.CHANNEL_ID["3MU"]}
        bst["mass_range"] = {ch: bands.intervals(win, b, ch) for ch in ccfg["channels"]}
        bst["classes"] = {}
        for lab, cn in cnames.items():
            m = ev["label"] == lab
            bst["classes"][cn] = {"entries": int(m.sum()), "sumw": float(ev["weight"][m].sum()),
                                  "entries_per_fold": [int((m & (ev["fold"] == k)).sum()) for k in range(N_FOLDS)],
                                  "mA_counts": {bwin.names[i]: int((m & np.isclose(p["mA"], bwin.mA[i])).sum())
                                                for i in range(bwin.n)}}
        bst["draw_prob"] = {ch: (prob[ch] / prob[ch].sum()).tolist() for ch in prob}
        bst["n_entries"], bst["n_nodes"], bst["max_nodes"] = int(n_ev), int(len(x)), int(counts.max())
        odir = os.path.join(args.out_dir, bname)
        os.makedirs(odir, exist_ok=True)
        np.savez(os.path.join(odir, "dataset.npz"), x=x, etaphi=ep, counts=counts, offsets=offsets,
                 **{f"ev_{k}": v for k, v in ev.items()}, **{f"p_{k}": v for k, v in p.items()})
        meta = {"band": bname, "band_lo": float(bands.lo[b]), "band_hi": float(bands.hi[b]),
                "bands_file": os.path.abspath(args.bands), "points": bwin.names, "mA": bwin.mA.tolist(),
                "windows_file": os.path.abspath(args.windows),
                "classes": [cnames[k] for k in sorted(cnames)], "class_config": ccfg, "samples": samples,
                "input_dir": os.path.abspath(args.input_dir), "n_folds": N_FOLDS, "features": pnet_io.FEATURES,
                "channels": pnet_io.CHANNEL_ID, "draw_prob": bst["draw_prob"]}
        json.dump(meta, open(os.path.join(odir, "meta.json"), "w"), indent=1)
        json.dump({"band": bst, "inputs": sstats}, open(os.path.join(odir, "stats.json"), "w"), indent=1)
        summary["bands"][bname] = {"points": bwin.names, "entries": {cn: v["entries"] for cn, v in bst["classes"].items()},
                                   "mass_range": bst["mass_range"]}
        logging.info("band %-7s points %s: entries %s, nodes %d", bname, [int(v) for v in bwin.mA],
                     {cn: v["entries"] for cn, v in bst["classes"].items()}, len(x))
    nb = {"events": 0, "in_two_bands": 0, "in_no_band": 0}
    for key, mm in member.items():
        k = mm.sum(1)
        nb["events"] += int(len(k))
        nb["in_two_bands"] += int((k >= 2).sum())
        nb["in_no_band"] += int((k == 0).sum())
    summary["background_band_membership"] = nb
    json.dump(summary, open(os.path.join(args.out_dir, "summary.json"), "w"), indent=1)
    logging.info("background events %s; %.1f s", nb, time.time() - t0)


if __name__ == "__main__":
    main()
