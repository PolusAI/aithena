#!/bin/bash

# Define the list of projects
projects=("qdrant" "ollama" "aithena-services" "ask-aithena-agent" "ask-aithena-app" )

# Loop through each project and run the microk8s kubectl install command
for project in "${projects[@]}"; do
  echo "Installing release for project: $project"
  microk8s helm install $project $project-chart 
done