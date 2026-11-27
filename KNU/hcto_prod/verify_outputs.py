"""verify_outputs.py <runlog master dir> <output dir> <CHANNEL>: every sample of
the run has <output dir>/<sample>.root with ALL init > 0 and a non-empty
<CHANNEL>/Central/cutflow; prints per-sample final-bin yield and lane count."""
import os, sys
import ROOT
ROOT.gROOT.SetBatch(True)
master, outdir, ch = sys.argv[1:4]
samples = sorted(os.listdir(os.path.join(master, "2024")))
bad = 0
for s in samples:
    p = os.path.join(outdir, s + ".root")
    if not os.path.exists(p):
        print(f"MISSING {s}"); bad += 1; continue
    f = ROOT.TFile.Open(p)
    a = f.Get("ALL/Central/cutflow"); c = f.Get(f"{ch}/Central/cutflow")
    d = f.Get(ch)
    nl = d.GetListOfKeys().GetSize() if d else 0
    if not a or not c or a.GetBinContent(1) == 0 or c.GetEntries() == 0:
        print(f"EMPTY {s} init={a.GetBinContent(1) if a else None} chEntries={c.GetEntries() if c else None}"); bad += 1
    else:
        print(f"OK {s:28s} init={a.GetBinContent(1):.4g} final={c.GetBinContent(9):.5g} entries={int(c.GetBinContent(9)) if 'Muon' in s or 'EG' in s else '-'} lanes={nl}")
    f.Close()
print(f"{len(samples)} samples, {bad} problems")
