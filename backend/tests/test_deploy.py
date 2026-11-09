from fnmatch import fnmatch

from backend.deploy import models


def test_download_without_repo_is_a_no_op():
    assert models.download(None) is False


def test_upload_patterns_cover_every_runtime_artifact():
    needed = ["transformer/model.safetensors", "context_model/tokenizer.json", "context_model/contextguard.json",
              "toxicity.joblib", "combiner.joblib", "wordpiece.tokenizer.json"]
    for path in needed:
        assert any(fnmatch(path, p) for p in models.PATTERNS), path
