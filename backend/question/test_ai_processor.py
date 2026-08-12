import json
import sys
from pathlib import Path

# ============================================================
# ALLOW IMPORTS FROM BACKEND
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from question.ai_processor import generate_question


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = PROJECT_ROOT / "backend" / "data" / "prepared_questions.json"

OUTPUT_FILE = PROJECT_ROOT / "backend" / "data" / "ai_test_results.json"


# ============================================================
# LOAD PREPARED QUESTIONS
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
    print(f"PROCESSING SOURCE ID: {record['source_id']}")
    print("=" * 70)

    print("Classification:", record.get("classification"))
    print()
    print("Source:")
    print(record.get("source_text", ""))
    print()

    try:

        result = generate_question(
            raw_question=record.get("source_text", ""),
            original_options=record.get("original_options"),
            options_source=(
                "original"
                if record.get("original_options")
                else "ai_generated"
            ),
            source_answer=record.get("source_answer"),
            question_type=record.get(
                "classification",
                "unknown"
            ),
            review_required=False
        )

        print("AI PROCESSING SUCCESS")

        print()
        print("Status:", result.get("status"))
        print("Review required:", result.get("review_required"))
        print("Confidence:", result.get("confidence"))
        print("Category:", result.get("category"))
        print("Topic:", result.get("topic"))
        print("Difficulty:", result.get("difficulty"))

        print()
        print("GENERATED QUESTION:")
        print(result.get("question"))

        print()
        print("OPTIONS:")

        options = result.get("options") or {}

        for letter in ["A", "B", "C", "D"]:
            print(
                f"{letter}. {options.get(letter)}"
            )

        print()
        print("CORRECT ANSWER:")
        print(result.get("correct_answer"))

        print()
        print("EXPLANATIONS:")

        explanations = result.get("explanations") or {}

        for letter in ["A", "B", "C", "D"]:
            print(
                f"{letter}: {explanations.get(letter)}"
            )

        print()
        print("REVIEW REASON:")
        print(result.get("review_reason"))

        return {
            "source_id": record["source_id"],
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
            "source_id": record["source_id"],
            "source_classification": record.get(
                "classification"
            ),
            "source_text": record.get(
                "source_text"
            ),
            "error": str(e)
        }


# ============================================================
# MAIN
# ============================================================

def main():

    questions = load_questions()

    # --------------------------------------------------------
    # ONLY TEST FIRST 10
    # --------------------------------------------------------

    test_questions = questions[:10]

    print()
    print("=" * 70)
    print("AI PROCESSOR TEST")
    print("=" * 70)

    print(
        f"Testing {len(test_questions)} questions."
    )

    results = []

    for record in test_questions:

        result = process_one(record)

        results.append(result)

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

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

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    print(
        f"Results saved to:\n{OUTPUT_FILE}"
    )

    print()
    print(
        f"Processed: {len(results)} questions"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
