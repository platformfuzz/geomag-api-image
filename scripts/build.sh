#!/bin/bash
set -e

# Script to build Docker image for geomag-api
# Can be used both locally and in CI/CD

IMAGE_NAME="geomag-api-image"
REGISTRY="ghcr.io/platformfuzz"
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"

# Detect version from git tag or VERSION file
if [ -n "${GITHUB_REF}" ] && [[ "${GITHUB_REF}" == refs/tags/* ]]; then
    # In GitHub Actions with a tag
    VERSION="${GITHUB_REF#refs/tags/}"
    # Remove 'v' prefix if present
    VERSION="${VERSION#v}"
elif git describe --tags --exact-match HEAD 2>/dev/null; then
    # Local: git tag exists
    VERSION=$(git describe --tags --exact-match HEAD)
    VERSION="${VERSION#v}"
elif [ -f VERSION ]; then
    # Fallback to VERSION file
    VERSION=$(cat VERSION | tr -d '[:space:]')
else
    # Default version
    VERSION="latest"
fi

# Get git commit SHA (short)
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "Building Docker image..."
echo "Version: ${VERSION}"
echo "Commit SHA: ${COMMIT_SHA}"

# Build the image with tags
BUILD_TAGS="-t ${FULL_IMAGE_NAME}:${VERSION} -t ${FULL_IMAGE_NAME}:${COMMIT_SHA}"

# Only add :latest tag if VERSION is not already "latest"
if [ "${VERSION}" != "latest" ]; then
    BUILD_TAGS="${BUILD_TAGS} -t ${FULL_IMAGE_NAME}:latest"
fi

docker build ${BUILD_TAGS} .

echo "Build complete!"
echo "Image tags:"
echo "  - ${FULL_IMAGE_NAME}:${VERSION}"
if [ "${VERSION}" != "latest" ]; then
    echo "  - ${FULL_IMAGE_NAME}:latest"
fi
echo "  - ${FULL_IMAGE_NAME}:${COMMIT_SHA}"

# If in CI and we have credentials, push the image
if [ -n "${GITHUB_ACTIONS}" ] && [ -n "${GITHUB_TOKEN}" ]; then
    echo "Pushing images to registry..."
    echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GITHUB_ACTOR}" --password-stdin

    docker push "${FULL_IMAGE_NAME}:${VERSION}"
    if [ "${VERSION}" != "latest" ]; then
        docker push "${FULL_IMAGE_NAME}:latest"
    fi
    docker push "${FULL_IMAGE_NAME}:${COMMIT_SHA}"

    echo "Images pushed successfully!"
fi
