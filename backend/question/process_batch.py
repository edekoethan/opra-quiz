import json
import sys
import time
from pathlib import Path

# ============================================================
# ALLOW IMPORTS FROM BACKEND
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from ai_processor import generate_question


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "prepared_questions.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "ai_test"
    / "ai_batch_11_60.json"
)


# ============================================================
# BATCH SETTINGS
# ============================================================

START_INDEX = 10       # Question 11
BATCH_SIZE = 50        # Questions 11–60


# ============================================================
# LOAD QUESTIONS
# ============================================================

def load_questions():

    print("Loading prepared questions...")
    print(f"File: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Total records available: {len(questions)}")

    return questions


# ============================================================
# PROCESS ONE QUESTION
# ============================================================

def process_one(record):

    print()
    print("=" * 70)
    print(f"PROCESSING SOURCE ID: {record.get('source_id')}")
    print("=" * 70)

    print("Classification:", record.get("classification"))
    print()
    print("Source:")
    print(record.get("source_text", ""))
    print()

    try:

        result = generate_question(
            raw_question=record.get("source_text", ""),

            original_options=record.get(
                "original_options"
            ),

            options_source=(
                "original"
                if record.get("original_options")
                else "ai_generated"
            ),

            source_answer=record.get(
                "source_answer"
            ),

            question_type=record.get(
                "classification",
                "unknown"
            ),

            review_required=False
        )

        print("AI PROCESSING SUCCESS")

        print()
        print("Status:", result.get("status"))
        print(
            "Review required:",
            result.get("review_required")
        )
        print(
            "Confidence:",
            result.get("confidence")
        )
        print(
            "Category:",
            result.get("category")
        )
        print(
            "Topic:",
            result.get("topic")
        )
        print(
            "Difficulty:",
            result.get("difficulty")
        )

        print()
        print("GENERATED QUESTION:")
        print(result.get("question"))

        print()
        print("CORRECT ANSWER:")
        print(result.get("correct_answer"))

        print()
        print("REVIEW REASON:")
        print(result.get("review_reason"))

        return {
            "source_id": record.get("source_id"),
            "source_classification": record.get(
                "classification"
            ),
            "source_text": record.get(
                "source_text"
            ),
            "ai_result": result
        }

    except Exception as e:

        print()
        print("ERROR PROCESSING QUESTION")
        print(type(e).__name__)
        print(str(e))

        return {
            "source_id": record.get("source_id"),
            "source_classification": record.get(
                "classification"
            ),
            "source_text": record.get(
                "source_text"
            ),
            "error": str(e)
        }


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# MAIN
# ============================================================

def main():

    questions = load_questions()

    end_index = min(
        START_INDEX + BATCH_SIZE,
        len(questions)
    )

    batch = questions[
        START_INDEX:end_index
    ]

    print()
    print("=" * 70)
    print("AI PROCESSING BATCH")
    print("=" * 70)

    print(
        f"Processing source IDs "
        f"{batch[0]['source_id']}–"
        f"{batch[-1]['source_id']}"
    )

    print(
        f"Number of questions: {len(batch)}"
    )

    results = []

    # --------------------------------------------------------
    # PROCESS QUESTIONS
    # --------------------------------------------------------

    for index, record in enumerate(
        batch,
        start=1
    ):

        result = process_one(record)

        results.append(result)

        # ----------------------------------------------------
        # SAVE AFTER EVERY QUESTION
        # ----------------------------------------------------

        save_results(results)

        print()
        print(
            f"Progress: {index}/{len(batch)}"
        )

        # Small pause to avoid hammering the API
        time.sleep(0.5)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    successful = sum(
        1
        for r in results
        if "ai_result" in r
    )

    errors = sum(
        1
        for r in results
        if "error" in r
    )

    print()
    print("=" * 70)
    print("BATCH COMPLETE")
    print("=" * 70)

    print(
        f"Processed: {len(results)}"
    )

    print(
        f"Successful: {successful}"
    )

    print(
        f"Errors: {errors}"
    )

    print()
    print(
        f"Results saved to:\n{OUTPUT_FILE}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
