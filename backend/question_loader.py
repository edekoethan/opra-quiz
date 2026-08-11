from data.question_loader import load_raw_questions


if __name__ == "__main__":
    questions = load_raw_questions()

    print("Questions loaded successfully!")
    print("--------------------------------")
    print(questions[:1000])