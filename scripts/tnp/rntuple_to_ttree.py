#!/usr/bin/env python3
"""Convert SKNano 2.0 tag-and-probe RNTuples to the TTrees tnp_tamsa reads.

MuonTnPProducer / ElectronTnPProducer (HcToWA_Analyzers) write one RNTuple per
job, at the top level of the output file under the flattened key
'muon_Events' / 'electron_Events', plus histograms TnP/{cutflow,nTags,...}.
tnp_tamsa (python/histUtils.py) reads TTrees through TChain + TTreeFormula, with
the tree names of the configs, 'muon/Events' and 'electron/Events'.

For each output file this script
  1. chains the given inputs' RNTuple with RDataFrame and Snapshots every field
     to a TTree <dir>/<tree> (default: muon/Events or electron/Events),
  2. sums the TnP/* histograms of the inputs and writes them under TnP/,
  3. checks: the number of output TTree entries equals the sum of the input
     RNTuple entries (inputs without the RNTuple key, i.e. jobs that found no
     pair, count as 0 and are listed); the output is written to <out>.partial
     and renamed only after the check passes.

Modes:
  one output from many inputs (merge per sample / PD):
    rntuple_to_ttree.py --lepton muon --out OUT.root IN1.root [IN2.root ...]
  one output per input, into a directory (e.g. one file per data period):
    rntuple_to_ttree.py --lepton muon --outdir DIR IN1.root [IN2.root ...]
  groups of N inputs per output, into a directory (per-job outputs of a sample,
  SKNano.py --no-hadd), named <prefix>_partNNN.root:
    rntuple_to_ttree.py --lepton muon --outdir DIR --group N --prefix NAME IN*.root
A directory of outputs is a valid tnp_tamsa sample (histUtils chains every
*.root in it and splits the hist jobs by file).
Inputs may be glob patterns (quoted). Runs in the NanoV15 environment
(ROOT 6.40 with RNTuple); Python 3.9 compatible. Exit code 1 if a check fails.
"""
import argparse
import glob
import os
import sys


def parse_args():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("inputs", nargs="+", help="SKNano output files (globs allowed)")
    p.add_argument("--lepton", choices=["muon", "electron"], required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--out", help="single merged output file")
    g.add_argument("--outdir", help="directory, one output per input (same basename)")
    p.add_argument("--group", type=int, default=0, help="with --outdir: inputs per output (0: one each)")
    p.add_argument("--prefix", default="part", help="with --group: output name prefix")
    p.add_argument("--tree", default=None, help="output TTree path (default <lepton>/Events)")
    p.add_argument("--threads", type=int, default=0, help="ROOT implicit MT threads (0: off)")
    p.add_argument("--force", action="store_true", help="overwrite existing outputs")
    return p.parse_args()


def expand(patterns):
    files = []
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if not hits:
            if os.path.exists(pat):
                hits = [pat]
            else:
                sys.exit("[rntuple_to_ttree] no file matches %s" % pat)
        files.extend(hits)
    return files


def count_entries(ROOT, path, key):
    """Entries of RNTuple 'key' in 'path'; None if the key is absent."""
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        sys.exit("[rntuple_to_ttree] cannot open %s" % path)
    has = bool(f.GetListOfKeys().FindObject(key))
    f.Close()
    if not has:
        return None
    reader = ROOT.RNTupleReader.Open(key, path)
    return int(reader.GetNEntries())


def sum_hists(ROOT, paths):
    out = {}
    for path in paths:
        f = ROOT.TFile.Open(path)
        d = f.Get("TnP")
        if d:
            for k in d.GetListOfKeys():
                h = k.ReadObj()
                if not h.InheritsFrom("TH1"):
                    continue
                if k.GetName() in out:
                    out[k.GetName()].Add(h)
                else:
                    c = h.Clone(k.GetName())
                    c.SetDirectory(0)
                    out[k.GetName()] = c
        f.Close()
    return out


def convert(ROOT, inputs, output, key, tree, force):
    if os.path.exists(output) and not force:
        print("[rntuple_to_ttree] exists, skipped: %s" % output)
        return True
    counts = [(p, count_entries(ROOT, p, key)) for p in inputs]
    present = [p for p, n in counts if n is not None]
    missing = [p for p, n in counts if n is None]
    n_in = sum(n for _, n in counts if n is not None)
    for p in missing:
        print("[rntuple_to_ttree] no %s in %s (counted as 0)" % (key, p))
    partial = output + ".partial"
    if present:
        df = ROOT.RDataFrame(key, present)
        opts = ROOT.RDF.RSnapshotOptions()
        opts.fMode = "RECREATE"
        opts.fOutputFormat = ROOT.RDF.ESnapshotOutputFormat.kTTree
        df.Snapshot(tree, partial, df.GetColumnNames(), opts)
    else:
        # Keep an empty, well-formed file so that a sample with no pair is visible.
        f = ROOT.TFile(partial, "RECREATE")
        f.Close()
    hists = sum_hists(ROOT, inputs)
    f = ROOT.TFile(partial, "UPDATE")
    if hists:
        f.mkdir("TnP").cd()
        for name in sorted(hists):
            hists[name].Write(name)
    f.Close()

    f = ROOT.TFile.Open(partial)
    t = f.Get(tree)
    n_out = int(t.GetEntries()) if t else 0
    f.Close()
    ok = n_out == n_in
    print("[rntuple_to_ttree] %s: inputs %d (%d without pairs), entries in %d, out %d -> %s"
          % (output, len(inputs), len(missing), n_in, n_out, "OK" if ok else "MISMATCH"))
    if ok:
        os.replace(partial, output)
    return ok


def main():
    args = parse_args()
    import ROOT  # noqa: E402  (after argparse so --help works without ROOT)
    ROOT.gROOT.SetBatch(True)
    if args.threads > 0:
        ROOT.EnableImplicitMT(args.threads)
    key = "%s_Events" % args.lepton
    tree = args.tree or "%s/Events" % args.lepton
    inputs = expand(args.inputs)
    ok = True
    if args.out:
        d = os.path.dirname(os.path.abspath(args.out))
        if not os.path.isdir(d):
            os.makedirs(d)
        ok = convert(ROOT, inputs, args.out, key, tree, args.force)
    else:
        if not os.path.isdir(args.outdir):
            os.makedirs(args.outdir)
        if args.group > 0:
            for k in range(0, len(inputs), args.group):
                out = os.path.join(args.outdir, "%s_part%03d.root" % (args.prefix, k // args.group))
                ok = convert(ROOT, inputs[k:k + args.group], out, key, tree, args.force) and ok
        else:
            for p in inputs:
                ok = convert(ROOT, [p], os.path.join(args.outdir, os.path.basename(p)),
                             key, tree, args.force) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
