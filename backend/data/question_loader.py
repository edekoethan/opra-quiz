from pathlib import Path


def load_raw_questions():
    """
    Load the original messy question bank without modifying it.

    The raw source is intentionally preserved exactly as supplied.
    """

    project_root = Path(__file__).resolve().parent.parent

    raw_file = project_root / "raw_questions.txt"

    if not raw_file.exists():
        raise FileNotFoundError(
            f"Could not find raw question bank: {raw_file}"
        )

    return raw_file.read_text(
        encoding="utf-8"
    )


if __name__ == "__main__":

    questions = load_raw_questions()

    print("Question bank loaded successfully!")
    print("--------------------------------")
    print(f"Characters: {len(questions):,}")
    print(f"Lines: {len(questions.splitlines()):,}")
    print("--------------------------------")
    print(questions[:1000])