"""Download a versioned public dataset. No data is uploaded."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

DESTINATION = Path(__file__).resolve().parents[1] / "data" / "raw"
REPOSITORY = "SetFit/toxic_conversations_50k"
REVISION = "ef2009a5444b8a278c4d0782bcc549a01fd0163d"


def download(revision=REVISION):
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for filename in ("train.jsonl", "test.jsonl", "README.md"):
        with urlopen(f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{revision}/{filename}", timeout=90) as response:
            payload = response.read()
        name = "DATASET_CARD.md" if filename == "README.md" else filename
        (DESTINATION / name).write_bytes(payload)
        print(f"{name}: {len(payload)} bytes, SHA256 {hashlib.sha256(payload).hexdigest()}")
    (DESTINATION / "revision.txt").write_text(revision, encoding="utf-8")


if __name__ == "__main__":
    download()
