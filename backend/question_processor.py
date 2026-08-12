import sys
import json
from pathlib import Path
from collections import Counter

# Allow imports when running from project root
sys.path.insert(0, "backend")

from question_loader import load_raw_questions
from question_parser import parse_questions


# ============================================================
# SOURCE CLASSIFICATION
# ============================================================

def classify_source_record(question):
    """
    Classify a parsed source record before AI processing.

    This classification describes the SOURCE FORMAT,
    not whether the medical content is correct.
    """

    text = question.get("raw_text", "").strip()
    qtype = question.get("question_type", "")

    if not text:
        return "empty"

    # --------------------------------------------------------
    # IMPORTANT:
    # Pharmaceutical calculation should only be used when
    # there is an actual numerical calculation/problem.
    # --------------------------------------------------------

    calculation_keywords = [
        "calculate",
        "calculation",
        "how many",
        "how much",
        "dose required",
        "dose to administer",
        "infusion rate",
        "rate of infusion",
        "dilution",
        "dilute",
        "concentration",
        "alligation",
        "percentage strength",
        "mg/ml",
        "mg/mL",
        "mcg/ml",
        "mcg/mL",
        "g/ml",
        "g/mL",
        "ml/hr",
        "mL/hr",
        "mg/kg",
        "mcg/kg",
        "mg/kg/day",
        "creatinine clearance",
        "cockcroft-gault",
    ]

    text_lower = text.lower()

    has_number = any(char.isdigit() for char in text)

    has_calculation_keyword = any(
        keyword.lower() in text_lower
        for keyword in calculation_keywords
    )

    # A real calculation should normally contain either
    # numerical information or an explicit calculation cue.
    if (
        qtype == "pharmaceutical_calculation"
        and (has_number or has_calculation_keyword)
    ):
        return "calculation"

    # --------------------------------------------------------
    # Standard parser classifications
    # --------------------------------------------------------

    if qtype == "mcq":
        return "mcq"

    if qtype == "yes_no":
        return "yes_no"

    if qtype == "incomplete":
        return "incomplete"

    # --------------------------------------------------------
    # Numbered fragments
    # --------------------------------------------------------

    if question.get("options_source") == "numbered_source":
        return "fragment"

    # --------------------------------------------------------
    # Very long records
    # --------------------------------------------------------

    if len(text) > 1200:
        return "possible_multiple_questions"

    return "unknown"

# ============================================================
# BUILD PROCESSING RECORD
# ============================================================

def prepare_record(question):
    """
    Convert parser output into a clean intermediate record.

    Nothing is deleted.
    Nothing is medically corrected.
    """

    classification = classify_source_record(question)

    return {
        "source_id": question["id"],
        "classification": classification,

        # Original source is preserved
        "source_text": question["raw_text"],

        # Existing information extracted by parser
        "original_options": question.get("options"),
        "numbered_options": question.get("numbered_options"),
        "source_answer": question.get("source_answer"),
        "yes_no_answer": question.get("yes_no_answer"),

        # Processing status
        "status": "pending",

        # These will be populated later by AI/human review
        "clean_question": None,
        "clean_options": None,
        "correct_answer": None,
        "explanation": None,
        "confidence": None,
        "review_reason": None,
    }


# ============================================================
# BUILD ALL PROCESSING RECORDS
# ============================================================

def prepare_question_bank(raw_text):
    """
    Parse the raw bank and prepare intermediate records.
    """

    parsed_questions = parse_questions(raw_text)

    records = []

    for question in parsed_questions:
        records.append(
            prepare_record(question)
        )

    return records


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(records):

    classifications = Counter(
        record["classification"]
        for record in records
    )

    print()
    print("=" * 70)
    print("QUESTION PROCESSING PIPELINE")
    print("=" * 70)

    print(f"Total source records: {len(records)}")

    print()
    print("CLASSIFICATION")
    print("-" * 70)

    for classification, count in classifications.most_common():
        print(repr(classification), count)

    print("=" * 70)


# ============================================================
# DISPLAY SAMPLE
# ============================================================

def display_sample(records, limit=5):

    print()
    print("=" * 70)
    print(f"FIRST {limit} PROCESSING RECORDS")
    print("=" * 70)

    for record in records[:limit]:

        print()
        print(f"Source ID: {record['source_id']}")
        print(f"Classification: {record['classification']}")
        print(f"Status: {record['status']}")

        source = (
            record["source_text"]
            .replace("\n", " ")
            .strip()
        )

        preview_length = 200

        if len(source) > preview_length:
            source = source[:preview_length] + "..."

        print(f"Source preview: {source}")

        print("-" * 70)


# ============================================================
# SAVE PREPARED RECORDS
# ============================================================

def save_prepared_records(records):

    output_path = Path(
        "backend/data/prepared_questions.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("SAVE COMPLETE")
    print("=" * 70)
    print(f"Prepared records saved: {output_path}")
    print(f"Total records saved: {len(records)}")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("Loading raw question bank...")

    raw_text = load_raw_questions()

    print("Parsing source records...")

    records = prepare_question_bank(
        raw_text
    )

    print_statistics(records)

    display_sample(
        records,
        limit=5
    )

    save_prepared_records(
        records
    )