"""Educational Hidden Markov Model (HMM) Part-of-Speech Tagger with Viterbi Decoding."""
import math
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Any, Optional

# Universal POS tag set
UNIVERSAL_TAGS = [
    "NOUN", "VERB", "ADJ", "ADV", "PRON", "DET", "ADP", "NUM", "CONJ", "PRT", ".", "X"
]

# Curated tagged sentences representing standard English dialogue, questions, and cyberbullying scenarios
BUILTIN_TAGGED_CORPUS = [
    [("the", "DET"), ("students", "NOUN"), ("are", "VERB"), ("studying", "VERB"), ("in", "ADP"), ("the", "DET"), ("library", "NOUN"), (".", ".")],
    [("alice", "NOUN"), ("sent", "VERB"), ("a", "DET"), ("message", "NOUN"), ("to", "ADP"), ("bob", "NOUN"), (".", ".")],
    [("you", "PRON"), ("are", "VERB"), ("such", "ADJ"), ("a", "DET"), ("genius", "NOUN"), (".", ".")],
    [("nobody", "PRON"), ("wants", "VERB"), ("you", "PRON"), ("in", "ADP"), ("this", "DET"), ("group", "NOUN"), (".", ".")],
    [("please", "PRT"), ("stop", "VERB"), ("calling", "VERB"), ("me", "PRON"), ("names", "NOUN"), (".", ".")],
    [("why", "ADV"), ("are", "VERB"), ("you", "PRON"), ("being", "VERB"), ("so", "ADV"), ("mean", "ADJ"), ("to", "ADP"), ("me", "PRON"), ("?", ".")],
    [("i", "PRON"), ("will", "VERB"), ("find", "VERB"), ("you", "PRON"), ("after", "ADP"), ("class", "NOUN"), ("tomorrow", "NOUN"), (".", ".")],
    [("alex", "NOUN"), ("defended", "VERB"), ("sam", "NOUN"), ("from", "ADP"), ("the", "DET"), ("aggressive", "ADJ"), ("bullies", "NOUN"), (".", ".")],
    [("they", "PRON"), ("played", "VERB"), ("an", "DET"), ("exciting", "ADJ"), ("game", "NOUN"), ("together", "ADV"), (".", ".")],
    [("we", "PRON"), ("must", "VERB"), ("protect", "VERB"), ("online", "ADJ"), ("communities", "NOUN"), ("with", "ADP"), ("empathy", "NOUN"), (".", ".")],
    [("she", "PRON"), ("laughed", "VERB"), ("loudly", "ADV"), ("at", "ADP"), ("his", "PRON"), ("playful", "ADJ"), ("joke", "NOUN"), (".", ".")],
    [("good", "ADJ"), ("friends", "NOUN"), ("support", "VERB"), ("each", "DET"), ("other", "ADJ"), ("always", "ADV"), (".", ".")],
    [("he", "PRON"), ("apologized", "VERB"), ("sincerely", "ADV"), ("for", "ADP"), ("his", "PRON"), ("harsh", "ADJ"), ("words", "NOUN"), (".", ".")],
    [("two", "NUM"), ("classmates", "NOUN"), ("reported", "VERB"), ("the", "DET"), ("threat", "NOUN"), ("yesterday", "NOUN"), (".", ".")],
    [("can", "VERB"), ("someone", "PRON"), ("share", "VERB"), ("the", "DET"), ("project", "NOUN"), ("slides", "NOUN"), ("now", "ADV"), ("?", ".")],
    [("this", "DET"), ("behavior", "NOUN"), ("is", "VERB"), ("completely", "ADV"), ("unacceptable", "ADJ"), (".", ".")],
    [("never", "ADV"), ("send", "VERB"), ("abusive", "ADJ"), ("messages", "NOUN"), ("to", "ADP"), ("anyone", "PRON"), (".", ".")],
    [("great", "ADJ"), ("work", "NOUN"), ("on", "ADP"), ("the", "DET"), ("presentation", "NOUN"), ("today", "NOUN"), (".", ".")],
    [("i", "PRON"), ("am", "VERB"), ("not", "ADV"), ("happy", "ADJ"), ("about", "ADP"), ("this", "DET"), ("situation", "NOUN"), (".", ".")],
    [("just", "ADV"), ("leave", "VERB"), ("her", "PRON"), ("alone", "ADJ"), (".", ".")],
]


