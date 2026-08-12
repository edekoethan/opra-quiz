import argparse
import json
import sys
from pathlib import Path

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "backend" / "data"
AI_TEST_DIR = DATA_DIR / "ai_test"

DEFAULT_INPUT = AI_TEST_DIR / "validated_needs_review.json"
DEFAULT_OUTPUT_DIR = AI_TEST_DIR / "human_review"


# ============================================================
# COMMAND LINE
# ============================================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Interactively review AI-generated OPRA questions."
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default=str(DEFAULT_INPUT),
        help=(
            "Needs-review JSON file. Can be a filename inside "
            "backend/data/ai_test or a full/relative path."
        ),
    )

    return parser.parse_args()


# ============================================================
# RESOLVE INPUT
# ============================================================

def resolve_input_file(input_file):
    path = Path(input_file)

    if path.exists():
        return path.resolve()

    path = AI_TEST_DIR / input_file

    if path.exists():
        return path.resolve()

    raise FileNotFoundError(
        f"Could not find input file:\n{input_file}"
    )


# ============================================================
# NORMALIZE RECORD SHAPE
# ============================================================

def normalize_review_record(record):
    """Support both flattened records and ai_result-nested records."""

    if not isinstance(record, dict):
        return record

    nested = record.get("ai_result")

    if not isinstance(nested, dict):
        return record

    normalized = dict(nested)
    normalized.update(record)

    return normalized


# ============================================================
# LOAD QUESTIONS
# ============================================================

