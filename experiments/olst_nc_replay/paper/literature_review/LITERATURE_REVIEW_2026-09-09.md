# Literature checkpoint 2026-09-09 — OLST/NC decision-compatibility paper

**Purpose.** The pre-submission plan calls for a structured literature checkpoint before any novelty language is written. This document is that checkpoint. It records the search matrix, hit counts, screening, the papers that come closest to the manuscript's four claimed contributions, and the Related Work language the evidence supports. It is an input to a future dated amendment; it does not edit the frozen manuscript (`OLST_MANUSCRIPT_DRAFT.md`, sha256 `8269444a…f41d`) or the frozen plan.

**Status.** Structured novelty scan with logged queries and title/abstract screening of every retrieved record. Not a systematic review: three bibliographic databases, English only, relevance-ranked top-N per query, one screening pass per record with full-text verification of every high-rated record. §8 lists what remains to be done before a "no prior work" sentence of any strength can be written.

**Companion files (same directory).**

| File | Content |
|---|---|
| `literature_search_log_2026-09-09.json` | Every query string verbatim, database, UTC timestamp, total hit count, and the top-N records retrieved (title, year, venue, PMID/DOI/arXiv id, abstract) |
| `literature_screening_2026-09-09.json` | The 1,676 deduplicated records with a 0–3 rating per axis, a one-line reason, and a role (precedent / foil / neighbour / canonical-ref / background / noise) |
| `LITERATURE_REVIEW_2026-09-09.bib` | 95 references, each resolved to a PMID, DOI or arXiv id on 2026-09-09 |

Citation keys in this document (`[key]`) are the BibTeX keys.

**Companion file identities (sha256).**

| File | sha256 |
|---|---|
| `literature_search_log_2026-09-09.json` | `9c6818c028d1ffb9ff257f11dd3cb79ffb77a4fdd7063742e891d40a911df685` |
| `literature_screening_2026-09-09.json` | `58014b7e1391891fed9123bfd8d6370c4f71d44c41a5d151b5633371390746ca` |
| `LITERATURE_REVIEW_2026-09-09.bib` | `6574108cd14a2f65e4115904a3f2e80c40ea26d20f3dcf36b124ddfc334fda12` |

Also included: `search_scripts/` (the query matrix, the search runner, the reference resolver, the screening brief, and `verified_refs.json`) so the matrix can be re-run at submission, and `screening_notes/` (the eight per-axis screening syntheses that fed §3).

---

## 1. Headline

The project is not redundant with anything found. No paper combines criterion-level declared derivability, structural non-evaluability with reasons, acquisition-protocol censoring of a clinical threshold, and content-addressed replay of a versioned clinical mapping. Three of the four contributions are, however, now partially anticipated by work that a reviewer in JBI or JAMIA will know or find, and the manuscript's positioning has to change in four specific places.

1. **Contribution 3 (acquisition protocol as part of admissibility) has a concurrent precedent.** EviBound [gao2026evibound] (arXiv, posted 2026-08-31) defines an "evidence package" of protocol profile, modality mask, claim-permission matrix and observations; the permission matrix is fixed before inference, is protocol-dependent ("fixed-reading text cannot support semantic symptom inference"), registers missing modalities up front, and a deterministic validator blocks claims and records the reason. That is the declared-ahead-of-time, protocol-conditioned admissibility pattern, in speech-based depression screening with LLMs. It does not have per-criterion derivability classes, a construct-insufficiency class, censoring of a measured continuous variable relative to a numeric clinical threshold, or content-addressed identities and v1→v2 replay; its "replay" is re-auditing cached reports. The manuscript must cite it as concurrent work and state contribution 3 as *protocol censoring of a measured construct* (label withheld, number retained, ceiling named, per participant and per criterion), which EviBound's categorical claim permissions do not do.
2. **Contribution 1 (declared derivability per criterion) has a design-time precedent in a different domain.** Bouzinier et al. [bouzinier2026] introduce meta-predicates that assert, for each clinical decision rule in a DSL, which evidence types are permissible, over an "epistemological type system" whose four dimensions include *method of acquisition*; validation is prospective (design time) and instantiated in a genomic variant curation platform. This is the closest prior statement that a rule's evidentiary entitlement should be declared and machine-checked rather than inferred. It validates rule *authoring* against evidence *types*; it does not evaluate, per case, whether the evidence actually present can support a criterion, emit non-evaluable outputs with reasons, treat protocol ceilings, or content-address results. Found only through a supplementary semantic search (alphaXiv), not through the keyword matrix — see §8.
3. **Contribution 4 (versioned clinical mapping with replay) is the phenomenon Cholan et al. documented in 2017.** Cholan, Weiskopf et al. re-implemented three successive versions of four CQMs and two developers' value sets on the same registry data and decomposed the resulting shifts into logic and vocabulary changes [cholan2017amia; cholan2017egems]. Stated as "a mapping change yields a different result from the same evidence", contribution 4 is theirs. Stated as the identity mechanism — measurement, interpretation and implementation carrying separate content-addressed identities, the historical result reproducible by construction, and divergence attributed by digest comparison without re-derivation — it is not in Cholan, nor in the hash-identified rule and assertion layers of Quant ES [saadat2025quantes] and TraceGraph [cao2026tracegraph], nor in gitOmmix's content-addressing of data [wack2025gitommix]. The manuscript should claim the mechanism and cite the phenomenon.
4. **Contribution 2 (structural non-evaluability distinct from missingness and uncertainty) is unanticipated as a per-criterion output, but the surrounding vocabulary exists and should be used.** ClinDet-Bench [watanabe2026clindet] shows that determinability of a clinical score under missing items is a logical property of the evidence rather than of model confidence, and that missing items do not always make a score undeterminable (S_min/S_max against the threshold). HL7 v3 NullFlavor distinguishes "not applicable" from "unknown" at the datum level [hl7nullflavor]; a production radiology CDS emitted "indeterminate (insufficient information)" separately from "not validated (no guideline)" [schneider2015]; the MDS-UPDRS has scale-specific rules for how many missing items invalidate a part score [goetz2015mdsupdrs]; and epidemiology already separates structural from random positivity violations [westreich2010positivity; petersen2012positivity]. None of these operationalizes structural non-evaluability at the level of an instrument criterion evaluated from a measurement modality. That remains the paper's contribution, and the taxonomy (modality / construct / protocol insufficiency) is the most portable thing in it.

