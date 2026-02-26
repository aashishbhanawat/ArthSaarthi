# This file is used to ensure all SQLAlchemy models are imported before
# initializing the database, so that they are registered properly on the metadata.

from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.portfolio import Portfolio  # noqa
from app.models.asset import Asset  # noqa
from app.models.transaction import Transaction  # noqa
from app.models.watchlist import Watchlist, WatchlistItem  # noqa
from app.models.portfolio_snapshot import DailyPortfolioSnapshot  # noqa
