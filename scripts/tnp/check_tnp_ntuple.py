#!/usr/bin/env python3
"""Validation summary of a tag-and-probe ntuple (MuonTnPProducer / ElectronTnPProducer).

Reads either the SKNano RNTuple ('muon_Events' / 'electron_Events') or the
converted TTree ('muon/Events' / 'electron/Events') with RDataFrame, and prints
the phase 2.3 gate quantities (docs/PLAN_LeptonID.md, step 2):
  - cutflow and tag / probe-candidate / pair counts (TnP/* histograms);
  - pair-mass peak: mode (0.5 GeV bins), median and mean in 70-110 GeV, the
    fraction of pairs in 81-101 GeV;
  - every numeric column: minimum, maximum and the number of entries equal to
    -999 or NaN (gen columns are checked only where *_gen_matched is true);
  - with the nominal tag selection of the tnp_tamsa configs: passing-probe
    fractions of our tight ID (probe_isHcToWATight) and of the POG working
    points (muons Medium, Tight; electrons MVA noIso WP90, cut-based tight);
  - electrons: probe_isHcToWATight against the tight ID re-derived from the
    stored inputs (same cuts as HcToWABase::EvaluateElectronIDs), counts must
    agree; muons: the same for the muon tight ID;
  - MC: gen-matching fractions and weight summary.
Runs in the NanoV15 environment; Python 3.9 compatible.

  check_tnp_ntuple.py --lepton muon FILE [FILE ...]
"""
import argparse
import math
import sys

MU_TAG = ("tag_isTight && tag_pt > 26 && abs(tag_eta) < 2.4 && tag_IsoMu24"
          " && abs(tag_dxy) < 0.2 && abs(tag_dz) < 0.5 && tag_pfRelIso04 < 0.2"
          " && probe_isTracker && abs(probe_dxy) < 0.2 && abs(probe_dz) < 0.5"
          " && pair_probeMultiplicity == 1 && !probe_isDuplicated")
EL_TAG = ("tag_cutBased >= 4 && tag_pt > 35 && abs(tag_sc_eta) < 2.5 && tag_trig && tag_q*probe_q < 0"
          " && !(abs(tag_sc_eta) > 1.4442 && abs(tag_sc_eta) < 1.566)")

MU_TIGHT_REDERIVED = ("probe_isMedium && abs(probe_dz) < 0.1 && probe_sip3d < 3"
                      " && probe_tkRelIso < 0.4 && probe_miniPFRelIso < 0.1")
EL_TRIGEMU = ("((probe_sc_abseta < 1.444 && probe_sieie < 0.013 && abs(probe_dEtaInSC) < 0.01"
              " && abs(probe_dPhiInSeed) < 0.07 && probe_hoe < 0.13"
              " && std::max(0.f, probe_ecalPFClusIso - rho*0.16544f) < 0.5f*probe_pt"
              " && std::max(0.f, probe_hcalPFClusIso - rho*0.05956f) < 0.3f*probe_pt)"
              " || (probe_sc_abseta >= 1.566 && probe_sieie < 0.035 && abs(probe_dEtaInSC) < 0.015"
              " && abs(probe_dPhiInSeed) < 0.1 && probe_hoe < 0.13"
              " && std::max(0.f, probe_ecalPFClusIso - rho*0.13212f) < 0.5f*probe_pt"
              " && std::max(0.f, probe_hcalPFClusIso - rho*0.13052f) < 0.3f*probe_pt))"
              " && probe_dr03TkSumPt < 0.2f*probe_pt")
