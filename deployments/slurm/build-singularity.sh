#!/bin/bash

# List of required Docker image environment variables
docker_images=(
  "OLLAMA_IMAGE"
  "QDRANT_IMAGE"
  "AITHENA_SERVICES_IMAGE"
  "ASK_AITHENA_AGENT_IMAGE"
  "ASK_AITHENA_DASHBOARD_IMAGE"
)

# Check if each required variable is set and build the Singularity image
for image in "${docker_images[@]}"; do
  if [ -z "${!image}" ]; then
    echo "Error: $image is not set."
    exit 1
  else
    echo "$image is set to ${!image}"
    singularity_image_name=$(basename "${!image}" | sed 's/:/_/').sif
    echo "Building Singularity image: $singularity_image_name from Docker image: ${!image}"
    singularity build "$singularity_image_name" "docker://${!image}"
  fi
done

echo "All Singularity images have been built."