FROM python:3.10-slim

WORKDIR /code

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

# FIX: install the CPU-only torch build first. The default PyPI `torch`
# wheel bundles CUDA and is ~2GB+, which risks blowing past build
# time/image-size limits on small hosting tiers (e.g. Render free/starter)
# and is completely unnecessary since this app never uses a GPU. Once this
# exact version is installed, the requirements.txt line for torch is
# already satisfied and pip will not re-download/reinstall it below.
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FIX: bake the sentence-transformer model into the image at build time
# instead of letting it download on the first live request. This avoids a
# slow/failed cold start if outbound network access is restricted at
# runtime, and means the model is already on disk (no repeated downloads
# across container restarts on platforms with ephemeral filesystems).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
