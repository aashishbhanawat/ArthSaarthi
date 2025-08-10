import uuid

from pydantic import BaseModel, ConfigDict

# Need to import Portfolio and User schemas to be used as nested objects
from .portfolio import Portfolio
from .user import User


# Shared properties
class ImportSessionBase(BaseModel):
    file_name: str
    status: str
    error_message: str | None = None


# Properties to receive on item creation
class ImportSessionCreate(ImportSessionBase):
    file_path: str
    portfolio_id: uuid.UUID


# Properties to receive on item update
class ImportSessionUpdate(BaseModel):
    parsed_file_path: str | None = None
    status: str | None = None
    error_message: str | None = None


# Properties shared by models in DB
class ImportSessionInDBBase(ImportSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    portfolio_id: uuid.UUID
    file_path: str
    parsed_file_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class ImportSession(ImportSessionInDBBase):
    portfolio: Portfolio
    user: User


# Schema for the parsed transaction data from the file
class ParsedTransaction(BaseModel):
    transaction_date: str
    ticker_symbol: str
    transaction_type: str
    quantity: float
    price_per_unit: float
    fees: float
