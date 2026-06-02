# **DeepNeuroBench:** A Benchmark for Cost and Energy-Efficient Execution of Neuroimaging Workflows on Commodity Clusters
**Abstract:**
Preprocessing large neuroimaging datasets is computationally intensive. Although cloud computing enables large-scale
execution, the cost and energy efficiency of neuroimaging workflows on commodity clusters remains largely unexplored.
In this work, we evaluate DeepPrep, an open-source GPUaccelerated pipeline for preprocessing neuroimaging datasets,
across four metrics: makespan, power consumption, energy utilization, and execution cost. We preprocessed five publicly
available neuroimaging datasets with different characteristics (e.g., number of subjects, scans per subject) on four cluster
configurations: a CPU-only cluster with a high core count, a CPU-GPU cluster, a CPU-only cluster with a modest core count,
and a CPU-only cluster with large RAM. Our experiments show that the optimal cost and energy-efficient configurations
depend on the scan size ratio between the structural and functional scans in the dataset. The CPU-GPU cluster achieved
the best execution time and energy efficiency for four of the five datasets. Based on these findings, we propose a
procedure to select the optimal cluster configuration given the target metric (e.g., makespan, power/energy consumption, or
execution cost).

This repository is for the reproducibility for the DeepNeuroBench. It contains, scripts, configuration files, profiling tools, dataset links and algorithm for optimization.

