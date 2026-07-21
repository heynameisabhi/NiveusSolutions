# ─── Backend Dockerfile ──────────────────────────────────────────────────────
# Veritas Claims Analytics — FastAPI Backend
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Prevents Python from writing .pyc files and enables stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS-level dependencies
# gosu: used by entrypoint.sh to drop from root → appuser after fixing volume perms
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source
COPY . .

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Make entrypoint executable (runs as root, then drops to appuser at runtime)
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# entrypoint.sh fixes /data volume ownership then execs as appuser
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
