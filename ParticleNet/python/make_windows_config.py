"""Build the mA-window configuration of the parametric ParticleNet (docs/PLAN_ParticleNet.md P3, P7).

Reads the 23 baseline mass points (SignalRegionStudy/configs/masspoints.json) and, per point and channel,
the SignalRegionStudy binning (templates/<MP>/Baseline/mc-signal/2024/{SR1E2Mu,SR3Mu}/binning.json:
DCB fit x0, sigma_eff, mass_min, mass_max, pairing), and writes ParticleNet/configs/windows.json:

    {"meta": {...}, "points": [{"name": "MHc130_MA90", "mHc": 130, "mA": 90.0,
       "channels": {"1E2MU": {"x0", "sigma_eff", "lo", "hi", "pairing"}, "3MU": {...}}}, ...]}

Window = [x0 - 10 sigma_eff, x0 + 10 sigma_eff] (checked against mass_min / mass_max of binning.json to
1e-6 GeV); pairing = which OS mu mu mass is the A candidate of the template: "mass1" (1E2MU),
"low" (3MU lowM: mass1 = lower OS pair) or "high" (3MU highM: mass2 = higher OS pair), as
SignalRegionStudy sample_reader.pairing_rule. Channel keys are the RNTuple channel names (1E2MU, 3MU).

With --grid FILE (SignalRegionStudy/configs/grid.json, grids.MHc<X>.grid) it writes instead the windows
of the interpolated grid (default out configs/windows_grid.json): x0 and sigma_eff interpolated linearly in
mA between the MC points per channel (the MC points exactly), lo / hi = x0 -+ 10 sigma_eff, pairing by the
rule of SignalRegionStudy sample_reader (3MU: high iff mHc >= 100 and mA >= 60, else low), names in
p-notation (90.5 -> MHc130_MA90p5). The interpolation is a stand-in for the SignalRegionStudy shape
interpolation (results/interpolation/fits/.../polynomials.json) until the template chain fixes it.

Run (any python with json): python ParticleNet/python/make_windows_config.py [--templates DIR] [--out FILE]
                            python ParticleNet/python/make_windows_config.py --grid SignalRegionStudy/configs/grid.json
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DEF_TEMPLATES = "/mnt/SKNanoOutput_Run3/SignalRegionStudy/2024/HcToWABTagEff_v2/templates"
DEF_POINTS = os.path.join(REPO, "SignalRegionStudy", "configs", "masspoints.json")
DEF_OUT = os.path.join(os.path.dirname(HERE), "configs", "windows.json")
CHANNELS = {"1E2MU": "SR1E2Mu", "3MU": "SR3Mu"}
PAIRING = {"mass1": "mass1", "lowM": "low", "highM": "high"}
N_SIGMA = 10.0


def parse_point(name):
    m = re.fullmatch(r"MHc(\d+(?:p\d+)?)_MA(\d+(?:p\d+)?)", name)
    if not m:
        raise ValueError(f"bad mass point name {name}")
    f = lambda s: float(s.replace("p", "."))
    return f(m.group(1)), f(m.group(2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--templates", default=DEF_TEMPLATES)
    ap.add_argument("--points", default=DEF_POINTS)
    ap.add_argument("--set", default="baseline", help="key of masspoints.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--grid", default=None, help="grid.json: write the interpolated-grid windows instead")
    ap.add_argument("--mc-windows", default=DEF_OUT, help="MC-point windows (input of --grid)")
    ap.add_argument("--mhc", default="MHc130")
    args = ap.parse_args()
    if args.grid:
        return make_grid(args)
    args.out = args.out or DEF_OUT

    names = json.load(open(args.points))[args.set]
    points = []
    for name in names:
        mhc, ma = parse_point(name)
        chans = {}
        for ch, cat in CHANNELS.items():
            path = os.path.join(args.templates, name, "Baseline", "mc-signal", "2024", cat, "binning.json")
            b = json.load(open(path))
            (key, c), = b["categories"].items()
            x0 = c["fit_result"]["x0"]
            sig = c["sigma_eff"]
            lo, hi = x0 - N_SIGMA * sig, x0 + N_SIGMA * sig
            if abs(lo - c["mass_min"]) > 1e-6 or abs(hi - c["mass_max"]) > 1e-6:
                raise RuntimeError(f"{path}: window [{c['mass_min']}, {c['mass_max']}] != x0 -+ 10 sigma_eff")
            chans[ch] = {"x0": x0, "sigma_eff": sig, "lo": lo, "hi": hi, "pairing": PAIRING[c["pairing"]],
                         "category": key}
        points.append({"name": name, "mHc": mhc, "mA": ma, "channels": chans})
    points.sort(key=lambda p: p["mA"])
    out = {"meta": {"doc": "mA windows of the parametric ParticleNet (PLAN_ParticleNet P3/P7): window = "
                           "[x0 - 10 sigma_eff, x0 + 10 sigma_eff] of the SignalRegionStudy DCB fit per channel; "
                           "pairing: A-candidate mass of the template (mass1 | low = mass1 | high = mass2)",
                    "source": args.templates, "points_file": args.points, "set": args.set, "n_sigma": N_SIGMA},
           "points": points}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {args.out}: {len(points)} points")


def ma_token(v):
    t = f"{round(v, 2):g}"
    return "MA" + t.replace(".", "p")


def make_grid(args):
    mc = json.load(open(args.mc_windows))
    pts = sorted(mc["points"], key=lambda p: p["mA"])
    grid = json.load(open(args.grid))["grids"][args.mhc]["grid"]
    mhc = float(args.mhc[3:])
    xs = [p["mA"] for p in pts]
    out_pts = []
    for ma in grid:
        chans = {}
        for ch in CHANNELS:
            x0s = [p["channels"][ch]["x0"] for p in pts]
            sgs = [p["channels"][ch]["sigma_eff"] for p in pts]
            interp = lambda ys: next((ys[i] + (ys[i + 1] - ys[i]) * (ma - xs[i]) / (xs[i + 1] - xs[i])
                                      for i in range(len(xs) - 1) if xs[i] <= ma <= xs[i + 1]),
                                     ys[0] if ma < xs[0] else ys[-1])
            x0, sg = interp(x0s), interp(sgs)
            pairing = "mass1" if ch == "1E2MU" else ("high" if (mhc >= 100 and ma >= 60) else "low")
            chans[ch] = {"x0": x0, "sigma_eff": sg, "lo": x0 - N_SIGMA * sg, "hi": x0 + N_SIGMA * sg,
                         "pairing": pairing, "interpolated": ma not in xs}
        out_pts.append({"name": f"{args.mhc}_{ma_token(ma)}", "mHc": mhc, "mA": float(ma), "channels": chans})
    out = {"meta": {"doc": "windows of the interpolated grid: x0, sigma_eff linear in mA between the MC points "
                           "(make_windows_config.py --grid)", "grid_file": os.path.abspath(args.grid),
                    "mc_windows": os.path.abspath(args.mc_windows), "n_sigma": N_SIGMA}, "points": out_pts}
    path = args.out or os.path.join(os.path.dirname(DEF_OUT), "windows_grid.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {path}: {len(out_pts)} points")


if __name__ == "__main__":
    main()