def load_questions(input_file):
    print("Loading questions for human review...")
    print(f"File: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if not isinstance(questions, list):
        raise ValueError(
            "Needs-review file must contain a JSON list."
        )

    questions = [
        normalize_review_record(record)
        for record in questions
    ]

    print(f"Total questions available: {len(questions)}")

    return questions


# ============================================================
# DISPLAY QUESTION
# ============================================================

def display_question(record, index, total):
    print()
    print("=" * 75)
    print(f"QUESTION {index + 1} OF {total}")
    print("=" * 75)

    print(f"Source ID:       {record.get('source_id')}")
    print(f"Category:        {record.get('category')}")
    print(f"Topic:           {record.get('topic')}")
    print(f"Difficulty:      {record.get('difficulty')}")
    print(f"AI confidence:   {record.get('confidence')}")
    print(f"Question type:   {record.get('question_type')}")
    print()

    print("QUESTION:")
    print(record.get("question", ""))
    print()

    print("OPTIONS:")

    options = record.get("options", {})

    for letter in ["A", "B", "C", "D"]:
        print(f"  {letter}. {options.get(letter, '[MISSING]')}")

    print()

    print(f"AI CORRECT ANSWER: {record.get('correct_answer')}")
    print()

    print("EXPLANATIONS:")

    explanations = record.get("explanations", {})

    for letter in ["A", "B", "C", "D"]:
        print(f"\n{letter}. {explanations.get(letter, '[MISSING]')}")

    print()

    print("REVIEW REASON:")
    print(record.get("review_reason") or "None")

    print()

    source_text = record.get("source_text")

    if source_text:
        print("ORIGINAL SOURCE:")
        print(source_text)
        print()


# ============================================================
# SAVE FILES
# ============================================================

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def save_progress(
    approved,
    rejected,
    pending,
    output_dir
):
    save_json(
        output_dir / "human_approved.json",
        approved
    )

    save_json(
        output_dir / "human_rejected.json",
        rejected
    )

    save_json(
        output_dir / "human_pending.json",
        pending
    )


# ============================================================
# HUMAN REVIEW
# ============================================================

def review_question(record):
    while True:

        print()
        print("-" * 75)
        print("ACTION:")
        print("  [A] Approve")
        print("  [R] Reject")
        print("  [E] Edit")
        print("  [S] Skip")
        print("  [Q] Quit and save progress")
        print("-" * 75)

        choice = input("Enter choice: ").strip().lower()

        if choice == "a":
            record["human_status"] = "approved"
            record["human_reviewed"] = True

            note = input(
                "Optional reviewer note (press Enter to skip): "
            ).strip()

            record["human_review_note"] = note

            return "approved"

        if choice == "r":
            record["human_status"] = "rejected"
            record["human_reviewed"] = True

            note = input(
                "Reason for rejection (optional): "
            ).strip()

            record["human_review_note"] = note

            return "rejected"

        if choice == "e":
            edit_record(record)

            print()
            print("Updated question:")
            print(record.get("question"))

            print()
            print("Updated correct answer:")
            print(record.get("correct_answer"))

            confirm = input(
                "Approve this edited question? [Y/N]: "
            ).strip().lower()

            if confirm == "y":
                record["human_status"] = "approved"
                record["human_reviewed"] = True
                record["human_review_note"] = (
                    "Approved after human editing."
                )
                return "approved"

            print("Edit retained. Returning to action menu.")
            continue

        if choice == "s":
            record["human_status"] = "pending"
            record["human_reviewed"] = False
            return "pending"

        if choice == "q":
            return "quit"

        print("Invalid choice. Please enter A, R, E, S, or Q.")


# ============================================================
# EDIT QUESTION
# ============================================================

def edit_record(record):
    print()
    print("=" * 75)
    print("EDIT QUESTION")
    print("=" * 75)

    current_question = record.get("question", "")

    print()
    print("Current question:")
    print(current_question)

    new_question = input(
        "\nNew question (press Enter to keep current): "
    ).strip()

    if new_question:
        record["question"] = new_question

    options = record.setdefault("options", {})

    print()
    print("Edit options. Press Enter to keep the current option.")

    for letter in ["A", "B", "C", "D"]:
        current = options.get(letter, "")

        print(f"\nCurrent {letter}: {current}")

        new_option = input(
            f"New {letter}: "
        ).strip()

        if new_option:
            options[letter] = new_option

    current_answer = record.get("correct_answer", "")

    print()
    print(f"Current correct answer: {current_answer}")

    while True:
        new_answer = input(
            "New correct answer [A/B/C/D] "
            "(press Enter to keep current): "
        ).strip().upper()

        if not new_answer:
            break

        if new_answer in {"A", "B", "C", "D"}:
            record["correct_answer"] = new_answer
            break

        print("Please enter A, B, C, or D.")

    print()
    print("Edit complete.")


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_arguments()

    try:
        input_file = resolve_input_file(
            args.input_file
        )

        questions = load_questions(
            input_file
        )

    except Exception as e:
        print()
        print("ERROR:")
        print(str(e))
        sys.exit(1)

    output_dir = AI_TEST_DIR / "human_review"

    approved = []
    rejected = []
    pending = []

    # --------------------------------------------------------
    # Resume previous progress if available
    # --------------------------------------------------------

    approved_file = output_dir / "human_approved.json"
    rejected_file = output_dir / "human_rejected.json"

    if approved_file.exists():
        try:
            with open(
                approved_file,
                "r",
                encoding="utf-8"
            ) as f:
                approved = json.load(f)

            if not isinstance(approved, list):
                approved = []

        except Exception:
            approved = []

    if rejected_file.exists():
        try:
            with open(
                rejected_file,
                "r",
                encoding="utf-8"
            ) as f:
                rejected = json.load(f)

            if not isinstance(rejected, list):
                rejected = []

        except Exception:
            rejected = []

    approved_ids = {
        record.get("source_id")
        for record in approved
    }

    rejected_ids = {
        record.get("source_id")
        for record in rejected
    }

    # --------------------------------------------------------
    # Review questions
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("OPRA QUESTION HUMAN REVIEW")
    print("=" * 75)

    print()
    print("Controls:")
    print("  A = Approve")
    print("  R = Reject")
    print("  E = Edit")
    print("  S = Skip")
    print("  Q = Quit and save")
    print()

    for index, record in enumerate(questions):

        source_id = record.get("source_id")

        if source_id in approved_ids:
            continue

        if source_id in rejected_ids:
            continue

        display_question(
            record,
            index,
            len(questions)
        )

        result = review_question(record)

        if result == "approved":
            approved.append(record)

        elif result == "rejected":
            rejected.append(record)

        elif result == "pending":
            pending.append(record)

        elif result == "quit":

            remaining = []

            for remaining_record in questions[index:]:
                remaining_id = remaining_record.get("source_id")

                if (
                    remaining_id not in approved_ids
                    and remaining_id not in rejected_ids
                ):
                    remaining.append(remaining_record)

            pending.extend(remaining)

            save_progress(
                approved,
                rejected,
                pending,
                output_dir
            )

            print()
            print("Review stopped.")
            print("Progress saved.")
            print()
            print(f"Approved: {len(approved)}")
            print(f"Rejected: {len(rejected)}")
            print(f"Pending:  {len(pending)}")

            return

        # Save after every question
        save_progress(
            approved,
            rejected,
            pending,
            output_dir
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("HUMAN REVIEW COMPLETE")
    print("=" * 75)

    print()
    print(f"Approved: {len(approved)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Pending:  {len(pending)}")

    print()
    print("Files saved to:")
    print(output_dir)

    print()
    print("Approved:")
    print(approved_file)

    print()
    print("Rejected:")
    print(rejected_file)

    print()
    print("Pending:")
    print(output_dir / "human_pending.json")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()