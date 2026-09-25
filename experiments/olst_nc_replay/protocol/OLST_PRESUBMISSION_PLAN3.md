# OLST paper: pre-submission plan

Companion to `OLST_MANUSCRIPT_v2_DRAFT.md`. Order: decide the v2 mapping → run the full corpus under v1 and v2 → (optionally) add Berg → freeze the artifact → fill placeholders → submit. Nothing below touches `dpg-platform` or `clinprep-core`; the experiment lives on `feature/olst-nc-replay-execution` in its own repo.

Note on what I could and could not verify: the experiment code is not in either attached repo, and PhysioNet and the Berg reference sites are blocked from this sandbox. Every dataset-semantics and Berg-rubric statement below is from the draft or from memory and is marked VERIFY where it matters.

---

## Step 0 — Decisions that gate everything (author, ~1 hour)

These are clinical-mapping decisions. The manuscript is written so either answer works; the numbers cannot be produced until they are made.

### D1. What duration variable does "sustained stance" correspond to in this dataset?

The draft evaluates `t_stable → t_break`, described as the stable phase within an attempt. Windows of 70 ms to 3.9 s are far too short to be one-legged stance durations for healthy young adults, which strongly suggests `t_stable → t_break` is a sub-phase and the stance itself is `t_foot_up → t_end` (touchdown).

