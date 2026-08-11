from pathlib import Path


DATA_FILE = Path(__file__).with_name("raw_questions.txt")


def load_raw_questions():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        content = file.read()

    return content


if __name__ == "__main__":
    questions = load_raw_questions()

    print("Questions loaded successfully!")
    print("--------------------------------")
    print(questions[:1000])