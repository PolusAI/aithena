#!/bin/bash
# Push Docker image for clinical-aithena UI

set -e

VERSION="${1:-latest}"
REGISTRY="${2:-docker.io}"

echo "========================================="
echo "   Pushing clinical-aithena UI image"
echo "========================================="
echo ""
echo "Version: $VERSION"
echo "Registry: $REGISTRY"
echo ""

echo "Pushing UI images..."
docker push ${REGISTRY}/polusai/ctaithena-ui:${VERSION}
docker push ${REGISTRY}/polusai/ctaithena-ui:latest

echo ""
echo "========================================="
echo "   Push Complete!"
echo "========================================="
echo ""
echo "Images pushed:"
echo "  - ${REGISTRY}/polusai/ctaithena-ui:${VERSION}"
echo "  - ${REGISTRY}/polusai/ctaithena-ui:latest"
echo ""
echo "Update your deployment manifests with:"
echo "  image: ${REGISTRY}/polusai/ctaithena-ui:${VERSION}"
echo ""
