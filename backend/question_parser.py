import re
from question_loader import load_raw_questions


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    """
    Clean formatting without changing the meaning of the
    original source.
    """

    text = text.replace("\r", "\n")

    # Replace multiple spaces/tabs with one space
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# DETECT OPTIONS
# ============================================================

def extract_options(text):

    options = {}

    # Standard A-D formats:
    # A. option
    # A) option
    # A - option
    patterns = {
        "A": r"(?:^|\n)\s*A\s*[\.\):\-]\s*(.*?)(?=\n\s*B\s*[\.\):\-]|\Z)",
        "B": r"(?:^|\n)\s*B\s*[\.\):\-]\s*(.*?)(?=\n\s*C\s*[\.\):\-]|\Z)",
        "C": r"(?:^|\n)\s*C\s*[\.\):\-]\s*(.*?)(?=\n\s*D\s*[\.\):\-]|\Z)",
        "D": r"(?:^|\n)\s*D\s*[\.\):\-]\s*(.*?)(?=\n|$)"
    }

    for letter, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.DOTALL | re.IGNORECASE
        )

        if match:

            option_text = clean_text(
                match.group(1)
            )

            if option_text:
                options[letter] = option_text

    # Only call them original MCQ options if all four
    # standard options are present.
    if len(options) == 4:
        return options

    return None


# ============================================================
# DETECT NUMBERED OPTIONS
# ============================================================

def extract_numbered_options(text):

    """
    Detect options such as:

        1. SGLT-2
        2. Metformin

    These are NOT automatically treated as standard
    A-D options. They are preserved as source material.
    """

    matches = re.findall(
        r"(?:^|\n)\s*([1-9])\s*[\.\):\-]\s*(.+?)(?=\n|$)",
        text,
        re.IGNORECASE
    )

    if not matches:
        return None

    options = {}

    for number, option in matches:

        option = clean_text(option)

        if option:
            options[number] = option

    return options if options else None


# ============================================================
# DETECT SOURCE ANSWER
# ============================================================

