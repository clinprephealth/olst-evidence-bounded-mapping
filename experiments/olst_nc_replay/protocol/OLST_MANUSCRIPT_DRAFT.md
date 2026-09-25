# Knowing What Cannot Be Scored: Replay-Stable, Evidence-Bounded Clinical Assessment from Multimodal Biomechanical Data

**Author:** Michael Ryder, DO
**Status:** Working draft, pre-protocol freeze. Not for circulation; professional review precedes any submission or public sharing. ("v1" and "v2" in this document always refer to criterion-map versions inside the experimental record, never to versions of this manuscript.)

**Drafting convention.** Only results that have actually been executed are written in the past tense. Work that the pre-submission protocol has not yet run is written as protocol, in the present or future tense, inside `⟨PROTOCOL: …⟩` blocks, and is rewritten as a result only after the artifact exists. `[[FILL: …]]` marks a number to be produced; `[[DECIDE: …]]` marks a clinical-mapping decision the author must make before the number can be produced. Executed as of this draft: the 19-fixture synthetic suite, the 10-capture real-data pilot, and the traceability and store measurements over both. Not yet executed: the full-corpus run, criterion map v2, and the Berg map. Criterion map v1 is the prespecified initial mapping used in the executed pilot; v2 is a prospectively specified correction defined after the pilot exposed a mismatch. Both are retained byte-identical in the experimental record so the versioning claims are checkable. Neither has been published or circulated; the v1 to v2 transition is reported because it is scientifically informative, not as a correction to prior public work.
**Artifact:** `experiments/olst_nc_replay/` at tag `[[FILL: release tag / SHA / Zenodo DOI]]`

> Working-title alternatives: *When the Evidence Is Not Enough: Replay-Stable Clinical Assessment from Multimodal Data* · *Replay-Stable, Evidence-Bounded Mapping of Multimodal Biomechanical Data to Clinical Assessment Criteria*

---

## Abstract

Clinical assessment frameworks routinely ask for information that no single measurement modality can supply. The Morse Fall Scale combines one item that biomechanics can inform (gait) with items that live in the medical record, in patient self-report, or in a cognitive examination. A computational pipeline that scores such a framework from sensor data alone must either impute what it cannot measure, silently narrow the framework, or state explicitly which criteria it cannot justify. We present a deterministic, content-addressed pipeline that takes the third path and makes evidence insufficiency a first-class output. The pipeline maps synchronized motion-capture, force-plate, and FMCW-radar recordings from the public PhysioNet One-Legged Stand Test (OLST) dataset into criterion-level evaluations of a clinical framework under a versioned criterion map. Every run is identified by a composite SHA-256 over the input fixture, the canonicalization specification, the criterion map, and the executing harness; every output is hashed independently; every evaluated criterion carries pointers to the evidence units it was derived from; every non-evaluable criterion carries an explicit reason. A local content-addressed store supports `recall` without re-execution and `verify_replay`, which re-executes a stored fixture and asserts bit-for-bit output equality. On a 19-fixture synthetic suite, 19,000 executions produced zero output-hash divergence, with 100% evidence-pointer coverage on evaluated criteria and 100% reason coverage on non-evaluable criteria. Against a naive threshold heuristic, the pipeline agrees on clean inputs and diverges exactly where evidence is missing: the heuristic returns a confident label from absent measurements, the pipeline refuses the criterion and names the missing evidence. A 10-capture real-data pilot surfaced a construct mismatch between the dataset's per-attempt stability windows and the sustained-stance convention against which the first criterion map (v1) was drafted: every real attempt fell in the lowest bracket, and the pipeline's lineage established that the implementation was correct and the clinical mapping was not. ⟨PROTOCOL: The pre-submission protocol extends evaluation to the complete 32-participant OLST corpus, preserves v1 unchanged, defines a revised mapping (v2) that corrects the construct without altering thresholds, and reports both, testing the property the architecture exists to provide: the same source evidence under a revised clinical interpretation yields a new, distinct, replayable result while the historical result remains reproducible. If the protocol's second-framework step holds, a Berg Balance Scale criterion map will have been added with no change to the harness, specification, or store.⟩ The contribution is a methods artifact, not a fall-risk instrument. Nothing here claims predictive validity.

---

## 1. Introduction

### 1.1 The problem

A clinical assessment framework is a contract between a clinician and a body of evidence. The Morse Fall Scale [Morse 1989] has six items: history of falling, secondary diagnosis, ambulatory aids, intravenous therapy, gait, and mental status. Three are record fields. One requires a cognitive assessment. One is inferred from observed ambulation. Only gait bears any relationship to what a force plate or a motion-capture rig measures, and even that relationship is a proxy.

When a computational system is asked to produce a framework score from a modality that cannot supply most of the framework's inputs, it has three options:

