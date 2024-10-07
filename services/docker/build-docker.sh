#!/bin/bash

version=$(<docker/VERSION)
docker build -t aithena-services:${version} -f docker/Dockerfile .