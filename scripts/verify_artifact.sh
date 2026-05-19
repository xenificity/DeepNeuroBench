#!/usr/bin/env bash
#
# verify_artifact.sh
# ==================
#
# One-command offline reproducibility check for the DeepNeuroBench
# IISWC 2026 artifact. Runs:
#
#   1. The Algorithm 1 unit-test suite (87 tests, ~0.5 s)
#   2. The Table 3 consistency tests (8 tests)
#   3. CLI smoke tests for src/recommend_cluster.py covering all
#      five benchmark datasets (DS-I .. DS-V)
#
# The script intentionally does **not** attempt to spin up FABRIC
# slices or run DeepPrep itself -- those steps require an external
# testbed account and ~24 h per run, and are documented separately in
# the main README.
#
# Exit status: 0 on full success; non-zero if any check fails.

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# --- Pretty-printing -------------------------------------------------------
GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YEL=$'\033[0;33m'; RST=$'\033[0m'
ok()   { printf '%s[OK]%s   %s\n' "$GREEN" "$RST" "$1"; }
warn() { printf '%s[WARN]%s %s\n' "$YEL" "$RST" "$1"; }
fail() { printf '%s[FAIL]%s %s\n' "$RED" "$RST" "$1"; exit 1; }

printf '======================================================================\n'
printf 'DeepNeuroBench artifact verification (IISWC 2026)\n'
printf '======================================================================\n'

# --- Prereq: Python 3.8+ ---------------------------------------------------
PY=${PYTHON:-python3}
if ! command -v "$PY" >/dev/null 2>&1; then
    fail "python3 not found on PATH (set \$PYTHON to override)"
fi
PY_VER=$($PY -c 'import sys; print("%d.%d" % sys.version_info[:2])')
ok "Python $PY_VER detected ($PY)"

# --- Prereq: pytest --------------------------------------------------------
if ! $PY -c 'import pytest' 2>/dev/null; then
    warn "pytest not installed; installing into user site-packages..."
    $PY -m pip install --user --quiet pytest \
        || fail "Failed to install pytest. Try: $PY -m pip install pytest"
fi
ok "pytest available"

# --- Step 1: full test suite ----------------------------------------------
printf '\n--- [1/3] Running unit tests ----------------------------------------\n'
$PY -m pytest tests/ -q --color=no --basetemp="${TMPDIR:-/tmp}/dnb-pytest" \
    || fail "Unit tests failed -- see output above"
ok "All unit tests passed"

# --- Step 2: Algorithm 1 CLI smoke tests ----------------------------------
printf '\n--- [2/3] Algorithm 1 CLI smoke (DS-I .. DS-V) ----------------------\n'

declare -A CASES=(
    ["DS-I:0.45:makespan"]="C2"
    ["DS-II:inf:co2"]="C2"
    ["DS-III:0.22:energy"]="C2"
    ["DS-IV:0.19:cost"]="C3"
    ["DS-V:0.013:makespan"]="C1"
    ["intermediate:0.05:energy"]="C4"
    ["intermediate:0.10:power"]="C4"
)

for key in "${!CASES[@]}"; do
    IFS=':' read -r ds R prio <<< "$key"
    expected=${CASES[$key]}
    got=$($PY src/recommend_cluster.py --R "$R" --priority "$prio" --json \
          | $PY -c 'import json,sys; print(json.load(sys.stdin)["cluster_id"])')
    if [[ "$got" == "$expected" ]]; then
        ok "$ds  R=$R  priority=$prio  ->  $got"
    else
        fail "$ds  R=$R  priority=$prio  ->  $got (expected $expected)"
    fi
done

# --- Step 3: Required files exist -----------------------------------------
printf '\n--- [3/3] Artifact completeness check -------------------------------\n'

REQUIRED_FILES=(
    "src/recommend_cluster.py"
    "tests/test_recommend_cluster.py"
    "tests/test_table3_consistency.py"
    "results/table2_morphology.csv"
    "results/table3_metrics.csv"
    "config/deepprep.slurm.cpu.config"
    "config/deepprep.slurm.gpu.config"
    "stats/deepPrep.sh"
    "stats/deepPrep_gpu.sh"
    "stats/power-plot.py"
    "stats/run_pstat.py"
    "stats/run_dstat.py"
    "stats/run_gpu_stat.py"
    "pynb/DeepPrep_Cluster_Creation.ipynb"
)
missing=0
for f in "${REQUIRED_FILES[@]}"; do
    if [[ -e "$f" ]]; then
        ok "exists: $f"
    else
        printf '%s[FAIL]%s missing: %s\n' "$RED" "$RST" "$f"
        missing=$((missing + 1))
    fi
done

if (( missing > 0 )); then
    fail "$missing required artifact file(s) are missing"
fi

printf '\n======================================================================\n'
printf '%s[SUCCESS]%s All offline reproducibility checks passed.\n' "$GREEN" "$RST"
printf '======================================================================\n'
printf 'For the full FABRIC + DeepPrep execution path, see README.md\n'
printf 'sections "Setup (Steps 1-11)" and "Running the Experiments".\n'
