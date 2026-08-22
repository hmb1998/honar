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

# Deno is used by modern yt-dlp for YouTube JavaScript challenges and by
# BgUtils for generating Proof-of-Origin tokens without a browser cookie.
RUN curl -fsSL https://deno.land/install.sh | sh \
    && ln -sf /root/.deno/bin/deno /usr/local/bin/deno

# BgUtils PO-token provider. This is used as an anonymous YouTube fallback
# for Railway/datacenter IPs that trigger YouTube's bot check.
RUN git clone --depth 1 --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /opt/bgutil-ytdlp-pot-provider \
    && cd /opt/bgutil-ytdlp-pot-provider/server \
    && deno install --allow-scripts=npm:canvas --frozen

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip install -U yt-dlp-ejs==0.8.0 bgutil-ytdlp-pot-provider==1.3.1

COPY . .

# Start the POT provider, web health server, and Discord bot in one Railway
# container. The provider listens only on localhost and is not publicly exposed.
CMD ["sh", "-c", "cd /opt/bgutil-ytdlp-pot-provider/server/node_modules && deno run --allow-env --allow-net --allow-ffi=. --allow-read=. ../src/main.ts --port 4416 >/tmp/bgutil.log 2>&1 & python web_server.py & exec python main.py"]