Two sentences in the frozen draft have to go regardless of framing: "No prior system we are aware of combines…" (§2, *Gap*) and "the first public corpus with synchronized motion capture, bilateral force plates, and radar" (§2, *Balance assessment*). The second is now the dataset authors' claim to make, and their descriptor exists [copeland2026scidata].

One finding is not about positioning but about D4a. The dataset's companion paper states that data were collected "during short (4 s) and long (20 s) OLST trials" [copeland2026gaitposture]. Amendment A3 left `observation_ceiling_ms` null for `MNTR*` because the README does not state the cue. A published source for a 4 s cue now exists. A 4,000 ms ceiling lies below the 5 s threshold, a case the frozen D4a rule text does not enumerate (it covers null, ≥10,000 ms, and 5,000–10,000 ms); the only consistent extension — no duration threshold observable, hence `protocol_censored` — gives the same output as the null ceiling, so no label changes. What changes is that the ceiling can be carried in the fixture with a named source, the rule text gains the sub-5 s case, and the record shows that observed `MNTR*` maxima (6.34 s) exceed the nominal cue, as `TRLG*` maxima (21.31 s) exceed 20 s. This belongs in the next dated amendment, not in a silent loader edit.

---

## 2. Method

**Databases and access.** PubMed (NCBI E-utilities, relevance sort, top 30 per query with abstracts), Europe PMC (REST, default relevance sort, top 25, includes medRxiv/bioRxiv/Research Square preprints), and arXiv (export API, relevance sort, top 15). Semantic Scholar and OpenAlex were rate-limited and unavailable on the day; Scopus, Web of Science, IEEE Xplore, ACM DL and Google Scholar were not searched. Supplementary: two semantic searches on alphaXiv (arXiv CS/stat) for the core claim and for versioned-mapping replay; verification of the four PMC citations and one ScienceDirect citation carried over from the earlier ChatGPT scan (§9).

**Matrix.** Eight axes: the seven named in the pre-submission checkpoint (A1 clinical score automation; A2 selective prediction/abstention; A3 structural missingness; A4 data provenance; A5 criterion-level traceability; A6 measurement/acquisition compatibility; A7 reproducible clinical pipelines) plus A8, a direct hunt for the combined claim ("non-evaluable" criteria in automated systems, modality-unobservable items, "evidence admissibility / decision compatibility" language, partial scale scoring, replay of versioned criteria). A5 and A6 were widened deliberately to the adjacent literatures most likely to hold a near-duplicate: computable eligibility criteria, CQL/eCQM/computable phenotypes, the DiMe V3 fit-for-purpose framework, single-leg-stance protocol ceilings, and censoring of timed performance tests. 37 queries, 99 query–database runs, all executed 2026-09-09 between 18:58 and 19:03 UTC (PubMed and arXiv), with the Europe PMC pass re-run immediately afterwards after an invalid sort parameter had returned zero hits.

