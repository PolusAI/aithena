#!/bin/bash
# Clinical Aithena pgvector Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_ROOT="$(dirname "$SCRIPT_DIR")"

NAMESPACE="clinical-aithena"
DATA_DIR="/polus1/schaubnj/clinical-aithena/agents/clinical-aithena-agent/.data"

echo "========================================="
echo "Clinical Aithena pgvector Deployment"
echo "========================================="
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "   kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if secret.yaml exists
if [ ! -f "$SCRIPT_DIR/secret.yaml" ]; then
    echo "   secret.yaml not found!"
    echo ""
    echo "Please create it from the template and edit with your credentials:"
    echo "  cp $SCRIPT_DIR/secret.yaml.template $SCRIPT_DIR/secret.yaml"
    echo "  nano $SCRIPT_DIR/secret.yaml"
    echo ""
    echo "Set your username and password in the stringData section (plain text)."
    echo ""
    exit 1
fi

# Create data directory if it doesn't exist
echo "   Checking data directory..."
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory: $DATA_DIR"
    mkdir -p "$DATA_DIR"
    chmod 700 "$DATA_DIR"
    echo "   Data directory created"
else
    echo "   Data directory exists"
fi

# Deploy resources
echo ""
echo "   Deploying resources..."
echo ""

echo "1   Creating namespace..."
kubectl apply -f "$DEPLOYMENT_ROOT/namespace.yaml"

echo ""
echo "2   Creating secret..."
kubectl apply -f "$SCRIPT_DIR/secret.yaml"

echo ""
echo "3   Creating PersistentVolume..."
kubectl apply -f "$SCRIPT_DIR/pv.yaml"

echo ""
echo "4   Applying PostgreSQL configuration..."
kubectl apply -f "$SCRIPT_DIR/postgres-config.yaml"

echo ""
echo "5   Applying initialization scripts..."
kubectl apply -f "$SCRIPT_DIR/postgres-init-scripts.yaml"

echo ""
echo "6   Creating headless service..."
kubectl apply -f "$SCRIPT_DIR/headless-service.yaml"

echo ""
echo "7   Deploying PostgreSQL StatefulSet..."
kubectl apply -f "$SCRIPT_DIR/statefulset.yaml"

echo ""
echo "========================================="
echo "   Deployment Complete!"
echo "========================================="
echo ""
echo "Monitor the deployment:"
echo "  kubectl -n $NAMESPACE get pods -w"
echo ""
echo "View logs:"
echo "  kubectl -n $NAMESPACE logs clinical-aithena-db-0 -f"
echo ""
echo "Connect to database (from within cluster):"
echo "  kubectl -n $NAMESPACE exec -it clinical-aithena-db-0 -- psql -U postgres -d clinical_aithena"
echo ""
echo "Connect from local machine (port-forward):"
echo "  kubectl -n $NAMESPACE port-forward clinical-aithena-db-0 5432:5432"
echo "  psql -h localhost -p 5432 -U postgres -d clinical_aithena"
echo ""
echo "Check status:"
echo "  kubectl -n $NAMESPACE get statefulset"
echo "  kubectl -n $NAMESPACE get pvc"
echo ""

