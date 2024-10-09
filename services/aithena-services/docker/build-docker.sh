#!/bin/bash

version=$(<docker/VERSION)
# docker build --platform linux/amd64,linux/arm64 -t aithena-services:${version} -f docker/Dockerfile .
docker build -t polusai/aithena-services:${version} -f docker/Dockerfile .