1. **Impute.** Fill the missing items with defaults or population priors and emit a complete-looking score. The output is clinically shaped and evidentially hollow.
2. **Narrow silently.** Score the derivable subset and emit it under the framework's name. Without a declared coverage schema, a downstream consumer cannot tell a partial score from a complete one.
3. **Refuse explicitly.** Evaluate what the evidence supports, mark every other criterion non-evaluable with a stated reason, and make the coverage machine-readable.

This paper builds and evaluates the third option and argues that it is the only one compatible with reproducible clinical computation. The argument is not that explicit refusal is more polite. It is that a system which cannot say what it did not know cannot be replayed, audited, or recalibrated when the clinical interpretation changes.

### 1.2 What the pipeline produces

Over the PhysioNet OLST dataset [DOI 10.13026/46hn-6b25], a 32-participant corpus with synchronized motion capture (100 Hz), bilateral force plates (1200 Hz), and 24 GHz FMCW radar (~27.6 Hz), labeled per attempt with foot-lift, start-of-stability, end-of-stability, and foot-touchdown events, the pipeline produces for each attempt:

1. A **canonical JSON** representation of the attempt's observed quantities, byte-stable across executions and environments (invariant O-CI-0).
2. Up to four **Evidence Modality Units** (EMUs): `gait_temporal_control`, `postural_stability_index`, `weight_distribution_asymmetry`, `balance_control_quality`. Each carries `non_authoritative=true`, `requires_human_ack=true`, attempt-level provenance, and a payload hash. An EMU whose required source is absent is omitted, never imputed.
3. A **criterion-by-criterion evaluation** of the target framework under a versioned criterion map. Evaluated criteria carry labels and evidence pointers to the EMUs that informed them. Non-evaluable criteria carry an explicit `non_evaluable_reason`.
4. A composite **`run_id`** over the full execution context and an **`output_hash`** over the result, which together bind every input byte to every decision artifact.

### 1.3 Contributions

1. **An evidence-bounded mapping architecture** in which criterion coverage is a declared, machine-readable output and non-evaluable criteria carry reasons rather than defaults (Sections 3.4–3.6).
2. **Content-addressed replay with source lineage** from the published dataset's per-file digests through the canonicalization specification, criterion map, and harness source to the output (Sections 3.7–3.8), with replay verified rather than assumed (Section 4.1).
3. **An empirical demonstration** that the architecture and a naive heuristic behave identically on clean data and differently when evidence is insufficient (Section 4.2), on a synthetic suite and on real OLST data (Section 4.3; ⟨PROTOCOL: complete corpus⟩).
4. **A worked case of versioned clinical recalibration.** The first criterion map (v1) was drafted against the sustained-stance clinical convention; the real-data pilot showed that the dataset's event windows encode a different construct (Section 4.3). ⟨PROTOCOL: We report v1 unchanged, define v2, and test whether both remain distinctly identified and independently replayable from the same source evidence (Section 4.4).⟩
5. ⟨PROTOCOL, conditional: **Framework extension without harness change.** A Berg Balance Scale criterion map is added as one JSON file. The claim survives only if the harness, specification, and store are byte-identical before and after, and the run_id decomposition shows that only the criterion-map digest moved (Section 4.5). If the claim does not survive, this contribution is withdrawn and the attempt is reported in Section 6.⟩

### 1.4 What this paper does not claim

The pipeline does not predict falls. The gait threshold is not clinically validated. The partial Morse evaluation is not intended for clinical use. Deterministic output is not clinically correct output; determinism is what makes correctness *checkable*. Section 6 states these boundaries in full.

---

## 2. Related Work

**Provenance and reproducible pipelines.** PROV-O [W3C 2013] gives a vocabulary for artifact origins without a runtime that enforces deterministic transformation. Content-addressed storage (Git, IPFS [Benet 2014]) gives byte-stable identity for files, not for the computational outputs derived from them. Workflow managers such as Snakemake [Mölder et al. 2021] and Nextflow [Di Tommaso et al. 2017] rerun pipelines from tracked inputs, but their guarantees stop at the artifact. They do not separate *what was measured* from *what was inferred about a clinical framework from the measurement*, which is the boundary this paper preserves at the level of individual criteria.

**Missing data in clinical computation.** The dominant treatment of missingness in clinical machine learning is imputation, with the choice of imputation method treated as a modeling decision [`[[FILL: 2–3 citations, e.g. reviews of imputation in EHR ML]]`]. Work on abstention and selective prediction lets a model decline to answer when uncertain [`[[FILL: selective prediction / reject option citations]]`]. Our setting is different from both: the missing inputs are not uncertain, they are *structurally absent from the modality*, and the correct behavior is not a confidence-thresholded abstention but a declared, reasoned non-evaluation at the granularity of the framework's own criteria.

