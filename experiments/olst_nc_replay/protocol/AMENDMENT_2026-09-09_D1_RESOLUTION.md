# Amendment 2026-09-09 — D1 resolution, protocol censoring (D4a), and pre-v1 harness freeze

Dated amendment to the frozen pre-submission protocol, per Step 0.5 item 2
("record the change as a dated amendment with its reason, not as a silent edit").
The two frozen drafts are not edited. This file is the record.

| Document | Identity |
|---|---|
| Frozen plan `OLST_PRESUBMISSION_PLAN3.md` | sha256 `4ade8845f132da647849c13263b558ef9723f188a4e7e13d897f7da2ed8acd89` |
| Frozen manuscript `OLST_MANUSCRIPT_DRAFT.md` | sha256 `8269444a132da002d8386b760d91f7de336a5ea37a61617fd5d1fb3f9c28f41a` |
| Freeze commit | `af1fc973ea05c6a56796856aad58a0d99e7f3691` (recorded at `efcbcf00fa9d911a2923636f4d074024a7692ce5`) |
| D1 artifact `d1_distributions.json` | sha256 `343c07c14bd2b98cf1fd41d4692d18433c15c9e92c56870ae881033256f4780e` |
| D1 script (outside repo) `~/Downloads/d1_duration_distributions.py` | sha256 `d01c2fcd22e36d746a9aa2bf7c334677cc8353a77b26c4157fd072dd00709dab` |
| `Metadata/OLST_Attempts.csv` | sha256 `fdfed70659a153f0be3a19edaf8c810ddb9d91c29f1668b8b95f80e192e3253b` (matches `SHA256SUMS.txt`) |
| `Metadata/Participant_Demographics.csv` | sha256 `92d8b45db27dd28af0949c735dc83027d4ec89ff76b21f3e7a403cd569cb83f5` (matches `SHA256SUMS.txt`) |

D1 was computed after the freeze commit and before any v2 artifact existed.
No threshold was changed. D2, D3, and D4 stand as frozen. This amendment
adds D4a and D2a, records the D1 resolution, and records the harness changes
made before the v1 full-corpus run so that v1 and v2 share `harness_version`
(plan Step 2.2).

---

## A1. D1 result and resolution

Definitions used by the D1 script: `stable_phase_s = t_break − t_stable`
(None when either event is empty; no fallback to `t_end`),
`stance_s = t_end − t_foot_up`. Corpus: 1238 attempts, 333 captures,
32 participants, 3 rows of `12_MNTRL_V2` excluded.

Per-attempt:

| Cohort | Variable | n | min | median | max | ≥3 s | ≥5 s | ≥10 s |
|---|---|---|---|---|---|---|---|---|
| young | stable_phase_s | 181 | 0.15 | 3.48 | 4.06 | 167 | 0 | 0 |
| young | stance_s | 269 | 0.53 | 4.53 | 5.28 | 223 | 13 | 0 |
| older | stable_phase_s | 642 | 0.02 | 2.07 | 17.25 | 222 | 57 | 18 |
| older | stance_s | 969 | 0.10 | 2.45 | 21.31 | 381 | 142 | 73 |

Best-of-attempts per capture under the frozen D2 rule (evaluable only if
every attempt in the capture has the field):

| Cohort | Variable | evaluable captures | median | max | ≥5 s | ≥10 s |
|---|---|---|---|---|---|---|
| young | stable_phase_s | 0 / 88 | — | — | 0 | 0 |
| young | stance_s | 88 / 88 | 4.79 | 5.28 | 12 | 0 |
| older | stable_phase_s | 28 / 245 | 4.04 | 17.25 | 7 | 4 |
| older | stance_s | 245 / 245 | 4.83 | 21.31 | 116 | 72 |

**Resolution: outcome (a), construct correction.** `t_foot_up → t_end` is
the one-legged stance interval by the dataset's own event definitions
(foot-lift to foot-touchdown, `README.txt`), it is present on every kept
attempt, and where the acquisition protocol permitted sustained stance it
spreads to 21.3 s. v2 evaluates `stance_duration_ms` over that interval.
`t_stable → t_break` is retained for the CoP-derived EMUs, where stable-phase
semantics are the correct ones for sway.

The binary decision rule in the plan ("young mostly >10 s, older spread")
did not fire cleanly because the young cohort never exceeds 5.3 s. That is
not a property of the variable. It is a property of the acquisition protocol
(A2). Option (b) of manuscript Section 3.6 therefore applies to a subset of
captures, not to the variable: for those captures the public protocol does
not instantiate the sustained clinical construct, and that non-equivalence
is declared per capture (A3), not by redefining the criterion.

Supporting observation: `t_break` is absent on every young final attempt and
on 415 attempts overall, so the stable-phase variable cannot support the D2
aggregate on any young capture. `t_break` marks end of stability, not end of
stance; the two events are not interchangeable, which is exactly why the two
windows feed different EMUs.

## A2. Protocol finding: the observation ceiling tracks the movement code

The capture id's movement code identifies two acquisition protocols. The
dataset README glosses `MNTR*` ("Mountain-to-Tree, left/right foot as base")
and states that "the older adult participants completed longer 20-second
trials"; those are the `TRLG*` captures, which the README does not gloss by
name.

| Movement code | Cohorts | Captures | Attempts | stance_s median | stance_s max | attempts ≥10 s | best-of ≥10 s |
|---|---|---|---|---|---|---|---|
| MNTRL | young | 43 | 132 | 4.48 | 5.22 | 0 | 0 |
| MNTRR | young | 45 | 137 | 4.59 | 5.28 | 0 | 0 |
| MNTRL | older | 61 | 261 | 2.52 | 6.34 | 0 | 0 |
| MNTRR | older | 60 | 251 | 2.60 | 5.64 | 0 | 0 |
| TRLGL | older | 62 | 250 | 1.86 | 21.31 | 35 | 34 |
| TRLGR | older | 62 | 207 | 2.45 | 20.93 | 38 | 38 |

