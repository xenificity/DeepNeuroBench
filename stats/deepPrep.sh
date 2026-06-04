cd ~/DeepNeuroBench/stats/
python3 run_dstat.py start 4
python3 run_pstat.py start 4
python3 run_cpuusage.py start 4

# Executing deepPrep on dataset here in detached screen mode

#screen -dmS deepPrep bash -c 'sudo docker run -it --rm --gpus all -v ~/chess_dataset/bids/:/input -v ./output:/output -v ./freesurfer/license.txt:/fs_license.txt pbfslab/deepprep:25.1.0 /input /output participant --fs_license_file /fs_license.txt --bold_task_type rest;cd BrainScale;python3 run_dstat.py stop 1; python3 run_gpu_stat.py stop 2'
# sleep 10

ssh vm1 "
cd /mydata && \
${DEEP_PREP_HOME}/deepprep/deepprep.sh \
  ${BIDS_DIR} \
  ${OUTPUT_DIR} \
  participant \
  --bold_task_type rest \
  --fs_license_file ${FS_LICENSE} \
  --skip_bids_validation \
  --debug \
  --executor cluster \
  --container ${SINGULARITY_IMG} \
  --config_file ${DEEP_PREP_HOME}/deepprep/nextflow/cluster/deepprep.slurm.cpu.config \
  --deepprep_home ${DEEP_PREP_HOME} \
  --resume  "

cd ~/DeepNeuroBench/stats && \
python3 run_dstat.py stop 4 && \
python3 run_cpuusage.py stop 4 && \ 
#run_pstat.py gets stop automatically as soon as run_dstat gets stop
python3 run_dstat.py collect 4 
python3 run_pstat.py collect 4
python3 run_cpuusage.py collect 4
python3 run_dstat.py plot 4 5m
python3 run_dstat.py plot 4 15m 
python3 run_dstat.py plot 4 1m 
