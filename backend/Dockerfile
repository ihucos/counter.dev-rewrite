FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev
EXPOSE 8000
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "counter.wsgi:application"]
