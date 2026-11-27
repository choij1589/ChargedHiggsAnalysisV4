"""Write our lepton ID scale factors as correctionlib JSON (PLAN_LeptonID.md step 6).

  python LeptonID/python/makeSFJson.py [--outdir LeptonID/data/2024]

Inputs (SKNanoOutput/TnP/2024/<config>/):
  muons      NUM_HcToWATight_DEN_TrackerMuons_2024/efficiency.root (tnp_tamsa combination:
             "sf" = nominal with stat (+) syst, "sf_sys" = syst only; data_s0m0 / sim_s0m0)
  electrons  NUM_HcToWATight_DEN_RecoElectrons_2024/sf_egm.root (EGM 2024 rule,
             combineElectronEGM.py: sf, sf_stat, sf_sys, data, sim)
Output: <outdir>/muon_ID_HcToWA.json (correction "HcToWATight_Muon_ID", inputs eta (signed),
pt, ValType) and <outdir>/electron_ID_HcToWA.json ("HcToWATight_Electron_ID", inputs
sceta, pt, ValType). ValType: sf, sfup, sfdown (total), sfstat, sfsyst (absolute
uncertainties), effData, effMC. pT is the scale/smear-corrected pT (L4, revised
2026-11-25). Flow: clamp in eta and pt (muons: pT > 200 GeV and < 10 GeV take the
edge bins). Electrons: the ECAL-gap cells (not measured, never looked up) are set to
sf = 1 with zero uncertainty; above 300 GeV the 200-300 GeV SF is used with its total
uncertainty scaled by pT / 300 GeV up to 1 TeV and constant above (EGM 2024
prescription, L8; the linear form is our reading of "growing linearly to 1 TeV").
Checks: every non-gap cell has 0 < sf, finite uncertainties; the JSON is read back
with correctionlib and evaluated at every cell centre against the input histograms.
"""
import argparse
import json
import math
from pathlib import Path

import correctionlib
import correctionlib.schemav2 as cs
import ROOT

REPO = Path(__file__).resolve().parents[2]
D = REPO / "SKNanoOutput" / "TnP" / "2024"
VALTYPES = ["sf", "sfup", "sfdown", "sfstat", "sfsyst", "effData", "effMC"]


def edges(axis):
    return [axis.GetBinLowEdge(i) for i in range(1, axis.GetNbins() + 2)]


def cell_values(h, ix, iy):
    sf, tot = h["sf"].GetBinContent(ix, iy), h["sf"].GetBinError(ix, iy)
    syst = h["sys"].GetBinError(ix, iy)
    stat = math.sqrt(max(tot * tot - syst * syst, 0.))
    return {"sf": sf, "sfup": sf + tot, "sfdown": sf - tot, "sfstat": stat, "sfsyst": syst,
            "effData": h["data"].GetBinContent(ix, iy), "effMC": h["sim"].GetBinContent(ix, iy)}


def muon(outdir):
    f = ROOT.TFile.Open(str(D / "NUM_HcToWATight_DEN_TrackerMuons_2024" / "efficiency.root"))
    h = {"sf": f.Get("sf"), "sys": f.Get("sf_sys"), "data": f.Get("data_s0m0"), "sim": f.Get("sim_s0m0")}
    for v in h.values():
        v.SetDirectory(0)
    f.Close()
    ex, ey = edges(h["sf"].GetXaxis()), edges(h["sf"].GetYaxis())
    content = {}
    for vt in VALTYPES:
        vals = []
        for ix in range(1, len(ex)):
            for iy in range(1, len(ey)):
                v = cell_values(h, ix, iy)
                assert v["sf"] > 0 and all(math.isfinite(x) for x in v.values()), (ix, iy, v)
                vals.append(v[vt])
        content[vt] = cs.MultiBinning(nodetype="multibinning", inputs=["eta", "pt"], edges=[ex, ey], content=vals, flow="clamp")
    corr = cs.Correction(
        name="HcToWATight_Muon_ID", version=1,
        description="HcToWA tight muon ID / TrackerMuons, 2024 (tag and probe, tnp_tamsa; MUO 2024 setup). "
                    "pt: scale/smear-corrected muon pT. sfup/sfdown: stat (+) syst (tnp_tamsa: largest deviation per systematic set).",
        inputs=[cs.Variable(name="eta", type="real", description="muon eta (signed)"),
                cs.Variable(name="pt", type="real", description="corrected muon pT [GeV]"),
                cs.Variable(name="ValType", type="string", description=", ".join(VALTYPES))],
        output=cs.Variable(name="value", type="real"),
        data=cs.Category(nodetype="category", input="ValType", content=[cs.CategoryItem(key=k, value=v) for k, v in content.items()]))
    write(corr, outdir / "muon_ID_HcToWA.json")
    return corr, h


