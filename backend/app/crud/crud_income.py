import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.income import IncomeEntry, IncomeSource
from app.schemas.income import (
    IncomeEntryCreate,
    IncomeEntryUpdate,
    IncomeSourceCreate,
    IncomeSourceUpdate,
)
from app.utils.pydantic_compat import model_dump


class CRUDIncomeSource(CRUDBase[IncomeSource, IncomeSourceCreate, IncomeSourceUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: IncomeSourceCreate, user_id: uuid.UUID
    ) -> IncomeSource:
        data = model_dump(obj_in)
        db_obj = IncomeSource(**data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[IncomeSource]:
        return (
            db.query(IncomeSource)
            .filter(IncomeSource.user_id == user_id)
            .order_by(IncomeSource.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_owner(
        self, db: Session, *, id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[IncomeSource]:
        return (
            db.query(IncomeSource)
            .filter(IncomeSource.id == id, IncomeSource.user_id == user_id)
            .first()
        )


class CRUDIncomeEntry(CRUDBase[IncomeEntry, IncomeEntryCreate, IncomeEntryUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: IncomeEntryCreate, user_id: uuid.UUID
    ) -> IncomeEntry:
        data = model_dump(obj_in)
        gross = Decimal(str(data["gross_amount"]))
        tds = Decimal(str(data.get("tds_amount", 0) or 0))
        net = gross - tds

        db_obj = IncomeEntry(
            user_id=user_id,
            source_id=data["source_id"],
            financial_year=data["financial_year"],
            entry_date=data["entry_date"],
            gross_amount=str(gross),
            tds_amount=str(tds),
            net_amount=str(net),
            notes=data.get("notes"),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_with_owner(
        self,
        db: Session,
        *,
        db_obj: IncomeEntry,
        obj_in: IncomeEntryUpdate,
    ) -> IncomeEntry:
        update_data = model_dump(obj_in, exclude_unset=True)

        # Calculate new amounts if gross or tds are updated
        gross_val = update_data.get("gross_amount", db_obj.gross_amount)
        tds_val = update_data.get("tds_amount", db_obj.tds_amount)

        gross = Decimal(str(gross_val))
        tds = Decimal(str(tds_val))
        if tds > gross:
            raise ValueError("TDS amount cannot exceed gross income amount")

        net = gross - tds

        for field, value in update_data.items():
            if field in ["gross_amount", "tds_amount"]:
                setattr(db_obj, field, str(value))
            elif field in ["notes", "financial_year", "entry_date", "source_id"]:
                setattr(db_obj, field, value)

        db_obj.net_amount = str(net)
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
        source_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[IncomeEntry]:
        query = db.query(IncomeEntry).filter(IncomeEntry.user_id == user_id)
        if financial_year:
            from app.core.tax_rules_registry import get_fy_variations
            fy_list = get_fy_variations(financial_year)
            query = query.filter(IncomeEntry.financial_year.in_(fy_list))
        if source_id:
            query = query.filter(IncomeEntry.source_id == source_id)

        return (
            query.order_by(IncomeEntry.entry_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_owner(
        self, db: Session, *, id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[IncomeEntry]:
        return (
            db.query(IncomeEntry)
            .filter(IncomeEntry.id == id, IncomeEntry.user_id == user_id)
            .first()
        )

    def get_summary_by_fy(
        self, db: Session, *, user_id: uuid.UUID, financial_year: str
    ) -> Dict[str, Any]:
        entries = self.get_multi_by_owner(
            db, user_id=user_id, financial_year=financial_year, limit=1000
        )

        total_gross = Decimal("0.00")
        total_tds = Decimal("0.00")
        total_net = Decimal("0.00")
        source_totals: Dict[str, Dict[str, Any]] = {}

        for entry in entries:
            g = Decimal(str(entry.gross_amount))
            t = Decimal(str(entry.tds_amount))
            n = Decimal(str(entry.net_amount))

            total_gross += g
            total_tds += t
            total_net += n

            sid = str(entry.source_id)
            s_name = entry.source.name if entry.source else "Unknown"
            s_cat = entry.source.category if entry.source else "OTHER"

            if sid not in source_totals:
                source_totals[sid] = {
                    "source_id": sid,
                    "source_name": s_name,
                    "category": s_cat,
                    "gross_amount": Decimal("0.00"),
                    "tds_amount": Decimal("0.00"),
                    "net_amount": Decimal("0.00"),
                    "count": 0,
                }
            source_totals[sid]["gross_amount"] += g
            source_totals[sid]["tds_amount"] += t
            source_totals[sid]["net_amount"] += n
            source_totals[sid]["count"] += 1

        return {
            "financial_year": financial_year,
            "total_gross": total_gross,
            "total_tds": total_tds,
            "total_net": total_net,
            "source_breakdown": list(source_totals.values()),
        }


crud_income_source = CRUDIncomeSource(IncomeSource)
crud_income_entry = CRUDIncomeEntry(IncomeEntry)
