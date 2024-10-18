#!/bin/bash
#SBATCH --job-name=ollama
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4 # CHECK REQUIREMENTS
#SBATCH --mem-per-cpu=10G # CHECK REQUIREMENTS
#SBATCH --gpus-per-task=4
#SBATCH --partition=quick_gpu
#SBATCH --ntasks=1
#SBATCH --output=ollama.out
#SBATCH --error=ollama.err

singularity run --writable-tmpfs \
--bind ${OLLAMA_DATA_PATH}:/home/${USER}/.ollama/ \ 
--env OLLAMA_DEBUG=1 --env OLLAMA_SCHED_SPREAD=true --env OLLAMA_KEEP_ALIVE=-1 \
--nv ${OLLAMA_IMAGE}