`MNTR*` captures are cued short attempts: young captures hold three attempts
with foot-lift events spaced 7.97 s apart (median) inside a ~30 s capture and
a per-participant maximum stance of 4.8–5.3 s for all 15 young participants.
Older `MNTR*` captures show the same ceiling (max 6.34 s across 512 attempts).
`TRLG*` captures are the 20-second sustained-balance trials and exist only for
the older cohort. Seventeen older participants performed both protocols, so
the same participants, under the same duration variable, are observable to
10 s in one capture type and not in the other.

Base leg for `TRLG*` was verified from the force plates, not assumed: during
the stable window of `30_TRLGL_V1` the left plate carries 99.3% of vertical
force; for `30_TRLGR_V1` the left plate carries −0.7%. `TRLGL → left`,
`TRLGR → right`, matching the `MNTR*` convention.

## A3. D4a — protocol censoring (new; D4 thresholds unchanged)

**Rule.** When the acquisition protocol imposes a maximum observation
duration below a criterion threshold, failure to cross that threshold is not
interpreted as failure of the participant. The criterion output records
`protocol_censored`, names the protocol ceiling, and reports the measured
duration. Threshold categories are emitted only where the protocol permitted
the relevant threshold to be observed.

**Operationalization (declared before v2 is written or run).**

1. The ceiling is an acquisition fact, so it is carried in the fixture
   (`acquisition_protocol`), derived by the loader from the movement code,
   with its source named. It is not a map parameter.
   - `TRLGL`, `TRLGR`: `observation_ceiling_ms = 20000`. Source:
     `README.txt`, "older adult participants completed longer 20-second
     trials". Observed maxima slightly exceed 20 s (21.31 s); the ceiling is
     the instructed trial duration, and it exceeds every v1/v2 threshold, so
     all categories are observable.
   - `MNTRL`, `MNTRR`: `observation_ceiling_ms = null`. The README does not
     state the cued attempt duration. The empirical bound from D1 is
     6.34 s over 781 attempts, which is below the 10 s threshold for every
     attempt; the nominal cue is not inferred from the data and is not
     written into the fixture.
2. Evaluation semantics for a duration-threshold rule with censoring enabled:
   - ceiling `null` → no duration threshold can be confirmed observable →
     `protocol_censored`, listing every duration threshold as unobservable.
   - ceiling ≥ 10000 ms → all categories emitted as in v1.
   - ceiling between 5000 and 10000 ms (none in this release) → `impaired`
     may be emitted when duration < 5000 ms; otherwise `protocol_censored`.
   - The sway bound is measured inside the stable window and is not bounded
     by the stance ceiling; `sway_area_mm2 ≥ 600` therefore still yields
     `impaired` on a censored capture. `normal` additionally requires
     `sway_area_mm2 < 250`, unchanged.
3. The measured `stance_duration_ms` is always present in the evaluation
   record, censored or not. Censoring withholds the label, not the number.
4. The conservative reading for `MNTR*` (withhold even `impaired` when the
   cue time is unpublished) is chosen because the metadata cannot distinguish
   an attempt that completed the cued interval from one that broke early at
   the same duration. Reading the cue time off the distribution would be
   inference from the data; the loader does not do it.

**Consequence, stated before inspection.** Under D4a, every `MNTR*` capture
(all 88 young, 121 older) will be `protocol_censored` for the duration
component of v2 gait, and the 10 s distinction is exercised only on the 124
`TRLG*` captures. This is the reportable result: the correct variable can be
decision-incompatible with a threshold under one acquisition protocol and
compatible under another, within the same dataset and, for seventeen
participants, within the same person.

## A4. D2a — attempt-window integrity (new; D2 unchanged)

Attempt numbering was checked against event time on all 333 captures. One
capture, `47_TRLGL_V4`, has a final attempt row (`an4`, `t_foot_up` 11.09 s,
`t_end` 30.3 s, stance 19.21 s) whose window spans the whole capture and
overlaps `an1`–`an3`; `an4` is not chronologically last. Every other capture
is monotone in `an`. The data are not edited. Rules:

1. The best-of aggregate is non-evaluable when any two attempt windows
   (`t_foot_up → t_end`) in the capture overlap; the reason names the
   attempts. `max()` is order-independent, but an overlapping window is not a
   separate attempt and must not compete in a best-of.
2. Temporal analyses within a capture order attempts by `t_foot_up`, not by
   `an`. `attempt_number` in fixtures remains the dataset's `an` (it is
   provenance, not an ordering claim).

## A5. Attempts without a stable phase

152 kept attempts (149 non-final, 3 final; all older; 87 older captures
affected) have no `t_stable`. All have `t_foot_up` and `t_end`. Five
non-final attempts have `t_stable` but no `t_break`.

- Before this amendment the loader refused to build a fixture when
  `t_stable` was empty. After it, the fixture is built with
  `stability_phase: null` and `force_plate: null`, each with a
  `__missing_reason`, and with `stance_phase` present. Nothing is imputed;
  the gap moves from "no fixture" to "fixture with a declared gap", so the
  capture aggregate can name the attempt instead of being silently short one
  row.
- Per attempt, `postural_stability_index` is then absent and v1/v2 gait is
  non-evaluable with the EMU named. `gait_temporal_control` is still emitted
  with `stance_duration_ms` only, so the D2 aggregate over stance remains
  evaluable for the capture.
- For the five non-final attempts with no `t_break`, the existing loader rule
  (`end_ms = t_end` when `t_break` is empty) is retained and is now written
  into spec §6.4 explicitly.

## A6. Harness, loader, and spec changes before the v1 full-corpus run

Made now, per plan Step 2.2, so that the full-corpus v1 run and the v2 run
share one `harness_version`. These change `harness_version` and `spec_id`
relative to the pilot (commit `37e436d`), which the manuscript must report as
"Execution identity of v1" (plan Step 2.2). The v1 map JSON is byte-identical;
all 19 synthetic golden `fixture_id` and `output_hash` values are unchanged,
which is the test that the additions are inert for fixtures lacking the new
fields.

