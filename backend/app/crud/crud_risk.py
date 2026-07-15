import json
import uuid
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.risk import UserRiskProfile
from app.schemas.risk import UserRiskProfileCreate, UserRiskProfileUpdate


def calculate_risk(answers: Dict[str, str]) -> Tuple[int, str]:
    # Grable & Lytton 13-item scale points definition
    points = {
        "q1": {"A": 4, "B": 3, "C": 2, "D": 1},
        "q2": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q3": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q4": {"A": 1, "B": 2, "C": 3},
        "q5": {"A": 1, "B": 2, "C": 3},
        "q6": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q7": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q8": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q9": {"A": 1, "B": 3},
        "q10": {"A": 1, "B": 3},
        "q11": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q12": {"A": 1, "B": 2, "C": 3},
        "q13": {"A": 1, "B": 2, "C": 3, "D": 4},
    }

    score = 0
    for q_key, choices in points.items():
        ans = answers.get(q_key)
        score += choices.get(ans, 0)

    # Determine risk category based on Grable & Lytton benchmarks:
    # 13 - 18: Low tolerance (Conservative)
    # 19 - 28: Below-average / Average tolerance (Moderate)
    # 29 - 32: Above-average tolerance (Growth)
    # 33 - 47: High tolerance (Aggressive)
    if score <= 18:
        category = "Conservative"
    elif score <= 28:
        category = "Moderate"
    elif score <= 32:
        category = "Growth"
    else:
        category = "Aggressive"

    return score, category


class CRUDRiskProfile(
    CRUDBase[UserRiskProfile, UserRiskProfileCreate, UserRiskProfileUpdate]
):
    def get_by_user(
        self, db: Session, *, user_id: uuid.UUID
    ) -> Optional[UserRiskProfile]:
        return (
            db.query(UserRiskProfile)
            .filter(UserRiskProfile.user_id == user_id)
            .first()
        )

    def create_or_update(
        self, db: Session, *, user_id: uuid.UUID, obj_in: UserRiskProfileCreate
    ) -> UserRiskProfile:
        db_obj = self.get_by_user(db, user_id=user_id)
        answers_str = json.dumps(obj_in.answers)
        score, category = calculate_risk(obj_in.answers)

        if db_obj:
            db_obj.answers = answers_str
            db_obj.score = score
            db_obj.risk_category = category
            db.add(db_obj)
            db.flush()
        else:
            db_obj = UserRiskProfile(
                user_id=user_id,
                answers=answers_str,
                score=score,
                risk_category=category,
            )
            db.add(db_obj)
            db.flush()
        return db_obj


risk_profile = CRUDRiskProfile(UserRiskProfile)
