from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, f1_score
from .knowledge import read_fixture


@lru_cache(maxsize=1)
def model():
    rows = read_fixture("tickets.json")["train"]
    pipeline = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
        LogisticRegression(C=5, max_iter=1000, random_state=42),
    )
    pipeline.fit([r["text"] for r in rows], [r["label"] for r in rows])
    return pipeline


def classify(text):
    pipeline = model()
    probabilities = pipeline.predict_proba([text])[0]
    index = int(probabilities.argmax())
    score = float(probabilities[index])
    return {
        "label": str(pipeline.classes_[index]) if score >= 0.30 else "general",
        "model_score": round(score, 3),
        "model": "TF-IDF + logistic regression",
    }


def evaluate_classifier():
    rows = read_fixture("tickets.json")["test"]
    truth = [r["label"] for r in rows]
    prediction = model().predict([r["text"] for r in rows]).tolist()
    return {
        "test_examples": len(rows),
        "accuracy": round(accuracy_score(truth, prediction), 4),
        "macro_f1": round(
            f1_score(truth, prediction, average="macro", zero_division=0), 4
        ),
        "majority_baseline_accuracy": round(
            max(truth.count(t) for t in set(truth)) / len(truth), 4
        ),
        "labels": sorted(set(truth)),
        "predictions": [{**r, "predicted": p} for r, p in zip(rows, prediction)],
    }
