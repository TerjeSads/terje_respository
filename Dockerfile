# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
ENV UV_KEYRING_PROVIDER subprocess
ENV UV_COMPILE_BYTECODE true
ENV UV_NO_CACHE true

# Tools added to Path
ENV PATH="/root/.local/bin/:$PATH"
RUN uv tool install keyring --with keyrings.google-artifactregistry-auth

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app

RUN uv sync --frozen --no-cache --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []