# Synthesis A8 — direct hunt: non-evaluable criteria, unobservable items, evidence admissibility, partial scoring, versioned replay

184 records (screen_A8.json): 1×3, 10×2, 20×1, 153 noise. "Non-evaluable" hits are mostly imaging/oncology usage; "admissible evidence" hits mostly legal/EBM — noise. Duplicates/mislinked DOIs rated 1 with pointer to canonical key.

## (a) What this literature does and does not do

Three strands. (i) Non-evaluability as an output category: LI-RADS has a formal "nonevaluable" category (Kielar 2018); guideline compliance was "impossible to assess" when key algorithm variables were non-assessable (Strand 2012); automated gates label spectra/reports evaluable vs not before interpretation (Menze 2008; Kreimeyer 2021). All are technical/completeness non-evaluability, removable by better acquisition or algorithms, never separated from structural unobservability (item 2) nor declared per criterion in advance. (ii) Partial scale scoring from sensors: Corponi 2024 infers every HDRS/YMRS item from wearables with no observability declaration; Zhou 2025 scores a designated 70% FMA-UE subset from IMUs without emitting excluded items or reasons. Neither treats a protocol as censoring a threshold. (iii) Evidence-admissibility AI (2026 preprints): Garg & Esposito formalise "evidence admissibility" as document-level retrieval eligibility; Lin 2026 (MedEventGraph-RAG, full text read) applies a query-specific evidence contract before assessment and returns supported/conflicting/refuted/insufficient with source links; Shi 2026 audits LLM abstention against supplied evidence boundaries. These share item 1's admissibility-before-judgment pattern but concern documents/events, not whether a measurement can support a clinical criterion; none has a structural class or versioned replay.

The exception is EviBound (Gao, Wu, Lu; arXiv 2608.31014, posted 31 Aug 2026), verified from full text. Each instance is an evidence package (protocol profile, modality mask, claim-permission matrix Π, observations); Π "defines the evidential scope associated with each protocol–modality combination and serves as the executable specification for runtime report validation", fixed before reasoning begins. Permissions are protocol-dependent — fixed-reading text "cannot support semantic symptom inference" — and "missing modalities are explicitly registered before inference". A deterministic validator blocks modality-hallucination, protocol-misuse and claim-scope violations, records blocked reasons, and reports carry evidence attribution and missing evidence. Against items 1–4: item 1 — admissibility declared ahead of time, but per claim type (acoustic, symptom-history, diagnosis), not per clinical-instrument criterion, and no derivability class is emitted; item 2 — partial: "modality absent" vs "protocol does not license" parallels modality vs protocol insufficiency, but no construct insufficiency, no taxonomy, no per-criterion non-evaluability output with reason; item 3 — nearest precedent, but as categorical claim permissions, not censoring of a numeric threshold on a measured construct; item 4 — no: "replay" means re-validating fixed packages; no content-addressed identities or v1→v2 attribution. Domain is speech/LLM depression screening, not sensor-to-scale mapping.

## (b) Records to cite

- arxiv:2608.31014v1 — Gao 2026, arXiv — precedent (item 3; item 1 pattern); concurrent work.
- arxiv:2608.22062v1 — Lin 2026, arXiv — neighbour: evidence contract before assessment, source-linked evidence.
- 10.32388/u0utrp — Garg 2026, Qeios — foil for the term "evidence admissibility".
- 10.3389/fpubh.2026.1904062 — Shi 2026, Front Public Health — neighbour: evidence-gated LLM abstention audit.
- 10.1038/s41398-024-02876-1 — Corponi 2024, Transl Psychiatry — foil: all items from wearables, no observability declaration.
- 10.1109/jbhi.2025.3542037 — Zhou 2025, IEEE JBHI — neighbour: partial FMA-UE scoring.
- 10.1016/j.injury.2012.01.001 — Strand 2012, Scand J Trauma Resusc Emerg Med — neighbour: algorithm unassessable on non-assessable variables.
- 10.1007/s00261-017-1281-6 — Kielar 2018, Abdom Radiol — canonical-ref: formal "nonevaluable" category.
- 10.1002/mrm.21519 — Menze 2008, Magn Reson Med — foil: evaluable/non-evaluable quality gate.
- 10.1016/j.compbiomed.2021.104517 — Kreimeyer 2021, Comput Biol Med — foil: assessable vs non-assessable reports.
- 10.20944/preprints202608.1091.v1 — Liu 2026, Preprints.org — neighbour: layered sensing/provenance/interpretation stack.

## (c) Verdict

Yes — arxiv:2608.31014v1 (EviBound) threatens novelty: it anticipates item 3's claim that acquisition protocol is part of admissibility, and item 1's executable admissibility specification fixed before inference with missing evidence registered up front. It does not anticipate item 2's structural-vs-ordinary distinction as a per-criterion output with reasons, the taxonomy (no construct insufficiency), protocol censoring of a threshold, or item 4. Position: cite as concurrent nearest precedent; EviBound licenses claim types per protocol, this paper declares derivability per clinical criterion and states protocol insufficiency as censoring of an observed continuous variable relative to a clinical threshold. Cite Lin and Garg to disambiguate "evidence admissibility" from retrieval eligibility. No other A8 record threatens items 1–4.

## (d) Possibly missing (unverified)

- Selective prediction / learning-to-reject (Chow 1970; Geifman & El-Yaniv 2017).
- Kendall & Gal 2017, aleatoric vs epistemic uncertainty.
- Structural missingness / not-applicable handling in questionnaire methodology — no canonical paper recalled.
- Terwee et al. 2007, COSMIN criteria incl. floor/ceiling effects.
- Goldsack et al. 2020, V3 framework (axis A6).
