"""Synthetic TriLepton outputs for the ParticleNet bench (docs/PLAN_ParticleNet.md steps 2-4).

Writes <out_dir>/Skim_TriLep_<sample>.root files in the format of SKNano HcToWA_Analyzers/src/TriLepton.cc
(branch HcToWA_Run3, f45096c): MC files with Train_1E2MU, Train_3MU (fields mass1, mass2, pT1, pT2, nJets,
nBJets, run, lumi, event, the object fields lep_* / jet_* / MET_*, nTight, allTight, passSR, weight_genpu,
weight_fake, category, lep_genType, prescale, signal: matchedPair) and SR_<CH>_Central / SR_<CH>_JetEn_Up
(the passSR events with weight and the object fields; JetEn_Up = jet pT x 1.02); data files
(MuonEG_C, Muon0_C) with SR_<CH>_Nonprompt only (loose-not-tight events). RNTuples are written with uproot
(mkrntuple); --ttree-samples writes those samples as TTrees instead, to test the reader on both.

Physics content is a toy: leptons 3 (muons first in descending pT, then the electron; 1E2MU OS mu mu,
3MU |sum q| = 1), the A-candidate OS pair at a target mass (signal: N(x0, sigma_eff) of the windows config
with 10% flat tails; diboson: Z peak + continuum; nonprompt / ttX: falling + flat), mass1 / mass2 computed
from the stored four-vectors (3MU: lower / higher OS pair; 1E2MU mass2 = -1), 2-8 jets with b tags,
MET; signal samples with run = lumi = 1 and repeated event numbers (~4 entries per key, as the 2024
signal); tight flags per lepton (nonprompt sources mostly loose-not-tight), weight_fake = -prod(-f/(1-f)) over
the loose-not-tight leptons (1 if all tight), a fraction of negative generator weights, unique event numbers for the backgrounds.

Run: micromamba run -n PNet python ParticleNet/test/make_synthetic_trees.py --out-dir DIR
"""
import argparse
import json
import os
import sys

import awkward as ak
import numpy as np
import uproot

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "python"))
from windows import Windows  # noqa: E402

MMU = 0.10566
# sample: (class kind, n events, weight scale, negative fraction, b prob, jet lambda, MET scale, prescale)
BKG = {
    "TTLL_powheg": ("np", 3000, 0.02, 0.0, 0.35, 1.5, 40., 2),
    "TTLJ_powheg": ("np", 1000, 0.05, 0.0, 0.35, 2.0, 35., 1),
    "DYto2Mu_2J_MLL50toInf": ("np_dy", 800, 0.10, 0.02, 0.25, 0.8, 20., 1),
    "DYto2E_2J_MLL10to50": ("np_dy", 400, 0.20, 0.02, 0.25, 0.8, 20., 1),
    "WZto3LNu": ("vv", 2500, 0.004, 0.0, 0.40, 0.6, 35., 1),
    "ZZto4L": ("vv", 1500, 0.002, 0.0, 0.40, 0.4, 15., 1),
    "ttZtoLL_MLL50toInf": ("ttx_z", 1500, 0.001, 0.08, 0.5, 2.5, 45., 1),
    "ttWtoLNu": ("ttx", 1000, 0.001, 0.12, 0.5, 2.5, 50., 1),
    "tZq": ("ttx_z", 600, 0.001, 0.10, 0.5, 1.0, 40., 1),
    "ttHtoNonbb_M125": ("ttx", 600, 0.0005, 0.05, 0.5, 2.5, 45., 1),
    "WWZ": ("vv", 300, 0.001, 0.0, 0.3, 1.0, 30., 1),  # not in any class
}
DATA = {"MuonEG_C": "1E2MU", "Muon0_C": "3MU"}
DEF_POINTS = ["MHc130_MA15", "MHc130_MA30", "MHc130_MA55", "MHc130_MA65", "MHc130_MA85", "MHc130_MA90",
              "MHc130_MA105", "MHc130_MA120"]  # all three bands (belowZ, onZ, aboveZ)


def p4(pt, eta, phi, m):
    px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta)
    return np.stack([np.sqrt(px ** 2 + py ** 2 + pz ** 2 + m ** 2), px, py, pz], -1)


def minv(a, b):
    s = a + b
    return np.sqrt(np.maximum(s[..., 0] ** 2 - s[..., 1] ** 2 - s[..., 2] ** 2 - s[..., 3] ** 2, 0))


