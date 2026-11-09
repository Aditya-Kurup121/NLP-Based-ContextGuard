"""Educational Word2Vec (Skip-gram) model implemented in NumPy with analogies and cosine similarity."""
import math
import re
import threading
import uuid
from collections import Counter, OrderedDict
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


DEFAULT_CORPUS = [
    "alice and bob are close friends who play games together",
    "friends respect each other and enjoy playful banter online",
    "cyberbullying causes distress anxiety pain and social isolation",
    "harassment intimidation and threats cross personal boundaries",
    "toxic comments hurt people and create hostile environments",
    "bystanders can defend victims and intervene against bullies",
    "supportive friends help stop harassment and report abuse",
    "laughter humor and jokes characterize healthy friendly conversations",
    "violence threats and aggressive insults require urgent intervention",
    "online safety requires clear rules reporting tools and empathy",
    "king rule queen palace royalty leader crown monarch",
    "man woman boy girl father mother brother sister",
    "happy joyful delighted cheerful glad pleased positive",
    "sad unhappy depressed miserable gloomy distressed upset",
    "game gaming play player match team competition winner",
    "good great awesome wonderful fantastic excellent kind",
    "bad terrible awful horrible negative harmful hostile",
    "colleague coworker classmate partner teammate friend peer",
    "message chat conversation dialogue turn talk reply",
    "threat harm hurt attack violence danger concern",
    "respect kindness empathy compassion care understanding",
    "banter joke humor teasing laughter smile laugh",
]


class EducationalWord2Vec:
    """
    Skip-gram Word2Vec model with negative sampling using NumPy.
    Provides vector embeddings, cosine similarity, nearest neighbors, and word analogies.
    """

    def __init__(self, embedding_dim: int = 32, window_size: int = 2, learning_rate: float = 0.05):
        self.embedding_dim = embedding_dim
        self.window_size = window_size
        self.learning_rate = learning_rate
        self.vocab: Dict[str, int] = {}
        self.inv_vocab: List[str] = []
        self.W_in: Optional[np.ndarray] = None
        self.W_out: Optional[np.ndarray] = None
        self.trained_epochs = 0
        self.corpus_size = 0

    def _tokenize_corpus(self, sentences: List[str]) -> List[List[str]]:
        tokenized = []
        for s in sentences:
            tokens = re.findall(r"\b[a-zA-Z]+\b", s.lower())
            if tokens:
                tokenized.append(tokens)
        return tokenized

    def fit(self, sentences: List[str], epochs: int = 40, min_count: int = 1) -> "EducationalWord2Vec":
        tokenized = self._tokenize_corpus(sentences)
        self.corpus_size = len(tokenized)

        counts = Counter(token for s in tokenized for token in s)
        filtered_vocab = [w for w, c in counts.items() if c >= min_count]
        filtered_vocab.sort()

        if not filtered_vocab:
            raise ValueError("Corpus has no valid tokens.")

        self.vocab = {w: i for i, w in enumerate(filtered_vocab)}
        self.inv_vocab = filtered_vocab
        V = len(self.vocab)
        D = self.embedding_dim

        # Xavier/He initialization
        np.random.seed(42)
        self.W_in = np.random.uniform(-0.5 / D, 0.5 / D, (V, D))
        self.W_out = np.random.uniform(-0.5 / D, 0.5 / D, (D, V))

        # Build training pairs (target, context)
        pairs: List[Tuple[int, int]] = []
        for tokens in tokenized:
            indices = [self.vocab[w] for w in tokens if w in self.vocab]
            for i, target in enumerate(indices):
                start = max(0, i - self.window_size)
                end = min(len(indices), i + self.window_size + 1)
                for j in range(start, end):
                    if i != j:
                        pairs.append((target, indices[j]))

        if not pairs:
            return self

        # Unigram distribution for negative sampling
        word_freqs = np.array([counts[w] for w in self.inv_vocab], dtype=float)
        unigram_dist = word_freqs ** 0.75
        unigram_dist /= unigram_dist.sum()

        lr = self.learning_rate
        num_negatives = 3

        # Skip-gram with negative sampling SGD training
        for _ in range(epochs):
            np.random.shuffle(pairs)
            for target_idx, context_idx in pairs:
                # Positive pair
                h = self.W_in[target_idx]  # shape: (D,)
                v_pos = self.W_out[:, context_idx]  # shape: (D,)

                z_pos = np.dot(h, v_pos)
                sigmoid_pos = 1.0 / (1.0 + np.exp(-np.clip(z_pos, -6.0, 6.0)))
                grad_pos = sigmoid_pos - 1.0  # target is 1

                # Negative samples
                neg_indices = np.random.choice(V, size=num_negatives, p=unigram_dist)

                # Accumulate gradient for W_in[target_idx]
                grad_h = grad_pos * v_pos

                # Update W_out for positive context
                self.W_out[:, context_idx] -= lr * (grad_pos * h)

                for neg_idx in neg_indices:
                    v_neg = self.W_out[:, neg_idx]
                    z_neg = np.dot(h, v_neg)
                    sigmoid_neg = 1.0 / (1.0 + np.exp(-np.clip(z_neg, -6.0, 6.0)))
                    grad_neg = sigmoid_neg  # target is 0

                    grad_h += grad_neg * v_neg
                    self.W_out[:, neg_idx] -= lr * (grad_neg * h)

                # Update W_in for target word
                self.W_in[target_idx] -= lr * grad_h

        self.trained_epochs = epochs
        return self

    def get_vector(self, word: str) -> Optional[List[float]]:
        word = word.lower().strip()
        if self.W_in is None or word not in self.vocab:
            return None
        idx = self.vocab[word]
        # Average input and output vectors or use input vector
        vec = self.W_in[idx]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def cosine_similarity(self, word1: str, word2: str) -> Optional[float]:
        v1 = self.get_vector(word1)
        v2 = self.get_vector(word2)
        if v1 is None or v2 is None:
            return None
        u, v = np.array(v1), np.array(v2)
        sim = float(np.dot(u, v))
        return round(float(np.clip(sim, -1.0, 1.0)), 4)

    def nearest_neighbors(self, word: str, top_n: int = 6) -> List[Dict[str, Any]]:
        word = word.lower().strip()
        if self.W_in is None or word not in self.vocab:
            return []
        query_vec = np.array(self.get_vector(word))
        # Compute cosine similarity with all words
        results = []
        for other_word, idx in self.vocab.items():
            if other_word == word:
                continue
            other_vec = np.array(self.get_vector(other_word))
            sim = float(np.dot(query_vec, other_vec))
            results.append({"word": other_word, "similarity": round(sim, 4)})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_n]

    def analogy(self, word_a: str, word_b: str, word_c: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """Computes word analogy: word_a is to word_b as word_c is to ? (b - a + c)"""
        va = self.get_vector(word_a)
        vb = self.get_vector(word_b)
        vc = self.get_vector(word_c)
        if va is None or vb is None or vc is None:
            return []
        target = np.array(vb) - np.array(va) + np.array(vc)
        norm = np.linalg.norm(target)
        if norm > 0:
            target /= norm

        results = []
        excluded = {word_a.lower(), word_b.lower(), word_c.lower()}
        for other_word in self.vocab:
            if other_word in excluded:
                continue
            other_vec = np.array(self.get_vector(other_word))
            sim = float(np.dot(target, other_vec))
            results.append({"word": other_word, "similarity": round(sim, 4)})
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_n]

    def get_summary(self) -> Dict[str, Any]:
        return {
            "vocabulary_size": len(self.vocab),
            "embedding_dim": self.embedding_dim,
            "window_size": self.window_size,
            "trained_epochs": self.trained_epochs,
            "corpus_sentences": self.corpus_size,
            "sample_words": self.inv_vocab[:15],
            "method": "Skip-gram with Negative Sampling (SGNS) implemented in NumPy",
        }