**Balance assessment and the OLST.** Single-leg stance time has published age-stratified norms [Springer et al. 2007; Bohannon 2006] and appears as an item in composite instruments including the Berg Balance Scale [Berg et al. 1989, 1992]. Force-plate sway analysis has an established measure set [Prieto et al. 1996; Quijoux et al. 2020]. The PhysioNet OLST dataset [`[[FILL: dataset citation and authors]]`] is, to our knowledge, the first public corpus with synchronized motion capture, bilateral force plates, and radar and with per-attempt event labels. Prior work uses such corpora to derive features and report associations with outcomes. We use the corpus as a substrate for testing replay, traceability, and evidence-bounded mapping, and defer outcome claims entirely.

**Gap.** No prior system we are aware of combines modality-specific deterministic transformation, criterion-level non-evaluable markers with stated reasons, and content-addressed replay verification with lineage to a published dataset's file digests. The contribution is the integrated, testable artifact.

---

## 3. Methods

### 3.1 Dataset

The PhysioNet OLST dataset (release 1.0, January 2026) contains 32 healthy participants, 15 young (≤32 y) and 17 older (≥64 y), performing the One-Legged Stand Test on either foot for three to ten attempts per capture, across multiple captures per participant. Each capture provides a motion-capture CSV (100 Hz), two force-plate CSVs (1200 Hz, one per plate: `Force_X/Y/Z`, `Moment_X/Y/Z`, `COP_X/Y/Z`, `COP_speed`), and a processed range-Doppler-map file from the 24 GHz radar (per-capture `Seconds_per_Frame` recorded in `OLST_Attempts.csv`). `OLST_Attempts.csv` is the system of record for attempt timing: `t_foot_up`, `t_stable`, `t_break`, and `t_end` in MoCap-clock seconds. The published `SHA256SUMS.txt` lists per-file digests, which we treat as the root of source lineage.

Two dataset properties constrain canonicalization: radar timestamps must use per-row `Seconds_per_Frame` rather than the nominal rate (a nominal-rate implementation produces a different canonical hash, so the error is detectable), and the 20-second capture protocol appears only in the older cohort, so fixtures and reports are stratified by cohort. The dataset's usage notes record one excluded capture, `12_MNTRL_V2`, which the pipeline refuses at ingest with a typed `ExcludedCaptureError` before any EMU derivation.

`[[FILL: full-corpus inventory — captures per participant, total captures, total attempts, cohort split, after the one exclusion.]]`

### 3.2 Canonicalization invariant (O-CI-0)

The canonicalization specification (`OLST_CANONICALIZATION_SPEC_v1.md` §6) fixes lexicographic key order, six-decimal float representation with `NaN`/`Inf` rejected in favor of `null` plus a `<field>__missing_reason` string, trial-internal time in milliseconds from `MOCAP_Start_Time`, force in newtons with the source unit recorded, and stability-phase boundaries from `t_stable` to `t_break` (or `t_end` on the final attempt). Invariant **O-CI-0**, that identical parsed input under identical rules yields byte-identical canonical JSON across executions and environments, is implemented as a single serialization call with sorted keys, compact separators, UTF-8, and pre-rounded floats.

### 3.3 Evidence Modality Units

| EMU type | Payload fields | Required source |
|---|---|---|
| `gait_temporal_control` | `stability_duration_ms`, `stance_duration_ms` `[[FILL: confirm field set after v2]]`, `trial_leg` | MoCap event labels |
| `postural_stability_index` | `mean_cop_displacement_mm`, `sway_area_mm2`, `stance_duration_ms` | Force-plate CoP over the stability window |
| `weight_distribution_asymmetry` | `left_pct`, `right_pct`, `asymmetry_index` | Bilateral `Force_Z` over the stability window |
| `balance_control_quality` | `composite_score` | Derived from the previous two (rule v1) |

Provenance on each EMU carries `attempt_number`, `total_attempts_in_session`, `source_trial_id`, and the applicable rule version. `mean_cop_displacement_mm` is the mean radial displacement from the per-attempt CoP centroid, not from the plate origin, because the plate offset varies with participant and footwear. `sway_area_mm2` is the 95% confidence ellipse, $A = \pi \cdot 5.991 \cdot \sqrt{\sigma_x^2 \sigma_y^2 - \mathrm{cov}(x,y)^2}$, pinned as rule v1. **No imputation:** an EMU whose required source is absent is omitted, and any criterion that requires it becomes non-evaluable downstream. This is the primitive that makes evidence gaps observable.

### 3.4 Criterion maps: general form

A criterion map is a versioned JSON document that, for each item of a target framework, declares the required EMUs, a derivability class (`derivable`, `partial`, `non-evaluable`), the thresholds or rules that turn EMU payloads into a label, and, for non-evaluable items, the reason. Maps are JSON rather than YAML so the harness depends on the Python standard library only. The map's SHA-256 (`criterion_map_id`) enters the `run_id` (Section 3.8), so a map revision is a new execution context by construction.

### 3.5 Morse Fall Scale, criterion map v1 (prespecified initial mapping)

