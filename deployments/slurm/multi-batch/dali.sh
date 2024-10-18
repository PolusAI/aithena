#!/bin/bash

# This script uses two sbatch scripts to deploy the aithena stack on dali.
# This allows us to deploy ollama on node using all available GPUs
# and the rest of the services on a cpu node. 

check_job_status() {
    squeue -j $1 -h -o "%T"
}

get_node_list() {
    squeue -j $1 -h -o "%N"
}

# Wait until a job is running
job_running() {
    while true; do
        status=$(check_job_status $1)
        echo "Job status: $status"
        if [ "$status" == "RUNNING" ]; then
            break
        elif [ -z "$status" ]; then
            echo "Error: Job $1 is no longer in the queue."
            exit 255
        fi
        sleep 1 
    done
}

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


# Parse command-line options
gpu=1  # Default value for ollama GPUs
while getopts "g:" opt; do
    case $opt in
        g)
            gpu=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Check that gpu is greater than or equal to 1
if [ "$gpu" -lt 1 ]; then
    echo "Error: The number of GPUs must be greater than or equal to 1."
    exit 1
fi

echo "Starting ollama with $gpu GPUs"
# Starting ollama with the specified number of GPUs
job_id=$(sbatch --parsable --gpus-per-task=$gpu ollama.sh)

echo "Starting ollama with job ID: $job_id"

# get ollama nodes
job_running $job_id
node_list=$(get_node_list $job_id)
echo "Ollama is running on nodes: $node_list"

# define ollama endpoint
IFS=',' read -r -a nodes <<< "$node_list"
node=${nodes[0]}
if [ ${#nodes[@]} -gt 1 ]; then
    # if started on several nodes, just take the first one as they are meshed
    echo "Ollama running on several nodes, using first one."
fi
export OLLAMA_HOST=http://$node.dali.hpc.ncats.nih.gov:11434
echo "OLLAMA_HOST: $OLLAMA_HOST"

# starting the rest of the aithena stack
job_id=$(sbatch --parsable ask-aithena.sh)
echo "starting aithena app with job ID: $job_id"
job_running $job_id
node_list=$(get_node_list $job_id)
IFS=',' read -r -a nodes <<< "$node_list"
if [ ${#nodes[@]} -gt 1 ]; then
    echo "Error: aithena must run on one node."
    exit 1
fi
node=${nodes[0]}
echo "aithena is running on node: $node"

# aithena is deployed!
echo "aithena app available at : http://$node.dali.hpc.ncats.nih.gov:8765"
