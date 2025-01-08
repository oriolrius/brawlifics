FROM ghcr.io/astral-sh/uv:python3.13-alpine

# Set working directory
WORKDIR /app

# Copy project files
ADD . /app

RUN uv sync --frozen

# Set environment variables
ENV PYTHONPATH=${PYTHONPATH}:/app
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=info

# Expose the application port
EXPOSE 8000

# Run the application
# CMD ["uv", "run", "uvicorn", "server:app", "--host", ${HOST}, "--port", ${PORT}, "--log-level", ${LOG_LEVEL}]
CMD uv run uvicorn "brawlifics.server:app" --host $HOST --port $PORT --log-level $LOG_LEVEL
