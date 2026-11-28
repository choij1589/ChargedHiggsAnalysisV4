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

Run (any python with json): python ParticleNet/python/make_windows_config.py [--templates DIR] [--out FILE]
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
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()

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


if __name__ == "__main__":
    main()
