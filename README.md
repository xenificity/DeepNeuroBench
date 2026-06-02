# **DeepNeuroBench:** A Benchmark for Cost and Energy-Efficient Execution of Neuroimaging Workflows on Commodity Clusters
This repository is the reproducibility artifact the DeepNeuroBench. It contains script, configuration file, profiling tool, dataset links, sample result, and the implementation of Algorithm-1.

## Prerequisites
- Access to [FABRIC testbed](https://fabric-testbed.net/) (free academic account)
- Ubuntu 20.04 VMs with PCIe GPU passthrough (for C2)
- FreeSurfer license (free from [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/registration.html))
- Each worker VM needs: Docker, Singularity, Nextflow, Java 17, Slurm, Redis, `powertop`, `dstat`, `nvidia-smi`

Step: 1 Cluster Configurations (C1–C4): 
Use the `DeepNeuroBench-cluster.ipynb` script in the `/src` directory to create clusters in FABRIC testbed.
| ID | Name | vCPUs (total) | GPUs | RAM/node (GB total) | FABRIC Site |
|----|------|--------------|------|---------------------|-------------|
| **C1** | High-Core CPU-Intensive | 64 (192) | — | 64 (192) | HAWI (Hawaii) |
| **C2** | GPU-Accelerated | 16 (48) | 3 (2× RTX 6000 + 1× T4) | 64 (192) | TACC (Texas) |
| **C3** | Standard-Core CPU-Only | 16 (48) | — | 64 (192) | HAWI (Hawaii) |
| **C4** | Memory-Enhanced | 16 (48) | — | 128 (384) | HAWI (Hawaii) |


Step: 2 Datasets downloading:

---

## Datasets
The paper uses five publicly available, BIDS-formatted neuroimaging datasets. All are available via the Hugging Face datasets hub (mirrored from OpenNeuro / NITRC).

| ID | Name | Subjects | Scans | Size | Morphology Index *M* | Optimal |
|----|------|----------|-------|------|----------------------|---------|
| DS-I | Professional Chess Players | 29 | 58 (29 sMRI + 29 fMRI) | 1.1 GB | 0.45 | C2 |
| DS-II | NeuroCycle+ | 4 | 100 (sMRI only) | 3 GB | ∞ | C2 |
| DS-III | Human Dignity | 40 | 80 (40 sMRI + 40 fMRI) | 2.7 GB | 0.22 | C2 |
| DS-IV | Tumor | 36 | 72 (36 sMRI + 36 fMRI) | 1.6 GB | 0.19 | C2 |
| DS-V | Cognition | 18 | 36 (18 sMRI + 18 fMRI) | 4.2 GB | 0.013 | C1 |

All five datasets are publicly available from their original sources. Download them into `/mydata/data` using the appropriate client per source (NITRC web download, or OpenNeuro CLI / DataLad for the ds00* IDs):

```bash
mkdir -p /mydata/data && cd /mydata/data

# DS-I (NITRC, requires registration)
# See http://fcon_1000.projects.nitrc.org/indi/pro/wchsu_li_index.html

# DS-II to DS-V (OpenNeuro — install openneuro-py: `pip install openneuro-py`)
openneuro-py download --dataset=ds006491 --target-dir=DS-II   # NeuroCycle+
openneuro-py download --dataset=ds007441 --target-dir=DS-III  # Human Dignity
openneuro-py download --dataset=ds005003 --target-dir=DS-IV   # Tumor
openneuro-py download --dataset=ds007376 --target-dir=DS-V    # Cognition
```

Original dataset sources:
- DS-I: [NITRC / Li et al. 2015](http://fcon_1000.projects.nitrc.org/indi/pro/wchsu_li_index.html)
- DS-II: [OpenNeuro ds006491](https://openneuro.org/datasets/ds006491/versions/1.0.1)
- DS-III: [OpenNeuro ds007441](https://openneuro.org/datasets/ds007441/versions/1.0.1)
- DS-IV: [OpenNeuro ds005003](https://openneuro.org/datasets/ds005003/versions/2.0.0)
- DS-V: [OpenNeuro ds007376](https://openneuro.org/datasets/ds007376/versions/1.0.0)

---





---
## Table of Contents

3. [Datasets](#datasets)
4. [Prerequisites](#prerequisites)
5. [Setup (Steps 1–11)](#setup-steps-111)
6. [Running the Experiments](#running-the-experiments)
7. [Profiling and Monitoring](#profiling-and-monitoring)
8. [Collecting and Plotting Results](#collecting-and-plotting-results)
9. [Dataset Morphology Index and Algorithm 1](#dataset-morphology-index-and-algorithm-1)
10. [Repository File Reference](#repository-file-reference)
11. [Sample Results & Table 3 Cross-Reference](#sample-results--table-3-cross-reference)
12. [Reproducibility Checklist](#reproducibility-checklist)
13. [Known Manuscript Discrepancies](#known-manuscript-discrepancies)
14. [Citation](#citation)

---

Config files to use per cluster:

| Cluster | Nextflow config |
|---------|----------------|
| C1, C3, C4 | `config/deepprep.slurm.cpu.config` |
| C2 | `config/deepprep.slurm.gpu.config` |



## Prerequisites

- Access to [FABRIC testbed](https://fabric-testbed.net/) (free academic account)
- Ubuntu 20.04 VMs with PCIe GPU passthrough (for C2)
- FreeSurfer license (free from [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/registration.html))
- Each worker VM needs: Docker, Singularity, Nextflow, Java 17, Slurm, Redis, `powertop`, `dstat`, `nvidia-smi`

The `config/config.sh` script installs all dependencies automatically.

---

## Setup (Steps 1–11)

Clone this repository on `vm0` (master node) at `/home/ubuntu`. During the IISWC 2026 anonymous review period, the artifact is hosted at:

```bash
# Anonymous mirror for IISWC 2026 review:
#   https://anonymous.4open.science/r/DeepNeuroBench-D818/
# Download as a tarball from the anonymous mirror, or use the
# git clone URL provided in the camera-ready version after acceptance.
```

### Step 1 — Bootstrap worker nodes

```bash
nodes=(vm1 vm2 vm3)
for node in "${nodes[@]}"; do
  scp vm0:~/DeepNeuroBench/config/config.sh $node:~
  ssh $node "screen -dmS config bash ~/config.sh"
done
```

### Step 2 — Install conda on all workers

Run `src/conda_installation.sh` on each worker (or include in the Step 1 bootstrap).

### Step 3 — Set up shared NFS storage

Follow `src/NFS-setup.md`. The shared volume mounts at `/mydata` on all nodes. Total space required: ~15 GB input + ~100 GB output per experiment run.

### Step 4 — Clone DeepPrep

```bash
git clone https://github.com/pBFSLab/DeepPrep.git /mydata/DeepPrep
```

### Step 5 — Install and configure Slurm

Follow `slurm/slurm_installation.md`. Copy `slurm/slurm.conf` to `/etc/slurm/slurm.conf` on all nodes.

### Step 6 — Build the DeepPrep Singularity image

```bash
cp src/install_singularity.sh /mydata
nodes=(vm0 vm1 vm2 vm3)
for node in "${nodes[@]}"; do
    ssh "$node" "screen -dmS singularity /mydata/install_singularity.sh"
done
# Build the .sif image (10–15 min)
ssh vm0 'screen -dmS build_sif bash -c "cd /mydata && sudo singularity build deepprep_25.1.0.sif docker://pbfslab/deepprep:25.1.0"'
mkdir -p /mydata/output
sudo chmod -R 777 /mydata && sudo chown -R ubuntu:ubuntu /mydata
```

### Step 7 — Download datasets

See the [Datasets](#datasets) section above.

### Step 8 — Copy FreeSurfer license

```bash
cp -r ~/DeepNeuroBench/freesurfer_key/ /mydata/
```

Replace `freesurfer_key/license.txt` with your own license file before this step.

### Step 9 — Install Python profiling dependencies on all nodes

```bash
nodes=(vm0 vm1 vm2 vm3)
for node in "${nodes[@]}"; do
    ssh "$node" '
        pip3 install --user --quiet pandas matplotlib
        sudo apt update -qq
        sudo apt install -yqq dstat powertop
    '
done
# Copy monitoring scripts to workers
for node in vm1 vm2 vm3; do
    scp vm0:~/DeepNeuroBench/stats/pscript_cpu.sh $node:/home/ubuntu/pscript.sh
    scp vm0:~/DeepNeuroBench/stats/pscript_gpus.sh $node:/home/ubuntu/pscript_gpu.sh
done
```

### Step 10 — Set environment variables on vm1

Edit these paths to match your dataset and output directories:

```bash
cat >> ~/.bashrc << 'EOF'
export DEEP_PREP_HOME=/mydata/DeepPrep
export OUTPUT_DIR=/mydata/output/run-1
export FS_LICENSE=/mydata/freesurfer_key/license.txt
export SINGULARITY_IMG=/mydata/deepprep_25.1.0.sif
export BIDS_DIR=/mydata/data/chess_data/bids   # change per dataset
EOF
source ~/.bashrc
```

### Step 11 — Deploy Nextflow configuration files

```bash
cp ~/DeepNeuroBench/config/deepprep.slurm.*.config \
   /mydata/DeepPrep/deepprep/nextflow/cluster/
```

---

## Running the Experiments

Each experiment is one (cluster × dataset) cell in Table 3 of the paper. There are 20 cells total (4 clusters × 5 datasets). Each run is launched from `vm0` with monitoring active on all workers.

### CPU cluster (C1, C3, C4)

```bash
cd ~/DeepNeuroBench/stats
bash deepPrep.sh
```

`deepPrep.sh` starts all monitoring processes, triggers the Nextflow/Slurm run via SSH to `vm1`, then stops and collects all profiling data when the run finishes.

### GPU cluster (C2)

```bash
cd ~/DeepNeuroBench/stats
bash deepPrep_gpu.sh
```

Same orchestration but uses `config/deepprep.slurm.gpu.config` and passes `--gres=gpu:1` to Slurm job steps that require GPU acceleration (FastSurferCNN, FastCSR, SUGAR, SynthMorph stages).

### To run a single subject (quick test)

```bash
sudo docker run --rm --gpus all \
  -v ${BIDS_DIR}:/input \
  -v ${OUTPUT_DIR}:/output \
  -v ${FS_LICENSE}:/fs_license.txt \
  pbfslab/deepprep:25.1.0 \
  /input /output participant \
  --fs_license_file /fs_license.txt \
  --bold_task_type rest \
  --cpus 16 --memory 64
```

---

## Profiling and Monitoring

The monitoring stack runs automatically inside `deepPrep.sh` / `deepPrep_gpu.sh`. It can also be controlled manually:

| Script | Purpose | Command |
|--------|---------|---------|
| `run_dstat.py start N` | Start dstat on N–1 workers | `python3 run_dstat.py start 4` |
| `run_pstat.py start N` | Start powertop on N–1 workers | `python3 run_pstat.py start 4` |
| `run_gpu_stat.py start N` | Start nvidia-smi on N–1 workers | `python3 run_gpu_stat.py start 4` |
| `run_cpuusage.py start N` | Start CPU utilization on N–1 workers | `python3 run_cpuusage.py start 4` |
| `run_dstat.py collect N` | Pull CSVs from workers to vm0 | `python3 run_dstat.py collect 4` |
| `run_pstat.py collect N` | Pull power CSVs to vm0 | `python3 run_pstat.py collect 4` |

**How CPU power is measured:** `pscript_cpu.sh` runs `powertop --csv` in kernel-tracepoint mode on each worker at 2-second intervals, extracts the "system baseline" power field, and writes timestamped rows to `plot_ready.csv`. `pscript.py` stops automatically when the `MYDSTAT` screen session ends.

**How GPU power is measured:** `pscript_gpus.sh` polls `nvidia-smi --query-gpu=power.draw` at 2-second intervals.

**Energy derivation** (matching §3.3 of the paper):

```
Energy (J)   = Σ (P_i × Δt)        where Δt = 2 s, sum over full makespan
Energy (kWh) = Energy (J) / 3.6×10⁶
Carbon (kgCO₂) = Energy (kWh) × EF(site)
```

eGRID2023 subregion emission factors used: HIOA = 0.667 (C1/Hawaii), CAMX = 0.207 (C2/San Diego), FRCC = 0.355 (C3/Miami), RFCE = 0.288 (C4/College Park).

---

## Collecting and Plotting Results

After all VMs have been collected back to vm0:

```bash
cd ~/DeepNeuroBench/stats

# Generate per-VM and combined power plots (reproduces Figs. 4, 5, 6)
python3 power-plot.py

# Or use the interactive notebook
jupyter notebook power-plot.ipynb
jupyter notebook cpu-plot.ipynb

# Extract makespan from Nextflow timeline
python3 create_duration.py results/timeline.html
```

`power-plot.py` reads `vm1_plot_ready.csv`, `vm2_plot_ready.csv`, `vm3_plot_ready.csv` (collected from workers) and generates:
- Per-VM CPU / GPU / Total power time series
- Combined multi-VM overlay chart

---

## Dataset Morphology Index and Algorithm 1

The **morphology ratio** *R* (called *M* in earlier drafts) is defined per §3 of the paper:

```
R = avg(sMRI scan size) / avg(fMRI scan size)
```

For datasets with no fMRI scans (DS-II), *R* = ∞ by convention.

### Algorithm 1 — reference implementation

`src/recommend_cluster.py` is a from-scratch, dependency-free reproduction of **Algorithm 1** (page 6 of the manuscript). It takes either a precomputed *R* or a BIDS directory, plus an optimization priority, and returns both the recommended cluster *C\** and the corresponding Nextflow/Slurm config profile *Φ(C\*)*.

```bash
# Compute the recommendation directly from R
python3 src/recommend_cluster.py --R 0.45 --priority makespan
# Recommended cluster: C2   (GPU-Accelerated)
# Config profile     : config/deepprep.slurm.gpu.config

# Or let the script compute R from a BIDS-formatted dataset
python3 src/recommend_cluster.py --bids-dir /mydata/data/DS-III --priority energy

# JSON output for scripting / Nextflow integration
python3 src/recommend_cluster.py --R inf --priority co2 --json
```

### Decision regimes (matches Algorithm 1 verbatim)

| Regime                | Routing                                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **R < 0.02**          | *fMRI-dominant* → **C1** (high-core CPU), regardless of priority. Example: DS-V.                                     |
| **R ≥ 0.15**          | *sMRI-dominant* → **C2** for `makespan`, `co2`, or `energy`; **C4** for `power`; **C3** for `cost`. Examples: DS-I, DS-II, DS-III, DS-IV. |
| **0.02 ≤ R < 0.15**   | *Intermediate* → **C2** for `makespan`/`co2`; **C4** for `power`/`energy`; **C3** for `cost`.                         |

The thresholds **0.02** and **0.15** are taken directly from §3 of the paper; the older draft value of 0.25 has been corrected.

### Verifying Algorithm 1 on the five benchmark datasets

```bash
python3 -m pytest tests/test_recommend_cluster.py -q
# 87 passed in 0.5s
```

The test suite exercises every branch of Algorithm 1 and confirms that `recommend_cluster(R, "makespan")` reproduces the *Optimal* column of Table 2 for all five datasets — including the two boundary regimes DS-II (R = ∞) and DS-V (R = 0.013).

---

## Repository File Reference

| File | Maps to paper section |
|------|-----------------------|
| `src/recommend_cluster.py` | **Algorithm 1** (p. 6) — multi-criteria cluster recommendation |
| `tests/test_recommend_cluster.py` | Algorithm 1 unit tests (Table 2 verification, branch coverage) |
| `tests/test_table3_consistency.py` | Internal-consistency checks on Table 3 |
| `scripts/verify_artifact.sh` | Single-command offline reproducibility check |
| `results/table2_morphology.csv` | **Table 2** — dataset characteristics + *R* values |
| `results/table3_metrics.csv` | **Table 3** — makespan, power, energy, carbon, cost |
| `config/deepprep.slurm.cpu.config` | §3.1 — cluster configurations C1/C3/C4 |
| `config/deepprep.slurm.gpu.config` | §3.1 — cluster configuration C2 |
| `slurm/slurm.conf` | §3.1.3 — Slurm setup |
| `stats/pscript_cpu.sh` | §3.3 — CPU power via powertop |
| `stats/pscript_gpus.sh` | §3.3 — GPU power via nvidia-smi |
| `stats/run_pstat.py` | §3.3 — orchestrated profiling |
| `stats/run_dstat.py` | §3.3 — dstat resource collection |
| `stats/power-plot.py` | Fig. 2 — power/utilization plots |
| `stats/create_duration.py` | Table 3 — makespan extraction |
| `stats/deepPrep.sh` | §4 — CPU cluster experiment runner |
| `stats/deepPrep_gpu.sh` | §4 — GPU cluster experiment runner |
| `results/` | Sample output from DS-I on C2 |
| `pynb/DeepPrep_Cluster_Creation.ipynb` | §3.1 — FABRIC slice provisioning |

---

## Sample Results & Table 3 Cross-Reference

The `results/` directory contains both a complete sample run for DS-I (Chess Players) on C2 and machine-readable copies of the manuscript's main tables for reviewer cross-reference.

### Sample run (DS-I on C2)

- `results/report.html` — Nextflow execution report (task-level resource usage)
- `results/timeline.html` — Pipeline execution timeline (used to extract makespan)
- `results/plot*.png` — Power consumption plots
- `results/sub-*/` — Per-subject DeepPrep QC reports (29 subjects)

This corresponds to the C2 / DS-I row in Table 3 of the paper: makespan 544.33 min, avg total power 231.45 W, energy 2.10 kWh, carbon 0.435 kgCO₂, projected on-demand cost $46.40.

### Machine-readable tables

| File | Description |
|------|-------------|
| `results/table2_morphology.csv` | Datasets, subject/scan counts, sMRI/fMRI size ranges, *R*, optimal cluster |
| `results/table3_metrics.csv` | Per-(dataset × cluster) makespan, power, energy, carbon, cost + grid metadata (FABRIC site, eGRID subregion, EF) |

`tests/test_table3_consistency.py` verifies that for 18 of 20 rows in `table3_metrics.csv` the reported carbon equals `Energy × EF` within rounding tolerance, and that Algorithm 1 selects exactly the per-dataset minimum-makespan row across all five datasets.

---

## Reproducibility Checklist

For IISWC 2026 artifact reviewers, the following are verifiable **offline** in under one minute:

- [x] **Algorithm 1** (paper page 6) — `src/recommend_cluster.py` + 87 unit tests in `tests/test_recommend_cluster.py`. Run: `python3 -m pytest tests/test_recommend_cluster.py -q`
- [x] **Table 2 *R* / Optimal column** — parametrized test `test_table2_optimal_makespan` covers all five datasets.
- [x] **Table 3 internal consistency** — 8 checks in `tests/test_table3_consistency.py` (carbon vs energy×EF, per-dataset min-makespan cluster).
- [x] **Φ(C\*) config-profile mapping** — `test_config_profile_paths_exist` confirms every cluster's declared Nextflow profile is actually present in the repository.
- [x] **Single-command verification** — `bash scripts/verify_artifact.sh` runs all of the above plus a CLI smoke test.

The following require the FABRIC testbed and ~24 h per run:

- [ ] End-to-end DeepPrep workflow on FABRIC slices C1–C4
- [ ] Live power / GPU / dstat collection via the `stats/` orchestration scripts
- [ ] Figure 2 plot generation from raw `vm*_plot_ready.csv` traces

---

## Known Manuscript Discrepancies

Two rows of Table 3 — **DS-I / C4** and **DS-II / C4** — exhibit an internal inconsistency: the reported Carbon column matches the *cluster-total* C4 power draws quoted in §4.2 (1.09 kW on DS-I, 1.81 kW on DS-II) when reconstructed as `Power × Makespan × EF`, but the Energy column appears to have been aggregated differently. The artifact preserves the manuscript's printed numbers verbatim in `results/table3_metrics.csv` so reviewers can cross-reference, and `tests/test_table3_consistency.py` explicitly documents these two rows in `KNOWN_TABLE3_CARBON_INCONSISTENCIES`. The qualitative claim of §4.2 — that C4 incurs disproportionate carbon / energy on DS-I and DS-II — is unaffected (C4 still has the highest reported carbon on DS-II in Table 3, by a wide margin).

---

## Citation

This artifact accompanies an anonymous submission to IISWC 2026. A complete citation block will be added in the camera-ready version. For the review period, please refer to the paper as:

```bibtex
@inproceedings{deepneurobench2026anon,
  title     = {A Benchmark for Cost and Energy-Efficient Execution of
               Neuroimaging Workflows on Commodity Clusters},
  booktitle = {Proceedings of the IEEE International Symposium on Workload
               Characterization (IISWC)},
  note      = {Anonymous submission \#344, under review},
  year      = {2026}
}
```

**DeepPrep** (the pipeline being characterized):
```bibtex
@article{ren2025deepprep,
  title   = {DeepPrep: an accelerated, scalable and robust pipeline for neuroimaging
             preprocessing empowered by deep learning},
  author  = {Ren, Jianxun and others},
  journal = {Nature Methods},
  volume  = {22},
  pages   = {473--476},
  year    = {2025},
  doi     = {10.1038/s41592-025-02599-1}
}
```

**FABRIC testbed**:
```bibtex
@article{baldin2019fabric,
  title   = {{FABRIC}: A national-scale programmable experimental network infrastructure},
  author  = {Baldin, Ilya and others},
  journal = {IEEE Internet Computing},
  volume  = {23},
  number  = {6},
  pages   = {38--47},
  year    = {2019}
}
```