## Prerequisites
- Access to [FABRIC testbed](https://fabric-testbed.net/) (free academic account)
- FreeSurfer license (free from [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/registration.html))

Step: 1 Create Clusters with following Configurations (C1–C4): Use the `DeepNeuroBench_Cluster_Creation.ipynb` script in the `/pynb` directory to create clusters in FABRIC testbed.
| ID | Name | vCPUs (total) | GPUs | RAM/node (GB total) | FABRIC Site |
|----|------|--------------|------|---------------------|-------------|
| **C1** | CPU-Only High-Core (CPU-Intensive) | 64 (192) | — | 64 (192) | HAWI (Hawaii) |
| **C2** | CPU-GPU Cluster (GPU-Accelerated) | 16 (48) | 3 (2× RTX 6000 + 1× T4) | 64 (192) | TACC (Texas) |
| **C3** | CPU-Only Standard-Core  | 16 (48) | — | 64 (192) | HAWI (Hawaii) |
| **C4** | CPU-Only (Memory-Enhanced) | 16 (48) | — | 128 (384) | MICH (Michigan) |


Step: 2 Clone this repository on `vm0` (master node) at `/home/ubuntu`:  
```bash
git clone https://github.com/xenificity/DeepNeuroBench.git
```

Step 3 : Set up shared NFS storage at `vm0`: Follow instructions at [`NFS-setup.md`](https://github.com/xenificity/DeepNeuroBench/blob/main/src/NFS-setup.md), shared volume mounts at `/mydata` on all nodes. 


Step 4 : Clone DeepPrep at the `/mydata` at `vm0` (_shared directory_):
```bash
git clone https://github.com/pBFSLab/DeepPrep.git /mydata/DeepPrep
```

Step 5 : Slurm Installation: Follow instructions at [`/slurm/slurm_installation.md`](https://github.com/xenificity/DeepNeuroBench/blob/main/slurm/slurm_installation.md), Copy `/slurm/slurm.conf` to `/etc/slurm/slurm.conf` on all nodes.

Step 7 : Configuration/Installation on worker nodes:
```bash
nodes=(vm1 vm2 vm3)
for node in "${nodes[@]}"; do
  scp vm0:~/DeepNeuroBench/config/config.sh $node:~
  ssh $node "screen -dmS config bash ~/config.sh"
done
```

Step 8 : Install Singularity and DeepPrep singularity image using command:   # This would take 10-15minutes for `.sif` file build
```bash
cp ~/Neuro*/src/install_singularity.sh /mydata
nodes=(vm0 vm1 vm2 vm3)
for node in "${nodes[@]}"; do
    echo "$node"
    ssh "$node" "screen -dmS myscreen /mydata/install_singularity.sh"
done
ssh vm0 'screen -dmS downloading_singu_image bash -c "cd /mydata && sudo singularity build deepprep_25.1.0.sif docker://pbfslab/deepprep:25.1.0"'
mkdir -p /mydata/output
sudo chmod -R 777 /mydata
sudo chown -R ubuntu:ubuntu /mydata
```

Step: 9 Download MRI dataset in BIDS data structure, and keep at `/mydata/data/bids` directory: 

| ID | Name | Subjects | Scans | Size | Morphology Index *R* | Optimal |
|----|------|----------|-------|------|----------------------|---------|
| DS-I | Professional Chess Players | 29 | 58 (29 sMRI + 29 fMRI) | 1.1 GB | 0.45 | C2 |
| DS-II | NeuroCycle+ | 4 | 100 (sMRI only) | 3 GB | ∞ | C2 |
| DS-III | Human Dignity | 40 | 80 (40 sMRI + 40 fMRI) | 2.7 GB | 0.22 | C2 |
| DS-IV | Tumor | 36 | 72 (36 sMRI + 36 fMRI) | 1.6 GB | 0.19 | C2 |
| DS-V | Cognition | 18 | 36 (18 sMRI + 18 fMRI) | 4.2 GB | 0.013 | C1 |

All five datasets are publicly available from their original sources. Download them into `/mydata/data` at `VM0`using the appropriate client per source (_NITRC web download, or OpenNeuro CLI / DataLad for the ds00* IDs_):

```
sudo apt install python3-pip -y
pip install huggingface_hub
# exit and login here
exit
```
```
screen -dmS downloadingdatasets bash -c "
mkdir -p /mydata/data
cd /mydata/data
hf download xenificity/ProfessionalChessPlayersMRI --repo-type dataset --local-dir .
hf download xenificity/NeuroCycleMRI --repo-type dataset --local-dir .
hf download xenificity/HumanDignityMRI --repo-type dataset --local-dir .
hf download xenificity/TumorMRI --repo-type dataset --local-dir .
hf download xenificity/CognitionMRI --repo-type dataset --local-dir .
hf download xenificity/PostNatalBrains --repo-type dataset --local-dir .
"
```

Step: 10 Copying `license.txt` to `/mydata`:  
```
cd /mydata
cp -r ~/DeepNeuroBench/freesurfer_key/ /mydata/
```

Step: 11 Setting environment paths on vm1 (change dataset input/output paths here):
```
ENV_VARS=$(cat <<EOF
# DeepPrep Environment Variables
export DEEP_PREP_HOME=/mydata/DeepPrep
export OUTPUT_DIR=/mydata/output/chess_data/run-1
export FS_LICENSE=/mydata/freesurfer_key/license.txt
export SINGULARITY_IMG=/mydata/deepprep_25.1.0.sif
export BIDS_DIR=/mydata/data/chess_data/bids # you may change this based on your input dataset
EOF
)
CONFIG_FILE="$HOME/.bashrc"
echo "$ENV_VARS" >> "$CONFIG_FILE"
source ~/.bashrc
```

Step: 12 Copying CPU and GPU configuration files: 
```
cp ~/DeepNeuroBench/config/deepprep.slurm.*.config /mydata/DeepPrep/deepprep/nextflow/cluster/
```

Step: 13 Use the below instruction to run on single vm,    
Using Docker  
```
sudo rm -r -f /mydata/output/*
sudo docker run -it --rm --gpus all -v /mydata/data/chess_dataset/bids:/input -v /mydata/output:/output -v /mydata/freesurfer_key/license.txt:/fs_license.txt pbfslab/deepprep:25.1.0 /input /output participant --fs_license_file /fs_license.txt --bold_task_type rest --cpus 16 --memory 64
```
Using Singularity  
```
sudo rm -r -f /mydata/output/*
sudo docker run -it --rm --gpus all -v /mydata/data/chess_dataset/bids:/input -v /mydata/output:/output -v /mydata/freesurfer_key/license.txt:/fs_license.txt pbfslab/deepprep:25.1.0 /input /output participant --fs_license_file /fs_license.txt --bold_task_type rest --cpus 16 --memory 64
```

Step: 14 Use the below instruction to run on cluster using slurm:  
Using CPUs:  
```
Go to ~/DeepNeuroBench/stats and run, deepPrep.sh in screen mode  
```

Usng GPUs: 
```
Go to ~/DeepNeuroBench/stats and run, deepPrep_gpu.sh in screen mode  
```


