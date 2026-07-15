import json
import uuid
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.risk import UserRiskProfile
from app.schemas.risk import UserRiskProfileCreate, UserRiskProfileUpdate


def calculate_risk(answers: Dict[str, str]) -> Tuple[int, str]:
    # Points definition
    points = {
        "q1": {"A": 6, "B": 4, "C": 2, "D": 1},
        "q2": {"A": 6, "B": 4, "C": 2, "D": 1},
        "q3": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q4": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q5": {"A": 1, "B": 2, "C": 3, "D": 4},
        "q6": {"A": 1, "B": 2, "C": 3, "D": 4},
    }

    score = 0
    for q_key, choices in points.items():
        ans = answers.get(q_key)
        score += choices.get(ans, 0)

    # Determine risk category
    if 6 <= score <= 10:
        category = "Conservative"
    elif 11 <= score <= 20:
        category = "Moderate"
    elif 21 <= score <= 24:
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
