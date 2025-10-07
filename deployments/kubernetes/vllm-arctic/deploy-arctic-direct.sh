#!/bin/bash

# Deploy Arctic Direct StatefulSet with individual pod access

echo "Deploying Arctic Direct infrastructure..."

# Create namespace if it doesn't exist
mkk create namespace box 2>/dev/null || echo "Namespace 'box' already exists"

# Deploy PVs
echo "Creating Persistent Volumes..."
mkk apply -f pvs.yaml

# Deploy headless service
echo "Creating headless service..."
mkk apply -f service-headless.yaml

# Deploy StatefulSet
echo "Creating StatefulSet..."
mkk apply -f statefulset.yaml

# Deploy NodePort services for individual pod access
echo "Creating NodePort services..."
mkk apply -f services-nodeport.yaml

echo ""
echo "Deployment complete!"
echo ""
echo "Wait for pods to be ready:"
echo "  mkk get pods -n box -l app=arctic-direct -w"
echo ""
echo "Once pods are ready, access them from the host:"
echo "  Pod 0: http://<node-ip>:30000"
echo "  Pod 1: http://<node-ip>:30001"
echo "  Pod 2: http://<node-ip>:30002"
echo "  Pod 3: http://<node-ip>:30003"
echo "  Pod 4: http://<node-ip>:30004"
echo "  Pod 5: http://<node-ip>:30005"
echo ""
echo "From inside the cluster, use:"
echo "  http://arctic-direct-0.arctic-direct-headless.box.svc.cluster.local:8000"
echo "  http://arctic-direct-1.arctic-direct-headless.box.svc.cluster.local:8000"
echo "  ... and so on"
