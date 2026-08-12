import sys

sys.path.insert(0, "backend")

from question_loader import load_raw_questions
from question_parser import parse_questions


questions = parse_questions(
    load_raw_questions()
)

print("=" * 70)
print("UNKNOWN RECORDS")
print("=" * 70)

count = 0

for question in questions:

    if question["question_type"] == "unknown":

        print()
        print(f"ID: {question['id']}")
        print(f"Options source: {question['options_source']}")
        print(f"Source answer: {question['source_answer']}")
        print("Raw source:")
        print(question["raw_text"])
        print("-" * 70)

        count += 1

        if count >= 30:
            break


print()
print("=" * 70)
print("NUMBERED SOURCE OPTIONS")
print("=" * 70)

count = 0

for question in questions:

    if question["options_source"] == "numbered_source":

        print()
        print(f"ID: {question['id']}")
        print("Raw source:")
        print(question["raw_text"])
        print()
        print("Numbered options:")
        print(question["numbered_options"])
        print("-" * 70)

        count += 1

        if count >= 20:
            break