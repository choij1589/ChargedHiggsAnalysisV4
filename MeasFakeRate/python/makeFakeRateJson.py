"""Fake rates as correctionlib JSON (PLAN_BkgEst step 3).

  python MeasFakeRate/python/makeFakeRateJson.py [--out MeasFakeRate/results/2024/fakerate_HcToWA.json]

Input: MeasFakeRate/results/2024/<flavour>/rates.json (measFakeRate.py --step rates, prompt scale from the
bounded MT fit, user 2026-11-27). Corrections FakeRate_Muon (abseta = |eta|) and FakeRate_Electron
(abseta = |eta_SC|), inputs (abseta, ptcorr, syst), flow clamp in both (pT_corr above 200 GeV takes the
last bin; to be revisited with the application, F7). syst:
  Central; Stat_Up / Stat_Down (central +- statistical error);
  PromptNorm_Up / PromptNorm_Down (prompt scale x (1 +- |s_fit / s_Z - 1|));
  AwayJet_Up / AwayJet_Down (away jet pT > 60 / > 20 (mu) or > 30 (e) GeV);
  BTag (>= 1 b-tagged jet in the event);
  Total_Up / Total_Down: central +- the bin-by-bin total (stat (+) PromptNorm (+) AwayJet (+) BTag, the largest
      deviation of each group; plotFakeRate.total_unc): the up/down rates of the single shape nuisance per
      flavour (CMS_..._nonprompt_mu / _el, user 2026-11-27, F1);
  MC_QCD, MC_TT (nonprompt), MC_QCD_<cls>, MC_TT_<cls> (cls b, c, light).
Each variation is a full set of rates; in the fit one shape nuisance per flavour uses Total_Up/Down (F1, user 2026-11-27). Rates are clipped
to [0, 0.95]; a bin without a rate (data: already replaced by the previous pT bin in rates.json; MC:
NaN) takes the previous pT bin of its |eta| row, as F7 (user 2026-11-27).
"""
import argparse
import json
import math
from pathlib import Path

import correctionlib.schemav2 as cs

from plotFakeRate import total_unc

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "MeasFakeRate" / "results" / "2024"
AWAY = {"mu": ("Away60", "Away20"), "el": ("Away60", "Away30")}
NAME = {"mu": "FakeRate_Muon", "el": "FakeRate_Electron"}


def clip(x):
    return min(max(x, 0.), 0.95)


def fill_prev(vals):
    out = []
    for v in vals:
        if v is None or math.isnan(v):
            v = out[-1] if out else float("nan")
        out.append(v)
    if any(math.isnan(v) for v in out):
        raise SystemExit(f"row starts without a rate: {vals}")
    return out


def correction(fl):
    r = json.loads((RES / fl / "rates.json").read_text())
    ex, ey = r["eta"], r["pt"]
    sets = {}

    def grid(get):
        g = []
        for i in range(len(ex) - 1):
            g += [clip(v) for v in fill_prev([get(str(i), j) for j in range(len(ey) - 1)])]
        return g

    D = r["data"]
    sets["Central"] = grid(lambda i, j: D["Central"][i][j]["f"])
    sets["Stat_Up"] = grid(lambda i, j: D["Central"][i][j]["f"] + D["Central"][i][j]["err"])
    sets["Stat_Down"] = grid(lambda i, j: D["Central"][i][j]["f"] - D["Central"][i][j]["err"])
    sets["PromptNorm_Up"] = grid(lambda i, j: D["PromptNormUp"][i][j]["f"])
    sets["PromptNorm_Down"] = grid(lambda i, j: D["PromptNormDown"][i][j]["f"])
    up, dn = AWAY[fl]
    sets["AwayJet_Up"] = grid(lambda i, j: D[up][i][j]["f"])
    sets["AwayJet_Down"] = grid(lambda i, j: D[dn][i][j]["f"])
    sets["BTag"] = grid(lambda i, j: D["BTag"][i][j]["f"])
    tot = {str(i): total_unc(r, fl, str(i)) for i in range(len(ex) - 1)}
    sets["Total_Up"] = grid(lambda i, j: D["Central"][i][j]["f"] + tot[i][j]["total"])
    sets["Total_Down"] = grid(lambda i, j: D["Central"][i][j]["f"] - tot[i][j]["total"])
    for grp, lab in (("qcd", "QCD"), ("tt", "TT")):
        sets[f"MC_{lab}"] = grid(lambda i, j, g=grp: r["mc"][g]["nonprompt"][i][j]["f"])
        for cl in ("b", "c", "light"):
            sets[f"MC_{lab}_{cl}"] = grid(lambda i, j, g=grp, c=cl: r["mc"][g][c][i][j]["f"])
    content = [cs.CategoryItem(key=k, value=cs.MultiBinning(nodetype="multibinning", inputs=["abseta", "ptcorr"],
                                                           edges=[ex, ey], content=v, flow="clamp"))
               for k, v in sets.items()]
    corr = cs.Correction(
        name=NAME[fl], version=1,
        description=f"{NAME[fl]}: tight-to-loose rate in the QCD-enriched region, 2024 (MeasFakeRate production "
                    f"2026-11-27, prompt scale from the MT fit bounded to the Z-window scale +-30%); pT_corr = pT (1 + max(0, miniIso - 0.1))",
        inputs=[cs.Variable(name="abseta", type="real", description="|eta|" if fl == "mu" else "|eta_SC|"),
                cs.Variable(name="ptcorr", type="real", description="pT_corr [GeV]"),
                cs.Variable(name="syst", type="string", description=", ".join(sets))],
        output=cs.Variable(name="rate", type="real"),
        data=cs.Category(nodetype="category", input="syst", content=content))
    return corr, sets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(RES / "fakerate_HcToWA.json"))
    a = ap.parse_args()
    corrs = [correction(fl)[0] for fl in ("mu", "el")]
    cset = cs.CorrectionSet(schema_version=2, corrections=corrs,
                            description="HcToWA 2024 fake (tight-to-loose) rates (ChargedHiggsAnalysisV4 PLAN_BkgEst)")
    out = Path(a.out)
    out.write_text(cset.model_dump_json(exclude_unset=True, indent=1))
    import correctionlib
    ev = correctionlib.CorrectionSet.from_file(str(out))
    print("written", out)
    for n, pts in (("FakeRate_Muon", (11., 25., 70., 500.)), ("FakeRate_Electron", (16., 30., 70., 500.))):
        print(f"  {n} |eta| 0.5: " + ", ".join(f"pT {p:g}: {ev[n].evaluate(0.5, p, 'Central'):.3f} "
                                                f"(QCD {ev[n].evaluate(0.5, p, 'MC_QCD'):.3f})" for p in pts))


if __name__ == "__main__":
    main()
