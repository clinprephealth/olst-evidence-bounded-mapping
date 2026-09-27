#!/usr/bin/env bash
# Build the public research release tree for the OLST/NC replay benchmark.
#
# The experimental freeze is the tag olst-nc-replay-artifact-2026-09-10 on the
# development repository. This script produces the *public* tree from a later
# commit: the same scientific artifacts, plus documentation, figures and the
# literature checkpoint, minus internal platform material. The science does not
# change between the two; the packaging does. Layout mirrors the repository
# (experiments/, tests/, artifacts/, pytest.ini) so the tests and the store
# resolve paths exactly as they do in development.
#
# Usage (from the repository root):
#   bash experiments/olst_nc_replay/release/make_public_release.sh <output_dir>
#
# Afterwards, from <output_dir>:
#   python -m pytest -q            # 165 tests; no PhysioNet data required
#
# Excluded on purpose (internal platform material or superseded documents):
#   experiments/olst_nc_replay/substrate_adapter.py
#   experiments/olst_nc_replay/paper/appendix_substrate.md
#   experiments/olst_nc_replay/paper/paper.md          (May 2026 draft, superseded)
#   tests/test_olst_substrate_adapter.py
# Licensing is decided: Apache-2.0 on code/tests; CC BY 4.0 on the manuscript,
# original figures, and dataset-derived fixtures/results (with PhysioNet OLST
# attribution). The public-package assembler writes those files; this script
# still warns if LICENSE is absent so a bare extraction is not silently unlicensed.

set -euo pipefail

OUT="${1:?output directory required}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$ROOT/experiments/olst_nc_replay"

if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  echo "refusing: $OUT exists and is not empty" >&2
  exit 2
fi
mkdir -p "$OUT/experiments/olst_nc_replay" "$OUT/tests" "$OUT/artifacts"

# 1. experiment package (rsync excludes are relative to SRC)
rsync -a \
  --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store' \
  --exclude 'substrate_adapter.py' \
  --exclude 'paper/appendix_substrate.md' \
  --exclude 'paper/paper.md' \
  "$SRC/" "$OUT/experiments/olst_nc_replay/"

# 2. tests: OLST suites only, minus the substrate adapter test
for t in "$ROOT"/tests/test_olst_*.py; do
  case "$(basename "$t")" in
    test_olst_substrate_adapter.py) continue ;;
  esac
  cp "$t" "$OUT/tests/"
done

# 3. artifacts: store snapshot and per-context summaries
rsync -a --exclude '.DS_Store' "$ROOT/artifacts/olst_lakehouse/" "$OUT/artifacts/olst_lakehouse/"
cp "$ROOT"/artifacts/olst_full_corpus_*.json "$OUT/artifacts/"
cp "$ROOT"/artifacts/olst_nc_*.json "$OUT/artifacts/"

# 4. test configuration and top-level pointer
cat > "$OUT/pytest.ini" <<'EOF'
[pytest]
testpaths = tests
pythonpath = .
addopts = --tb=short -q
EOF

cat > "$OUT/README.md" <<'EOF'
# OLST / NC replay benchmark — public research release

Deterministic, content-addressed mapping of the public PhysioNet One-Legged
Stand Test dataset onto clinical-framework criteria with explicit
non-evaluable reasons and protocol censoring instead of imputation.

Start at `experiments/olst_nc_replay/README.md` (operational guide) and
`experiments/olst_nc_replay/protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md`
(the dated laboratory record). The executed manuscript draft is
`experiments/olst_nc_replay/paper/OLST_MANUSCRIPT_EXECUTED_v3.md`.

Verify the artifact without the dataset:

    python -m pytest -q

Nothing here predicts falls or is intended for clinical use. The PhysioNet
dataset is not redistributed; see the operational guide for what to obtain
and how it is verified.
EOF

# 5. hygiene checks. Platform-specific tokens only: the English word
# "substrate" is used generically in the manuscript and literature review.
# The frozen pre-submission plan is expected to match (three historical lines
# naming internal projects); it is preregistration evidence and is kept.
PAT='substrate_adapter|appendix_substrate|EvidencePackV1|HomeField|ProvenanceOS|ClinPrep|dpg-platform|DPG Substrate'
hits=$(grep -rIl -E "$PAT" "$OUT" --exclude-dir=olst_lakehouse --exclude='*.json' --exclude='make_public_release.sh' || true)
if [ -n "$hits" ]; then
  echo "NOTE: platform-specific tokens found in (review before deposit):" >&2
  echo "$hits" >&2
fi
[ -f "$OUT/LICENSE" ] || echo "NOTE: no LICENSE in $OUT (expected Apache-2.0 / CC BY 4.0 files in the public package)." >&2

# 6. manifest
( cd "$OUT" && find . -type f ! -name MANIFEST.sha256 | LC_ALL=C sort | xargs shasum -a 256 > MANIFEST.sha256 )
echo "public release tree written to $OUT"
echo "  files: $(wc -l < "$OUT/MANIFEST.sha256")   size: $(du -sh "$OUT" | cut -f1)"
