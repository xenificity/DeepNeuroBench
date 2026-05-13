#!/bin/bash
#SBATCH --job-name=test_job          # Job name
#SBATCH --output=output_%j.txt       # Output file (%j will be replaced with the job ID)
#SBATCH --error=error_%j.txt         # Error file (%j will be replaced with the job ID)
#SBATCH --ntasks=1                   # Number of tasks (processes)
#SBATCH --cpus-per-task=1            # Number of CPUs per task
#SBATCH --time=00:05:00              # Time limit (hh:mm:ss)
#SBATCH --partition=fabric            # Partition name (adjust based on your setup)

# Commands to execute
echo "Starting job on $(hostname)"
sleep 60  # Simulate a task that runs for 60 seconds
echo "Job completed"
