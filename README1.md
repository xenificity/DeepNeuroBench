# A Benchmark Performance of DeepPrep on FABRIC Research Testbed for Speed, Utilization, Energy and Scalability
## Pre-requisites:
- Use [DeepPrep Cluster Creation Script](https://github.com/MU-CyberTraining/NeuroImaging-on-FABRIC/blob/main/DeepPrep_Cluster_Creation.ipynb) to create cluster (1-Master node + 3 workers (4-Node cluster)).  
- Clone this repository on `vm0` at `/home/ubuntu`: 
```
git clone https://github.com/MU-CyberTraining/NeuroImaging-on-FABRIC.git
```

## Instructions:  
Step: 1 Modify the number of nodes (in our case we have `vm1 to vm3` so `3` nodes) and run the below chunk to install basic configuration on worker nodes,  
```
nodes=(vm1 vm2 vm3)
for node in "${nodes[@]}"; do
  echo $node; 
  scp vm0:~/Neuro*/config/config.sh $node:~;
  ssh $node screen -dmS config "bash ~/config.sh"
done
```

Step: 2 Install `conda` using `conda_installation.sh` scrip on all worker nodes.   
Step: 3 Use [`NFS-setup.md`](https://github.com/MU-CyberTraining/NeuroImaging-on-FABRIC/blob/main/src/NFS-setup.md) to setup shared NFS storage.   
Step: 4 Git clone DeepPrep at `/mydata` directory using following command:  
```
git clone https://github.com/pBFSLab/DeepPrep.git
```  
Step: 5 Use [`slurm_install.md`](https://github.com/MU-CyberTraining/NeuroImaging-on-FABRIC/blob/main/slurm/slurm_installation.md) to install and configure slurm on cluster.   
Step: 6 Install Singularity and DeepPrep singularity image using command:   # This would take 10-15minutes for `.sif` file build
```
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

Step: 7 Download MRI dataset in BIDS data structure, and keep at `/mydata/data/bids` directory: 
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

Step: 8 Copying `license.txt` to `/mydata`:  
```
cd /mydata
cp -r ~/Neuro*/freesurfer_key/ /mydata/
```

Step: 9 Some python installation packages:  
```
nodes=(vm0 vm1 vm2 vm3)
for node in "${nodes[@]}"; do
    echo "→ $node"
    ssh "$node" '
        pip3 install --user --quiet pandas matplotlib &&
        sudo apt update -qq &&
        sudo apt install -yqq dstat powertop
    ' && echo " OK" || echo " FAILED"
done
#Moving pscript to other VMs
nodes=(vm1 vm2 vm3)
for node in "${nodes[@]}"; do
    echo "-> $node"
    scp vm0:~/Neuro*/stats/pscript.sh $node:/home/ubuntu
done
```
Note: Please check powertop installed if not install manually on each machine. 


Step: 10 Setting environment paths on vm1 (change dataset input/output paths here):
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

Step: 11 Copying CPU and GPU configuration files: 
```
cp ~/NeuroImaging-on-FABRIC/config/deepprep.slurm.*.config /mydata/DeepPrep/deepprep/nextflow/cluster/
```

Step: 12 Use the below instruction to run on single vm,    
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

Step: 12 Use the below instruction to run on cluster using slurm:  
Using CPUs:  
```
Go to ~/Neuro*/stats and run, deepPrep.sh in screen mode  
```

Usng GPUs: 
```
Go to ~/Neuro*/stats and run, deepPrep_gpu.sh in screen mode  
```


Addionally,  
1. If you are looking for general command to execute the DeepPrep on single virtual machine through docker containers, you may use,
```
sudo docker run -it --rm --gpus all -v ~/capsule-5517404-data/bids:/input -v ./output:/output -v ./freesurfer/license.txt:/fs_license.txt pbfslab/deepprep:25.1.0 /input /output participant --fs_license_file /fs_license.txt --bold_task_type rest --cpus 24 --memory 60
```

2. If you are looking to run through native installation, you may use,  
```
/opt/DeepPrep/deepprep/deepprep.sh ~/capsule-5517404-data/bids/ ~/output/  --fs_license_file ~/freesurfer/license.txt --cpus 10 --memory 20 --resume --bold_only FALSE --task_type rest --bold_task_type rest
```

3. Command to run container from image,
```
sudo docker run -it --entrypoint bash pbfslab/deepprep:25.1.0
```

4. Copying files from container to local host,
```
sudo docker cp containerId:/opt/conda .
```
