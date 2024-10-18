#!/bin/bash
#SBATCH --job-name=ask-aithena-single-batch-gpu-dali
#SBATCH --nodes=2              
#SBATCH --ntasks=5            
#SBATCH --cpus-per-task=4 
#SBATCH --mem-per-cpu=4g
#SBATCH --gpus-per-task=1
#SBATCH --partition=quick_gpu
#SBATCH --output=ask-aithena-single-batch-gpu-dali.out
#SBATCH --error=ask-aithena-single-batch-gpu-dali.err

# This batch job runs ask-aithena on dali on two gpu nodes.

echo "Starting ask-aithena..."
echo "Node list: $SLURM_NODELIST"
echo "Current hostname: $(hostname)"
echo "Current IP address: $(hostname -i)"

# List of required environment variables
required_vars=(
  "OLLAMA_IMAGE"
  "QDRANT_IMAGE"
  "AITHENA_SERVICES_IMAGE"
  "ASK_AITHENA_AGENT_IMAGE"
  "ASK_AITHENA_DASHBOARD_IMAGE"
  "QDRANT_DATA_PATH"
  "QDRANT_SNAPSHOTS_PATH"
  "OLLAMA_DATA_PATH"
  "DB_PORT"
  "DOC_COLLECTION"
  "EMBED_MODEL"
  "CHAT_MODEL"
)

# Check if each required variable is set
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: $var is not set."
    exit 1
  else
    echo "$var is set to ${!var}"
done

echo "All required environment variables are set."


# We deploy 5 gpu tasks as gpu tasks but each node has only 4 gpus,
# so we need two nodes.
FIRST_NODE=$(scontrol show hostname $SLURM_NODELIST | head -n 1)
SECOND_NODE=$(scontrol show hostname $SLURM_NODELIST | tail -n 1)

# Define service endpoints
# Ollama will be deployed on one node
# and the rest of the services will be deployed on the other node.
export OLLAMA_HOST=http://$FIRST_NODE.dali.hpc.ncats.nih.gov:11434
echo "OLLAMA_HOST: $OLLAMA_HOST"
export AITHENA_SERVICES_URL=http://$SECOND_NODE.dali.hpc.ncats.nih.gov:9000
echo "AITHENA_SERVICES_URL: $AITHENA_SERVICES_URL"
export ASK_AITHENA_API_URL=http://$SECOND_NODE.dali.hpc.ncats.nih.gov:8000
echo "ASK_AITHENA_API_URL: $ASK_AITHENA_API_URL"
export DB_HOST=$SECOND_NODE

# ollama
srun --ntasks=1 --nodes=1 -w $FIRST_NODE singularity run --writable-tmpfs --env OLLAMA_DEBUG=1 --env OLLAMA_SCHED_SPREAD=true --env OLLAMA_KEEP_ALIVE=-1  --bind ${OLLAMA_DATA_PATH}:/home/${USER}/.ollama/ --nv ${OLLAMA_IMAGE} &
echo "Running ollama on ${SECOND_NODE}"

# qdrant
srun --ntasks=1 --nodes=1 -w $SECOND_NODE singularity run --writable-tmpfs --bind ${QDRANT_DATA_PATH}:/qdrant/storage --bind ${QDRANT_SNAPSHOTS_PATH}:/qdrant/snapshots ${QDRANT_IMAGE} &
echo "Running qdrant on ${FIRST_NODE}"

# aithena services
srun --ntasks=1 --nodes=1 -w $SECOND_NODE singularity run --pwd /aithena_services_src/ ${AITHENA_SERVICES_IMAGE} uvicorn --host 0.0.0.0 --port 9000 api.main:app &
echo "Running aithena services on ${SECOND_NODE}"

# ask aithena agent
srun --ntasks=1 --nodes=1 -w $SECOND_NODE singularity run ${ASK_AITHENA_AGENT_IMAGE} &

# ask aithena apps
srun --ntasks=1 --nodes=1 -w $SECOND_NODE singularity run --pwd /ask_aithena_dashboard/ --writable-tmpfs ${ASK_AITHENA_DASHBOARD_IMAGE} &

wait  # Wait for all child jobs to finish
echo "All child jobs started successfully on nodes : ${FIRST_NODE}, ${SECOND_NODE}."