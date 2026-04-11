FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build dependencies for C-extensions (tree-sitter, etc.)
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Create data directory and ensure proper ownership for HFS user (UID 1000)
RUN mkdir -p /app/data/hf_cache /app/data/numba_cache && chown -R 1000:1000 /app/data

# AI Environment Patch: Provide a system username and writable cache for Hugging Face/PyTorch/Numba
ENV USER=codegalaxy
ENV HF_HOME=/app/data/hf_cache
ENV NUMBA_CACHE_DIR=/app/data/numba_cache

USER 1000

# Expose the default port
EXPOSE 7860

# Start FastAPI server binding to 0.0.0.0 and the dynamic HFS $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}
