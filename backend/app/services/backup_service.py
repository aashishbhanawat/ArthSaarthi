import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.schemas.transaction import TransactionType

logger = logging.getLogger(__name__)

BACKUP_VERSION = "1.2"


def _serialize_date(d: date | datetime | None) -> str | None:
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")
    return None


def _serialize_decimal(d: Decimal | None) -> float | None:
    if d is None:
        return None
    return float(d)


def _parse_date(d_str: str | None) -> date | None:
    if not d_str:
        return None
    return datetime.strptime(d_str, "%Y-%m-%d").date()


def create_backup(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    user = crud.user.get(db, id=user_id)
    if not user:
        raise ValueError("User not found")

    # Fetch Portfolios
    portfolios = crud.portfolio.get_multi_by_owner(db, user_id=user_id)
    portfolio_map = {p.id: p.name for p in portfolios}

    # Fetch Transactions (iterating portfolios)
    all_transactions = []
    transaction_assets = set()

    for p in portfolios:
        txs = crud.transaction.get_multi_by_portfolio(db, portfolio_id=p.id)
        for tx in txs:
            transaction_assets.add(tx.asset_id)
            t_type = tx.transaction_type
            if t_type == TransactionType.CONTRIBUTION:
                t_type = "PPF_CONTRIBUTION"

            asset = crud.asset.get(db, id=tx.asset_id)

            tx_data = {
                "portfolio_name": p.name,
                "transaction_type": t_type,
                "quantity": _serialize_decimal(tx.quantity),
                "price_per_unit": _serialize_decimal(tx.price_per_unit),
                "transaction_date": _serialize_date(tx.transaction_date),
                "fees": _serialize_decimal(tx.fees),
                "details": tx.details,
            }

            if asset:
                if asset.asset_type == "PPF":
                    tx_data["ppf_account_number"] = asset.account_number
                else:
                    tx_data["ticker_symbol"] = asset.ticker_symbol
                    tx_data["isin"] = asset.isin

            all_transactions.append(tx_data)

    # Fetch Assets for Definitions (PPF, Bonds)
    ppf_accounts = []
    bonds = []

    # Use a set to track processed assets to avoid duplicates in definitions
    processed_assets = set()

    if transaction_assets:
        for aid in transaction_assets:
            if aid in processed_assets:
                continue
            processed_assets.add(aid)

            a = crud.asset.get(db, id=aid)
            if a:
                if a.asset_type == "PPF":
                    ppf_accounts.append({
                        "account_number": a.account_number,
                        "institution": a.name,
                        "opening_date": _serialize_date(a.opening_date)
                    })
                elif a.asset_type == "BOND":
                    # Access related bond - handling both relationship styles just in
                    # case
                    b = a.bond
                    if isinstance(b, list) and b:
                        b = b[0]

                    if b:
                        bonds.append({
                            "name": a.name,
                            "isin": a.isin,
                            "bond_type": b.bond_type,
                            "coupon_rate": _serialize_decimal(b.coupon_rate),
                            "face_value": _serialize_decimal(b.face_value),
                            "maturity_date": _serialize_date(b.maturity_date)
                        })

    # Fetch FDs
    fds = (
        db.query(models.FixedDeposit)
        .filter(models.FixedDeposit.user_id == user_id)
        .all()
    )
    fd_list = []
    for fd in fds:
        p_name = portfolio_map.get(fd.portfolio_id)
        fd_list.append({
            "portfolio_name": p_name,
            "account_number": fd.account_number,
            "institution": fd.name,
            "principal": _serialize_decimal(fd.principal_amount),
            "interest_rate": _serialize_decimal(fd.interest_rate),
            "start_date": _serialize_date(fd.start_date),
            "maturity_date": _serialize_date(fd.maturity_date),
            "compounding_frequency": fd.compounding_frequency.upper()
            if fd.compounding_frequency
            else "ANNUALLY",
            "payout_type": fd.interest_payout.upper()
            if fd.interest_payout
            else "CUMULATIVE",
        })

    # Fetch RDs
    rds = (
        db.query(models.RecurringDeposit)
        .filter(models.RecurringDeposit.user_id == user_id)
        .all()
    )
    rd_list = []
    for rd in rds:
        p_name = portfolio_map.get(rd.portfolio_id)
        rd_list.append({
            "portfolio_name": p_name,
            "account_number": rd.account_number,
            "institution": rd.name,
            "monthly_installment": _serialize_decimal(rd.monthly_installment),
            "interest_rate": _serialize_decimal(rd.interest_rate),
            "start_date": _serialize_date(rd.start_date),
            "tenure_months": rd.tenure_months
        })

    # Fetch Goals
    goals = crud.goal.get_multi_by_owner(db, user_id=user_id)
    goal_list = []
    for g in goals:
        linked_names = []
        linked_assets = []
        for link in g.links:
            if link.portfolio:
                linked_names.append(link.portfolio.name)
            elif link.asset:
                linked_assets.append(link.asset.ticker_symbol)

        goal_list.append({
            "name": g.name,
            "target_amount": _serialize_decimal(g.target_amount),
            "target_date": _serialize_date(g.target_date),
            "linked_portfolios": linked_names,
            "linked_assets": linked_assets
        })

    # Fetch Watchlists
    watchlists = crud.watchlist.get_multi_by_user(db, user_id=user_id)
    watchlist_list = []
    for w in watchlists:
        items = [wi.asset.ticker_symbol for wi in w.items if wi.asset]
        watchlist_list.append({
            "name": w.name,
            "items": items
        })

    # Portfolios list
    portfolio_list = [
        {"name": p.name, "description": p.description} for p in portfolios
    ]

    data = {
        "portfolios": portfolio_list,
        "transactions": all_transactions,
        "fixed_deposits": fd_list,
        "recurring_deposits": rd_list,
        "ppf_accounts": ppf_accounts,
        "bonds": bonds,
        "goals": goal_list,
        "watchlists": watchlist_list,
    }

    return {
        "metadata": {
            "version": BACKUP_VERSION,
            "export_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "data": data,
    }


def restore_backup(db: Session, user_id: uuid.UUID, backup_data: Dict[str, Any]):
    metadata = backup_data.get("metadata", {})
    # Basic version check (allow major version match 1.x)
    version = metadata.get("version", "0.0")
    if not version.startswith("1."):
        raise HTTPException(
            status_code=400, detail=f"Unsupported backup version: {version}"
        )

    data = backup_data.get("data", {})

    try:
        with db.begin_nested():
            # 1. Delete Phase
            # Delete Watchlists
            watchlists = crud.watchlist.get_multi_by_user(db, user_id=user_id)
            for w in watchlists:
                db.delete(w)

            # Delete Goals
            goals = crud.goal.get_multi_by_owner(db, user_id=user_id)
            for g in goals:
                db.delete(g)

            # Delete FDs
            db.query(models.FixedDeposit).filter(
                models.FixedDeposit.user_id == user_id
            ).delete()

            # Delete RDs
            db.query(models.RecurringDeposit).filter(
                models.RecurringDeposit.user_id == user_id
            ).delete()

            # Delete Portfolios (Cascades transactions)
            portfolios = crud.portfolio.get_multi_by_owner(db, user_id=user_id)
            for p in portfolios:
                db.delete(p)

            db.flush() # Ensure deletions are applied before recreation

            # 2. Restore Phase

            # Create Portfolios
            portfolio_map = {} # name -> id
            for p_data in data.get("portfolios", []):
                p_in = schemas.PortfolioCreate(
                    name=p_data["name"],
                    description=p_data.get("description")
                )
                p = crud.portfolio.create_with_owner(db, obj_in=p_in, user_id=user_id)
                portfolio_map[p.name] = p.id

            # Create Watchlists
            watchlist_map = {} # name -> id
            for w_data in data.get("watchlists", []):
                w_in = schemas.WatchlistCreate(name=w_data["name"])
                w = crud.watchlist.create_with_user(db, obj_in=w_in, user_id=user_id)
                watchlist_map[w.name] = w.id

                for ticker in w_data.get("items", []):
                    asset = crud.asset.get_or_create_by_ticker(db, ticker_symbol=ticker)
                    if asset:
                        crud.watchlist_item.create_with_watchlist_and_user(
                            db,
                            obj_in=schemas.WatchlistItemCreate(asset_id=asset.id),
                            watchlist_id=w.id,
                            user_id=user_id
                        )

            # Independent Assets: PPF
            for ppf_data in data.get("ppf_accounts", []):
                ticker = f"PPF-{ppf_data['account_number']}"
                asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
                if not asset:
                    # Create Asset
                    asset_in = schemas.AssetCreate(
                        name=ppf_data["institution"],
                        ticker_symbol=ticker,
                        asset_type="PPF",
                        currency="INR",
                        account_number=ppf_data["account_number"],
                        opening_date=_parse_date(ppf_data.get("opening_date"))
                    )
                    crud.asset.create(db, obj_in=asset_in)

            # Independent Assets: Bonds
            for bond_data in data.get("bonds", []):
                isin = bond_data.get("isin")
                if not isin:
                    continue
                # Check if asset exists by ISIN or Ticker? ISIN is unique
                # Models don't always have ISIN unique constraint enforced in get_by,
                # but Asset model has unique index on ISIN.
                asset = db.query(models.Asset).filter(models.Asset.isin == isin).first()
                if not asset:
                    # Create Asset
                    asset_in = schemas.AssetCreate(
                        name=bond_data["name"],
                        ticker_symbol=isin,  # Bonds use ISIN as ticker
                        # Requirement doesn't specify ticker for bonds in backup.
                        # We can assume ticker=isin or check if backup provides ticker?
                        asset_type="BOND",
                        currency="INR",
                        isin=isin
                    )
                    # Need unique ticker. If Bond definition doesn't have ticker, use
                    # ISIN.
                    asset = crud.asset.create(db, obj_in=asset_in)

                    # Create Bond details
                    bond_in = schemas.BondCreate(
                        asset_id=asset.id,
                        bond_type=bond_data["bond_type"],
                        face_value=Decimal(bond_data["face_value"]),
                        coupon_rate=Decimal(bond_data["coupon_rate"]),
                        maturity_date=_parse_date(bond_data["maturity_date"]),
                        isin=isin
                    )
                    crud.bond.create(db, obj_in=bond_in)

            # FDs
            for fd_data in data.get("fixed_deposits", []):
                p_name = fd_data.get("portfolio_name")
                if p_name and p_name in portfolio_map:
                    fd_in = schemas.FixedDepositCreate(
                        name=fd_data["institution"],
                        account_number=fd_data["account_number"],
                        principal_amount=Decimal(fd_data["principal"]),
                        interest_rate=Decimal(fd_data["interest_rate"]),
                        start_date=_parse_date(fd_data["start_date"]),
                        maturity_date=_parse_date(fd_data["maturity_date"]),
                        compounding_frequency=fd_data.get("compounding_frequency"),
                        interest_payout=fd_data.get("payout_type"),
                        portfolio_id=portfolio_map[p_name]
                    )
                    crud.fixed_deposit.create_with_owner(
                        db, obj_in=fd_in, owner_id=user_id
                    )

            # RDs
            for rd_data in data.get("recurring_deposits", []):
                p_name = rd_data.get("portfolio_name")
                if p_name and p_name in portfolio_map:
                    rd_in = schemas.RecurringDepositCreate(
                        name=rd_data["institution"],
                        account_number=rd_data["account_number"],
                        monthly_installment=Decimal(rd_data["monthly_installment"]),
                        interest_rate=Decimal(rd_data["interest_rate"]),
                        start_date=_parse_date(rd_data["start_date"]),
                        tenure_months=rd_data.get("tenure_months", 12),
                        portfolio_id=portfolio_map[p_name]
                    )
                    crud.recurring_deposit.create_with_owner(
                        db, obj_in=rd_in, owner_id=user_id
                    )

            # Transactions
            for tx_data in data.get("transactions", []):
                p_name = tx_data.get("portfolio_name")
                if not p_name or p_name not in portfolio_map:
                    continue

                p_id = portfolio_map[p_name]
                t_type = tx_data["transaction_type"]
                if t_type == "PPF_CONTRIBUTION":
                    t_type = TransactionType.CONTRIBUTION

                # Skip sell-to-cover SELL transactions - they are auto-created
                # when restoring the parent RSU_VEST transaction
                details = tx_data.get("details")
                if t_type == "SELL" and details and details.get("related_rsu_vest_id"):
                    logger.debug(f"Skipping sell-to-cover SELL: {tx_data}")
                    continue

                # Find Asset
                asset = None
                if "ppf_account_number" in tx_data:
                    ticker = f"PPF-{tx_data['ppf_account_number']}"
                    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
                elif "isin" in tx_data and tx_data["isin"]:
                    asset = (
                        db.query(models.Asset)
                        .filter(models.Asset.isin == tx_data["isin"])
                        .first()
                    )
                    if not asset and "ticker_symbol" in tx_data:
                        asset = crud.asset.get_or_create_by_ticker(
                            db, ticker_symbol=tx_data["ticker_symbol"]
                        )
                elif "ticker_symbol" in tx_data:
                    asset = crud.asset.get_or_create_by_ticker(
                        db, ticker_symbol=tx_data["ticker_symbol"]
                    )

                if not asset:
                    # Log warning but skip? Or fail?
                    # We should try best effort.
                    logger.warning(f"Could not find asset for transaction: {tx_data}")
                    continue

                # Create Transaction
                tx_in = schemas.TransactionCreate(
                    asset_id=asset.id,
                    transaction_type=t_type,
                    quantity=Decimal(tx_data["quantity"]),
                    price_per_unit=Decimal(tx_data["price_per_unit"]),
                    transaction_date=_parse_date(tx_data["transaction_date"]),
                    fees=Decimal(tx_data.get("fees", 0)),
                    details=tx_data.get("details"),
                )
                crud.transaction.create_with_portfolio(
                    db, obj_in=tx_in, portfolio_id=p_id
                )

            # Goals
            for g_data in data.get("goals", []):
                g_in = schemas.GoalCreate(
                    name=g_data["name"],
                    target_amount=Decimal(g_data["target_amount"]),
                    target_date=_parse_date(g_data["target_date"])
                )
                goal = crud.goal.create_with_owner(db, obj_in=g_in, user_id=user_id)

                # Links
                for p_name in g_data.get("linked_portfolios", []):
                    if p_name in portfolio_map:
                        crud.goal_link.create_with_owner(
                            db,
                            obj_in=schemas.GoalLinkCreate(
                                goal_id=goal.id, portfolio_id=portfolio_map[p_name]
                            ),
                            user_id=user_id,
                        )

                # Asset Links
                for ticker in g_data.get("linked_assets", []):
                    asset = crud.asset.get_by_ticker(db, ticker_symbol=ticker)
                    if asset:
                        crud.goal_link.create_with_owner(
                            db,
                            obj_in=schemas.GoalLinkCreate(
                                goal_id=goal.id, asset_id=asset.id
                            ),
                            user_id=user_id,
                        )

        db.commit()

        # Invalidate dashboard summary cache
        from app.cache.factory import get_cache_client
        cache = get_cache_client()
        dashboard_key = f"analytics:dashboard_summary:{user_id}"
        cache.delete(dashboard_key)
        logger.info(f"Invalidated dashboard cache for user {user_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Restore failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
