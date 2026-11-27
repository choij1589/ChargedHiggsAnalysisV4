#!/usr/bin/env python3
"""Build config/xsec_2024.csv: the single source of the 2024 MC cross sections.

Every MC sample on KNU gets one row with the value SKNano uses (pb), its class and
its reference. Classes:
  HO      a higher-order calculation for the same phase space and decay
          (FEWZ, MATRIX, LHC Top WG, LHCHWG), used directly: the generator
          cross section never enters the normalization (weight = xsec*lumi*w/sumW).
  HO*K    the calculation is inclusive but the sample has cuts: generator value
          (XSDB) times K = sigma_HO / sigma_NLO (inclusive), as in AN-25-154.
  GEN     no higher-order calculation: the generator value from XSDB.
  PENDING no value yet; the note says what is needed.
Higher-order values and K-factors follow AN-25-154 (Sections/Dataset.tex, Run 3
table and K-factor paragraph) unless the note says otherwise. Generator values come
from XSDB records of the 2024 sample itself when one exists, otherwise from the
record named in the note. The XSDB value is kept for every row as a cross-check,
with the AN-25-154 value where the process was used there. `flag` marks rows that
need a decision.

Usage: make_xsec_table_2024.py --info CommonSampleInfo.json --xsdb config/xsdb_2024_raw_<date>.json
                               --pds <file with the KNU MC dataset names> --out config/xsec_2024.csv
"""
import argparse
import csv
import json
import re
import sys

# Branching ratios as formula strings, so that xsec_formula reads exactly as its source.
BR_W_LNU = "(3*0.1086)"         # PDG, l = e, mu, tau
BR_W_QQ = "0.6741"              # PDG
BR_H_NONBB = "(1-0.5824)"       # YR4, mH = 125 GeV
SIGMA_TT = 923.6                # NNLO+NNLL, 13.6 TeV (TTbarXsecRecommedation)

# MATRIX v2.1, 13.6 TeV (AN-25-154 docs/CMS_MATRIXCrossSectionsat13p6TeV.md), fb, NNLO QCD.
# WZ -> 3l nu, m_OSSF > 4 GeV: per charge, 6 different-flavour + 3 same-flavour (W, Z) combinations.
WZ3L_NNLO_PB = (6 * 240.8 + 3 * 239.7 + 6 * 351.2 + 3 * 350.2) / 1000.0
# ZZ -> 4l, m_OSSF > 4 GeV: 3 different-flavour (eemumu-like) + 3 same-flavour (eeee-like).
# MATRIX NNLO QCD already contains loop-induced gg -> ZZ at LO (27.3 / 7.6 fb per channel);
# nNNLO = NNLO + (NLO_gg - LO_gg) carries gg at NLO (44.3 / 13.3 fb).
ZZ4L_NNLO_PB = (3 * 375.1 + 3 * 160.2) / 1000.0          # qqbar + gg(LO)
ZZ4L_QQ_PB = (3 * (375.1 - 27.3) + 3 * (160.2 - 7.6)) / 1000.0   # qqbar only
ZZ4L_NNNLO_GG_PB = (3 * 392.1 + 3 * 165.9) / 1000.0      # qqbar + gg(NLO)
# W -> l nu per flavour, NNLO QCD: e- nubar + e+ nu.
W_LNU_NNLO_PB = 9045.8 + 12170.9

AN = "AN-25-154 Dataset.tex"

# alias -> (class, value or formula, order, reference, note, flag, an25154_value)
# For HO*K the value is "K" and the generator value is taken from XSDB (or `gen` in note).
ROWS = {}
def ho(alias, value, order, ref, note="", flag="", an=None):
    ROWS[alias] = ("HO", value, order, ref, note, flag, an)
def hok(alias, gen, k, order, ref, note="", flag="", an=None):
    ROWS[alias] = ("HO*K", (gen, k), order, ref, note, flag, an)
def gen(alias, note="", flag="", an=None, value=None, order="generator"):
    ROWS[alias] = ("GEN", value, order, "XSDB", note, flag, an)
