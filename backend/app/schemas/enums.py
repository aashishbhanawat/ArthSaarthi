from enum import Enum


class BondType(str, Enum):
    CORPORATE = "CORPORATE"
    GOVERNMENT = "GOVERNMENT"
    SGB = "SGB"
    TBILL = "TBILL"


class PaymentFrequency(str, Enum):
    ANNUALLY = "ANNUALLY"
    SEMI_ANNUALLY = "SEMI_ANNUALLY"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    BONUS = "BONUS"
    CONTRIBUTION = "CONTRIBUTION"
    INTEREST_CREDIT = "INTEREST_CREDIT"
    COUPON = "COUPON"
