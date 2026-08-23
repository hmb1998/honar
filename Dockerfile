FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    YOUTUBE_POT_PROVIDER_URL=http://127.0.0.1:4416

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg ca-certificates curl unzip git \
    && rm -rf /var/lib/apt/lists/*

# Modern yt-dlp YouTube extraction uses a JS runtime.
RUN curl -fsSL https://deno.land/install.sh | sh \
    && ln -sf /root/.deno/bin/deno /usr/local/bin/deno

# BgUtils PO-token HTTP provider. Keep the provider version aligned with
# bgutil-ytdlp-pot-provider in requirements.txt.
RUN git clone --depth 1 --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /opt/bgutil-ytdlp-pot-provider \
    && cd /opt/bgutil-ytdlp-pot-provider/server \
    && deno install --allow-scripts=npm:canvas --frozen

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

# IMPORTANT: do NOT import bgutil_ytdlp_pot_provider in Python.
# It is a yt-dlp plugin discovered automatically by yt-dlp.
RUN python -m pip show bgutil-ytdlp-pot-provider >/dev/null \
    && python -c "import yt_dlp; print('yt-dlp:', yt_dlp.version.__version__)"

CMD ["sh", "-c", "deno run -A /opt/bgutil-ytdlp-pot-provider/server/src/main.ts >/tmp/bgutil-pot.log 2>&1 & for i in $(seq 1 30); do if curl -fsS http://127.0.0.1:4416/ping >/dev/null 2>&1; then echo \"BgUtils PO-token provider is ready\"; break; fi; sleep 1; done; python web_server.py & exec python main.py"]
