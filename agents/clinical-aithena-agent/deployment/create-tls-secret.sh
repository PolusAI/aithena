#!/bin/bash
# Create TLS secret for polus1.ncats.nih.gov
# This script creates a Kubernetes TLS secret from the SSL certificates

set -e

NAMESPACE="clinical-aithena"
SECRET_NAME="polus1-tls"
CERT_DIR="/etc/ssl/polus1.ncats.nih.gov"
CERT_FILE="$CERT_DIR/polus1.ncats.nih.gov.pem"
KEY_FILE="$CERT_DIR/polus1.ncats.nih.gov.key"

echo "========================================="
echo "Creating TLS Secret for polus1.ncats.nih.gov"
echo "========================================="
echo ""

# Check if microk8s is available
if ! command -v microk8s &> /dev/null; then
    echo "❌ microk8s not found. Please install microk8s first."
    exit 1
fi

KUBECTL="microk8s kubectl"

# Check if certificate files exist
if [ ! -f "$CERT_FILE" ]; then
    echo "❌ Certificate file not found: $CERT_FILE"
    exit 1
fi

if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found: $KEY_FILE"
    exit 1
fi

echo "📜 Certificate: $CERT_FILE"
echo "🔑 Key: $KEY_FILE"
echo ""

# Check if namespace exists
if ! $KUBECTL get namespace "$NAMESPACE" &> /dev/null; then
    echo "❌ Namespace '$NAMESPACE' not found!"
    echo ""
    echo "Please create the namespace first:"
    echo "  $KUBECTL create namespace $NAMESPACE"
    echo ""
    exit 1
fi

# Check if secret already exists
if $KUBECTL -n "$NAMESPACE" get secret "$SECRET_NAME" &> /dev/null; then
    echo "⚠️  Secret '$SECRET_NAME' already exists in namespace '$NAMESPACE'"
    echo ""
    read -p "Do you want to replace it? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Operation cancelled."
        exit 0
    fi
    echo ""
    echo "Deleting existing secret..."
    $KUBECTL -n "$NAMESPACE" delete secret "$SECRET_NAME"
fi

# Create the TLS secret
echo "Creating TLS secret..."
$KUBECTL -n "$NAMESPACE" create secret tls "$SECRET_NAME" \
    --cert="$CERT_FILE" \
    --key="$KEY_FILE"

echo ""
echo "✅ TLS secret created successfully!"
echo ""
echo "Verify the secret:"
echo "  $KUBECTL -n $NAMESPACE get secret $SECRET_NAME"
echo "  $KUBECTL -n $NAMESPACE describe secret $SECRET_NAME"
echo ""

