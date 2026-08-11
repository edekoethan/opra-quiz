from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="OPRA Quiz API",
    description="Backend API for the OPRA Quiz application",
    version="1.0.0"
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# FILE LOCATIONS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

APPROVED_FILE = os.path.join(
    BASE_DIR,
    "approved_questions.json"
)

REVIEW_FILE = os.path.join(
    BASE_DIR,
    "needs_review_questions.json"
)

REJECTED_FILE = os.path.join(
    BASE_DIR,
    "rejected_questions.json"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_questions(filename):
    """Load questions from a JSON file."""

    if not os.path.exists(filename):
        return []

    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def save_questions(filename, questions):
    """Save questions to a JSON file."""

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            questions,
            file,
            indent=4,
            ensure_ascii=False
        )


def find_question(question_id, questions):
    """Find a question using its source_id."""

    for question in questions:
        if question.get("source_id") == question_id:
            return question

    return None


# ============================================================
# REQUEST MODEL FOR EDITING QUESTIONS
# ============================================================

class QuestionEdit(BaseModel):

    question: Optional[str] = None

    options: Optional[dict] = None

    correct_answer: Optional[str] = None

    explanations: Optional[dict] = None

    category: Optional[str] = None

    topic: Optional[str] = None

    difficulty: Optional[str] = None

    calculation: Optional[dict] = None


# ============================================================
# BASIC HEALTH CHECK
# ============================================================

@app.get("/")
def home():

    return {
        "message": "OPRA Quiz API is running!"
    }


# ============================================================
# GET REVIEW QUEUE
# ============================================================

@app.get("/admin/review")
def get_review_questions():

    questions = load_questions(REVIEW_FILE)

    return {
        "count": len(questions),
        "questions": questions
    }


# ============================================================
# GET ONE REVIEW QUESTION
# ============================================================

@app.get("/admin/review/{question_id}")
def get_review_question(question_id: int):

    questions = load_questions(REVIEW_FILE)

    question = find_question(
        question_id,
        questions
    )

    if question is None:

        raise HTTPException(
            status_code=404,
            detail="Question not found in review queue."
        )

    return question


# ============================================================
# EDIT QUESTION
# ============================================================

@app.put("/admin/review/{question_id}")
def edit_question(
    question_id: int,
    edits: QuestionEdit
):

    questions = load_questions(REVIEW_FILE)

    question = find_question(
        question_id,
        questions
    )

    if question is None:

        raise HTTPException(
            status_code=404,
            detail="Question not found in review queue."
        )

    # Only update fields that were actually supplied.
    changes = edits.model_dump(
        exclude_unset=True
    )

    for field, value in changes.items():
        question[field] = value

    # Editing does not automatically approve.
    question["human_status"] = "pending"
    question["human_reviewed"] = False
    question["status"] = "needs_review"

    save_questions(
        REVIEW_FILE,
        questions
    )

    return {
        "message": "Question updated successfully.",
        "question": question
    }


# ============================================================
# APPROVE QUESTION
# ============================================================

@app.post("/admin/review/{question_id}/approve")
def approve_question(question_id: int):

    review_questions = load_questions(
        REVIEW_FILE
    )

    approved_questions = load_questions(
        APPROVED_FILE
    )

    question = find_question(
        question_id,
        review_questions
    )

    if question is None:

        raise HTTPException(
            status_code=404,
            detail="Question not found in review queue."
        )

    # --------------------------------------------------------
    # Human approval
    # --------------------------------------------------------

    question["human_status"] = "approved"
    question["human_reviewed"] = True
    question["status"] = "approved"

    # --------------------------------------------------------
    # Prevent accidental duplicate approval
    # --------------------------------------------------------

    existing = find_question(
        question_id,
        approved_questions
    )

    if existing is None:

        approved_questions.append(question)

    # --------------------------------------------------------
    # Remove from review queue
    # --------------------------------------------------------

    review_questions = [
        q for q in review_questions
        if q.get("source_id") != question_id
    ]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_questions(
        REVIEW_FILE,
        review_questions
    )

    save_questions(
        APPROVED_FILE,
        approved_questions
    )

    return {
        "message": "Question approved successfully.",
        "question_id": question_id,
        "human_status": "approved"
    }


# ============================================================
# REJECT QUESTION
# ============================================================

@app.post("/admin/review/{question_id}/reject")
def reject_question(question_id: int):

    review_questions = load_questions(
        REVIEW_FILE
    )

    rejected_questions = load_questions(
        REJECTED_FILE
    )

    question = find_question(
        question_id,
        review_questions
    )

    if question is None:

        raise HTTPException(
            status_code=404,
            detail="Question not found in review queue."
        )

    # --------------------------------------------------------
    # Human rejection
    # --------------------------------------------------------

    question["human_status"] = "rejected"
    question["human_reviewed"] = True
    question["status"] = "rejected"

    # --------------------------------------------------------
    # Store rejected question
    # --------------------------------------------------------

    existing = find_question(
        question_id,
        rejected_questions
    )

    if existing is None:

        rejected_questions.append(question)

    # --------------------------------------------------------
    # Remove from review queue
    # --------------------------------------------------------

    review_questions = [
        q for q in review_questions
        if q.get("source_id") != question_id
    ]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_questions(
        REVIEW_FILE,
        review_questions
    )

    save_questions(
        REJECTED_FILE,
        rejected_questions
    )

    return {
        "message": "Question rejected.",
        "question_id": question_id,
        "human_status": "rejected"
    }


# ============================================================
# GET APPROVED QUESTIONS
# ============================================================

@app.get("/admin/approved")
def get_approved_questions():

    questions = load_questions(
        APPROVED_FILE
    )

    return {
        "count": len(questions),
        "questions": questions
    }


# ============================================================
# GET REJECTED QUESTIONS
# ============================================================

@app.get("/admin/rejected")
def get_rejected_questions():

    questions = load_questions(
        REJECTED_FILE
    )

    return {
        "count": len(questions),
        "questions": questions
    }