from dataclasses import dataclass
from typing import Dict


@dataclass
class Question:
    id: int
    category: str
    topic: str
    difficulty: str
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: Dict[str, str]
    status: str