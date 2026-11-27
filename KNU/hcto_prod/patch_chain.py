import sys
B='/d0/scratch/choij/SKNanoAnalyzer/HcToWA_Analyzers/'
def rep(path,a,b):
    s=open(B+path).read()
    if s.count(a)!=1: sys.exit(f"{path}: {s.count(a)}x {a[:60]!r}")
    open(B+path,'w').write(s.replace(a,b))
rep('include/HcToWA/DiLepton.h','''        bool notImplemented = false;''','''        bool notImplemented = false;
        // _NotImplemented lanes: bit mask of the factors divided out = the factor and every
        // SF measured on top of it (user 2026-11-26): electron reco -> electron ID -> trigger,
        // muon ID -> trigger (the trigger legs are measured on tight-ID leptons).
        unsigned removed = 0;''')
rep('src/DiLepton.cc','''                wl.notImplemented = true;''','''                wl.notImplemented = true;
                wl.removed = 1u << f;
                if (f == kFEleReco) wl.removed |= (1u << kFEleID) | (1u << kFEMuTrig) | (1u << kFEleTrigProxy);
                if (f == kFEleID) wl.removed |= (1u << kFEMuTrig) | (1u << kFEleTrigProxy);
                if (f == kFMuID) wl.removed |= (1u << kFDblMuTrig) | (1u << kFEMuTrig);''')
rep('src/DiLepton.cc','''                        for (int f = 0; f < kNFactors; ++f) {
                            if (f != wl.factor) w *= fv.nom(f);''','''                        for (int f = 0; f < kNFactors; ++f) {
                            if ((wl.removed >> f) & 1u) continue;
                            if (f != wl.factor) w *= fv.nom(f);''')
rep('data/DiLeptonSystematics.yaml','''# Central has NO top-pT weight;''','''# A "<factor>_NotImplemented" lane also divides out the SFs measured on top of that factor
# (user 2026-11-26): ElectronRecoSF -> ElectronIDSF -> EMuTrigSF / ElectronTrigSFProxy,
# MuonIDSF -> DblMuTrigSF / EMuTrigSF.
# Central has NO top-pT weight;''')
print("patched")
