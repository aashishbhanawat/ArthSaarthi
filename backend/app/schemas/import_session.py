import math
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator

try:
    from pydantic import ConfigDict
except ImportError:
    ConfigDict = None

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

    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            from_orm = True


# Properties to return to client
class ImportSession(ImportSessionInDBBase):
    portfolio: Portfolio
    user: User


# Schema for the parsed transaction data from the file
class ParsedTransaction(BaseModel):
    transaction_date: datetime
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


class ParsedFixedDeposit(BaseModel):
    bank: str
    account_number: Optional[str] = None
    principal_amount: float
    interest_rate: float
    start_date: str
    maturity_date: str
    maturity_amount: Optional[float] = None
    interest_payout: str = "Cumulative"
    compounding_frequency: str = "Quarterly"

    @validator("*", pre=True, each_item=False)
    @classmethod
    def fix_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v


# Schema for FD import preview response
class FDImportPreview(BaseModel):
    parsed_fds: List[ParsedFixedDeposit]
    duplicates: List[ParsedFixedDeposit]


# Schema for FD import commit request body
class FDImportCommit(BaseModel):
    fds_to_commit: List[ParsedFixedDeposit]
