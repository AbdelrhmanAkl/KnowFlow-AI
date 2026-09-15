import sys
import json
import time
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
from src.pipeline import generate_answer


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
    PROJECT_ROOT / "evaluation" / "generation_results.json"
)

TOP_K = 4

# Gemini request pacing
REQUESTS_PER_MINUTE = 5
REQUEST_INTERVAL_SECONDS = 13

# Maximum retries for temporary rate-limit errors.
# Daily quota errors are NOT retried.
MAX_RETRIES = 5


# ============================================================
# RATE LIMITER
# ============================================================

class RateLimiter:
    """
    Simple request limiter to avoid exceeding the Gemini
    requests-per-minute limit.
    """

    def __init__(
        self,
        interval_seconds: float = REQUEST_INTERVAL_SECONDS,
    ):
        self.interval_seconds = interval_seconds
        self.last_request_time = None

    def wait(self) -> None:
        if self.last_request_time is None:
            return

        elapsed = time.monotonic() - self.last_request_time
        remaining = self.interval_seconds - elapsed

        if remaining > 0:
            print(
                f"\nRate-limit protection: "
                f"waiting {remaining:.1f}s..."
            )
            time.sleep(remaining)

    def mark_request(self) -> None:
        self.last_request_time = time.monotonic()


# ============================================================
# ERROR CLASSIFICATION
# ============================================================

def is_daily_quota_error(exc: Exception) -> bool:
    """
    Detect Gemini daily free-tier quota exhaustion.

    These errors should NOT be retried because waiting a few
    seconds will not restore the daily quota.
    """

    error_text = str(exc).lower()

    daily_quota_indicators = [
        "generaterequestsperday",
        "generate_content_free_tier_requests",
        "generaterequestsperdaypermodelfreetier",
        "quota exceeded for metric",
        "per-day",
        "per day",
    ]

    return any(
        indicator in error_text
        for indicator in daily_quota_indicators
    )


def is_rate_limit_error(exc: Exception) -> bool:
    """
    Detect temporary Gemini rate-limit errors.

    This function is used only after daily quota errors
    have been excluded.
    """

    error_text = str(exc).upper()

    rate_limit_indicators = [
        "429",
        "RESOURCE_EXHAUSTED",
        "RATE LIMIT",
        "TOO MANY REQUESTS",
    ]

    return any(
        indicator in error_text
        for indicator in rate_limit_indicators
    )


# ============================================================
# SAFE GENERATION
# ============================================================

def generate_with_retry(
    knowledge_base,
    question: str,
    rate_limiter: RateLimiter,
) -> dict:
    """
    Generate an answer while respecting Gemini rate limits.

    Behavior:

    1. Successful request
       -> return success.

    2. Daily free-tier quota exhausted
       -> stop immediately.
       -> DO NOT retry.

    3. Temporary rate-limit error
       -> retry up to MAX_RETRIES.

    4. Other API/application error
       -> return failure immediately.

    Returns:
        {
            "success": bool,
            "result": dict | None,
            "error": str | None,
            "quota_exhausted": bool
        }
    """

    for attempt in range(1, MAX_RETRIES + 1):

        rate_limiter.wait()
        rate_limiter.mark_request()

        try:

            result = generate_answer(
                vector_store=knowledge_base,
                query=question,
                top_k=TOP_K,
                memory=None,
            )

            return {
                "success": True,
                "result": result,
                "error": None,
                "quota_exhausted": False,
            }

        except Exception as exc:

            error_message = str(exc)

            # =================================================
            # DAILY QUOTA
            # =================================================

            if is_daily_quota_error(exc):

                print(
                    "\n" + "=" * 72
                )
                print(
                    "GEMINI DAILY FREE-TIER QUOTA EXHAUSTED"
                )
                print(
                    "=" * 72
                )
                print(
                    "The remaining generation evaluations "
                    "cannot be completed with the current "
                    "Gemini quota."
                )
                print(
                    "Stopping immediately without retrying."
                )
                print(
                    "=" * 72
                )

                return {
                    "success": False,
                    "result": None,
                    "error": error_message,
                    "quota_exhausted": True,
                }

            # =================================================
            # TEMPORARY RATE LIMIT
            # =================================================

            if is_rate_limit_error(exc):

                print(
                    f"\nGemini temporary rate limit detected "
                    f"(attempt {attempt}/{MAX_RETRIES})."
                )

                if attempt >= MAX_RETRIES:

                    return {
                        "success": False,
                        "result": None,
                        "error": error_message,
                        "quota_exhausted": False,
                    }

                retry_wait = 35

                print(
                    f"Waiting {retry_wait}s before retry..."
                )

                time.sleep(retry_wait)

                continue

            # =================================================
            # OTHER ERROR
            # =================================================

            return {
                "success": False,
                "result": None,
                "error": error_message,
                "quota_exhausted": False,
            }

    return {
        "success": False,
        "result": None,
        "error": "Maximum retries exceeded.",
        "quota_exhausted": False,
    }