| Criterion | Required EMUs | Derivability | Reason if non-evaluable |
|---|---|---|---|
| History of falling | none | non-evaluable | Self-report or medical record required |
| Secondary diagnosis | none | non-evaluable | Clinical record required |
| Ambulatory aids | `gait_temporal_control` | partial | Gait pattern is a proxy, not definitive |
| IV therapy | none | non-evaluable | Clinical record required |
| Gait | `gait_temporal_control`, `postural_stability_index` | derivable | — |
| Mental status | none | non-evaluable | Cognitive assessment required |

Four of six criteria are structurally non-evaluable from biomechanics. The v1 gait rule uses `stability_duration_ms` from the `t_stable → t_break` window with thresholds `normal ≥ 10000 ms`, `weak ≥ 5000 ms`, else `impaired`, plus sway-area bounds (`normal ≤ 250 mm²`, `impaired ≥ 600 mm²`). These thresholds were drafted against the clinical convention of a sustained one-legged stance with a 10-second cutoff. Section 4.3 reports what happened when they met the real data.

### 3.6 Morse Fall Scale, criterion map v2 (prospectively specified correction)

⟨PROTOCOL: this section defines a map that has not yet been run.⟩ Map v1 was the initial mapping specified before any real data were processed. Map v2 is specified here, after the pilot of Section 4.3 exposed the mismatch and before the full-corpus runs, and this specification is frozen before any v2 output is inspected. The v1 map is preserved unchanged. v2 revises the clinical interpretation only; the harness, specification, EMU derivation, and store are untouched. `[[DECIDE: the following is the proposed v2 definition; confirm or replace each element before running, and freeze D2–D4 before inspecting any v2 label distribution.]]`

**Duration construct.** v1 evaluated the `t_stable → t_break` sub-window, which the dataset labels as the *stable phase within an attempt*. The sustained-stance construct that clinical cutoffs refer to is the interval during which the participant remains on one leg, which we hypothesize corresponds to `t_foot_up → t_end` (foot touchdown). This is a hypothesis, not a finding: the pilot windows of 70 ms to 3.9 s are implausibly short for sustained stance in healthy young adults, but plausibility is not verification. The protocol computes both `t_break − t_stable` and `t_end − t_foot_up` over the complete corpus, stratified by cohort, and checks the dataset's event definitions, before v2 is fixed. Two outcomes are possible and both are reported as results. (a) If `t_foot_up → t_end` behaves like a stance duration, v2 evaluates `stance_duration_ms` over that interval and the v1 to v2 change is a construct correction. (b) If it does not, the public dataset's protocol does not instantiate the sustained clinical construct at all, and v2 instead defines a per-attempt criterion with documented non-equivalence to that construct. `[[DECIDE after the distributions are computed.]]`

**Aggregation.** OLST is conventionally recorded as the best (longest) of several attempts. v2 introduces an explicit session-level aggregation rule, `best_of_attempts = max(stance_duration_ms)` over the attempts in a capture, evaluated only when every attempt in the capture produced a `gait_temporal_control` EMU. Aggregation is a declared rule in the map, never a silent merge, and the per-attempt evaluations remain in the output alongside the aggregate.

**Derivability class.** The Morse gait item is defined by observed ambulation (posture, step length, use of furniture for support), not by single-leg stance. v2 therefore reclassifies `gait` from `derivable` to `partial`, with the reason text stating that single-leg balance is a proxy for the ambulation descriptors the item names. `[[DECIDE: keep as recommended, or retain "derivable" with a documented justification.]]`

**Thresholds.** v2 retains the 10 s / 5 s cutoffs applied to the corrected construct, and records the age-stratified norms [Springer et al. 2007; Bohannon 2006] in the map as reference values without using them to alter labels. `[[DECIDE: confirm.]]`

v1 and v2 differ only in the criterion-map bytes. Every v2 run therefore carries a different `criterion_map_id` and `run_id` than its v1 counterpart over the same fixture, and both remain in the store and remain verifiable (Section 4.4).

### 3.7 Second framework: Berg Balance Scale criterion map ⟨PROTOCOL⟩

The Berg Balance Scale [Berg et al. 1989] has 14 items scored 0–4. Item 14, *standing on one leg*, is the one item whose construct the OLST directly instantiates, with a published duration rubric (4: >10 s; 3: 5–10 s; 2: ≥3 s; 1: attempts but holds <3 s while standing independently; 0: unable). `[[VERIFY: rubric wording and boundaries against the original scale sheet.]]` Items 2, 6, 7, and 13 (standing unsupported, eyes closed, feet together, tandem) are bipedal or differently conditioned stances and are mapped `partial` or `non-evaluable` with reasons naming the condition difference. Items 1, 3, 4, 5, 8, 9, 10, 11, and 12 involve transfers, reaching, turning, or stepping that the OLST protocol does not elicit and are `non-evaluable`.

