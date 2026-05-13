# Shell commands to convert chess dataset into deepprep required format
for i in sub-*;do echo $i; cd ${i}/ses-01/anat;echo ${i}_T1w.json;cd ~/chess_dataset/bids;done
for i in sub-*;do echo $i; cd ${i}/ses-01/func;mv ${i}_task-rest_bold.json ${i}_ses-01_task-rest_run-01_bold.json; mv ${i}_task-rest_bold.nii.gz ${i}_ses-01_task-rest_run-01_bold.nii.gz ;cd ~/chess_dataset/bids;done
for i in sub*;do echo $i;cd ${i}/ses-01;rm -r -f dwi;cd ../..;done
