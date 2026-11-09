# ContextGuard API (FastAPI backend), CPU only.
# Works on Hugging Face Spaces (Docker SDK), Render, Railway, Fly.io, Cloud Run or any VM.
#
#   docker build -t contextguard-api .
#   docker run -p 7860:7860 -e MODEL_REPO=your-name/contextguard-models -e HF_TOKEN=hf_... \
#     -e CORS_ORIGINS=https://your-app.vercel.app contextguard-api
#
# Model weights are not in git: the container downloads them from MODEL_REPO on start.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=7860 \
    HF_HOME=/tmp/hf-cache

# Hugging Face Spaces runs containers as user 1000; other hosts don't mind.
RUN useradd --create-home --uid 1000 app
WORKDIR /home/app/contextguard

# CPU-only PyTorch (~200 MB instead of ~2.5 GB for the CUDA build).
RUN pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements-deploy.txt backend/requirements-deploy.txt
RUN pip install -r backend/requirements-deploy.txt

COPY --chown=app:app backend backend
COPY --chown=app:app deploy/start.sh deploy/start.sh

USER app
EXPOSE 7860
CMD ["sh", "deploy/start.sh"]