| Query | Axis | PubMed | Europe PMC | arXiv |
|---|---|---:|---:|---:|
| A1.1 BBS × sensors/ML × automated/estimated | A1 | 113 | 92 | 2 |
| A1.2 Morse Fall Scale × automation/EHR/sensor | A1 | 28 | 22 | 0 |
| A1.3 single-leg stance × sensor/force plate/radar/mocap | A1 | 483 | 399 | 3 |
| A1.4 instrumented clinical balance tests, automated scoring | A1 | 144 | 2 | — |
| A1.5 PhysioNet OLST / OLST × radar | A1 | 4 | 5 | 1 |
| A2.1 selective prediction / reject option / learning to defer, clinical | A2 | 966 | 83 | 140 |
| A2.2 uncertainty × abstain / "I don't know" / known unknowns | A2 | 10 | 9 | 2150† |
| A2.3 unanswerable / answerability / sufficient context, clinical | A2 | 25 | 13 | 49 |
| A3.1 structured/structural missingness, legitimate skip | A3 | 95 | 34 | 60 |
| A3.2 informative missingness / presence, MNAR in EHR | A3 | 57 | 38 | 16 |
| A3.3 "not applicable" vs unknown; NullFlavor | A3 | 30 | 24 | 269† |
| A3.4 EHR completeness, fitness for use, task-dependent | A3 | 148 | 47 | — |
| A3.5 data / evidence sufficiency × decision support | A3 | 17 | 15 | 168† |
| A4.1 provenance × CDS / EHR / LHS | A4 | 201 | 24 | 398 |
| A4.2 PROV-O / PROV-DM / provenance templates × health | A4 | 21 | 20 | 2 |
| A4.3 provenance/traceability/auditability × clinical AI × guidance | A4 | 402 | 187 | 996 |
| A5.1 criterion-level / per-criterion × traceability / justification × automation | A5 | 9 | 9 | 5 |
| A5.2 eligibility criteria × computability / data availability × EHR | A5 | 151 | 4 | 30 |
| A5.3 CQL / eCQM / computable phenotype / CIG / Arden × versioning / data requirements | A5 | 119 | 55 | 2 |
| A5.4 explanation / rule tracing × rule-based CDS | A5 | 24 | 8 | — |
| A6.1 fit-for-purpose × digital health technology / biomarker / sensor | A6 | 125 | 87 | 4 |
| A6.2 verification + analytical validation + clinical validation (V3) | A6 | 18 | 12 | — |
| A6.3 concept of interest / context of use × digital / sensor | A6 | 277 | 155 | — |
| A6.4 single-leg stance × protocol / ceiling / cut-off / normative / censor | A6 | 389 | 98 | — |
| A6.5 acquisition protocol × AI datasets × guidance / metadata | A6 | 49 | 5 | 35 |
| A6.6 right-censoring / ceiling × timed balance / endurance tests | A6 | 64 | 8 | — |
| A6.7 construct validity / crosswalk × balance × sensor / instrumented | A6 | 181 | 56 | — |
| A7.1 reproducibility × clinical ML pipelines × versioning / provenance / hash | A7 | 374 | 51 | 26 |
| A7.2 content-addressed / cryptographic hash / SHA-256 × clinical × integrity | A7 | 281 | 24 | 15 |
| A7.3 CDS knowledge base × versioning / maintenance / drift | A7 | 86 | 21 | — |
| A7.4 value set × drift / versioning | A7 | 35 | 8 | — |
| A7.5 OHDSI / OMOP × reproducibility / study packages | A7 | 42 | 25 | — |
| A8.1 non-evaluable / not assessable / cannot be scored × criteria × automation | A8 | 39 | 243 | 19227† |
| A8.2 modality / single sensor × cannot be observed / not derivable × items | A8 | 1 | 44 | 4 |
| A8.3 decision compatibility / evidence admissibility / evidence-bounded | A8 | 43 | 21 | 13 |
| A8.4 partial scoring / subset of items × sensors × scale | A8 | 4 | 51 | — |
| A8.5 replay / re-execution × versioned criteria / mapping × clinical | A8 | 0 | 0 | 1 |

† arXiv boolean over-match on broad OR terms; only the relevance-ranked top 15 were screened. Full query strings are in the search log.

**Screening.** 1,676 unique records after deduplication on DOI, PMID, arXiv id or title. Each record was rated on every axis that retrieved it: 3 = potential near-duplicate or direct precedent for one of the four contributions or the taxonomy; 2 = neighbour the Related Work must cite; 1 = background; 0 = off-topic. Screening was done in four parallel passes (two axes each) against a written brief that stated the four contributions and the taxonomy and forbade adding papers from memory; every rating-3 record, and the rating-2 records used in §4, were then verified by me from the abstract or full text. Result: 9 rating-3 entries (8 unique papers; one duplicate key), 108 rating-2, 611 background, 948 noise. Per axis (3/2/1/0): A1 0/15/134/43; A2 1/14/59/73; A3 1/16/124/144; A4 0/10/60/83; A5 1/16/43/87; A6 2/16/105/203; A7 3/13/80/168; A8 1/10/20/153.

**Identifier hygiene.** The first PubMed parse picked up reference-list DOIs for 485 of 881 records; all PubMed DOIs in the log were re-resolved from `esummary` and both values are retained (`doi`, `doi_as_parsed`). Every reference in the `.bib` was resolved independently by PMID, DOI or arXiv id; five items that no API indexes (HL7 NullFlavor, FHIR data-absent-reason, ICH E9(R1), FDA DHT guidance, W3C PROV-DM, El-Yaniv & Wiener 2010 in JMLR) are entered by hand and marked.

---

## 3. What each literature does, and does not do

### A1 — Clinical score automation from sensors

The Berg Balance Scale has been scored from body-worn accelerometers [badura2016bbs], wearable IMUs with deep learning [kim2021bbs; lu2025bbs], multi-depth cameras [eichler2022bbs], and BBS-defined fall-risk category has been estimated from an instrumented Timed Up and Go [zhang2026bbs]; single-leg stance duration has been timed from video [kawa2018sls] and used alone, via Kinect, as a stand-in for BBS fall-risk category [tripathy2018sls]. Morse Fall Scale work replaces the scale with an EHR-derived model [lee2016mfs], crosswalks AM-PAC mobility scores to the mobility components of fall-risk tools and finds the mapping succeeds for only a minority of items [stenum2025mfs], or shows that fall history — the one item no sensor can observe — is the only MFS item that discriminates fallers in nursing-home residents [oppegaard2026mfs]. The OLST dataset's own papers describe the corpus [copeland2026scidata] and a radar phase classifier trained on it [copeland2026gaitposture].

None of these represents which items it cannot score as a formal output. Eichler et al. predict all 14 BBS item scores and then reduce the task set by a confidence rule; Lu et al. note "the inability to predict the score of individual tasks" as a prose limitation; the total-score regressors score no item directly and do not say so. This is the "narrow silently" option of the manuscript's §1.1, and the literature supplies the examples. Stenum et al. and Oppegaard et al. are the strongest foils: an item-level crosswalk that fails, and a modality-unobservable item that carries the signal.

**Verdict.** No threat. Cite the automation strand as the occupied space, and Stenum / Oppegaard as evidence that the unscorable items are not incidental.

### A2 — Selective prediction, abstention, learning to defer, answerability