def target_mass(rng, kind, n, sig=None):
    if kind == "sig":
        x0, sg = sig
        m = rng.normal(x0, sg, n)
        tail = rng.random(n) < 0.10
        m[tail] = rng.uniform(12.5, 160., tail.sum())
        return m
    u = rng.random(n)
    m = 12. + rng.exponential(30., n)
    flat = rng.uniform(12., 160., n)
    if kind in ("np", "np_dy", "ttx"):
        return np.where(u < 0.6, m, flat)
    z = 91.19 + 2.5 * rng.standard_cauchy(n) * 0.5
    z = np.clip(z, 12.5, 200.)
    frac = 0.6 if kind == "vv" else 0.35
    return np.where(u < frac, z, np.where(u < frac + 0.25, m, flat))


def pair_with_mass(rng, m):
    """Two massless-approximated muons with invariant mass m (pt_b solved from pt_a and the angles)."""
    n = len(m)
    pta, eta_a, phi_a = np.zeros(n), np.zeros(n), np.zeros(n)
    ptb, eta_b, phi_b = np.zeros(n), np.zeros(n), np.zeros(n)
    todo = np.ones(n, bool)
    while todo.any():
        k = todo.sum()
        a = 10. + rng.exponential(30., k)
        ea, pa = rng.uniform(-2.4, 2.4, k), rng.uniform(-np.pi, np.pi, k)
        eb, pb = rng.uniform(-2.4, 2.4, k), rng.uniform(-np.pi, np.pi, k)
        b = m[todo] ** 2 / (2 * a * (np.cosh(ea - eb) - np.cos(pa - pb)))
        ok = (b > 10.) & (b < 400.)
        idx = np.nonzero(todo)[0][ok]
        pta[idx], eta_a[idx], phi_a[idx] = a[ok], ea[ok], pa[ok]
        ptb[idx], eta_b[idx], phi_b[idx] = b[ok], eb[ok], pb[ok]
        todo[idx] = False
    return (pta, eta_a, phi_a), (ptb, eta_b, phi_b)


