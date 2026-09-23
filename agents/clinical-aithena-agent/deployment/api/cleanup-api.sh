#!/bin/bash
# Clinical Aithena API Cleanup Script

set -e

NAMESPACE="clinical-aithena"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Clinical Aithena API Cleanup"
echo "========================================="
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "❌ Namespace '$NAMESPACE' not found!"
    exit 1
fi

# Warning
echo "⚠️  WARNING: This will delete the following API resources:"
echo "  - Deployment (clinical-aithena-api)"
echo "  - Service (clinical-aithena-api)"
echo "  - ConfigMap (clinical-aithena-api-config)"
echo "  - Secret (clinical-aithena-api-secret)"
echo "  - Ingress (clinical-aithena-api) [if exists]"
echo ""
echo "⚠️  This will NOT affect:"
echo "  - Database (clinical-aithena-db)"
echo "  - Database data"
echo ""

read -p "Are you sure you want to proceed? (yes/no) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🗑️  Deleting resources..."
echo ""

# Delete in reverse order of creation
echo "1️⃣  Deleting Ingress (if exists)..."
kubectl delete ingress clinical-aithena-api -n "$NAMESPACE" 2>/dev/null || echo "  (Ingress not found, skipping)"

echo ""
echo "2️⃣  Deleting Deployment..."
kubectl delete deployment clinical-aithena-api -n "$NAMESPACE" 2>/dev/null || echo "  (Deployment not found)"

echo ""
echo "3️⃣  Deleting Service..."
kubectl delete service clinical-aithena-api -n "$NAMESPACE" 2>/dev/null || echo "  (Service not found)"

echo ""
echo "4️⃣  Deleting Secret..."
kubectl delete secret clinical-aithena-api-secret -n "$NAMESPACE" 2>/dev/null || echo "  (Secret not found)"

echo ""
echo "5️⃣  Deleting ConfigMap..."
kubectl delete configmap clinical-aithena-api-config -n "$NAMESPACE" 2>/dev/null || echo "  (ConfigMap not found)"

echo ""
echo "========================================="
echo "✅ Cleanup Complete!"
echo "========================================="
echo ""
echo "Verify cleanup:"
echo "  kubectl -n $NAMESPACE get all -l app=clinical-aithena-api"
echo ""
echo "Note: The namespace '$NAMESPACE' and database resources were preserved."
echo ""

