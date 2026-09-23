#!/bin/bash
# Deploy Clinical Aithena Jobs

set -e

NAMESPACE="clinical-aithena"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Clinical Aithena Jobs Deployment"
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
    echo "  ./deploy.sh"
    echo ""
    exit 1
fi

echo "📋 Deploying jobs to namespace: $NAMESPACE"
echo ""

# Deploy updatedb CronJob
echo "1️⃣  Deploying updatedb CronJob..."
$KUBECTL apply -f "$SCRIPT_DIR/updatedb-cronjob.yaml"

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""

# Ask if user wants to run updatedb now
read -p "Would you like to run updatedb immediately? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Triggering updatedb job now..."
    $KUBECTL create job --from=cronjob/clinical-aithena-updatedb \
      clinical-aithena-updatedb-manual-$(date +%Y%m%d-%H%M%S) \
      -n "$NAMESPACE"
    
    echo ""
    echo "✅ Manual job created!"
    echo ""
    echo "Monitor the job:"
    echo "  $KUBECTL -n $NAMESPACE get jobs"
    echo "  $KUBECTL -n $NAMESPACE get pods -l component=updatedb"
    echo ""
    echo "View logs:"
    echo "  $KUBECTL -n $NAMESPACE logs -l component=updatedb -f"
    echo ""
fi

echo ""
echo "📊 Status:"
echo "  CronJob: $KUBECTL -n $NAMESPACE get cronjob clinical-aithena-updatedb"
echo "  Jobs:    $KUBECTL -n $NAMESPACE get jobs -l component=updatedb"
echo ""
echo "🔄 Next scheduled run: Check with:"
echo "  $KUBECTL -n $NAMESPACE get cronjob clinical-aithena-updatedb"
echo ""
echo "💡 To manually trigger the job anytime:"
echo "  $KUBECTL create job --from=cronjob/clinical-aithena-updatedb \\"
echo "    clinical-aithena-updatedb-manual-\$(date +%Y%m%d-%H%M%S) -n $NAMESPACE"
echo ""

