"""Band sizes and training-cost estimate of the three band ParticleNets (docs/PLAN_ParticleNet.md; user
decisions 2026-11-28: belowZ / onZ / aboveZ networks, one entry per background event and band, no
replication).

Band content from the existing 2024 SR RNTuples (only mass1 / mass2 are read): SR_<CH>_Central of the MC
samples of the training classes (all tight, N_b >= 1) and SR_<CH>_Nonprompt of the data as the proxy of the
loose-not-tight nonprompt events. Per band and channel: the band mass range (union of the band's template
windows with their pairing, configs/windows.json + configs/bands.json; python/bands.py) as merged intervals
with the gaps inside it, the fraction of background events entering the band, the fraction in two bands and
in none; the signal share of each band (SR signal entries of its points / all).

Cost: the per-step times of test/run_synthetic_bench.py (bench_results.json, batch 512, eager / compiled)
x the training entries per network (3/5 of the band) + the ES entries (1/5) give the epoch time per band;
totals for --epochs-expected epochs x 5 folds x 3 bands. Input event counts (signal, diboson + ttX,
nonprompt) are arguments; signal is shared among the bands by the SR signal entries, the backgrounds by the
measured band fractions. GPU memory = measured step peak + node store (11 floats per node) + per-entry
tensors (~40 B).

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
from bands import Bands  # noqa: E402
from windows import Windows  # noqa: E402

SRDIR = "/mnt/SKNanoOutput_Run3/TriLepton/Run1E2Mu_Run3Mu_SRTree_RunSyst_BTagEffHists_HcToWABTagEff/2024"
CLASSES = {
    "prompt_bkg": ["WZto3LNu", "ZZto4L", "ttZtoLL_MLL50toInf", "ttZtoLL_MLL4to50", "ttWtoLNu", "ttHtoNonbb_M125", "tZq"],
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sr-dir", default=SRDIR)
    cfg = os.path.join(os.path.dirname(HERE), "configs")
    ap.add_argument("--windows", default=os.path.join(cfg, "windows.json"))
    ap.add_argument("--bands", default=os.path.join(cfg, "bands.json"))
    ap.add_argument("--bench-results", required=True)
    ap.add_argument("--n-signal", type=float, default=1.4e6)
    ap.add_argument("--n-prompt-bkg", type=float, default=0.4e6, help="diboson + ttX events")
    ap.add_argument("--n-nonprompt", type=float, nargs="+", default=[0.4e6, 1.0e6, 2.0e6])
    ap.add_argument("--epochs-expected", type=int, nargs="+", default=[40, 120])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    win, bands = Windows(args.windows), Bands(args.bands)
    res = {"mass_range": {}, "band_fraction": {}, "signal_share": {}}
    for b, bn in enumerate(bands.names):
        res["mass_range"][bn] = {}
        for ch in ("1E2MU", "3MU"):
            iv = bands.intervals(win, b, ch)
            gaps = {p: [[round(v[k][1], 2), round(v[k + 1][0], 2)] for k in range(len(v) - 1)] for p, v in iv.items()}
            res["mass_range"][bn][ch] = {"intervals": {p: [[round(a, 2), round(z, 2)] for a, z in v] for p, v in iv.items()},
                                         "gaps": gaps}

    def fractions(key, ch, m1, m2):
        mem = np.stack([bands.in_band(win, b, ch, m1, m2) for b in range(bands.n)], 1)
        k = mem.sum(1)
        res["band_fraction"].setdefault(key, {})[ch] = {
            "events": int(len(k)), **{bn: float(mem[:, b].mean()) for b, bn in enumerate(bands.names)},
            "two_bands": float((k >= 2).mean()), "no_band": float((k == 0).mean())}

    for cls, samples in CLASSES.items():
        for ch in ("1E2MU", "3MU"):
            mm = [masses(os.path.join(args.sr_dir, f"Skim_TriLep_{s}.root"), f"SR_{ch}_Central") for s in samples]
            fractions(cls, ch, np.concatenate([m[0] for m in mm]), np.concatenate([m[1] for m in mm]))
    for ch, samples in DATA_NP.items():
        mm = [masses(os.path.join(args.sr_dir, f"Skim_TriLep_{s}.root"), f"SR_{ch}_Nonprompt") for s in samples]
        fractions("nonprompt_data_LNT", ch, np.concatenate([m[0] for m in mm]), np.concatenate([m[1] for m in mm]))
    nsig = np.zeros(bands.n)
    for i, p in enumerate(win.names):
        for ch in ("1E2MU", "3MU"):
            nsig[bands.band_of(win.mA[i])[0]] += len(masses(os.path.join(args.sr_dir, f"Skim_TriLep_TTToHcToWAToMuMu-{p}.root"),
                                                             f"SR_{ch}_Central")[0])
    share = nsig / nsig.sum()
    res["signal_share"] = {bn: float(share[b]) for b, bn in enumerate(bands.names)}

    def frac(key, bn):  # event-weighted over channels
        r = res["band_fraction"][key]
        return sum(v[bn] * v["events"] for v in r.values()) / sum(v["events"] for v in r.values())

    b_ = json.load(open(args.bench_results))["timing"]
    npe = b_["mean_nodes_per_graph"]
    est = []
    for nnp in args.n_nonprompt:
        row = {"n_nonprompt": nnp, "bands": {}}
        tot = {f"{m}_{ne}": 0.0 for m in ("eager", "compiled") for ne in args.epochs_expected}
        mem = 0.0
        for b, bn in enumerate(bands.names):
            n = args.n_signal * share[b] + args.n_prompt_bkg * frac("prompt_bkg", bn) + nnp * frac("nonprompt_data_LNT", bn)
            ntr, nes = 0.6 * n, 0.2 * n
            d = {"entries": n, "train_per_net": ntr, "steps_per_epoch": ntr / 512}
            for m in ("eager", "compiled"):
                te = ntr / 512 * b_[m]["t_train_step_ms"] / 1e3 + nes / 512 * b_[m]["t_eval_step_ms"] / 1e3
                d[f"t_epoch_{m}_min"] = te / 60
                for ne in args.epochs_expected:
                    tot[f"{m}_{ne}"] += 5 * ne * te / 3600
            d["gpu_MB_est"] = n * (npe * 11 * 4 + 40) / 2 ** 20 + b_["compiled"]["max_mem_MB"]
            mem = max(mem, d["gpu_MB_est"])
            row["bands"][bn] = d
        row["entries_total"] = sum(v["entries"] for v in row["bands"].values())
        row["t_total_15nets_h"] = tot
        row["gpu_MB_max"] = mem
        est.append(row)
    res["estimate"] = est
    res["inputs"] = {"n_signal": args.n_signal, "n_prompt_bkg": args.n_prompt_bkg, "nodes_per_event": npe,
                     "bench_timing": {m: {k: b_[m][k] for k in ("t_train_step_ms", "t_eval_step_ms", "max_mem_MB")}
                                      for m in ("eager", "compiled")}}
    print(json.dumps(res, indent=1))
    if args.out:
        json.dump(res, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
