#!/bin/bash
# Deploy Clinical Aithena UI to Kubernetes

set -e

NAMESPACE="clinical-aithena"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Clinical Aithena UI Deployment"
echo "========================================="
echo ""

# Check if kubectl is available
if ! command -v microk8s &> /dev/null; then
    echo "❌ microk8s not found. Please install microk8s first."
    exit 1
fi

KUBECTL="microk8s kubectl"

# Check if namespace exists
if ! $KUBECTL get namespace "$NAMESPACE" &> /dev/null; then
    echo "❌ Namespace '$NAMESPACE' not found!"
    echo ""
    echo "Please deploy the namespace first:"
    echo "  $KUBECTL apply -f $SCRIPT_DIR/../../agents/clinical-aithena-agent/deployment/namespace.yaml"
    echo ""
    exit 1
fi

echo "📋 Deploying UI to namespace: $NAMESPACE"
echo ""

echo "1️⃣  Applying ConfigMap..."
$KUBECTL apply -f "$SCRIPT_DIR/ui-config.yaml"

echo "2️⃣  Applying Service..."
$KUBECTL apply -f "$SCRIPT_DIR/ui-service.yaml"

echo "3️⃣  Applying Deployment..."
$KUBECTL apply -f "$SCRIPT_DIR/ui-deployment.yaml"

echo "4️⃣  Applying Ingress..."
$KUBECTL apply -f "$SCRIPT_DIR/ui-ingress.yaml"

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "📊 Monitor the deployment:"
echo "  $KUBECTL -n $NAMESPACE get pods -l app=clinical-aithena-ui -w"
echo ""
echo "📝 View logs:"
echo "  $KUBECTL -n $NAMESPACE logs -l app=clinical-aithena-ui -f"
echo ""
echo "🔍 Check status:"
echo "  $KUBECTL -n $NAMESPACE get deployment clinical-aithena-ui"
echo "  $KUBECTL -n $NAMESPACE get pods -l app=clinical-aithena-ui"
echo "  $KUBECTL -n $NAMESPACE get service clinical-aithena-ui"
echo ""
echo "🌐 Access the UI:"
echo "  External: https://polus1.ncats.nih.gov/gardian"
echo ""
echo "🔄 To restart (after a new image push):"
echo "  $KUBECTL -n $NAMESPACE rollout restart deployment clinical-aithena-ui"
echo ""
