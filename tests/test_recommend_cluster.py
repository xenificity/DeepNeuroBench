"""
Unit tests for Algorithm 1 (``src/recommend_cluster.py``).

These tests verify two things:

1. The implementation reproduces the **makespan-optimal cluster**
   reported in Table 2 of the manuscript for all five benchmark
   datasets (DS-I .. DS-V), including the two boundary regimes
   (DS-II at R = inf, DS-V at R = 0.013).

2. The priority-dependent branches of Algorithm 1 select the cluster
   stated in the paper:
       - P = makespan -> C2 (except R < 0.02 -> C1)
       - P = co2      -> C2 (except R < 0.02 -> C1)
       - P = energy   -> C2 if R >= 0.15 else C4 (except R < 0.02 -> C1)
       - P = power    -> C4                       (except R < 0.02 -> C1)
       - P = cost     -> C3                       (except R < 0.02 -> C1)

The test suite has **no third-party dependencies** beyond ``pytest``;
it can be invoked from a fresh virtualenv with ``pip install pytest``.
"""

from __future__ import annotations

import math
import os
import struct
import tempfile
from pathlib import Path

import pytest

from recommend_cluster import (
    CLUSTERS,
    PRIORITIES,
    R_FMRI_DOMINANT,
    R_SMRI_DOMINANT,
    compute_morphology_ratio,
    recommend_cluster,
)


# ---------------------------------------------------------------------------
# Table 2 — five-dataset ground truth (paper, page 4)
# ---------------------------------------------------------------------------
#
# DS    R       Optimal (minimum-makespan)
# ----  ------  --------------------------
# DS-I  0.45    C2
# DS-II inf     C2
# DS-III 0.22   C2
# DS-IV 0.19    C2
# DS-V  0.013   C1
# ---------------------------------------------------------------------------

PAPER_TABLE2 = [
    ("DS-I",   0.45,       "C2"),
    ("DS-II",  math.inf,   "C2"),
    ("DS-III", 0.22,       "C2"),
    ("DS-IV",  0.19,       "C2"),
    ("DS-V",   0.013,      "C1"),
]


@pytest.mark.parametrize("dataset,R,expected", PAPER_TABLE2)
def test_table2_optimal_makespan(dataset, R, expected):
    """Algorithm 1 must reproduce Table 2's Optimal column under
    priority = 'makespan' for every benchmark dataset."""
    rec = recommend_cluster(R, priority="makespan")
    assert rec.cluster_id == expected, (
        f"{dataset}: R={R} -> expected {expected}, got {rec.cluster_id}"
    )


# ---------------------------------------------------------------------------
# Algorithm-1 branch coverage
# ---------------------------------------------------------------------------

class TestFmriDominantBranch:
    """R < 0.02 always routes to C1, regardless of priority."""

    @pytest.mark.parametrize("priority", PRIORITIES)
    @pytest.mark.parametrize("R", [0.0, 0.005, 0.013, 0.019])
    def test_extreme_fmri_dominant_always_c1(self, R, priority):
        rec = recommend_cluster(R, priority=priority)
        assert rec.cluster_id == "C1", (
            f"R={R} priority={priority} should route to C1 "
            f"(fMRI-dominant branch), got {rec.cluster_id}"
        )

    def test_boundary_R_equals_002_is_not_fmri_dominant(self):
        """R = 0.02 is the *boundary*; per Algorithm 1 it is **not**
        < 0.02, so it must fall through to the priority-dependent
        branch."""
        rec = recommend_cluster(R_FMRI_DOMINANT, priority="makespan")
        assert rec.cluster_id == "C2"


class TestSmriLeaningBranch:
    """R >= 0.15 routes by priority, with energy -> C2."""

    @pytest.mark.parametrize("R", [0.15, 0.22, 0.45, 1.0, math.inf])
    def test_makespan_picks_c2(self, R):
        assert recommend_cluster(R, "makespan").cluster_id == "C2"

    @pytest.mark.parametrize("R", [0.15, 0.22, 0.45, 1.0, math.inf])
    def test_co2_picks_c2(self, R):
        assert recommend_cluster(R, "co2").cluster_id == "C2"

    @pytest.mark.parametrize("R", [0.15, 0.22, 0.45, 1.0, math.inf])
    def test_energy_picks_c2(self, R):
        assert recommend_cluster(R, "energy").cluster_id == "C2"

    @pytest.mark.parametrize("R", [0.15, 0.22, 0.45, 1.0, math.inf])
    def test_power_picks_c4(self, R):
        assert recommend_cluster(R, "power").cluster_id == "C4"

    @pytest.mark.parametrize("R", [0.15, 0.22, 0.45, 1.0, math.inf])
    def test_cost_picks_c3(self, R):
        assert recommend_cluster(R, "cost").cluster_id == "C3"


class TestIntermediateBranch:
    """0.02 <= R < 0.15 routes by priority, with energy -> C4."""

    @pytest.mark.parametrize("R", [0.02, 0.05, 0.10, 0.149])
    def test_makespan_picks_c2(self, R):
        assert recommend_cluster(R, "makespan").cluster_id == "C2"

    @pytest.mark.parametrize("R", [0.02, 0.05, 0.10, 0.149])
    def test_co2_picks_c2(self, R):
        assert recommend_cluster(R, "co2").cluster_id == "C2"

    @pytest.mark.parametrize("R", [0.02, 0.05, 0.10, 0.149])
    def test_energy_picks_c4(self, R):
        """Manuscript line 11 of Algorithm 1: in this regime, energy -> C4."""
        assert recommend_cluster(R, "energy").cluster_id == "C4"

    @pytest.mark.parametrize("R", [0.02, 0.05, 0.10, 0.149])
    def test_power_picks_c4(self, R):
        assert recommend_cluster(R, "power").cluster_id == "C4"

    @pytest.mark.parametrize("R", [0.02, 0.05, 0.10, 0.149])
    def test_cost_picks_c3(self, R):
        assert recommend_cluster(R, "cost").cluster_id == "C3"


