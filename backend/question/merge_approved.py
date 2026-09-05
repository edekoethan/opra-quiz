import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "backend" / "data"
AI_TEST_DIR = DATA_DIR / "ai_test"
HUMAN_REVIEW_DIR = AI_TEST_DIR / "human_review"

EXISTING_BANK_FILE = DATA_DIR / "final_approved_questions.json"
AUTO_APPROVED_FILE = AI_TEST_DIR / "validated_approved.json"
HUMAN_APPROVED_FILE = HUMAN_REVIEW_DIR / "human_approved.json"

OUTPUT_FILE = DATA_DIR / "final_approved_questions.json"

def load_json(path):
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_question_data(record):
    """
    Supports both schemas:

    Nested:
    {
        "source_id": 1,
        "source_text": "...",
        "ai_result": {
            "question": "...",
            "options": {...}
        }
    }

    Direct:
    {
        "source_id": 1,
        "source_text": "...",
        "question": "...",
        "options": {...}
    }
    """
    ai_result = record.get("ai_result")

    if isinstance(ai_result, dict):
        return ai_result

    return record

def normalize(text):
    if not isinstance(text, str):
        return ""

    return " ".join(text.lower().split())

def record_key(record):
    """
    Use the actual generated question as the primary identity.

    source_id is NOT globally unique in prepared_questions.json.
    """
    data = get_question_data(record)

    question = normalize(data.get("question"))

    if question:
        return ("question", question)

    # Fallback for unusual records without a generated question
    source_id = record.get("source_id")
    source_text = normalize(record.get("source_text"))

    return ("source", source_id, source_text)

def main():
    print("Loading approved question sets...")

    existing_bank = load_json(EXISTING_BANK_FILE)
    auto_approved = load_json(AUTO_APPROVED_FILE)
    human_approved = load_json(HUMAN_APPROVED_FILE)

    print(f"Existing final bank:     {len(existing_bank)}")
    print(f"Current auto-approved:   {len(auto_approved)}")
    print(f"Cumulative human-approved: {len(human_approved)}")

    merged = {}
    duplicates = 0

    # Existing bank first.
    # Later records replace earlier copies of the same question,
    # allowing newer human-reviewed versions to take precedence.
    for record in existing_bank + auto_approved + human_approved:
        key = record_key(record)

        if key in merged:
            duplicates += 1

        merged[key] = record

    final_questions = list(merged.values())

    def sort_key(record):
        source_id = record.get("source_id")

        if isinstance(source_id, int):
            return (0, source_id)

        return (1, str(source_id or ""))

    final_questions.sort(key=sort_key)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            final_questions,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 65)
    print("APPROVED QUESTION BANK MERGE COMPLETE")
    print("=" * 65)

    print(f"Existing bank:       {len(existing_bank)}")
    print(f"Auto-approved input: {len(auto_approved)}")
    print(f"Human-approved input:{len(human_approved)}")
    print(f"Duplicate copies skipped/replaced: {duplicates}")
    print(f"Final unique questions: {len(final_questions)}")

    print()
    print("Saved to:")
    print(OUTPUT_FILE)

if __name__ == "__main__":
    main()