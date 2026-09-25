# Step 0.5 — protocol freeze

Preregistration record for the OLST pre-submission protocol. Created **before** any D1 duration-distribution analysis. The manuscript and plan in this directory are frozen byte-identical to the Downloads drafts listed below. Do not edit those two files in place; any later change is a dated amendment.

## Frozen files

| File | SHA-256 |
| --- | --- |
| `OLST_MANUSCRIPT_DRAFT.md` | `8269444a132da002d8386b760d91f7de336a5ea37a61617fd5d1fb3f9c28f41a` |
| `OLST_PRESUBMISSION_PLAN3.md` | `4ade8845f132da647849c13263b558ef9723f188a4e7e13d897f7da2ed8acd89` |

The git commit SHA that introduced these two files (the freeze commit) is recorded below after that commit exists. It is **not** written into the manuscript or plan, because filling `[[FILL]]` inside the plan would change the plan's digest.

- **Freeze commit:** `af1fc973ea05c6a56796856aad58a0d99e7f3691`
- **Worktree:** `/Users/michaelpryder/dev-olst`
- **Branch:** `feature/olst-nc-replay-execution`
- **Parent:** `14607e3ea7002232b41fc1c822e4940d106cc207`

## D1 script (outside the repo)

The D1 computation lives outside this repo, as specified by the plan:

- Path: `/Users/michaelpryder/Downloads/d1_duration_distributions.py`
- SHA-256: `d01c2fcd22e36d746a9aa2bf7c334677cc8353a77b26c4157fd072dd00709dab`

Headers in that script were aligned to PhysioNet OLST 1.0 `Metadata/` column names before freeze. The two duration definitions were not changed:

- `stable_phase_s = t_break - t_stable`
- `stance_s = t_end - t_foot_up`

Do not run it until this freeze commit exists.

## D2–D4 as of this freeze

Decided at this freeze; change only via dated amendment if D1 outcome (b) forces it.

- **D2:** `best_of_attempts = max(duration)` per capture; evaluable only when every attempt in the capture has the field.
- **D3:** Morse gait reclassified from `derivable` to `partial` in v2.
- **D4:** keep 10 s / 5 s on the corrected construct; do not tune.
- **D1:** not yet resolved. Strict `t_break - t_stable` leaves final-attempt rows without `t_break` as missing; harness v1 used `t_end` on `is_attempt_final`. That definitional choice is part of reading the D1 output, not a silent rewrite of the script.

## Amendments after this freeze

- **2026-09-09** — `AMENDMENT_2026-09-09_D1_RESOLUTION.md`: D1 resolved (construct correction with protocol censoring D4a, attempt-window integrity D2a). D2–D4 unchanged.
