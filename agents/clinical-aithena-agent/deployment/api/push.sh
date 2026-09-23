#!/bin/bash
# Push Docker image for clinical-aithena API

set -e

VERSION="${1:-latest}"
REGISTRY="${2:-docker.io}"

echo "========================================="
echo "   Pushing clinical-aithena API image"
echo "========================================="
echo ""
echo "Version: $VERSION"
echo "Registry: $REGISTRY"
echo ""

echo "Pushing API images..."
docker push ${REGISTRY}/polusai/ctaithena-api:${VERSION}
docker push ${REGISTRY}/polusai/ctaithena-api:latest

echo ""
echo "========================================="
echo "   Push Complete!"
echo "========================================="
echo ""
echo "Images pushed:"
echo "  - ${REGISTRY}/polusai/ctaithena-api:${VERSION}"
echo "  - ${REGISTRY}/polusai/ctaithena-api:latest"
echo ""
echo "Update your deployment manifests with:"
echo "  image: ${REGISTRY}/polusai/ctaithena-api:${VERSION}"
echo ""
