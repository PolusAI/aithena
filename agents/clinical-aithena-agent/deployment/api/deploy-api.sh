#!/bin/bash
# Deploy Clinical Aithena API to Kubernetes

set -e

NAMESPACE="clinical-aithena"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Clinical Aithena API Deployment"
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
    echo "Please deploy the database first:"
    echo "  cd $SCRIPT_DIR/.."
    echo "  ./postgres/deploy.sh"
    echo ""
    exit 1
fi

# Check if api-secret.yaml exists
if [ ! -f "$SCRIPT_DIR/api-secret.yaml" ]; then
    echo "❌ api-secret.yaml not found!"
    echo ""
    echo "Please create it from the template and edit with your credentials:"
    echo "  cd $SCRIPT_DIR"
    echo "  cp api-secret.yaml.template api-secret.yaml"
    echo "  nano api-secret.yaml"
    echo ""
    exit 1
fi

echo "📋 Deploying API to namespace: $NAMESPACE"
echo ""

echo "1️⃣  Applying ConfigMap..."
$KUBECTL apply -f "$SCRIPT_DIR/api-config.yaml"

echo "2️⃣  Applying Secret..."
$KUBECTL apply -f "$SCRIPT_DIR/api-secret.yaml"

echo "3️⃣  Applying Service..."
$KUBECTL apply -f "$SCRIPT_DIR/api-service.yaml"

echo "4️⃣  Applying Deployment..."
$KUBECTL apply -f "$SCRIPT_DIR/api-deployment.yaml"

echo "5️⃣  Applying Ingress..."
$KUBECTL apply -f "$SCRIPT_DIR/api-ingress.yaml"

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "📊 Monitor the deployment:"
echo "  $KUBECTL -n $NAMESPACE get pods -l app=clinical-aithena-api -w"
echo ""
echo "📝 View logs:"
echo "  $KUBECTL -n $NAMESPACE logs -l app=clinical-aithena-api -f"
echo ""
echo "🔍 Check status:"
echo "  $KUBECTL -n $NAMESPACE get deployment clinical-aithena-api"
echo "  $KUBECTL -n $NAMESPACE get pods -l app=clinical-aithena-api"
echo "  $KUBECTL -n $NAMESPACE get service clinical-aithena-api"
echo ""
echo "🌐 Access the API:"
echo "  External: https://polus1.ncats.nih.gov/apis/ctaithena/health"
echo "  Docs:     https://polus1.ncats.nih.gov/apis/ctaithena/docs"
echo ""
echo "🔄 To restart (after a new image push):"
echo "  $KUBECTL -n $NAMESPACE rollout restart deployment clinical-aithena-api"
echo ""