| Class | Berg items | Count |
|---|---|---|
| derivable | 14 | 1 |
| partial | `[[DECIDE: e.g. 2, 6, 7, 13 or subset]]` | `[[FILL]]` |
| non-evaluable | remainder | `[[FILL]]` |

The Berg map is to be added as a single JSON file plus fixture expectations and golden hashes; Section 4.5 states the test the addition must pass.

The two frameworks also give a contrast that is itself part of the argument. Under v2 the Morse gait item is `partial`, because Morse gait is an ambulation observation and single-leg balance is related evidence rather than the same construct. Berg item 14 *is* single-leg stance, so the same EMU can support a `derivable` classification there. The same measurement does not acquire the same epistemic standing in two instruments merely because both contain a superficially related item; the criterion map is where that difference is declared.

### 3.8 Replay harness and identity scheme

`run(fixture_path, mapping_spec_version)` reads the fixture bytes and computes `fixture_id = SHA-256(bytes)`; parses and resolves `participant_id` and `capture_id` from required fields with no fallbacks; applies the capture-exclusion and participant-exclusion gates before any further work; validates `dataset_version` (mismatch warns, never silently passes); canonicalizes per O-CI-0; derives EMUs; applies the criterion map; and computes two digests:

- **`output_hash`**: SHA-256 over the canonical JSON of `{emu_outputs, criterion_evaluations, non_evaluable_criteria, traceability, mapping_spec_version, dataset_version}`. The traceability dictionary is inside the scope, so two runs with identical labels but different evidence pointers cannot share an output hash.
- **`run_id`**: SHA-256 over the canonical JSON of `{fixture_id, dataset_version, mapping_spec_version, spec_id, criterion_map_id, harness_version}`.

`spec_id` and `criterion_map_id` are read from disk on every call, so a specification or map edit between two runs in one process changes `run_id` without re-import. `harness_version` is digested once at import and captures the running code. For real-data fixtures, a `dataset_pointer` block pins the PhysioNet `SHA256SUMS.txt` entries for every source CSV the loader read. The pointer is part of the fixture bytes, so a dataset republish changes `fixture_id`, hence `run_id`, and, if content moved, `output_hash`.

The `run_id` decomposition is what makes Sections 4.4 and 4.5 readable: for two runs over the same fixture, the components that differ name the cause of divergence.

### 3.9 Content-addressed store

The store is five JSONL streams: `runs` (by `run_id`), `emus` (by `run_id, emu_id`), `criterion_evaluations` and `non_evaluable` (by `run_id, criterion_id`), and `fixtures` (verbatim UTF-8 fixture text by `fixture_id`). Ingest is idempotent. `recall(run_id)` rebuilds a report from the streams without execution. `verify_replay(run_id)` reads the stored fixture text, re-executes it under the current harness, and asserts output-hash equality. A divergence with matching `fixture_id` localizes to the harness, specification, or map, and the stored-versus-current digest pairs say which.

### 3.10 Baseline and evaluation protocol

The **naive baseline** applies the 10-second cutoff directly to whatever duration field is present, defaulting absent values to zero, and emits a label with no evidence pointers. It is the shape of a reasonable first implementation, not a straw man.

Metrics:

- **Determinism**: number of distinct `output_hash` values per fixture over N executions (target: 1).
- **Evidence-pointer coverage**: fraction of evaluated criterion lines with at least one pointer (target: 100%).
- **Reason coverage**: fraction of non-evaluable lines with a non-empty reason (target: 100%).
- **Baseline agreement**: label agreement on clean fixtures; behavior on missing-data fixtures.
- **Version distinctness**: for each fixture, `run_id(v1) ≠ run_id(v2)`, both `verify_replay` true, and `harness_version`, `spec_id`, `fixture_id` equal across the pair.

---

## 4. Results

Sections 4.1 (synthetic), 4.2, 4.3 (pilot), and 4.6 (current snapshot) report executed results, reproducible from commit `37e436d` of `feature/olst-nc-replay-execution`. Sections marked ⟨PROTOCOL⟩ describe what the pre-submission protocol will run; their placeholders are filled, and their tense changed, only after execution. Final numbers are to be reproducible from tag `[[FILL]]` with:

```
PYTHONPATH=. python -m pytest tests/test_olst_nc_replay.py -q
PYTHONPATH=. OLST_DETERMINISM_N=1000 python -m pytest tests/test_olst_nc_replay.py::test_replay_is_deterministic -q
PYTHONPATH=. python -m experiments.olst_nc_replay._ingest_all
PYTHONPATH=. python -m experiments.olst_nc_replay._run_gold_standard
[[FILL: v2 and Berg invocations]]
```

### 4.1 Replay determinism