# ---------------------------------------------------------------------------
# Aliases / case-insensitivity
# ---------------------------------------------------------------------------

class TestPriorityAliases:

    def test_carbon_is_co2(self):
        assert recommend_cluster(0.5, "carbon").cluster_id \
            == recommend_cluster(0.5, "co2").cluster_id

    def test_carbon_footprint_is_co2(self):
        assert recommend_cluster(0.5, "carbon_footprint").cluster_id \
            == recommend_cluster(0.5, "co2").cluster_id

    def test_runtime_is_makespan(self):
        assert recommend_cluster(0.5, "runtime").cluster_id \
            == recommend_cluster(0.5, "makespan").cluster_id

    def test_case_insensitive(self):
        assert recommend_cluster(0.5, "MAKESPAN").cluster_id == "C2"
        assert recommend_cluster(0.5, "Cost").cluster_id == "C3"


# ---------------------------------------------------------------------------
# Φ(C*) — config-profile mapping
# ---------------------------------------------------------------------------

class TestConfigProfile:

    def test_c2_uses_gpu_config(self):
        rec = recommend_cluster(0.5, "makespan")
        assert rec.config_profile.endswith("deepprep.slurm.gpu.config")

    @pytest.mark.parametrize("cluster,priority,R", [
        ("C1", "makespan", 0.005),
        ("C3", "cost",     0.5),
        ("C4", "power",    0.5),
    ])
    def test_cpu_clusters_use_cpu_config(self, cluster, priority, R):
        rec = recommend_cluster(R, priority)
        assert rec.cluster_id == cluster
        assert rec.config_profile.endswith("deepprep.slurm.cpu.config")

    def test_config_profile_paths_exist(self):
        """Each cluster's declared config profile must actually be a
        file in the artifact (otherwise reproducibility is broken)."""
        repo_root = Path(__file__).resolve().parent.parent
        for cid, profile in CLUSTERS.items():
            cfg = repo_root / profile.config_profile
            assert cfg.exists(), \
                f"Config profile for {cid} not found at {cfg}"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:

    def test_unknown_priority_raises(self):
        with pytest.raises(ValueError):
            recommend_cluster(0.5, "throughput")

    def test_negative_R_raises(self):
        with pytest.raises(ValueError):
            recommend_cluster(-0.1, "makespan")

    def test_nan_R_raises(self):
        with pytest.raises(ValueError):
            recommend_cluster(float("nan"), "makespan")


# ---------------------------------------------------------------------------
# compute_morphology_ratio — exercised on a tiny synthetic BIDS layout
# ---------------------------------------------------------------------------

def _make_fake_nifti(path: Path, n_bytes: int) -> None:
    """Create a stub file of the requested size; the contents don't
    matter for size-based R computation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(b"\0" * n_bytes)


class TestMorphologyRatio:

    def test_ratio_matches_expected_value(self, tmp_path):
        """Build a fake BIDS tree with known sMRI/fMRI sizes and verify
        that the computed R equals the analytical ratio."""
        # 10 MB average T1w, 50 MB average BOLD => R = 0.2
        for sub in (1, 2):
            _make_fake_nifti(
                tmp_path / f"sub-{sub:02d}" / "anat" / f"sub-{sub:02d}_T1w.nii.gz",
                10 * 1024 * 1024,
            )
            _make_fake_nifti(
                tmp_path / f"sub-{sub:02d}" / "func"
                / f"sub-{sub:02d}_task-rest_bold.nii.gz",
                50 * 1024 * 1024,
            )

        R = compute_morphology_ratio(tmp_path)
        assert R == pytest.approx(0.2, rel=1e-9)

    def test_no_fmri_returns_inf(self, tmp_path):
        _make_fake_nifti(
            tmp_path / "sub-01" / "anat" / "sub-01_T1w.nii.gz", 1024,
        )
        assert math.isinf(compute_morphology_ratio(tmp_path))

    def test_missing_t1w_raises(self, tmp_path):
        _make_fake_nifti(
            tmp_path / "sub-01" / "func" / "sub-01_task-rest_bold.nii.gz",
            1024,
        )
        with pytest.raises(ValueError):
            compute_morphology_ratio(tmp_path)

    def test_end_to_end_round_trip(self, tmp_path):
        """Build an fMRI-dominant dataset and verify that the pipeline
        compute_R -> recommend_cluster returns the same answer the paper
        gives for DS-V."""
        # ~3.4 MB T1w, ~410 MB bold -> R ~= 0.0083 (< 0.02)
        for sub in (1, 2):
            _make_fake_nifti(
                tmp_path / f"sub-{sub:02d}" / "anat" / f"sub-{sub:02d}_T1w.nii.gz",
                int(3.4 * 1024 * 1024),
            )
            _make_fake_nifti(
                tmp_path / f"sub-{sub:02d}" / "func"
                / f"sub-{sub:02d}_task-rest_bold.nii.gz",
                int(410 * 1024 * 1024),
            )
        R = compute_morphology_ratio(tmp_path)
        assert R < R_FMRI_DOMINANT
        rec = recommend_cluster(R, "makespan")
        assert rec.cluster_id == "C1"


# Suppress an unused-import warning for `struct` and `os` (kept to make
# extending these tests with NIfTI header introspection easier).
_ = (struct, os)
