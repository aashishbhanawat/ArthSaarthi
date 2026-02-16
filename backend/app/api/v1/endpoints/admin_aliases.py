"""
Admin endpoints for symbol alias management.
"""
import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User as UserModel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[schemas.AssetAliasWithAsset])
def list_aliases(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """List all symbol aliases with associated asset info."""
    aliases = crud.asset_alias.get_all_with_assets(db)
    result = []
    for alias in aliases:
        result.append(schemas.AssetAliasWithAsset(
            id=alias.id,
            alias_symbol=alias.alias_symbol,
            source=alias.source,
            asset_id=alias.asset_id,
            asset_name=alias.asset.name if alias.asset else "",
            asset_ticker=alias.asset.ticker_symbol if alias.asset else "",
        ))
    return result


@router.post("/", response_model=schemas.AssetAlias, status_code=201)
def create_alias(
    alias_in: schemas.AssetAliasCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """Create a new symbol alias."""
    # Check for duplicate
    existing = crud.asset_alias.get_by_alias(
        db, alias_symbol=alias_in.alias_symbol, source=alias_in.source
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Alias '{alias_in.alias_symbol}' already exists"
                f" for source '{alias_in.source}'."
            ),
        )
    # Verify asset exists
    asset = crud.asset.get(db, id=alias_in.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Target asset not found.")
    alias = crud.asset_alias.create(db, obj_in=alias_in)
    db.commit()
    db.refresh(alias)
    return alias


@router.put("/{alias_id}", response_model=schemas.AssetAlias)
def update_alias(
    alias_id: uuid.UUID,
    alias_in: schemas.AssetAliasUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """Update an existing symbol alias."""
    db_alias = crud.asset_alias.get(db, id=alias_id)
    if not db_alias:
        raise HTTPException(status_code=404, detail="Alias not found.")
    # If changing asset_id, verify it exists
    if alias_in.asset_id is not None:
        asset = crud.asset.get(db, id=alias_in.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Target asset not found.")
    updated = crud.asset_alias.update(db, db_obj=db_alias, obj_in=alias_in)
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/{alias_id}")
def delete_alias(
    alias_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
):
    """Delete a symbol alias."""
    db_alias = crud.asset_alias.get(db, id=alias_id)
    if not db_alias:
        raise HTTPException(status_code=404, detail="Alias not found.")
    crud.asset_alias.remove(db, id=alias_id)
    db.commit()
    return {"msg": "Alias deleted successfully."}
