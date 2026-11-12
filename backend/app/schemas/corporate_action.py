import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CorporateActionEventBase(BaseModel):
    event_type: str
    event_date: date
    units: Decimal
    amount: Decimal
    status: str
    details: Optional[Dict[str, Any]] = None


class CorporateActionEventOut(CorporateActionEventBase):
    id: uuid.UUID
    user_id: uuid.UUID
    portfolio_id: uuid.UUID
    asset_id: uuid.UUID
    transaction_id: Optional[uuid.UUID] = None
    created_at: datetime
    bond_name: Optional[str] = None
    isin: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CorporateActionEventListResponse(BaseModel):
    items: List[CorporateActionEventOut]
    total: int
    unread_count: int


class CorporateActionTriggerResponse(BaseModel):
    message: str
    events_created: int
    status: str
