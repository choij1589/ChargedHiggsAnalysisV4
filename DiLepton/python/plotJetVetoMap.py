"""Jet eta-phi maps before and after the event-level jet veto map (JERC asks for these in the AN).

  python DiLepton/python/plotJetVetoMap.py [--style an|pw] [--channel DIMU]

Jets: the veto-map selection (tightLepVeto, pT > 15 GeV, EM fraction < 0.9), filled
for every event passing the noise filters, before any lepton selection
(JetEtaPhi/{BeforeEventVeto,PassedEventVeto}_Run3/eta_phi). Data of the channel's
primary datasets and the sum of all simulated samples (normalization weights only).
Maps: data before, data after, data removed (before - after), simulation before and after.
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--style", default="an", choices=list(plotter.STYLES))
    ap.add_argument("--channel", default="DIMU", choices=list(CHANNELS))
    args = ap.parse_args()
    c = CHANNELS[args.channel]
    src = histutils.Source("DiLepton", c["flags"], ERA)
    groups = plotter.load_json("groups.json")["DiLepton"]
    members = [m for g in groups["order"] for m in groups["groups"][g]["members"]]
    datas = src.data_samples(c["pds"])

    def get(samples, stage):
        return histutils.add([src.get(s, f"JetEtaPhi/{stage}_Run3/eta_phi") for s in samples], f"{stage}")

    maps = {"data_before": (get(datas, "BeforeEventVeto"), True), "data_after": (get(datas, "PassedEventVeto"), True),
            "sim_before": (get(members, "BeforeEventVeto"), False), "sim_after": (get(members, "PassedEventVeto"), False)}
    removed = maps["data_before"][0].Clone("data_removed")
    removed.Add(maps["data_after"][0], -1)
    maps["data_removed"] = (removed, True)
    pds = ", ".join(c["pds"])
    for name, (h, is_data) in maps.items():
        what = "Data" if is_data else "Simulation"
        stage = {"before": "before the veto", "after": "after the veto",
                 "removed": "all jets of vetoed events"}[name.split("_")[1]]
        cfg = {"xTitle": "#eta", "yTitle": "#phi", "zTitle": "Jets", "logz": True,
               "caption": [f"{what} ({pds if is_data else 'all samples'}), {stage}"]}
        path = plotter.output_path(args.style, ERA, "DiLepton", "JetVetoMap", f"{args.channel}_{name}", "Central")
        plotter.Map2DCanvas(h, cfg, style=args.style, era=ERA, has_data=is_data).draw().save(path)
    nb, na = maps["data_before"][0].Integral(), maps["data_after"][0].Integral()
    mb, ma = maps["sim_before"][0].Integral(), maps["sim_after"][0].Integral()
    print(f"jets kept: data {na / nb:.4f}, simulation {ma / mb:.4f}")


if __name__ == "__main__":
    main()
