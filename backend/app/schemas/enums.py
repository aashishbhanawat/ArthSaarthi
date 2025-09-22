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