def electron(outdir):
    f = ROOT.TFile.Open(str(D / "NUM_HcToWATight_DEN_RecoElectrons_2024" / "sf_egm.root"))
    h = {"sf": f.Get("sf"), "sys": f.Get("sf_sys"), "data": f.Get("data"), "sim": f.Get("sim")}
    for v in h.values():
        v.SetDirectory(0)
    f.Close()
    ex, ey = edges(h["sf"].GetXaxis()), edges(h["sf"].GetYaxis())
    assert abs(ey[-1] - 300.) < 1e-6
    ey_out = ey + [1000.]
    content = {}
    for vt in VALTYPES:
        rows = []
        for ix in range(1, len(ex)):
            gap = h["sf"].GetBinContent(ix, 1) <= 0
            for iy in range(1, len(ey)):
                if gap:
                    rows.append(1.0 if vt in ("sf", "sfup", "sfdown") else 0.0)
                    continue
                v = cell_values(h, ix, iy)
                assert v["sf"] > 0 and all(math.isfinite(x) for x in v.values()), (ix, iy, v)
                rows.append(v[vt])
            # 300 GeV - 1 TeV (and above, by clamping pt at 1 TeV): the 200-300 GeV values,
            # total uncertainty scaled by pt / 300
            last = len(ey) - 1
            if gap:
                rows.append(1.0 if vt in ("sf", "sfup", "sfdown") else 0.0)
                continue
            v = cell_values(h, ix, last)
            tot = v["sfup"] - v["sf"]
            if vt in ("sfup", "sfdown"):
                sign = "+" if vt == "sfup" else "-"
                rows.append(cs.Formula(nodetype="formula", variables=["pt"], parser="TFormula",
                                       expression="[0]%s[1]*min(x,1000.)/300." % sign, parameters=[v["sf"], tot]))
            elif vt in ("sfstat", "sfsyst"):
                rows.append(cs.Formula(nodetype="formula", variables=["pt"], parser="TFormula",
                                       expression="[0]*min(x,1000.)/300.", parameters=[v[vt]]))
            else:
                rows.append(v[vt])
        content[vt] = rows
    nodes = {}
    for vt, rows in content.items():
        # multibinning content must be numbers, so build eta -> pt binning nodes instead
        per_eta, k = [], 0
        for ix in range(1, len(ex)):
            vals = rows[k:k + len(ey_out) - 1]
            k += len(ey_out) - 1
            per_eta.append(cs.Binning(nodetype="binning", input="pt", edges=ey_out, content=vals, flow="clamp"))
        nodes[vt] = cs.Binning(nodetype="binning", input="sceta", edges=ex, content=per_eta, flow="clamp")
    corr = cs.Correction(
        name="HcToWATight_Electron_ID", version=1,
        description="HcToWA tight electron ID / reco electrons, 2024 (tag and probe, tnp_tamsa; EGM 2024 setup and "
                    "uncertainty rule: altSig and altBkg data deviations / effMC (+) stat, systematic symmetrized in |eta_SC|). "
                    "pt: scale/smear-corrected electron pT. ECAL-gap cells: sf = 1 (not measured). Above 300 GeV: the 200-300 GeV "
                    "SF with its uncertainty scaled by pt/300 up to 1 TeV.",
        inputs=[cs.Variable(name="sceta", type="real", description="electron supercluster eta"),
                cs.Variable(name="pt", type="real", description="corrected electron pT [GeV]"),
                cs.Variable(name="ValType", type="string", description=", ".join(VALTYPES))],
        output=cs.Variable(name="value", type="real"),
        data=cs.Category(nodetype="category", input="ValType", content=[cs.CategoryItem(key=k, value=v) for k, v in nodes.items()]))
    write(corr, outdir / "electron_ID_HcToWA.json")
    return corr, h


def write(corr, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    cset = cs.CorrectionSet(schema_version=2, description="ChargedHiggsAnalysisV4 lepton ID scale factors, 2024", corrections=[corr])
    path.write_text(cset.model_dump_json(exclude_unset=True, indent=1) if hasattr(cset, "model_dump_json") else cset.json(exclude_unset=True, indent=1))


def check(path, name, h, gap_ok):
    c = correctionlib.CorrectionSet.from_file(str(path))[name]
    worst, n = 0., 0
    for ix in range(1, h["sf"].GetNbinsX() + 1):
        for iy in range(1, h["sf"].GetNbinsY() + 1):
            if h["sf"].GetBinContent(ix, iy) <= 0:
                assert gap_ok
                continue
            x, y = h["sf"].GetXaxis().GetBinCenter(ix), h["sf"].GetYaxis().GetBinCenter(iy)
            v = cell_values(h, ix, iy)
            for vt in VALTYPES:
                worst = max(worst, abs(c.evaluate(x, y, vt) - v[vt]))
            n += 1
    print("%s: %d cells read back, max |json - input| = %.2e" % (path.name, n, worst))
    assert worst < 1e-9
    return c


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default=str(REPO / "LeptonID" / "data" / "2024"))
    args = ap.parse_args()
    out = Path(args.outdir)
    _, hm = muon(out)
    check(out / "muon_ID_HcToWA.json", "HcToWATight_Muon_ID", hm, False)
    _, he = electron(out)
    ce = check(out / "electron_ID_HcToWA.json", "HcToWATight_Electron_ID", he, True)
    for pt in (250., 300., 650., 1000., 2000.):
        print("electron sceta 0.4: pt %6.0f sf %.4f sfup %.4f sfdown %.4f" % (pt, ce.evaluate(0.4, pt, "sf"), ce.evaluate(0.4, pt, "sfup"), ce.evaluate(0.4, pt, "sfdown")))
