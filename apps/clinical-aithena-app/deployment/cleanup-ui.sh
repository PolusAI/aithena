#!/bin/bash
# Clinical Aithena UI Cleanup Script

set -e

NAMESPACE="clinical-aithena"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Clinical Aithena UI Cleanup"
echo "========================================="
echo ""

# Check if kubectl is available
if ! command -v microk8s &> /dev/null; then
    echo "❌ microk8s not found. Please install microk8s first."
    exit 1
fi

KUBECTL="microk8s kubectl"

# Warning
echo "⚠️  WARNING: This will delete all UI resources from the '$NAMESPACE' namespace."
echo ""
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🗑️  Deleting resources..."
echo ""

# Delete resources in reverse order
if $KUBECTL get ingress clinical-aithena-ui -n "$NAMESPACE" &> /dev/null; then
    echo "1️⃣  Deleting Ingress..."
    $KUBECTL delete -f "$SCRIPT_DIR/ui-ingress.yaml" --ignore-not-found=true
fi

echo ""
echo "2️⃣  Deleting Deployment..."
$KUBECTL delete -f "$SCRIPT_DIR/ui-deployment.yaml" --ignore-not-found=true

echo ""
echo "3️⃣  Deleting Service..."
$KUBECTL delete -f "$SCRIPT_DIR/ui-service.yaml" --ignore-not-found=true

echo ""
echo "4️⃣  Deleting ConfigMap..."
$KUBECTL delete -f "$SCRIPT_DIR/ui-config.yaml" --ignore-not-found=true

echo ""
echo "========================================="
echo "✅ Cleanup Complete!"
echo "========================================="
echo ""
echo "All UI resources have been removed from the '$NAMESPACE' namespace."
echo ""