1. Loader: `stance_phase {foot_up_ms, touchdown_ms, event_label_source}`;
   `acquisition_protocol {protocol_code, observation_ceiling_ms,
   observation_ceiling_source}`; `TRLGL/TRLGR` base-leg mapping; fixtures
   built for attempts without `t_stable` (A5).
2. Harness `gait_temporal_control`: payload gains `stance_duration_ms`,
   `observation_ceiling_ms`, and `protocol_code` only when the fixture carries
   them; provenance gains the stance-window bounds and ceiling source.
   Emission requires at least one of the two windows. `balance_control_quality`
   requires `stability_duration_ms` explicitly.
3. Harness criterion-map selection by `mapping_spec_version`
   (`specs/NC_CRITERION_EMU_MAP_<version>.json`). An unknown version raises;
   it never falls back to v1.
4. Harness declarative rule block: a criterion may carry `rule` with a
   duration field, the same four numeric thresholds as v1, and a
   `protocol_censoring` flag. v1's map has no `rule` block and keeps the
   hard-pinned v1 path, which now reports non-evaluable (instead of raising)
   when `stability_duration_ms` is absent.
5. New module `olst_capture_aggregate.py` implementing the D2 best-of rule as
   declared in a map's `aggregation` block, with the A4 overlap check and the
   A3 censoring applied to the aggregate. It is outside `harness_version`
   and records its own file digest as `aggregator_version`. Sway is
   per-attempt and does not enter the aggregate label; per-attempt labels are
   listed beside the aggregate.
6. Naming caution, recorded so it cannot surprise a reader: the pre-existing
   `postural_stability_index.stance_duration_ms` is the stable-window length
   (`t_stable → t_break`), identical to `gait_temporal_control.stability_duration_ms`.
   It is a misnomer retained for v1 output-hash stability. No v2 rule reads it.
   The corrected construct is `gait_temporal_control.stance_duration_ms` only.
7. Loader float summation uses `math.fsum`. Rebuilding the pilot fixture
   `01_MNTRL_V1_an1` on Python 3.14.6 reproduced every value except the last
   bits of `mean_cop_displacement_mm` and `left_pct`/`right_pct`
   (10.926190301956588 vs 10.926190301956622). Cause: the pilot was built on
   Python 3.9.6, and built-in `sum()` switched to compensated summation in
   3.12. `output_hash` was never affected because canonicalization rounds
   floats to 6 decimal places; `fixture_id` is the raw bytes and was. `fsum`
   is correctly rounded on every interpreter, so the fixture builder no longer
   depends on the interpreter. The committed pilot fixtures are left as built.
   The full-corpus fixtures are built once, on one recorded interpreter, and
   their `fixture_id`s are what the store verifies against.

## A7. Data availability (Step 1 precondition, not met at the time of writing)

Inventory of the local mirror against `Metadata/OLST_Attempts.csv` and
`SHA256SUMS.txt` on 2026-09-09:

| Item | Count |
|---|---|
| Captures in metadata (excl. `12_MNTRL_V2`) | 333 |
| Captures with MoCap + both force-plate files on disk | 99 |
| Participants with raw data present | 10 (`01 02 14 15 22 30 35 39 51 56`) |
| Participant directories present but empty | 22 |
| Present raw files verified against `SHA256SUMS.txt` | 298 / 298, 0 mismatches |
| Files listed in metadata but absent from `SHA256SUMS.txt` | 2: `Raw/ForcePlate/35/35_MNTRL_FP_V4_{left,right}.csv` |

The 2 manifest-absent files mean capture `35_MNTRL_V4` cannot be built under
the current loader even from a complete mirror (no force-plate source, no
content hash for the pointer). It is recorded here as a release-level gap
alongside `12_MNTRL_V2`, but it is not added to `KNOWN_CAPTURE_EXCLUSIONS`,
which is reserved for maintainer-published exclusions. The full-corpus script
reports it as `source_missing_upstream`; locally absent files are
`source_missing_local`. Neither is a non-evaluable criterion reason, and
neither is ingested into the committed store as a result.

Step 1 does not start until `Raw/MOCAP` and `Raw/ForcePlate` are complete for
all 32 participants and verified. No partial "full corpus" run is ingested
into `artifacts/olst_lakehouse/`. Metadata-only fixtures (stance window
without force-plate metrics) were considered and rejected: they would make a
local-mirror gap look like an evidence gap.

## A8. Unchanged

- D2 `best_of_attempts = max(stance_duration_ms)`, evaluable only if every
  attempt yields the EMU.
- D3 Morse gait `partial` under v2.
- D4 thresholds 10 s / 5 s and sway bounds 250 / 600 mm², applied to the
  corrected construct. No tuning was performed after seeing D1.
- `NC_CRITERION_EMU_MAP_v1.json` bytes.
- The two frozen drafts.

## A9. Freeze record

- Amendment commit: `e293265f042c0120850ff59fc669577f5f290290`
- Harness freeze commit (loader, harness, spec v1.3, aggregate module,
  tests): `7252ce6c77196a2a06f4b675bc816536e72be13c`
- `HARNESS_VERSION` at freeze: `193dba29eda4a682aa63cc8c2d674b3274fc4c6ec9f2dbdb410b96417638d5d5`
- `spec_id` at freeze (spec v1.3): `9de0a3dac84dea495e88a36a304b7499dbd50cfeabbf9c26eaa94adfc7a562be`
- `criterion_map_id` of v1 (unchanged since the pilot): `2267d7c95ee88df0856f16897317394838804d2bee3f63c9f857c57346c6e4ed`
- `AGGREGATOR_VERSION` (`olst_capture_aggregate.py`): `d30f3254b4cdf494fd962d3cd8cfbecdf121fc4676b68c8561a67031d3c5ad15`
- Tests at freeze: 59 pass on Python 3.9.6 and 3.14.6; pilot store
  `verify_replay` 28/28 under the frozen harness.
- Pilot-era v1 execution context for comparison (plan Step 2.2): commit
  `37e436d9`, fixtures built on Python 3.9.6.

## A10. v2 map specified and frozen before any v2 execution on real data

