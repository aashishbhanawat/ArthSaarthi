import math
import uuid
from typing import Any, List

from pydantic import BaseModel, root_validator

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

    class Config:
        from_attributes = True
        orm_mode = True


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

    @root_validator(pre=True)
    @classmethod
    def fix_nan(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, float) and math.isnan(v):
                    data[k] = None
        return data


# New schema for the categorized preview response
class ImportSessionPreview(BaseModel):
    valid_new: List[ParsedTransaction]
    duplicates: List[ParsedTransaction]
    invalid: List[dict]  # e.g., {"row_data": {...}, "error": "Invalid data format"}
    needs_mapping: List[
        ParsedTransaction
    ]  # For rows with unrecognized ticker symbols


# New schema for the selective commit request body
class ImportSessionCommit(BaseModel):
    transactions_to_commit: List[ParsedTransaction]
    aliases_to_create: List[AssetAliasCreate] = []


# Schema for parsed FD data from bank statements
class ParsedFixedDeposit(BaseModel):
    bank: str
    account_number: str | None = None
    principal_amount: float
    interest_rate: float
    start_date: str
    maturity_date: str
    maturity_amount: float | None = None
    interest_payout: str = "Cumulative"
    compounding_frequency: str = "Quarterly"

    @root_validator(pre=True)
    @classmethod
    def fix_nan(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, float) and math.isnan(v):
                    data[k] = None
        return data


# Schema for FD import preview response
class FDImportPreview(BaseModel):
    parsed_fds: List[ParsedFixedDeposit]
    duplicates: List[ParsedFixedDeposit]


# Schema for FD import commit request body
class FDImportCommit(BaseModel):
    fds_to_commit: List[ParsedFixedDeposit]
