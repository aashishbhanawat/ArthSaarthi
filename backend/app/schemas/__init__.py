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
from .bond import (
    Bond,
    BondCreate,
    BondUpdate,
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
    AssetInGoalLink,
    Goal,
    GoalCreate,
    GoalLink,
    GoalLinkCreate,
    GoalLinkUpdate,
    GoalUpdate,
    GoalWithAnalytics,
    PortfolioInGoalLink,
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
    "WatchlistUpdate",
]

# Manually update forward references to resolve circular dependencies
import pydantic

is_v2 = pydantic.__version__.startswith("2.")

if is_v2:
    # In Pydantic v2, we should use model_rebuild.
    # We pass the types namespace to help it find the classes.
    Asset.model_rebuild()
    Transaction.model_rebuild(_types_namespace={"Asset": Asset})
    WatchlistItem.model_rebuild(_types_namespace={"Asset": Asset})
    ImportSession.model_rebuild(_types_namespace={"Portfolio": Portfolio, "User": User})
    Goal.model_rebuild(_types_namespace={"GoalLink": GoalLink})
    GoalLink.model_rebuild(_types_namespace={
        "AssetInGoalLink": AssetInGoalLink,
        "PortfolioInGoalLink": PortfolioInGoalLink
    })
else:
    # Pydantic v1 (Android)
    Asset.update_forward_refs()
    Transaction.update_forward_refs(Asset=Asset)
    WatchlistItem.update_forward_refs(Asset=Asset)
    ImportSession.update_forward_refs(Portfolio=Portfolio, User=User)
    Goal.update_forward_refs(GoalLink=GoalLink)
    GoalLink.update_forward_refs(
        AssetInGoalLink=AssetInGoalLink,
        PortfolioInGoalLink=PortfolioInGoalLink
    )
