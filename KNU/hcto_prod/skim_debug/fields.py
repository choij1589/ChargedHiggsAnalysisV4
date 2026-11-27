"""Top-level field names of each RNTuple 'Events' in a list of files (metadata only); prints the fields not present in all files."""
import sys, ROOT
files = [l.strip() for l in open(sys.argv[1]) if l.strip()]
sets = {}
for f in files:
    r = ROOT.RNTupleReader.Open("Events", f)
    d = r.GetDescriptor()
    sets[f] = {d.GetFieldDescriptor(i).GetFieldName() for i in d.GetTopLevelFields() if True} if False else {fd.GetFieldName() for fd in d.GetTopLevelFields()}
allf = set.union(*sets.values()); common = set.intersection(*sets.values())
print(len(files), "files; fields: union", len(allf), "common", len(common))
for f, s in sets.items():
    miss = sorted(allf - s)
    print(f.split("/")[-1], len(s), "missing:", miss[:12], "..." if len(miss) > 12 else "")
