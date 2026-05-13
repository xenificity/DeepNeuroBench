cd BrainScale
python3 run_dstat.py start 1
python3 run_gpu_stat.py start 2
screen -dmS pscript bash pscript.sh
cd ..
# Executing deepPrep on dataset here in detached screen mode
screen -dmS deepPrep bash -c 'sudo docker run -it --rm --gpus all -v ~/chess_dataset/bids/:/input -v ./output:/output -v ./freesurfer/license.txt:/fs_license.txt pbfslab/deepprep:25.1.0 /input /output participant --fs_license_file /fs_license.txt --bold_task_type rest;cd BrainScale;python3 run_dstat.py stop 1; python3 run_gpu_stat.py stop 2'
# cd BrainScale
# python3 run_dstat.py stop 1
# python3 run_gpu_stat.py stop 2 #pscript will automatically get stopped once run_dstat stops

