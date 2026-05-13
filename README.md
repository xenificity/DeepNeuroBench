# DeepNeuroBench — Artifact for IISWC 2026

**DeepNeuroBench: Characterizing Performance, Power, Energy Efficiency of DeepPrep Neuroimaging Workflow on Commodity Clusters**

This repository contains all scripts, configuration files, profiling tools, and sample results needed to reproduce the experiments reported in the IISWC 2026 paper. The artifact covers the full pipeline: FABRIC cluster provisioning → DeepPrep execution → power/CPU/GPU profiling → result collection and plotting.

---

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [Cluster Configurations (C1–C4)](#cluster-configurations-c1c4)
3. [Datasets](#datasets)
4. [Prerequisites](#prerequisites)
5. [Setup (Steps 1–11)](#setup-steps-111)
6. [Running the Experiments](#running-the-experiments)
7. [Profiling and Monitoring](#profiling-and-monitoring)
8. [Collecting and Plotting Results](#collecting-and-plotting-results)
9. [Dataset Morphology Index](#dataset-morphology-index)
10. [Repository File Reference](#repository-file-reference)
11. [Sample Results](#sample-results)
12. [Citation](#citation)

---

## Repository Structure

```
.
├── config/                        # Nextflow/Slurm execution profiles
│   ├── config.sh                  # Worker-node bootstrap (CUDA, Docker, Nextflow)
│   ├── deepprep.slurm.cpu.config  # Nextflow config for CPU-only clusters (C1, C3, C4)
│   ├── deepprep.slurm.gpu.config  # Nextflow config for GPU-accelerated cluster (C2)
│   └── deepprep.slurm.gpu+cpu.config
├── slurm/                         # Slurm cluster setup
│   ├── slurm_installation.md      # Step-by-step Slurm install guide
│   ├── slurm.conf                 # Slurm configuration file
│   ├── job_deployment_script.sh
│   ├── check_munge.sh / check_status.sh
│   ├── restart_slurm.sh / start_slurm.sh
├── src/                           # Node setup scripts
│   ├── config.sh / conda_installation.sh
│   ├── install_singularity.sh
│   ├── check_nvidia.sh
│   ├── NFS-setup.md               # Shared storage setup guide
│   └── chess-data-preprocess.sh
├── stats/                         # Profiling and monitoring
│   ├── pscript_cpu.sh             # CPU power monitoring via powertop (runs on workers)
│   ├── pscript_gpus.sh            # GPU power monitoring via nvidia-smi (runs on workers)
│   ├── run_pstat.py               # Orchestrates powertop collection across VMs
│   ├── run_dstat.py               # Orchestrates dstat collection across VMs
│   ├── run_gpu_stat.py            # Orchestrates GPU stat collection
│   ├── run_cpuusage.py            # CPU utilization collection
│   ├── power-plot.py              # Generates power consumption plots (Fig. 4, 5, 6)
│   ├── power-plot.ipynb           # Interactive version of power-plot.py
│   ├── cpu-plot.ipynb             # CPU utilization plotting notebook
│   ├── create_duration.py         # Parses Nextflow timeline for makespan extraction
│   ├── deepPrep.sh                # CPU cluster run script (C1 / C3 / C4)
│   └── deepPrep_gpu.sh            # GPU cluster run script (C2)
├── pynb/
│   └── DeepPrep_Cluster_Creation.ipynb  # FABRIC slice provisioning notebook
├── results/                       # Sample output from one run (DS-I on C2)
│   ├── report.html / timeline.html
│   ├── nextflow.run.config / nextflow.run.command
│   ├── plot*.png
│   └── sub-*/                     # Per-subject DeepPrep HTML reports
├── freesurfer_key/
│   └── license.txt                # FreeSurfer license (replace with your own)
├── deepprep.sh                    # Top-level DeepPrep launcher (wraps Nextflow)
└── README.md
```

---

## Cluster Configurations (C1–C4)

The paper evaluates four cluster configurations, each a 4-node FABRIC slice (1 master + 3 workers). All CPUs run at 2395.45 MHz.

| ID | Name | vCPUs (total) | GPUs | RAM/node (GB total) | FABRIC Site |
|----|------|--------------|------|---------------------|-------------|
| **C1** | High-Core CPU-Intensive | 64 (192) | — | 64 (192) | HAWI (Hawaii) |
| **C2** | GPU-Accelerated | 16 (48) | 3 (2× RTX 6000 + 1× T4) | 64 (192) | UCSD (San Diego) |
| **C3** | Standard-Core CPU-Only | 16 (48) | — | 64 (192) | FIU (Miami) |
| **C4** | Memory-Enhanced | 16 (48) | — | 128 (384) | MAX (College Park) |

Use the `pynb/DeepPrep_Cluster_Creation.ipynb` notebook to provision each slice on FABRIC.

Config files to use per cluster:

| Cluster | Nextflow config |
|---------|----------------|
| C1, C3, C4 | `config/deepprep.slurm.cpu.config` |
| C2 | `config/deepprep.slurm.gpu.config` |

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

Download all datasets to `/mydata/data`:

```bash
pip install huggingface_hub
screen -dmS downloadingdatasets bash -c "
mkdir -p /mydata/data
cd /mydata/data
hf download xenificity/ProfessionalChessPlayersMRI --repo-type dataset --local-dir .
hf download xenificity/NeuroCycleMRI               --repo-type dataset --local-dir .
hf download xenificity/HumanDignityMRI             --repo-type dataset --local-dir .
hf download xenificity/TumorMRI                    --repo-type dataset --local-dir .
hf download xenificity/CognitionMRI                --repo-type dataset --local-dir .
"
```

Original dataset sources:
- DS-I: [NITRC / Li et al. 2015](http://fcon_1000.projects.nitrc.org/indi/pro/wchsu_li_index.html)
- DS-II: [OpenNeuro ds006491](https://openneuro.org/datasets/ds006491/versions/1.0.1)
- DS-III: [OpenNeuro ds007441](https://openneuro.org/datasets/ds007441/versions/1.0.1)
- DS-IV: [OpenNeuro ds005003](https://openneuro.org/datasets/ds005003/versions/2.0.0)
- DS-V: [OpenNeuro ds007376](https://openneuro.org/datasets/ds007376/versions/1.0.0)

---

## Prerequisites

- Access to [FABRIC testbed](https://fabric-testbed.net/) (free academic account)
- Ubuntu 20.04 VMs with PCIe GPU passthrough (for C2)
- FreeSurfer license (free from [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/registration.html))
- Each worker VM needs: Docker, Singularity, Nextflow, Java 17, Slurm, Redis, `powertop`, `dstat`, `nvidia-smi`

The `config/config.sh` script installs all dependencies automatically.

---

## Setup (Steps 1–11)

Clone this repository on `vm0` (master node) at `/home/ubuntu`:

```bash
git clone https://github.com/xenificity/benchmark-neuro-fabric.git
```

### Step 1 — Bootstrap worker nodes

```bash
nodes=(vm1 vm2 vm3)
for node in "${nodes[@]}"; do
  scp vm0:~/benchmark-neuro-fabric/config/config.sh $node:~
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
cp -r ~/benchmark-neuro-fabric/freesurfer_key/ /mydata/
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
    scp vm0:~/benchmark-neuro-fabric/stats/pscript_cpu.sh $node:/home/ubuntu/pscript.sh
    scp vm0:~/benchmark-neuro-fabric/stats/pscript_gpus.sh $node:/home/ubuntu/pscript_gpu.sh
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
cp ~/benchmark-neuro-fabric/config/deepprep.slurm.*.config \
   /mydata/DeepPrep/deepprep/nextflow/cluster/
```

---

## Running the Experiments

Each experiment is one (cluster × dataset) cell in Table 3 of the paper. There are 20 cells total (4 clusters × 5 datasets). Each run is launched from `vm0` with monitoring active on all workers.

### CPU cluster (C1, C3, C4)

```bash
cd ~/benchmark-neuro-fabric/stats
bash deepPrep.sh
```

`deepPrep.sh` starts all monitoring processes, triggers the Nextflow/Slurm run via SSH to `vm1`, then stops and collects all profiling data when the run finishes.

### GPU cluster (C2)

```bash
cd ~/benchmark-neuro-fabric/stats
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
cd ~/benchmark-neuro-fabric/stats

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

## Dataset Morphology Index

The **Dataset Morphology Index** *M* is computed as:

```
M = avg(sMRI scan size in MB) / avg(fMRI scan size in MB)
```

For datasets with no fMRI scans (DS-II), *M* = ∞ by convention.

Quick Python calculation:

```python
import os, numpy as np

def morphology_index(bids_dir):
    smri = [os.path.getsize(f) for f in Path(bids_dir).rglob("*T1w.nii*")]
    fmri = [os.path.getsize(f) for f in Path(bids_dir).rglob("*bold.nii*")]
    if not fmri:
        return float('inf')
    return np.mean(smri) / np.mean(fmri)
```

| *M* ≥ 0.25 | sMRI-dominant → recommend **C2** (GPU) |
|---|---|
| *M* < 0.02 | fMRI-dominant → recommend **C1** (high-core CPU) |
| 0.02 ≤ *M* < 0.25 | Moderate → depends on priority (see Algorithm 1 in paper) |

---

## Repository File Reference

| File | Maps to paper section |
|------|-----------------------|
| `config/deepprep.slurm.cpu.config` | §3.1 — cluster configurations C1/C3/C4 |
| `config/deepprep.slurm.gpu.config` | §3.1 — cluster configuration C2 |
| `slurm/slurm.conf` | §3.1.3 — Slurm setup |
| `stats/pscript_cpu.sh` | §3.3 — CPU power via powertop |
| `stats/pscript_gpus.sh` | §3.3 — GPU power via nvidia-smi |
| `stats/run_pstat.py` | §3.3 — orchestrated profiling |
| `stats/run_dstat.py` | §3.3 — dstat resource collection |
| `stats/power-plot.py` | Figs. 4, 5, 6 — power/utilization plots |
| `stats/create_duration.py` | Table 3 — makespan extraction |
| `stats/deepPrep.sh` | §4 — CPU cluster experiment runner |
| `stats/deepPrep_gpu.sh` | §4 — GPU cluster experiment runner |
| `results/` | Sample output from DS-I on C2 |
| `pynb/DeepPrep_Cluster_Creation.ipynb` | §3.1 — FABRIC slice provisioning |

---

## Sample Results

The `results/` directory contains a complete sample run for DS-I (Chess Players dataset) on C2 (GPU-accelerated cluster):

- `results/report.html` — Nextflow execution report (task-level resource usage)
- `results/timeline.html` — Pipeline execution timeline (used to extract makespan)
- `results/plot*.png` — Power consumption plots
- `results/sub-*/` — Per-subject DeepPrep QC reports (29 subjects)

This corresponds to the C2 / DS-I row in Table 3 of the paper: makespan 544.33 min, avg total power 231.5 W, energy 2.10 kWh, carbon 0.43 kgCO₂, spot cost $18.42.

---

## Citation

If you use this artifact, please cite:

```bibtex
@inproceedings{deepneurobench2026,
  title     = {{DeepNeuroBench}: Characterizing Performance, Power, Energy Efficiency
               of {DeepPrep} Neuroimaging Workflow on Commodity Clusters},
  booktitle = {Proceedings of the IEEE International Symposium on Workload
               Characterization (IISWC)},
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
