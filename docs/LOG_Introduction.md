# LOG: Introduction

Decisions and findings for the Introduction of AN-26-267. Newest entry first.

## 2026-11-27 (AN: Introduction finalized)

- **Checked** (an-writer): no change of content needed. The three TODOs now state their category: B2G-25-013 citation not obtainable yet (no arXiv / CDS record, checked 2026-11-27); final scope statement later phase (PLAN 6.1-6.4); PUPPI tune / jet requirements later phase (PLAN 2.6).
- **Open**: unchanged (bib entry for B2G-25-013 once public; scope sentence after PLAN 6; PUPPI item PLAN 2.6).

## 2026-11-25 (AN: Introduction written)

- **Written** (an-writer) `docs/AN-26-267/Sections/Introduction.tex` (skeleton replaced): 2HDM motivation (Type-I, H+ -> W A, custodial symmetry, light H+ in top decays, A -> mu mu), earlier searches (LEP, CDF, CMS 2016, ATLAS Run 2), the B2G-25-013 result, the 2024 feasibility scope (109.82 /fb, mH+ = 130 GeV, mA 15-125 GeV in 5 GeV steps), technical differences from B2G-25-013, roadmap. Shorter than AN-25-154: no 2HDM equations and no 2HDMC figures (not produced for this note).
- **Sources**: B2G-25-013 abstract (`docs/previous_analysis/B2G-25-013/B2G-25-013.tex`: 200 /fb, mH+ 70-160 GeV, observed limits 0.5-3.6e-6 and 0.8-6.8e-6); LEP limits 80 / 72.5 GeV as quoted in AN-25-154 with its reference; `HLT_Path.json` (luminosity); `CommonSampleInfo.json` (23 signal points); `LOG_Dataset.md`, `LOG_ObjectID.md`, `LOG_Trigger.md` for the differences. "Off shell for mA >~ 50 GeV" from mH+ - mA < mW with mH+ = 130 GeV.
- **Open**:
  - no bib entry for B2G-25-013 (cite once public);
  - the PUPPI tune / forNextIteration N5 point of the old TODO could not be verified from the repository; left as a TODO (PLAN 2.6);
  - final scope sentence (expected limits, combination, verdict) after PLAN 6.1-6.4.