Over 19 synthetic fixtures × 1000 executions (19,000 runs), exactly one `output_hash` was observed per fixture. Over the 10 pilot real-data fixtures × 200 executions, the same. The synthetic suite at N=1000 completes in 2.76 s on a development laptop, which we read as evidence that determinism is cheap rather than a theoretical bound. ⟨PROTOCOL: the complete corpus is run at N=100 per fixture under both v1 and v2; `[[FILL: N fixtures, distinct-hash count, timing]]`.⟩

### 4.2 Synthetic suite: behavior when evidence is insufficient

The 19 fixtures comprise 5 clean (3 young, 2 older), 3 noisy, 2 missing-data, 2 axis-flip, 2 unit-mismatch, 2 borderline at the 10 s cutoff, 2 adversarial (`end_ms < start_ms`; stale metadata), and 1 negative control pinned to the excluded capture. Golden `fixture_id` and `output_hash` are committed per fixture and asserted independently, so content drift and output drift are detected separately.

Traceability over the suite: 33 evaluated criterion lines, 33 with evidence pointers (100%); 75 non-evaluable lines, 75 with reasons (100%).

| | Clean fixtures | Missing-data fixtures |
|---|---|---|
| Naive heuristic | 5/5 agree with pipeline | imputes 0 ms, returns `impaired` with no evidence pointer |
| Pipeline | 5/5 | `gait` enters `non_evaluable_criteria`; reason names the absent EMU |

On `missing_fp_channel` and `missing_mocap_events`, the heuristic emits a confident label from absent inputs; the pipeline emits `"Required EMU(s) absent from derived set: ['postural_stability_index']."` Neither system detects axis flips or unit mismatches (neither claims to), but the pipeline's per-criterion pointers make the subsequent forensic path deterministic.

### 4.3 Real data under map v1: a construct mismatch, surfaced

Ten captures (five young: `01_MNTRR_V1`, `01_MNTRL_V1`, `01_MNTRR_V2`, `02_MNTRL_V1`, `02_MNTRL_V2`; five older: `30_MNTRR_V1`, `35_MNTRR_V1`, `39_MNTRR_V1`, `51_MNTRR_V1`, `56_MNTRR_V1`) were processed through the loader and the harness. Each fixture pins five PhysioNet source-file digests. `t_stable → t_break` windows ranged from 70 ms to 3.9 s. Under v1, all 10 attempts were labeled `impaired`, and the pipeline agreed with the naive heuristic on 10 of 10. The pipeline emitted 30 evidence pointers (three per attempt); the heuristic emitted zero.

⟨PROTOCOL: the complete corpus is run under v1 and the same quantities reported: `[[FILL: captures, attempts, window range and medians by cohort, label counts, agreement, pointer counts]]`, together with the distribution figure for both duration variables described in Section 3.6.⟩

The agreement is not a coincidence and not a validation. The v1 thresholds were written for a sustained stance measured in seconds; the dataset's stable-phase window in the pilot was a sub-interval measured in tens of milliseconds to a few seconds. Every attempt therefore fell in the lowest bracket under both systems. Two facts are separable here and the architecture separates them: the implementation behaved exactly as specified (replay-verified, fully traced), and the clinical mapping was miscalibrated to the event-window construct supplied to the v1 rule. Whether the dataset encodes the sustained-stance construct elsewhere, or does not instantiate it at all, is the D1 question Section 3.6 leaves open. A system that had imputed, or reported a single score without pointers, would have offered no way to tell the two apart.

### 4.4 Map v2 and versioned replay ⟨PROTOCOL⟩

Nothing in this section has been executed. The protocol runs the complete corpus under the v2 map fixed in Section 3.6 and reports: the per-attempt and best-of-attempts distributions of the v2 duration variable by cohort; the label distribution per capture (normal, weak, impaired, non-evaluable, the last for captures with an attempt lacking event labels); and the v1 and v2 label distributions side by side. `[[FILL after execution.]]`

**Execution identity of v1.** The v1 criterion map remains byte-identical throughout. If the protocol requires an additive evidence field in the harness for v2 (Section 3.3), that change is made once, before the full-corpus runs, and both full-corpus v1 and v2 are executed under the same frozen harness. The pilot v1 runs of Section 4.3 then remain separately replayable under their original execution identity, with a different `harness_version` and therefore a different `run_id`, while sharing `fixture_id`, `spec_id`, and `criterion_map_id` with their full-corpus v1 counterparts. The store holds both; the identity decomposition says why they differ. `[[FILL: state whether the harness changed, and the two harness_version digests if so.]]`

The version-distinctness test (Section 3.10) is then asserted on every fixture: `run_id(v1) ≠ run_id(v2)`; within each pair `fixture_id`, `spec_id`, and `harness_version` identical and only `criterion_map_id` different; `verify_replay` true for every v1 and every v2 run from the same store; and `recall` of a v1 run after v2 ingest reproducing the historical output hash byte-for-byte. `[[FILL: counts.]]`

