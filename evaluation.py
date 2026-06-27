import csv
import sys
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# Import your verifier from modules
from modules.citation_verifier import verify_citation

def load_dataset(file_path):
    """
    Load citations dataset from CSV.
    Returns a list of citation dicts with ground truth labels.
    """
    citations = []
    try:
        with open(file_path, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                citations.append({
                    "id": row["ID"],
                    "authors": row["Author"],
                    "title": row["Title"],
                    "year": row["Year"],
                    "venue": row["Venue"],
                    "true_label": row["Label"].strip().lower(),
                    "doi": row["DOI"]
                })
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        sys.exit(1)

    return citations


def run_verification(citations):
    """
    Run citation_verifier on each citation and collect predictions.
    """
    y_true, y_pred = [], []
    for c in citations:
        result = verify_citation({
            "title": c["title"],
            "authors": c["authors"],
            "year": c["year"],
            "venue": c["venue"],
            "doi": c["doi"],
            "raw": c["title"]  # fallback raw text
        })
        y_true.append(c["true_label"])
        y_pred.append(result["status"].lower())
    return y_true, y_pred


def evaluate(y_true, y_pred):
    """
    Evaluate predictions with multiple metrics.
    Supports multi-class evaluation for: valid, partially_valid, hallucinated.
    """
    labels = ["valid", "partially_valid", "hallucinated"]

    print("\n=== Evaluation Results ===")
    print(f"Total samples: {len(y_true)}")
    print(f"Overall Accuracy: {accuracy_score(y_true, y_pred):.3f}")

    print("\nConfusion Matrix (rows = true, cols = predicted):")
    print(confusion_matrix(y_true, y_pred, labels=labels))

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, labels=labels, digits=3))

    print("\nPer-Class Metrics:")
    for label in labels:
        precision = precision_score(y_true, y_pred, labels=[label], average="micro")
        recall = recall_score(y_true, y_pred, labels=[label], average="micro")
        f1 = f1_score(y_true, y_pred, labels=[label], average="micro")
        support = sum(1 for t in y_true if t == label)
        print(f"{label:15} | Precision: {precision:.3f} | Recall: {recall:.3f} | F1: {f1:.3f} | Support: {support}")


if __name__ == "__main__":
    dataset_file = "data/citations_dataset.csv"
    if len(sys.argv) > 1:
        dataset_file = sys.argv[1]

    citations = load_dataset(dataset_file)
    y_true, y_pred = run_verification(citations)
    evaluate(y_true, y_pred)
