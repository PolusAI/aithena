#!/bin/bash
# uninstall all releases in the given namespace.
# If none is provided, default namespace is used.

# Check if namespace argument is provided
if [ -z "$1" ]; then
  echo "No namespace provided. Uninstalling all releases in the default namespace."
  NAMESPACE_OPTION=""
else
  NAMESPACE=$1
  echo "Uninstalling all releases in namespace: $NAMESPACE"
  NAMESPACE_OPTION="--namespace $NAMESPACE"
fi

NAMESPACE=$1

# List all Helm releases
echo "Listing all Helm releases:"
microk8s helm list

# Get the list of all Helm releases
releases=$(microk8s helm list -q $NAMESPACE_OPTION)

# Loop through each release and uninstall it
for release in $releases; do
  echo "Uninstalling release: $release"
  microk8s  helm uninstall $release $NAMESPACE_OPTION
done

echo "All Helm releases have been uninstalled."