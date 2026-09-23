#!/bin/bash
# Build and push Docker images for clinical-aithena jobs

set -e

VERSION="${1:-latest}"
REGISTRY="${2:-docker.io}"

echo "========================================="
echo "   Building clinical-aithena job images"
echo "========================================="
echo ""
echo "Version: $VERSION"
echo "Registry: $REGISTRY"
echo ""

cd "$(dirname "$0")/../.."

# Build updatedb image
echo "2. Building updatedb image..."
docker build \
  -f deployment/jobs/Dockerfile.updatedb \
  -t ${REGISTRY}/polusai/ctaithena-updatedb:${VERSION} \
  .

echo "   Tagging as latest..."
docker tag ${REGISTRY}/polusai/ctaithena-updatedb:${VERSION} ${REGISTRY}/polusai/ctaithena-updatedb:latest

echo ""
echo "========================================="
echo "   Build Complete!"
echo "========================================="
echo ""
echo "Images created:"
echo "  - ${REGISTRY}/polusai/ctaithena-updatedb:${VERSION}"
echo "  - ${REGISTRY}/polusai/ctaithena-updatedb:latest"
echo ""
echo "To push to registry:"
echo "  docker push ${REGISTRY}/polusai/ctaithena-updatedb:${VERSION}"
echo "  docker push ${REGISTRY}/polusai/ctaithena-updatedb:latest"
echo ""
echo "To push all at once:"
echo "  ./deployment/jobs/push.sh ${VERSION} ${REGISTRY}"
echo ""

