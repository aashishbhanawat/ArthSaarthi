from enum import Enum


class AssetType(str, Enum):
    STOCK = "STOCK"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    PPF = "PPF"


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    CONTRIBUTION = "CONTRIBUTION"
    INTEREST_CREDIT = "INTEREST_CREDIT"
