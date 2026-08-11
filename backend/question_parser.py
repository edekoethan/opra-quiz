import re
from question_loader import load_raw_questions


# --------------------------------------------------
# Detect whether a question contains A-D options
# --------------------------------------------------

def extract_options(text):

    options = {}

    patterns = {
        "A": r"(?:^|\n)\s*A[\.\):\-]\s*(.*?)(?=\n\s*B[\.\):\-]|\Z)",
        "B": r"(?:^|\n)\s*B[\.\):\-]\s*(.*?)(?=\n\s*C[\.\):\-]|\Z)",
        "C": r"(?:^|\n)\s*C[\.\):\-]\s*(.*?)(?=\n\s*D[\.\):\-]|\Z)",
        "D": r"(?:^|\n)\s*D[\.\):\-]\s*(.*?)(?=\n|$)"
    }

    for letter, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.DOTALL | re.IGNORECASE
        )

        if match:
            options[letter] = match.group(1).strip()

    # Only consider them original options if
    # all four A-D options were found.
    if len(options) == 4:
        return options

    return None


# --------------------------------------------------
# Detect an explicitly stated answer
# --------------------------------------------------

def extract_source_answer(text):

    patterns = [
        r"(?:answer|ans|correct answer)\s*[:\-]?\s*([A-D])\b",
        r"\(ans\)\s*([A-D])\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).upper()

    return None


# --------------------------------------------------
# Detect pharmaceutical calculations
# --------------------------------------------------

def detect_calculation(text):

    calculation_terms = [
        "calculate",
        "calculation",
        "how many ml",
        "how many mL",
        "how much",
        "dose",
        "dosage",
        "mg/ml",
        "mg/mL",
        "mcg",
        "microgram",
        "milligram",
        "dilution",
        "dilute",
        "ratio",
        "percentage",
        "percent",
        "alligation",
        "alligations",
        "concentration",
        "infusion rate",
        "drop rate",
        "drops per minute",
        "units/kg",
        "mg/kg",
        "mcg/kg"
    ]

    text_lower = text.lower()

    for term in calculation_terms:

        if term.lower() in text_lower:
            return True

    return False


# --------------------------------------------------
# Main parser
# --------------------------------------------------

def parse_questions(raw_text):

    # Split whenever we find a number followed by a hyphen.
    parts = re.split(
    r'\r?\n(?=\d+\s*[-.)])',
    raw_text.strip()
    )
    
    questions = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        # Extract question number
        match = re.match(
            r'(\d+)-(.*)',
            part,
            re.DOTALL
        )

        if not match:
            continue

        question_id = int(match.group(1))

        question_text = match.group(2).strip()

        # ------------------------------------------
        # Extract original options
        # ------------------------------------------

        options = extract_options(question_text)

        if options:
            options_source = "original"
        else:
            options_source = "ai_generated"

        # ------------------------------------------
        # Extract source answer
        # ------------------------------------------

        source_answer = extract_source_answer(
            question_text
        )

        # ------------------------------------------
        # Detect calculation
        # ------------------------------------------

        is_calculation = detect_calculation(
            question_text
        )

        if is_calculation:
            question_type = "pharmaceutical_calculation"
            review_required = True
        else:
            question_type = "unknown"
            review_required = False

        questions.append({

            "id": question_id,

            "raw_text": question_text,

            "options": options,

            "options_source": options_source,

            "source_answer": source_answer,

            "question_type": question_type,

            "review_required": review_required
        })

    return questions


# --------------------------------------------------
# Test parser
# --------------------------------------------------

if __name__ == "__main__":

    raw_text = load_raw_questions()

    questions = parse_questions(raw_text)

    print(
        f"Found {len(questions)} questions."
    )

    print("--------------------------------")

    for question in questions:

        print(
            f"ID: {question['id']}"
        )

        print(
            f"Type: {question['question_type']}"
        )

        print(
            f"Options source: {question['options_source']}"
        )

        print(
            f"Source answer: {question['source_answer']}"
        )

        print(
            f"Review required: {question['review_required']}"
        )

        if question["options"]:

            print("Original options:")

            for letter, option in question["options"].items():

                print(
                    f"{letter}. {option}"
                )

        print(
            question["raw_text"]
        )

        print("--------------------------------")