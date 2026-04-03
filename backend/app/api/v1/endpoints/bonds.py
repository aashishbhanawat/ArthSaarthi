import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models
from app.cache import utils as cache_utils
from app.core import dependencies
from app.schemas.bond import Bond, BondCreate, BondUpdate, BondWithTransactionCreate
from app.schemas.msg import Msg
from app.utils.pydantic_compat import model_dump

router = APIRouter()

def _check_bond_ownership(db: Session, bond: models.Bond, user_id: uuid.UUID) -> None:
    if not bond.asset.transactions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    for transaction in bond.asset.transactions:
        portfolio = crud.portfolio.get(db=db, id=transaction.portfolio_id)
        if portfolio and portfolio.user_id == user_id:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
    )



@router.post("/", response_model=Bond, status_code=status.HTTP_201_CREATED)
def create_bond(
    *,
    db: Session = Depends(dependencies.get_db),
    portfolio_id: uuid.UUID,
    bond_and_tx_in: BondWithTransactionCreate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Create new bond details for an existing asset.
    """
    portfolio = crud.portfolio.get(db=db, id=portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    asset = crud.asset.get(db, id=bond_and_tx_in.transaction_data.asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=(
                f"Asset with ID {bond_and_tx_in.transaction_data.asset_id} not found.")
        )

    # Check if the asset is actually a bond
    if asset.asset_type.upper() != "BOND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(f"Asset with ID {bond_and_tx_in.transaction_data.asset_id} "
                    "is not a BOND type asset.")
         )

    # Check if bond details already exist for this asset
    existing_bond = crud.bond.get_by_asset_id(
        db=db, asset_id=bond_and_tx_in.transaction_data.asset_id
    )

    bond_in = BondCreate(
        **model_dump(bond_and_tx_in.bond_data),
        asset_id=asset.id
    )

    if existing_bond:
        # If bond details already exist (e.g., from seeder), update them
        new_bond = crud.bond.update(db=db, db_obj=existing_bond, obj_in=bond_in)
    else:
        # Otherwise, create new bond details
        new_bond = crud.bond.create(db=db, obj_in=bond_in)

    crud.transaction.create_with_portfolio(
        db=db, obj_in=bond_and_tx_in.transaction_data, portfolio_id=portfolio_id
    )
    db.commit()
    db.refresh(new_bond)

    # Invalidate caches
    cache_utils.invalidate_caches_for_portfolio(db=db, portfolio_id=portfolio_id)

    return new_bond


@router.put("/by-asset/{asset_id}", response_model=Bond)
def update_bond_by_asset_id(
    *,
    db: Session = Depends(dependencies.get_db),
    asset_id: uuid.UUID,
    bond_in: BondUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update a bond using its asset_id.
    """
    bond = crud.bond.get_by_asset_id(db=db, asset_id=asset_id)
    if not bond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bond details for this asset not found",
        )
    _check_bond_ownership(db, bond, current_user.id)
    bond = crud.bond.update(db=db, db_obj=bond, obj_in=bond_in)
    db.commit()
    db.refresh(bond)
    return bond


@router.get("/{bond_id}", response_model=Bond)
def read_bond(
    *,
    db: Session = Depends(dependencies.get_db),
    bond_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Get bond by ID.
    """
    bond = crud.bond.get(db=db, id=bond_id)
    if not bond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bond not found")
    _check_bond_ownership(db, bond, current_user.id)
    return bond


@router.put("/{bond_id}", response_model=Bond)
def update_bond(
    *,
    db: Session = Depends(dependencies.get_db),
    bond_id: uuid.UUID,
    bond_in: BondUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Update a bond.
    """
    bond = crud.bond.get(db=db, id=bond_id)
    if not bond:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Bond not found")
    _check_bond_ownership(db, bond, current_user.id)
    bond = crud.bond.update(db=db, db_obj=bond, obj_in=bond_in)
    db.commit()
    db.refresh(bond)
    return bond


@router.delete("/{bond_id}", response_model=Msg)
def delete_bond(
    *,
    db: Session = Depends(dependencies.get_db),
    bond_id: uuid.UUID,
    current_user: models.User = Depends(dependencies.get_current_user),
) -> Any:
    """
    Delete a bond.
    """
    bond = crud.bond.get(db=db, id=bond_id)
    if not bond:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Bond not found")
    _check_bond_ownership(db, bond, current_user.id)
    crud.bond.remove(db=db, id=bond_id)
    db.commit()
    return {"msg": "Bond deleted successfully"}