`specs/NC_CRITERION_EMU_MAP_v2.json` was written on 2026-09-09 after the
harness freeze and before the Raw/ mirror was complete, so no v2 label on real
data existed or could exist when its bytes were fixed. It encodes D1 (stance
construct), D2/D2a (aggregation block), D3 (`partial`), D4 (same numbers),
and D4a (`protocol_censoring: true`). Non-gait criteria text is byte-identical
to v1 apart from `mapping_rule_version`; a test asserts this.

- `criterion_map_id` of v2: `d4ac623a2590f51bb8351bced784f58e88e3c4f75683482ca0cc1d2d2529d3c4`
- `fixtures/golden_output_hashes_v2.json` (19 synthetic fixtures under v2;
  gait_type non-evaluable on all, since synthetic fixtures carry no stance
  window): sha256 `861dc990a1c38e681db660ce291891b57f8ba04e9aec83c7e7aacebaf98a681e`
- v2 map commit: `950e04b4f1767ccf2b75d4b59e41da861ed9a683`

Step 1 (v1 full corpus) and Step 2.3 (v2 full corpus) run in that order once
A7's precondition is met. Both use `_run_full_corpus.py` under the frozen
`HARNESS_VERSION` above.

## A11. Step 1 executed (v1 full corpus), 2026-09-09

**Mirror completion.** The 698 Raw files missing from the local mirror (A7)
were fetched from PhysioNet on 2026-09-09 (UTC 18:00–23:25). PhysioNet's TLS
certificate expired at 20:22:45Z mid-fetch; the remaining 297 files were
fetched with certificate verification disabled and every file was verified
against `SHA256SUMS.txt` (obtained earlier over a valid session; metadata
hashes matched), once by the fetch loop and again by the driver. Transport
trust was replaced by content verification, not waived. Result: 997 of 999
Raw files referenced by the metadata present and verified, 0 mismatches; the
2 absent are the `35_MNTRL_V4` force-plate files missing from the release
manifest (spec §6.7).

**Run.** `_run_full_corpus.py --mapping-spec-version v1 --determinism-n 100`,
Python 3.14.6, `allow_partial = false`. Artifact
`artifacts/olst_full_corpus_v1.json`; fixtures `fixtures/real_full/`
(1233 files); store `artifacts/olst_lakehouse/` (1261 runs: 28 pilot-era +
1233). Identity: `HARNESS_VERSION` and `spec_id` as in A9; v1
`criterion_map_id 2267d7c9…`.

| Item | Value |
|---|---|
| Attempt rows / captures / participants | 1238 / 333 / 32 (15 young, 17 older) |
| Built | 1233 |
| `source_missing_upstream` (35_MNTRL_V4 an1–an5) | 5 |
| `source_missing_local`, `build_refused`, hash mismatch | 0 / 0 / 0 |
| Fixtures with a stable phase / without (no `t_stable`) | 1082 / 151 |
| Determinism | 1233 fixtures × 100 = 123,300 executions, 0 divergent |
| v1 gait evaluated / non-evaluable | 1082 / 151 (all 151: `postural_stability_index` absent) |
| v1 gait labels | `impaired` 1082, `weak` 0, `normal` 0 |
| Naive baseline labels | impaired 1113, weak 54, normal 66 |
| Naive = governed | 962 of 1233 (all 120 disagreements are naive normal/weak → governed impaired) |
| Evidence pointers | governed 3397, naive 0 |

**Finding: the v1 sway bounds are miscalibrated to real CoP data, independently
of the duration construct.** Under v1 every evaluated attempt is `impaired`,
including the 66 `TRLG*` attempts whose stable phase exceeds 10 s (naive
labels them `normal`). They are `impaired` because their 95 % confidence-ellipse
sway area is ≥ 600 mm² in every case (minimum 825, median 1789). Over all
1082 attempts with a stable phase:

| Group | n | sway p5 | median | p95 | < 250 mm² | ≥ 600 mm² |
|---|---|---|---|---|---|---|
| young MNTRL | 132 | 357 | 960 | 2850 | 4 | 109 |
| young MNTRR | 137 | 348 | 1025 | 3103 | 4 | 104 |
| older MNTRL | 228 | 105 | 1550 | 5293 | 22 | 189 |
| older MNTRR | 226 | 71 | 1417 | 10889 | 25 | 183 |
| older TRLGL | 190 | 32 | 1523 | 5949 | 30 | 144 |
| older TRLGR | 169 | 62 | 1561 | 6109 | 19 | 135 |
| all | 1082 | 77 | 1273 | 5620 | 104 (9.6 %) | 864 (79.9 %) |

The v1 bounds (`normal` requires < 250 mm²; ≥ 600 mm² forces `impaired`) were
drafted against synthetic fixture values of 140–250 mm² for clean cases and
480–540 mm² for "noisy" cases. Real single-leg-stance CoP ellipse areas are
roughly an order of magnitude larger. The 104 attempts below 250 mm² are
almost all sub-second stable windows (97 of 104 under 1000 ms, median 395 ms,
none at or above 5 s), so the conjunction `normal` requires (≥ 10 s stable
and < 250 mm²) is unreachable on this corpus; overall sway is only weakly
related to window length (Pearson r = 0.12, n = 1082). This is the same kind
of finding as D1, surfaced one layer later: a rule parameter whose scale was
never checked against the measurement it gates.

**Consequence for v2, stated before v2 is run.** v2 as frozen (A10) keeps the
v1 sway bounds and applies `sway ≥ 600 → impaired` before protocol censoring
(A3 item 2, "the sway bound is not censored"). On this corpus that override
would label about 80 % of attempts `impaired` irrespective of stance duration
or protocol, masking both the construct correction and the censoring result.
No change is made to v2 here. Options for the author to decide, as a dated
amendment, before or alongside the v2 run:

- (i) run v2 exactly as frozen and report the sway dominance as the
  preregistered result, then specify v2.1 with sway carried as evidence
  (reported in `detail`) but not as a labeling bound, and report both;
- (ii) amend v2 before running so that the gait label depends on the
  censored duration construct only, with sway reported, not gating;
- (iii) keep sway gating but with bounds derived from a stated external
  reference, which would be tuning unless the reference is independent of
  this corpus.

