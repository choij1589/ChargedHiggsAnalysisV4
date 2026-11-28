"""Offline scoring of the TriLepton RNTuples with the 5-fold ParticleNet (docs/PLAN_ParticleNet.md step 4; P8, P9).

For every input file (one per sample) and every RNTuple whose name starts with one of --prefixes
(default SR_: SR_<CH>_<lane> for MC lanes incl. the object variations, data SR_<CH>_Nonprompt; Train_ to
score the training trees, e.g. the MC loose-not-tight events of the P5 data check), each event is scored
by the network of its fold (event % 5, network j = test fold j, P8) at every grid mass point whose window
contains its A-candidate mass (template pairing of that point, P3; python/windows.py). Graph parameter =
the mA of the grid point / mA_scale. Output: <out_dir>/<input file name> with one RNTuple of the same name
as the input RNTuple and one row per input row, in the input order:
    run, lumi (int32), event (uint64), fold (int32),
    score_mA (var float32: the grid mA of the windows containing the event, ascending),
    score_signal, score_nonprompt, score_diboson, score_ttX (var float32, aligned with score_mA)
(events outside every window: empty lists). The score RNTuple is a friend aligned by entry index: row i
scores entry i of the input RNTuple (SignalRegionStudy sample_reader must join by entry index, never by the
event key: in the 2024 signal samples run = lumi = 1 and the event numbers repeat across generation files);
run, lumi, event are kept only as a consistency check (equal to the input row by row);
an RNTuple without entries is not written (as the producer). A JSON sidecar <file>.json lists the model
directory, the grid (names, mA) and the RNTuples written.

The grid defaults to the trained points (the checkpoint); --grid / --windows select other points of a
windows config (e.g. the interpolated grid later).

Run: micromamba run -n PNet python ParticleNet/python/score.py --model-dir DIR --out-dir DIR FILE [FILE ...]
"""
import argparse
import json
import logging
import os
import sys
import time

import awkward as ak
import numpy as np
import torch
import uproot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pnet_io  # noqa: E402
from gpu_data import GraphStore  # noqa: E402
from model import ParticleNet  # noqa: E402
from train import predict  # noqa: E402
from windows import Windows  # noqa: E402

CLASS_FIELDS = ["score_signal", "score_nonprompt", "score_diboson", "score_ttX"]


def load_networks(model_dir, device):
    nets, ck0 = [], None
    for j in range(5):
        ck = torch.load(os.path.join(model_dir, f"net{j}", "model.pt"), map_location="cpu", weights_only=False)
        assert ck["net"] == j
        m = ParticleNet(**ck["model"]).to(device).float()
        m.load_state_dict(ck["state_dict"])
        m.eval()
        nets.append(m)
        ck0 = ck0 or ck
    if ck0["classes"] != ["signal", "nonprompt", "diboson", "ttX"]:
        raise ValueError(f"unexpected classes {ck0['classes']}")
    return nets, ck0


def channel_of(name):
    for ch in pnet_io.CHANNEL_ID:
        if name.startswith(f"SR_{ch}_") or name == f"Train_{ch}":
            return ch
    raise ValueError(f"no channel in RNTuple name {name}")


def score_arrays(arr, ch, win, nets, mcfg, device):
    """Per-event score lists of the record array `arr` of channel `ch`."""
    n = len(arr)
    ec = pnet_io.event_columns(arr)
    x, ep, cnt = pnet_io.build_nodes(arr)
    off = (np.cumsum(cnt, dtype=np.int64) - cnt)
    store = GraphStore(x, ep, cnt, off, device)
    e, wi = win.assign(ch, ec["mass1"], ec["mass2"])  # sorted by event, then window (ascending mA)
    fold = (ec["event"] % np.uint64(5)).astype(np.int64)
    probs = np.zeros((len(e), 4), np.float32)
    used = np.full(len(e), -1, np.int8)
    for j, net in enumerate(nets):
        sel = np.nonzero(fold[e] == j)[0]
        if len(sel) == 0:
            continue
        ev_t = torch.as_tensor(e[sel], device=device)
        mA_t = torch.as_tensor(win.mA[wi[sel]] / mcfg["mA_scale"], dtype=torch.float32, device=device)
        probs[sel] = predict(net, store, ev_t, mA_t, mcfg["k"])
        used[sel] = j
    assert (used == fold[e]).all()
    counts = np.bincount(e, minlength=n)
    out = {"run": ec["run"], "lumi": ec["lumi"], "event": ec["event"], "fold": fold.astype(np.int32),
           "score_mA": ak.unflatten(win.mA[wi].astype(np.float32), counts)}
    for c, f in enumerate(CLASS_FIELDS):
        out[f] = ak.unflatten(probs[:, c], counts)
    return out, len(e)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--prefixes", nargs="+", default=["SR_"])
    ap.add_argument("--windows", default=None, help="windows config (default: the one of the training)")
    ap.add_argument("--grid", nargs="*", default=None, help="mass points (default: the trained points)")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    device = torch.device(args.device)
    nets, ck = load_networks(args.model_dir, device)
    win = Windows(args.windows or ck["windows_file"], args.grid or ck["points"])
    os.makedirs(args.out_dir, exist_ok=True)
    fields = pnet_io.OBJ_FIELDS + pnet_io.EVT_FIELDS
    for path in args.files:
        t0 = time.time()
        names = [nm for p in args.prefixes for nm in pnet_io.list_ntuples(path, p)]
        outp = os.path.join(args.out_dir, os.path.basename(path))
        written = {}
        with uproot.recreate(outp) as fo:
            for nm in names:
                arr = pnet_io.read_ntuple(path, nm, fields)
                if len(arr) == 0:
                    continue
                out, npairs = score_arrays(arr, channel_of(nm), win, nets, ck["model"], device)
                fo.mkrntuple(nm, ak.Array(out))
                written[nm] = {"entries": len(arr), "pairs": int(npairs)}
        json.dump({"input": os.path.abspath(path), "model_dir": os.path.abspath(args.model_dir),
                   "grid": win.names, "mA": win.mA.tolist(), "windows_file": os.path.abspath(win.path),
                   "ntuples": written}, open(outp + ".json", "w"), indent=1)
        logging.info("%s: %s (%.1f s)", os.path.basename(path), written, time.time() - t0)


if __name__ == "__main__":
    main()
