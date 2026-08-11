import json
import time

from question_loader import load_raw_questions
from question_parser import parse_questions
from ai_processor import generate_question


# ============================================================
# SETTINGS
# ============================================================

APPROVED_FILE = "approved_questions.json"
REVIEW_FILE = "needs_review_questions.json"

# Small delay between API requests.
# We can adjust this later depending on rate limits.
REQUEST_DELAY = 0.5


# ============================================================
# SAVE JSON
# ============================================================

def save_json(filename, data):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# PROCESS QUESTIONS
# ============================================================

def process_questions():

    # --------------------------------------------------------
    # Load raw questions
    # --------------------------------------------------------

    raw_text = load_raw_questions()

    questions = parse_questions(raw_text)

    print(
        f"Found {len(questions)} raw questions."
    )

    print("--------------------------------")

    approved_questions = []
    review_questions = []

    # --------------------------------------------------------
    # Process each question
    # --------------------------------------------------------

    for index, question in enumerate(
        questions,
        start=1
    ):

        print(
            f"Processing question {index}/{len(questions)}..."
        )

        try:

            result = generate_question(

                raw_question=question["raw_text"],

                original_options=question["options"],

                options_source=question["options_source"],

                source_answer=question["source_answer"],

                question_type=question["question_type"],

                review_required=question["review_required"]
            )

            # ------------------------------------------------
            # Add original question ID
            # ------------------------------------------------

            result["source_id"] = question["id"]

            # Keep the original source text.
            # This is extremely useful for later auditing.
            result["source_text"] = question["raw_text"]

            # ------------------------------------------------
            # Decide where the question goes
            # ------------------------------------------------

            if result.get("review_required") is True:

                review_questions.append(result)

                print(
                    "  ⚠ Needs human review"
                )

            elif result.get("status") == "approved":

                approved_questions.append(result)

                print(
                    "  ✓ Approved"
                )

            else:

                # Anything unexpected goes into review.
                result["status"] = "needs_review"

                result["review_required"] = True

                result["review_reason"] = (
                    result.get("review_reason")
                    or
                    "Unexpected AI status. Manual review required."
                )

                review_questions.append(result)

                print(
                    "  ⚠ Unexpected status → review"
                )

        except Exception as error:

            print(
                f"  ✗ ERROR: {error}"
            )

            # Don't lose the question if the API fails.
            review_questions.append({

                "source_id": question["id"],

                "source_text": question["raw_text"],

                "status": "needs_review",

                "review_required": True,

                "review_reason": (
                    f"AI processing failed: {str(error)}"
                )
            })

        # ----------------------------------------------------
        # Delay between requests
        # ----------------------------------------------------

        time.sleep(REQUEST_DELAY)

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    save_json(
        APPROVED_FILE,
        approved_questions
    )

    save_json(
        REVIEW_FILE,
        review_questions
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("--------------------------------")

    print(
        f"Finished processing {len(questions)} questions."
    )

    print(
        f"Approved: {len(approved_questions)}"
    )

    print(
        f"Needs review: {len(review_questions)}"
    )

    print("--------------------------------")

    print(
        f"Saved approved questions to: {APPROVED_FILE}"
    )

    print(
        f"Saved review questions to: {REVIEW_FILE}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    process_questions()