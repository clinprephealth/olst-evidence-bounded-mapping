# Synthesis A6 — measurement/acquisition compatibility

Screened 326 records (`screen_A6.json`): 2 rated 3 (one paper, two keys), 16 rated 2, 105 rated 1, 203 rated 0.

## (a) What this literature does / does not do relative to items 1–4

**Canonical V3 / fit-for-purpose references present:** Goldsack 2020 V3 (`10.1038/s41746-020-0260-4`; duplicate key `10.1038/s41746-019-0084-2` mismatched); Bakker 2025 V3+ (`10.1038/s41746-024-01322-2`; duplicate `10.1186/s12889-021-12393-1` mismatched); Walton 2020 evidence dossier (concept of interest, context of use); Manta 2021 EVIDENCE; Manta 2020 "measures that matter"; Roussos 2022 sources of variability; Hill 2022 DHT metadata. All validate a *measure* for a *context of use* at instrument level; none decides per criterion whether a modality/protocol can support it (item 1) or separates structural non-evaluability from missing data (item 2). Hill 2022 pre-specifies acquisition metadata bound to COI/COU — documentation, not admissibility. Galanty 2024 and Clark 2026 (Bridge2AI) require acquisition/provenance documentation of AI datasets; neither gates which criteria may be adjudicated. Kalokyri 2025 (AI Model Passport) is provenance-space work the paper disclaims; nothing versions a clinical mapping with divergence attribution (item 4).

**Protocol ceiling as censoring:** one record treats maximum trial duration as limiting which clinical distinctions can be made. de Abreu 2024 (full text checked): 30 s max-duration stances; "setting the ceiling test period at 10 s may be useful for patients with evident balance impairment but may not be useful for identifying those with subtle imbalance"; recommends ≥23 s. This is item 3's premise as protocol advice — no withheld label, censoring never named. Adjacent: Vereeck 2008 (10 s/30 s limits, age ceilings); Oliveira 2018 (time-limit capped at 30 s); Chiu 2026 (child OLST norms hit 30 s, SD 0). The only explicit censoring model (Haab 2026) is a wastewater time-to-detection sensor.

**Construct validity:** Ringhof & Stein 2018 (Verbecque 2021 in children) show balance tests are task-specific and non-interchangeable — psychometric support for construct insufficiency.

## (b) Records to cite

- `10.1038/s41746-020-0260-4` — Goldsack 2020, NPJ Digit Med — canonical foil (V3).
- `10.1038/s41746-024-01322-2` — Bakker 2025, NPJ Digit Med — canonical foil (V3+).
- `10.1016/j.cct.2020.105962` — Walton 2020, Contemp Clin Trials — canonical-ref, COI/COU vocabulary.
- `10.1586/17434440.2016.1153421` (mismatched DOI) — Roussos 2022, NPJ Digit Med — neighbour: acquisition as variability.
- `10.1038/s41598-021-91633-1` (mismatched DOI) — Hill 2022, Sensors — neighbour: pre-specified acquisition metadata.
- `10.1186/s12877-024-05380-9` — de Abreu 2024, BMC Geriatr — precedent for item 3's premise, not its mechanism.
- `10.1080/14992020701689688` — Vereeck 2008, Int J Audiol — neighbour: 10 s/30 s time-limit dichotomization.
- `10.1371/journal.pone.0167456` — Oliveira 2018, PLoS One — neighbour: 30 s-capped time-limit variable.
- `10.1519/00139143-200704000-00003` — Springer 2007, J Geriatr Phys Ther — canonical normative UPST values.
- `10.1016/j.jamda.2025.105773` — Chung 2025, JAMDA — canonical nationwide OLS norms.
- `10.1093/ageing/afac095` — Beauchamp 2022, Age Ageing — canonical: SLS cut-offs vary by age/sex.
- `10.1016/j.apmr.2004.11.005` (mismatched DOI) — Chomiak 2015, J Clin Med Res — ~10 s SLST threshold reference.
- `10.1016/j.humov.2018.02.004` — Ringhof 2018, Hum Mov Sci — neighbour: balance tests are not one construct.
- `10.1038/s41467-020-17478-w` (mismatched DOI) — Galanty 2024, Sci Rep — neighbour: dataset documentation audit.
- `10.60775/fairhub.3` — Clark 2026, bioRxiv — neighbour: Bridge2AI AI-readiness metadata.

## (c) Verdict

No record threatens items 1, 2, 4 or the taxonomy. Item 3 is partially anticipated in premise by **de Abreu 2024** (`10.1186/s12877-024-05380-9`): a 10 s ceiling cannot identify subtle imbalance. Cite it; position protocol censoring as the operationalization (withhold the label, name the ceiling, per participant and criterion) of what it states as protocol advice.

## (d) Possibly missing (unverified)

- Araujo et al. 2022, Br J Sports Med, 10-second OLS and survival — canonical 10 s threshold.
- FDA 2023 DHT remote-data-acquisition guidance; FDA-NIH BEST Resource (2016) — regulatory CoU sources.
- Bohannon 1984 single-limb stance norms — cited by de Abreu.
- Mismatched DOIs on several keys (flagged above); verify before citing.
