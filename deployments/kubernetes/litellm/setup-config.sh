#!/bin/bash

# Create the directory for litellm config if it doesn't exist
sudo mkdir -p /data/litellm-config

# Create a sample config.yaml if it doesn't exist
if [ ! -f /data/litellm-config/config.yaml ]; then
  cat > /data/litellm-config/config.yaml << EOF
model_list:
  - model_name: ollama
    litellm_params:
      model: ollama/mistral
      api_base: http://ollama-service:11434
general_settings:
  completion_model: ollama/mistral
environment_variables:
  DATABASE_URL: postgresql://\${LITELLM_DB_USER}:\${LITELLM_DB_PASSWORD}@litellm-db:5432/litellm
  STORE_MODEL_IN_DB: "True"
  OLLAMA_HOST: http://ollama-service:11434
EOF
  echo "Created default config.yaml in /data/litellm-config/"
else
  echo "config.yaml already exists in /data/litellm-config/"
fi

# Set proper permissions
sudo chmod 644 /data/litellm-config/config.yaml
sudo chown 1000:1000 /data/litellm-config/config.yaml

echo "Configuration is ready. You can now edit /data/litellm-config/config.yaml directly."
echo "Apply the Kubernetes resources with: kubectl apply -f services/aithena-services/kubernetes/litellm/" 