def pending(alias, note, flag="decide"):
    ROWS[alias] = ("PENDING", None, "", "", note, flag, None)

# --- ttbar and single top: LHC Top WG x BR (AN-25-154 Run 3 values) ---
ho("TTLL_powheg", f"{SIGMA_TT}*{BR_W_LNU}**2", "NNLO+NNLL", "TTbarXsecRecommedation", an=98.03)
ho("TTLJ_powheg", f"{SIGMA_TT}*2*{BR_W_LNU}*{BR_W_QQ}", "NNLO+NNLL", "TTbarXsecRecommedation", an=405.69)
ho("TTLJ_powheg_CustomBPH", f"{SIGMA_TT}*2*{BR_W_LNU}*{BR_W_QQ}", "NNLO+NNLL", "TTbarXsecRecommedation", note="same PD as TTLJ_powheg")
ho("TTJJ_powheg", f"{SIGMA_TT}*{BR_W_QQ}**2", "NNLO+NNLL", "TTbarXsecRecommedation")
for a in ("ST_tW_top_Semilep", "ST_tW_antitop_Semilep"):
    ho(a, 19.36, "NLO+NNLL", "SingleTopNNLORef,SingleTop_tW_NNLL", an=19.36,
       note="2024 shared entry had 19.30 (87.9 pb x BR)")
for a in ("ST_tW_top_Lep", "ST_tW_antitop_Lep"):
    ho(a, 4.76, "NLO+NNLL", "SingleTopNNLORef,SingleTop_tW_NNLL", an=4.76,
       note="2024 shared entry had 4.665 (87.9 pb x BR)")
ho("ST_tch_top_lep", f"145.0*{BR_W_LNU}", "NNLO QCD", "SingleTopNNLORef,SingleTop_tchannel_NNLO",
   note="AN-25-154 used the inclusive-decay sample (145.0 pb); 2024 sample is leptonic", an=145.0)
ho("ST_tch_antitop_lep", f"87.2*{BR_W_LNU}", "NNLO QCD", "SingleTopNNLORef,SingleTop_tchannel_NNLO",
   note="AN-25-154 used the inclusive-decay sample (87.2 pb); 2024 sample is leptonic", an=87.2)
ho("ST_tch_top_had", f"145.0*{BR_W_QQ}", "NNLO QCD", "SingleTopNNLORef,SingleTop_tchannel_NNLO")
ho("ST_tch_antitop_had", f"87.2*{BR_W_QQ}", "NNLO QCD", "SingleTopNNLORef,SingleTop_tchannel_NNLO")
ho("ST_sch_top_Lep", 3.7, "NNLO QCD", "SingleTopNNLORef,SingleTop_schannel_NNLO", an=3.7, flag="check",
   note="LHC Top WG SingleTopNNLORef (NNLO QCD, Liu & Gao PRD 98 (2018) 071501): 7.244 pb x BR(W->lnu) = 2.360, "
        "which is the 2024 shared entry (mislabelled 'NLO parametrization'). AN-25-154's 3.7 (x1.57) has no formula "
        "and does not match its own reference. Proposed: 2.360. XSDB LO 2.278")
ho("ST_sch_antitop_Lep", 2.322, "NNLO QCD", "SingleTopNNLORef,SingleTop_schannel_NNLO", an=2.322, flag="check",
   note="LHC Top WG SingleTopNNLORef (NNLO QCD): 4.534 pb x BR(W->lnu) = 1.477, the 2024 shared entry. "
        "AN-25-154's 2.322 (x1.57) does not match its own reference. Proposed: 1.477. XSDB LO 1.43")

# --- ttV, ttH, tZq ---
hok("ttZtoLL_MLL50toInf", None, 1.164, "aN3LO QCD + NLO EW", "ttZaN3LO", an=0.1006)
hok("ttZtoLL_MLL4to50", None, 1.164, "aN3LO QCD + NLO EW", "ttZaN3LO", an=0.04597)
hok("ttWtoLNu", 0.2502, 1.15, "aN3LO QCD", "ttWaN3LO", an=0.2877,
    note="generator value as in AN-25-154 (XSDB has only a Run3Summer22EE record, 0.2505)")
