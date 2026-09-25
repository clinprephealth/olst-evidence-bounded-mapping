# Synthesis A4 — Data provenance in healthcare and clinical AI

153 records: 0 rated 3, 10 rated 2, 60 rated 1, 83 rated 0. One fetch verified the sole rating-3 candidate (Seneviratne 2023); downgraded to 2.

## (a) What this literature does / does not do

A4 records **provenance of data and of outputs**: (i) W3C PROV / provenance-template infrastructure for LHS and CDS (Curcin, Fairweather; TRANSFoRm/Consult), capturing *which data and rule fired* after the fact; (ii) data-lineage provenance in warehouses, ETL and PGHD (gitOmmix, Gierend, Johns, Wittner), versioning *data*; (iii) governance guidance and "source-verifiable" RAG clinical AI (FUTURE-AI, AMIA, Alu 2026, ClinicBot, DeepRare) demanding traceability of *recommendations to sources*.

None does items 1–3: no record declares, per criterion, the required evidence units and whether the modality is *capable* of supporting the criterion before inference; none operationalises structurally-unobservable vs missing; none treats acquisition protocol as censoring a threshold. Item 4 is approached from two sides that never meet: gitOmmix gives content-addressed (git) identity to *data and analyses*; Seneviratne gives separate ontologies to *guideline editions* (AJCC 7th vs 8th). Neither replays a historical result under old vs new mapping nor attributes divergence; Seneviratne's "applicability" means cohort-to-patient similarity, not evidence capability. Ibrahim (structural opacity vs ordinary uncertainty) and Tran ("silent guideline drift") are rhetorical echoes of items 2 and 4, not mechanisms.

## (b) Records to cite

| key | first author, year, venue | use |
|---|---|---|
| 10.1016/j.jbi.2016.10.022 | Curcin 2017, J Biomed Inform | **Foil/canonical**: provenance templates record which data and rules produced a CDS recommendation — provenance *of outputs*, vs admissibility declared *before* output. |
| 10.1002/lrh2.10019 | Curcin 2017, Learn Health Syst | **Canonical-ref**: provenance as LHS auditability; establishes "we added provenance" as occupied. |
| arxiv:2006.11233v1 | Fairweather 2020, arXiv | **Neighbour**: non-repudiable provenance for a CDS (Consult); never asks whether evidence can support a criterion. |
| 10.2196/51297 | Gierend 2024, JMIR | **Canonical-ref**: scoping review showing provenance capture is mature. |
| 10.1016/j.jbi.2025.104788 | Wack 2025, J Biomed Inform | **Neighbour**: gitOmmix ties data to analyses/decisions via git content addressing plus PROV; nearest analogue to item 4, but the versioned object is data, not the clinical mapping. |
| 10.3233/ao-2011-0087 (indexed key; paper is J Biomed Semantics 2023) | Seneviratne 2023 | **Neighbour**: separate ontologies per guideline edition and recommendation provenance; closest guideline-versioning precedent — state that it lacks replay/attribution. |
| 10.1055/s-0038-1638748 | de Lusignan 2011, Yearb Med Inform | **Foil**: dataset-level "fit for purpose" quality/provenance/traceability; the granularity the paper moves below. |
| 10.1038/s41746-024-01116-6 | Lekadir 2025, BMJ (FUTURE-AI) | **Canonical-ref**: consensus Traceability principle; the demand the paper satisfies structurally rather than by logging. |
| 10.1111/1745-9125.12123 (indexed key; paper is JAMIA 2022) | Solomonides 2022, JAMIA | **Canonical-ref**: AMIA principles — audit trail and "safe failure"; item 2 is a concrete safe-failure form. |
| 10.3389/frai.2026.1737532 | Alu 2026, Front Artif Intell | **Neighbour**: "auditable, source-verified" RAG-CDS verifies *sources of recommendations*, not admissibility of patient evidence. |

## (c) Verdict

**Nothing in A4 threatens items 1–4 or the taxonomy.** Nearest: Seneviratne 2023 (guideline editions as separate artifacts, no replay/attribution) and Wack 2025 (content-addressed identity for data, not the interpretation layer). Neither decides per criterion whether evidence can support it, nor decomposes result identity into measurement / interpretation / implementation. Position explicitly against Curcin 2017 so reviewers do not conflate item 1's run-time evidence pointers with post-hoc provenance capture.

Two index key/DOI mismatches (Seneviratne carries an Applied Ontology 2011 DOI; Solomonides a Criminology DOI). Keys kept as-is per brief; verify DOIs before citing.

## (d) Possibly missing (unverified)

- Moreau & Missier, W3C PROV-DM (2013) — base standard; unverified.
- Later Consult/TRANSFoRm provenance-template papers (Chapman, Fairweather ~2019–2021); unverified.
- ONC SAFER guides on CDS auditability — governance foil; unverified.
