#!/bin/bash
# Build Docker image for clinical-aithena API

set -e

VERSION="${1:-latest}"
REGISTRY="${2:-docker.io}"

echo "========================================="
echo "   Building clinical-aithena API image"
echo "========================================="
echo ""
echo "Version: $VERSION"
echo "Registry: $REGISTRY"
echo ""

cd "$(dirname "$0")/../.."

echo "Building API image..."
docker build \
  -f Dockerfile \
  -t ${REGISTRY}/polusai/ctaithena-api:${VERSION} \
  .

echo "Tagging as latest..."
docker tag ${REGISTRY}/polusai/ctaithena-api:${VERSION} ${REGISTRY}/polusai/ctaithena-api:latest

echo ""
echo "========================================="
echo "   Build Complete!"
echo "========================================="
echo ""
echo "Images created:"
echo "  - ${REGISTRY}/polusai/ctaithena-api:${VERSION}"
echo "  - ${REGISTRY}/polusai/ctaithena-api:latest"
echo ""
echo "To push to registry:"
echo "  ./deployment/api/push.sh ${VERSION} ${REGISTRY}"
echo ""