# ============================================================
# ANSWER EVALUATION
# ============================================================

def evaluate_answer(
    answer: str,
    expected_topic: str,
) -> dict:
    """
    Lightweight deterministic evaluation.

    This checks:

    1. Whether an answer was actually generated.
    2. Whether the exact expected topic appears.

    This is NOT a semantic correctness metric.
    """

    answer_normalized = answer.casefold().strip()
    topic_normalized = expected_topic.casefold().strip()

    answer_present = bool(answer_normalized)

    topic_mentioned = (
        topic_normalized in answer_normalized
        if answer_present
        else False
    )

    return {
        "answer_present": answer_present,
        "expected_topic_mentioned": topic_mentioned,
    }


# ============================================================
# GENERATION EVALUATION
# ============================================================

def evaluate_generation() -> dict:

    print("=" * 72)
    print("KnowFlow-AI | Generation Evaluation")
    print("=" * 72)

    print(
        "\nRate-limit configuration:"
        f"\n- Maximum requests/minute: {REQUESTS_PER_MINUTE}"
        f"\n- Request interval: {REQUEST_INTERVAL_SECONDS}s"
        f"\n- Maximum retries: {MAX_RETRIES}"
        "\n- Daily quota errors: STOP IMMEDIATELY"
    )

    # --------------------------------------------------------
    # STEP 1 — Load evaluation dataset
    # --------------------------------------------------------

    print("\n[1/5] Loading evaluation dataset...")

    evaluation_df = pd.read_excel(
        EVALUATION_URL,
        sheet_name=EVALUATION_SHEET,
    )

    required_columns = {
        "Test ID",
        "Question",
        "Expected Topic",
        "Expected Source Type",
        "Difficulty",
    }

    missing_columns = (
        required_columns
        - set(evaluation_df.columns)
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

    print("\n[2/5] Loading FAISS knowledge base...")

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
    # STEP 3 — Generate answers
    # --------------------------------------------------------

    print("\n[3/5] Generating answers...")
    print("-" * 72)

    results = []

    answers_generated = 0
    answers_with_topic = 0
    generation_failures = 0

    quota_exhausted = False
    stopped_reason = None

    rate_limiter = RateLimiter()

    total_questions = len(evaluation_df)

    for index, row in evaluation_df.iterrows():

        test_id = str(
            row["Test ID"]
        ).strip()

        question = str(
            row["Question"]
        ).strip()

        expected_topic = str(
            row["Expected Topic"]
        ).strip()

        expected_source_type = str(
            row["Expected Source Type"]
        ).strip()

        difficulty = str(
            row["Difficulty"]
        ).strip()

        print(
            f"\n[{index + 1}/{total_questions}] "
            f"{test_id} | {question}"
        )

        # ----------------------------------------------------
        # Generate answer safely
        # ----------------------------------------------------

        generation = generate_with_retry(
            knowledge_base=knowledge_base,
            question=question,
            rate_limiter=rate_limiter,
        )

        # ----------------------------------------------------
        # DAILY QUOTA EXHAUSTED
        # ----------------------------------------------------

        if generation["quota_exhausted"]:

            quota_exhausted = True

            stopped_reason = (
                "Gemini daily free-tier generation "
                "quota exhausted."
            )

            print(
                "\nGeneration evaluation stopped safely."
            )
            print(
                "Previously generated results will be saved."
            )

            break

        # ----------------------------------------------------
        # Generation succeeded
        # ----------------------------------------------------

        if generation["success"]:

            result = generation["result"]

            answer = result["answer"]

            rewritten_query = result["query"]

            retrieved_documents = result[
                "documents"
            ]

            generation_status = "success"

            answers_generated += 1

            answer_metrics = evaluate_answer(
                answer=answer,
                expected_topic=expected_topic,
            )

            if answer_metrics[
                "expected_topic_mentioned"
            ]:
                answers_with_topic += 1

        # ----------------------------------------------------
        # Generation failed
        # ----------------------------------------------------

        else:

            error_message = generation["error"]

            print(
                "\nGeneration failed permanently:"
                f"\n{error_message}"
            )

            answer = ""

            rewritten_query = question

            retrieved_documents = []

            generation_status = "failed"

            generation_failures += 1

            answer_metrics = {
                "answer_present": False,
                "expected_topic_mentioned": False,
            }

        # ----------------------------------------------------
        # Retrieved source information
        # ----------------------------------------------------

        retrieved_sources = []

        for document in retrieved_documents:

            metadata = document.metadata

            retrieved_sources.append(
                {
                    "source": metadata.get(
                        "source",
                        "unknown",
                    ),
                    "page": metadata.get(
                        "page"
                    ),
                    "row": metadata.get(
                        "row"
                    ),
                }
            )

        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        evaluation_result = {
            "test_id": test_id,
            "question": question,
            "expected_topic": expected_topic,
            "expected_source_type": (
                expected_source_type
            ),
            "difficulty": difficulty,
            "generation_status": generation_status,
            "rewritten_query": rewritten_query,
            "answer": answer,
            "answer_present": answer_metrics[
                "answer_present"
            ],
            "expected_topic_mentioned": (
                answer_metrics[
                    "expected_topic_mentioned"
                ]
            ),
            "retrieved_sources": retrieved_sources,
        }

        if not generation["success"]:

            evaluation_result["error"] = (
                generation["error"]
            )

        results.append(
            evaluation_result
        )

        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        if answer:

            print("\nAnswer:")
            print(answer)

            print(
                "\nExpected topic mentioned: "
                f"{answer_metrics['expected_topic_mentioned']}"
            )

        else:

            print(
                "\nAnswer: [Generation failed]"
            )

    # --------------------------------------------------------
    # STEP 4 — Calculate summary metrics
    # --------------------------------------------------------

    successful_results = [
        result
        for result in results
        if result["generation_status"] == "success"
    ]

    successful_count = len(
        successful_results
    )

    evaluated_count = len(results)

    # Generation success rate across the QUESTIONS THAT
    # WERE ACTUALLY ATTEMPTED.
    #
    # This avoids incorrectly treating questions that were
    # never attempted because daily quota was exhausted
    # as generation failures.

    answer_generation_rate = (
        successful_count / evaluated_count
        if evaluated_count
        else 0.0
    )

    # Topic mention rate ONLY among successfully generated
    # answers.

    topic_mention_rate = (
        answers_with_topic / successful_count
        if successful_count
        else 0.0
    )

    # --------------------------------------------------------
    # STEP 5 — Save evaluation results
    # --------------------------------------------------------

    summary = {
        "project": "KnowFlow-AI",

        "evaluation_type": (
            "Generation Evaluation"
        ),

        "evaluation_dataset": (
            EVALUATION_SHEET
        ),

        "knowledge_base": str(
            KNOWLEDGE_BASE_PATH
        ),

        "top_k": TOP_K,

        "rate_limit": {
            "requests_per_minute": (
                REQUESTS_PER_MINUTE
            ),
            "request_interval_seconds": (
                REQUEST_INTERVAL_SECONDS
            ),
            "max_retries": MAX_RETRIES,
            "daily_quota_errors_are_not_retried": True,
        },

        "total_questions": total_questions,

        "evaluated_questions": evaluated_count,

        "successful_generations": (
            successful_count
        ),

        "generation_failures": (
            generation_failures
        ),

        "quota_exhausted": quota_exhausted,

        "stopped_reason": stopped_reason,

        "remaining_questions_not_evaluated": (
            total_questions - evaluated_count
        ),

        "metrics": {

            "answer_generation_rate_on_evaluated_questions": round(
                answer_generation_rate,
                4,
            ),

            "expected_topic_mention_rate_on_successful_answers": round(
                topic_mention_rate,
                4,
            ),
        },

        "evaluation_note": (
            "Expected topic mention is a lightweight "
            "deterministic signal and must not be interpreted "
            "as semantic correctness, factual accuracy, "
            "faithfulness, or overall answer quality. "
            "Questions skipped because of daily API quota "
            "exhaustion are not counted as generation failures."
        ),

        "results": results,
    }

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
    print("FINAL GENERATION EVALUATION")
    print("=" * 72)

    print(
        f"Total Questions              : "
        f"{total_questions}"
    )

    print(
        f"Questions Evaluated          : "
        f"{evaluated_count}/{total_questions}"
    )

    print(
        f"Successful Generations       : "
        f"{successful_count}/{evaluated_count} "
        f"({answer_generation_rate:.2%})"
        if evaluated_count
        else
        "Successful Generations       : N/A"
    )

    print(
        f"Generation Failures          : "
        f"{generation_failures}/{evaluated_count}"
        if evaluated_count
        else
        "Generation Failures          : N/A"
    )

    print(
        f"Questions Not Evaluated     : "
        f"{total_questions - evaluated_count}"
    )

    print(
        f"Topic Mention Rate "
        f"(successful answers only)    : "
        f"{answers_with_topic}/{successful_count} "
        f"({topic_mention_rate:.2%})"
        if successful_count
        else
        "Topic Mention Rate "
        "(successful answers only)    : N/A"
    )

    print(
        f"Daily Quota Exhausted        : "
        f"{quota_exhausted}"
    )

    if stopped_reason:

        print(
            f"Stopped Reason               : "
            f"{stopped_reason}"
        )

    print(
        "\nIMPORTANT:"
        "\n- Topic Mention Rate is NOT an accuracy metric."
        "\n- It is only a lightweight deterministic signal."
        "\n- Daily quota exhaustion is NOT a project failure."
        "\n- Unevaluated questions are NOT counted as generation failures."
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
    evaluate_generation()