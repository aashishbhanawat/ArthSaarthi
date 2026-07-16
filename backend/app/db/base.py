# This file is used to ensure all SQLAlchemy models are imported before
# initializing the database, so that they are registered properly on the metadata.

from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.portfolio import Portfolio  # noqa
from app.models.asset import Asset  # noqa
from app.models.transaction import Transaction  # noqa
from app.models.transaction_link import TransactionLink  # noqa
from app.models.import_session import ImportSession  # noqa
from app.models.parsed_transaction import ParsedTransaction  # noqa
from app.models.asset_alias import AssetAlias  # noqa
from app.models.goal import Goal, GoalLink  # noqa
from app.models.historical_interest_rate import HistoricalInterestRate  # noqa
from app.models.fixed_deposit import FixedDeposit  # noqa
from app.models.recurring_deposit import RecurringDeposit  # noqa
from app.models.watchlist import Watchlist, WatchlistItem  # noqa
from app.models.bond import Bond  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.risk import UserRiskProfile  # noqa
from app.models.portfolio_snapshot import DailyPortfolioSnapshot  # noqa


