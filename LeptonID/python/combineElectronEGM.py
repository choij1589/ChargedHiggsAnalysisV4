"""Electron ID SFs with EGM's 2024 uncertainty rule (user decision 2026-11-25).

  python LeptonID/python/combineElectronEGM.py [--configs NAME,...]

Input: SKNanoOutput/TnP/2024/<config>/efficiency.root (tnp_tamsa summary; members
s0m0 nominal, s1m0 altSig (EGM model: gen-level Z line shape x RooCBExGaussShapeTNP),
s2m0 altBkg (exponential); s3m0 altMC is not used here).
Rule, which reproduces EGM's published 2024 uncertainties (electron.json sfup - sf;
docs/LOG_ObjectID.md 2026-11-25):
  central  SF = eff_data(s0m0) / eff_MC(s0m0)
  stat     SF * sqrt((err_data/eff_data)^2 + (err_MC/eff_MC)^2), nominal fits, per cell
  syst     sqrt(dAltSig^2 + dAltBkg^2) / eff_MC(s0m0), d = eff_data(member) - eff_data(s0m0),
           symmetrized in |eta|: the larger value of the two cells mirrored in eta
           (same pT bin) is used for both
  total    sqrt(stat^2 + syst^2)
Output: SKNanoOutput/TnP/2024/<config>/sf_egm.root with TH2Ds
  sf (total error), sf_stat, sf_sys (systematic error), data, sim (nominal, stat error),
  dAltSig, dAltBkg (signed SF-level deviations before symmetrization).
Cells whose nominal or alternative efficiency is missing or NaN are reported and
left empty (0).
"""
import argparse
import math
from pathlib import Path

import ROOT

REPO = Path(__file__).resolve().parents[2]
D = REPO / "SKNanoOutput" / "TnP" / "2024"
CONFIGS = ["NUM_HcToWATight_DEN_RecoElectrons_2024", "NUM_wp90noiso_DEN_RecoElectrons_2024", "NUM_cutBasedTight_DEN_RecoElectrons_2024"]


def ok(v):
    return v == v and v > 0


def combine(config):
    f = ROOT.TFile.Open(str(D / config / "efficiency.root"))
    h = {k: f.Get(k) for k in ("data_s0m0", "data_s1m0", "data_s2m0", "sim_s0m0")}
    for v in h.values():
        v.SetDirectory(0)
    f.Close()
    out = {k: h["data_s0m0"].Clone(k) for k in ("sf", "sf_stat", "sf_sys", "dAltSig", "dAltBkg")}
    for v in out.values():
        v.Reset()
        v.SetDirectory(0)
    out["data"], out["sim"] = h["data_s0m0"].Clone("data"), h["sim_s0m0"].Clone("sim")
    raw_syst, bad = {}, []
    nx, ny = h["data_s0m0"].GetNbinsX(), h["data_s0m0"].GetNbinsY()
    for ix in range(1, nx + 1):
        for iy in range(1, ny + 1):
            d0, m0 = h["data_s0m0"].GetBinContent(ix, iy), h["sim_s0m0"].GetBinContent(ix, iy)
            d1, d2 = h["data_s1m0"].GetBinContent(ix, iy), h["data_s2m0"].GetBinContent(ix, iy)
            if d0 == 0 and m0 == 0:
                continue  # empty cell (ECAL gap)
            if not all(ok(v) for v in (d0, m0, d1, d2)):
                bad.append((ix, iy, d0, m0, d1, d2))
                continue
            sf = d0 / m0
            stat = sf * math.hypot(h["data_s0m0"].GetBinError(ix, iy) / d0, h["sim_s0m0"].GetBinError(ix, iy) / m0)
            out["sf_stat"].SetBinContent(ix, iy, sf)
            out["sf_stat"].SetBinError(ix, iy, stat)
            out["dAltSig"].SetBinContent(ix, iy, (d1 - d0) / m0)
            out["dAltBkg"].SetBinContent(ix, iy, (d2 - d0) / m0)
            raw_syst[(ix, iy)] = math.hypot(d1 - d0, d2 - d0) / m0
    for (ix, iy), s in raw_syst.items():
        x = h["data_s0m0"].GetXaxis().GetBinCenter(ix)
        jx = h["data_s0m0"].GetXaxis().FindBin(-x)
        s = max(s, raw_syst.get((jx, iy), 0.))
        sf, stat = out["sf_stat"].GetBinContent(ix, iy), out["sf_stat"].GetBinError(ix, iy)
        out["sf_sys"].SetBinContent(ix, iy, sf)
        out["sf_sys"].SetBinError(ix, iy, s)
        out["sf"].SetBinContent(ix, iy, sf)
        out["sf"].SetBinError(ix, iy, math.hypot(stat, s))
    fo = ROOT.TFile(str(D / config / "sf_egm.root"), "RECREATE")
    for k, v in out.items():
        v.SetTitle(k)
        v.Write(k)
    fo.Close()
    tot = sorted(out["sf"].GetBinError(ix, iy) for (ix, iy) in raw_syst)
    print("%s: %d cells, total SF unc. median %.4f, max %.4f; cells left empty (missing/NaN): %d %s" % (
        config, len(raw_syst), tot[len(tot) // 2], tot[-1], len(bad), bad[:4]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--configs", default="")
    args = ap.parse_args()
    ROOT.gROOT.SetBatch(True)
    for c in CONFIGS:
        if not args.configs or c in args.configs.split(","):
            combine(c)
