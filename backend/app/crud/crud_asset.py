import uuid
from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app import crud, models, schemas
from app.crud.base import CRUDBase
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services.financial_data_service import financial_data_service


class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    def get_or_create_by_ticker(
        self,
        db: Session,
        *,
        ticker_symbol: str,
        asset_type: Optional[str] = None,
    ) -> Optional[Asset]:
        """
        Gets an asset by ticker symbol. If it doesn't exist, it fetches details
        from an external service and creates it.
        """
        ticker_symbol = ticker_symbol.upper()
        db_asset = self.get_by_ticker(db, ticker_symbol=ticker_symbol)
        if db_asset:
            return db_asset

        # Asset not found locally, fetch details from the financial data service
        details = financial_data_service.get_asset_details(
            ticker_symbol, asset_type=asset_type
        )
        if not details:
            return None  # Could not find asset details externally

        # Create the new asset
        new_asset_data = AssetCreate(ticker_symbol=ticker_symbol, **details)
        return self.create(db=db, obj_in=new_asset_data)

    def get_all_by_type_and_portfolio(
        self, db: Session, *, asset_type: str, portfolio_id: uuid.UUID
    ) -> List[Asset]:
        """
        Retrieves all assets of a specific type that have at least one
        transaction in the specified portfolio.
        """
        return (
            db.query(self.model)
            .join(models.Transaction)
            .filter(
                models.Transaction.portfolio_id == portfolio_id,
                self.model.asset_type == asset_type,
            )
            .distinct()
            .all()
        )

    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID, asset_type: Optional[str] = None
    ) -> List[Asset]:
        """
        Retrieves all assets that have at least one transaction in the
        specified portfolio.
         """
        # Get distinct asset_ids from transactions for the given portfolio
        query = (
            db.query(models.Transaction.asset_id)
            .filter(models.Transaction.portfolio_id == portfolio_id)
            .distinct()
        )

        # Join with Asset to filter by asset_type if provided
        if asset_type:
            query = query.join(self.model, self.model.id == models.Transaction.asset_id)
            query = query.filter(self.model.asset_type == asset_type)

        asset_ids = [item[0] for item in query.all()]

        if not asset_ids:
            return []

        # Fetch the Asset objects corresponding to these IDs
        return db.query(self.model).filter(self.model.id.in_(asset_ids)).all()

    def create_ppf_and_first_contribution(
        self, db: Session, *, portfolio_id: uuid.UUID, ppf_in: schemas.PpfAccountCreate
    ) -> models.Transaction:
        """
        Creates a PPF Asset and its initial contribution transaction.
        """
        # 1. Create the Asset
        asset_in = schemas.AssetCreate(
            name=ppf_in.institution_name,
            ticker_symbol=f"PPF-{ppf_in.account_number or uuid.uuid4().hex[:8]}",
            asset_type="PPF",
            currency="INR",
            account_number=ppf_in.account_number,
            opening_date=ppf_in.opening_date,
        )
        new_asset = self.create(db=db, obj_in=asset_in)

        # 2. Create the first contribution transaction
        transaction_in = schemas.TransactionCreate(
            asset_id=new_asset.id,
            transaction_type="CONTRIBUTION",
            quantity=ppf_in.amount,
            price_per_unit=1,
            transaction_date=ppf_in.contribution_date,
            fees=0,
        )
        new_transaction = crud.transaction.create_with_portfolio(
            db=db, obj_in=transaction_in, portfolio_id=portfolio_id
        )
        return new_transaction

    def get_by_ticker(self, db: Session, *, ticker_symbol: str) -> Asset | None:
        return (
            db.query(self.model)
            .filter(self.model.ticker_symbol == ticker_symbol)
               .first()
        )

    def search_by_name_or_ticker(
        self, db: Session, *, query: str, asset_type: Optional[str] = None
    ) -> List[Asset]:
        # Use ILIKE for case-insensitive search on PostgreSQL, and it works
        # correctly on SQLite as well, providing a consistent behavior.
        search_term = f"%{query}%"
        db_query = db.query(self.model).filter(
            or_(
                self.model.name.ilike(search_term),
                self.model.ticker_symbol.ilike(search_term),
            )
        )
        if asset_type:
            # Use case-insensitive comparison for asset_type
            db_query = db_query.filter(
                func.upper(self.model.asset_type) == asset_type.upper()
            )

        # Eager load bond details if asset_type is BOND
        if asset_type == "BOND":
            db_query = db_query.options(joinedload(self.model.bond))
        return db_query.limit(10).all()


asset = CRUDAsset(Asset)
