import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "backend" / "data"
AI_TEST_DIR = DATA_DIR / "ai_test"
HUMAN_REVIEW_DIR = AI_TEST_DIR / "human_review"

AUTO_APPROVED_FILE = AI_TEST_DIR / "validated_approved.json"
HUMAN_APPROVED_FILE = HUMAN_REVIEW_DIR / "human_approved.json"

OUTPUT_FILE = DATA_DIR / "final_approved_questions.json"


def load_json(path):
    if not path.exists():
        print(f"Missing file: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_source_id(record):
    """
    Supports both:
    {
        "source_id": 123,
        "ai_result": {...}
    }

    and direct:
    {
        "source_id": 123,
        ...
    }
    """
    return record.get("source_id")


def main():
    print("Loading approved question sets...")

    auto_approved = load_json(AUTO_APPROVED_FILE)
    human_approved = load_json(HUMAN_APPROVED_FILE)

    print(f"Automatically approved: {len(auto_approved)}")
    print(f"Human approved:       {len(human_approved)}")

    combined = []
    seen_ids = set()

    for record in auto_approved + human_approved:
        source_id = get_source_id(record)

        if source_id is not None and source_id in seen_ids:
            print(f"Skipping duplicate source ID: {source_id}")
            continue

        combined.append(record)

        if source_id is not None:
            seen_ids.add(source_id)

    combined.sort(
        key=lambda record: (
            get_source_id(record) is None,
            get_source_id(record) or 0
        )
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("APPROVED QUESTION BANK MERGE COMPLETE")
    print("=" * 60)
    print(f"Auto approved:   {len(auto_approved)}")
    print(f"Human approved:  {len(human_approved)}")
    print(f"Final questions: {len(combined)}")
    print()
    print(f"Saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()