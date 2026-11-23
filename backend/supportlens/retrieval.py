import math
import re
import threading
from collections import Counter
from functools import lru_cache
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

STOP_WORDS = set(ENGLISH_STOP_WORDS) | {
    "hello",
    "hi",
    "please",
    "thanks",
    "thank",
    "help",
    "tell",
    "need",
    "want",
    "know",
    "does",
}


def tokenize(text):
    return [
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if word not in STOP_WORDS and len(word) > 1
    ]


@lru_cache(maxsize=2)
def load_embedding_model(model_name):
    from sentence_transformers import SentenceTransformer

    # Leave Apple GPU memory available to the language model.
    return SentenceTransformer(model_name, device="cpu")


class Retriever:
    """Small-corpus reference implementation. No hidden hosted search dependency."""

    def __init__(
        self, semantic=False, model_name="sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.semantic = semantic
        self.model_name = model_name
        self._signature = None
        self._dense_signature = None
        self._model = None
        self._lock = threading.RLock()

    def _index(self, corpus):
        signature = tuple((c["id"], c["text"], c["title"]) for c in corpus)
        if signature == self._signature:
            return
        self._tokens = [tokenize(c["title"] + " " + c["text"]) for c in corpus]
        self._counts = [Counter(t) for t in self._tokens]
        self._df = Counter(t for tokens in self._tokens for t in set(tokens))
        self._avg_length = max(1, sum(map(len, self._tokens)) / len(corpus))
        self._vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        )
        texts = [c["title"] + " " + c["text"] for c in corpus]
        try:
            self._matrix = self._vectorizer.fit_transform(texts)
        except ValueError:
            self._matrix = None
        self._signature = signature

    def _dense_index(self, corpus):
        if self._dense_signature != self._signature:
            if self._model is None:
                self._model = load_embedding_model(self.model_name)
            self._embeddings = self._model.encode(
                [c["title"] + " " + c["text"] for c in corpus],
                normalize_embeddings=True,
            )
            self._dense_signature = self._signature

    def search(self, question, corpus, method="hybrid", limit=3):
        if not corpus or not tokenize(question):
            return []
        with self._lock:
            self._index(corpus)
            query_tokens = set(tokenize(question))
            bm25 = np.zeros(len(corpus))
            for i, counts in enumerate(self._counts):
                for token in query_tokens:
                    freq = counts[token]
                    if freq:
                        idf = math.log(
                            1
                            + (len(corpus) - self._df[token] + 0.5)
                            / (self._df[token] + 0.5)
                        )
                        denominator = freq + 1.5 * (
                            0.25 + 0.75 * len(self._tokens[i]) / self._avg_length
                        )
                        bm25[i] += idf * freq * 2.5 / denominator
            tfidf = (
                np.zeros(len(corpus))
                if self._matrix is None
                else (self._matrix @ self._vectorizer.transform([question]).T)
                .toarray()
                .ravel()
            )
            dense = None
            if self.semantic and method == "hybrid":
                self._dense_index(corpus)
                dense = (
                    self._embeddings
                    @ self._model.encode([question], normalize_embeddings=True)[0]
                )
            if method == "bm25":
                scores = bm25
            else:
                # Reciprocal rank fusion makes incompatible score scales comparable.
                scores = np.zeros(len(corpus))
                for values in [bm25, dense if dense is not None else tfidf]:
                    for rank, index in enumerate(np.argsort(-values, kind="stable")):
                        if values[index] > 0:
                            scores[index] += 1 / (60 + rank + 1)
            results = []
            for index in np.argsort(-scores, kind="stable"):
                coverage = len(query_tokens.intersection(self._tokens[index])) / max(
                    1, len(query_tokens)
                )
                # Conservative lexical gate; dense mode may also accept a strong semantic match.
                eligible = (tfidf[index] >= 0.075 and coverage >= 0.20) or (
                    dense is not None and dense[index] >= 0.42
                )
                if scores[index] > 0 and eligible:
                    results.append(
                        {
                            **corpus[index],
                            "score": round(float(scores[index]), 5),
                            "similarity": round(
                                float(
                                    dense[index] if dense is not None else tfidf[index]
                                ),
                                4,
                            ),
                        }
                    )
                if len(results) >= limit:
                    break
            return results
