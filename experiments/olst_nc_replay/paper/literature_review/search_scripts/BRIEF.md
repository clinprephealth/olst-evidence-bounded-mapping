# Screening brief — OLST/NC decision-compatibility literature checkpoint (2026-09-09)

## The paper being positioned (do not search for it; it is unpublished)
A methods paper in clinical informatics. A deterministic, content-addressed pipeline maps a public multimodal
biomechanical dataset (PhysioNet One-Legged Stand Test: motion capture + force plates + radar, 32 healthy adults)
onto individual criteria of clinical assessment frameworks (Morse Fall Scale; Berg Balance Scale) under a
*versioned criterion map*. Its claimed contribution is NOT "we automated a balance scale", NOT "we added provenance",
NOT "we built a reproducible pipeline". Those spaces are occupied. The claimed contribution is a
**compatibility layer between evidence and clinical criteria**:

1. **Criterion-level evidence admissibility declared ahead of time** — for each criterion of the scale the map declares the
   required evidence units, a derivability class (`derivable` / `partial` / `non_evaluable`), the reason a criterion cannot be
   evaluated, and (at run time) pointers to the evidence that supported each emitted label.
2. **Structural non-evaluability is distinguished from ordinary missing data / model uncertainty.** A Morse "history of
   falling" item is not missing because a sensor failed; the modality cannot observe it at all. No imputation, larger model,
   or confidence calibration changes that.
3. **The acquisition protocol is part of admissibility** ("protocol censoring"): the same stance-duration variable, in the same
   participant, is compatible with a >=10 s clinical threshold under a 20-second trial protocol and logically unobservable under a
   short cued-attempt protocol; the system withholds the label (not the number) and names the ceiling.
4. **Measurement, clinical interpretation, and implementation carry separate content-addressed identities**, so a change
   in the clinical mapping (v1 -> v2) yields a new replayable result while the historical result stays reproducible, and the
   identity decomposition attributes the divergence to the criterion map.

Taxonomy the paper proposes: *modality insufficiency* (measurement system cannot observe the information),
*construct insufficiency* (observes something related but not what the criterion asks — single-leg balance vs Morse observed gait),
*protocol insufficiency* (construct measured, but the acquisition procedure prevents the criterion boundary from being observed).

## What you are screening for
Rate every candidate record in your file. Ratings:
- 3 = potential near-duplicate or direct precedent for ANY of items 1–4 or the taxonomy (e.g. a system that classifies which
  criteria/items of a clinical instrument or rule set CAN be evaluated from available data and emits that as an output; an
  explicit "not applicable / structurally unobservable vs unknown" distinction operationalized in software; acquisition-protocol
  ceilings treated as censoring of a clinical threshold; versioned clinical-rule/mapping replay with attribution of divergence).
- 2 = a neighbour the Related Work must cite (it occupies an adjacent space, or is the canonical reference for a concept the paper uses as a foil).
- 1 = background only (relevant topic, not needed in the paper).
- 0 = irrelevant / off-topic noise from the query.

## Rules
- Use ONLY records in your file. Never add a paper from memory into the shortlist. If you believe a canonical paper is missing,
  list it separately under "possibly missing (unverified)" with your best recollection and mark it unverified.
- You may use WebFetch/WebSearch sparingly (rate limits are tight: at most ~10 fetches) to read the full abstract/paper of records
  you rate 3, to confirm what they actually do. Do not fetch for ratings ≤2.
- Quote nothing longer than a sentence. Do not fabricate DOIs.
- Be sceptical: a title containing "provenance" or "abstain" is not by itself a precedent. Ask: does this work decide, per criterion,
  whether the available evidence is *capable* of supporting the criterion — before/independent of any prediction?

## Output (write both files; keep them machine-readable)
1. `screen_<AXIS>.json`: a JSON list of {"key", "rating", "why" (≤30 words), "role" (one of: precedent, foil, neighbour, canonical-ref, background, noise)}
   for EVERY record in the input (ratings 0 may be batched with why="noise").
2. `synthesis_<AXIS>.md` (≤600 words per axis): (a) what this literature does and does not do relative to items 1–4;
   (b) the 5–12 records to cite, each with key, first author, year, venue, and one sentence on how it is used in the paper (precedent/foil/neighbour);
   (c) an explicit verdict: does anything in this axis threaten the novelty of items 1–4 or the taxonomy? Name the record if so.
   (d) "possibly missing (unverified)" list.
