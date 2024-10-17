#!/bin/bash

# List all Helm releases
echo "Listing all Helm releases:"
microk8s helm list

# Get the list of all Helm releases
releases=$(microk8s helm list -q)

# Loop through each release and uninstall it
for release in $releases; do
  echo "Uninstalling release: $release"
  microk8s  helm uninstall $release
done

echo "All Helm releases have been uninstalled."