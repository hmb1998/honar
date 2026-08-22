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

RUN python -c "import yt_dlp, bgutil_ytdlp_pot_provider; print('yt-dlp + bgutil POT plugin OK')"

CMD ["sh", "-c", "python web_server.py & exec python main.py"]