ho("ttHtoNonbb_M125", f"0.5700*{BR_H_NONBB}", "NLO QCD + NLO EW", "LHCHWG136TeV", an=0.24111,
   note="arXiv:2402.09955 Table 5 (mH = 125 GeV). Decided (user, 2026-11-24): BR(H->bb) = 0.5824 (YR4) for all Higgs "
        "samples; AN-25-154's 0.24111 implied BR(bb) ~ 0.577")
gen("tZq", an=0.08, note="AN-25-154 0.08 (XSDB of the 2022 sample)")
gen("tHq", an=0.7445); gen("tHW", an=0.1331)
gen("tWZ_thadWlep", an=0.00334, note="2024 XSDB (decided by the user, 2026-11-24); 11% below AN-25-154 (2022 sample). "
                              "No prediction beyond NLO QCD exists. CMS TOP-24-009 (arXiv:2510.19080) quotes 148 +10/-9 fb at NLO (DR1); x BR gives 3.28/3.28/1.59 fb, i.e. 2024 XSDB is ~10% lower")
gen("tWZ_tlepWhad", an=0.00334, note="2024 XSDB (decided by the user, 2026-11-24); 11% below AN-25-154 (2022 sample). "
                              "No prediction beyond NLO QCD exists. CMS TOP-24-009 (arXiv:2510.19080) quotes 148 +10/-9 fb at NLO (DR1); x BR gives 3.28/3.28/1.59 fb, i.e. 2024 XSDB is ~10% lower")
gen("tWZ_tlepWlep", an=0.00167, note="2024 XSDB (decided by the user, 2026-11-24); 17% below AN-25-154 (2022 sample). "
                              "No prediction beyond NLO QCD exists. CMS TOP-24-009 (arXiv:2510.19080) quotes 148 +10/-9 fb at NLO (DR1); x BR gives 3.28/3.28/1.59 fb, i.e. 2024 XSDB is ~10% lower")
gen("TTTT", an=0.009652, order="NLO QCD",
    note="XSDB record from Run3Summer22EE, labelled LO in XSDB; the aMC@NLO sample is NLO QCD (as in AN-25-154)")

# --- dibosons ---
ho("WZto3LNu", round(WZ3L_NNLO_PB, 4), "NNLO QCD", "MATRIX,CMS_MATRIX_XS_13p6TeV", an=5.847,
   note=f"MATRIX m_OSSF>4 GeV, l=e,mu,tau: {WZ3L_NNLO_PB:.3f} pb. AN-25-154 used 5.315 x K 1.10 = 5.847, "
        "where 5.315 is XSDB's value for the FxFx sample; XSDB for this POWHEG sample is 4.924. "
        "Decided (user, 2026-11-24): 5.32 pb; the Run 3 WZ normalization is corrected again by the Nj SF")
ho("WZto3LNu_1J_amcatnloFXFX", round(WZ3L_NNLO_PB, 4), "NNLO QCD", "MATRIX,CMS_MATRIX_XS_13p6TeV",
   note="forNextIteration N9 sample. Decided (user, 2026-11-24): MATRIX NNLO; the POWHEG sample stays the default WZ")
ho("ZZto4L", round(ZZ4L_NNNLO_GG_PB, 4), "nNNLO QCD (gg at NLO)", "MATRIX,CMS_MATRIX_XS_13p6TeV", an=1.774,
   note=f"qqbar sample normalized to qqbar + gg (decided by the user, 2026-11-24, for the feasibility study: no gg->ZZ "
        f"sample). nNNLO {ZZ4L_NNNLO_GG_PB:.3f} pb; NNLO {ZZ4L_NNLO_PB:.3f} pb includes gg at LO; qqbar only "
        f"{ZZ4L_QQ_PB:.3f} pb. AN-25-154: 1.529 x K 1.16 = 1.774 plus a separate gg->ZZ sample (K 1.7)")
