#!/usr/bin/env bash

IMG_NAME="syncplay-proxy"
IMG_TAG="ghcr.io/weeb-poly/syncplay-proxy"

# Copy Image from root to current user
sudo podman save "${IMG_NAME}" | podman load

# Add Proper Tag
podman tag "${IMG_NAME}" "${IMG_TAG}"

# Remove extra tag
# Note: Only works because we added another tag
podman rmi "${IMG_NAME}"

# Push Image with tag
podman push "${IMG_TAG}"

# Delete Image from User
# podman rmi "${IMG_TAG}"
