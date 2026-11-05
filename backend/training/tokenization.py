"""Train small educational subword vocabularies, not transformer weights."""
from sklearn.model_selection import train_test_split
from tokenizers import Tokenizer, models, trainers, normalizers, pre_tokenizers, decoders
from backend.training.train import ROOT, read_unique


def train_tokenizers():
    rows = read_unique(ROOT / "data" / "raw" / "train.jsonl")
    text, labels = zip(*rows.values())
    train_x, _, _, _ = train_test_split(list(text), list(labels), test_size=.2, random_state=42, stratify=labels)
    wordpiece = Tokenizer(models.WordPiece(unk_token="[UNK]"))
    wordpiece.normalizer = normalizers.Sequence([normalizers.NFKC(), normalizers.Lowercase()])
    wordpiece.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
    wordpiece.decoder = decoders.WordPiece(prefix="##")
    wordpiece.train_from_iterator(train_x, trainers.WordPieceTrainer(vocab_size=8000, min_frequency=3, special_tokens=["[UNK]"]))
    bpe = Tokenizer(models.BPE(unk_token="[UNK]"))
    bpe.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    bpe.decoder = decoders.ByteLevel()
    bpe.train_from_iterator(train_x, trainers.BpeTrainer(vocab_size=8000, min_frequency=3, special_tokens=["[UNK]"], initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    for name, tokenizer in (("wordpiece", wordpiece), ("bpe", bpe)):
        tokenizer.save(str(ROOT / "artifacts" / f"{name}.tokenizer.json"))
        print(f"{name}: {tokenizer.get_vocab_size()} tokens; fitted on training split only")


if __name__ == "__main__":
    train_tokenizers()