The reject option [chow1970], selective classification [elyaniv2010; geifman2017], learning to defer [madras2018; mozannar2020], selective question answering [kamath2020; rajpurkar2018], and their clinical applications [kompa2021; swaminathan2023] all decide *whether to emit a prediction after the model has run*, from a score derived from that prediction: confidence, calibrated uncertainty, conformal set size, or an error/abstention cost trade-off. The answerability strand moves the trigger to the evidence — "is the retrieved context sufficient?" [joren2024] — but sufficiency is judged post hoc by a learned classifier or an LLM over free text, never declared ahead of time, tied to a modality or protocol, or versioned.

Three records break the confidence pattern and must be cited. ClinDet-Bench [watanabe2026clindet] labels cases from 16 clinical scoring systems as determinable or undeterminable by pure logic — the interval of possible totals over the missing items against the threshold — and shows current LLMs both impute (81.6% of errors) and over-abstain. It is a benchmark; missingness is only "item not provided"; there is no not-applicable-versus-unknown distinction, no modality, construct or protocol class, no per-item derivability output, no versioned map. Gárate et al. [garate2026] specify declared abstention categories for a deterministic rule-based CDS, including "required clinical information is absent" (ordinary missingness, unimplemented). Schneider et al. [schneider2015] report a deployed radiology order CDS that emitted "indeterminate (insufficient information)" separately from "not validated (no guideline)" — two distinct non-evaluability states in production, and the handling of those states was the main driver of the two systems' divergent appropriateness rates.

**Verdict.** No threat to contributions 1, 3, 4 or the taxonomy. ClinDet-Bench partially anticipates the core of contribution 2 — that non-evaluability can be a property of the evidence rather than of confidence — at score level, and it adds a nuance the criterion map should adopt explicitly: a missing required input does not always make a criterion non-evaluable; whether it does depends on whether the criterion's decision boundary can be crossed by the missing information. The map's `partial` class is where that lives.

### A3 — Structural and informative missingness; "not applicable"; task-relative completeness

Rubin's MCAR/MAR/MNAR taxonomy [rubin1976] and its EHR descendants treat absence as something to model: informative presence and missingness as a signal to exploit or a bias to correct [agniel2018; groenwold2020; harton2022; che2018grud]; structured missingness as a mask with structure to be learned or imputed [mitra2023]. The EHR data-quality literature defines completeness relative to a task [weiskopf2013jamia; weiskopf2013jbi; kahn2016], at dataset or variable level, before any criterion is evaluated. "Not applicable" as a state distinct from "unknown" exists at the datum level in HL7 v3 NullFlavor (NA vs UNK, NI, NAV, ASKU, NASK, MSK) [hl7nullflavor] and FHIR `data-absent-reason` [fhirdataabsent], in survey skip logic, and in structural zeros; at instrument level, the MDS-UPDRS defines how many missing items invalidate a part score [goetz2015mdsupdrs]; in trials, ICH E9(R1) treats an outcome after an intercurrent event as a matter of estimand definition rather than as missing data [ichE9R1]; in causal inference, structural (deterministic) positivity violations are distinguished from random ones [westreich2010positivity; petersen2012positivity].

One cross-domain precedent: Quant ES [saadat2025quantes] computes, per genomic variant, a binary matrix over registered evidence rules recording whether the required evidence is *available*, before any interpretation logic runs, from an MD5-hashed rule specification, and reduces it to a single sufficiency score. That anticipates the separation of evidence availability from interpretation and the hashing of the rule set. It has no not-applicable semantics, no modality/construct/protocol taxonomy, no protocol ceiling, and one aggregate score rather than per-criterion classes with reasons.

**Verdict.** No record formalizes a structurally-unobservable state at clinical-criterion level in software. The vocabulary is established at other levels (datum, instrument, estimand, identification) and the paper should borrow it: the NullFlavor NA/UNK split and the structural/random positivity distinction are the shortest way to explain to an informatics reviewer what `non_evaluable` is and is not. Cite Quant ES and distinguish it.

### A4 — Data provenance in healthcare and clinical AI

Provenance capture is mature: W3C PROV-DM [w3cprov], provenance templates for CDS and the Learning Health System [curcin2017jbi; curcin2017lhs], a scoping review of biomedical provenance approaches [gierend2024], a systematic review of healthcare provenance technologies [ahmed2023], and content-addressed (git) versioning of clinical data with PROV alignment [wack2025gitommix]. Governance guidance now requires provenance, transparency and lifecycle re-evaluation of AI-CDS [labkoff2024; lekadir2025futureai; solomonides2022], and test-dataset guidance requires acquisition-protocol documentation, versioning and hashing [homeyer2022]. Seneviratne et al. [seneviratne2023] give separate ontologies to guideline editions with recommendation provenance, but "applicability" there means cohort-to-patient similarity and there is no replay or attribution.

All of this is provenance *of data and outputs*, recorded after the fact. Nothing decides, before inference, whether the evidence is capable of supporting a criterion; nothing decomposes result identity into measurement, interpretation and implementation.

**Verdict.** No threat. The manuscript's current Related Work paragraph on provenance is adequate in substance but should cite Curcin 2017 explicitly so that run-time evidence pointers are not mistaken for post-hoc provenance capture, and should drop any claim that criterion-level traceability is itself new.

### A5 — Criterion-level traceability; computable eligibility criteria; computable guidelines

The computable-eligibility literature asks a design-time, population-level question — which criteria can be resolved from the data an EHR holds. Formal representations [weng2010], complexity analysis [ross2010], element-presence audits [kopcke2013], the finding that structured data alone cannot resolve 59–77% of criteria [raghavan2015], criteria-to-query translation [yuan2019c2q], and most recently LLM tiering of criteria by "EHR predictability" — inferable from routine data versus dependent on specialised testing [muqeeth2026]. At run time, LLM prescreening emits per-criterion labels with rationale and evidence locations, including "no documentation found" as a state distinct from "uncertain", and versions criterion prompts under human approval while preserving historical outputs [dohopolski2026]. Computable phenotype desiderata [mo2015], the Arden Syntax [hripcsak1994arden], and computer-interpretable guidelines [peleg2013] declare data requirements as artefacts; Makadia et al. show definition edits move incidence rates across a data network [makadia2023].

