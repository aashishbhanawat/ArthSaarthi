from .analytics import (
    AssetAnalytics,
    DiversificationResponse,
    DiversificationSegment,
    FixedDepositAnalytics,
    PortfolioAnalytics,
)
from .asset import (
    Asset,
    AssetCreate,  # noqa: F401
    AssetCreateIn,
    AssetSearchResult,
    AssetType,
    AssetUpdate,
    PpfAccountCreate,
)
from .asset_alias import (
    AssetAlias,
    AssetAliasCreate,
    AssetAliasUpdate,
    AssetAliasWithAsset,
)
from .audit_log import AuditLog, AuditLogCreate
from .bond import (
    Bond,
    BondCreate,
    BondUpdate,
    BondWithTransactionCreate,
)
from .capital_gains import (
    CapitalGainsSummary,
    UnrealizedGainsSummary,
    UnrealizedTaxLot,
)
from .dashboard import (
    AssetAllocation,
    AssetAllocationResponse,
    DashboardSummary,
    PortfolioHistoryPoint,
    PortfolioHistoryResponse,
    TopMover,
)
from .fixed_deposit import (
    FixedDeposit,
    FixedDepositCreate,
    FixedDepositDetails,
    FixedDepositUpdate,
)
from .goal import (
    Goal,
    GoalCreate,
    GoalLink,
    GoalLinkCreate,
    GoalLinkUpdate,
    GoalUpdate,
    GoalWithAnalytics,
)
from .historical_interest_rate import (
    HistoricalInterestRate,
    HistoricalInterestRateCreate,
    HistoricalInterestRateUpdate,
)
from .holding import (
    Holding,
    HoldingsResponse,
    PortfolioHoldingsAndSummary,
    PortfolioSummary,
)
from .import_session import (
    FDImportCommit,
    FDImportPreview,
    ImportSession,
    ImportSessionCommit,
    ImportSessionCreate,
    ImportSessionPreview,
    ImportSessionUpdate,
    ParsedFixedDeposit,
    ParsedTransaction,
)
from .income import (
    IncomeEntry,
    IncomeEntryCreate,
    IncomeEntryUpdate,
    IncomeFYSummary,
    IncomeSource,
    IncomeSourceCreate,
    IncomeSourceUpdate,
)
from .msg import Msg
from .portfolio import Portfolio, PortfolioCreate, PortfolioUpdate
from .recurring_deposit import (
    RecurringDeposit,
    RecurringDepositAnalytics,
    RecurringDepositCreate,
    RecurringDepositDetails,
    RecurringDepositUpdate,
)
from .risk import (
    UserRiskProfile,
    UserRiskProfileCreate,
    UserRiskProfileUpdate,
)
from .tax_deduction import (
    SectionLimitSummary,
    TaxDeductionBase,
    TaxDeductionCreate,
    TaxDeductionFYSummary,
    TaxDeductionResponse,
    TaxDeductionUpdate,
)
from .token import Token, TokenPayload
from .transaction import (
    Transaction,
    TransactionCreate,
    TransactionCreatedResponse,
    TransactionCreateIn,
    TransactionLinkCreate,
    TransactionsResponse,
    TransactionType,
    TransactionUpdate,
)
from .user import User, UserCreate, UserPasswordChange, UserUpdate, UserUpdateMe
from .watchlist import (
    Watchlist,
    WatchlistCreate,
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistUpdate,
)

__all__ = [
    "SectionLimitSummary",
    "TaxDeductionBase",
    "TaxDeductionCreate",
    "TaxDeductionFYSummary",
    "TaxDeductionResponse",
    "TaxDeductionUpdate",
    "AuditLog",
    "AuditLogCreate",
    "RecurringDeposit",
    "RecurringDepositAnalytics",
    "RecurringDepositCreate",
    "RecurringDepositDetails",
    "RecurringDepositUpdate",

    "TransactionType",
    "AssetType",
    "Asset",
    "AssetAlias",
    "FixedDeposit",
    "FixedDepositCreate",
    "FixedDepositDetails",
    "FixedDepositUpdate",
    "AssetAliasCreate",
    "AssetAliasUpdate",
    "AssetAliasWithAsset",
    "AssetAllocation",
    "AssetAllocationResponse",
    "AssetCreate",
    "AssetCreateIn",
    "AssetSearchResult",
    "AssetUpdate",
    "AssetAnalytics",
    "CapitalGainsSummary",

    "DiversificationResponse",
    "DiversificationSegment",
    "FixedDepositAnalytics",
    "PortfolioHoldingsAndSummary",
    "DashboardSummary",
    "Holding",
    "HoldingsResponse",
    "ImportSession",
    "ImportSessionCommit",
    "ImportSessionCreate",
    "ImportSessionPreview",
    "ImportSessionUpdate",
    "Msg",
    "ParsedTransaction",
    "ParsedFixedDeposit",
    "FDImportPreview",
    "FDImportCommit",
    "Portfolio",
    "PortfolioCreate",
    "PortfolioHistoryPoint",
    "PortfolioAnalytics",
    "PortfolioHistoryResponse",
    "PortfolioSummary",
    "PortfolioUpdate",
    "TopMover",
    "Token",
    "TokenPayload",
    "Transaction",
    "TransactionCreate",
    "TransactionCreatedResponse",
    "TransactionCreateIn",
    "TransactionLinkCreate",
    "TransactionUpdate",
    "TransactionsResponse",
    "User",
    "UserCreate",
    "UserPasswordChange",
    "UserUpdate",
    "UserUpdateMe",
    "Goal",
    "GoalCreate",
    "GoalUpdate",
    "GoalLink",
    "GoalLinkCreate",
    "GoalLinkUpdate",
    "GoalWithAnalytics",
    "Bond",
    "BondCreate",
    "BondUpdate",
    "BondWithTransactionCreate",
    "HistoricalInterestRate",
    "HistoricalInterestRateCreate",
    "HistoricalInterestRateUpdate",
    "PpfAccountCreate",
    "Watchlist",
    "WatchlistCreate",
    "WatchlistItem",
    "WatchlistItemCreate",
    "CapitalGainsSummary",
    "UnrealizedGainsSummary",
    "UnrealizedTaxLot",
    "WatchlistUpdate",
    "UserRiskProfile",
    "UserRiskProfileCreate",
    "UserRiskProfileUpdate",
    "IncomeSource",
    "IncomeSourceCreate",
    "IncomeSourceUpdate",
    "IncomeEntry",
    "IncomeEntryCreate",
    "IncomeEntryUpdate",
    "IncomeFYSummary",
]

# Manually update forward references to resolve circular dependencies
if hasattr(Asset, "model_rebuild"):
    Asset.model_rebuild()
    Transaction.model_rebuild()
else:
    Asset.update_forward_refs()
    Transaction.update_forward_refs(Asset=Asset)

