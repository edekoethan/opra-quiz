from question_loader import load_raw_questions
from question_parser import parse_questions
from collections import Counter


def main():

    print("Loading question bank...")
    print("--------------------------------")

    raw_text = load_raw_questions()
    questions = parse_questions(raw_text)

    print(f"TOTAL RECORDS: {len(questions)}")
    print()

    # --------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------

    with_options = [
        q for q in questions
        if q.get("options")
    ]

    without_options = [
        q for q in questions
        if not q.get("options")
    ]

    calculations = [
        q for q in questions
        if q.get("question_type")
        == "pharmaceutical_calculation"
    ]

    review_required = [
        q for q in questions
        if q.get("review_required")
    ]

    source_answers = [
        q for q in questions
        if q.get("source_answer")
    ]

    print("QUESTION BANK SUMMARY")
    print("================================")
    print(
        f"With detected A-D options: {len(with_options)}"
    )
    print(
        f"Without detected A-D options: {len(without_options)}"
    )
    print(
        f"Calculations: {len(calculations)}"
    )
    print(
        f"Review required: {len(review_required)}"
    )
    print(
        f"Records with source answer: {len(source_answers)}"
    )

    # --------------------------------------------------
    # QUESTION TYPES
    # --------------------------------------------------

    print()
    print("QUESTION TYPES")
    print("================================")

    type_counts = Counter(
        q.get("question_type", "unknown")
        for q in questions
    )

    for question_type, count in type_counts.items():

        print(
            f"{question_type}: {count}"
        )

    # --------------------------------------------------
    # OPTIONS SOURCE
    # --------------------------------------------------

    print()
    print("OPTIONS SOURCE")
    print("================================")

    option_counts = Counter(
        q.get("options_source", "unknown")
        for q in questions
    )

    for source, count in option_counts.items():

        print(
            f"{source}: {count}"
        )

    # --------------------------------------------------
    # CALCULATION EXAMPLES
    # --------------------------------------------------

    print()
    print("FIRST 20 CALCULATION RECORDS")
    print("================================")

    for q in calculations[:20]:

        print(
            f"ID: {q['id']}"
        )

        print(
            q["raw_text"]
        )

        print("--------------------------------")

    # --------------------------------------------------
    # RECORDS WITHOUT OPTIONS
    # --------------------------------------------------

    print()
    print("FIRST 30 RECORDS WITHOUT DETECTED OPTIONS")
    print("================================")

    for q in without_options[:30]:

        print(
            f"ID: {q['id']}"
        )

        print(
            q["raw_text"]
        )

        print("--------------------------------")

    # --------------------------------------------------
    # SOURCE ANSWERS
    # --------------------------------------------------

    print()
    print("FIRST 30 RECORDS WITH SOURCE ANSWERS")
    print("================================")

    for q in source_answers[:30]:

        print(
            f"ID: {q['id']}"
        )

        print(
            f"Source answer: {q['source_answer']}"
        )

        print(
            q["raw_text"]
        )

        print("--------------------------------")


if __name__ == "__main__":
    main()