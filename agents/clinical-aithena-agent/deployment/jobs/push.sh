#!/bin/bash
# Push Docker images for clinical-aithena jobs

set -e

VERSION="${1:-latest}"
REGISTRY="${2:-docker.io}"

echo "========================================="
echo "   Pushing clinical-aithena job images"
echo "========================================="
echo ""
echo "Version: $VERSION"
echo "Registry: $REGISTRY"
echo ""

# Push updatedb images
echo "2. Pushing updatedb images..."
docker push ${REGISTRY}/polusai/ctaithena-updatedb:${VERSION}
docker push ${REGISTRY}/polusai/ctaithena-updatedb:latest

echo ""
echo "========================================="
echo "   Push Complete!"
echo "========================================="
echo ""
echo "Images pushed:"
echo "  - ${REGISTRY}/polusai/ctaithena-updatedb:${VERSION}"
echo "  - ${REGISTRY}/polusai/ctaithena-updatedb:latest"
echo ""
echo "Update your job manifests with:"
echo "  image: ${REGISTRY}/polusai/ctaithena-updatedb:${VERSION}"
echo ""

