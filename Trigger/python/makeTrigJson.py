"""Write the trigger-leg and pairwise-filter efficiencies as correctionlib JSON (PLAN_Trigger step 3).

  python Trigger/python/makeTrigJson.py [--out Trigger/data/2024/trigger_HcToWA.json]

Corrections (inputs, then ValType in effData, effDataUp, effDataDown, effMC, effMCUp, effMCDown):
  DblMu_Mu17Leg, DblMu_Mu8Leg   (abseta, pt)    tnp_tamsa results
        SKNanoOutput/TnP/2024/NUM_{Mu17Leg1,Mu8Leg2}_DEN_HcToWATight_2024/efficiency.root:
        nominal fit (data_s0m0, sim_s0m0), uncertainty = "data" / "sim" error (stat (+) the
        largest deviation of each systematic set, tnp_tamsa combination)
  EMu_Mu23Leg, EMu_Mu8Leg       (abseta, pt)    Trigger/results/2024/emu_legs.root
  EMu_Ele23Leg, EMu_Ele12Leg    (abssceta, pt)  (measEMuEff.py): data Clopper-Pearson
        (asymmetric), MC (TTLL powheg) weighted binomial; statistical only (user 2026-11-26)
  PairFilter                    (name: "DblMu_DZ", "EMu_DZ")  inclusive path-decision ratios
        (measEMuEff.py summary; dimuon DZ = DZ_Mass3p8; e-mu DZ of Mu23Ele12 for both paths).
        One number for all pT and eta (user 2026-11-26), so its data uncertainty covers the
        binned values: effDataUp/Down = effData x (1 +- sqrt(stat^2 + spread^2)), spread up/down =
        largest positive/negative deviation of the binned SF (data/TT, max|eta| and leading-pT
        bins with N_den >= 1000) from the inclusive SF (user 2026-11-26).
The MC closure (trigClosure.py) is a check of these uncertainties, not an uncertainty (user
2026-11-26): no closure term is written.
pT is the corrected pT (T4). Flow: clamp in |eta| and pT. The electron ECAL-gap cells
(1.4442 < |eta_SC| < 1.566, not selected by our ID) copy the 0.8-1.4442 row. Up/down are
clipped to [0, 1]. The per-event efficiency (T1) and SF are built in HcToWABase.
"""
import argparse
import json
import math
import re
from pathlib import Path

import correctionlib.schemav2 as cs
import ROOT

REPO = Path(__file__).resolve().parents[2]
TNP = REPO / "SKNanoOutput" / "TnP" / "2024"
RES = REPO / "Trigger" / "results" / "2024"
VALTYPES = ["effData", "effDataUp", "effDataDown", "effMC", "effMCUp", "effMCDown"]
GAP = (1.4442, 1.566)


def edges(axis):
    return [round(axis.GetBinLowEdge(i), 6) for i in range(1, axis.GetNbins() + 2)]


def clip(x):
    return min(max(x, 0.), 1.)


def multibinning(name, xname, ex, ey, cells, desc):
    """cells[(ix, iy)] = dict(valtype -> value), ix over |eta| bins, iy over pT bins (1-based)."""
    content = []
    for vt in VALTYPES:
        vals = [cells[(ix, iy)][vt] for ix in range(1, len(ex)) for iy in range(1, len(ey))]
        content.append(cs.CategoryItem(key=vt, value=cs.MultiBinning(
            nodetype="multibinning", inputs=[xname, "pt"], edges=[ex, ey], content=vals, flow="clamp")))
    return cs.Correction(
        name=name, description=desc, version=1,
        inputs=[cs.Variable(name=xname, type="real", description="|eta|" if xname == "abseta" else "|eta_SC|"),
                cs.Variable(name="pt", type="real", description="corrected pT [GeV]"),
                cs.Variable(name="ValType", type="string", description=", ".join(VALTYPES))],
        output=cs.Variable(name="eff", type="real"),
        data=cs.Category(nodetype="category", input="ValType", content=content))


def dimuon_leg(config, name):
    f = ROOT.TFile.Open(str(TNP / config / "efficiency.root"))
    h = {k: f.Get(k) for k in ("data", "sim", "data_s0m0", "sim_s0m0")}
    ex, ey = edges(h["data"].GetXaxis()), edges(h["data"].GetYaxis())
    cells = {}
    for ix in range(1, len(ex)):
        for iy in range(1, len(ey)):
            d, m = h["data_s0m0"].GetBinContent(ix, iy), h["sim_s0m0"].GetBinContent(ix, iy)
            ed, em = h["data"].GetBinError(ix, iy), h["sim"].GetBinError(ix, iy)
            if math.isnan(d) or math.isnan(m):
                raise SystemExit(f"{config}: NaN in cell {ix},{iy}")
            cells[(ix, iy)] = {"effData": d, "effDataUp": clip(d + ed), "effDataDown": clip(d - ed),
                               "effMC": m, "effMCUp": clip(m + em), "effMCDown": clip(m - em)}
    f.Close()
    return multibinning(name, "abseta", ex, ey, cells,
                        f"{name}: dimuon-path leg efficiency (tnp_tamsa {config}); error = stat (+) syst")


