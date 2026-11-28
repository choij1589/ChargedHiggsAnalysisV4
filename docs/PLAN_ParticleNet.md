# PLAN: ParticleNet (2024, mH+ = 130 GeV, full mA range)

Milestone: a ParticleNet classifier for the 2024 signal regions, parametric in mA over the full range
(15-125 GeV at mH+ = 130 GeV), trained on the local GPU, and its score used in the templates
(PLAN phase 5). Status and decisions: below; dated findings in `LOG_EventSel.md` / `LOG_TmpCnstrct.md`.

## User decisions (2026-11-28)

- **Full mA range.** The network covers all of mA (previous: only 82.5-97.5 GeV, 15 per-point models).
  The background composition changes with mA (conversions / low-mass DY at low mA, WZ / ZZ around the
  Z, ttX higher up), so the training sample design must follow it (P3, P4).
- **Parametric network**, one model, trained on the local host (RTX 2070 SUPER, 8 GB). **No GA
  optimisation** this round: fixed hyperparameters.
- **FP32** training.

## What the previous analysis did (B2G-25-013, code is authoritative)

Research summary 2026-11-28 (paths under `docs/previous_analysis/`):

- **Variant:** `ChargedHiggsAnalysisV3/ParticleNetMD` (DisCo mass decorrelation, lambda = 0.1), 15
  classifiers mA = 85/90/95 x mH+ = 100-160 (+2 validation points), used only in 82.5 <= mA <= 97.5 with
  template-sharing groups of +-2.5 GeV; template variable `LR_modified = s_sig / (s_sig + sum w_i s_i)`
  (w_i = background-class fractions in the window), cut at background efficiency 20%.
- **Training trees:** `SKNanoAnalyzer/Analyzers/src/EvtTreeProducer.cc` (MC only), "reduced baseline":
  exact loose-lepton counts per channel (Run1E2Mu: 2 mu + 1 e; Run3Mu: 3 mu, 0 e), OS mu mu with
  M > 12, one pair in 60-120 GeV (!), >= 2 jets; no trigger, no N_b, no tight requirement, no SFs.
  Flat TTree: up to 3 muons, 1 electron, 20 jets (pT, eta, phi, mass, charge, miniIso / b-score,
  isTight), PUPPI MET; weights genWeight x xsec x lumi, PU, prefire.
- **Classes (4):** signal (tight); nonprompt = TTLL MC (9 variants) loose-not-tight + >= 1 b, fake-rate
  weighted; diboson = WZ + ZZ tight with 0 b, rank-based b-jet promotion (conditional tables); ttX =
  ttZ + tZq (no ttH despite the AN). No DY, conversion or ttW.
- **Graph:** nodes = muons, electrons, jets, b jets, MET; 9 features (E, px, py, pz, charge, isMu, isE,
  isJet, isB; no b-score / isolation), k = 4 nearest in Delta R for the first layer; 8-bit era one-hot.
- **Model:** GraphNorm, 3 DynamicEdgeConv (k = 4, residual, BN, dropout 0.4), mean pooling, 2 dense,
  4 logits; weighted CE + 0.1 [dCor(s_sig, m1) + dCor(s_sig, m2)]; batch 512, <= 120 epochs, patience
  10, phi rotation. GA over nNodes / optimizer / scheduler / LR / weight decay on Perlmutter.
- **Splits:** random 5 folds (seed 42, not event number), train 0-2 / valid 3 / test 4, 50k per class
  per fold, class-balanced weights. **Inference** in python SKNano PyAnalyzers on all events (training
  events included in the templates).
- **Issues to fix:** Run3Mu training kept only total charge +1 (the SR uses |sum q| = 1); signal and
  ttX had no b-jet requirement; training trees not at the SR selection; nonprompt / diboson
  validation and test folds are augmented; the "60 < M < 120" requirement restricts training to the
  Z window (fine for 85-95, wrong for the full range).

## Design (proposal; decisions P1-P10 below)

1. **Training trees from TriLepton** (P1, decided): a `TrainTree` lane in TriLepton (2024 object
   definitions and corrections identical to the SR trees), RNTuple per channel, object-level vectors
   (leptons with tight flag, jets with b-tag flag, MET), weights generator x pileup (+ fake-rate weight), the SR selection without the N_b and
   tight requirements, plus flags (tight, N_b, SR membership) so every class is selected offline. Both
   charge signs. MC only (data LNT optional, P5).
2. **Parametrization in mA** (P3): signal events carry their generated mA; background events get the
   mA values of the signal points whose template window `[x0 - 10 sigma_eff, x0 + 10 sigma_eff]`
   contains their A-candidate mass (one graph per (event, mA) pair), so the network learns the
   background mix of each window.
