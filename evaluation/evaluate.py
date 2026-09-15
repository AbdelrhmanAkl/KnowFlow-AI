import sys
import json
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

import pandas as pd

from src.knowledge_base import load_knowledge_base
from src.retrieval.retriever import retrieve_documents


# ============================================================
# CONFIGURATION
# ============================================================

EVALUATION_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1GONF_2lzc8co_QCxYyaF2WK0sHYpR1oYCrd6TkXvYhg"
    "/export?format=xlsx"
)

EVALUATION_SHEET = "Evaluation Questions"

KNOWLEDGE_BASE_PATH = (
    PROJECT_ROOT / "data" / "knowledge_base"
)

RESULTS_PATH = (
    PROJECT_ROOT / "evaluation" / "results.json"
)

TOP_K = 4


# ============================================================
# TOPIC EXTRACTION
# ============================================================

def extract_topic(document) -> str:
    """
    Extract the Topic field from a retrieved knowledge-base document.

    Google Sheet documents are expected to contain structured
    fields such as:

        ID:
        Category:
        Topic:
        Question:
        Answer:

    PDF documents may not contain a Topic field, so they are
    safely classified as Unknown.
    """

    if not document or not getattr(document, "page_content", None):
        return "Unknown"

    for line in document.page_content.splitlines():
        line = line.strip()

        if line.lower().startswith("topic:"):
            topic = line.split(":", 1)[1].strip()

            if topic:
                return topic

    return "Unknown"


# ============================================================
# RETRIEVAL EVALUATION
# ============================================================

def evaluate_retrieval() -> dict:
    """
    Evaluate the KnowFlow-AI retrieval system.

    Metrics:

        Hit@1:
            Expected Topic appears as the first retrieved topic.

        Hit@4:
            Expected Topic appears anywhere in the top 4
            retrieved documents.

    Important:
        These metrics evaluate retrieval against the
        Expected Topic field. They are NOT generation
        accuracy metrics.
    """

    print("=" * 72)
    print("KnowFlow-AI | Retrieval Evaluation")
    print("=" * 72)

    # --------------------------------------------------------
    # STEP 1 — Load evaluation dataset
    # --------------------------------------------------------

    print("\n[1/4] Loading evaluation dataset...")

    try:
        evaluation_df = pd.read_excel(
            EVALUATION_URL,
            sheet_name=EVALUATION_SHEET,
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to load the Evaluation Questions sheet."
        ) from exc

    required_columns = {
        "Test ID",
        "Question",
        "Expected Topic",
        "Expected Source Type",
        "Difficulty",
    }

    missing_columns = required_columns - set(
        evaluation_df.columns
    )

    if missing_columns:
        raise ValueError(
            "Evaluation sheet is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    print(
        f"Evaluation questions loaded: "
        f"{len(evaluation_df)}"
    )

    # --------------------------------------------------------
    # STEP 2 — Load knowledge base
    # --------------------------------------------------------

    print("\n[2/4] Loading FAISS knowledge base...")

    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(
            "Knowledge base was not found at:\n"
            f"{KNOWLEDGE_BASE_PATH}"
        )

    knowledge_base = load_knowledge_base(
        KNOWLEDGE_BASE_PATH
    )

    print("Knowledge base loaded successfully.")

    # --------------------------------------------------------
    # STEP 3 — Evaluate retrieval
    # --------------------------------------------------------

    print("\n[3/4] Running retrieval evaluation...")
    print("-" * 72)

    results = []

    hit_at_1 = 0
    hit_at_4 = 0

    for _, row in evaluation_df.iterrows():

        test_id = str(row["Test ID"]).strip()

        question = str(row["Question"]).strip()

        expected_topic = str(
            row["Expected Topic"]
        ).strip()

        expected_source_type = str(
            row["Expected Source Type"]
        ).strip()

        difficulty = str(
            row["Difficulty"]
        ).strip()

        # ----------------------------------------------------
        # Retrieve documents
        # ----------------------------------------------------

        documents = retrieve_documents(
            vector_store=knowledge_base,
            query=question,
            k=TOP_K,
        )

        # ----------------------------------------------------
        # Extract retrieved topics
        # ----------------------------------------------------

        retrieved_topics = [
            extract_topic(document)
            for document in documents
        ]

        # ----------------------------------------------------
        # Normalize topics for comparison
        # ----------------------------------------------------

        expected_normalized = (
            expected_topic.casefold().strip()
        )

        retrieved_normalized = [
            topic.casefold().strip()
            for topic in retrieved_topics
        ]

        # ----------------------------------------------------
        # Hit@1
        # ----------------------------------------------------

        hit1 = (
            bool(retrieved_normalized)
            and retrieved_normalized[0]
            == expected_normalized
        )

        # ----------------------------------------------------
        # Hit@4
        # ----------------------------------------------------

        hit4 = (
            expected_normalized
            in retrieved_normalized
        )

        if hit1:
            hit_at_1 += 1

        if hit4:
            hit_at_4 += 1

        # ----------------------------------------------------
        # Store detailed result
        # ----------------------------------------------------

        result = {
            "test_id": test_id,
            "question": question,
            "expected_topic": expected_topic,
            "expected_source_type": expected_source_type,
            "difficulty": difficulty,
            "retrieved_topics": retrieved_topics,
            "hit_at_1": hit1,
            "hit_at_4": hit4,
        }

        results.append(result)

        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        top1 = (
            retrieved_topics[0]
            if retrieved_topics
            else "None"
        )

        status = "PASS" if hit4 else "MISS"

        print(
            f"{test_id:<10} | "
            f"Expected: {expected_topic:<30} | "
            f"Top-1: {top1:<30} | "
            f"Hit@1: {str(hit1):<5} | "
            f"Hit@4: {str(hit4):<5} | "
            f"{status}"
        )

    # --------------------------------------------------------
    # STEP 4 — Calculate metrics
    # --------------------------------------------------------

    total_questions = len(results)

    hit_at_1_rate = (
        hit_at_1 / total_questions
        if total_questions > 0
        else 0.0
    )

    hit_at_4_rate = (
        hit_at_4 / total_questions
        if total_questions > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Build final evaluation object
    # --------------------------------------------------------

    summary = {
        "project": "KnowFlow-AI",
        "evaluation_type": "Retrieval Evaluation",
        "evaluation_dataset": EVALUATION_SHEET,
        "knowledge_base": str(
            KNOWLEDGE_BASE_PATH
        ),
        "total_questions": total_questions,
        "top_k": TOP_K,
        "metrics": {
            "Hit@1": {
                "correct": hit_at_1,
                "total": total_questions,
                "rate": round(
                    hit_at_1_rate,
                    4,
                ),
            },
            "Hit@4": {
                "correct": hit_at_4,
                "total": total_questions,
                "rate": round(
                    hit_at_4_rate,
                    4,
                ),
            },
        },
        "results": results,
    }

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n" + "=" * 72)
    print("FINAL RETRIEVAL EVALUATION")
    print("=" * 72)

    print(
        f"Total Questions : "
        f"{total_questions}"
    )

    print(
        f"Hit@1           : "
        f"{hit_at_1}/{total_questions} "
        f"({hit_at_1_rate:.2%})"
    )

    print(
        f"Hit@4           : "
        f"{hit_at_4}/{total_questions} "
        f"({hit_at_4_rate:.2%})"
    )

    print(
        f"\nResults saved to:\n"
        f"{RESULTS_PATH}"
    )

    print("=" * 72)

    return summary


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    evaluate_retrieval()