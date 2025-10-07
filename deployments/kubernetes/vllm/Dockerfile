# Use an official NVIDIA CUDA image as a base
# The devel tag includes the full CUDA toolkit, which is useful for building packages
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Set non-interactive frontend for package managers to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including Python, venv, dev headers, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa && apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# We use 'bash -c' to ensure the 'source' command is available and works as expected.
SHELL ["/bin/bash", "-c"]

# Install uv using the official installer and add to PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to the system's PATH. It's installed in /root/.local/bin by default.
ENV PATH="/root/.local/bin:${PATH}"

# Create a Python virtual environment using uv
# Activate it and install the specified Python package.
# Using a venv isolates dependencies and avoids polluting the system Python.
RUN uv venv /opt/venv --python python3.12 && \
    source /opt/venv/bin/activate && \
    uv pip install --no-cache-dir 'arctic-inference[embedding]'

# Add the virtual environment's bin directory to the PATH.
# This makes `python` and other executables from the venv available directly.
ENV PATH="/opt/venv/bin:${PATH}"

# Set the working directory for the container
WORKDIR /app

# Set the default command to launch a bash shell when the container starts.
# This is useful for interactive sessions.
CMD ["bash"]
