import uuid

from pydantic import BaseModel, ConfigDict

# Need to import Portfolio and User schemas to be used as nested objects
from .asset_alias import AssetAliasCreate
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
    source: str


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
    source: str
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
    isin: str | None = None


# New schema for the categorized preview response
class ImportSessionPreview(BaseModel):
    valid_new: list[ParsedTransaction]
    duplicates: list[ParsedTransaction]
    invalid: list[dict]  # e.g., {"row_data": {...}, "error": "Invalid data format"}
    needs_mapping: list[
        ParsedTransaction
    ]  # For rows with unrecognized ticker symbols


# New schema for the selective commit request body
class ImportSessionCommit(BaseModel):
    transactions_to_commit: list[ParsedTransaction]
    aliases_to_create: list[AssetAliasCreate] = []