class HiddenMarkovModelTagger:
    """
    First-order Hidden Markov Model POS tagger with Viterbi decoding.
    States = POS tags, Observations = word tokens.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha  # Laplace smoothing parameter
        self.tags = list(UNIVERSAL_TAGS)
        self.tag_to_idx = {tag: i for i, tag in enumerate(self.tags)}
        self.vocab: set = set()
        self.initial_log_probs: Dict[str, float] = {}
        self.transition_log_probs: Dict[str, Dict[str, float]] = {}
        self.emission_log_probs: Dict[str, Dict[str, float]] = {}
        self.tag_counts: Counter = Counter()
        self.word_counts: Counter = Counter()
        self.total_sentences = 0

    def fit(self, tagged_corpus: List[List[Tuple[str, str]]]) -> "HiddenMarkovModelTagger":
        self.total_sentences = len(tagged_corpus)
        initial_counts = Counter()
        transition_counts = defaultdict(Counter)
        emission_counts = defaultdict(Counter)
        self.tag_counts = Counter()
        self.word_counts = Counter()
        self.vocab = set()

        for sentence in tagged_corpus:
            if not sentence:
                continue
            first_tag = sentence[0][1]
            initial_counts[first_tag] += 1

            for i, (word, tag) in enumerate(sentence):
                w_lower = word.lower()
                self.vocab.add(w_lower)
                self.word_counts[w_lower] += 1
                self.tag_counts[tag] += 1
                emission_counts[tag][w_lower] += 1

                if i > 0:
                    prev_tag = sentence[i - 1][1]
                    transition_counts[prev_tag][tag] += 1

        V_size = len(self.vocab)
        T_size = len(self.tags)
        alpha = self.alpha

        # Compute initial log probabilities with Laplace smoothing
        total_initial = sum(initial_counts.values())
        self.initial_log_probs = {
            t: math.log((initial_counts[t] + alpha) / (total_initial + alpha * T_size))
            for t in self.tags
        }

        # Compute transition log probabilities A[t1][t2]
        self.transition_log_probs = {t1: {} for t1 in self.tags}
        for t1 in self.tags:
            t1_count = self.tag_counts[t1]
            denom = t1_count + alpha * T_size
            for t2 in self.tags:
                self.transition_log_probs[t1][t2] = math.log((transition_counts[t1][t2] + alpha) / denom)

        # Compute emission log probabilities B[t][w]
        self.emission_log_probs = {t: {} for t in self.tags}
        for t in self.tags:
            t_count = self.tag_counts[t]
            denom = t_count + alpha * (V_size + 1)
            for w in self.vocab:
                count = emission_counts[t][w]
                self.emission_log_probs[t][w] = math.log((count + alpha) / denom)
            # Default for unknown words
            self.emission_log_probs[t]["<UNK>"] = math.log(alpha / denom)

        return self

    def _get_emission_log_prob(self, tag: str, word: str) -> float:
        w_lower = word.lower()
        if w_lower in self.emission_log_probs[tag]:
            return self.emission_log_probs[tag][w_lower]

        # Morphological heuristics for unknown words
        base_unk = self.emission_log_probs[tag]["<UNK>"]
        if w_lower.endswith("ing"):
            bonus = 2.0 if tag == "VERB" else -1.0
        elif w_lower.endswith("ed"):
            bonus = 2.0 if tag == "VERB" else -1.0
        elif w_lower.endswith("ly"):
            bonus = 2.5 if tag == "ADV" else -1.0
        elif w_lower.endswith("ous") or w_lower.endswith("ful") or w_lower.endswith("able") or w_lower.endswith("ive"):
            bonus = 2.5 if tag == "ADJ" else -1.0
        elif w_lower.endswith("tion") or w_lower.endswith("ment") or w_lower.endswith("ness"):
            bonus = 2.5 if tag == "NOUN" else -1.0
        elif w_lower.endswith("s"):
            bonus = 1.0 if tag in ("NOUN", "VERB") else -0.5
        elif word[0].isupper() and word.isalpha():
            bonus = 1.5 if tag == "NOUN" else -0.5
        elif re.match(r"^\d+$", word):
            bonus = 3.0 if tag == "NUM" else -2.0
        elif not word.isalnum():
            bonus = 3.0 if tag == "." else -2.0
        else:
            bonus = 0.5 if tag == "NOUN" else 0.0

        return base_unk + bonus

    def viterbi(self, tokens: List[str]) -> Tuple[List[str], float, List[Dict[str, float]]]:
        """
        Executes Viterbi decoding to find the optimal POS tag sequence.
        Returns: (predicted_tags, log_likelihood, trellis_steps)
        """
        if not tokens:
            return [], 0.0, []

        N = len(tokens)
        T = len(self.tags)

        # V[step][tag_idx] stores max log probability
        V = [{tag: 0.0 for tag in self.tags} for _ in range(N)]
        backpointers = [{tag: "" for tag in self.tags} for _ in range(N)]

        # Step 0: Initialization
        first_word = tokens[0]
        for tag in self.tags:
            init_p = self.initial_log_probs[tag]
            emit_p = self._get_emission_log_prob(tag, first_word)
            V[0][tag] = init_p + emit_p

        # Steps 1 to N - 1: Induction
        for t in range(1, N):
            curr_word = tokens[t]
            for curr_tag in self.tags:
                emit_p = self._get_emission_log_prob(curr_tag, curr_word)
                best_prev_score = -float("inf")
                best_prev_tag = self.tags[0]

                for prev_tag in self.tags:
                    trans_p = self.transition_log_probs[prev_tag][curr_tag]
                    score = V[t - 1][prev_tag] + trans_p
                    if score > best_prev_score:
                        best_prev_score = score
                        best_prev_tag = prev_tag

                V[t][curr_tag] = best_prev_score + emit_p
                backpointers[t][curr_tag] = best_prev_tag

        # Termination: best final state
        best_final_score = -float("inf")
        best_final_tag = self.tags[0]
        for tag in self.tags:
            if V[N - 1][tag] > best_final_score:
                best_final_score = V[N - 1][tag]
                best_final_tag = tag

        # Backtracking
        best_path = [best_final_tag]
        for t in range(N - 1, 0, -1):
            prev_tag = backpointers[t][best_path[-1]]
            best_path.append(prev_tag)

        best_path.reverse()
        return best_path, round(best_final_score, 4), V


_global_hmm: Optional[HiddenMarkovModelTagger] = None


def get_hmm_tagger() -> HiddenMarkovModelTagger:
    global _global_hmm
    if _global_hmm is None:
        tagger = HiddenMarkovModelTagger(alpha=1.0)
        tagger.fit(BUILTIN_TAGGED_CORPUS)
        _global_hmm = tagger
    return _global_hmm

