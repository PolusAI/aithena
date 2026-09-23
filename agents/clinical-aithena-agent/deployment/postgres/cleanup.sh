#!/bin/bash
# Clinical Aithena pgvector Cleanup Script
# ⚠️  WARNING: This will delete the database and all data!

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_ROOT="$(dirname "$SCRIPT_DIR")"

NAMESPACE="clinical-aithena"

echo "========================================="
echo "   Clinical Aithena Cleanup"
echo "========================================="
echo ""
echo "This will DELETE:"
echo "  - StatefulSet (clinical-aithena-db)"
echo "  - PersistentVolumeClaim (data will be deleted!)"
echo "  - Services"
echo "  - ConfigMaps"
echo "  - Secret"
echo "  - PersistentVolume"
echo "  - Namespace"
echo ""
echo "   WARNING: All database data will be PERMANENTLY DELETED!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "   Starting cleanup..."
echo ""

# Delete StatefulSet
echo "1   Deleting StatefulSet..."
kubectl delete -f "$SCRIPT_DIR/statefulset.yaml" --ignore-not-found=true

# Delete PVC (this deletes the data!)
echo ""
echo "2   Deleting PersistentVolumeClaim..."
kubectl -n $NAMESPACE delete pvc postgres-storage-clinical-aithena-db-0 --ignore-not-found=true

# Delete service
echo ""
echo "3   Deleting headless service..."
kubectl delete -f "$SCRIPT_DIR/headless-service.yaml" --ignore-not-found=true

# Delete ConfigMaps
echo ""
echo "4   Deleting ConfigMaps..."
kubectl delete -f "$SCRIPT_DIR/postgres-config.yaml" --ignore-not-found=true
kubectl delete -f "$SCRIPT_DIR/postgres-init-scripts.yaml" --ignore-not-found=true

# Delete secret
echo ""
echo "5   Deleting secret..."
kubectl delete -f "$SCRIPT_DIR/secret.yaml" --ignore-not-found=true

# Delete PV
echo ""
echo "6   Deleting PersistentVolume..."
kubectl delete -f "$SCRIPT_DIR/pv.yaml" --ignore-not-found=true

# Delete namespace
echo ""
echo "7   Deleting namespace..."
kubectl delete -f "$DEPLOYMENT_ROOT/namespace.yaml" --ignore-not-found=true

echo ""
echo "========================================="
echo "   Cleanup Complete!"
echo "========================================="
echo ""
echo "Note: The .data directory still exists on the host."
echo "To remove it manually:"
echo "  rm -rf /polus1/schaubnj/clinical-aithena/agents/clinical-aithena-agent/.data"
echo ""
echo "To redeploy:"
echo "  ./deploy.sh"
echo ""

