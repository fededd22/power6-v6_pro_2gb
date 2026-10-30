# ═══════════════════════════════════════════════════════════════
# OOREDOO BOT — Docker Image
# Python 3.11 Slim + Async + SQLite WAL
# ═══════════════════════════════════════════════════════════════

FROM python:3.11-slim

# ─── Metadata ───
LABEL maintainer="moon" \
      version="3.0.0" \
      description="Ooredoo Bot - Async Edition (handles 500+ concurrent users)"

# ─── Environment ───
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Africa/Algiers

# ─── System dependencies ───
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        tzdata \
        sqlite3 \
        libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# ─── Working directory ───
WORKDIR /app

# ─── Python dependencies (layered cache) ───
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Application code ───
COPY bot.py .

# ─── Data directory (persistent volume) ───
RUN mkdir -p /app/data && chmod 755 /app/data
VOLUME ["/app/data"]

# ─── Non-root user ───
RUN useradd -m -u 1000 -s /bin/bash moon && \
    chown -R moon:moon /app
USER moon

# ─── Health check (process alive) ───
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python.*bot.py" > /dev/null || exit 1

# ─── Run ───
CMD ["python", "-u", "bot.py"]