def extract_source_answer(text):

    patterns = [

        # Answer: B
        r"(?:answer|ans|correct answer)"
        r"\s*[:\-]?\s*([A-D])\b",

        # (ans) B
        r"\(ans\)\s*([A-D])\b",

        # Answer = B
        r"(?:answer|ans)\s*=\s*([A-D])\b"
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


# ============================================================
# DETECT YES / NO SOURCE ANSWER
# ============================================================

def extract_yes_no_answer(text):

    """
    Detect simple remembered answers such as:

        Yes
        No

    Only used as source information. It does NOT mean
    the question is automatically approved.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    last_line = lines[-1].lower()

    if last_line in {"yes", "no"}:
        return last_line.capitalize()

    return None


# ============================================================
# DETECT CALCULATIONS
# ============================================================

def detect_calculation(text):

    calculation_terms = [

        "calculate",
        "calculation",
        "how many ml",
        "how many ml",
        "how much",
        "dose",
        "dosage",
        "mg/ml",
        "mg/ml",
        "mcg",
        "microgram",
        "milligram",
        "gram",
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
        "mcg/kg",
        "per kg",
        "ml per hour",
        "ml/hour"
    ]

    text_lower = text.lower()

    for term in calculation_terms:

        if term.lower() in text_lower:
            return True

    return False


# ============================================================
# DETECT WHETHER SOURCE LOOKS INCOMPLETE
# ============================================================

def detect_incomplete(text):

    """
    Conservative detection of obviously incomplete source
    material.

    This does NOT attempt to correct the question.
    """

    stripped = text.strip()

    if not stripped:
        return True

    words = stripped.split()

    # Very short fragments are likely incomplete.
    if len(words) <= 3:
        return True

    # Common unfinished endings.
    incomplete_endings = [
        "which",
        "what",
        "why",
        "how",
        "caused by",
        "used for",
        "treatment for",
        "associated with",
        "least associated",
        "not commonly",
        "which one",
        "which drug",
        "which medication",
        "is",
        "are",
        "the",
        "of",
        "for"
    ]

    lower = stripped.lower()

    for ending in incomplete_endings:

        if lower.endswith(ending):
            return True

    return False


# ============================================================
# DETECT LIKELY FRAGMENTED NUMBERED OPTIONS
# ============================================================

def looks_like_numbered_option(line):

    """
    Detect lines such as:

        1. SGLT-2
        2. metformin

    These can occur inside a question after PDF extraction.
    """

    return bool(
        re.match(
            r"^\s*[1-9]\s*[\.\):\-]\s*\S+",
            line
        )
    )


# ============================================================
# SPLIT RAW BANK INTO SOURCE RECORDS
# ============================================================

def split_question_blocks(raw_text):

    """
    Split the raw document into likely question blocks.

    The source uses formats such as:

        1. Question
        2. Question

    We deliberately preserve the original text.
    """

    lines = raw_text.splitlines()

    blocks = []

    current_block = []
    current_id = None

    for line in lines:

        stripped = line.strip()

        if not stripped:
            if current_block:
                current_block.append("")
            continue

        # Detect top-level question numbering.
        match = re.match(
            r"^\s*(\d+)\s*[\.\)]\s+(.*)",
            line
        )

        if match:

            number = int(match.group(1))
            content = match.group(2).strip()

            if current_block:

                blocks.append({
                    "id": current_id,
                    "text": "\n".join(
                        current_block
                    ).strip()
                })

            current_id = number

            current_block = [
                content
            ]

        else:

            if current_block:
                current_block.append(line)

    # Add final block
    if current_block:

        blocks.append({
            "id": current_id,
            "text": "\n".join(
                current_block
            ).strip()
        })

    return blocks


# ============================================================
# MAIN PARSER
# ============================================================

def parse_questions(raw_text):

    blocks = split_question_blocks(
        raw_text
    )

    questions = []

    for block in blocks:

        question_id = block["id"]

        raw_question = clean_text(
            block["text"]
        )

        # ----------------------------------------------------
        # OPTIONS
        # ----------------------------------------------------

        options = extract_options(
            raw_question
        )

        numbered_options = None

        if not options:

            numbered_options = (
                extract_numbered_options(
                    raw_question
                )
            )

        if options:

            options_source = "original"

        elif numbered_options:

            options_source = "numbered_source"

        else:

            options_source = "ai_generated"

        # ----------------------------------------------------
        # SOURCE ANSWER
        # ----------------------------------------------------

        source_answer = (
            extract_source_answer(
                raw_question
            )
        )

        yes_no_answer = (
            extract_yes_no_answer(
                raw_question
            )
        )

        # ----------------------------------------------------
        # QUESTION TYPE
        # ----------------------------------------------------

        is_calculation = detect_calculation(
            raw_question
        )

        incomplete = detect_incomplete(
            raw_question
        )

        if is_calculation:

            question_type = (
                "pharmaceutical_calculation"
            )

            review_required = True

        elif incomplete:

            question_type = "incomplete"

            review_required = True

        elif options:

            question_type = "mcq"

            review_required = False

        elif yes_no_answer:

            question_type = "yes_no"

            review_required = True

        else:

            question_type = "unknown"

            review_required = True

        # ----------------------------------------------------
        # BUILD RECORD
        # ----------------------------------------------------

        question = {

            "id": question_id,

            "raw_text": raw_question,

            "options": options,

            "numbered_options":
                numbered_options,

            "options_source":
                options_source,

            "source_answer":
                source_answer,

            "yes_no_answer":
                yes_no_answer,

            "question_type":
                question_type,

            "review_required":
                review_required
        }

        questions.append(
            question
        )

    return questions


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    raw_text = load_raw_questions()

    questions = parse_questions(
        raw_text
    )

    print()
    print("=" * 70)
    print("OPRA QUESTION BANK PARSER")
    print("=" * 70)

    print(
        f"Total source records: {len(questions)}"
    )

    print()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    mcq = 0
    incomplete = 0
    calculations = 0
    yes_no = 0
    unknown = 0
    review = 0

    for question in questions:

        qtype = question[
            "question_type"
        ]

        if qtype == "mcq":
            mcq += 1

        elif qtype == "incomplete":
            incomplete += 1

        elif qtype == "pharmaceutical_calculation":
            calculations += 1

        elif qtype == "yes_no":
            yes_no += 1

        else:
            unknown += 1

        if question[
            "review_required"
        ]:
            review += 1

    print(
        f"Complete MCQs: {mcq}"
    )

    print(
        f"Incomplete: {incomplete}"
    )

    print(
        f"Calculations: {calculations}"
    )

    print(
        f"Yes/No: {yes_no}"
    )

    print(
        f"Unknown: {unknown}"
    )

    print(
        f"Requires review: {review}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Display first 30 records
    # --------------------------------------------------------

    print()
    print("FIRST 30 SOURCE RECORDS")
    print("=" * 70)

    for question in questions[:30]:

        print()
        print(
            f"ID: {question['id']}"
        )

        print(
            f"Type: {question['question_type']}"
        )

        print(
            f"Options source: "
            f"{question['options_source']}"
        )

        print(
            f"Source answer: "
            f"{question['source_answer']}"
        )

        print(
            f"Review required: "
            f"{question['review_required']}"
        )

        print(
            "Raw source:"
        )

        print(
            question["raw_text"]
        )

        print("-" * 70)