The closest conceptual precedent for contribution 1 is outside this axis's retrieval: Bouzinier et al. [bouzinier2026] (see §1). Within the axis, Muqeeth is the design-time half (which criteria are evaluable from this source, at population level, no per-case output, no structural reason) and Dohopolski the run-time half (per-criterion status with evidence pointers, post hoc, ordinary missingness). No record combines both; none emits a per-criterion evaluability class with a structural reason; none targets an instrument scored from a measurement modality.

**Verdict.** Contribution 1 is anticipated in halves and in a neighbouring domain. Position it against Bouzinier (design-time evidence-type constraints on rules → per-criterion, per-case evaluability with reasons), Muqeeth (population tiers → declared derivability per criterion) and Dohopolski ("no documentation found" → structural non-evaluability, versioned prompts → content-addressed maps).

### A6 — Measurement and acquisition compatibility

The V3 framework (verification, analytical validation, clinical validation) [goldsack2020v3], its V3+ extension [bakker2025v3plus], the evidence-dossier structure with "concept of interest" and "context of use" [walton2020], FDA's DHT guidance [fda2023dht], and the COSMIN taxonomy of measurement properties including floor and ceiling effects [mokkink2010cosmin; terwee2007] all validate a *measure* for a *context of use* at instrument level. Tekwe et al. [tekwe2026] propose "inferential validity" — how well a measure supports a scientific, clinical or regulatory conclusion — as a downstream layer linking measurement evidence to conclusions; that is the compatibility layer stated as a validity concept rather than as executable machinery. Balance tests are task-specific and not interchangeable [ringhof2018].

On protocol ceilings: de Abreu et al. [deabreu2024] used 30 s maximum stances and state that a 10 s ceiling "may not be useful for identifying those with subtle imbalance" — the premise of contribution 3, as protocol advice, with no withheld label and censoring never named. Vereeck et al. dichotomize at both 10 s and 30 s limits [vereeck2008]; Araujo et al. define the test by whether 10 s is completed [araujo2022]; normative values [springer2007; bohannon2006; chung2025] and age/sex-specific cut-offs [beauchamp2022] show the threshold is protocol- and population-dependent. Nothing treats the ceiling as censoring that withholds a label per participant. The dataset's own papers do not treat the 4 s cued window as censoring the ≥10 s convention [copeland2026scidata; copeland2026gaitposture].

**Verdict.** Contribution 3's premise is in de Abreu 2024 and the OLST protocol literature; its mechanism (censoring semantics, ceiling carried as an acquisition fact with a named source, label withheld and number retained) is not. EviBound (§1) is the nearest mechanism in another modality. Tekwe 2026 supplies the name for what the criterion map is: an executable inferential-validity layer.

### A7 — Reproducible and versioned clinical pipelines

Reproducibility in clinical ML is a recognised problem [mcdermott2021; beam2020]; workflow managers [molder2021snakemake; ditommaso2017nextflow], BioCompute Objects [simonyan2017biocompute] and OHDSI study packages version code, data and execution. Nine expert teams reproducing one cohort from its text description produced cohorts from one-third to ten times the reference size [ostropolets2023]. CDS knowledge maintenance [geissbuhler1999] and malfunction analyses [wright2016] document that rule and terminology change is a leading failure mode. The re-execution of historical results under changed definitions is Cholan et al. [cholan2017amia; cholan2017egems]; hash-identified, versioned clinical assertions with point-in-time rollback are TraceGraph [cao2026tracegraph] (unrefereed preprint); "what a frozen evaluation licenses" and replay of historical claims bound to commits is Qin & Tong [qin2026replay] in ML evaluation.

**Verdict.** Contribution 4's phenomenon is documented; its mechanism is not. See §1 item 3.

### A8 — Direct hunt

"Non-evaluable" as an output category exists in imaging (LI-RADS "nonevaluable"), as quality gates on spectra and reports, and as "impossible to assess" in guideline-compliance audits; all are technical non-evaluability removable by better acquisition. "Evidence admissibility" in 2026 AI preprints means document-level retrieval eligibility or an evidence contract applied before assessment with a supported/insufficient verdict [lin2026medeventgraph]. Partial scale scoring from sensors is common and never declared. EviBound [gao2026evibound] is the one genuine precedent (§1).

---

## 4. Closest neighbours

