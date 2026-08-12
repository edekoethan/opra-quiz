import os
import json

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# 1. LOAD OPENAI API KEY
# ============================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# 2. GENERATE / PROCESS ONE QUESTION
# ============================================================

def generate_question(
    raw_question,
    original_options=None,
    options_source="ai_generated",
    source_answer=None,
    question_type="unknown",
    review_required=False
):

    # --------------------------------------------------------
    # Tell the AI what kind of options it received
    # --------------------------------------------------------

    if original_options:

        options_instruction = f"""
The source question already contains original answer options.

YOU MUST PRESERVE THESE OPTIONS.

Do NOT:
- rewrite them
- replace them
- invent new options
- remove options
- change their meaning

Use exactly these options:

A. {original_options["A"]}
B. {original_options["B"]}
C. {original_options["C"]}
D. {original_options["D"]}

Your task is to identify the correct option and explain
why each option is correct or incorrect.
"""

    else:

        options_instruction = """
The source question does NOT contain four original answer
options.

Create exactly FOUR options.

Create THREE plausible distractors and ONE correct answer.

The distractors should be medically/pharmaceutically plausible
and should test knowledge rather than being obviously wrong.
"""

    # --------------------------------------------------------
    # Calculation instructions
    # --------------------------------------------------------

    if question_type == "pharmaceutical_calculation":

        calculation_instruction = """
THIS IS A PHARMACEUTICAL CALCULATION.

This question MUST be flagged for human review.

You must:

1. Carefully identify all numerical information.
2. Preserve the units exactly.
3. Pay particular attention to:
   - mg vs mcg
   - g vs mg
   - mL vs L
   - concentration
   - percentages
   - ratios
   - dose/kg
   - infusion rates
   - alligation
   - dilution
4. Show the calculation step-by-step.
5. State the proposed final answer and units.
6. DO NOT mark the question as approved.
7. Set status to "needs_review".
8. Set review_required to true.

Even if you are highly confident in the calculation,
human verification is mandatory.
"""

    else:

        calculation_instruction = """
This is not currently classified as a pharmaceutical
calculation.

Do not invent calculations that are not necessary.
"""

    # --------------------------------------------------------
    # Source answer information
    # --------------------------------------------------------

    if source_answer:

        source_answer_instruction = f"""
The original source indicates that the answer is:

{source_answer}

You MUST preserve this answer.

If original options are present, identify which option
corresponds to this answer.

If you believe the supplied answer is questionable,
DO NOT silently change it.

Instead:
- preserve the supplied answer
- set status to "needs_review"
- explain the concern in review_reason
"""

    else:

        source_answer_instruction = """
The source does not explicitly provide an answer letter.

Determine the correct answer from the supplied source
material.

Do not invent unsupported information.
"""

    # ========================================================
    # MAIN PROMPT
    # ========================================================

    prompt = f"""
You are an expert pharmacy examination question editor
and quality-control reviewer.

Your task is to transform a remembered pharmacy examination
question into a high-quality single-best-answer MCQ.

The source material may be incomplete, abbreviated,
poorly formatted, or contain notes remembered from an exam.

IMPORTANT:

The source material is the primary basis for the question.

Do not silently replace the intended answer with a different
answer simply because you would have written the question
differently.

------------------------------------------------------------
QUESTION TYPE
------------------------------------------------------------

Current classification:

{question_type}

------------------------------------------------------------
OPTIONS
------------------------------------------------------------

{options_instruction}

------------------------------------------------------------
SOURCE ANSWER
------------------------------------------------------------

{source_answer_instruction}

------------------------------------------------------------
CALCULATIONS
------------------------------------------------------------

{calculation_instruction}

------------------------------------------------------------
GENERAL RULES
------------------------------------------------------------

1. Preserve the intended knowledge being tested.

2. Create exactly FOUR options.

3. There must be exactly ONE best answer.

4. Do not create two options that could reasonably both
   be considered correct.

5. Distractors should be plausible.

6. Avoid obviously ridiculous distractors.

7. Keep explanations concise.

8. Explain every option.

9. Each explanation should normally be 1-2 sentences.

10. Assign exactly ONE category.

11. Assign an appropriate topic.

12. Assign difficulty:
    - easy
    - medium
    - hard

13. If the source is ambiguous, incomplete, potentially
    incorrect, or medically questionable, use:
    "needs_review"

14. Never hide uncertainty.

15. Pharmaceutical calculations ALWAYS require human review.

------------------------------------------------------------
ALLOWED CATEGORIES
------------------------------------------------------------

Choose exactly ONE:

- Biomedical Sciences
- Medicinal Chemistry & Biopharmaceutics
- Pharmacokinetics & Pharmacodynamics
- Pharmacology & Toxicology
- Therapeutics & Patient Care

------------------------------------------------------------
OUTPUT
------------------------------------------------------------

Return ONLY valid JSON.

Do not use Markdown.

Do not put the JSON inside ```json```.

Use exactly this structure:

{{
    "status": "approved",

    "review_required": false,

    "review_reason": null,

    "confidence": 0.95,

    "question_type": "factual",

    "options_source": "ai_generated",

    "source_answer": null,

    "category": "Pharmacology & Toxicology",

    "topic": "Example topic",

    "difficulty": "easy",

    "question": "Example question?",

    "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
    }},

    "correct_answer": "A",

    "explanations": {{
        "A": "Why A is correct.",
        "B": "Why B is incorrect.",
        "C": "Why C is incorrect.",
        "D": "Why D is incorrect."
    }},

    "calculation": null
}}

For pharmaceutical calculations, use this structure
inside "calculation":

{{
    "given_information": "...",
    "formula": "...",
    "working": "...",
    "proposed_answer": "...",
    "units": "..."
}}

------------------------------------------------------------
SOURCE QUESTION
------------------------------------------------------------

{raw_question}
"""

    # ========================================================
    # CALL OPENAI
    # ========================================================

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    result_text = response.output_text

    # ========================================================
    # CONVERT JSON TEXT → PYTHON DICTIONARY
    # ========================================================

    result = json.loads(result_text)

    # ========================================================
    # SAFETY OVERRIDES
    # ========================================================

    # Pharmaceutical calculations can NEVER bypass human review.

    if question_type == "pharmaceutical_calculation":

        result["status"] = "needs_review"
        result["review_required"] = True

        if not result.get("review_reason"):
            result["review_reason"] = (
                "Pharmaceutical calculation requires "
                "human verification before publication."
            )

    # --------------------------------------------------------
    # Incomplete source records should not automatically
    # become approved questions.
    # --------------------------------------------------------

    if question_type == "incomplete":

        result["status"] = "needs_review"
        result["review_required"] = True

        if not result.get("review_reason"):
            result["review_reason"] = (
                "Source question is incomplete and requires "
                "human verification before publication."
            )

    # --------------------------------------------------------
    # Very low confidence requires review.
    # --------------------------------------------------------

    confidence = result.get("confidence")

    if confidence is not None:

        try:
            confidence_value = float(confidence)

            if confidence_value < 0.80:

                result["status"] = "needs_review"
                result["review_required"] = True

                if not result.get("review_reason"):
                    result["review_reason"] = (
                        "AI confidence is below the publication "
                        "threshold and requires human review."
                    )

        except (TypeError, ValueError):
            pass

    return result


# ============================================================
# 3. TEST
# ============================================================

if __name__ == "__main__":

    test_question = """
    Which drug is used for Q Fever? Doxycycline
    """

    print("Sending question to OpenAI...")
    print("--------------------------------")

    result = generate_question(
        raw_question=test_question,
        original_options=None,
        options_source="ai_generated",
        source_answer="Doxycycline",
        question_type="unknown",
        review_required=False
    )

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )