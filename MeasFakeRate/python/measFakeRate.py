"""Fake (tight-to-loose) rates from the MeasFakeRate production (PLAN_BkgEst steps 2-3).

  python MeasFakeRate/python/measFakeRate.py --flavour mu|el [--step gate|rates|all]

Input: SKNanoOutput/MeasFakeRate/<flags>/2024/ (synced from /pnfs), the MeasFakeRate analyzer of
HcToWA_Analyzers (2026-11-27 production, hcto_prod/submit_measfr.sh):
  data   <flags>=MeasMuFR (Skim_FakeRate_Muon{0,1}_<era>), MeasElFR (Skim_FakeRate_EGamma{0,1}_<era>)
  QCD    same directories, Skim_FakeRate_QCD_* (muons MuEnriched; electrons EMEnriched + bcToE, F8)
  prompt MeasMuFR_MeasElFR, the 22 samples of PROMPT (F6)
MC histograms are normalized to the full luminosity (MCweight x GetTriggerLumi("Full") x PU; no top pT weight, user 2026-11-27);
data are prescaled, hence the prompt scale s per (path, ID).

Histograms (MuFR|ElFR/<path>/...): <region>/<id>/<sel>/<class>/ptcorr_abseta (region QCD: MET < 25 and
MT < 25; W: MT > 60; Inc), Z/<id>/<sel>/<class>/mll_{os,ss} (two loose leptons of the flavour, away jet),
Control/..., Lanes/<lane>/<id>/{QCD_ptcorr_abseta,Z_mll_os} (prompt MC, Nom selection). "loose" includes
the tight leptons. Classes: data | prompt, conv, b, c, light, other.

Step "gate" (PLAN step 2; F5): per (path, ID)
  s = N_data / N_MC in the Z window (OS, |m_ll - 91.2| < 15 GeV, approximated by the 1 GeV bins 76-106),
      MC = all prompt-MC samples, all classes (PLAN table: data - s x (W, DY, tt, ST, VV));
  delta = (a) Z statistics (+) (b) W transfer |N_data / (s N_MC) - 1| in the W region (single lepton,
      MT > 60, Nom) (+) (c) object systematics: R = N_MC(QCD region) / N_MC(Z window), per source the
      larger |R_var / R - 1| of up/down (JES, JER, unclustered, lepton scale and resolution; pileup
      reported, not included: not in the F5 list);
  plus same-sign and sideband checks of the Z window, and the mean nPV of data and MC in the Z region.
Step "rates" (PLAN step 3; F7): rebinned to the F7 bins, one path per pT_corr bin (V4 mapping,
TRIG_RANGES); data rate f = (T_d - s_T T_MC) / (L_d - s_L L_MC) in the QCD region, error from the
statistics of data and MC (loose-not-tight and tight parts treated as independent); a bin with a
negative or undefined rate takes the rate of the previous pT bin of its |eta| row (user 2026-11-27).
Prompt scale (--scale): "fit" (default, user 2026-11-27): s = the MT template fit in the inclusive
single-lepton region with s bounded to s_Z (1 +- 0.3) (fitPromptScale.py --mode zbound), per (path, ID);
uncertainty delta = |s_fit / s_Z - 1| per (path, ID); selection variations use s_fit x s_Z(sel) / s_Z(Nom)
(the control histograms of the fit exist for Nom only). "zwindow": s = s_Z, delta per path from the gate.
Variations: Away20/30/60, BTag (selection; s recomputed with the same selection), PromptNorm up/down
(s -> s (1 +- delta)). MC rates (QCD, tt = TTLL + TTLJ) per class b/c/light and inclusive nonprompt,
weighted binomial errors.
Output: MeasFakeRate/results/2024/<flavour>/{gate.txt,gate.json,rates.txt,rates.json}.
"""
import argparse
import glob
import json
import math
from pathlib import Path

import ROOT

ROOT.gROOT.SetBatch(True)
REPO = Path(__file__).resolve().parents[2]
ERA = "2024"
OUT = REPO / "SKNanoOutput" / "MeasFakeRate"
RES = REPO / "MeasFakeRate" / "results" / ERA

PROMPT = ["DYto2E_2J_MLL10to50", "DYto2E_2J_MLL50toInf", "DYto2Mu_2J_MLL10to50", "DYto2Mu_2J_MLL50toInf",
          "DYto2Tau_2J_MLL10to50", "DYto2Tau_2J_MLL50toInf", "TTLL_powheg", "TTLJ_powheg",
          "ST_tch_top_lep", "ST_tch_antitop_lep", "ST_tW_top_Lep", "ST_tW_antitop_Lep", "ST_tW_top_Semilep",
          "ST_tW_antitop_Semilep", "ST_sch_top_Lep", "ST_sch_antitop_Lep", "WW_pythia", "WZ_pythia", "ZZ_pythia",
          "WtoENu_2J", "WtoMuNu_2J", "WtoTauNu_2J"]
TT = ["TTLL_powheg", "TTLJ_powheg"]
MC_CLASSES = ["prompt", "conv", "b", "c", "light", "other"]
NONPROMPT = ["b", "c", "light", "other"]
SELS = ["Nom", "Away20", "Away30", "Away60", "BTag"]
LANE_SOURCES = {"mu": ["JetEn", "JetRes", "UnclusteredEn", "MuonEn", "MuonRes"],
                "el": ["JetEn", "JetRes", "UnclusteredEn", "ElectronEn", "ElectronRes"]}

FLAV = {
    "mu": {"top": "MuFR", "flags": "MeasMuFR", "pds": ["Muon0", "Muon1"], "qcd": ["MuEnriched"],
           "paths": ["Mu8", "Mu17"],
           "eta": [0., 0.9, 1.6, 2.4], "pt": [10., 12., 14., 17., 20., 30., 50., 100., 200.]},
    "el": {"top": "ElFR", "flags": "MeasElFR", "pds": ["EGamma0", "EGamma1"], "qcd": ["EMEnriched", "bcToE"],
           "paths": ["Ele8", "Ele12", "Ele23"],
           "eta": [0., 0.8, 1.444, 2.5], "pt": [15., 17., 20., 25., 35., 50., 100., 200.]},
}
# one path per pT_corr bin (V4 measFakeRate.py get_trig_prefix; AN-25-154 tab:trigger_pt_cuts)
TRIG_RANGES = {"mu": [("Mu8", 10., 30.), ("Mu17", 30., 1e9)],
               "el": [("Ele8", 15., 20.), ("Ele12", 20., 35.), ("Ele23", 35., 1e9)]}
ZWIN = (76., 106.)


def path_of(fl, ptlow):
    for p, lo, hi in TRIG_RANGES[fl]:
        if lo <= ptlow < hi:
            return p
    raise ValueError(ptlow)


class Store:
    """Sums of histograms over sample groups, cached."""

    def __init__(self, fl):
        c = FLAV[fl]
        self.fl, self.top = fl, c["top"]
        d = OUT / c["flags"] / ERA
        self.files = {
            "data": sorted(f for pd in c["pds"] for f in glob.glob(str(d / f"Skim_FakeRate_{pd}_*.root"))),
            "qcd": sorted(f for q in c["qcd"] for f in glob.glob(str(d / f"Skim_FakeRate_QCD_*_{q}.root"))),
            "prompt": [str(OUT / "MeasMuFR_MeasElFR" / ERA / f"{s}.root") for s in PROMPT],
            "tt": [str(OUT / "MeasMuFR_MeasElFR" / ERA / f"{s}.root") for s in TT],
        }
        for g, fs in self.files.items():
            missing = [f for f in fs if not Path(f).exists()]
            if missing or not fs:
                raise SystemExit(f"{g}: missing inputs {missing[:3]} (n={len(fs)})")
        self.tf = {}
        self.cache = {}

    def _open(self, f):
        if f not in self.tf:
            self.tf[f] = ROOT.TFile.Open(f)
        return self.tf[f]

    def get(self, group, rel, classes=None):
        """Sum of <top>/<rel with {cls}> over the files of the group and the classes."""
        classes = ["data"] if group == "data" else (classes or MC_CLASSES)
        key = (group, rel, tuple(classes))
        if key in self.cache:
            return self.cache[key]
        tot = None
        for f in self.files[group]:
            tf = self._open(f)
            for c in classes:
                h = tf.Get(f"{self.top}/{rel.format(cls=c)}")
                if not h:
                    continue
                if tot is None:
                    tot = h.Clone(f"sum_{len(self.cache)}")
                    tot.SetDirectory(0)
                    tot.Reset()
                tot.Add(h)
        if tot is None:
            raise SystemExit(f"no histogram {group}:{self.top}/{rel} {classes}")
        self.cache[key] = tot
        return tot


def integral(h, lo=None, hi=None):
    """Integral and error, all bins with flow, or the bins between lo and hi (bin edges)."""
    import ctypes
    e = ctypes.c_double(0.)
    if lo is None:
        v = h.IntegralAndError(0, h.GetNbinsX() + 1, e) if h.GetDimension() == 1 else \
            h.IntegralAndError(0, h.GetNbinsX() + 1, 0, h.GetNbinsY() + 1, e)
    else:
        b1, b2 = h.FindBin(lo + 1e-6), h.FindBin(hi - 1e-6)
        v = h.IntegralAndError(b1, b2, e)
    return v, e.value


def zwin(store, group, path, idn, sel="Nom", sign="os", classes=None, lo=ZWIN[0], hi=ZWIN[1]):
    return integral(store.get(group, f"{path}/Z/{idn}/{sel}/{{cls}}/mll_{sign}", classes), lo, hi)


def prompt_scale(store, path, idn, sel="Nom"):
    d, de = zwin(store, "data", path, idn, sel)
    m, me = zwin(store, "prompt", path, idn, sel)
    s = d / m if m > 0 else float("nan")
    rel = math.hypot(de / d, me / m) if d > 0 and m > 0 else float("nan")
    return s, rel, d, m


def gate(fl):
    st = Store(fl)
    c = FLAV[fl]
    out, lines = {}, [f"# MeasFakeRate step-2 gate, {fl} ({c['top']}), production 2026-11-27 (measFakeRate.py --step gate)",
                      f"# Z window {ZWIN[0]:.0f}-{ZWIN[1]:.0f} GeV (OS, Nom selection); MC = {len(PROMPT)} prompt-MC samples, all classes"]
    for p in c["paths"]:
        out[p] = {}
        for idn in ("loose", "tight"):
            s, rel_a, nd, nm = prompt_scale(st, p, idn)
            # non-Z checks: same sign, sidebands
            ssd, _ = zwin(st, "data", p, idn, sign="ss")
            ssm, _ = zwin(st, "prompt", p, idn, sign="ss")
            sbd = zwin(st, "data", p, idn, lo=60., hi=76.)[0] + zwin(st, "data", p, idn, lo=106., hi=120.)[0]
            sbm = zwin(st, "prompt", p, idn, lo=60., hi=76.)[0] + zwin(st, "prompt", p, idn, lo=106., hi=120.)[0]
            npm = zwin(st, "prompt", p, idn, classes=["prompt"])[0]
            # (b) W-region transfer
            wd, wde = integral(st.get("data", f"{p}/W/{idn}/Nom/{{cls}}/ptcorr_abseta"))
            wm, wme = integral(st.get("prompt", f"{p}/W/{idn}/Nom/{{cls}}/ptcorr_abseta"))
            w_ratio = wd / (s * wm) if wm > 0 else float("nan")
            rel_b = abs(w_ratio - 1.)
            w_err = w_ratio * math.hypot(wde / wd, wme / wm) if wd > 0 and wm > 0 else float("nan")
            # (c) object systematics on R = QCD region / Z window (prompt MC)
            q0 = integral(st.get("prompt", f"{p}/QCD/{idn}/Nom/{{cls}}/ptcorr_abseta"))[0]
            R0 = q0 / nm if nm > 0 else float("nan")
            per = {}
            for src in LANE_SOURCES[fl] + ["Pileup"]:
                devs = []
                for ud in ("Up", "Down"):
                    lq = integral(_lane(st, p, src + ud, idn, "QCD_ptcorr_abseta"))[0]
                    lz = integral(_lane(st, p, src + ud, idn, "Z_mll_os"), *ZWIN)[0]
                    devs.append(abs((lq / lz) / R0 - 1.) if lz > 0 and R0 > 0 else float("nan"))
                per[src] = max(devs)
            rel_c = math.sqrt(sum(v * v for k, v in per.items() if k != "Pileup"))
            delta = math.sqrt(rel_a ** 2 + rel_b ** 2 + rel_c ** 2)  # per ID, for reference
            # nPV in the Z region
            nd_h = st.get("data", f"{p}/Control/Z/{idn}/{{cls}}/nPVsGood")
            nm_h = st.get("prompt", f"{p}/Control/Z/{idn}/{{cls}}/nPVsGood", ["prompt", "nonprompt"])
            out[p][idn] = {"s": s, "N_data_Z": nd, "N_MC_Z": nm, "prompt_frac_MC_Z": npm / nm if nm else None,
                           "delta_a_Zstat": rel_a, "W_data_over_sMC": w_ratio, "W_err": w_err, "delta_b_W": rel_b,
                           "R_QCD_over_Z": R0, "delta_c_sources": per, "delta_c": rel_c, "delta": delta,
                           "SS_data": ssd, "SS_sMC": s * ssm, "SB_data_over_sMC": sbd / (s * sbm) if sbm > 0 else None,
                           "nPV_mean_data": nd_h.GetMean(), "nPV_mean_MC": nm_h.GetMean()}
            o = out[p][idn]
            lines.append(f"## {p} {idn}")
            lines.append(f"  s = {s:.4g}  (N_data {nd:.0f}, N_MC {nm:.1f}; MC prompt class {o['prompt_frac_MC_Z']:.3f})")
            lines.append(f"  components: (a) Z stat {rel_a:.4f}, (b) W {rel_b:.4f}, (c) obj {rel_c:.4f}")
            lines.append(f"    W region: data / (s MC) = {w_ratio:.4f} +- {w_err:.4f}  (N_data {wd:.0f})")
            lines.append("    (c) per source: " + ", ".join(f"{k} {v:.4f}" for k, v in per.items()) + "  (Pileup not included)")
            lines.append(f"  checks: SS data {ssd:.0f} vs s x MC {s * ssm:.1f}; sidebands data / (s MC) {o['SB_data_over_sMC']:.3f}")
            lines.append(f"  nPV mean in Z region: data {o['nPV_mean_data']:.2f}, MC {o['nPV_mean_MC']:.2f}")
            # W region per pT_corr bin of the F7 grid served by this path
            hd = st.get("data", f"{p}/W/{idn}/Nom/{{cls}}/ptcorr_abseta")
            hm = st.get("prompt", f"{p}/W/{idn}/Nom/{{cls}}/ptcorr_abseta")
            per_pt = []
            ey = c["pt"] + [300.]
            for j in range(len(ey) - 1):
                if path_of(fl, ey[j]) != p:
                    continue
                y1, y2 = hd.GetYaxis().FindBin(ey[j] + 1e-5), hd.GetYaxis().FindBin(ey[j + 1] - 1e-5)
                a = hd.Integral(0, hd.GetNbinsX() + 1, y1, y2)
                b = hm.Integral(0, hm.GetNbinsX() + 1, y1, y2)
                per_pt.append((ey[j], ey[j + 1], a, a / (s * b) if b > 0 else float("nan")))
            o["W_per_pt"] = per_pt
            lines.append("    W region per pT_corr: " + ", ".join(f"{lo:.0f}-{hi:.0f}: {r:.3f} ({n:.0f})" for lo, hi, n, r in per_pt))
        # one delta per (path, flavour), from the single tight lepton (F5), applied to s_loose and s_tight
        t = out[p]["tight"]
        out[p]["delta"] = math.sqrt(t["delta_a_Zstat"] ** 2 + t["delta_b_W"] ** 2 + t["delta_c"] ** 2)
        lines.append(f"## {p}: delta = {out[p]['delta']:.4f} (tight: Z stat {t['delta_a_Zstat']:.4f}, W {t['delta_b_W']:.4f}, obj {t['delta_c']:.4f})")
    d = RES / fl
    d.mkdir(parents=True, exist_ok=True)
    (d / "gate.json").write_text(json.dumps(out, indent=1))
    (d / "gate.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return out


def _lane(st, p, lane, idn, name):
    """Lane histograms have no class level: Lanes/<lane>/<id>/<name>."""
    key = ("prompt-lane", p, lane, idn, name)
    if key in st.cache:
        return st.cache[key]
    tot = None
    for f in st.files["prompt"]:
        h = st._open(f).Get(f"{st.top}/{p}/Lanes/{lane}/{idn}/{name}")
        if not h:
            continue
        if tot is None:
            tot = h.Clone(f"lane_{len(st.cache)}")
            tot.SetDirectory(0)
            tot.Reset()
        tot.Add(h)
    if tot is None:
        raise SystemExit(f"no lane histogram {p}/Lanes/{lane}/{idn}/{name}")
    st.cache[key] = tot
    return tot


def rebin2d(h, ex, ey):
    """(value, sumw2) on the coarse (|eta| x pT_corr) grid from the fine 2D histogram (x = |eta|, y = pT_corr)."""
    res = {}
    for i in range(len(ex) - 1):
        for j in range(len(ey) - 1):
            x1, x2 = h.GetXaxis().FindBin(ex[i] + 1e-5), h.GetXaxis().FindBin(ex[i + 1] - 1e-5)
            y1, y2 = h.GetYaxis().FindBin(ey[j] + 1e-5), h.GetYaxis().FindBin(ey[j + 1] - 1e-5)
            for edge, ax, b in ((ex[i], h.GetXaxis(), x1), (ex[i + 1], h.GetXaxis(), x2 + 1),
                                (ey[j], h.GetYaxis(), y1), (ey[j + 1], h.GetYaxis(), y2 + 1)):
                if abs(ax.GetBinLowEdge(b) - edge) > 1e-3:
                    raise SystemExit(f"edge {edge} is not a bin edge of {h.GetName()}")
            import ctypes
            e = ctypes.c_double(0.)
            v = h.IntegralAndError(x1, x2, y1, y2, e)
            res[(i, j)] = (v, e.value ** 2)
    return res


def wbinom(T, L):
    """Weighted binomial: T, L = (sum w, sum w^2), tight subset of loose."""
    (t, t2), (l, l2) = T, L
    if l <= 0:
        return float("nan"), float("nan")
    f = t / l
    var = ((1 - 2 * f) * t2 + f * f * l2) / (l * l)
    return f, math.sqrt(max(var, 0.))


def rates(fl, gate_out=None, scale="fit"):
    st = Store(fl)
    c = FLAV[fl]
    ex, ey = c["eta"], c["pt"]
    if gate_out is None:
        gate_out = json.loads((RES / fl / "gate.json").read_text())
    variations = ["Central", "Away20", "Away30", "Away60", "BTag", "PromptNormUp", "PromptNormDown"]
    fit = json.loads((RES / fl / "promptfit_MT_zbound.json").read_text()) if scale == "fit" else None

    def data_rates(var):
        sel = var if var in SELS else "Nom"
        sc = {}
        for p in c["paths"]:
            for idn in ("loose", "tight"):
                s = prompt_scale(st, p, idn, sel)[0]
                if fit is not None:
                    s_nom_z = prompt_scale(st, p, idn, "Nom")[0]
                    s = fit[p][idn]["s_ratio"] * s / s_nom_z
                    delta = abs(fit[p][idn]["s_fit_over_s_Z"] - 1.)
                else:
                    delta = gate_out[p]["delta"]
                if var.startswith("PromptNorm"):
                    s *= 1 + (1 if var.endswith("Up") else -1) * delta
                sc[(p, idn)] = s
        grid = {}
        for p in c["paths"]:
            g = {idn: {grp: rebin2d(st.get(grp, f"{p}/QCD/{idn}/{sel}/{{cls}}/ptcorr_abseta"), ex, ey)
                       for grp in ("data", "prompt")} for idn in ("loose", "tight")}
            grid[p] = g
        out = {}
        for i in range(len(ex) - 1):
            row = []
            for j in range(len(ey) - 1):
                p = path_of(fl, ey[j])
                sT, sL = sc[(p, "tight")], sc[(p, "loose")]
                Td, _ = grid[p]["tight"]["data"][(i, j)]
                Ld, _ = grid[p]["loose"]["data"][(i, j)]
                Tm, Tm2 = grid[p]["tight"]["prompt"][(i, j)]
                Lm, Lm2 = grid[p]["loose"]["prompt"][(i, j)]
                T, L = Td - sT * Tm, Ld - sL * Lm
                A = L - T
                varT = Td + sT * sT * Tm2
                varA = (Ld - Td) + sL * sL * max(Lm2 - Tm2, 0.) + (sL - sT) ** 2 * Tm2
                f = T / L if L > 0 else float("nan")
                ef = math.sqrt(A * A * varT + T * T * varA) / (L * L) if L > 0 else float("nan")
                row.append({"path": p, "f": f, "err": ef, "T_data": Td, "L_data": Ld,
                            "prompt_frac_T": sT * Tm / Td if Td > 0 else None,
                            "prompt_frac_L": sL * Lm / Ld if Ld > 0 else None, "replaced": False})
            # negative / undefined rate -> previous pT bin of the row (user 2026-11-27)
            for j, b in enumerate(row):
                if not (b["f"] > 0) or math.isnan(b["f"]):
                    if j == 0:
                        b["replaced"] = "no previous bin"
                    else:
                        b["f_raw"], b["f"], b["err"] = b["f"], row[j - 1]["f"], row[j - 1]["err"]
                        b["replaced"] = True
            out[i] = row
        return out, sc

    def mc_rates(group, classes):
        T = {}
        for p in c["paths"]:
            T[p] = {idn: rebin2d(st.get(group, f"{p}/QCD/{idn}/Nom/{{cls}}/ptcorr_abseta", classes), ex, ey)
                    for idn in ("loose", "tight")}
        out = {}
        for i in range(len(ex) - 1):
            out[i] = []
            for j in range(len(ey) - 1):
                p = path_of(fl, ey[j])
                f, e = wbinom(T[p]["tight"][(i, j)], T[p]["loose"][(i, j)])
                out[i].append({"path": p, "f": f, "err": e, "L": T[p]["loose"][(i, j)][0]})
        return out

    res = {"eta": ex, "pt": ey, "paths": TRIG_RANGES[fl], "data": {}, "scales": {}, "mc": {}}
    for v in variations:
        r, sc = data_rates(v)
        res["data"][v] = r
        res["scales"][v] = {f"{p}/{idn}": s for (p, idn), s in sc.items()}
    for grp in ("qcd", "tt"):
        res["mc"][grp] = {"nonprompt": mc_rates(grp, NONPROMPT)}
        for cl in ("b", "c", "light"):
            res["mc"][grp][cl] = mc_rates(grp, [cl])

    lines = [f"# fake rates, {fl}, production 2026-11-27 (measFakeRate.py --step rates --scale {scale})",
             f"# rows |eta| {ex}, columns pT_corr {ey}; path per bin {TRIG_RANGES[fl]}",
             "# * = negative or undefined, replaced by the previous pT bin (user 2026-11-27)"]

    def table(title, r, extra=None):
        lines.append(f"## {title}")
        lines.append("  |eta| \\ pT  " + "  ".join(f"{ey[j]:>5.0f}-{ey[j + 1]:<5.0f}" for j in range(len(ey) - 1)))
        for i in range(len(ex) - 1):
            cells = []
            for b in r[i]:
                star = "*" if b.get("replaced") else " "
                cells.append(f"{b['f']:.3f}+-{b['err']:.3f}{star}" if not math.isnan(b["f"]) else "     nan     ")
            lines.append(f"  {ex[i]:.3g}-{ex[i + 1]:.3g}  " + " ".join(f"{x:>13s}" for x in cells))
        if extra:
            for i in range(len(ex) - 1):
                lines.append(f"    {extra} {ex[i]:.3g}-{ex[i + 1]:.3g}: " + " ".join(
                    f"{(b.get('prompt_frac_T') or float('nan')):.2f}/{(b.get('prompt_frac_L') or float('nan')):.2f}" for b in r[i]))

    table("data, Central", res["data"]["Central"], extra="prompt fraction T/L")
    for v in variations[1:]:
        table(f"data, {v}", res["data"][v])
    for grp in ("qcd", "tt"):
        for cl in ("nonprompt", "b", "c", "light"):
            table(f"MC {grp.upper()}, {cl}", res["mc"][grp][cl])
    lines.append("## prompt scales per variation")
    for v, sc in res["scales"].items():
        lines.append(f"  {v}: " + ", ".join(f"{k} {s:.4g}" for k, s in sc.items()))
    d = RES / fl
    tag = "" if scale == "fit" else f"_{scale}"
    res["scale"] = scale
    (d / f"rates{tag}.json").write_text(json.dumps(res, indent=1, default=str))
    (d / f"rates{tag}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--flavour", required=True, choices=list(FLAV))
    ap.add_argument("--step", default="all", choices=["gate", "rates", "all"])
    ap.add_argument("--scale", default="fit", choices=["fit", "zwindow"],
                    help="prompt scale: MT fit bounded to s_Z +- 30%% (default) or the Z window")
    a = ap.parse_args()
    g = gate(a.flavour) if a.step in ("gate", "all") else None
    if a.step in ("rates", "all"):
        rates(a.flavour, g, a.scale)


if __name__ == "__main__":
    main()
