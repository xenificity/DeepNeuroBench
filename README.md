# **DeepNeuroBench:** A Benchmark for Cost and Energy-Efficient Execution of Neuroimaging Workflows on Commodity Clusters
This repository is the reproducibility artifact the DeepNeuroBench. It contains script, configuration file, profiling tool, dataset links, sample result, and the implementation of Algorithm-1.

## Prerequisites
- Access to [FABRIC testbed](https://fabric-testbed.net/) (free academic account)
- FreeSurfer license (free from [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/registration.html))

Step: 1 Cluster Configurations (C1–C4): 
Use the `DeepNeuroBench_Cluster_Creation.ipynb` script in the `/pynb` directory to create clusters in FABRIC testbed.
| ID | Name | vCPUs (total) | GPUs | RAM/node (GB total) | FABRIC Site |
|----|------|--------------|------|---------------------|-------------|
| **C1** | CPU-Only High-Core (CPU-Intensive) | 64 (192) | — | 64 (192) | HAWI (Hawaii) |
| **C2** | CPU-GPU Cluster (GPU-Accelerated) | 16 (48) | 3 (2× RTX 6000 + 1× T4) | 64 (192) | TACC (Texas) |
| **C3** | CPU-Only Standard-Core  | 16 (48) | — | 64 (192) | HAWI (Hawaii) |
| **C4** | CPU-Only (Memory-Enhanced) | 16 (48) | — | 128 (384) | HAWI (Hawaii) |


Step: 2 Clone this repository on `vm0` (master node) at `/home/ubuntu`:  
```
git clone https://github.com/xenificity/DeepNeuroBench.git
```

Step: 3 : Configuration/Installation on worker nodes:
```bash
nodes=(vm1 vm2 vm3)
for node in "${nodes[@]}"; do
  scp vm0:~/DeepNeuroBench/config/config.sh $node:~
  ssh $node "screen -dmS config bash ~/config.sh"
done
```

Step 4 : Set up shared NFS storage:
Follow `/src/NFS-setup.md`. The shared volume mounts at `/mydata` on all nodes. 

Step 5 : Clone DeepPrep:
```bash
git clone https://github.com/pBFSLab/DeepPrep.git /mydata/DeepPrep
```

Step 6 — Install and configure Slurm
Follow `/slurm/slurm_installation.md`. Copy `slurm/slurm.conf` to `/etc/slurm/slurm.conf` on all nodes.

Step: nn Datasets downloading: The paper uses five publicly available, BIDS-formatted neuroimaging datasets. All are available via the Hugging Face datasets hub (mirrored from OpenNeuro / NITRC).

| ID | Name | Subjects | Scans | Size | Morphology Index *R* | Optimal |
|----|------|----------|-------|------|----------------------|---------|
| DS-I | Professional Chess Players | 29 | 58 (29 sMRI + 29 fMRI) | 1.1 GB | 0.45 | C2 |
| DS-II | NeuroCycle+ | 4 | 100 (sMRI only) | 3 GB | ∞ | C2 |
| DS-III | Human Dignity | 40 | 80 (40 sMRI + 40 fMRI) | 2.7 GB | 0.22 | C2 |
| DS-IV | Tumor | 36 | 72 (36 sMRI + 36 fMRI) | 1.6 GB | 0.19 | C2 |
| DS-V | Cognition | 18 | 36 (18 sMRI + 18 fMRI) | 4.2 GB | 0.013 | C1 |

All five datasets are publicly available from their original sources. Download them into `/mydata/data` at `VM0`using the appropriate client per source (_NITRC web download, or OpenNeuro CLI / DataLad for the ds00* IDs_):






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

