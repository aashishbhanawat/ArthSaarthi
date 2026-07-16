import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class UserRiskProfileBase(BaseModel):
    answers: Dict[str, str]

    @field_validator("answers", mode="before")
    @classmethod
    def validate_answers(cls, v: Any) -> Dict[str, str]:
        import json
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except Exception:
                raise ValueError("answers must be a valid JSON string")
        if not isinstance(v, dict):
            raise ValueError("answers must be a dictionary")

        required_questions = {f"q{i}" for i in range(1, 14)}
        valid_choices_map = {
            "q1": {"A", "B", "C", "D"},
            "q2": {"A", "B", "C", "D"},
            "q3": {"A", "B", "C", "D"},
            "q4": {"A", "B", "C"},
            "q5": {"A", "B", "C"},
            "q6": {"A", "B", "C", "D"},
            "q7": {"A", "B", "C", "D"},
            "q8": {"A", "B", "C", "D"},
            "q9": {"A", "B"},
            "q10": {"A", "B"},
            "q11": {"A", "B", "C", "D"},
            "q12": {"A", "B", "C"},
            "q13": {"A", "B", "C", "D"},
        }

        # Check all questions are answered
        missing = required_questions - set(v.keys())
        if missing:
            raise ValueError(f"Missing answers for: {', '.join(sorted(missing))}")

        # Check for unexpected questions
        extra = set(v.keys()) - required_questions
        if extra:
            raise ValueError(f"Unexpected questions found: {', '.join(sorted(extra))}")

        # Validate choices
        for q, ans in v.items():
            allowed = valid_choices_map.get(q, set())
            if ans not in allowed:
                raise ValueError(
                    f"Invalid answer '{ans}' for question '{q}'. "
                    f"Must be one of {sorted(allowed)}"
                )

        return v


class UserRiskProfileCreate(UserRiskProfileBase):
    pass


class UserRiskProfileUpdate(UserRiskProfileBase):
    pass


class UserRiskProfile(UserRiskProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    score: Optional[int] = None
    risk_category: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