# Global singleton instance trained on DEFAULT_CORPUS
_global_w2v: Optional[EducationalWord2Vec] = None


# Custom models trained from the workbench. Each gets its own id so one user's
# retraining never replaces the shared default model for everyone else.
MAX_CUSTOM_MODELS = 16
_custom_models: "OrderedDict[str, EducationalWord2Vec]" = OrderedDict()
_custom_lock = threading.Lock()


def get_word2vec_model(model_id: Optional[str] = None) -> EducationalWord2Vec:
    """Return the default model, or a custom one by id. Raises KeyError for an unknown id."""
    global _global_w2v
    if model_id:
        with _custom_lock:
            model = _custom_models[model_id]
            _custom_models.move_to_end(model_id)
            return model
    if _global_w2v is None:
        model = EducationalWord2Vec(embedding_dim=32, window_size=2, learning_rate=0.06)
        model.fit(DEFAULT_CORPUS, epochs=45)
        _global_w2v = model
    return _global_w2v


def train_custom_word2vec_model(sentences: List[str], epochs: int = 35) -> Tuple[str, EducationalWord2Vec]:
    """Train a separate model and store it under a new id (oldest evicted beyond MAX_CUSTOM_MODELS)."""
    model = EducationalWord2Vec(embedding_dim=32, window_size=2, learning_rate=0.06)
    model.fit(sentences, epochs=epochs)
    model_id = uuid.uuid4().hex
    with _custom_lock:
        _custom_models[model_id] = model
        while len(_custom_models) > MAX_CUSTOM_MODELS:
            _custom_models.popitem(last=False)
    return model_id, model

