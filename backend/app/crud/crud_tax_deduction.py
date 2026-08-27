import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.tax_deduction import TaxDeduction
from app.schemas.tax_deduction import TaxDeductionCreate, TaxDeductionUpdate
from app.utils.pydantic_compat import model_dump

STATUTORY_LIMITS: Dict[str, Dict[str, Any]] = {
    "80C": {
        "limit": Decimal("150000.00"),
        "name": "Section 80C (PPF, ELSS, EPF, LIC, etc.)",
    },
    "80D": {
        "limit": Decimal("25000.00"),
        "name": "Section 80D (Health Insurance & Medical)",
    },
    "80CCD_1B": {
        "limit": Decimal("50000.00"),
        "name": "Section 80CCD(1B) (NPS Contribution)",
    },
    "80TTA": {
        "limit": Decimal("10000.00"),
        "name": "Section 80TTA (Savings Account Interest)",
    },
    "80TTB": {
        "limit": Decimal("50000.00"),
        "name": "Section 80TTB (Senior Citizen Savings Interest)",
    },
    "80G": {
        "limit": None,
        "name": "Section 80G (Donations to Charitable Funds)",
    },
    "80E": {
        "limit": None,
        "name": "Section 80E (Education Loan Interest)",
    },
    "OTHER": {
        "limit": None,
        "name": "Other Chapter VI-A Deductions",
    },
}


class CRUDTaxDeduction(CRUDBase[TaxDeduction, TaxDeductionCreate, TaxDeductionUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: TaxDeductionCreate, user_id: uuid.UUID
    ) -> TaxDeduction:
        data = model_dump(obj_in)
        amount_dec = Decimal(str(data["amount"]))

        db_obj = TaxDeduction(
            user_id=user_id,
            financial_year=data["financial_year"],
            section=data["section"],
            title=data["title"],
            amount=str(amount_dec),
            deduction_date=data["deduction_date"],
            proof_notes=data.get("proof_notes"),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_with_owner(
        self,
        db: Session,
        *,
        db_obj: TaxDeduction,
        obj_in: TaxDeductionUpdate,
    ) -> TaxDeduction:
        update_data = model_dump(obj_in, exclude_unset=True)

        for field, value in update_data.items():
            if field == "amount" and value is not None:
                setattr(db_obj, field, str(Decimal(str(value))))
            elif field in [
                "financial_year",
                "section",
                "title",
                "deduction_date",
                "proof_notes",
            ]:
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        financial_year: Optional[str] = None,
        section: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaxDeduction]:
        query = db.query(TaxDeduction).filter(TaxDeduction.user_id == user_id)
        if financial_year:
            query = query.filter(TaxDeduction.financial_year == financial_year)
        if section:
            query = query.filter(TaxDeduction.section == section)

        return (
            query.order_by(TaxDeduction.deduction_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_owner(
        self, db: Session, *, id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[TaxDeduction]:
        return (
            db.query(TaxDeduction)
            .filter(TaxDeduction.id == id, TaxDeduction.user_id == user_id)
            .first()
        )

    def get_summary_by_fy(
        self, db: Session, *, user_id: uuid.UUID, financial_year: str
    ) -> Dict[str, Any]:
        entries = self.get_multi_by_owner(
            db, user_id=user_id, financial_year=financial_year, limit=1000
        )

        section_invested: Dict[str, Decimal] = {}
        for entry in entries:
            sec = entry.section
            amt = Decimal(str(entry.amount))
            section_invested[sec] = section_invested.get(sec, Decimal("0.00")) + amt

        sections_list = []
        total_invested = Decimal("0.00")
        total_eligible = Decimal("0.00")

        all_sections = list(STATUTORY_LIMITS.keys())
        for sec in section_invested.keys():
            if sec not in all_sections:
                all_sections.append(sec)

        for sec in all_sections:
            invested = section_invested.get(sec, Decimal("0.00"))
            limit_info = STATUTORY_LIMITS.get(
                sec, {"limit": None, "name": f"Section {sec}"}
            )
            max_limit = limit_info["limit"]
            sec_name = limit_info["name"]

            if max_limit is not None:
                eligible = min(invested, max_limit)
            else:
                eligible = invested

            total_invested += invested
            total_eligible += eligible

            if invested > Decimal("0.00") or sec in ["80C", "80D", "80CCD_1B"]:
                sections_list.append(
                    {
                        "section": sec,
                        "section_name": sec_name,
                        "total_invested": invested,
                        "max_limit": max_limit,
                        "eligible_deduction": eligible,
                    }
                )

        return {
            "financial_year": financial_year,
            "total_invested": total_invested,
            "total_eligible_deduction": total_eligible,
            "sections": sections_list,
        }


crud_tax_deduction = CRUDTaxDeduction(TaxDeduction)
