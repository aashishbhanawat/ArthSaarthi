from pydantic import BaseModel, ConfigDict
from typing import List
from typing import Optional
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
    id: int
    user_id: int
    transactions: List[Transaction] = []
    model_config = ConfigDict(from_attributes=True)