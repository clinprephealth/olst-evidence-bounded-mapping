# Synthesis A2 — selective prediction / abstention / learning-to-defer / answerability (147 records: 1×3, 14×2, 59×1, 73×0)

## (a) What this literature does and does not do (items 1–4)

Every selective-prediction, reject-option and learning-to-defer record decides *whether to emit a prediction* after the model has run, from a score derived from the prediction: softmax/MC-dropout uncertainty, conformal sets, energy scores, calibrated confidence, or an FP/FN/abstain cost trade-off. The canonical references present — Kompa 2021, Swaminathan 2023, Liu 2021 (LDU), Joshi 2021 (SLTD), Abdulai 2025, Jabbour 2025 — are therefore **confidence- or cost-driven**; none asks, per criterion of a clinical instrument, whether the available evidence is *capable* of supporting the criterion before prediction. The answerability/sufficient-context strand (Asai & Choi 2021, Joren 2024, KnowGuard 2025, Afrasyab 2026) moves the trigger to "evidence", but sufficiency is judged post hoc by a learned classifier, LLM autorater or prompt over free text — never declared ahead of time, tied to a modality/protocol, or versioned. Nothing touches item 3 (protocol censoring) or item 4 (separate identities, divergence attribution).

Three records break the confidence pattern:
- **ClinDet-Bench (Watanabe 2026, fetched)**: cases from 16 clinical scores (CURB-65, qSOFA, Child-Pugh, HAS-BLED…) are labelled *determinable/undeterminable* by pure logic — S_min/S_max over missing items against the threshold. Evidence-driven, confidence-independent non-evaluability at *score* level. But: a benchmark; missingness is only "item not provided"; no NA-vs-unknown; no modality/construct/protocol classes; no per-item derivability output; no versioned map.
- **Gárate 2026 (fetched)**: deterministic rule-based CDS framework whose declared abstention categories include "missing inputs: required clinical information … is absent". Declared, evidence-driven abstention, but ordinary missingness, no NA-vs-unknown, unimplemented.
- **Schneider 2015**: deployed radiology CDS emitting "indeterminate (insufficient information)" separately from "not validated (no guideline)" — two distinct non-evaluability states in production CDS.

## (b) Records to cite

| key | first author, year, venue | use |
|---|---|---|
| arxiv:2602.22771v1 | Watanabe 2026, arXiv | partial precedent: logical score determinability; distinguish from criterion-level modality/protocol admissibility |
| 10.1038/s41746-020-00367-3 | Kompa 2021, npj Digit Med | canonical foil: uncertainty-driven "I don't know" |
| 10.1007/s10618-016-0460-3 (key DOI wrong) | Swaminathan 2023, JAMIA | canonical foil: cost-driven selective prediction |
| arxiv:2108.07392v5 | Liu 2021, arXiv | canonical foil: L2D with uncertainty |
| arxiv:2109.06312v2 | Joshi 2021, arXiv | canonical foil: sequential, value-driven deferral |
| 10.1016/j.ijmedinf.2025.105957 | Abdulai 2025, IJMI | foil: conformal "Don't know" |
| arxiv:2508.07617v2 | Jabbour 2025, arXiv | neighbour: clinician response to withheld predictions |
| arxiv:2411.06037v3 | Joren 2024, arXiv | canonical foil: post-hoc sufficient-context autorater |
| arxiv:2010.11915v2 | Asai & Choi 2021, arXiv | canonical foil: learned answerability |
| arxiv:2509.24816v1 | Dang 2025, arXiv | neighbour: "insufficient information" abstention, model-mediated |
| arxiv:2607.18086v1 | Afrasyab 2026, arXiv | neighbour: evidence-sufficiency prompting |
| arxiv:2603.10027v1 | Gárate 2026, arXiv | neighbour: declared abstention categories in deterministic CDS |
| 10.1016/j.jacr.2014.12.005 | Schneider 2015, JACR | neighbour: "indeterminate" vs "not validated" |
| 10.20944/preprints202608.0414.v1 | Radiuk 2026, Preprints | neighbour: reason-coded abstention (rule conflict) |

## (c) Verdict

Nothing in A2 threatens items 1, 3, 4 or the taxonomy. **ClinDet-Bench** partially anticipates item 2's core — that non-evaluability can be a logical property of the evidence rather than of confidence — and must be cited and distinguished (score-level interval logic over "not provided" items; no modality/construct/protocol distinction; no emitted per-criterion class; benchmark, not pipeline). Gárate 2026 shows "missing required input" abstention is already articulated for rule-based CDS; the paper's claim should rest on *structural* admissibility, evidence pointers and versioned replay, not on declared abstention per se.

Hygiene: several PubMed-derived keys carry wrong DOIs (Kompa → 10.1126/science.aaw4399; Swaminathan → 10.1007/s10618-016-0460-3; Lee TRAP → 10.1109/cvpr…); resolve by title.

## (d) Possibly missing (unverified)
- Chow 1970, reject-option origin (IEEE Trans IT).
- El-Yaniv & Wiener 2010 (JMLR); Geifman & El-Yaniv 2017, selective classification for DNNs (NeurIPS).
- Madras, Pitassi & Zemel 2018, learning to defer (NeurIPS); Mozannar & Sontag 2020 (ICML).
- Rajpurkar et al. 2018, SQuAD 2.0; Kamath, Jia & Liang 2020, selective QA under domain shift (ACL).
