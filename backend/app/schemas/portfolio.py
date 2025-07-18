from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from .transaction import Transaction


# Shared properties
class PortfolioBase(BaseModel):
    name: str


# Properties to receive on portfolio creation
class PortfolioCreate(PortfolioBase):
    pass


# Properties to receive on portfolio update
class PortfolioUpdate(BaseModel):
    name: Optional[str] = None


# Properties shared by models stored in DB
class PortfolioInDBBase(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Properties to return to client
class Portfolio(PortfolioInDBBase):
    transactions: List[Transaction] = []


# Properties stored in DB
class PortfolioInDB(PortfolioInDBBase):
    pass