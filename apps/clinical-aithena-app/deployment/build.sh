#!/bin/bash
# Build Docker image for clinical-aithena UI

set -e

VERSION="${1:-latest}"
REGISTRY="${2:-docker.io}"
API_URL="${3:-https://polus1.ncats.nih.gov/apis/ctaithena}"

echo "========================================="
echo "   Building clinical-aithena UI image"
echo "========================================="
echo ""
echo "Version: $VERSION"
echo "Registry: $REGISTRY"
echo "API URL:  $API_URL"
echo ""

cd "$(dirname "$0")/.."

echo "Building UI image..."
docker build \
  --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
  -f Dockerfile \
  -t ${REGISTRY}/polusai/ctaithena-ui:${VERSION} \
  .

echo "Tagging as latest..."
docker tag ${REGISTRY}/polusai/ctaithena-ui:${VERSION} ${REGISTRY}/polusai/ctaithena-ui:latest

echo ""
echo "========================================="
echo "   Build Complete!"
echo "========================================="
echo ""
echo "Images created:"
echo "  - ${REGISTRY}/polusai/ctaithena-ui:${VERSION}"
echo "  - ${REGISTRY}/polusai/ctaithena-ui:latest"
echo ""
echo "To push to registry:"
echo "  ./deployment/push.sh ${VERSION} ${REGISTRY}"
echo ""
