# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to the workspace root
# Gemini CLI will mount the workspace here
WORKDIR /workspace

# Install common development tools
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    ruff \
    black \
    mypy \
    ipython

# Copy requirements and install them to speed up agent runs
# Note: Gemini CLI mounts the project root, so we can access files directly.
# However, pre-installing dependencies in the image makes the sandbox faster.
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Default command
CMD ["/bin/bash"]
