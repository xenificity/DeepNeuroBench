#!/usr/bin/env python3
"""
recommend_cluster.py
====================

Reference implementation of **Algorithm 1** from the IISWC 2026 paper
*A Benchmark for Cost and Energy-Efficient Execution of Neuroimaging
Workflows on Commodity Clusters* (DeepNeuroBench).

Given a dataset's morphology ratio ``R = avg(sMRI scan size) / avg(fMRI
scan size)`` and a user-specified priority ``P`` (one of ``makespan``,
``power``, ``energy``, ``co2``, ``cost``), the function
:func:`recommend_cluster` returns the recommended cluster identifier
``C*`` and the matching Nextflow/Slurm configuration profile
``Phi(C*)`` (a relative path inside this repository).

The algorithm is reproduced verbatim from the paper below; see
``tests/test_recommend_cluster.py`` for case-by-case verification
against Table 2 of the manuscript.

::

    Algorithm 1  Multi-Criteria sMRI/fMRI Optimal Cluster Configuration
        Input : R = s_sMRI / s_fMRI  (R := inf if no fMRI)
                P in {makespan, power, energy, co2, cost}
                C = {C1, C2, C3, C4}
        Output: Recommended cluster C* and config profile Phi(C*)

         1: Compute R from input dataset
         2: if R < 0.02 then
         3:     C* <- C1                    # fMRI-dominant
         4: else
         5:     if P == makespan or P == co2:
         6:         C* <- C2                # GPU
         7:     elif P == energy:
         8:         if R >= 0.15: C* <- C2
         9:         else:         C* <- C4
        10:     elif P == power:
        11:         C* <- C4
        12:     elif P == cost:
        13:         C* <- C3
        14: end if
        15: Build profile Phi(C*) with CPU, GPU and memory allocations
        16: return (C*, Phi(C*))

This module intentionally has **zero third-party runtime dependencies**
so that reviewers can run it on a stock Python 3.8+ install without any
``pip install`` step.

Usage (CLI)
-----------

.. code-block:: console

    # Direct R value:
    $ python3 src/recommend_cluster.py --R 0.45 --priority makespan
    Recommended cluster : C2   (GPU-Accelerated)
    Config profile      : config/deepprep.slurm.gpu.config

    # Compute R automatically from a BIDS-formatted directory:
    $ python3 src/recommend_cluster.py --bids-dir /mydata/data/DS-I --priority energy

    # JSON output (useful for scripting):
    $ python3 src/recommend_cluster.py --R 0.013 --priority makespan --json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Algorithm 1 constants (from the manuscript)
# ---------------------------------------------------------------------------

#: R-threshold below which a workload is considered *extreme fMRI-dominant*.
R_FMRI_DOMINANT = 0.02

#: R-threshold at and above which a workload is considered *sMRI-dominant*.
R_SMRI_DOMINANT = 0.15

#: Canonical set of priorities the algorithm accepts.
PRIORITIES = ("makespan", "power", "energy", "co2", "cost")


@dataclass(frozen=True)
class ClusterProfile:
    """Hardware and Nextflow-profile description of one cluster."""

    cluster_id: str           # e.g. "C2"
    name: str                 # human-readable label
    vcpus_per_node: int       # vCPU count of a single worker VM
    gpus_per_node: int        # GPU count of a single worker VM
    ram_gb_per_node: int      # RAM (GB) of a single worker VM
    config_profile: str       # relative path to the Nextflow .config file

    @property
    def total_vcpus(self) -> int:
        """Aggregate vCPUs across the three worker VMs."""
        return 3 * self.vcpus_per_node

    @property
    def total_ram_gb(self) -> int:
        """Aggregate RAM (GB) across the three worker VMs."""
        return 3 * self.ram_gb_per_node


#: Cluster catalogue matching Table 1 in the manuscript.
CLUSTERS: dict[str, ClusterProfile] = {
    "C1": ClusterProfile(
        cluster_id="C1",
        name="CPU-Intensive (High-Cores)",
        vcpus_per_node=64,
        gpus_per_node=0,
        ram_gb_per_node=64,
        config_profile="config/deepprep.slurm.cpu.config",
    ),
    "C2": ClusterProfile(
        cluster_id="C2",
        name="GPU-Accelerated",
        vcpus_per_node=16,
        gpus_per_node=1,  # 3 GPUs total across 3 worker VMs
        ram_gb_per_node=64,
        config_profile="config/deepprep.slurm.gpu.config",
    ),
    "C3": ClusterProfile(
        cluster_id="C3",
        name="CPU-Only (Modest-Cores)",
        vcpus_per_node=16,
        gpus_per_node=0,
        ram_gb_per_node=64,
        config_profile="config/deepprep.slurm.cpu.config",
    ),
    "C4": ClusterProfile(
        cluster_id="C4",
        name="CPU-Only (Memory-Enhanced)",
        vcpus_per_node=16,
        gpus_per_node=0,
        ram_gb_per_node=128,
        config_profile="config/deepprep.slurm.cpu.config",
    ),
}


# ---------------------------------------------------------------------------
# Morphology ratio R
# ---------------------------------------------------------------------------

def _scan_sizes(bids_dir: Path, patterns: Iterable[str]) -> list[int]:
    """Return file sizes (bytes) for files matching any of ``patterns``."""
    sizes: list[int] = []
    for pat in patterns:
        for f in bids_dir.rglob(pat):
            if f.is_file():
                try:
                    sizes.append(f.stat().st_size)
                except OSError:
                    # Skip unreadable files rather than abort.
                    continue
    return sizes


def compute_morphology_ratio(bids_dir: os.PathLike | str) -> float:
    """Compute the morphology ratio R for a BIDS-formatted directory.

    R = mean(sMRI file size) / mean(fMRI file size), where sMRI files are
    those matching ``*T1w.nii*`` and fMRI files match ``*bold.nii*``.

    If no fMRI scans are found, returns ``math.inf`` as per the
    convention in §3 of the paper (e.g. DS-II / NeuroCycle+).

    Raises ``FileNotFoundError`` if ``bids_dir`` does not exist or
    ``ValueError`` if no sMRI scans are found (the dataset is unusable
    by DeepPrep without at least one T1w scan).
    """
    bids = Path(bids_dir)
    if not bids.exists():
        raise FileNotFoundError(f"BIDS directory not found: {bids}")

    smri = _scan_sizes(bids, ("*T1w.nii*",))
    fmri = _scan_sizes(bids, ("*bold.nii*",))

    if not smri:
        raise ValueError(
            f"No sMRI (T1w) scans found under {bids}; DeepPrep requires "
            "at least one anatomical scan per subject."
        )
    if not fmri:
        return math.inf

    return (sum(smri) / len(smri)) / (sum(fmri) / len(fmri))


# ---------------------------------------------------------------------------
# Algorithm 1 — multi-criteria cluster recommendation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Recommendation:
    """Result of running Algorithm 1 on (R, priority)."""

    cluster_id: str                # "C1" | "C2" | "C3" | "C4"
    cluster_name: str
    config_profile: str            # Phi(C*)
    rationale: str                 # short human-readable explanation
    R: float
    priority: str

    def to_dict(self) -> dict:
        d = asdict(self)
        # math.inf is not JSON-serializable on some encoders; coerce to string.
        if math.isinf(self.R):
            d["R"] = "inf"
        return d


def recommend_cluster(R: float, priority: str) -> Recommendation:
    """Return the optimal cluster ``C*`` and config profile ``Phi(C*)``.

    Parameters
    ----------
    R
        Morphology ratio ``avg sMRI size / avg fMRI size``. Use
        ``math.inf`` for sMRI-only datasets (e.g. DS-II).
    priority
        One of ``makespan``, ``power``, ``energy``, ``co2``, ``cost``.
        Case-insensitive. The aliases ``carbon`` and ``carbon_footprint``
        map to ``co2``; ``runtime`` maps to ``makespan``.

    Returns
    -------
    Recommendation
        A frozen dataclass containing ``cluster_id`` (e.g. ``"C2"``),
        ``config_profile`` (the relative path to the Nextflow profile),
        and a short ``rationale`` string suitable for logs.

    Raises
    ------
    ValueError
        If ``R`` is negative (or ``NaN``) or ``priority`` is unrecognised.
    """
    if R != R:  # NaN check (NaN != NaN by IEEE 754)
        raise ValueError("R must not be NaN")
    if R < 0:
        raise ValueError(f"R must be non-negative, got {R!r}")

    p = priority.strip().lower()
    aliases = {
        "carbon": "co2",
        "carbon_footprint": "co2",
        "carbon-footprint": "co2",
        "co_2": "co2",
        "runtime": "makespan",
        "time": "makespan",
        "$": "cost",
        "dollars": "cost",
    }
    p = aliases.get(p, p)
    if p not in PRIORITIES:
        raise ValueError(
            f"priority must be one of {PRIORITIES}, got {priority!r}"
        )

    # --- Lines 2-3 of Algorithm 1 -----------------------------------------
    if R < R_FMRI_DOMINANT:
        cid = "C1"
        rationale = (
            f"R={R:.3g} < {R_FMRI_DOMINANT} (fMRI-dominant); "
            "high-core CPU cluster maximises CPU-bound fMRI-stage throughput."
        )
    # --- Lines 4-17 -------------------------------------------------------
    else:
        if p == "makespan" or p == "co2":
            cid = "C2"
            rationale = (
                f"Priority={p}, R={R:.3g} >= {R_FMRI_DOMINANT}; "
                "GPU offload yields the shortest runtime, and on a clean grid "
                "(CAMX) carbon scales with runtime."
            )
        elif p == "energy":
            if R >= R_SMRI_DOMINANT:
                cid = "C2"
                rationale = (
                    f"Priority=energy, R={R:.3g} >= {R_SMRI_DOMINANT} "
                    "(sMRI-leaning); GPU stages dominate, GPU cluster wins."
                )
            else:
                cid = "C4"
                rationale = (
                    f"Priority=energy, {R_FMRI_DOMINANT} <= R={R:.3g} "
                    f"< {R_SMRI_DOMINANT} (fMRI-leaning); memory-enhanced "
                    "CPU cluster gives lowest energy in this regime."
                )
        elif p == "power":
            cid = "C4"
            rationale = (
                "Priority=power; C4 sustains the lowest average wattage on "
                "fMRI-leaning workloads."
            )
        else:  # p == "cost"
            cid = "C3"
            rationale = (
                "Priority=cost; modest-core CPU cluster minimises $/sample "
                "under the AWS counterfactual model."
            )

    profile = CLUSTERS[cid]
    return Recommendation(
        cluster_id=profile.cluster_id,
        cluster_name=profile.name,
        config_profile=profile.config_profile,
        rationale=rationale,
        R=R,
        priority=p,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_r(value: str) -> float:
    """Argparse helper that accepts ``inf`` / ``infinity`` for R."""
    s = value.strip().lower()
    if s in ("inf", "+inf", "infinity", "+infinity"):
        return math.inf
    try:
        return float(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"--R expects a non-negative float or 'inf', got {value!r}"
        ) from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recommend_cluster",
        description=(
            "Recommend the optimal FABRIC cluster configuration for "
            "DeepPrep workflow execution per Algorithm 1 of the "
            "DeepNeuroBench paper."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  recommend_cluster --R 0.45 --priority makespan\n"
               "  recommend_cluster --bids-dir /mydata/data/DS-I --priority energy\n"
               "  recommend_cluster --R inf --priority co2 --json\n",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--R",
        type=_parse_r,
        help="Morphology ratio R = avg(sMRI size)/avg(fMRI size). "
             "Use 'inf' for sMRI-only datasets.",
    )
    src.add_argument(
        "--bids-dir",
        type=Path,
        help="Path to a BIDS-formatted dataset; R is computed by scanning "
             "*T1w.nii* and *bold.nii* files.",
    )
    parser.add_argument(
        "--priority", "-p",
        required=True,
        choices=PRIORITIES + ("carbon", "carbon_footprint", "runtime"),
        help="Optimisation target. 'carbon'/'carbon_footprint' alias to "
             "'co2'; 'runtime' aliases to 'makespan'.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON object instead of plain text.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.R is not None:
        R = args.R
    else:
        R = compute_morphology_ratio(args.bids_dir)

    rec = recommend_cluster(R, args.priority)

    if args.json:
        payload = rec.to_dict()
        if args.bids_dir is not None:
            payload["bids_dir"] = str(args.bids_dir)
        print(json.dumps(payload, indent=2))
    else:
        print(f"Morphology ratio R : {R if R != math.inf else 'inf'}")
        print(f"Priority           : {rec.priority}")
        print(f"Recommended cluster: {rec.cluster_id}   "
              f"({rec.cluster_name})")
        print(f"Config profile     : {rec.config_profile}")
        print(f"Rationale          : {rec.rationale}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
