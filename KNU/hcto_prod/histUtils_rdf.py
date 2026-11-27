
##################################################################
# RDataFrame hist step (KNU 2026-11-25, ChargedHiggsAnalysisV4)
##################################################################
# Same histograms as makePassFailHistogramsLoop, from one RDataFrame pass.
# Reads TTrees and RNTuples (ROOT >= 6.34), so the SKNano TnP RNTuples are
# used directly. Per (config, histogram type) one TH2D (bin index x mass) is
# filled; the per-bin TH1Ds are cut out of it, with the statistics recomputed
# from the bins (in-range sum of w and w^2, as Fill does) and the entry count
# taken from an unweighted twin (every Fill call, in or out of range).
# Semantics reproduced from the loop:
#   - preselection of configs[0], then per config: skip if expr == 0
#   - bin: bisect_right on each axis (abs() if 'abs' is in the axis var),
#     then config.find_bin (subclasses such as tnpConfigSkipGap included)
#   - weight per histogram type: skip if 0, > 1e10, NaN or inf; clamp to
#     +-maxweight; fill mass (or genmass) with expr*weight
# TNP_HIST_BACKEND=loop selects the old per-entry loop (TTree input only).
import re

_ABS_RE = re.compile(r'(?<![\w:.])abs\s*\(')
_CPP_DECLARED = False


def _cpp(expr):
    """TTreeFormula expression -> C++ for RDataFrame (abs -> std::abs, so that
    floats are not truncated by the integer abs)."""
    return _ABS_RE.sub('std::abs(', expr)


def _declare_cpp():
    global _CPP_DECLARED
    if _CPP_DECLARED:
        return
    ROOT.gInterpreter.Declare(r'''
#include <cmath>
#include <vector>
#include <algorithm>
namespace tnprdf {
struct Binner {
    std::vector<std::vector<double>> edges;
    std::vector<int> map;          // full product index -> config bin index or -1
    int find(double v0, double v1, double v2) const {
        const double v[3] = {v0, v1, v2};
        int index = 0, stride = 1;
        for (std::size_t a = 0; a < edges.size(); ++a) {
            const auto &e = edges[a];
            // python bisect.bisect_right(e, v) - 1
            const int ib = int(std::upper_bound(e.begin(), e.end(), v[a]) - e.begin()) - 1;
            if (ib < 0 || ib >= int(e.size()) - 1) return -1;
            index += ib * stride;
            stride *= int(e.size()) - 1;
        }
        return map[index];
    }
};
std::vector<Binner> binners;
inline int find(int id, double v0, double v1, double v2) { return binners[id].find(v0, v1, v2); }
// fill weight as in the loop: 0 means "not filled"
inline double weight(double expr, double w, double maxweight) {
    if (expr == 0.) return 0.;
    if (w == 0.) return 0.;
    if (w > 1e10 || std::isnan(w) || std::isinf(w)) return 0.;
    if (maxweight > 0. && std::fabs(w) > maxweight) w = std::copysign(maxweight, w);
    return expr * w;
}
}
''')
    _CPP_DECLARED = True


def _register_binner(config):
    """Register a C++ binner reproducing config.find_bin; returns its id."""
    axes = config.axes
    if len(axes) > 3:
        print("Error: RDF hist step supports up to 3 axes")
        exit(1)
    edges = [list(map(float, a['bins'])) for a in axes]
    sizes = [len(e) - 1 for e in edges]
    nfull = 1
    for s in sizes:
        nfull *= s
    mapping = []
    for k in range(nfull):
        rest, centers = k, []
        for a, s in enumerate(sizes):
            i = rest % s
            rest //= s
            centers.append(0.5 * (edges[a][i] + edges[a][i + 1]))
        ib = config.find_bin(centers)
        mapping.append(-1 if ib is None else int(ib))
    b = ROOT.tnprdf.Binner()
    for e in edges:
        v = ROOT.std.vector['double']()
        for x in e:
            v.push_back(x)
        b.edges.push_back(v)
    for m in mapping:
        b.map.push_back(m)
    ROOT.tnprdf.binners.push_back(b)
    return ROOT.tnprdf.binners.size() - 1


