"""For each job file list: fields not common to all files of the job (metadata only), and whether given fields are common."""
import sys, ROOT
check = sys.argv[2].split(",")
files = [l.strip() for l in open(sys.argv[1]) if l.startswith("root://")]
sets = []
for f in files:
    d = ROOT.RNTupleReader.Open("Events", f).GetDescriptor()
    sets.append({fd.GetFieldName() for fd in d.GetTopLevelFields()})
allf, common = set.union(*sets), set.intersection(*sets)
diff = sorted(allf - common)
pref = sorted({x.split("_")[0] for x in diff})
print(f"{sys.argv[1].split('/')[-3]}/{sys.argv[1].split('/')[-1]}: {len(files)} files, {len(diff)} non-common fields, prefixes {pref}, "
      f"non-L1: {[x for x in diff if not x.startswith('L1_')][:8]}; checked fields missing somewhere: {[c for c in check if c not in common]}")
