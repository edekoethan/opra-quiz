import argparse
import json
import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "backend" / "data"
AI_TEST_DIR = DATA_DIR / "ai_test"


# ============================================================
# VALIDATION SETTINGS
# ============================================================

REQUIRED_FIELDS = [
    "status",
    "question",
    "options",
    "correct_answer",
    "explanations",
    "confidence",
    "category",
    "topic",
    "difficulty",
]

VALID_STATUSES = {
    "approved",
    "needs_review",
    "rejected",
}

VALID_ANSWERS = {
    "A",
    "B",
    "C",
    "D",
}

MIN_APPROVAL_CONFIDENCE = 0.90


# ============================================================
# COMMAND LINE
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Validate AI-generated OPRA questions."
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default="ai_batch_11_60.json",
        help=(
            "AI results JSON file. "
            "Can be a filename inside backend/data/ai_test "
            "or a full/relative path."
        ),
    )

    return parser.parse_args()


# ============================================================
# RESOLVE INPUT FILE
# ============================================================

def resolve_input_file(input_file):

    path = Path(input_file)

    # Full or relative path that already exists
    if path.exists():
        return path.resolve()

    # Otherwise look inside backend/data/ai_test
    path = AI_TEST_DIR / input_file

    if path.exists():
        return path.resolve()

    raise FileNotFoundError(
        f"Could not find input file:\n{input_file}"
    )


# ============================================================
# LOAD AI RESULTS
# ============================================================

def load_results(input_file):

    print("Loading AI results...")
    print(f"File: {input_file}")

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as f:

        results = json.load(f)

    if not isinstance(results, list):

        raise ValueError(
            "AI results file must contain a JSON list."
        )

    print(
        f"Total records available: {len(results)}"
    )

    return results


# ============================================================
# VALIDATE ONE RECORD
# ============================================================

def validate_record(record):

    flags = []

    # --------------------------------------------------------
    # Basic record validation
    # --------------------------------------------------------

    if not isinstance(record, dict):

        return {
            "valid": False,
            "flags": [
                "Record is not a JSON object."
            ],
        }

    # --------------------------------------------------------
    # Get AI result
    # --------------------------------------------------------

    ai_result = record.get("ai_result")

    if not isinstance(ai_result, dict):

        return {
            "valid": False,
            "flags": [
                "Missing or invalid ai_result object."
            ],
        }

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    for field in REQUIRED_FIELDS:

        if field not in ai_result:

            flags.append(
                f"Missing required field: {field}"
            )

    # --------------------------------------------------------
    # If required fields are missing, stop deeper checks
    # --------------------------------------------------------

    if flags:

        return {
            "valid": False,
            "flags": flags,
        }

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    status = ai_result.get("status")

    if status not in VALID_STATUSES:

        flags.append(
            f"Invalid status: {status}"
        )

    # --------------------------------------------------------
    # Question
    # --------------------------------------------------------

    question = ai_result.get("question")

    if not isinstance(question, str) or not question.strip():

        flags.append(
            "Question is empty."
        )

    # --------------------------------------------------------
    # Options
    # --------------------------------------------------------

    options = ai_result.get("options")

    if not isinstance(options, dict):

        flags.append(
            "Options must be an object."
        )

    else:

        for letter in VALID_ANSWERS:

            if letter not in options:

                flags.append(
                    f"Missing option: {letter}"
                )

            elif not str(
                options[letter]
            ).strip():

                flags.append(
                    f"Empty option: {letter}"
                )

    # --------------------------------------------------------
    # Correct answer
    # --------------------------------------------------------

    correct_answer = ai_result.get(
        "correct_answer"
    )

    if correct_answer not in VALID_ANSWERS:

        flags.append(
            "Correct answer must be A, B, C, or D."
        )

    # --------------------------------------------------------
    # Explanations
    # --------------------------------------------------------

    explanations = ai_result.get(
        "explanations"
    )

    if not isinstance(explanations, dict):

        flags.append(
            "Explanations must be an object."
        )

    else:

        for letter in VALID_ANSWERS:

            if letter not in explanations:

                flags.append(
                    f"Missing explanation: {letter}"
                )

            elif not str(
                explanations[letter]
            ).strip():

                flags.append(
                    f"Empty explanation: {letter}"
                )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = ai_result.get(
        "confidence"
    )

    if not isinstance(
        confidence,
        (int, float)
    ):

        flags.append(
            "Confidence must be numeric."
        )

    else:

        if confidence < 0 or confidence > 1:

            flags.append(
                "Confidence must be between 0 and 1."
            )

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    category = ai_result.get("category")

    if not isinstance(
        category,
        str
    ) or not category.strip():

        flags.append(
            "Category is empty."
        )

    # --------------------------------------------------------
    # Topic
    # --------------------------------------------------------

    topic = ai_result.get("topic")

    if not isinstance(
        topic,
        str
    ) or not topic.strip():

        flags.append(
            "Topic is empty."
        )

    # --------------------------------------------------------
    # Difficulty
    # --------------------------------------------------------

    difficulty = ai_result.get(
        "difficulty"
    )

    if not isinstance(
        difficulty,
        str
    ) or not difficulty.strip():

        flags.append(
            "Difficulty is empty."
        )

    # --------------------------------------------------------
    # Final structural validity
    # --------------------------------------------------------

    return {
        "valid": len(flags) == 0,
        "flags": flags,
    }


