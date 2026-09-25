# Synthesis A7 — Reproducible/versioned clinical pipelines; CDS knowledge-base and value-set versioning

264 records: 3 rated 3, 13 rated 2, 80 rated 1, 168 rated 0 (A7.2 hash/blockchain hits were near-pure noise). All three 3s verified from full abstract/text.

## (a) What this literature does / does not do

(i) **Reproducible pipelines** (containerized workflows, Gupta 2022 MIMIC-IV, BioCompute Objects, Voss 2015 OMOP, Ostropolets 2023 multi-team reproduction, OxyMake) version *code, data, execution*; none separates clinical interpretation from measurement. (ii) **Re-execution under old vs new rules**: Cholan 2017 AMIA re-implements three successive versions of four CQMs and quantifies the shift; Cholan 2017 eGEMs runs two developers' value sets for one measure on the same data; Kasa 2026 replays a readmission target under faithful vs naive definitions; Bouaud 2007 types KB changes forced by a guideline update, without re-executing. (iii) **Knowledge-maintenance / value-set-drift foils**: Geissbuhler 1999, Thayer 2024 (rule-CDS malfunctions), Zahn 2025 (value-set errors), Gold 2024 ("error or intentional decision" indistinguishable), Mohammadi 2026 (phenotype libraries). (iv) **Hashed, versioned knowledge**: TraceGraph 2026 (immutable assertions, deterministic ids, SHA-256 evidence hashes, point-in-time rollback, drift alerts).

Items 1–3 and the taxonomy: nothing. No record declares per-criterion evidence requirements or derivability classes, separates structural non-evaluability from missingness (MoDN treats systematic missingness statistically), or treats acquisition protocol as censoring. Item 4: the *phenomenon* (mapping versions change results, decomposable into logic vs vocabulary) is Cholan's; the *mechanism* (three content-addressed identities, historical result reproducible by construction, attribution by identity diff) appears nowhere; TraceGraph never replays patient-level results.

## (b) Records to cite

| key | first author, year, venue | use |
|---|---|---|
| pmid:29854122 | Cholan 2017, AMIA | **Precedent**: replay under successive CQM versions. |
| 10.5334/egems.212 | Cholan 2017, eGEMs | **Precedent**: variant value sets on same data; asks developers to "provide rationale". |
| 10.21203/rs.3.rs-8466783/v1 | Cao 2026, Research Square (preprint) | **Precedent/neighbour**: hash-identified versioned assertions with drift detection; differentiate on result replay and three-way identity split. |
| 10.1101/2021.10.14.21264917 | Ostropolets 2023, JAMIA | **Foil**: nine teams diverge on one cohort via logic interpretation; divergence here is attributed to a hashed artifact. |
| 10.1136/amiajnl-2011-000456 (indexed key; paper is PLoS One 2024) | Gold 2024 | **Foil**: the error-vs-intent attribution gap in value sets. |
| 10.1101/2025.02.27.25323054 | Zahn 2025, medRxiv | **Foil**: taxonomy of value-set errors and CDS consequences. |
| 10.1093/jamia/ocy041 (indexed key; paper is JAMIA 2024) | Thayer 2024 | **Foil**: rule-based CDS malfunctions incl. terminology/logic change. |
| pmid:10566464 | Geissbuhler 1999, AMIA | **Canonical-ref**: CDS knowledge maintenance as process. |
| pmid:17911832 | Bouaud 2007, SHTI | **Neighbour**: KB-change typology under guideline update. |
| 10.1093/jamia/ocv112 | Mo 2015, JAMIA | **Canonical-ref**: phenotype logic as formal computable artifact. |
| 10.1093/jamia/ocu023 | Voss 2015, JAMIA | **Canonical-ref**: OMOP replication across databases. |
| 10.5731/pdajpst.2016.006734 | Simonyan 2017, PDA J Pharm Sci Technol | **Canonical-ref**: BioCompute Objects for computational provenance. |

Optional: arxiv:2606.20989v3 (OxyMake), 10.21203/rs.3.rs-10319770/v1 (Kasa 2026).

## (c) Verdict

**Item 4 is partially anticipated; items 1–3 and the taxonomy are not.** Cholan 2017 (both) already re-execute under different CQM versions/value sets and decompose the change into logic vs vocabulary. Stated as "a mapping change yields a divergent result", item 4 will draw a Cholan citation; state it instead as the identity mechanism — content-addressed separation of measurement / interpretation / implementation, historical result reproducible by construction, attribution by identity diff without re-derivation — which Cholan lacks. TraceGraph (unrefereed preprint) overlaps the hash-identified versioned interpretation layer; differentiate on patient-level replay and the three-way split. A7 never touches criterion-level admissibility, structural-vs-missing, or protocol censoring.

Verify before citing: Gold 2024 and Thayer 2024 carry wrong DOIs in the index.

## (d) Possibly missing (unverified)

- McDermott 2021 Sci Transl Med; Beam, Manrai, Ghassemi 2020 JAMA; Johnson, Pollard, Mark 2017 MLHC — canonical reproducibility-in-clinical-ML (i).
- Wang 2020 MIMIC-Extract.
- Wright 2016 JAMIA CDS malfunction analysis — primary taxonomy Thayer extends.
- Dolstra 2004 (Nix) / Guix / DVC — content-addressed build identity.
