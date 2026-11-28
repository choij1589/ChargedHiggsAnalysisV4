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
- **P6 diboson b-jet promotion:** re-derive the rank-promotion tables for 2024 (previous method) or use
  genuine b-tagged WZ / ZZ only (low statistics).
- **P7 mass decorrelation:** keep DisCo lambda = 0.1 on the A-candidate mass(es) without a lambda scan,
  or drop it (with window-based parametrization the score shape on the mass matters less).
- **P8 splits:** (a) event-number based folds (train / valid / test), templates from all events as
  before; (b) k-fold cross-training (k networks, each event scored by the network that did not see it).
- **P9 inference:** offline python on the SR RNTuples (recommended) vs SKNano PyAnalyzer vs libtorch C++.
- **P10 environment:** a pinned local env `PNet` (torch with CUDA 12, PyG), exported to `config/env/`
  (the local `Nano` env has torch 2.4.1+cu121 with CUDA but no PyG).

## Steps (after the decisions)

1. TrainTree lane in TriLepton (local compile check during the KNU downtime), production after
   11/30 20:00.
2. Dataset builder (graphs, mA assignment, classes, weights, folds) and its validation.
3. Local training (fixed hyperparameters), monitoring of loss / AUC per mA window and class.
4. Inference on the SR RNTuples, templates with the score (working point per window), limits; compare
   with the Baseline limits and B2G-25-013.
