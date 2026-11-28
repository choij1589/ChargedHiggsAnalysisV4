"""Window replication factor and training-cost estimate of the 2024 ParticleNet (docs/PLAN_ParticleNet.md P3, P8).

Replication: reads mass1 / mass2 of the existing 2024 SR RNTuples (SR_<CH>_Central of the MC samples of
the training classes, all tight with N_b >= 1, and SR_<CH>_Nonprompt of the data as the proxy of the
loose-not-tight nonprompt events; only the two mass fields are read) and counts, per class and channel,
the mean number of the 23 windows of configs/windows.json containing each event (template pairing per
window; = pairs per event of the training data set), the fraction of events in no window (not trained),
and for the signal points the fraction inside their own window.

Cost: with the per-step times measured by test/run_synthetic_bench.py (bench_results.json: training step
and evaluation step at batch 512, eager and compiled), the number of training pairs per network
(3/5 of the pairs) and ES pairs (1/5) gives the time per epoch; the total uses --epochs-expected epochs
per network (early stopping) and 5 networks. The input event counts (signal, diboson + ttX, nonprompt) are
arguments (before window replication). GPU memory = measured step peak + the node store (11 floats per
node) + the pair tensors (~40 B per pair).

Run: micromamba run -n PNet python ParticleNet/test/estimate_training_cost.py --bench-results FILE
"""
import argparse
import json
import os
import sys

import numpy as np
import uproot

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "python"))
from windows import Windows  # noqa: E402

SRDIR = "/mnt/SKNanoOutput_Run3/TriLepton/Run1E2Mu_Run3Mu_SRTree_RunSyst_BTagEffHists_HcToWABTagEff/2024"
CLASSES = {
    "diboson": ["WZto3LNu", "ZZto4L"],
    "ttX": ["ttZtoLL_MLL50toInf", "ttZtoLL_MLL4to50", "ttWtoLNu", "ttHtoNonbb_M125", "tZq"],
    "nonprompt_MC_tight_TTLL": ["TTLL_powheg"],
}
DATA_NP = {"1E2MU": ["MuonEG_C", "MuonEG_D", "MuonEG_E", "MuonEG_F", "MuonEG_G", "MuonEG_H", "MuonEG_I",
                     "MuonEG_I_v2"],
           "3MU": [f"Muon{i}_{e}" for i in (0, 1) for e in ("C", "D", "E", "F", "G", "H", "I", "I_v2")]}


def masses(path, name):
    with uproot.open(path) as f:
        if name not in [k.split(";")[0] for k in f.keys(recursive=False)]:
            return np.zeros(0), np.zeros(0)
        a = f[name].arrays(["mass1", "mass2"], library="np")
    return a["mass1"].astype(np.float64), a["mass2"].astype(np.float64)


