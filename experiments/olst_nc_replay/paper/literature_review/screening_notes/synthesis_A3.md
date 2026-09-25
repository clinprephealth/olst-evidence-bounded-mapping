# Synthesis A3 — structured/informative missingness, NA-vs-unknown, task-relative completeness, evidence sufficiency (285 records: 1×3, 16×2, 124×1, 144×0)

## (a) What this literature does and does not do (items 1–4)

Three strands. (i) **Informative missingness/presence** (Che 2016 GRU-D, Groenwold 2020, Harton 2022, ~40 imputation/representation papers): absence is a *signal* to exploit or a bias to correct — the mirror image of withholding a criterion because the modality cannot observe it. (ii) **Structured missingness** (Mitra 2023, Jackson 2023, Rehak Buckova 2025, Liang 2026): missingness with structure (by design, site protocol, "logically undefined"), always resolved by modelling, imputing or marginalising; none emits a per-item "not evaluable" state. Liang 2026 (fetched) names "logically undefined" values, then marginalises them like unobserved ones. (iii) **EHR data quality / fitness for use** (Weiskopf & Weng 2013, Kahn 2016, Weiskopf 2017, Razzaghi 2022): completeness is task-dependent, judged at dataset/variable level before any criterion, with no per-item evidence requirements.

"Not applicable vs unknown" appears only as survey skip logic (Zhang 2023: impute only among applicable respondents) and structural zeros (He 2014: not-at-risk vs observed zero) — item-level NA formalised for estimation, not as an admissibility verdict. **No HL7 NullFlavor / FHIR data-absent-reason record was retrieved** despite the A3.3 query; see (d). Criterion evaluability under incomplete EHR data is studied empirically (Harris 2025; Gooch 2024), never emitted per criterion.

One cross-domain precedent: **Saadat 2025, Quant ES (fetched)**. Per genomic variant, a binary matrix over registered evidence rules records whether *required evidence is available* — checked before interpretation logic, from an MD5-hashed rule specification, implemented as an R package, yielding a replayable sufficiency score. This anticipates item 1 (per-rule evidence availability separated from interpretation) and item 4 (hashed rule identity). It has no NA-vs-unknown state, no modality/construct/protocol taxonomy, no protocol censoring, and one aggregate score rather than per-criterion classes.

Imaging "data sufficiency conditions" (Tuy; Gullberg 1992, Tang 2018, Jia 2026) — acquisition geometry decides what is reconstructable — are a one-sentence analogy for protocol insufficiency, not a precedent.

## (b) Records to cite

| key | first author, year, venue | use |
|---|---|---|
| 10.64898/2025.12.02.25341503 | Saadat 2025, medRxiv | precedent (cross-domain): evidence-availability layer, hashed rules |
| arxiv:2304.01429v1 | Mitra 2023, arXiv | canonical structured missingness; foil |
| arxiv:2307.02650v1 | Jackson 2023, arXiv | canonical SM taxonomy; no NA state |
| arxiv:2601.18500v2 | Liang 2026, arXiv | foil: "logically undefined" marginalised |
| 10.1101/2025.06.07.658014 | Rehak Buckova 2025, bioRxiv | foil: protocol-induced missingness imputed |
| 10.1136/amiajnl-2011-000681 | Weiskopf & Weng 2013, JAMIA | canonical DQ dimensions |
| 10.13063/2327-9214.1244 | Kahn 2016, eGEMs | canonical fitness-for-use |
| 10.5334/egems.218 | Weiskopf 2017, eGEMs | canonical task-dependent completeness |
| 10.1002/lrh2.10264 | Razzaghi 2022, Learn Health Syst | neighbour: fitness vs intended use |
| arxiv:1606.01865v2 | Che 2016, arXiv | canonical informative missingness; foil |
| 10.1175/… (key DOI wrong) | Groenwold 2020, Diagn Progn Res | foil: missingness-as-predictor non-transportable |
| 10.1093/jamia/ocac050 | Harton 2022, JAMIA | canonical informative presence |
| 10.1093/jssam/smt008 | Zhang 2023, J Stat Comput Simul | neighbour: item-level NA distinct from missing |
| 10.1177/0193945910379220 | He 2014, Shanghai Arch Psychiatry | canonical structural zeros; foil |
| 10.1001/jamanetworkopen.2025.39870 | Harris 2025, JAMA Netw Open | neighbour: CDS criteria under incomplete history |

## (c) Verdict

No A3 record formalises a "structurally unobservable / not applicable" state at clinical-criterion or instrument-item level and operationalises it in software; the taxonomy and item 3 are unthreatened. **Saadat 2025** partially anticipates items 1 and 4 (per-rule evidence availability before interpretation, hashed rule identity, replay) and must be cited and distinguished: single aggregate score, availability = presence of a data source, no structural-absence semantics, no protocol ceiling, no divergence attribution across map versions. Structured-missingness work supplies the contrast vocabulary: "structure" there is a property of the mask to be modelled; here it is a declared property of the evidence–criterion relation.

Hygiene: several PubMed-derived keys carry wrong DOIs (Groenwold → 1950 meteorology DOI; Lewis 2023 → 10.1136/bmj.n71); resolve by title.

## (d) Possibly missing (unverified)
- HL7 v3 / ISO 21090 NullFlavor (NI, NA, UNK, ASKU, NASK, NAV, MSK); FHIR `data-absent-reason`.
- Weiskopf, Hripcsak, Swaminathan & Weng 2013, "Defining and measuring completeness of EHRs for secondary use" (JBI).
- Rubin 1976; Little & Rubin, *Statistical Analysis with Missing Data*.
- Hripcsak & Albers 2013 (JAMIA); Agniel, Kohane & Weber 2018 (BMJ).
- ICH E9(R1) estimands — outcomes undefined after intercurrent events.