Recommendation: (i). It preserves the preregistered v2 and makes the sway
miscalibration a second reported recalibration episode rather than a silent
fix.

- Step 1 commit: `044335b2dad1dc437b97a3af527f479e39c6a6c0`

## A12. v2.1 — sway loses categorical authority, keeps evidentiary standing (2026-09-09)

Specified after the v1 full-corpus run (A11) and before any v2 or v2.1
execution on real data. v2 is not edited and is executed exactly as frozen
(A10); v2.1 is a further prospectively specified correction, triggered by
evidence that was available before it was written and that did not come from
inspecting any v2 output.

**Evidence (A11).** Under v1 on the full corpus, 1082 of 1082 evaluable
attempts were classified `impaired`. The duration-only naive comparator on
the same attempts produced 66 `normal` and 54 `weak`, so the collapse is not
caused by stance duration alone. Every one of the 120 disagreements is forced
by the `sway_area_mm2 ≥ 600` gate; no attempt with a stable phase ≥ 10 s has
sway below 825 mm², and only 104 of 1082 attempts (almost all sub-second
windows) fall below the 250 mm² `normal` bound.

**Finding.** The 250 / 600 mm² bounds originated in the synthetic fixture
regime (clean fixtures 140–250 mm², "noisy" fixtures 480–540 mm²). The
synthetic suite was built to establish software behaviour (determinism,
missingness, borderline logic, adversarial handling); it was never a
calibration dataset, and the bounds were never validated for this dataset's
single-leg force-plate acquisition, CoP computation, or ellipse definition.
A 95 % CoP confidence ellipse is a legitimate measurement. That does not make
600 mm² a Morse gait category boundary; those are separate propositions. The
bounds are therefore not entitled to act as clinical-category gates. This is
construct insufficiency again, one layer below D1: the pilot showed the wrong
temporal construct for the threshold; the full corpus shows a real
biomechanical quantity given an unsupported role in the interpretation.

**Decision (v2.1).**

1. `NC_CRITERION_EMU_MAP_v2.1.json` is v2 with one semantic change: the gait
   rule carries `sway_gating: false`. Sway takes no part in label
   determination. The label depends on the censored duration construct only.
2. No replacement sway thresholds are introduced. The 250 / 600 values stay in
   the rule block as historical record; the harness ignores them when
   `sway_gating` is false. Nothing was searched for in the literature to make
   these data look reasonable; an imported bound would be tuning by citation
   unless defined under a directly comparable protocol, plate configuration,
   filtering, CoP computation, ellipse definition, population, and units.
3. Sway is retained in full as evidence: `postural_stability_index` stays in
   `required_emus` (the gait criterion keeps its evidence pointer to the sway
   EMU, and an absent CoP EMU still yields non-evaluable, so the 151
   no-stable-phase attempts remain non-evaluable for gait under v2.1);
   `sway_area_mm2` is reported in the evaluation `detail`; its distribution is
   reported in the paper. What changes is what the measurement is permitted to
   decide, not whether it exists.
4. Unchanged: D1 stance construct, D2/D2a aggregation, D3 `partial`, D4
   10 s / 5 s, D4a protocol censoring. The output remains a proxy category
   under the criterion map, not a Morse gait classification; a cleaner proxy
   is still a proxy.
5. The frozen harness could not express "sway reported but not gating", so
   the rule interpreter gains one additive flag (`rule.sway_gating`, default
   true). With the flag absent, output is byte-identical to before: the v1 and
   v2 synthetic golden files pass unchanged. This changes `HARNESS_VERSION`.
   To keep the claim "the maps differ only in map bytes" exact, v1, v2, and
   v2.1 are all executed on the full corpus under the new `HARNESS_VERSION`.
   The Step 1 run under `193dba29…` (A11, commit `044335b2`) remains in the
   store as its own execution context and its artifact is kept as
   `artifacts/olst_full_corpus_v1__harness_193dba29.json`; the v1 rerun under
   the new harness must reproduce its `output_hash` for every fixture
   (harness change inert for v1), and a test asserts this.

**Reading of the expected sequence, before execution.** v1 → pilot exposes
the duration construct → v2 prospectively corrects duration and adds protocol
censoring → full-corpus v1 exposes an independent sway-authority error → v2.1
prospectively removes unsupported sway gating → v2 executed unchanged → v2.1
executed unchanged. v2 is expected to collapse toward `impaired` on the sway
gate exactly as its frozen specification implies; that is reported as the
preregistered result. Determinism reproduced a bad clinical interpretation
123,300 times without divergence; its value is that the bad interpretation
became localizable rather than disappearing inside the computation.

- `criterion_map_id` of v2.1: `b284beb3d8924a2b136b95f3801bb16a9617f5b4d4f33c205b6508fafd8e145d`
- `golden_output_hashes_v2.1.json`: `7208d81a574861c0e2c38a2abfbd919babf31667fa6e8fab13b414aea9515551`
- `HARNESS_VERSION` after the flag: `f718e4addc1c04641c5b6f1c5e591044d47c6e83a40fc1586e520f5e020a21f8`
  (`spec_id` unchanged: `9de0a3da…`)
- v2.1 freeze commit: `a722c193dcb0171005d84c7aa1d368ad322a22ab`

## A13. Step 2 executed: v1 (rerun), v2, v2.1 on the full corpus under one harness (2026-09-10)

Chain run 2026-09-10 00:00–00:23 UTC, `_run_full_corpus.py --determinism-n 100`
for `v1`, `v2`, `v2.1` in that order, Python 3.14.6, `allow_partial = false`,
`HARNESS_VERSION f718e4ad…`, `spec_id 9de0a3da…`, `AGGREGATOR_VERSION d30f3254…`.
Artifacts `artifacts/olst_full_corpus_{v1,v2,v2.1}.json`; store
`artifacts/olst_lakehouse/` now 4960 runs (28 pilot-era, 1233 Step 1 v1 under
`193dba29…`, 3 × 1233 under `f718e4ad…`) and 664 capture aggregates.