| Record | What it does | Overlap | What it lacks | Positioning |
|---|---|---|---|---|
| EviBound [gao2026evibound], arXiv 2026-08-31 | Evidence package (protocol profile, modality mask, claim-permission matrix, observations); permissions fixed before inference; missing modalities registered; deterministic validator blocks claims and records reasons | C1 (declared ahead of time), C3 (protocol-dependent admissibility), C2 partly (modality absent vs protocol does not license) | Per-criterion derivability classes; construct insufficiency; censoring of a numeric threshold on a measured construct; content-addressed identities; v1→v2 replay attribution; domain is LLM speech screening | Concurrent work; nearest precedent for C3. This paper declares admissibility per clinical criterion and states protocol insufficiency as censoring of an observed continuous variable relative to a clinical threshold |
| Bouzinier 2026 [bouzinier2026] | Meta-predicates assert which evidence types (purpose, domain, scale, *method of acquisition*) a decision rule may use; prospective validation in a DSL; per-variant audit trail | C1 (declared evidentiary entitlement, machine-checked before deployment); acquisition as a declared dimension | Per-case evaluability of a criterion from the evidence present; non-evaluable output with reasons; protocol ceilings; content-addressed replay; genomics not measurement | Design-time type checking of rules vs run-time, per-criterion admissibility of evidence; complementary |
| ClinDet-Bench [watanabe2026clindet] | Determinable vs undeterminable clinical-score judgments under missing items by interval logic; LLMs fail both ways | C2 (non-evaluability as a logical property of the evidence, not confidence) | NA vs unknown; modality/construct/protocol classes; per-item derivability; versioned map; a benchmark, not a pipeline | Cite for the evidence-not-confidence point and for the nuance that missing inputs need not make a criterion non-evaluable |
| Cholan 2017 ×2 [cholan2017amia; cholan2017egems] | Re-implements successive CQM versions and alternative value sets on the same data; decomposes shifts into logic vs vocabulary | C4 (phenomenon) | Separate identities for measurement / interpretation / implementation; historical result reproducible by construction; attribution by digest without re-derivation | Claim the mechanism, cite the phenomenon |
| Quant ES [saadat2025quantes] | Per-variant × per-rule evidence-availability matrix computed before interpretation, from hashed registered rule sets; R package | C1 (availability separated from interpretation), C4 (hashed rule identity) | NA semantics; taxonomy; protocol ceiling; per-criterion classes with reasons (single aggregate score) | Cross-domain precedent; distinguish on granularity and on structural vs available |
| TraceGraph [cao2026tracegraph], Research Square preprint | Immutable versioned clinical assertions with deterministic ids, SHA-256 evidence hashes, point-in-time rollback, drift alerts | C4 (hash-identified versioned interpretation layer) | Patient-level result replay; three-way identity split; divergence attribution | Differentiate on result replay |
| Muqeeth 2026 [muqeeth2026] | LLM tiers eligibility concepts by EHR predictability (inferable vs needs specialised testing) | C1 design-time half | Per-case output; structural reason; instrument from modality | Population tiers → per-criterion declaration with reasons |
| Dohopolski 2026 [dohopolski2026] | Per-criterion met / not met / uncertain / *no documentation found* with rationale and evidence locations; versioned prompts, historical outputs preserved | C1 run-time half; evidence pointers; two distinct absence states | Structural non-evaluability declared ahead; identity decomposition | "No documentation found" is ordinary missingness; `non_evaluable` is structural |
| Schneider 2015 [schneider2015] | Deployed CDS emitting "indeterminate (insufficient information)" vs "not validated (no guideline)" | C2 (two non-evaluability states in production) | Any declared structure; reasons per criterion | Evidence that distinct non-evaluability states matter operationally |
| de Abreu 2024 [deabreu2024] | 30 s stances; a 10 s ceiling cannot identify subtle imbalance | C3 premise | Censoring semantics; withheld label; per-participant | Premise as protocol advice; this paper operationalizes it |
| Tekwe 2026 [tekwe2026] | "Inferential validity": how well a measure supports a conclusion, as a downstream layer | The compatibility layer as a validity concept | Executable form; per-criterion; protocol | Name the criterion map as an executable inferential-validity layer |
| Qin & Tong 2026 [qin2026replay] | Freeze an evaluation collection, replay historical claims bound to commits; most stop because evidence is not bound | C4 analogue in ML evaluation | Clinical mapping; identity decomposition | Analogue for "what a result licenses" |
| Homeyer 2022 [homeyer2022] | Test datasets must document acquisition protocol, be versioned and hashed | Acquisition as a documented fact; hashing | Acquisition as an admissibility input | Documentation vs admissibility |
| Curcin 2017 [curcin2017jbi] | Provenance templates record which data and rules produced a CDS recommendation | Run-time lineage | Admissibility before output | Provenance of outputs vs entitlement of evidence |

---

## 5. The taxonomy against the literature

The three-way taxonomy (modality, construct, protocol insufficiency) survives the review intact and each class now has an external anchor.

*Modality insufficiency* — the measurement system cannot observe the information. Anchors: Raghavan 2015 (structured data alone cannot resolve most criteria), Oppegaard 2026 (the unobservable MFS item is the discriminating one), NullFlavor NA vs UNK, structural positivity violations. The literature's standard response is imputation or informative-missingness modelling, which the paper's §1.1 option 1 names.

*Construct insufficiency* — the modality observes something related but not what the criterion asks. Anchors: V3 concept-of-interest / context-of-use [goldsack2020v3; walton2020], Tekwe's inferential validity, Ringhof's task specificity of balance tests, Stenum's failed item-level crosswalk, and the total-score regressors [zhang2026bbs] that substitute one construct for another without saying so. The paper's Morse-gait `partial` vs Berg-item-14 `derivable` contrast is the cleanest empirical statement of this class in the set.

*Protocol insufficiency* — the construct is measured, but the acquisition procedure prevents the criterion boundary from being observed. Anchors: de Abreu 2024, Vereeck 2008 (10 s vs 30 s limits), Araujo 2022 (test defined by the 10 s protocol), Homeyer 2022 (acquisition protocol as required documentation), EviBound (protocol-dependent claim permissions), ICH E9(R1) (an outcome made undefined by the estimand definition rather than missing) [ichE9R1]. The MNTR/TRLG result — seventeen participants observable to 10 s under one protocol and not the other, on the same variable — has no counterpart in the set.

The foil sentence the paper can now write: selective prediction handles uncertainty in a prediction; structured-missingness methods handle structure in the mask; the criterion map handles incompatibility between evidence and question, which neither confidence nor imputation can repair.