- **VERIFY** against the dataset description / `OLST_Attempts.csv` column notes: what exactly do `t_stable` and `t_break` mark? Is `t_end` foot touchdown or capture end?
- Compute, on all captures, both `t_break − t_stable` and `t_end − t_foot_up`. Plot the two distributions by cohort. This single figure settles D1 and belongs in the paper (Section 4.3/4.4).
- If `t_end − t_foot_up` lands in the expected range (young mostly >10 s, older spread), v2 = foot-up-to-touchdown. If it is also short, the protocol and the clinical construct genuinely differ, and v2 should be a per-attempt criterion with documented non-equivalence (the draft's option b).

Do not freeze D1 on plausibility. The 70 ms to 3.9 s windows make the sub-phase reading likely, but the distributions and the dataset's own event definitions decide it, and either outcome is a reportable result (construct correction, or documented non-equivalence between the public protocol and the clinical construct).

**Recommendation, conditional on the distributions:** v2 uses `t_foot_up → t_end`, keeps the `t_stable → t_break` window for the CoP-derived EMUs (that is where "stable phase" semantics are correct for sway), and adds `stance_duration_ms` to `gait_temporal_control` if it is not already there.

### D2. Session aggregation rule

OLST clinical convention records the best of several attempts. Recommendation: `best_of_attempts = max(stance_duration_ms)` per capture, evaluated only if every attempt yielded the EMU; else the aggregate is non-evaluable with a reason naming the attempt that lacked labels. Keep per-attempt evaluations in the output next to the aggregate. Aggregation is declared in the map JSON, not in harness code, so the harness stays untouched.

Alternatives you might prefer: mean of attempts (less conventional), or first-attempt only (matches Berg's single-trial administration). Pick one and state it; do not pick by looking at which gives the nicest label distribution.

### D3. Derivability class of the Morse gait item

Morse "gait" is scored from observed ambulation (normal; weak = stooped, short steps, may shuffle; impaired = difficulty rising, watches ground, grasps furniture). Single-leg balance is a proxy. Recommendation: reclassify `gait` from `derivable` to `partial` in v2 with the reason stated. This makes v2 both a recalibration and an honesty increase, and it is a stronger story than a threshold tweak alone. If you keep `derivable`, add a sentence justifying it.

### D4. Thresholds

Recommendation: keep 10 s / 5 s on the corrected construct so the v1→v2 change is purely a construct correction and the comparison is clean. Record Springer 2007 / Bohannon 2006 age norms in the map as reference metadata, not as label-changing rules. Do not tune.

### D5. Second framework: do it if it is really one file

Berg Balance Scale is the cheap choice because item 14 (standing on one leg) has a published duration rubric that maps straight onto the corrected v2 construct: 4: >10 s, 3: 5–10 s, 2: ≥3 s, 1: tries but <3 s while standing independently, 0: unable (**VERIFY** wording against the original scale sheet; the 1/0 anchors will map to non-evaluable or to "attempt with no stable phase", decide which). Items 2, 6, 7, 13 are different stance conditions (bipedal, eyes closed, feet together, tandem): mark partial or non-evaluable with the condition difference as the reason. Items 1, 3, 4, 5, 8, 9, 10, 11, 12 are non-evaluable.

Timed Up and Go is not a good second framework here: it is a walking task and the corpus has no walking, so every criterion would be non-evaluable. That is a degenerate demonstration, not a generalization demonstration.

Success condition for the claim "no harness change": `git diff --stat` between the pre-Berg and post-Berg commits shows only the new map JSON, golden hashes, fixture expectations, and tests; `harness_version` and `spec_id` identical across Morse and Berg runs. Put the diff stat in the paper.

---

## Step 0.5 — Freeze the protocol before any D1 analysis

Because nothing has been circulated, the protocol can be frozen honestly now, and the final paper can then truthfully report: initial mapping → unexpected empirical finding → prospectively specified correction → validation run. To make that checkable:

1. Commit the current manuscript draft and this plan into the experiment repo (e.g. `experiments/olst_nc_replay/protocol/`) **before** computing the D1 distributions. Record the commit SHA and the SHA-256 of both files here: `[[FILL]]`.
2. Treat D2–D4 as decided at that commit. If the D1 distributions force a change to D2–D4 (outcome (b) in manuscript Section 3.6), record the change as a dated amendment with its reason, not as a silent edit.
3. The manuscript's `⟨PROTOCOL⟩` blocks are the preregistered analysis; Section 4.5's success condition and Section 3.10's version-distinctness test are the prespecified pass/fail criteria.

## One paper or two: decision rule (settled now, applied after Step 3)

Default: one paper. The current story is coherent as a single progression: replay-stable clinical computation meets evidence insufficiency, exposes a construct error in its own mapping, preserves the original execution, revises the interpretation as a separately identified version, and tests whether the same evidence machinery supports a second framework without changing the transformation or replay system.

Split only if the experiments reveal a second question, judged by these rules after Steps 1–3:

- Berg is one map file plus tests plus a coverage table → stays in Paper 1 as the generality demonstration.
- Berg exposes substantially new framework semantics, new kinds of partial or non-evaluable relationships, or motivates systematic comparison across several frameworks → that material becomes Paper 2 (working idea: *decision compatibility across clinical frameworks*, the same evidence having different legitimate standing under different instruments).
- The v1→v2 recalibration produces substantial material (strong cohort differences, important construct consequences) → still Paper 1; it is the best demonstration of replay and versioning.
- Never split to obtain two publications. Paper 1 must not lose its generality demonstration to make Paper 2 viable.

## Step 1 — Full PhysioNet corpus (~1 day, mostly download)

1. Pull the full release (~10 GB) and verify every file against `SHA256SUMS.txt` before anything else.
2. Run `olst_real_loader.build_fixture()` on every capture; confirm `12_MNTRL_V2` is refused by the gate and nothing else is.
3. Record inventory: participants, captures per participant, attempts per capture, cohort split. Fill Section 3.1.
4. Determinism on real fixtures: N=100 per fixture is plenty (N=1000 on ~100+ captures is unnecessary; say so in the paper if a reviewer asks why the synthetic N is larger).
5. Baseline comparison over the full corpus under v1: agreement count, evidence-pointer counts (3 per trial vs 0). Fill Section 4.3.
6. The distribution figure from D1 (both duration variables, by cohort, log-scale x is probably needed). This is the paper's Figure 1 or 2.

## Step 2 — v2 map and versioned replay (~half a day once D1–D4 are decided)

1. Write `NC_CRITERION_EMU_MAP_v2.json`. Leave v1 byte-identical (its golden hashes must still pass).
2. Extend the harness only if `stance_duration_ms` is not already in `gait_temporal_control`; if you must touch the harness, do it *before* the v1 full-corpus run so v1 and v2 share a `harness_version`. Otherwise the v1/v2 distinctness result is confounded.
   This creates two v1 execution contexts in the store: pilot-era v1 at commit `37e436d`, and full-corpus v1 under the frozen pre-v2 harness. Same map bytes, different `harness_version`, different `run_id`. Report it that way (manuscript Section 4.4, "Execution identity of v1"); never imply the full-corpus v1 run is byte-identical in execution context to the pilot if the harness gained a field. Record both harness digests.
3. Run the full corpus under v2. Ingest into the same store as the v1 runs.
4. Assertions to add to the test suite (these become paper claims):
   - for every real fixture, `run_id(v1) != run_id(v2)`;
   - in each pair, `fixture_id`, `spec_id`, `harness_version` equal and `criterion_map_id` different;
   - `verify_replay` true on all v1 and all v2 runs;
   - `recall` of a v1 run after v2 ingest reproduces the v1 output hash.
5. Report v1 and v2 label distributions side by side, by cohort. Fill Section 4.4.

## Step 3 — Berg (optional, ~half a day)

1. `BERG_CRITERION_EMU_MAP_v1.json`, fixture expectation rows, golden hashes, tests.
2. Run synthetic suite and full corpus under Berg; ingest.
3. Coverage table, item 14 distribution, diff stat. Fill Sections 3.7 and 4.5.

## Step 4 — Freeze the artifact

1. Tag a release; record the SHA in the manuscript header and Section 4.
2. Archive the tag (Zenodo or equivalent) for a DOI. Include the store snapshot, fixtures, golden hashes, and a README with the exact commands.
3. License the code (MIT/Apache-2.0) and confirm the fixture files do not redistribute PhysioNet data beyond what its terms allow (fixtures derived from the CSVs may count as redistribution; the `dataset_pointer` design lets you ship hashes only and regenerate fixtures from a local copy if needed).
4. Run the full test suite from a clean clone of the tag, not from the working tree.

## Step 5 — Manuscript fill and cuts

**Tense rule.** The manuscript now carries `⟨PROTOCOL: …⟩` blocks around every unrun result. A block is converted to past-tense prose only when its numbers exist from a clean-clone run of the tagged artifact. Before submission, grep for `⟨PROTOCOL` and `[[`; both counts must be zero. If Berg was attempted and the no-harness-change condition failed, contribution 5 is withdrawn and Section 4.5 reports the attempt.

Fill every `[[FILL]]`. Then check these cuts, all of which the draft already partially makes:

- Remove every reference to substrate, gateway, HomeField, ProvenanceOS, EMU-as-product, federation, or the internal technical brief. The revised draft already drops them; make sure nothing creeps back in via Appendix or acknowledgments. "EMU" is fine as a term defined in Section 3.3.
- Remove the old Section 6 "cross-domain extension" paragraph entirely (done in the revision).
- Keep the calibration episode as a headline result (Sections 4.3–4.4, Discussion), not a limitation.
- Confirm the paper never says: fall prediction, clinically validated, use clinically, or that determinism implies correctness. Section 1.4 and Section 6 item 6 state the opposite explicitly.
- References: add 2–3 on imputation in clinical ML and 1–2 on selective prediction / reject option; add the dataset authors' citation in PhysioNet's required form; add Berg 1989/1992, Springer 2007, Bohannon 2006.

## Step 6 — Venue (suggestions, not part of the recommendations you were given)

Methods-and-artifact framing fits: *Journal of Biomedical Informatics*, *JAMIA Open*, *PLOS Digital Health*, *Scientific Data* (if reframed around the fixtures/store as a data artifact), or *Journal of Open Research Software* for a software-paper variant. Preprint on arXiv (cs.SE / q-bio.QM) or medRxiv is reasonable once the artifact is frozen.

---

## Placeholder inventory (what the experiments must produce)

| Placeholder | Source |
|---|---|
| Corpus inventory (captures, attempts, cohorts) | Step 1.3 |
| Distribution of both duration variables by cohort | Step 1.6 (figure) |
| v1 full-corpus labels, agreement, pointer counts | Step 1.5 |
| v2 per-attempt and best-of-attempts distributions, label counts, cohort table | Step 2.5 |
| v1/v2 distinctness and verify_replay counts | Step 2.4 |
| Real-data determinism N and timing | Step 1.4 |
| Berg coverage table, item 14 distribution, diff stat | Step 3 |
| Store size and run count | Step 4 |
| Release tag, SHA, DOI | Step 4 |

## Manuscript language rule on versions

Internally, `v1` and `v2` are real identities and stay. In the manuscript, v1 is "the prespecified initial mapping" and v2 is "a correction specified after the mismatch was discovered, with the original retained unchanged for reproducibility." Nothing in the public text should read as though a previously published method existed. The draft header now says so explicitly.

## Things I changed in the manuscript that you should review

1. Title and abstract lead with evidence insufficiency; architecture vocabulary moved behind it.
2. Contributions list rewritten as five claims; the fifth is conditional on Berg.
3. New Section 3.6 (Morse v2) and 3.7 (Berg) with the D1–D5 decisions embedded as `[[DECIDE]]` markers.
4. The calibration finding moved from Limitations 5.1 to Results 4.3 and 4.4 and to the Discussion.
5. A "Missing data in clinical computation" paragraph added to Related Work to position against imputation and selective prediction; needs citations.
6. Removed the internal HomeField technical brief citation and all substrate/gateway text.
7. Added Limitation 6 ("determinism is not correctness") and a short "what this paper does not claim" subsection in the Introduction.
8. Baseline described as "the shape of a reasonable first implementation, not a straw man"; reviewers will otherwise say it is one.
