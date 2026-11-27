"""Entries of the skim RNTuple in each listed file vs the expected count (metadata only)."""
import sys, os, ROOT
for line in open(sys.argv[1]):
    f, exp = line.split()
    try:
        tf = ROOT.TFile.Open(f); names = [k.GetName() for k in tf.GetListOfKeys()]; tf.Close()
        nt = [n for n in names if n not in ("skim",)][0]
        n = ROOT.RNTupleReader.Open(nt, f).GetNEntries()
        print(f"{'OK ' if n == int(exp) else 'BAD'} {os.path.basename(os.path.dirname(f))}/{os.path.basename(f)} {nt} entries {n} expected {exp} size {os.path.getsize(f)}")
    except Exception as e:
        print(f"ERR {f}: {str(e)[:150]}")