**Execution identity.** All three maps: 1233 built, 5 `source_missing_upstream`
(35_MNTRL_V4), 0 divergent fixtures at N = 100 (3 × 123,300 executions). The v1
rerun reproduced the Step 1 `output_hash` on 1233 of 1233 fixtures with
identical `fixture_id` and a different `run_id` (harness flag inert for v1,
A12.5). Across maps every fixture has equal `fixture_id`, `spec_id`,
`harness_version` and distinct `criterion_map_id` and `run_id`.

**Per-attempt gait outcome (1233 built; NE = non-evaluable, all 151 for absent CoP EMU).**

| Cohort / protocol | v1 | v2 (frozen) | v2.1 (frozen) |
|---|---|---|---|
| young MNTRL (132) | impaired 132 | impaired 109, censored 23 | censored 132 |
| young MNTRR (137) | impaired 137 | impaired 104, censored 33 | censored 137 |
| older MNTRL (256) | impaired 228, NE 28 | impaired 189, censored 39, NE 28 | censored 228, NE 28 |
| older MNTRR (251) | impaired 226, NE 25 | impaired 183, censored 43, NE 25 | censored 226, NE 25 |
| older TRLGL (250) | impaired 190, NE 60 | impaired 190, NE 60 | normal 35, weak 28, impaired 127, NE 60 |
| older TRLGR (207) | impaired 169, NE 38 | impaired 169, NE 38 | normal 38, weak 29, impaired 102, NE 38 |
| all (1233) | impaired 1082, NE 151 | impaired 944, censored 138, NE 151 | normal 73, weak 57, impaired 229, censored 723, NE 151 |

