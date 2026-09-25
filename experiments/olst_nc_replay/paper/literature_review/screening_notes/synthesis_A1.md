# Synthesis A1 — clinical score automation from sensors (BBS, MFS, SLS/OLST)

Screened 192 records (`screen_A1.json`): 0 rated 3, 15 rated 2, 134 rated 1, 43 rated 0.

## (a) What this literature does / does not do relative to items 1–4

Three families. (i) **BBS automation**: per-item scoring from IMUs/depth cameras (Kim 2021; Eichler 2022) and total-score regression from a proxy task (Yen 2024; Ou 2025; Lu 2025; Zhang 2026). (ii) **SLS automation**: video timing of the one-leg-stance item (Kawa 2018), Kinect SLS as stand-in for the whole BBS (Tripathy 2018), IMU SLS duration (Berg-Hansen 2023), radar OLST on the same PhysioNet cohort (Copeland 2026 ×2). (iii) **MFS automation**: EMR replacement of nurse scoring (Lee 2016), AM-PAC crosswalk to MFS components (Stenum 2025), item-level MFS analysis (Oppegaard 2026).

None decides, per criterion and before prediction, whether the evidence is *capable* of supporting the criterion (item 1). **No paper represents unscorable items as a formal output.** Closest: Lu 2025 states in prose "the inability to predict the score of individual tasks"; Eichler 2022 (full text checked) predicts all 14 item scores and drops tasks by a confidence-threshold stopping rule — predictive value, not observability; Kim 2021 scores all 14. Proxy-regression papers score zero items directly and never say so. No paper separates structural non-evaluability from missing data or uncertainty (item 2); Oppegaard 2026 is a foil because the one MFS item sensors cannot observe (fall history) is the only discriminating item. Protocol censoring (item 3) is absent: the dataset paper (full text checked) uses three cued 4 s attempt windows, with 20 s trials only in the older cohort, and no ceiling/censoring language; the Gait & Posture paper (paywalled) treats short trials only as a feature source. Versioned criterion-map replay (item 4) is absent.

## (b) Records to cite

- `10.3390/s21227628` — Kim 2021, Sensors — neighbour: per-task IMU scoring of all 14 BBS items.
- `10.1007/bf00116251` (mismatched; verified DOI 10.3390/s22041557) — Eichler 2022, Sensors — neighbour: 14-item depth-camera scoring; task reduction by confidence, not admissibility.
- `10.3390/bioengineering12040395` — Lu 2025, Bioengineering — foil: BBS total from walking; item non-scorability only as prose limitation.
- `10.1109/jbhi.2025.3543095` — Zhang 2026, IEEE JBHI — foil: BBS regressed from mocap TUG (construct substitution).
- `10.3389/fbioe.2025.1703500` — Ou 2025, Front Bioeng Biotech — foil: insole regression of BBS total (duplicate key `10.1016/j.knosys.2024.112835`).
- `10.1016/j.compmedimag.2017.07.003` — Kawa 2018, Comput Med Imaging Graph — neighbour: automates only the one-leg-stance item duration.
- `10.1109/embc.2018.8513263` — Tripathy 2018, EMBC — foil: SLS alone mapped to BBS fall-risk category.
- `10.1109/embc44109.2020.9176827` (mismatched DOI) — Berg-Hansen 2023, Front Neurol — neighbour: instrumented SLS with automated duration.
- `10.1093/intqhc/mzv122` — Lee 2016, Int J Qual Health Care — foil: replaces MFS rather than mapping evidence to its criteria.
- `10.1111/jocn.17098` — Stenum 2025, J Clin Nurs — neighbour: item-level crosswalk to MFS components succeeds only 40%.
- `10.1016/j.jamda.2026.106160` — Oppegaard 2026, JAMDA — foil: modality-unobservable item carries the MFS signal.
- `10.1038/s41597-026-06831-1` — Copeland 2026, Sci Data — canonical dataset (duplicate key `10.1038/s41597-025-05113-6` is mismatched).
- `10.1016/j.gaitpost.2026.110108` — Copeland 2026, Gait & Posture — neighbour: radar OLST, short vs long trials.

## (c) Verdict

Nothing in A1 threatens items 1–4 or the taxonomy. Eichler 2022, Lu 2025 and Stenum 2025 touch item-level scorability only as accuracy tables or prose limitations, never as a declared, machine-readable admissibility class. The dataset's own papers do not treat the 4 s window as censoring the ≥10 s threshold.

## (d) Possibly missing (unverified)

- Araujo et al. 2022, Br J Sports Med, 10-second one-legged stance and survival (cited by the Sci Data paper) — canonical 10 s threshold.
- Berg 1992 (BBS), Morse 1989 (MFS) — instrument sources.
- Several keys carry mismatched DOIs (Eichler, Berg-Hansen, Ou, Copeland Sci Data); verify before citing.
