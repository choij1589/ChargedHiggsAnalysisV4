"""|eff(accepted refit) - eff(original)| for every replaced bin (originals in fits_*.d.orig)."""
import sys, os, glob
sys.path.insert(0, "/d0/scratch/choij/tnp_tamsa/python")
import checkFitStatus as cfs
R = "/d0/scratch/choij/tnp_tamsa/results"
for orig in sorted(glob.glob(R + "/*/*/fits_*.d.orig")):
    cfg = orig.split("/")[-2]; kind = orig.split("/")[-1].split("_")[1].split(".")[0]
    rows = []
    for f in sorted(glob.glob(orig + "/*/bin*.root")):
        m = f.split("/")[-2]; b = os.path.basename(f)
        o = cfs.read_bin(f, m); n = cfs.read_bin(f.replace(".d.orig/", ".d/"), m)
        if not (o and n): continue
        if o["eff"] != o["eff"]: rows.append((float("inf"), "%s/%s orig NaN -> %.4f" % (b[:-5], m, n["eff"]))); continue
        d = abs(n["eff"] - o["eff"]); rows.append((d, "%s/%s %.4f -> %.4f (%.2f sigma)" % (b[:-5], m, o["eff"], n["eff"], d / max(o["eff_err"], 1e-9))))
    ds = sorted(r[0] for r in rows if r[0] != float("inf"))
    print("== %s %s: %d replaced | |shift| median %.1e, 90%% %.1e, max %.1e" % (cfg, kind, len(rows), ds[len(ds)//2] if ds else 0, ds[int(0.9*len(ds))] if ds else 0, ds[-1] if ds else 0))
    for d, t in sorted(rows, reverse=True)[:3]:
        if d > 0.005: print("     " + t)