def _axis_value(var):
    """Column expression for an axis, as the loop: strip operators, abs() if
    'abs' appears in the axis definition."""
    name = var
    for p in ['&', '|', '+', '-', 'max(', 'cos(', 'sqrt(', 'fabs(', 'abs(', '(', ')', '>', '<', '=', '!', '*', '/', '?', ':', ',']:
        name = name.replace(p, "")
    if "abs" in var:
        return "std::abs((double)({}))".format(name)
    return "(double)({})".format(name)


def _dataset_name(path, name):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        print("Error: cannot open " + path)
        exit(1)
    for cand in [name, name.replace("/", "_")]:
        if f.Get(cand):
            f.Close()
            return cand
    print("Error: neither {} nor {} in {}".format(name, name.replace("/", "_"), path))
    exit(1)


def makePassFailHistogramsRDF(configs, njob, ijob, reduction=1):
    ROOT.TH1.SetDefaultSumw2()
    if not type(configs) is list:
        configs = [configs]
    _declare_cpp()

    sample = configs[0].sample
    if os.path.isdir(sample):
        rootfiles = os.popen('find -L ' + sample + ' -type f -name \'*.root\' | sort -V').read().split()
    elif os.path.isfile(sample):
        rootfiles = [sample]
    else:
        print("Error: {} doesn't exists".format(sample))
        exit(1)
    if len(rootfiles) < njob:
        split_events = True
    else:
        split_events = False
        rootfiles = [rootfiles[i] for i in range(len(rootfiles)) if i % njob == ijob]
    hist_file = configs[0].path + "/" + configs[0].hist_file.replace(".root", ".d/job{}.root".format(ijob))
    for p in rootfiles:
        print(' adding rootfile: ', p)

    name = _dataset_name(rootfiles[0], configs[0].tree)
    files = ROOT.std.vector['std::string']()
    for p in rootfiles:
        files.push_back(p)
    df = ROOT.RDataFrame(name, files)

    nevents = int(df.Count().GetValue()) if (split_events or reduction != 1) else None
    if reduction != 1:
        print("reduction: {} -> {}".format(nevents, int(nevents / reduction)))
        nevents = int(nevents / reduction)
    if split_events:
        start = ijob * (nevents // njob)
        end = (ijob + 1) * (nevents // njob)
        if ijob == njob - 1:
            end = nevents
        df = df.Range(start, end)
    elif reduction != 1:
        df = df.Range(0, nevents)

    if hasattr(configs[0], "preselection") and configs[0].preselection not in [None, ""]:
        df = df.Filter("(bool)({})".format(_cpp(configs[0].preselection)), "preselection")

    bins = configs[0].bins
    plan = []   # (ic, ih, isPass, genmatching, genmass, h2 weighted, h2 count)
    for ic, config in enumerate(configs):
        bid = _register_binner(config)
        vals = [_axis_value(a['var']) for a in config.axes] + ["0."] * (3 - len(config.axes))
        df = df.Define("__expr{}".format(ic), "(double)({})".format(_cpp(config.expr)))
        df = df.Define("__bin{}".format(ic), "tnprdf::find({}, {}, {}, {})".format(bid, *vals))
        maxweight = float(config.maxweight) if hasattr(config, "maxweight") and config.maxweight is not None else -1.
        hist_types = [[isPass, genmatching, genmass] for isPass in [False, True] for genmatching in [None, False, True] for genmass in [False, True]]
        ih = 0
        for isPass, genmatching, genmass in hist_types:
            if not config.genmatching and genmatching is not None: continue
            if not config.genmass and genmass: continue
            if genmatching != True and genmass: continue
            weight = "({})".format(config.test) if isPass else "!({})".format(config.test)
            if genmatching == True:
                weight += "*({})".format(config.genmatching)
            elif genmatching == False:
                if hasattr(config, "notgenmatching") and config.notgenmatching not in [None, ""]:
                    weight += "*({})".format(config.notgenmatching)
                else:
                    weight += "*!({})".format(config.genmatching)
            if config.weight:
                weight += "*({})".format(config.weight)
            wcol, icol, xcol = "__w{}_{}".format(ic, ih), "__i{}_{}".format(ic, ih), "__x{}_{}".format(ic, ih)
            df = df.Define(wcol, "tnprdf::weight(__expr{}, (double)({}), {})".format(ic, _cpp(weight), repr(maxweight)))
            df = df.Define(icol, "({} != 0. && __bin{} >= 0) ? __bin{} : -1".format(wcol, ic, ic))
            df = df.Define(xcol, "(double)({})".format(config.genmass if genmass else config.mass))
            nb = len(bins)
            m = ROOT.RDF.TH2DModel("h2_{}_{}".format(ic, ih), "", nb, 0., float(nb), config.hist_nbins, float(config.hist_range[0]), float(config.hist_range[1]))
            mc = ROOT.RDF.TH2DModel("c2_{}_{}".format(ic, ih), "", nb, 0., float(nb), config.hist_nbins, float(config.hist_range[0]), float(config.hist_range[1]))
            plan.append((ic, isPass, genmatching, genmass, df.Histo2D(m, icol, xcol, wcol), df.Histo2D(mc, icol, xcol)))
            ih += 1
    print("Total {} hists = {} configs * {} bins * types".format(len(plan) * len(bins), len(configs), len(bins)))

    print("Starting RDataFrame event loop to fill histograms..")
    sys.stdout.flush()
    ts = time.time()
    ROOT.RDF.RunGraphs([p[4] for p in plan] + [p[5] for p in plan])
    print("Event loop time", time.time() - ts, "seconds")

    mkdirp(os.path.dirname(hist_file))
    outfile = ROOT.TFile(hist_file, 'recreate')
    nwritten = 0
    for ic, isPass, genmatching, genmass, h2r, c2r in plan:
        config = configs[ic]
        h2, c2 = h2r.GetValue(), c2r.GetValue()
        ny = config.hist_nbins
        for ib in range(len(bins)):
            histname = config.get_histname(ib, isPass=isPass, genmatching=genmatching, genmass=genmass)
            h = ROOT.TH1D(histname, bins[ib]['title'], config.hist_nbins, config.hist_range[0], config.hist_range[1])
            h.SetDirectory(0)
            nfill = 0.
            for iy in range(ny + 2):
                g = h2.GetBin(ib + 1, iy)
                h.SetBinContent(iy, h2.GetBinContent(g))
                h.SetBinError(iy, h2.GetBinError(g))
                nfill += c2.GetBinContent(g)
            h.ResetStats()
            h.SetEntries(nfill)
            dirname = os.path.dirname(histname)
            basename = os.path.basename(histname)
            if not outfile.GetDirectory(dirname):
                outfile.mkdir(dirname)
            outfile.cd(dirname)
            h.Write(basename)
            nwritten += 1
    print("Wrote", nwritten, "hists")
    sys.stdout.flush()
    ROOT.gROOT.GetListOfFiles().Remove(outfile)
    outfile.Close()


def makePassFailHistograms(configs, njob, ijob, reduction=1):
    """Dispatch: RDataFrame (default) or the per-entry loop (TNP_HIST_BACKEND=loop)."""
    if os.getenv("TNP_HIST_BACKEND", "rdf") == "loop":
        return makePassFailHistogramsLoop(configs, njob, ijob, reduction)
    return makePassFailHistogramsRDF(configs, njob, ijob, reduction)