def nwin(win, ch, m1, m2):
    n = np.zeros(len(m1), np.int64)
    for i in range(win.n):
        n += win.in_window(ch, i, m1, m2)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sr-dir", default=SRDIR)
    ap.add_argument("--windows", default=os.path.join(os.path.dirname(HERE), "configs", "windows.json"))
    ap.add_argument("--bench-results", required=True)
    ap.add_argument("--n-signal", type=float, default=1.4e6)
    ap.add_argument("--n-prompt-bkg", type=float, default=0.4e6, help="diboson + ttX events")
    ap.add_argument("--n-nonprompt", type=float, nargs="+", default=[0.4e6, 1.0e6, 2.0e6])
    ap.add_argument("--epochs-expected", type=int, nargs="+", default=[40, 120])
    ap.add_argument("--nodes-per-event", type=float, default=None, help="default: from the bench")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    win = Windows(args.windows)
    res = {"replication": {}, "signal_in_own_window": {}}

    def summarize(key, ch, m1, m2):
        n = nwin(win, ch, m1, m2)
        res["replication"].setdefault(key, {})[ch] = {
            "events": int(len(n)), "pairs_per_event": float(n.mean()) if len(n) else 0.0,
            "pairs_per_event_in_any_window": float(n[n > 0].mean()) if (n > 0).any() else 0.0,
            "frac_no_window": float((n == 0).mean()) if len(n) else 0.0}

    for cls, samples in CLASSES.items():
        for ch in ("1E2MU", "3MU"):
            mm = [masses(os.path.join(args.sr_dir, f"Skim_TriLep_{s}.root"), f"SR_{ch}_Central") for s in samples]
            summarize(cls, ch, np.concatenate([m[0] for m in mm]), np.concatenate([m[1] for m in mm]))
    for ch, samples in DATA_NP.items():
        mm = [masses(os.path.join(args.sr_dir, f"Skim_TriLep_{s}.root"), f"SR_{ch}_Nonprompt") for s in samples]
        summarize("nonprompt_data_LNT", ch, np.concatenate([m[0] for m in mm]), np.concatenate([m[1] for m in mm]))
    nsig = {}
    for i, p in enumerate(win.names):
        for ch in ("1E2MU", "3MU"):
            m1, m2 = masses(os.path.join(args.sr_dir, f"Skim_TriLep_TTToHcToWAToMuMu-{p}.root"), f"SR_{ch}_Central")
            inside = win.in_window(ch, i, m1, m2)
            res["signal_in_own_window"].setdefault(p, {})[ch] = float(inside.mean()) if len(m1) else 0.0
            nsig.setdefault(ch, [0, 0])
            nsig[ch][0] += int(inside.sum()); nsig[ch][1] += len(m1)
    f_sig = sum(v[0] for v in nsig.values()) / sum(v[1] for v in nsig.values())
    res["signal_in_own_window_all"] = f_sig

    def comb(key):
        r = res["replication"][key]
        ev = sum(v["events"] for v in r.values())
        return sum(v["pairs_per_event"] * v["events"] for v in r.values()) / ev
    R_prompt = (comb("diboson") * sum(v["events"] for v in res["replication"]["diboson"].values())
                + comb("ttX") * sum(v["events"] for v in res["replication"]["ttX"].values())) / \
               (sum(v["events"] for v in res["replication"]["diboson"].values())
                + sum(v["events"] for v in res["replication"]["ttX"].values()))
    R_np = comb("nonprompt_data_LNT")
    res["R_prompt_bkg"], res["R_nonprompt"] = R_prompt, R_np

    b = json.load(open(args.bench_results))["timing"]
    npe = args.nodes_per_event or b["mean_nodes_per_graph"]
    est = []
    for nnp in args.n_nonprompt:
        pairs = args.n_signal * f_sig + args.n_prompt_bkg * R_prompt + nnp * R_np
        events = args.n_signal + args.n_prompt_bkg + nnp
        ntr, nes = 0.6 * pairs, 0.2 * pairs
        row = {"n_nonprompt": nnp, "pairs": pairs, "train_pairs_per_net": ntr, "es_pairs_per_net": nes,
               "steps_per_epoch": ntr / 512}
        for mode in ("eager", "compiled"):
            te = ntr / 512 * b[mode]["t_train_step_ms"] / 1e3 + nes / 512 * b[mode]["t_eval_step_ms"] / 1e3
            row[f"t_epoch_{mode}_min"] = te / 60
            for ne in args.epochs_expected:
                row[f"t_total_5nets_{ne}ep_{mode}_h"] = 5 * ne * te / 3600
        row["gpu_store_MB"] = (events * npe * 11 * 4 + pairs * 40) / 2 ** 20
        row["gpu_total_MB_est"] = row["gpu_store_MB"] + b["compiled"]["max_mem_MB"]
        est.append(row)
    res["estimate"] = est
    res["inputs"] = {"n_signal": args.n_signal, "n_prompt_bkg": args.n_prompt_bkg, "nodes_per_event": npe,
                     "bench_timing": {m: {k: b[m][k] for k in ("t_train_step_ms", "t_eval_step_ms", "max_mem_MB")}
                                      for m in ("eager", "compiled")}}
    print(json.dumps(res, indent=1))
    if args.out:
        json.dump(res, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
