FROM python:3.11-slim

# System deps: libgeos for shapely, build tools for wheels that lack binaries
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces convention: run as UID 1000
RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/home/user/.cache/huggingface \
    ARTIFACTS_DIR=/home/user/data

WORKDIR $HOME/app

# Python deps (layer cached on requirements.txt)
COPY --chown=user requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# Pre-download NLTK corpora so first /api/search doesn't block on a net fetch
RUN python -c "import nltk; [nltk.download(p, quiet=True) for p in ('punkt','punkt_tab','wordnet')]"

# App code
COPY --chown=user app/ ./app/
COPY --chown=user src/ ./src/
COPY --chown=user entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 7860
CMD ["./entrypoint.sh"]