def emu_leg(leg, name):
    f = ROOT.TFile.Open(str(RES / "emu_legs.root"))
    g = lambda k: f.Get(f"{leg}/{leg}_{k}")
    d, dl, dh, m = g("data"), g("data_errlow"), g("data_errhigh"), g("sim")
    ex, ey = edges(d.GetXaxis()), edges(d.GetYaxis())
    electron = leg.startswith("Ele")
    cells = {}
    for ix in range(1, len(ex)):
        src = ix
        if electron and abs(ex[ix - 1] - GAP[0]) < 1e-4 and abs(ex[ix] - GAP[1]) < 1e-4:
            src = ix - 1  # ECAL gap: copy the barrel row below
        for iy in range(1, len(ey)):
            vd, vm = d.GetBinContent(src, iy), m.GetBinContent(src, iy)
            cells[(ix, iy)] = {"effData": vd, "effDataUp": clip(vd + dh.GetBinContent(src, iy)),
                               "effDataDown": clip(vd - dl.GetBinContent(src, iy)),
                               "effMC": vm, "effMCUp": clip(vm + m.GetBinError(src, iy)),
                               "effMCDown": clip(vm - m.GetBinError(src, iy))}
    f.Close()
    return multibinning(name, "abssceta" if electron else "abseta", ex, ey, cells,
                        f"{name}: e-mu path leg efficiency (MeasTrigEff, reference-trigger method); statistical error")


NMIN_SPREAD = 1000


def sf_spread(block_text, sf0):
    """Largest positive and negative relative deviation of the binned SF from sf0."""
    devs = []
    for lab in ("max|eta|", "lead pT"):
        line = re.search(re.escape(lab) + r" data/TT \(N_den\): (.*)", block_text).group(1)
        for d, m, n in re.findall(r"\S+: (\S+)/(\S+) \((\d+)\)", line):
            if int(n) >= NMIN_SPREAD:
                devs.append(float(d) / float(m) / sf0 - 1)
    return max(max(devs), 0.), max(-min(devs), 0.)


def pair_filters():
    text = (RES / "summary.txt").read_text()
    out = {}
    for key, block in (("DblMu_DZ", "DblMu_DZ"), ("EMu_DZ", "EMu_Mu23Ele12_DZ")):
        m = re.search(rf"## {block}\n  inclusive: N_den\(data\) \S+  data (\S+) \+(\S+) -(\S+)  TT (\S+) \+- (\S+)", text)
        if not m:
            raise SystemExit(f"{block} not found in summary.txt")
        d, dh, dl, mc, me = map(float, m.groups())
        up, dn = sf_spread(text.split(f"## {block}\n")[1].split("\n## ")[0], d / mc)
        out[key] = {"effData": d, "effDataUp": clip(d * (1 + math.hypot(dh / d, up))),
                    "effDataDown": clip(d * (1 - math.hypot(dl / d, dn))),
                    "effMC": mc, "effMCUp": clip(mc + me), "effMCDown": clip(mc - me)}
        print(f"  {key}: SF {d / mc:.5f}, binned spread +{up:.4f} -{dn:.4f}")
    content = [cs.CategoryItem(key=k, value=cs.Category(nodetype="category", input="ValType",
                                                        content=[cs.CategoryItem(key=vt, value=v[vt]) for vt in VALTYPES]))
               for k, v in out.items()]
    corr = cs.Correction(
        name="PairFilter", version=1,
        description="Pairwise filter efficiencies, inclusive (user 2026-11-26): DblMu_DZ (= DZ_Mass3p8), EMu_DZ (both e-mu paths); "
                    "data Up/Down include the spread of the binned SF (max|eta|, leading pT)",
        inputs=[cs.Variable(name="name", type="string", description="DblMu_DZ, EMu_DZ"),
                cs.Variable(name="ValType", type="string", description=", ".join(VALTYPES))],
        output=cs.Variable(name="eff", type="real"),
        data=cs.Category(nodetype="category", input="name", content=content))
    return corr, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(REPO / "Trigger" / "data" / "2024" / "trigger_HcToWA.json"))
    args = ap.parse_args()
    pf, pvals = pair_filters()
    corrs = [dimuon_leg("NUM_Mu17Leg1_DEN_HcToWATight_2024", "DblMu_Mu17Leg"),
             dimuon_leg("NUM_Mu8Leg2_DEN_HcToWATight_2024", "DblMu_Mu8Leg"),
             emu_leg("Mu23", "EMu_Mu23Leg"), emu_leg("Mu8", "EMu_Mu8Leg"),
             emu_leg("Ele23", "EMu_Ele23Leg"), emu_leg("Ele12", "EMu_Ele12Leg"), pf]
    cset = cs.CorrectionSet(schema_version=2, description="HcToWA 2024 trigger legs and pairwise filters (ChargedHiggsAnalysisV4 PLAN_Trigger)",
                            corrections=corrs)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(cset.model_dump_json(exclude_unset=True, indent=1))
    # read back
    import correctionlib
    ev = correctionlib.CorrectionSet.from_file(str(out))
    print("written", out)
    for name, x in (("DblMu_Mu17Leg", 0.5), ("DblMu_Mu8Leg", 0.5), ("EMu_Mu23Leg", 0.5), ("EMu_Mu8Leg", 0.5),
                    ("EMu_Ele23Leg", 0.5), ("EMu_Ele12Leg", 0.5)):
        print(f"  {name:14s} |eta| {x} pT 40: data {ev[name].evaluate(x, 40., 'effData'):.4f}  MC {ev[name].evaluate(x, 40., 'effMC'):.4f}"
              f"  gap/flow check {ev[name].evaluate(1.5, 1000., 'effData'):.4f}")
    for k in pvals:
        pf_ = ev["PairFilter"]
        print(f"  PairFilter {k}: data {pf_.evaluate(k, 'effData'):.5f} (+{pf_.evaluate(k, 'effDataUp'):.5f} -{pf_.evaluate(k, 'effDataDown'):.5f})"
              f" MC {pf_.evaluate(k, 'effMC'):.5f}")


if __name__ == "__main__":
    main()
