#!/bin/bash

# Create the directory for Ollama models if it doesn't exist
sudo mkdir -p /data/ollama

# Set proper permissions
sudo chmod 755 /data/ollama
sudo chown 1000:1000 /data/ollama

echo "Ollama data directory has been created at /data/ollama"
echo "Apply the Kubernetes resources with: kubectl apply -f services/aithena-services/kubernetes/ollama/"
echo ""
echo "After deployment, you can pull models with:"
echo "kubectl exec -it deployment/ollama -- ollama pull mistral" 