If these assertions hold, they demonstrate the property the pipeline exists to provide: the clinical interpretation changed, the evidence did not, the store holds both interpretations as distinct, identified, reproducible results, and the identity decomposition names the cause of the difference. If any assertion fails, the failure is reported here as a result and its cause localized by the digest pairs.

### 4.5 Second framework ⟨PROTOCOL, conditional⟩

Nothing in this section has been executed. The success condition is stated in advance: the diff between the pre-Berg and post-Berg commits contains only the map JSON, fixture expectation rows, golden hashes, and tests, with zero lines in the harness, specification, or store; and `harness_version` and `spec_id` are identical between Morse and Berg runs over every fixture, with only `criterion_map_id` differing. If the condition holds, this section reports the diff stat, the coverage table (expected: 1 of 14 items derivable, item 14; partial and non-evaluable counts per Section 3.7), the item 14 label distribution under the Berg rubric by cohort, and evidence-pointer and reason coverage. If it does not hold, the section reports what had to change in the harness and why, and contribution 5 is withdrawn. `[[FILL after execution.]]`

### 4.6 Store properties

The committed store snapshot holds 28 runs (19 synthetic + 10 real − 1 excluded by the gate), approximately 167 KB across five streams. Second-pass ingest reports zero new rows. `verify_replay` is true on every stored run; tampering with stored fixture bytes raises rather than passing. ⟨PROTOCOL: after the full-corpus, v2, and Berg runs, `[[FILL: run count, size]]`.⟩

---

## 5. Discussion

**Explicit insufficiency is what makes recalibration safe.** The v1 episode is the paper's central result and we present it as such. A pipeline that had filled the four record-dependent items and reported one Morse total would have produced a number that looked like a clinical score and was wrong in a way no consumer could detect. The pipeline instead reported one proxy label, four reasons, and enough lineage to establish that the label was correctly computed from a miscalibrated map. The computation was reproducible; the clinical interpretation was wrong; because the two were separately identified, the interpretation can be corrected without erasing or rewriting the historical result. ⟨PROTOCOL: Section 4.4 tests whether correcting the map as a one-file change produces a new identified result without disturbing the old one.⟩ Reproducibility is not validity. Determinism guaranteed that the v1 error was reproducibly present, which is what made it findable.

**Parity on clean data is the right result.** A governed pipeline that disagreed with a straightforward heuristic on unambiguous inputs would be suspect. The value is in the divergence when inputs are missing, and in the pointers that exist in one system and not the other.

**Relationship to reproducible-pipeline tooling.** Workflow managers would reproduce the same bytes from the same inputs. They would not tell a reviewer that four of six criteria were never evaluable, or which EMU a label depended on, or that the criterion map, rather than the harness, had changed between two runs. The unit of reproducibility here is the criterion evaluation, not the file.

**Generality.** The harness knows nothing about Morse or Berg; it knows EMUs, maps, and hashes. ⟨PROTOCOL: Section 4.5 is designed to demonstrate this rather than assert it, and states in advance what would falsify it.⟩ What the harness cannot do is decide what a clinically legitimate mapping is. That remained a human decision at v1, at v2, and would at v3.

---

## 6. Limitations

1. **No outcome or validity claim.** Nothing here shows that any EMU or label predicts falls or any clinical outcome. Morse and Berg are illustrative frameworks chosen for established reliability and for being only partially derivable from biomechanics.
2. **Healthy participants, one dataset.** The corpus is 32 healthy adults in a laboratory protocol. Behavior on clinical populations, on other sensors, or on free-living data is untested.
3. **v2 is a defensible mapping, not a validated one.** The construct correction and aggregation rule are stated and versioned; they are not validated against clinician-scored OLST or Morse gait ratings. ⟨PROTOCOL: if Berg is included, the item 14 rubric is applied as published; the OLST protocol instructions differ from Berg's administration instructions, and that difference is recorded as a reason on the partial items.⟩
4. **Gaps are surfaced, not resolved.** The pipeline does not integrate a record system or self-report. Those inputs would enter as additional EMUs through the same mapping mechanism; this paper does not demonstrate that.
5. **Synthetic coverage is representative, not exhaustive.** A reviewer can construct a new adversarial fixture in seconds and observe behavior; we do not claim to have enumerated adversarial patterns.
6. **Determinism is not correctness.** Byte-identical replay guarantees that a wrong answer is reproducibly wrong. It is the precondition for finding and fixing the error, as Section 4.3 shows, not a substitute for it.

---

## 7. Conclusion

A clinical computational pipeline should be able to prove what evidence produced an answer, reproduce that answer exactly, and decline explicitly the portions of a clinical construct that the available evidence cannot support. We built a pipeline with those properties over a public multimodal biomechanical dataset, verified replay over 19,000 synthetic and 2,000 real-data executions with zero divergence, and showed that it agrees with a naive heuristic on clean inputs and refuses where the heuristic imputes. When real data exposed a construct mismatch in the first clinical mapping, the pipeline's lineage separated a correct implementation from a miscalibrated interpretation. ⟨PROTOCOL: the pre-submission protocol corrects the mapping as a versioned artifact while keeping the historical result reproducible, extends evaluation to the complete corpus, and tests whether a second framework can be added without touching the transformation or replay machinery. This paragraph is rewritten in the past tense only for the steps that were executed.⟩ The artifact, fixtures, store snapshot, and tests are public.

