FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies, Python, and curl (needed to download uv)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    python3.12 \
    python3.12-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv using the official standalone installer script
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to the PATH so it can be executed globally
ENV PATH="/root/.local/bin:$PATH"

# Configure uv behavior
ENV UV_PYTHON=python3.15
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

# Copy application files
COPY . .

# Sync dependencies using uv's cache mount for speed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000

# Put the virtual environment's bin folder at the front of the PATH
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "counter.wsgi:application"]
