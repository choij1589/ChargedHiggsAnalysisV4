"""Z peak shapes, data vs simulation, with corrected and with MiniAOD lepton momenta.

  python DiLepton/python/plotZPeak.py [--style an|pw]

Tests the lepton momentum scale and resolution corrections (muons: MUO scale and
smearing; electrons: EGM scale in data, smearing in MC). Both shapes are
normalized to unit area in 81-101 GeV, so SFs and normalization do not enter.
The mean and RMS in the window are printed on the plot and in zpeak.txt.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Common" / "Tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import histutils  # noqa: E402
import plotter  # noqa: E402
from plot import CHANNELS, ERA  # noqa: E402

WINDOW = [81, 101]
TITLES = {"DIMU": "#mu#mu", "ZEE": "ee"}


def stats(h):
    h2 = plotter.prepare(h, {"xRange": WINDOW})
    return h2.GetMean(), h2.GetRMS()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    args = ap.parse_args()
    groups = plotter.load_json("groups.json")["DiLepton"]
    members = [m for g in groups["order"] for m in groups["groups"][g]["members"]]
    lines = []
    for ch in ("DIMU", "ZEE"):
        c = CHANNELS[ch]
        src = histutils.Source("DiLepton", c["flags"], ERA)
        for key, tag, title in (("pair/mass", "corrected", "m"), ("pair/massMiniAOD", "MiniAOD", "m^{MiniAOD}")):
            data = histutils.data_hist(src, c["pds"], ch, key)
            mc = histutils.total(src, members, ch, key, "Central")
            (md, sd), (mm, sm) = stats(data), stats(mc)
            lines.append(f"{ch} {tag:9s} data mean {md:.3f} rms {sd:.3f} | MC mean {mm:.3f} rms {sm:.3f} | "
                         f"shift {md - mm:+.3f} GeV")
            cfg = {"xTitle": f"{title}({TITLES[ch]}) [GeV]", "xRange": WINDOW, "normalize": True,
                   "rTitle": "Sim. / Data", "rRange": [0.8, 1.2], "caption": c["caption"] + [f"{tag} p_{{T}}"],
                   "text": [f"Data: mean {md:.2f}, RMS {sd:.2f} GeV", f"Sim.: mean {mm:.2f}, RMS {sm:.2f} GeV"]}
            curves = [("Data", data, "#000000", "data"), ("Simulation", mc, "#3f90da", "line")]
            path = plotter.output_path(args.style, ERA, "DiLepton", ch, f"zpeak_{tag}", "Central")
            plotter.ShapeCanvas(curves, cfg, style=args.style, era=ERA).draw().save(path)
    out = plotter.plot_dir("DiLepton", "an", ERA) / "zpeak.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