---

## 6. Consequences for the manuscript

**Delete.** §2 *Gap*: "No prior system we are aware of combines modality-specific deterministic transformation, criterion-level non-evaluable markers with stated reasons, and content-addressed replay verification with lineage to a published dataset's file digests." §2 *Balance assessment*: "is, to our knowledge, the first public corpus with synchronized motion capture, bilateral force plates, and radar" — replace with the dataset citation [copeland2026scidata] and let the descriptor carry its own claim.

**Fill.** `[[FILL: dataset citation and authors]]` → [copeland2026scidata] (Sci Data 2026, PMID 41741492) with [copeland2026gaitposture] for the protocol description. `[[FILL: imputation-in-clinical-ML reviews; selective prediction / reject option]]` → [rubin1976; mitra2023; che2018grud; agniel2018] and [chow1970; elyaniv2010; geifman2017; mozannar2020; kompa2021; swaminathan2023].

**Reframe contribution 3** as protocol censoring of a measured construct relative to a clinical threshold, with the ceiling as an acquisition fact carried in the fixture with a named source; cite EviBound as concurrent and de Abreu as premise.

**Reframe contribution 4** as the identity mechanism; cite Cholan for the phenomenon, Quant ES / TraceGraph / gitOmmix for hashed rules, assertions and data respectively.

**Add to contribution 2** the ClinDet-Bench nuance and the NullFlavor / positivity vocabulary; cite Schneider 2015 for operational consequence.

**Position contribution 1** against Bouzinier 2026, Muqeeth 2026 and Dohopolski 2026 as in §4.

**D4a source.** Record [copeland2026gaitposture]'s "short (4 s)" trial statement in the next amendment as a candidate source for `observation_ceiling_ms` on `MNTR*`; note that the label outcome under D4a is unchanged and that observed maxima exceed the nominal cue under both protocols.

### Proposed Related Work text

> **Automating clinical scales from sensors.** Berg Balance Scale scores or BBS-defined risk categories have been estimated from accelerometers, wearable IMUs, depth cameras and an instrumented Timed Up and Go [badura2016bbs; kim2021bbs; eichler2022bbs; lu2025bbs; zhang2026bbs], and single-leg stance has been timed from video and used alone as a proxy for fall-risk category [kawa2018sls; tripathy2018sls]. These systems ask how much of a clinician's score can be predicted from limited observations; items that cannot be observed are dropped, regressed through a proxy, or noted as a limitation, not represented as an output. Item-level crosswalks between mobility instruments succeed for a minority of items [stenum2025mfs], and for the Morse Fall Scale the item no sensor observes, fall history, is the one that discriminates fallers [oppegaard2026mfs]. We ask the inverse question — which criteria the observations are entitled to support — and make the answer machine-readable.
>
> **Abstention and determinability.** The reject option and selective prediction let a model decline to answer when its confidence or expected cost warrants [chow1970; elyaniv2010; geifman2017; mozannar2020], and have been applied to clinical extraction and risk models [kompa2021; swaminathan2023]. Answerability and sufficient-context work move the trigger to the evidence but judge sufficiency post hoc with a learned model [joren2024]. ClinDet-Bench shows that determinability of a clinical score under missing items is a logical property of the evidence rather than of model confidence, and that current language models both impute and over-abstain [watanabe2026clindet]; a deployed radiology CDS that emitted "indeterminate (insufficient information)" separately from "not validated (no guideline)" showed that the handling of such states dominates downstream behaviour [schneider2015]. Our `non_evaluable` state is neither uncertainty nor cost: the criterion is inadmissible because the modality, the construct, or the acquisition protocol cannot supply the required evidence, and no calibration changes that.
>
> **Missingness.** The dominant treatments of missing clinical data are imputation and the modelling of informative missingness [rubin1976; che2018grud; agniel2018; groenwold2020; mitra2023]; EHR data-quality frameworks define completeness relative to a task at dataset level [weiskopf2013jbi; kahn2016]. The distinction between *not applicable* and *unknown* exists at the datum level in HL7 NullFlavor and FHIR data-absent-reason [hl7nullflavor; fhirdataabsent], at instrument level in scale-specific rules for invalidating scores [goetz2015mdsupdrs], and in causal inference as structural versus random positivity violations [westreich2010positivity]. We carry that distinction to the level of an instrument criterion evaluated from a measurement modality, and we separate three structural causes.
>
> **Declared evidentiary entitlement.** Computable-eligibility research classifies which trial criteria can be resolved from EHR data at design time [weng2010; ross2010; kopcke2013; raghavan2015; muqeeth2026], and LLM prescreening emits per-criterion labels with evidence locations at run time, including "no documentation found" as a state distinct from "uncertain" [dohopolski2026]. Bouzinier et al. assert, per decision rule, which evidence types — including method of acquisition — the rule may use, and validate rules prospectively against that specification [bouzinier2026]; Quant ES computes per-variant evidence availability against hashed rule sets before interpretation [saadat2025quantes]. Concurrently with this work, EviBound fixes a protocol-conditioned claim-permission matrix before inference for speech-based screening and blocks claims the protocol does not license [gao2026evibound]. We share the declare-before-inference stance and differ in the unit and the object: we declare derivability per clinical criterion, evaluate it per case against the evidence actually present, treat an acquisition ceiling as censoring of a measured construct relative to a numeric threshold rather than as a categorical permission, and bind the declaration to the result's identity. Inferential validity — whether a measure supports a conclusion — has been proposed as a validity concept for digital measures [tekwe2026]; the criterion map is an executable instance of it.
>
> **Provenance and versioned interpretation.** Provenance capture for clinical data and decision support is mature [w3cprov; curcin2017jbi; gierend2024], AI-CDS guidance requires it [labkoff2024; lekadir2025futureai], and test-dataset guidance requires acquisition documentation, versioning and hashing [homeyer2022]. That definitions change results is documented: successive CQM versions and alternative value sets re-executed on the same data shift measured prevalence [cholan2017amia; cholan2017egems], phenotype edits move incidence rates [makadia2023], and independent teams implementing one cohort description diverge by an order of magnitude [ostropolets2023]. Hash-identified rule sets, clinical assertions and data exist separately [saadat2025quantes; cao2026tracegraph; wack2025gitommix]. What we add is the identity decomposition: source evidence, canonicalization, criterion map and harness each carry a content-addressed identity, the historical result remains reproducible by construction when the map changes, and the cause of any divergence is attributable by comparing digests without re-deriving either result.
>
> **Balance assessment and the OLST.** The Morse Fall Scale [morse1989] and the Berg Balance Scale [berg1992] are the target frameworks. Single-leg stance norms and cut-offs are protocol- and population-dependent [springer2007; bohannon2006; vereeck2008; araujo2022; beauchamp2022; chung2025], ceiling effects are a recognised measurement property [terwee2007; mokkink2010cosmin], and a 10 s ceiling has been noted to hide subtle imbalance [deabreu2024]. The V3 framework validates a digital measure for a context of use [goldsack2020v3; walton2020]. The PhysioNet OLST dataset [copeland2026scidata; copeland2026gaitposture] provides synchronized motion capture, force plates and radar with per-attempt event labels under two acquisition protocols; we use it as a substrate for testing evidence-bounded mapping and replay, and defer outcome claims.