EL_TIGHT_REDERIVED = ("(" + EL_TRIGEMU + ") && probe_convVeto && probe_lostHits < 2"
                      " && abs(probe_dz) < 0.1 && probe_isMVANoIsoWP90 && probe_sip3d < 4"
                      " && probe_miniPFRelIso < 0.1")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("files", nargs="+")
    p.add_argument("--lepton", choices=["muon", "electron"], required=True)
    args = p.parse_args()
    import ROOT
    ROOT.gROOT.SetBatch(True)
    lep = args.lepton

    f0 = ROOT.TFile.Open(args.files[0])
    if f0.Get("%s/Events" % lep):
        name = "%s/Events" % lep
    else:
        name = "%s_Events" % lep
    hists = {}
    for fn in args.files:
        f = ROOT.TFile.Open(fn)
        for h in ("cutflow", "nTags", "nProbeCandidates", "nPairs"):
            o = f.Get("TnP/" + h)
            if not o:
                continue
            if h in hists:
                hists[h].Add(o)
            else:
                hists[h] = o.Clone(h)
                hists[h].SetDirectory(0)
        f.Close()
    f0.Close()

    df = ROOT.RDataFrame(name, args.files)
    cols = [str(c) for c in df.GetColumnNames()]
    isMC = "genWeight" in cols
    n = df.Count().GetValue()
    print("== %s: %d files, %d pairs, %s" % (lep, len(args.files), n, "MC" if isMC else "data"))
    if "cutflow" in hists:
        c = hists["cutflow"]
        labels = ["all", "event filters", "HLT", ">=1 tag", ">=1 pair"]
        print("cutflow: " + ", ".join("%s %d" % (labels[i], c.GetBinContent(i + 1)) for i in range(5)))
    for h in ("nTags", "nProbeCandidates", "nPairs"):
        if h in hists:
            o = hists[h]
            tot = sum(o.GetBinCenter(i) * o.GetBinContent(i) for i in range(1, o.GetNbinsX() + 2))
            print("%s: total %d (mean per counted event %.3f)" % (h, tot, o.GetMean()))

    # Mass peak
    hm = df.Histo1D(("m", "m", 160, 50., 130.), "pair_mass").GetValue()
    mode = hm.GetBinCenter(hm.GetMaximumBin())
    win = df.Filter("pair_mass > 70 && pair_mass < 110")
    mean = win.Mean("pair_mass").GetValue()
    frac = df.Filter("pair_mass > 81 && pair_mass < 101").Count().GetValue() / max(n, 1)
    q = ROOT.std.vector("double")([0.5])
    vals = ROOT.std.vector("double")([0.])
    hw = win.Histo1D(("mw", "mw", 800, 70., 110.), "pair_mass").GetValue()
    hw.GetQuantiles(1, vals.data(), q.data())
    print("pair_mass: mode %.2f GeV, median(70-110) %.2f, mean(70-110) %.2f, frac(81-101) %.3f"
          % (mode, vals[0], mean, frac))
    if "pair_mass_cor" in cols:
        hc = df.Histo1D(("mc", "mc", 160, 50., 130.), "pair_mass_cor").GetValue()
        print("pair_mass_cor: mode %.2f GeV" % hc.GetBinCenter(hc.GetMaximumBin()))

    # Column ranges and sentinel values
    print("columns (min, max, n(-999), n(NaN)):")
    bad = []
    for cname in cols:
        t = df.GetColumnType(cname)
        if t not in ("float", "Float_t", "double", "int", "Int_t", "unsigned int", "UInt_t",
                     "ULong64_t", "unsigned long", "unsigned long long", "bool", "Bool_t",
                     "std::int32_t", "std::uint32_t", "std::uint64_t", "Long64_t"):
            continue
        d = df
        if "_gen_" in cname and cname.startswith(("tag_", "probe_")) and not cname.endswith("matched"):
            d = df.Filter(cname.split("_gen_")[0] + "_gen_matched")
        if cname == "pair_gen_mass":
            d = df.Filter("pair_gen_matched")
        mn = d.Min(cname)
        mx = d.Max(cname)
        n999 = d.Filter("%s == -999" % cname).Count() if t not in ("bool", "Bool_t") else d.Filter("false").Count()
        nnan = d.Filter("!(%s == %s)" % (cname, cname)).Count() if t in ("float", "Float_t", "double") else None
        a, b, c = mn.GetValue(), mx.GetValue(), n999.GetValue()
        e = nnan.GetValue() if nnan is not None else 0
        if c or e:
            bad.append(cname)
        print("  %-24s %-8s %12.4g %12.4g %8d %6d" % (cname, t, a, b, c, e))
    print("columns with -999 / NaN: %s" % (", ".join(bad) if bad else "none"))

    # Passing fractions with the nominal tag selection, in the fit window
    if lep == "muon":
        sel, window = MU_TAG, "pair_mass > 70 && pair_mass < 110"
        tests = [("HcToWA tight", "probe_isHcToWATight"), ("POG Medium", "probe_isMedium"),
                 ("POG Tight", "probe_isTight"), ("HcToWA loose", "probe_isHcToWALoose")]
        rederived = MU_TIGHT_REDERIVED
    else:
        sel, window = EL_TAG + " && !(probe_sc_abseta > 1.4442 && probe_sc_abseta < 1.566)", "pair_mass > 60 && pair_mass < 120"
        tests = [("HcToWA tight", "probe_isHcToWATight"), ("MVA noIso WP90", "probe_isMVANoIsoWP90"),
                 ("cut-based tight", "probe_cutBased >= 4"), ("trigger emulation", "probe_passTrigEmu"),
                 ("HcToWA loose", "probe_isHcToWALoose")]
        rederived = EL_TIGHT_REDERIVED
    base = df.Filter(sel).Filter(window)
    if lep == "muon":
        base = base.Filter("probe_pt > 10")
    nb = base.Count().GetValue()
    print("nominal tag selection, %s: %d probes" % (window, nb))
    wcol = "weight" if isMC else None
    for label, expr in tests:
        k = base.Filter(expr).Count().GetValue()
        line = "  pass %-18s %8d  %.4f" % (label, k, k / max(nb, 1))
        if wcol:
            sw = base.Sum(wcol).GetValue()
            sp = base.Filter(expr).Sum(wcol).GetValue()
            line += "  (weighted %.4f)" % (sp / sw if sw else float("nan"))
        print(line)

    # Stored tight-ID boolean vs the ID re-derived from the stored inputs
    a = df.Filter("probe_isHcToWATight").Count()
    b = df.Filter(rederived).Count()
    both = df.Filter("probe_isHcToWATight && (%s)" % rederived).Count()
    print("tight ID: stored %d, re-derived %d, both %d -> %s"
          % (a.GetValue(), b.GetValue(), both.GetValue(),
             "AGREE" if a.GetValue() == b.GetValue() == both.GetValue() else "DIFFER"))

    if isMC:
        g = df.Filter("pair_gen_matched").Count().GetValue()
        gw = df.Filter(sel).Filter(window)
        print("gen matched pairs: %.4f (all), %.4f (nominal selection, window)"
              % (g / max(n, 1), gw.Filter("pair_gen_matched").Count().GetValue() / max(gw.Count().GetValue(), 1)))
        for w in ("genWeight", "PUweight", "weight"):
            print("  %-10s mean %.4g min %.4g max %.4g" % (w, df.Mean(w).GetValue(), df.Min(w).GetValue(),
                                                          df.Max(w).GetValue()))
        print("  negative-weight fraction %.4f" % (df.Filter("genWeight < 0").Count().GetValue() / max(n, 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
