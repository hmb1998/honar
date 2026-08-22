FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg ca-certificates curl unzip git \
    && rm -rf /var/lib/apt/lists/*

# Deno is used by modern yt-dlp and the BgUtils POT script.
RUN curl -fsSL https://deno.land/install.sh | sh \
    && ln -sf /root/.deno/bin/deno /usr/local/bin/deno

# Install BgUtils POT provider source. In script mode yt-dlp invokes the
# provider directly, so Railway does not need a second localhost server.
RUN git clone --depth 1 --branch 1.3.1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /opt/bgutil-ytdlp-pot-provider \
    && cd /opt/bgutil-ytdlp-pot-provider/server \
    && deno install --allow-scripts=npm:canvas --frozen

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

# Verify the actual plugin is discoverable by yt-dlp. The PyPI package is a
# yt-dlp plugin and is intentionally NOT imported as a top-level Python module.
RUN python -m pip show bgutil-ytdlp-pot-provider >/dev/null \
    && python -c "import yt_dlp; print('yt-dlp OK')"

# Run the POT provider locally in the same Railway container, then start the bot.
CMD ["sh", "-c", "deno run -A /opt/bgutil-ytdlp-pot-provider/server/src/main.ts >/tmp/bgutil-pot.log 2>&1 & python web_server.py & exec python main.py"]