Every bracketed key resolves in the `.bib`. Keys flagged manual (`hl7nullflavor`, `fhirdataabsent`, `w3cprov`, `elyaniv2010`, `ichE9R1`, `fda2023dht`) need venue-style formatting by hand.

---

## 7. Venue implications

Unchanged from the earlier assessment, with one added reason: the neighbours that matter — Curcin 2017, Wack 2025, Weiskopf 2013, Peleg 2013 — are JBI papers, and Cholan, Ostropolets, Mo, Swaminathan, Labkoff, Solomonides are JAMIA. The paper's argument will be read by the community that produced its foils. A rehabilitation or falls venue would ask for the validation the paper deliberately does not offer.

---

## 8. Limits of this checkpoint and what remains before submission

1. **Coverage.** Scopus, Web of Science, IEEE Xplore, ACM DL, Google Scholar, Semantic Scholar and OpenAlex were not searched. Bouzinier 2026 — the closest design-time precedent — was found by a semantic search outside the keyword matrix, which means the matrix is not saturating for contribution 1. Before submission: re-run A5, A8 and the EviBound/Bouzinier terms ("claim permission", "evidence permission", "meta-predicate", "epistemological type", "evidence-bounded", "protocol-aware") on Scopus and Web of Science; forward-citation chase Curcin 2017, Cholan 2017, Goldsack 2020, Watanabe 2026, Bouzinier 2026 and Gao 2026.
2. **Depth.** Relevance-ranked top-N screening for the large-count queries (A1.3, A2.1, A4.3, A6.3, A6.4, A7.1, A7.2) leaves the tail unscreened. Those axes hold foils, not precedents, so the risk is to completeness of citations rather than to the novelty verdict.
3. **Concurrency.** EviBound was posted 2026-08-31 and has no code release yet; it should be cited as a preprint with its date, and checked again at submission for a published version.
4. **Self-consistency.** The rating-3 set is small (8 papers) and each was read; the rating-2 set (108) was screened from abstracts by four independent passes with one verification pass. A second reader over the rating-2 set would tighten §4.
5. **Language and grey literature.** English only; standards and regulatory guidance entered by hand.

---

## 9. Verification of citations carried over from the earlier scan

| Cited as | Resolves to | Assessment |
|---|---|---|
| PMC10746316 (selective clinical information extraction) | Swaminathan et al., *JAMIA* 2023, 10.1093/jamia/ocad182 | Correct; canonical clinical selective-prediction foil [swaminathan2023] |
| PMC10384601 (healthcare provenance literature) | Ahmed et al., *Sensors* 2023, 10.3390/s23146495, systematic review | Correct [ahmed2023] |
| PMC13250854 ("2026 drug-regulatory AI study … criterion-level classifications linked to source") | *Front Med* 2026, 10.3389/fmed.2026.1811333 — LEXI, RAG triage of generic-medicine dossiers against SAHPRA's risk-based quality matrix, GAMP5-validated | Real but weak as a criterion-level-traceability precedent; a regulatory RAG tool, not a clinical criterion evaluator. Not cited in §6 |
| PMC9708586 (test datasets: acquisition protocols, versioning, hashing) | Homeyer et al., *Mod Pathol* 2022, 10.1038/s41379-022-01147-y | Correct; pathology-specific [homeyer2022] |
| ScienceDirect S1746809415001718 (2016 accelerometer BBS) | Badura & Piętka, *Biomed Signal Process Control* 2016, 10.1016/j.bspc.2015.10.005 | Correct [badura2016bbs]; the "2017 balance-board", "2022 IEEE Sensors" and "2025 deep-learning" BBS items from the earlier scan were not individually re-verified; Lu 2025 [lu2025bbs] serves for the last |
| JAMIA 31(11):2730 (AI-CDS guidance) | Labkoff et al., *JAMIA* 2024, 10.1093/jamia/ocae209 | Correct [labkoff2024] |