def gen_channel(rng, ch, n, kind, wscale, negfrac, bprob, jlam, metscale, prescale, sig=None, is_data=False,
                ev_offset=0):
    m_t = target_mass(rng, "sig" if kind == "sig" else kind, n, sig)
    (pa, ea, fa), (pb, eb, fb) = pair_with_mass(rng, m_t)
    pc = 10. + rng.exponential(25., n)
    ec, fc = rng.uniform(-2.4, 2.4, n), rng.uniform(-np.pi, np.pi, n)
    q = rng.choice([-1, 1], n)
    # leptons: a, b = the A-candidate OS pair; c = third lepton (electron in 1E2MU, ss muon in 3MU)
    if ch == "1E2MU":
        qa, qb, qc = -q, q, rng.choice([-1, 1], n)
        mc = np.zeros(n)
    else:
        qa, qb, qc = -q, q, q
        mc = np.full(n, MMU)
    pts = np.stack([pa, pb, pc], 1)
    etas = np.stack([ea, eb, ec], 1)
    phis = np.stack([fa, fb, fc], 1)
    ms = np.stack([np.full(n, MMU), np.full(n, MMU), mc], 1)
    qs = np.stack([qa, qb, qc], 1)
    nmu = 2 if ch == "1E2MU" else 3
    # muons in descending pT, then the electron
    order = np.argsort(-pts[:, :nmu], 1)
    if nmu == 2:
        order = np.concatenate([order, np.full((n, 1), 2)], 1)
    take = lambda a: np.take_along_axis(a, order, 1)
    pts, etas, phis, ms, qs = map(take, (pts, etas, phis, ms, qs))
    ismu = np.ones((n, 3), bool)
    if ch == "1E2MU":
        ismu[:, 2] = False
    v = p4(pts, etas, phis, ms)
    if ch == "1E2MU":
        mass1 = minv(v[:, 0], v[:, 1])
        mass2 = np.full(n, -1.0)
        pT1 = np.hypot(*(v[:, 0, 1:3] + v[:, 1, 1:3]).T)
        pT2 = np.full(n, -1.0)
    else:
        os_i = np.argmax(qs != np.sign(qs.sum(1))[:, None], 1)
        ss = np.array([[1, 2], [0, 2], [0, 1]])[os_i]
        r = np.arange(n)
        m1 = minv(v[r, ss[:, 0]], v[r, os_i])
        m2 = minv(v[r, ss[:, 1]], v[r, os_i])
        mass1, mass2 = np.minimum(m1, m2), np.maximum(m1, m2)
        pT1 = pT2 = np.zeros(n)
    # jets
    nj = np.minimum(2 + rng.poisson(jlam, n), 8)
    tot = nj.sum()
    jpt = 30. + rng.exponential(40., tot)
    jstart = np.cumsum(nj) - nj
    # sort jets in descending pT within the event
    key = np.repeat(np.arange(n), nj) * 1e6 - jpt
    jpt = jpt[np.argsort(key, kind="stable")]
    jeta = rng.uniform(-2.5, 2.5, tot)
    jphi = rng.uniform(-np.pi, np.pi, tot)
    jm = 5. + rng.exponential(5., tot)
    jb = rng.random(tot) < bprob
    nb = np.add.reduceat(jb.astype(int), jstart)
    met = rng.exponential(metscale, n)
    metphi = rng.uniform(-np.pi, np.pi, n)
    # tight flags and weights
    u = rng.random(n)
    if kind.startswith("np"):
        nlnt = np.where(u < 0.7, 1, np.where(u < 0.8, 2, 0))
    else:
        nlnt = np.where(u < 0.9, 0, 1)
    tight = np.ones((n, 3), bool)
    for kk in range(n):  # small toy sizes
        if nlnt[kk]:
            tight[kk, rng.choice(3, nlnt[kk], replace=False)] = False
    f = rng.uniform(0.05, 0.3, (n, 3))
    term = np.where(tight, 1.0, -f / (1 - f))
    wfake = np.where(nlnt > 0, -np.prod(term, 1), 1.0)
    alltight = nlnt == 0
    sign = np.where(rng.random(n) < negfrac, -1.0, 1.0)
    wgenpu = wscale * sign * rng.uniform(0.8, 1.2, n) * prescale
    if kind == "np_dy":
        cat = rng.choice([0, 1, 3], n, p=[0.2, 0.3, 0.5])
        passconv = cat == 1
    elif kind.startswith("np"):
        cat = rng.choice([0, 3, 4], n, p=[0.1, 0.85, 0.05])
        passconv = np.ones(n, bool)
    else:
        cat = rng.choice([0, 3], n, p=[0.95, 0.05])
        passconv = np.ones(n, bool)
    passsr = alltight & (nb >= 1) & passconv
    if kind == "sig":  # as the 2024 signal samples: run = lumi = 1, event numbers repeat across files
        event = rng.integers(1, max(2, n // 4), n).astype(np.uint64)
        lumi = np.ones(n, np.int32)
    else:
        event = (rng.choice(2 ** 40, n, replace=False).astype(np.uint64) + np.uint64(ev_offset))
        lumi = rng.integers(1, 5000, n).astype(np.int32)
    lj = lambda a, t=np.float32: ak.unflatten(a.astype(t), nj)
    rows = {
        "mass1": mass1.astype(np.float32), "mass2": mass2.astype(np.float32), "pT1": pT1.astype(np.float32),
        "pT2": pT2.astype(np.float32), "nJets": nj.astype(np.int32), "nBJets": nb.astype(np.int32),
        "run": np.ones(n, np.int32), "lumi": lumi, "event": event,
        "lep_pt": ak.Array(pts.astype(np.float32)), "lep_eta": ak.Array(etas.astype(np.float32)),
        "lep_phi": ak.Array(phis.astype(np.float32)), "lep_mass": ak.Array(ms.astype(np.float32)),
        "lep_charge": ak.Array(qs.astype(np.int32)), "lep_isMuon": ak.Array(ismu),
        "lep_isTight": ak.Array(tight),
        "jet_pt": lj(jpt), "jet_eta": lj(jeta), "jet_phi": lj(jphi), "jet_mass": lj(jm), "jet_isBtagged": lj(jb, bool),
        "MET_pt": met.astype(np.float32), "MET_phi": metphi.astype(np.float32),
        "nTight": (3 - nlnt).astype(np.int32), "allTight": alltight, "passSR": passsr,
        "weight_genpu": wgenpu.astype(np.float32), "weight_fake": wfake.astype(np.float32),
        "category": cat.astype(np.int32), "lep_genType": ak.Array(rng.integers(0, 6, (n, 3)).astype(np.int32)),
        "prescale": np.full(n, prescale, np.int32),
        "_weight": (wgenpu * 0.95 if not is_data else wfake).astype(np.float32),
    }
    # regular -> jagged for the fixed 3-lepton fields (as std::vector)
    for k in [k for k in rows if k.startswith("lep_")]:
        rows[k] = ak.from_regular(rows[k], axis=1)
    if kind == "sig":
        rows["matchedPair"] = rng.choice([0, 1, 2] if ch == "3MU" else [0, 1], n).astype(np.int32)
    return rows


OBJ = ["lep_pt", "lep_eta", "lep_phi", "lep_mass", "lep_charge", "lep_isMuon", "lep_isTight", "jet_pt", "jet_eta",
       "jet_phi", "jet_mass", "jet_isBtagged", "MET_pt", "MET_phi"]
BASE = ["mass1", "mass2", "pT1", "pT2", "nJets", "nBJets", "run", "lumi", "event"]
TRAIN = ["nTight", "allTight", "passSR", "weight_genpu", "weight_fake", "category", "lep_genType", "prescale"]


def sub(rows, mask, fields, extra=None):
    out = {k: rows[k][mask] for k in fields}
    if extra:
        out.update(extra)
    return out


def write(f, name, d, ttree):
    if len(d["event"]) == 0:
        return
    if ttree:  # explicit TTree (f[name] = dict writes an RNTuple in uproot 5.7); jagged: counter branches n<field>
        f.mktree(name, {k: (v.type if isinstance(v, ak.Array) else np.asarray(v).dtype) for k, v in d.items()})
        f[name].extend(d)
    else:
        f.mkrntuple(name, ak.Array(d))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--windows", default=os.path.join(os.path.dirname(HERE), "configs", "windows.json"))
    ap.add_argument("--points", nargs="*", default=DEF_POINTS)
    ap.add_argument("--n-signal", type=int, default=1500)
    ap.add_argument("--scale", type=float, default=1.0, help="scale of the background sizes")
    ap.add_argument("--ttree-samples", nargs="*", default=["ZZto4L"])
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    win = Windows(args.windows, args.points)
    os.makedirs(args.out_dir, exist_ok=True)
    jobs = []
    for i, p in enumerate(win.names):
        jobs.append((f"TTToHcToWAToMuMu-{p}", ("sig", args.n_signal, 1e-4, 0.0, 0.5, 2.0, 45., 1), i))
    for s, spec in BKG.items():
        jobs.append((s, spec[:1] + (int(spec[1] * args.scale),) + spec[2:], -1))
    summary = {}
    for k, (sample, spec, ip) in enumerate(jobs):
        kind, n, wsc, negf, bp, jl, ms, pres = spec
        ttree = sample in args.ttree_samples
        path = os.path.join(args.out_dir, f"Skim_TriLep_{sample}.root")
        with uproot.recreate(path) as f:
            for ich, ch in enumerate(("1E2MU", "3MU")):
                nn = int(n * (0.45 if ch == "1E2MU" else 0.55))
                sig = (win.ch[ch]["x0"][ip], win.ch[ch]["sigma"][ip]) if kind == "sig" else None
                r = gen_channel(rng, ch, nn, kind, wsc, negf, bp, jl, ms, pres, sig,
                                ev_offset=(k * 2 + ich) * 2 ** 41)
                tf = BASE + OBJ + TRAIN + (["matchedPair"] if kind == "sig" else [])
                write(f, f"Train_{ch}", sub(r, slice(None), tf), ttree)
                m = np.asarray(r["passSR"])
                sr = sub(r, m, BASE + OBJ, {"weight": r["_weight"][m]})
                write(f, f"SR_{ch}_Central", sr, ttree)
                sv = dict(sr)
                sv["jet_pt"] = sv["jet_pt"] * np.float32(1.02)
                write(f, f"SR_{ch}_JetEn_Up", sv, ttree)
                summary.setdefault(sample, {})[ch] = {"train": nn, "sr": int(m.sum()), "ttree": ttree}
    for k, (sample, ch) in enumerate(DATA.items()):
        path = os.path.join(args.out_dir, f"Skim_TriLep_{sample}.root")
        r = gen_channel(rng, ch, 1000, "np", 1.0, 0.0, 0.35, 1.5, 40., 1, is_data=True,
                        ev_offset=(100 + k) * 2 ** 41)
        m = ~np.asarray(r["allTight"]) & (np.asarray(r["nBJets"]) >= 1)
        with uproot.recreate(path) as f:
            write(f, f"SR_{ch}_Nonprompt", sub(r, m, BASE + OBJ, {"weight": r["_weight"][m]}), False)
        summary[sample] = {ch: {"sr_nonprompt": int(m.sum())}}
    json.dump({"points": win.names, "samples": summary}, open(os.path.join(args.out_dir, "synthetic.json"), "w"),
              indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
