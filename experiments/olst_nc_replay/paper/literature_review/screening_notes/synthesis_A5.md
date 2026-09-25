# Synthesis A5 — criterion-level traceability; computable eligibility; CQL/eCQM/CIG data requirements

147 records (screen_A5.json): 1×3, 16×2, 43×1, 87 noise. Preprint/journal duplicates and mislinked DOIs rated 1 with pointer to canonical key; several input keys carry the wrong DOI (flagged in `why`) — verify before citing.

## (a) What this literature does and does not do

The computable-eligibility strand asks a design-time, population-level question: which criteria's data elements exist in the EHR, how complete they are, how complex the logic is. Answers are availability/completeness audits (von Lucadou; Vass; Girardeau; Doods), concept-to-data-element mappings (Zhang 2018) and, newest, an LLM tiering of criteria by "EHR predictability" (Muqeeth 2026). Raghavan 2015 is closest to the modality argument — structured data alone cannot resolve 59–77% of criteria — but as an empirical finding, not a class a system emits. None emits, per criterion and per case, a machine-readable evaluability verdict with a reason; all treat unavailability as missing data or "needs specialised testing". No record separates modality, construct and protocol insufficiency; item 3 is absent from this axis.

At runtime, LLM matchers (Dohopolski 2026; TrialMatchAI; Sum-of-Checks) produce criterion-level labels with rationale and evidence pointers — the runtime half of item 1. Dohopolski (full text read) labels "no documentation found" distinct from "uncertain", versions criterion prompts under human approval and preserves historical outputs. This is the closest operationalised absent-vs-unknown split, but it is post-hoc ordinary missingness, not structural non-evaluability declared ahead of time (item 2), and its versioning is audit logging without identity decomposition or divergence attribution (item 4).

CQL/eCQM/CIG records are canonical references only: artefacts that declare data requirements (Arden MLM data slots; PheRM desiderata; four-level eCQM decomposition; layered CIG customisation) plus one demonstration that editing a phenotype definition changes results (Makadia). They are item-4 foils: versioned artefacts without separate measurement/interpretation/implementation identities.

## (b) Records to cite

- pmid:42317858 — Muqeeth 2026, AMIA Summits — partial precedent (item 1): design-time tiers of eligibility concepts by EHR inferability; population-level, no per-case output or structural reason. Abstract-only verification (PMC blocked).
- 10.64898/2026.03.20.26348890 — Dohopolski 2026, medRxiv — neighbour/foil: per-criterion status incl. "no documentation found", rationale, evidence locations, versioned prompts; post hoc.
- arxiv:1502.04049v1 — Raghavan 2015, arXiv — foil: per-criterion resolvability by data source, observed not declared.
- 10.1093/jamia/ocv112 — Mo 2015, JAMIA — canonical-ref: computable phenotype desiderata incl. site data availability.
- 10.3233/shti220046 — Vass 2022, Stud Health Technol Inform — neighbour: per-criterion-class data completeness.
- 10.1093/ije/20.4.1057 (mislinked) — von Lucadou 2019, BMC Med Inform Decis Mak — neighbour: per-criterion EHR availability audit.
- 10.2196/49347 — Blasini 2024, JMIR Form Res — neighbour: some criteria assessable only at enrolment.
- arxiv:2406.16830v2 — Benz 2024, arXiv — foil (item 2): missing eligibility variables as statistical missingness.
- 10.1093/jamiaopen/ooad096 — Makadia 2023, JAMIA Open — foil (item 4): definition edits shift results, no replay identity.
- 10.1177/1460458218813705 — Fux 2020, Health Informatics J — neighbour (item 4): primary vs local-customisation layers.
- 10.1016/j.artmed.2016.08.001 — Jenders 2018, Artif Intell Med — canonical-ref: Arden MLMs declare required data.
- arxiv:2604.22156v1 — You 2026, arXiv/IJCARS — neighbour: criterion decomposed into justified checks.

Optional (rated 2): 10.1038/s41467-026-70509-w; 10.1055/s-0039-3402755; 10.1186/1472-6947-13-37; pmid:30815206; 10.1097/jhq.0000000000000467.

## (c) Verdict

Nothing in A5 threatens items 2–4 or the taxonomy. Item 1 is partially anticipated in two halves: design-time (which criteria are evaluable from this source) by Muqeeth 2026 and the availability audits; runtime (per-criterion label, evidence pointers, distinct "no evidence" state) by Dohopolski 2026 and TrialMatchAI. No record combines both, none emits a per-criterion evaluability class with a structural reason as machine-readable output, none targets a clinical instrument scored from sensors. Position item 1 against Muqeeth (population tiering → per-criterion declaration with reasons) and Dohopolski ("no documentation found" → structural non-evaluability).

## (d) Possibly missing (unverified)

- Weng C et al., formal representations of eligibility criteria review, JBI 2010.
- Ross J, Tu S, Carini S, Sim I, eligibility criteria complexity, AMIA Summits 2010.
- Köpcke F et al., EHR data completeness for trial recruitment, BMC MIDM 2013.
- Yuan C et al., Criteria2Query, JAMIA 2019.
- Peleg M, computer-interpretable guidelines methodological review, JBI 2013.
- Hripcsak G et al., rationale for the Arden Syntax, Comput Biomed Res 1994.