3. **Classes** (P4): signal / nonprompt / diboson / ttX (+ conversion if the low-mA windows need it).
4. **Training** local (PyG, CUDA, FP32), fixed hyperparameters from the previous best model at
   MHc130_MA90 (AN-25-154 `tab:BestModel`), DisCo on the A-candidate mass(es).
5. **Inference offline** on the SR RNTuples (local GPU), score columns written as friend RNTuples read
   by SignalRegionStudy (P9).

## Open decisions (one by one)

- **P1 training-tree producer: decided (user, 2026-11-28): (a) a `TrainTree` lane in TriLepton.**
  MC RNTuple `Train_<CH>` at the SR selection (trigger, plateau, jets, 2024 objects with their
  corrections) with loose leptons (tight flag per lepton) and any N_b, no Z window, both charge signs.
  Fields: per lepton 4-vector, charge, flavour, tight flag (no mini-isolation); per jet 4-vector and
  b-tag flag (no b-tag score: it would need a shape-based b-tagging correction); MET pT / phi; the two
  A-candidate masses and the pairing; event number; weights: **generator x pileup only** (any rescale
  of the central weight by SFs would require re-training; the object corrections are applied anyway;
  a slightly sub-optimal classifier is accepted) and the **fake-rate weight** computed in the analyzer
  (2024 rates). **The same object fields are added to all SR-tree lanes** (`SR_<CH>_<lane>`, incl.
  object variations and the data Nonprompt lane) for the offline scoring.
- **P2 node features: decided with P1 (user):** the previous 9 features (E, px, py, pz, charge, isMu,
  isE, isJet, isB); no b-tag score, no isolation.
- **P3 mA parametrization: decided (user, 2026-11-28): (a) window-based.** Signal events carry their
  generated mA. A background event enters with parameter mA_i for every signal point i whose template
  window `[x0 - 10 sigma_eff, x0 + 10 sigma_eff]` (SignalRegionStudy binning, 23 points; the interpolated
  grid later) contains its A-candidate mass; copies are weighted so that each mA_i sees the real
  background mix of its window. Scoring: the template at mA_i scores every window event with mA_i.
  Caveat: inside a window the network can learn |m(mu mu) - mA| from the muon 4-vectors (sculpting
  towards the signal peak, partly double counting the fitted mass) -> mass decorrelation in P7.
- **P4 classes: decided (user, 2026-11-28): (c) 4 classes** - signal, nonprompt, diboson (WZ + ZZ),
  ttX (ttZ + ttW + ttH + tZq). No conversion class (too few weighted MC events in the training
  selection; e.g. the MA30 eμμ template had one event carrying 4.6 of 9.9 events in a bin); "others"
  not trained. Window composition (v2 templates, % of window background): nonprompt 37-73 everywhere;
  WZ+ZZ + ttZ + tZq ~ half at the Z (80-105); conversion up to 10-16 off-Z; ttW up to 13 at high mA
  (eμμ); others 2-6.
- **P5 nonprompt sample: decided (user, 2026-11-28): (a) MC loose-not-tight with the 2024 fake-rate
  weights, with the (c) data check.** Sources TTLL + TTLJ + DY 2J (TrainTree lane, fake-rate weight from
  the analyzer). The data sideband is too small for training (2024 SR loose-not-tight: 2529 eμμ / 2689
  μμμ events, ~17% negative-weight, vs ~50k per class per fold before). Negative-weight events (two
  loose-not-tight leptons) dropped from the training, kept in the check (default, as proposed).
  Check after training: score distributions of MC vs data loose-not-tight per mA window.
- **P6 diboson: decided (user, 2026-11-28): (a) genuine b-tagged WZ + ZZ only, no rank promotion.**
  2024 SR (all tight, N_b >= 1) raw / weighted: WZ 36256 / 77.0 (eμμ), 48222 / 107.6 (μμμ); ZZ 59624 /
  43.2, 63264 / 47.9 (final production, 2026-11-28) - about 200k genuine events, above the previous
  per-class cap; promotion only if a window turns out short of diboson events.
- **P7 mass decorrelation: decided (user, 2026-11-28): DisCo on the in-window mass position**,
  Delta_k = (m_k(mu mu) - mA) / sigma_eff(mA) for the OS pairs k, lambda = 0.1 fixed (no scan), over the
  background events of each batch: loss = CE + lambda [dCor(s_sig, Delta_1) + dCor(s_sig, Delta_2)];
  mu mu mu uses both OS pairs (no pairing rule); e mu mu has only Delta_1, and the Delta_2 term is
  computed over the mu mu mu events of the batch only (mask, not Delta_2 = 0, which would correlate with
  the channel), so both channels train together in one network. Window membership (P3) stays with the
  template's A candidate. dCor per window logged as a monitor.
