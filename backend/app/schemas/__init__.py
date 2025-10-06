from .analytics import AssetAnalytics, FixedDepositAnalytics, PortfolioAnalytics
from .asset import (
    Asset,
    AssetCreate,  # noqa: F401
    AssetCreateIn,
    AssetSearchResult,
    AssetType,
    AssetUpdate,
    PpfAccountCreate,
)
from .asset_alias import AssetAlias, AssetAliasCreate
from .bond import (
    BondWithTransactionCreate,
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
from .holding import Holding, HoldingsResponse, PortfolioSummary
from .import_session import (
    ImportSession,
    ImportSessionCommit,
    ImportSessionCreate,
    ImportSessionPreview,
    ImportSessionUpdate,
    ParsedTransaction,
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
from .token import Token, TokenPayload
from .transaction import (
    Transaction,
    TransactionCreate,
    TransactionCreateIn,
    TransactionsResponse,
    TransactionType,
    TransactionUpdate,
)
from .user import User, UserCreate, UserPasswordChange, UserUpdate, UserUpdateMe

__all__ = [
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
    "AssetAllocation",
    "AssetAllocationResponse",
    "AssetCreate",
    "AssetCreateIn",
    "AssetSearchResult",
    "AssetUpdate",
    "AssetAnalytics",
    "FixedDepositAnalytics",
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
    "TransactionCreateIn",
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
    "BondWithTransactionCreate",
    "HistoricalInterestRate",
    "HistoricalInterestRateCreate",
    "HistoricalInterestRateUpdate",
    "PpfAccountCreate",
]

# Manually update forward references to resolve circular dependencies
Asset.model_rebuild()

Transaction.model_rebuild()