**Future work.** Ingesting record-derived evidence units for the non-biomechanical items; a clinical population; Timed Up and Go once a corpus with a walking protocol is available; and validation of v2 against clinician-scored stance times.

---

## Acknowledgments

This work uses the PhysioNet OLST dataset (DOI 10.13026/46hn-6b25) under PhysioNet's usage terms. `[[FILL: PhysioNet-required citation text, dataset authors.]]`

## References `[[FILL: complete for venue style]]`

- Benet J. (2014). IPFS: Content addressed, versioned, P2P file system.
- Berg K, Wood-Dauphinee S, Williams JI, Gayton D. (1989). Measuring balance in the elderly: preliminary development of an instrument. *Physiotherapy Canada* 41(6):304–311.
- Berg K, Wood-Dauphinee S, Williams JI, Maki B. (1992). Measuring balance in the elderly: validation of an instrument. *Can J Public Health* 83(Suppl 2):S7–S11.
- Bohannon RW. (2006). Single limb stance times: a descriptive meta-analysis of data from individuals at least 60 years of age. *Topics in Geriatric Rehabilitation* 22(1):70–77.
- Di Tommaso P, et al. (2017). Nextflow enables reproducible computational workflows. *Nature Biotechnology* 35(4).
- Mölder F, et al. (2021). Sustainable data analysis with Snakemake. *F1000Research* 10.
- Morse JM, Morse RM, Tylko SJ. (1989). Development of a scale to identify the fall-prone patient. *Canadian Journal on Aging* 8(4):366–377.
- Prieto TE, et al. (1996). Measures of postural steadiness: differences between healthy young and elderly adults. *IEEE Trans Biomed Eng* 43(9).
- Quijoux F, et al. (2020). A review of center of pressure (COP) variables to quantify standing balance. *Physiological Reports* 8(22).
- Springer BA, Marin R, Cyhan T, Roberts H, Gill NW. (2007). Normative values for the unipedal stance test with eyes open and closed. *J Geriatr Phys Ther* 30(1):8–15.
- W3C (2013). PROV-O: The PROV Ontology.
- PhysioNet OLST dataset, 10.13026/46hn-6b25, January 2026. `[[FILL: authors]]`
- `[[FILL: imputation-in-clinical-ML reviews; selective prediction / reject option]]`

---

## Appendix A — Artifact pointers

| Artifact | Path |
|---|---|
| Canonicalization spec | `experiments/olst_nc_replay/specs/OLST_CANONICALIZATION_SPEC_v1.md` |
| EMU schema | `experiments/olst_nc_replay/specs/olst_emu_schema_v1.yaml` |
| Morse criterion map v1 | `experiments/olst_nc_replay/specs/NC_CRITERION_EMU_MAP_v1.json` |
| Morse criterion map v2 | `experiments/olst_nc_replay/specs/NC_CRITERION_EMU_MAP_v2.json` `[[FILL]]` |
| Berg criterion map v1 | `experiments/olst_nc_replay/specs/BERG_CRITERION_EMU_MAP_v1.json` ⟨PROTOCOL⟩ |
| Replay harness | `experiments/olst_nc_replay/olst_replay_harness.py` |
| Store module | `experiments/olst_nc_replay/lakehouse.py` |
| Real-data loader | `experiments/olst_nc_replay/olst_real_loader.py` |
| Naive baseline | `experiments/olst_nc_replay/olst_naive_baseline.py` |
| Synthetic fixtures | `experiments/olst_nc_replay/fixtures/*.json` |
| Real-data fixtures | `experiments/olst_nc_replay/fixtures/real/*.json` |
| Tests | `tests/test_olst_nc_replay.py` |
| Store snapshot | `artifacts/olst_lakehouse/` |
| Traceability, baseline comparison, gold standard | `artifacts/olst_nc_*.json` |

## Appendix B — Reproducibility checklist

- [x] All transformations are pure functions of `(fixture_bytes, spec_bytes, criterion_map_bytes, harness_bytes)`.
- [x] No randomness, clock dependence, or machine-specific paths in any hashed artifact.
- [x] Source lineage is content-addressed via PhysioNet `SHA256SUMS.txt`.
- [x] Harness, specification, and criterion maps are content-addressed at run time.
- [x] `ingest → recall → verify_replay` is asserted on every committed fixture.
- [x] Determinism N is one environment variable; CI runs N=50, the paper runs N=1000.
- [x] No external services, paid APIs, or non-public data are required.
- [ ] `[[FILL: frozen release tag and archival DOI]]`