- **P8 splits: decided (user, 2026-11-28): (b) 5-fold cross-training.** Folds by `event % 5` (fold of
  any event known at scoring). Network j: test fold j (never seen), early-stopping fold (j+1) % 5,
  training on the other three. Every event (MC, SR data, data sideband) is scored by the network of its
  fold: no overtraining bias in the templates, full MC statistics. Checks: (1) per network, training vs
  held-out score distributions per class and mA window (ROC/AUC, KS); (2) fold-to-fold consistency of
  the held-out score distributions and AUCs; (3) the same fold rule for data, the P5 data check per
  network; (4) optional: one process' template from network j alone (fold j x 5) vs the fold-wise one.
  Cost: 5 trainings on the local GPU.
- **P9 inference: decided (user, 2026-11-28): (a) offline python on the local GPU.** Reads the SR
  RNTuples (object fields of P1), scores each event with its fold's network (P8) at every grid mA whose
  window contains its A candidate, for every lane (object variations), SR data and the data sideband;
  writes a score RNTuple per sample and lane (event key, list of (mA, 4 class scores)), joined by event
  key in SignalRegionStudy `sample_reader`. Score files go to our SKNanoOutput on /pnfs for the KNU
  chain (or the chain runs locally in the el9 container). No PyG in SKNano's environments.
