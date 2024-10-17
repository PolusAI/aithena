#!/bin/bash

# Define the list of projects
projects=("dbs/qdrant-db" "backends/ollama-backend" "services/aithena-services" "agents/ask-aithena-agent" "apps/ask-aithena-app" )

repo_root=$(git rev-parse --show-toplevel)

# Loop through each project and run the microk8s kubectl install command
for project in "${projects[@]}"; do
  echo "Installing release for project: $project"
  microk8s helm install $project/helm $project-chart 
done