import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models
from app.core import dependencies
from app.schemas.bond import Bond, BondCreate, BondUpdate, BondWithTransactionCreate
from app.schemas.msg import Msg

router = APIRouter()


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
        asset_id=bond_and_tx_in.transaction_data.asset_id,
        **bond_and_tx_in.bond_data.model_dump(),
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
    # Add ownership check if necessary in the future
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
    # Add ownership check if necessary
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
     # Add ownership check if necessary
    crud.bond.remove(db=db, id=bond_id)
    db.commit()
    return {"msg": "Bond deleted successfully"}