ho("WW_pythia", 124.4, "NNLO QCD + NLO EW", "MATRIX,CMS_MATRIX_XS_13p6TeV", an=124.4)
ho("WZ_pythia", 54.1, "NNLO QCD + NLO EW", "MATRIX,CMS_MATRIX_XS_13p6TeV", an=54.1)
ho("ZZ_pythia", 17.6, "NNLO QCD + NLO EW", "MATRIX,CMS_MATRIX_XS_13p6TeV", an=17.6)
for a, an in (("WWW", 0.2328), ("WWZ", 0.1851), ("WZZ", 0.06206), ("ZZZ", 0.01591)):
    gen(a, an=an)

# --- Higgs ---
ho("ggHtoZZto4L_M125", 0.01434, "N3LO QCD", "LHCHWG136TeV", an=0.01434)
ho("VBFHtoZZto4L_M125", 0.00112, "NNLO QCD + NLO EW", "LHCHWG136TeV", an=0.00112)
# LHCHWG 13.6 TeV interim recommendations, arXiv:2402.09955 (LHCHWG-2024-001), mH = 125 GeV,
# NNLO QCD + NLO EW: Table 3 (W+H 0.8889, W-H 0.5677 pb), Table 4 (ZH 0.9439 pb, of which gg->ZH 0.1360 pb).
BR_NOTE = "BR(H->non-bb) = 1-0.5824 (YR4; decided by the user on 2026-11-24 for all Higgs samples)"
ho("WplusHtoNonbb_M125", f"0.8889*{BR_H_NONBB}", "NNLO QCD + NLO EW", "LHCHWG136TeV",
   note="arXiv:2402.09955 Table 3. " + BR_NOTE)
ho("WminusHtoNonbb_M125", f"0.5677*{BR_H_NONBB}", "NNLO QCD + NLO EW", "LHCHWG136TeV",
   note="arXiv:2402.09955 Table 3. " + BR_NOTE)
ho("ZHtoNonbb_M125", f"0.9439*{BR_H_NONBB}", "NNLO QCD + NLO EW", "LHCHWG136TeV",
   note="arXiv:2402.09955 Table 4: total 0.9439 pb incl. gg->ZH 0.1360 pb (14.4%). The qqbar-initiated FxFx sample "
        "is normalized to qqbar + gg (decided by the user, 2026-11-24, for the feasibility study). " + BR_NOTE)

# --- DY, W (per lepton flavour) ---
for fl in ("E", "Mu", "Tau"):
    for nj in ("2J", "4J"):
        ho(f"DYto2{fl}_{nj}_MLL50toInf", "6345.99/3", "NNLO QCD", "FEWZ",
           note="AN-25-154 all-flavour 6345.99 / 3; MATRIX NNLO QCD per flavour 2113.4 agrees")
        ho(f"DYto2{fl}_{nj}_MLL10to50", "19982.5/3", "NNLO QCD (scaled)", "FEWZ", flag="check",
           note="AN-25-154 all-flavour 19982.5 / 3. The 2024 per-flavour XSDB records (21140 FxFx, 17230 MLM; "
                "'Automatically computed') equal the 2022 all-flavour DYto2L records (20950, 17380), while the "
                "MLL-50 per-flavour record was 'Manually fixed' to 6688/3: XSDB 10-50 lacks the /3. 21140/3 = 7047 (NLO); "
                "6660.8/7047 = 0.945, as for MLL-50 (2115/2244 = 0.943)")
        ho(f"Wto{fl}Nu_{nj}", round(W_LNU_NNLO_PB, 1), "NNLO QCD", "MATRIX,CMS_MATRIX_XS_13p6TeV",
           note="MATRIX e-nubar + e+nu per flavour (decided by the user, 2026-11-24). AN-25-154 used XSDB NLO 64481.58 "
                "(all flavours) / 3 = 21493.9. The 2024 per-flavour XSDB records (~68k) carry the all-flavour value")

