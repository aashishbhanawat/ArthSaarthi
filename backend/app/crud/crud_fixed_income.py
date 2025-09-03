import uuid

from sqlalchemy.orm import Session

from app import models, schemas
from app.crud.base import CRUDBase


class CRUDFixedIncome(CRUDBase[models.Asset, schemas.AssetCreate, schemas.AssetUpdate]):
    def create_fixed_deposit(
        self,
        db: Session,
        *,
        portfolio_id: uuid.UUID,
        fixed_deposit_in: schemas.FixedDepositCreate,
    ) -> models.Asset:
        # Create a unique ticker symbol for internal tracking
        ticker_symbol = f"FD_{uuid.uuid4().hex[:8].upper()}"

        # Create the base asset
        asset_data = schemas.AssetCreate(
            ticker_symbol=ticker_symbol,
            name=f"{fixed_deposit_in.institution_name} FD",
            asset_type="FIXED_DEPOSIT",
            currency="INR",
            portfolio_id=portfolio_id,
        )
        db_asset = self.create(db=db, obj_in=asset_data)

        # Create the fixed deposit details
        fd_data = fixed_deposit_in.model_dump()
        db_fd = models.FixedDeposit(**fd_data, asset_id=db_asset.id)
        db.add(db_fd)
        db.commit()
        db.refresh(db_fd)

        return db_asset

    def create_bond(
        self, db: Session, *, portfolio_id: uuid.UUID, bond_in: schemas.BondCreate
    ) -> models.Asset:
        # Create a unique ticker symbol for internal tracking
        ticker_symbol = f"BOND_{uuid.uuid4().hex[:8].upper()}"

        # Create the base asset
        asset_data = schemas.AssetCreate(
            ticker_symbol=ticker_symbol,
            name=bond_in.bond_name,
            asset_type="BOND",
            currency="INR",
            portfolio_id=portfolio_id,
        )
        db_asset = self.create(db=db, obj_in=asset_data)

        # Create the bond details
        bond_data = bond_in.model_dump()
        db_bond = models.Bond(**bond_data, asset_id=db_asset.id)
        db.add(db_bond)
        db.commit()
        db.refresh(db_bond)

        return db_asset

    def create_ppf(
        self,
        db: Session,
        *,
        portfolio_id: uuid.UUID,
        ppf_in: schemas.PublicProvidentFundCreate,
    ) -> models.Asset:
        # Create a unique ticker symbol for internal tracking
        ticker_symbol = f"PPF_{uuid.uuid4().hex[:8].upper()}"

        # Create the base asset
        asset_data = schemas.AssetCreate(
            ticker_symbol=ticker_symbol,
            name=f"PPF Account ({ppf_in.account_number})",
            asset_type="PPF",
            currency="INR",
            portfolio_id=portfolio_id,
        )
        db_asset = self.create(db=db, obj_in=asset_data)

        # Create the PPF details
        ppf_data = ppf_in.model_dump()
        db_ppf = models.PublicProvidentFund(**ppf_data, asset_id=db_asset.id)
        db.add(db_ppf)
        db.commit()
        db.refresh(db_ppf)

        return db_asset


fixed_income = CRUDFixedIncome(models.Asset)
