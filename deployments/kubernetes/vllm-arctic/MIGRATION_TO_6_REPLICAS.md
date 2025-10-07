# Migration Guide: Single Ollama to 6-Replica Setup

## Overview
This guide helps you migrate from a single Ollama deployment to 6 replicas for increased throughput.

## Benefits
- 6x parallel processing capacity
- Each replica gets dedicated GPU
- Better load distribution
- ~2-4x throughput improvement

## Migration Steps

### 1. Delete the existing deployment (but keep the service)
```bash
mkk -n box delete deployment ollama
```

### 2. Apply the headless service for StatefulSet
```bash
mkk apply -f service-headless.yaml
```

### 3. Deploy the StatefulSet
```bash
mkk apply -f statefulset.yaml
```

### 4. Wait for all pods to be ready
```bash
mkk -n box get pods -l app=ollama -w
```

### 5. Verify GPU assignment
```bash
# Check each pod has 1 GPU
for i in {0..5}; do
  echo "Pod ollama-$i:"
  mkk -n box exec ollama-$i -- nvidia-smi --query-gpu=index,name,utilization.gpu --format=csv
done
```

### 6. Load the model on each instance
```bash
# Load nomic-embed-text on all replicas
for i in {0..5}; do
  echo "Loading model on ollama-$i..."
  mkk -n box exec ollama-$i -- ollama pull nomic-embed-text
done
```

### 7. Test the load balancing
```bash
# The existing service should load balance across all replicas
curl http://localhost:32101/api/tags
```

## Configuration Details

- **Replicas**: 6 (one per GPU)
- **Resources per replica**:
  - 1 GPU
  - 8-16GB RAM
  - 4-8 CPU cores
- **Storage**: 
  - Shared model storage (via PVC)
  - Individual instance data (10GB per replica)

## Rollback (if needed)
```bash
# Delete StatefulSet
mkk -n box delete statefulset ollama

# Delete headless service
mkk -n box delete service ollama-headless

# Re-apply original deployment
mkk apply -f deployment.yaml
```

## Notes
- The existing `ollama-service` will automatically load balance across all 6 replicas
- pgai-vectorizer-worker doesn't need any changes - it continues using `http://ollama-service:11434`
- Each replica will use approximately 8-16GB RAM plus GPU memory for models
