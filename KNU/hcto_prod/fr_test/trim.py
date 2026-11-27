import sys, re, os
d, k, skim = sys.argv[1], int(sys.argv[2]), sys.argv[3] == "1"
p = os.path.join(d, "job_1.cc"); s = open(p).read().split("\n")
out, n = [], 0
for l in s:
    if "module.AddFile(" in l:
        n += 1
        if n > k: continue
    if skim and "SetOutfilePath(" in l:
        l = re.sub(r'SetOutfilePath\("[^"]*"\)', 'SetOutfilePath("%s/output/tree_0.root")' % d, l)
    out.append(l)
assert n >= k, (d, n)
open(p, "w").write("\n".join(out)); print(d, "files kept", min(n, k), "of", n)