# --- conversions and others ---
for a in ("TTG_1J", "TTG_1J_PTG100toInf", "TTG_1J_PTG200toInf"):
    gen(a, note="AN-25-154 used the 2022 PTG-binned samples (4.216, 0.4114, 0.1284)")
for a in ("DYGto2LG_1J_MLL4to50", "DYGto2LG_1J_MLL50toInf", "DYGto2LG_1J_MLL50_PTG100toInf",
          "DYGto2LG_1J_MLL50_PTG200toInf", "DYGto2LG_1J_MLL50_PTG400toInf", "DYGto2LG_1J_MLL50_PTG600toInf"):
    gen(a, note="not used in AN-25-154")
gen("TTLL_CPV_madgraph", note="XSDB record from Run3Summer22EE; not used by B2G-25-013")
QCD_RE = re.compile(r"QCD_PT\d+to(\d+|Inf)_(EMEnriched|MuEnriched|bcToE)$")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--info", required=True)
    ap.add_argument("--xsdb", required=True)
    ap.add_argument("--pds", required=True, help="text file, one KNU MC dataset name per line")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    info = json.load(open(args.info))
    xsdb = json.load(open(args.xsdb))
    knu = {l.strip() for l in open(args.pds) if l.strip()}

    out, errors = [], []
    for alias, e in sorted(info.items()):
        if not e.get("isMC") or e.get("PD") not in knu or alias.startswith("TTToHcToWA"):
            continue
        recs = xsdb.get(e["PD"], [])
        r24 = [r for r in recs if "RunIII2024Summer24" in (r.get("DAS") or "")]
        rec = (r24 or recs or [None])[0]
        x_val = float(rec["cross_section"]) if rec else None
        x_camp = (rec.get("DAS") or "").split("/")[2] if rec and rec.get("DAS") else ""
        spec = ROWS.get(alias)
        if spec is None and QCD_RE.match(alias):
            spec = ("GEN", None, "generator", "XSDB",
                    "" if "RunIII2024Summer24" in x_camp else "XSDB record from another campaign", "", None)
        if spec is None:
            errors.append(f"no row definition for {alias} ({e['PD']})")
            continue
        cls, val, order, ref, note, flag, an = spec
        kfac, gen_val, formula = "", "", ""
        if cls == "HO":
            formula = val if isinstance(val, str) else ""
            xsec = eval(val, {"__builtins__": {}}) if isinstance(val, str) else float(val)
        elif cls == "HO*K":
            g, kfac = val
            gen_val = g if g is not None else x_val
            if gen_val is None:
                errors.append(f"{alias}: no generator value"); continue
            formula = f"{gen_val}*{kfac}"
            xsec = gen_val * kfac
        elif cls == "GEN":
            gen_val = val if val is not None else x_val
            if gen_val is None:
                errors.append(f"{alias}: no XSDB record"); continue
            xsec = gen_val
            if not order or order == "generator":
                order = (rec or {}).get("accuracy") or "generator"
        else:
            xsec = -1
        out.append({"alias": alias, "PD": e["PD"], "class": cls, "xsec_pb": f"{xsec:.6g}",
                    "formula": formula, "order": order, "ref": ref, "kfactor": kfac,
                    "generator_xsec": gen_val, "xsdb_xsec": x_val if x_val is not None else "",
                    "xsdb_campaign": x_camp[:60], "an25154_xsec": an if an is not None else "",
                    "current_json": e.get("xsec"), "flag": flag, "note": note})
    unused = sorted(set(ROWS) - {r["alias"] for r in out})
    if unused:
        print("rows not matched to a KNU sample (not on KNU):", ", ".join(unused))
    if errors:
        sys.exit("ERROR:\n  " + "\n  ".join(errors))
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    from collections import Counter
    print(f"{len(out)} rows -> {args.out}; classes {dict(Counter(r['class'] for r in out))}; "
          f"flags {dict(Counter(r['flag'] for r in out if r['flag']))}")


if __name__ == "__main__":
    main()