- **P10 environment: decided (user, 2026-11-28): a separate env `PNet`** (first tried in `NanoV15`,
  reverted: triton needs gcc < 16, which forced NanoV15's compiler / C++ headers 16.2 -> 15.3 and broke
  ROOT's interpreter include-path detection). `PNet` (local, `config/env/PNet_local_explicit.txt`):
  python 3.14, pytorch 2.14.1 (cuda134_mkl), pytorch_geometric 2.8.1, pytorch_cluster 1.6.3 (CUDA 13.4),
  triton 3.7.1, cuda-cudart-dev 13.5, uproot 5.7.8, awkward, numpy, scikit-learn, pyyaml; **no ROOT**
  (RNTuples read with uproot, checked on the SR RNTuples incl. vector / uint64 fields). Training,
  scoring in PNet; plots in NanoV15 with plotter.py from the JSON / npz outputs. NanoV15 recreated from
  its morning lock (307/307 packages, ROOT clean). Driver 620.70 (CUDA 13.5).
  - PyG 2.8 `DynamicEdgeConv` needs pyg-lib >= 0.6 (py314 builds only up to torch 2.12): the layer is
    `torch_cluster.knn_graph` + PyG `EdgeConv` (same operation).
  - `torch.compile` works with the k-NN call excluded from tracing (`torch.compiler.disable`; no
    fake-tensor kernel for torch_cluster.knn) and GraphNorm / pooling given the batch size: eager 50 FP32
    steps 0.40 s, compiled 0.32 s (x1.26), first step 14 s, 221 MB (`ParticleNet/test/compile_test.py`,
    `micromamba run -n PNet`).
- **Hardware (user, 2026-11-28):** local RTX 2070 SUPER (8 GB). gamsa (RTX 3090, code under ~/Sync) is a
  possible fallback but heavily used by another user: train on the local host.

- **P11 sample weights and class balance: decided (user, 2026-11-28).** As ParticleNetMD
  (`DynamicDatasetLoader.py`: per class and fold a uniform random subsample to 50k events keeping the
  physical weights; `_balance_and_shuffle` rescales each class to the total weight of the heaviest class,
  per split), with two changes: (1) the per-sample **prescale** of the Train trees replaces the uniform
  subsample, N_s = round((n_s / Y_s) / min_s'(n_s' / Y_s')) within a class (kept events proportional to
  xsec x acceptance, ~uniform per-event weights; physical weights incl. N carry the composition);
  (2) **class rescaling per split and per mA window (ii)**: every window has equal signal and background-
  class totals (the Z-peak windows have ~10x the background of the low-mA ones). Preview from the SR
  trees (all tight, N_b >= 1): diboson WZ 1 / ZZ 3 (~125k kept); ttX ttZ(>50) 1, ttZ(4-50) 2, ttW 2,
  ttH 6, tZq 3 (~290k); signal 1 for all 23 points (1.39M; raw counts already follow the acceptance).
  Nonprompt (TTLL, TTLJ, DY 2J loose-not-tight x fake weight) and the final values from the first KNU
  Train test -> `HcToWA_Analyzers/data/TrainTreePrescale.yaml`. Signal within its class: by acceptance
  (low-mA points ~half the weight of mid-mA points).

## Status

- **Step 1 implemented (2026-11-28, SKNano `bcb270f`, local compile check only):** object fields in all
  `SR_<CH>_<lane>` RNTuples (lep_pt/eta/phi/mass [3, muons first, then the electron; lep_pt = the
  lane pT_corr, = pT for tight leptons], lep_charge, lep_isMuon, lep_isTight; jet_pt/eta/phi/mass,
  jet_isBtagged [UParT M, no score]; MET_pt / MET_phi; mass1/mass2 = both OS mu mu masses, pairing
  applied offline) and the MC-only `TrainTree` flag -> `Train_<CH>` (SR selection with loose leptons,
  any N_b, no Z window, both charge signs; nTight, allTight, passSR, weight_genpu = gen x xsec x lumi x
  PU, weight_fake = -prod(-f/(1-f)) over loose-not-tight leptons (2024 rates; 1 for all-tight),
  category + lep_genType, matchedPair). Size of the SR RNTuples ~1.6 -> ~7.6 GB.
  Open for the user: the conversion-sample filter is not applied in Train (DY 2J as a nonprompt
  source keeps its non-conversion events; `category` stored to reapply it offline).
  Validation plan on KNU after the downtime: histograms and existing fields identical to the
  previous build, vector sizes, masses from the lep 4-vectors, Train[passSR] = SR Central, weight
  checks, blinding, uproot read.

- **Steps 2-4 implemented (2026-11-28 evening, local, synthetic bench only):** `ParticleNet/python/`
  (`build_dataset.py`, `train.py`, `score.py`, model / losses / weights / windows modules), configs
  `ParticleNet/configs/{windows,classes,training}.json` (windows from the v2 binning.json per channel). Synthetic
  bench in the analyzer format (`test/run_synthetic_bench.py`): inputs, node building, window assignment, P11
  weights per (split, window, class), DisCo Delta_2 mask (zero gradient from e mu mu), torch.compile (|Delta logits|
  <= 2.5e-6), scores = held-out score of the own fold, row alignment with duplicated event keys: all pass
  (`test/results/synthetic_bench_20261128.json`). Step 20 ms (compiled, batch 512, 256 hidden), ~1 GB GPU.
  Replication ~3.4 (event, mA) pairs per background event (from the real SR masses); cost for 1.4M signal + 0.4M
  diboson/ttX + 0.4-2M nonprompt: 6-14 h for 5 networks x 40 epochs, 17-42 h at the 120-epoch cap
  (`test/results/cost_estimate_20261128.json`).
- **P9 amended (finding 2026-11-28):** (run, lumi, event) is not unique in the signal samples (run = lumi = 1,
  event numbers repeat across generation files). Score files are row-aligned friends of the input RNTuples (one
  file per sample, same RNTuple names and entry order); the event key is only a check. SignalRegionStudy
  `sample_reader` must align by entry.
- **Open for the user (choices made in the implementation, adjustable in the configs):**
  1. **Window coverage:** windows x0 +- 10 sigma_eff are narrow at low mA (2.8 GeV at mA = 15 with 5 GeV spacing):
     3-27% of background events (3MU 23-27%) are in no window and never trained; interp-grid points between the
     windows (e.g. mA = 17.5) would be scored on mass regions the network never saw. Options: train on the windows
     of the interpolated grid (376 points), or widen the training windows to the midpoints between neighbours.
  2. **P11 (ii) target:** every (split, window, class) cell gets the same total, so windows are also equal to
     each other (not only classes within a window). With signal only in its own window, the "signal by acceptance"
     weighting has no effect.
  3. **Signal only in its own window** (80% kept; 3MU 56-91%, lowest at MA60 from the pairing).
  4. **Delta_k** uses the channel's fitted x0 and sigma_eff (not the nominal mA); not clipped.
  5. **No jet charge** in the trees (P2's charge feature is 0 for jets; the previous analysis had it).
  6. Nonprompt = !allTight && N_b >= 1, positive total weight, TTLL + TTLJ + six DY 2J samples, no conversion
     filter (the open Train conversion-filter question; `classes.json` has the knob).
  7. Graph feature mA / 100 only (no era / channel flag); edge dropout 0.4 and ReduceLROnPlateau on the training
     loss kept from ParticleNetMD.

## Steps (after the decisions)

1. TrainTree lane in TriLepton (local compile check during the KNU downtime), production after
   11/30 20:00.
2. Dataset builder (graphs, mA assignment, classes, weights, folds) and its validation.
3. Local training (fixed hyperparameters), monitoring of loss / AUC per mA window and class.
4. Inference on the SR RNTuples, templates with the score (working point per window), limits; compare
   with the Baseline limits and B2G-25-013.