# ============================================================
# CLASSIFY RECORD
# ============================================================

def classify_record(record, validation):

    ai_result = record.get(
        "ai_result",
        {}
    )

    status = ai_result.get(
        "status"
    )

    confidence = ai_result.get(
        "confidence"
    )

    flags = validation["flags"]

    # --------------------------------------------------------
    # Invalid structural record
    # --------------------------------------------------------

    if not validation["valid"]:

        return "rejected"

    # --------------------------------------------------------
    # Explicit AI rejection
    # --------------------------------------------------------

    if status == "rejected":

        return "rejected"

    # --------------------------------------------------------
    # AI requested review
    # --------------------------------------------------------

    if status == "needs_review":

        return "needs_review"

    # --------------------------------------------------------
    # Low confidence
    # --------------------------------------------------------

    if isinstance(
        confidence,
        (int, float)
    ) and confidence < MIN_APPROVAL_CONFIDENCE:

        return "needs_review"

    # --------------------------------------------------------
    # Approved
    # --------------------------------------------------------

    if status == "approved":

        return "approved"

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    return "needs_review"


# ============================================================
# DISPLAY ONE RESULT
# ============================================================

def display_result(
    record,
    validation,
    final_status
):

    ai_result = record.get(
        "ai_result",
        {}
    )

    print()
    print("---")

    print(
        f"Source ID: "
        f"{record.get('source_id')}"
    )

    print(
        f"Classification: "
        f"{record.get('source_classification')}"
    )

    print(
        f"Status: "
        f"{final_status}"
    )

    print(
        f"AI Status: "
        f"{ai_result.get('status')}"
    )

    print(
        f"Confidence: "
        f"{ai_result.get('confidence')}"
    )

    print()
    print("Question:")

    print(
        ai_result.get(
            "question"
        )
    )

    print()
    print("Correct answer:")

    print(
        ai_result.get(
            "correct_answer"
        )
    )

    print()
    print("Review reason:")

    review_reason = ai_result.get(
        "review_reason"
    )

    if review_reason:

        print(review_reason)

    else:

        print("None")

    print()
    print("Validation flags:")

    if validation["flags"]:

        for flag in validation["flags"]:

            print(
                f"- {flag}"
            )

    else:

        print("- None")


# ============================================================
# MAIN VALIDATION
# ============================================================

def main():

    args = parse_arguments()

    try:

        input_file = resolve_input_file(
            args.input_file
        )

        results = load_results(
            input_file
        )

    except Exception as e:

        print()
        print("ERROR:")
        print(str(e))

        sys.exit(1)

    print()
    print(
        "Validating questions..."
    )

    approved = []
    needs_review = []
    rejected = []
    invalid_records = []

    # --------------------------------------------------------
    # Process records
    # --------------------------------------------------------

    for record in results:

        validation = validate_record(
            record
        )

        if not isinstance(
            record,
            dict
        ):

            invalid_records.append(
                record
            )

            continue

        final_status = classify_record(
            record,
            validation
        )

        if final_status == "approved":

            approved.append(
                record
            )

        elif final_status == "needs_review":

            needs_review.append(
                record
            )

        elif final_status == "rejected":

            rejected.append(
                record
            )

        display_result(
            record,
            validation,
            final_status
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    print()
    print(
        f"Total processed:       {len(results)}"
    )

    print(
        f"Valid approved:        {len(approved)}"
    )

    print(
        f"Needs review:          {len(needs_review)}"
    )

    print(
        f"Rejected:              {len(rejected)}"
    )

    print(
        f"Invalid records:       {len(invalid_records)}"
    )

    print()

    # --------------------------------------------------------
    # Save categorized results
    # --------------------------------------------------------

    approved_file = (
        AI_TEST_DIR
        / "validated_approved.json"
    )

    review_file = (
        AI_TEST_DIR
        / "validated_needs_review.json"
    )

    rejected_file = (
        AI_TEST_DIR
        / "validated_rejected.json"
    )

    with open(
        approved_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            approved,
            f,
            indent=4,
            ensure_ascii=False
        )

    with open(
        review_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            needs_review,
            f,
            indent=4,
            ensure_ascii=False
        )

    with open(
        rejected_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            rejected,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        "Categorized files saved:"
    )

    print(
        f"Approved:      {approved_file}"
    )

    print(
        f"Needs review:  {review_file}"
    )

    print(
        f"Rejected:      {rejected_file}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()