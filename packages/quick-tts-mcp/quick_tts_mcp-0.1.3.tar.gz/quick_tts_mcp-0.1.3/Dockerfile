FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install -e .

# Copy source code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 mcpuser
USER mcpuser

# Expose port (if needed for HTTP MCP)
EXPOSE 8000

# Run the MCP server
CMD ["quick-tts-mcp"]
