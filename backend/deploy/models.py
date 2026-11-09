"""Move trained model files between backend/artifacts/ and a Hugging Face model repo.

The weights are git-ignored, so a deployed server fetches them from the Hub instead.

    # once, on the machine that trained the models (after `hf auth login`):
    python -m backend.deploy.models upload --repo your-name/contextguard-models

    # on the server, before starting the API (the Docker image does this):
    MODEL_REPO=your-name/contextguard-models python -m backend.deploy.models download

Keep the model repo private: the context model was trained partly on CONDA, which
has no licence for redistribution. The server then needs a read-only HF_TOKEN.
"""
import argparse
import logging
import os
from pathlib import Path

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

# Everything the API loads at runtime that is not in git.
PATTERNS = [
    "transformer/*",
    "context_model/*",
    "*.joblib",
    "*.tokenizer.json",
]

logger = logging.getLogger("contextguard.deploy")


def upload(repo: str, private: bool = True) -> None:
    from huggingface_hub import HfApi

    missing = [p for p in ("transformer", "context_model") if not (ARTIFACTS / p / "model.safetensors").exists()]
    if missing:
        logger.warning("Not found locally, will not be uploaded: %s", ", ".join(missing))
    api = HfApi()
    api.create_repo(repo, repo_type="model", private=private, exist_ok=True)
    api.upload_folder(
        repo_id=repo,
        repo_type="model",
        folder_path=ARTIFACTS,
        allow_patterns=PATTERNS,
        commit_message="Upload ContextGuard model artifacts",
    )
    logger.info("Uploaded to https://huggingface.co/%s", repo)


def download(repo: str | None) -> bool:
    """Fetch the artifacts into backend/artifacts. Returns False when nothing was configured."""
    if not repo:
        logger.warning("MODEL_REPO is not set: starting with the rule engine and any models already in the image.")
        return False
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=repo,
        repo_type="model",
        local_dir=ARTIFACTS,
        allow_patterns=PATTERNS,
        revision=os.getenv("MODEL_REVISION") or None,
    )
    logger.info("Model artifacts ready in %s", ARTIFACTS)
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    up = sub.add_parser("upload", help="push local artifacts to a Hub model repo")
    up.add_argument("--repo", required=True, help="e.g. your-name/contextguard-models")
    up.add_argument("--public", action="store_true", help="make the repo public (not recommended, see module docstring)")
    down = sub.add_parser("download", help="pull artifacts from the Hub (defaults to $MODEL_REPO)")
    down.add_argument("--repo", default=os.getenv("MODEL_REPO"))
    args = parser.parse_args()

    if args.command == "upload":
        upload(args.repo, private=not args.public)
    else:
        download(args.repo)


if __name__ == "__main__":
    main()
