import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .transaction import Transaction


# Shared properties
class PortfolioBase(BaseModel):
    name: str
    description: str | None = None


# Properties to receive on portfolio creation
class PortfolioCreate(PortfolioBase):
    pass


# Properties to receive on portfolio update
class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# Properties to return to client
class Portfolio(PortfolioBase):
    id: uuid.UUID
    user_id: uuid.UUID
    transactions: List[Transaction] = []
    model_config = ConfigDict(from_attributes=True)
