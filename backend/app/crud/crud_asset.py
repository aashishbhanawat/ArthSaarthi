import uuid
from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

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

    def get_multi_by_portfolio(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> List[Asset]:
        """
        Retrieves all assets that have at least one transaction in the
        specified portfolio.
         """
        # Get distinct asset_ids from transactions for the given portfolio
        asset_ids_query = (
            db.query(models.Transaction.asset_id)
            .filter(models.Transaction.portfolio_id == portfolio_id)
            .distinct()
        )
        asset_ids = [item[0] for item in asset_ids_query.all()]

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
            quantity=1,  # For PPF, quantity is 1, price is the amount
            price_per_unit=ppf_in.amount,
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

    def get_by_isin(self, db: Session, *, isin: str) -> Asset | None:
        return db.query(self.model).filter(self.model.isin == isin).first()

    def search_by_name_or_ticker(self, db: Session, *, query: str) -> List[Asset]:
        # Use wildcards and ensure lowercase for case-insensitive search.
        search = f"%{query.lower()}%"
        return (
            db.query(self.model)
            .filter(
                or_(
                    func.lower(self.model.name).like(search),
                    func.lower(self.model.ticker_symbol).like(search),
                )
            )
            .limit(10)
            .all()
        )


asset = CRUDAsset(Asset)