v2 behaved exactly as its frozen specification implies (A12 "reading before
execution"): the sway gate forced `impaired` on 944 attempts, all 359
evaluable TRLG attempts and 585 of the 723 evaluable MNTR attempts, and only
the 138 MNTR attempts with sway below 600 mm² reached `protocol_censored`. Under v2.1
the duration construct alone decides: every MNTR attempt (723) is
`protocol_censored` because the cued-attempt ceiling is unpublished, and the
10 s distinction is exercised only on the 359 TRLG attempts with a stable
phase, where `normal`/`weak`/`impaired` split 73 / 57 / 229.

**Capture aggregates (D2 best-of, 332 captures with at least one built
attempt; identical under v2 and v2.1 because sway never entered the aggregate).**

| Cohort / protocol | captures | aggregate outcome |
|---|---|---|
| young MNTRL / MNTRR | 43 / 45 | protocol_censored 43 / 45 |
| older MNTRL / MNTRR | 60 / 60 | protocol_censored 60 / 60 |
| older TRLGL | 62 | normal 33, weak 18, impaired 9, non-evaluable 2 |
| older TRLGR | 62 | normal 38, weak 15, impaired 9 |

Both non-evaluable aggregates are attempt-window overlaps (D2a):
`47_TRLGL_V4` (A4: final row spans the capture) and `56_TRLGL_V4`, where
`an2` lifts the foot at 12.26 s before `an1` touches down at 12.61 s and the
two rows share `t_break` = 12.29 s. The A4 check tested only whether attempt
numbers were chronological, which 56_TRLGL_V4 satisfies; the aggregate's
pairwise window check is the stronger test and found it. The D2a rule is
unchanged: any overlap withholds the aggregate and names the attempts. No
tolerance was introduced after seeing the data.

**Naive comparator agreement.** v1 962 / 1233, v2 824 / 1233, v2.1 340 / 1233.
The comparator thresholds the stable-phase window with no censoring and no
evidence requirement, so agreement falls as the governed mapping stops sharing
its errors. Governed evidence pointers 3397 per map; naive 0.

**What this run is and is not.** It is the prespecified versioning
demonstration: three maps, one harness, one spec, one fixture set, each
execution replayable from the store, the two corrections each triggered by
evidence available before the corrected map was frozen. It is not a
validation of any label. The v2.1 TRLG split is a proxy category under the
criterion map, not a Morse gait classification, and the cohort that the
Morse thresholds were drafted for (young adults) is entirely censored by the
dataset's protocol.

- Step 2 commit: `6a60385aee39429febd48b17b5a52de53c5619bb`

## A14. Source-metadata amendment: the `MNTR*` observation ceiling is published (2026-09-10)

**This is not a clinical-map correction.** No map, threshold, rule, or
harness byte changes. It is an improvement in the evidence context: an
acquisition fact that A3 recorded as unpublished (`observation_ceiling_ms =
null` for `MNTR*`, "README does not state the cued attempt duration") has a
published source.

**Source.** Copeland D, Zhang X, Linton E, Mori B, Namburi P, Anthony BW.
Non-contact radar assessment of One-Legged Stand Test for fall risk in aging.
*Gait & Posture* 2026;126:110108. doi 10.1016/j.gaitpost.2026.110108, PMID
41687572. Abstract: "synchronized radar, force plate, and motion capture data
were collected during short (4 s) and long (20 s) OLST trials." Surfaced by
the literature checkpoint in `paper/literature_review/` (2026-09-09), which
recommended it be recorded in the next dated amendment rather than by a
silent loader edit; the phrase was re-confirmed against the logged abstract
before this amendment was written. The dataset README still does not state
the cue; the companion data descriptor (Copeland et al., *Sci Data* 2026,
PMID 41741492) is the dataset's required citation.

**Decision.** Spec v1.4: `MNTR*` carries `observation_ceiling_ms = 4000`
with the source above; `TRLG*` unchanged at 20000 (README, corroborated by the
same paper's "long (20 s)"). The loader table is updated accordingly. The
v1.3 fixtures (`fixtures/real_full/`) and every v1.3 run (A11, A13) are
preserved in the store and in the repository as their own execution context.
The v1.4 fixtures are built into `fixtures/real_full_spec1.4/`; artifacts are
suffixed `__spec1.4` so nothing is overwritten.

**Expected outcome, stated before execution.** 4000 ms is below both
duration thresholds (5000, 10000), so under D4a every duration threshold is
unobservable for `MNTR*` and the outcome is `protocol_censored`, exactly as
under the null ceiling. The A3 semantics list covered null, ≥ 10 s, and
5–10 s; the sub-5 s case follows from the same rule ("categories are emitted
only where the protocol permitted the threshold to be observed") and the
harness already implements it; a test now pins it. Under v2 the sway gate
still overrides censoring on `MNTR*`; under v2.1 nothing does. `TRLG*`
fixtures are byte-identical between v1.3 and v1.4 (their acquisition block
did not change), so their `fixture_id`s and `output_hash`es must be identical
across the two contexts while their `run_id`s differ through `spec_id`.
`MNTR*` fixtures get new `fixture_id`s; their labels must be unchanged under
every map. This is the replay example: same observed measurements, better
acquisition metadata → new evidence identity, same decision outcome.

Observed maxima exceed the nominal cue under both protocols (`MNTR*` 6.34 s
against 4 s; `TRLG*` 21.31 s against 20 s). The ceiling is the instructed
duration, the longest the protocol asked for, and D4a treats it as such; it
is not a hard cap on the recorded interval.

- `spec_id` v1.4: `4e26b6948fb46b9feb952586ebc7525ccbe060a4a596c06954ba34053ead4789`
  (`HARNESS_VERSION` unchanged `f718e4ad…`; map ids unchanged)
- v1.4 freeze commit: `aab36f0ffd2c7920ce67434a6b148d5f94585751`
- Execution (v1, v2, v2.1 under spec v1.4, same `HARNESS_VERSION f718e4ad…`):
  2026-09-10 00:46–01:17 UTC, artifacts `olst_full_corpus_{v1,v2,v2.1}__spec1.4.json`,
  fixtures `fixtures/real_full_spec1.4/` (1233). Every prediction above held
  exactly, under each of the three maps: 1233 built, 0 divergent at N = 100;
  labels identical to the v1.3 run for 1233 / 1233 attempts; the 457 `TRLG*`
  fixtures byte-identical (`fixture_id` and `output_hash` equal) and the 776
  `MNTR*` fixtures re-identified with `observation_ceiling_ms = 4000`; every
  `run_id` different through `spec_id`; `criterion_map_id` and
  `harness_version` unchanged. Capture aggregates identical (208 `MNTR*`
  captures `protocol_censored`, `TRLG*` 71 / 33 / 18, 2 withheld). Store:
  8659 runs, 1328 aggregates. Same measurements, better acquisition metadata,
  new evidence identity, same decision, asserted by
  `test_a14_better_acquisition_metadata_changes_identity_not_decision`.
- Execution commit: `049fd548be1c8b190afc8b87cff01fc5af81e4ae`

**Process note (2026-09-10).** While the spec v1.4 chain was executing, the
harness file on disk was edited for the Berg work (A15). Each map runs in a
fresh interpreter and computes `HARNESS_VERSION` at import, so the in-flight
v1 run was unaffected (its artifact records `f718e4ad…`), but v2 and v2.1
would have imported the edited file. The chain was stopped before v2
started, the committed harness bytes were restored and re-hashed, and v2 and
v2.1 were re-queued behind a guard that refuses to start unless the v1
artifact's `harness_version` equals the on-disk digest. The Berg edits were
parked outside the repository until the v1.4 runs completed. No run was
ingested under a mixed harness. Rule adopted: the harness is not edited while
any corpus run is in flight.

## A15. Second framework: Berg Balance Scale (Step 3) — attempted; "no harness change" withdrawn

**Rubric verification.** Item text taken from the Academy of Neurologic
Physical Therapy *Core Measure: Berg Balance Scale (BBS)* document, reprinted
with permission from the author Katherine Berg from *J Neurol Phys Ther*
2018;42(2):174-220, read on 2026-09-10. Item 14, *Standing on one leg*.
Instructions: "Stand on one leg as long as you can without holding on with
your hands. Do not let your lifted leg touch your standing leg." Scoring:
4 "able to lift leg independently and hold >10 seconds"; 3 "… hold 5-10
seconds"; 2 "… hold ≥3 seconds"; 1 "tries to lift leg unable to hold
3 seconds but remains standing independently"; 0 "unable to try or needs
assist to prevent fall". Items 2 (stand unsupported 2 minutes), 6 (eyes
closed 10 seconds), 7 (feet together 1 minute), 13 (tandem 30 seconds) were
read from the same document. Two other public copies were unreachable
(HTTP 403); one source suffices because the text is reprinted from the
author. The manuscript's draft rubric in Section 3.7 was correct except that
level 4 is strictly *greater than* 10 s.

**Inspection before writing a line.** The frozen harness's only rule type
(`duration_sway_thresholds`) emits three fixed labels, `normal` / `weak` /
`impaired`, at two duration boundaries. Berg item 14 needs a strict > 10 s
boundary, a 3 s boundary, five ordinal levels, and a 1-versus-0 anchor. It
cannot be expressed with zero harness lines without dropping the 3 s
boundary and reporting Berg scores in Morse vocabulary, which is the silent
framework-narrowing the paper argues against. Therefore the plan's success
condition for Contribution 5 ("`git diff --stat` shows only the new map JSON,
golden hashes, fixture expectations, and tests; `harness_version` identical")
**cannot be met**, and the claim in that form is withdrawn as the plan
promised. The attempt is reported instead.

**What the harness had to gain.** One generic rule type,
`ordinal_duration_thresholds`: the map supplies the level labels and lower
boundaries and a floor label; the harness places the duration and applies
the same censoring principle as A3 (a level is emitted only if every boundary
needed to place the duration in it was observable). `git diff --stat`: +86 / −7
lines in `olst_replay_harness.py` (one function, a two-branch dispatch on
`rule.type`, and docstrings), `HARNESS_VERSION f718e4ad… → 98dc66fb…`; no
change to EMU derivation, canonicalization, hashing, the spec, the loader,
the store, or the fixture set. The finding to report is that the rule
vocabulary, not the evidence machinery, was framework-specific: the first
rule type had Morse's three category names baked in.

**Berg map (`NC_CRITERION_EMU_MAP_berg_v1.json`, `mapping_spec_version =
berg_v1`).** 14 items: 9 non-evaluable (transfers, reaching, turning,
stepping: not elicited by the OLST protocol), 4 partial (items 2, 6, 7, 13:
different stance condition, reason names the condition), 1 derivable (item
14). Item 14 requires `gait_temporal_control` only: the rubric is a duration
rubric and CoP sway is not part of it, so the 151 attempts with no stable
phase are scorable under Berg while remaining non-evaluable for Morse gait,
whose map requires the sway EMU as evidence. Levels: `score_4` ≥ 10001 ms
(strictly > 10 s in integer milliseconds), `score_3` ≥ 5000, `score_2`
≥ 3000, floor `score_1_or_0_unresolved` (every attempt has a foot-lift, so
"unable to try" does not apply, but assistance and loss of balance are not
annotated, so 1 and 0 cannot be separated and the map refuses to choose).
Protocol censoring on. No aggregation block: Berg is scored per attempt.

**Expected outcome, stated before execution (spec v1.4 fixtures).** Under
the 4000 ms `MNTR*` ceiling the 3000 ms boundary is observable and the 5000
and 10001 ms boundaries are not: `MNTR*` attempts below 3 s score at the
floor, those at or above 3 s are `protocol_censored` (could be 2, 3, or 4).
Under the 20000 ms `TRLG*` ceiling every level is observable. The same
measurement is `partial` for Morse gait and `derivable` for Berg item 14, and
the upper Berg categories are still unreachable under the short-trial
protocol: the taxonomy (modality, framework, protocol) is exercised on one
EMU.

- Berg map `criterion_map_id`: `b9d2cfbc52b8f93d7ab1603e8efb658eb83052cfd4d4026600c4c988ce18096e`
- `HARNESS_VERSION` with the ordinal rule type: `98dc66fbec2b155617e0283f8ef3192385b70c8511c46da03b508cf8a0fe4c15`
  (the 19 synthetic v1 / v2 / v2.1 golden files pass unchanged under it)
- `golden_output_hashes_berg_v1.json`: `bb18d7812a7291f86738d62af2e0b083493b461c4ce5a1d9b000d6d0a50b9a2f`
- Berg runs use the spec v1.4 fixtures (`fixtures/real_full_spec1.4/`), so
  they share `fixture_id` and `spec_id` with the A14 runs and differ from
  them in `criterion_map_id` and `harness_version`. The Morse maps are not
  rerun under the Berg harness: the harness difference is the reported fact.
- Berg freeze commit: `8727fd5ed02a3e3a8ae886a193723932e54ac7ab`
- Execution: 2026-09-10 01:57–02:09 UTC (and an idempotent rerun to
  complete the artifact's summary columns after the driver was generalized
  from `gait_type` to the map's rule-bearing criterion; the store gained no
  rows). Artifact `olst_full_corpus_berg_v1__spec1.4.json`; 1233 built, 0
  divergent at N = 100; `fixture_id` and `spec_id` identical to the A14 v2.1
  run on all 1233 attempts. Store: 9892 runs.

  **Berg item 14 per attempt** (every built attempt scored or censored; the
  9 non-evaluable items are the same on every run):

  | Cohort / protocol | score_4 | score_3 | score_2 | 1-or-0 unresolved | protocol_censored |
  |---|---|---|---|---|---|
  | young MNTRL / MNTRR (269) | 0 | 0 | 0 | 27 / 19 | 105 / 118 |
  | older MNTRL / MNTRR (507) | 0 | 0 | 0 | 167 / 150 | 89 / 101 |
  | older TRLGL (250) | 35 | 28 | 32 | 155 | 0 |
  | older TRLGR (207) | 38 | 30 | 27 | 112 | 0 |
  | all (1233) | 73 | 58 | 59 | 630 | 413 |

  Under the 4 s `MNTR*` cue the 3 s boundary is observable: 313 `MNTR*`
  attempts that fell short of 3 s are placed at the floor, and the 413 that
  reached 3 s are `protocol_censored` because 2, 3 and 4 cannot be told apart.
  No upper Berg category is reachable under the short-trial protocol. Under
  `TRLG*` all levels are observable.

  **Same attempts, two frameworks.** On the 457 `TRLG*` attempts, Morse gait
  v2.1 and Berg 14 agree level for level where both are labelled (73 normal =
  score_4; 57 weak = score_3; the 229 Morse `impaired` split into 58
  score_2 and 171 floor), because both read the same
  `stance_duration_ms` and the maps' boundaries coincide except that Berg
  adds 3 s and requires strictly > 10 s (no attempt sits at exactly
  10000 ms). The difference is standing, not arithmetic: Morse gait is
  `partial` and requires the sway EMU as linked evidence; Berg 14 is
  `derivable` and requires only the stance interval. Hence the 151 attempts
  with no stable phase are non-evaluable for Morse gait on every map and
  scored for Berg 14 (149 floor, 1 score_2, 1 score_3). The measurement did
  not change between frameworks; what it is entitled to establish did.

  **Contribution 5 as stated is withdrawn.** The second framework needed a
  harness change (+86 / −7, one generic rule type). What survives is the
  narrower claim: the spec, loader, canonicalization, EMU derivation, store,
  and fixture set were untouched, and the change was to the rule vocabulary,
  which had Morse's three category names baked in. That is reported, not
  claimed as zero change.
- Execution commit: `23c42011d33696c131ed4e80dce7518dbe5942ce`

## A16. Clerical erratum to A15 (2026-09-10) — no execution change

The A15 prose under the Berg item 14 table states "313 `MNTR*` attempts that
fell short of 3 s are placed at the floor". This is a transcription error.
The A15 table and the executed artifact
(`artifacts/olst_full_corpus_berg_v1__spec1.4.json`) give **363**
(young MNTRL 27 + MNTRR 19 = 46; older MNTRL 167 + MNTRR 150 = 317), and
363 + 413 censored = 776 `MNTR*` attempts. The A15 prose is left as written
and corrected here. No code, fixture, execution, map, label, hash, or
analysis changes. Manuscript v3 states 363.
