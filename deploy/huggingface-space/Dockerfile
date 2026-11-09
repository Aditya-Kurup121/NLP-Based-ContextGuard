# Hugging Face Space for the ContextGuard API.
# Copy this file and README.md (next to it) into a new Docker Space. The Space
# builds from the public GitHub repo, so "Factory rebuild" picks up new commits.
FROM python:3.12-slim

ARG REPO_URL=https://github.com/Aditya-Kurup121/NLP-Based-ContextGuard.git
ARG GIT_REF=main

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=7860 \
    HF_HOME=/tmp/hf-cache

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 app
WORKDIR /home/app/contextguard

RUN pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu
RUN git clone --depth 1 --branch "$GIT_REF" "$REPO_URL" /tmp/src \
 && pip install -r /tmp/src/backend/requirements-deploy.txt \
 && cp -r /tmp/src/backend /tmp/src/deploy . \
 && rm -rf /tmp/src \
 && chown -R app:app /home/app/contextguard

USER app
EXPOSE 7860
CMD ["sh", "deploy/start.sh"]
