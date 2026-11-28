"""Input reading and graph nodes of the 2024 ParticleNet (docs/PLAN_ParticleNet.md P1, P2).

Reads the TriLepton RNTuples Train_<CH> / SR_<CH>_<lane> (SKNano HcToWA_Analyzers/src/TriLepton.cc,
BindObjectFields / BookTrainTrees) with uproot. The reader accepts an RNTuple or a TTree with the same
field (branch) names (uproot exposes both through .keys() / .arrays()), so the synthetic bench can use
either. Fields used:
  objects: lep_pt, lep_eta, lep_phi, lep_mass (3 entries: muons, then the electron), lep_charge,
           lep_isMuon, (lep_isTight), jet_pt, jet_eta, jet_phi, jet_mass, jet_isBtagged, MET_pt, MET_phi;
  event:   mass1, mass2 (3MU lower / higher OS pair; 1E2MU mu mu, mass2 = -1), nBJets, run, lumi, event;
  Train:   allTight, passSR, weight_genpu, weight_fake, prescale, category.

Nodes (P2, previous ParticleNetMD DataFormat): one per lepton, jet and MET, 9 features
    [E, px, py, pz, charge, isMu, isE, isJet, isB]
with E = sqrt(p^2 + m^2) from (pt, eta, phi, mass); jets: charge 0 (no jet charge field in the 2024
trees), isJet = 1 for every jet, isB = jet_isBtagged; MET: (E = MET_pt, px, py, pz = 0), all flags 0.
Node order per event: the 3 leptons, the jets (descending pT, as stored), MET. Per node also (eta, phi)
for the Delta R k-NN of the first EdgeConv layer (MET: eta = 0, as the previous TLorentzVector(pt, 0, phi, 0)).
"""
import numpy as np
import awkward as ak
import uproot

OBJ_FIELDS = ["lep_pt", "lep_eta", "lep_phi", "lep_mass", "lep_charge", "lep_isMuon",
              "jet_pt", "jet_eta", "jet_phi", "jet_mass", "jet_isBtagged", "MET_pt", "MET_phi"]
EVT_FIELDS = ["mass1", "mass2", "nBJets", "run", "lumi", "event"]
TRAIN_FIELDS = ["allTight", "passSR", "weight_genpu", "weight_fake", "prescale", "category"]
CHANNEL_ID = {"1E2MU": 0, "3MU": 1}
N_FEAT = 9
FEATURES = ["E", "px", "py", "pz", "charge", "isMu", "isE", "isJet", "isB"]


def list_ntuples(path, prefix):
    """Names (without cycle) of the RNTuples / TTrees in `path` starting with `prefix`."""
    with uproot.open(path) as f:
        out = []
        for k, cls in f.classnames(recursive=False).items():
            name = k.split(";")[0]
            if name.startswith(prefix) and ("RNTuple" in cls or cls == "TTree") and name not in out:
                out.append(name)
    return sorted(out)


def has_ntuple(path, name):
    with uproot.open(path) as f:
        return name in [k.split(";")[0] for k in f.keys(recursive=False)]


def read_ntuple(path, name, fields):
    """Fields of one RNTuple or TTree as an awkward record array (missing optional fields raise)."""
    with uproot.open(path) as f:
        obj = f[name]
        keys = set(obj.keys())
        miss = [x for x in fields if x not in keys]
        if miss:
            raise KeyError(f"{path}:{name} lacks fields {miss}")
        return obj.arrays(fields)


def build_nodes(arr):
    """Node features of every event of `arr` (awkward record array with OBJ_FIELDS).

    Returns (x [N_nodes, 9] float32, etaphi [N_nodes, 2] float32, counts [N_events] int32); the nodes
    of event i are x[offset[i]:offset[i] + counts[i]] with offset = cumsum(counts) - counts."""
    n = len(arr)
    nlep = ak.num(arr["lep_pt"]).to_numpy()
    if n and not np.all(nlep == 3):
        raise ValueError("every entry must have 3 leptons")
    lpt = ak.to_numpy(arr["lep_pt"]).astype(np.float64).reshape(n, 3)
    leta = ak.to_numpy(arr["lep_eta"]).astype(np.float64).reshape(n, 3)
    lphi = ak.to_numpy(arr["lep_phi"]).astype(np.float64).reshape(n, 3)
    lm = ak.to_numpy(arr["lep_mass"]).astype(np.float64).reshape(n, 3)
    lq = ak.to_numpy(arr["lep_charge"]).astype(np.float64).reshape(n, 3)
    lmu = ak.to_numpy(arr["lep_isMuon"]).astype(bool).reshape(n, 3)
    nj = ak.num(arr["jet_pt"]).to_numpy().astype(np.int64)
    jpt = ak.to_numpy(ak.flatten(arr["jet_pt"])).astype(np.float64)
    jeta = ak.to_numpy(ak.flatten(arr["jet_eta"])).astype(np.float64)
    jphi = ak.to_numpy(ak.flatten(arr["jet_phi"])).astype(np.float64)
    jm = ak.to_numpy(ak.flatten(arr["jet_mass"])).astype(np.float64)
    jb = ak.to_numpy(ak.flatten(arr["jet_isBtagged"])).astype(bool)
    met = ak.to_numpy(arr["MET_pt"]).astype(np.float64)
    metphi = ak.to_numpy(arr["MET_phi"]).astype(np.float64)

    counts = 3 + nj + 1
    start = np.cumsum(counts) - counts
    ntot = int(counts.sum())
    x = np.zeros((ntot, N_FEAT), dtype=np.float64)
    ep = np.zeros((ntot, 2), dtype=np.float64)

    def fill(idx, pt, eta, phi, m):
        px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta)
        x[idx, 0] = np.sqrt(px * px + py * py + pz * pz + m * m)
        x[idx, 1], x[idx, 2], x[idx, 3] = px, py, pz
        ep[idx, 0], ep[idx, 1] = eta, phi

    for a in range(3):
        idx = start + a
        fill(idx, lpt[:, a], leta[:, a], lphi[:, a], lm[:, a])
        x[idx, 4] = lq[:, a]
        x[idx, 5] = lmu[:, a]
        x[idx, 6] = ~lmu[:, a]
    jstart = np.cumsum(nj) - nj
    jidx = np.repeat(start + 3, nj) + (np.arange(len(jpt)) - np.repeat(jstart, nj))
    fill(jidx, jpt, jeta, jphi, jm)
    x[jidx, 7] = 1.0
    x[jidx, 8] = jb
    midx = start + 3 + nj
    x[midx, 0] = met
    x[midx, 1], x[midx, 2] = met * np.cos(metphi), met * np.sin(metphi)
    ep[midx, 0], ep[midx, 1] = 0.0, metphi
    return x.astype(np.float32), ep.astype(np.float32), counts.astype(np.int32)


def event_columns(arr):
    """Event-level numpy columns (mass1, mass2, nBJets, run, lumi, event) of `arr`."""
    return {"mass1": ak.to_numpy(arr["mass1"]).astype(np.float32),
            "mass2": ak.to_numpy(arr["mass2"]).astype(np.float32),
            "nBJets": ak.to_numpy(arr["nBJets"]).astype(np.int32),
            "run": ak.to_numpy(arr["run"]).astype(np.int32),
            "lumi": ak.to_numpy(arr["lumi"]).astype(np.int32),
            "event": ak.to_numpy(arr["event"]).astype(np.uint64)}
