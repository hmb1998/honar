FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    YOUTUBE_POT_PROVIDER_URL=http://127.0.0.1:4416

WORKDIR /app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
        curl \
        unzip \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Deno
# Modern yt-dlp YouTube extraction uses a JS runtime.
RUN curl -fsSL https://deno.land/install.sh | sh \
    && ln -sf /root/.deno/bin/deno /usr/local/bin/deno

# Install BgUtils PO-token provider
RUN git clone \
        --depth 1 \
        --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /opt/bgutil-ytdlp-pot-provider \
    && cd /opt/bgutil-ytdlp-pot-provider/server \
    && deno install \
        --allow-scripts=npm:canvas \
        --frozen

# Install Python dependencies
COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Copy project
COPY . .

# Verify important Python packages
RUN python -m pip show bgutil-ytdlp-pot-provider >/dev/null \
    && python -c "import yt_dlp; print('yt-dlp:', yt_dlp.version.__version__)"

# Start:
# 1. Public Render health server
# 2. Internal BgUtils provider on 127.0.0.1:4416
# 3. Discord bot
CMD ["sh", "-c", "\
python web_server.py >/tmp/hmb-web.log 2>&1 & \
WEB_PID=$!; \
for i in $(seq 1 15); do \
    if curl -fsS http://127.0.0.1:${PORT:-10000}/healthz >/dev/null 2>&1; then \
        echo \"HMB health server is ready on ${PORT:-10000}\"; \
        break; \
    fi; \
    sleep 1; \
done; \
deno run -A /opt/bgutil-ytdlp-pot-provider/server/src/main.ts \
    --host 127.0.0.1 \
    --port 4416 \
    >/tmp/bgutil-pot.log 2>&1 & \
for i in $(seq 1 30); do \
    if curl -fsS http://127.0.0.1:4416/ping >/dev/null 2>&1; then \
        echo \"BgUtils PO-token provider is ready on 127.0.0.1:4416\"; \
        break; \
    fi; \
    sleep 1; \
done; \
exec python main.py"]
