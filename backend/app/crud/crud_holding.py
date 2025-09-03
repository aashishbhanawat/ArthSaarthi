import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.services.financial_data_service import financial_data_service


class CRUDHolding:
    """
    CRUD operations for portfolio holdings.
    This is a read-only CRUD module that calculates holdings.
    """

    def get_portfolio_holdings_and_summary(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Calculates the consolidated holdings and a summary for a given portfolio.
        """
        all_assets = crud.asset.get_all_by_portfolio(db=db, portfolio_id=portfolio_id)
        transactions = crud.transaction.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )

        if not all_assets:
            return {
                "summary": schemas.PortfolioSummary(
                    total_value=Decimal(0),
                    total_invested_amount=Decimal(0),
                    days_pnl=Decimal(0),
                    total_unrealized_pnl=Decimal(0),
                    total_realized_pnl=Decimal(0),
                ),
                "holdings": [],
            }

        transaction_based_assets = [
            asset
            for asset in all_assets
            if asset.asset_type not in ["FIXED_DEPOSIT", "BOND", "PPF"]
        ]
        fixed_income_assets = [
            asset
            for asset in all_assets
            if asset.asset_type in ["FIXED_DEPOSIT", "BOND", "PPF"]
        ]

        # Process transaction-based assets
        transaction_holdings, transaction_summary_data = (
            self._process_transaction_based_assets(
                transactions, transaction_based_assets
            )
        )

        # Process fixed-income assets
        fixed_income_holdings, fixed_income_summary_data = (
            self._process_fixed_income_assets(fixed_income_assets)
        )

        holdings_list = transaction_holdings + fixed_income_holdings

        # Combine summaries
        summary_total_value = (
            transaction_summary_data["total_value"]
            + fixed_income_summary_data["total_value"]
        )
        summary_total_invested = (
            transaction_summary_data["total_invested"]
            + fixed_income_summary_data["total_invested"]
        )
        summary_days_pnl = transaction_summary_data[
            "days_pnl"
        ]  # No day pnl for fixed income yet

        summary = schemas.PortfolioSummary(
            total_value=summary_total_value,
            total_invested_amount=summary_total_invested,
            days_pnl=summary_days_pnl,
            total_unrealized_pnl=summary_total_value - summary_total_invested,
            total_realized_pnl=transaction_summary_data["realized_pnl"],
        )

        return {"summary": summary, "holdings": holdings_list}

    def _process_transaction_based_assets(
        self, transactions: List[models.Transaction], assets: List[models.Asset]
    ):
        if not transactions:
            return [], {
                "total_value": Decimal(0),
                "total_invested": Decimal(0),
                "days_pnl": Decimal(0),
                "realized_pnl": Decimal(0),
            }

        transactions.sort(key=lambda tx: tx.transaction_date)
        holdings_state = defaultdict(
            lambda: {"quantity": Decimal("0.0"), "total_invested": Decimal("0.0")}
        )
        total_realized_pnl = Decimal("0.0")
        asset_map = {asset.ticker_symbol: asset for asset in assets}

        for tx in transactions:
            ticker = tx.asset.ticker_symbol
            if tx.transaction_type == "BUY":
                holdings_state[ticker]["quantity"] += tx.quantity
                holdings_state[ticker]["total_invested"] += (
                    tx.quantity * tx.price_per_unit
                )
            elif tx.transaction_type == "SELL":
                if holdings_state[ticker]["quantity"] > 0:
                    avg_buy_price = (
                        holdings_state[ticker]["total_invested"]
                        / holdings_state[ticker]["quantity"]
                    )
                    realized_pnl_for_sale = (
                        tx.price_per_unit - avg_buy_price
                    ) * tx.quantity
                    total_realized_pnl += realized_pnl_for_sale
                    proportion_sold = tx.quantity / holdings_state[ticker]["quantity"]
                    holdings_state[ticker]["total_invested"] *= 1 - proportion_sold
                    holdings_state[ticker]["quantity"] -= tx.quantity

        current_holdings_tickers = [
            ticker for ticker, data in holdings_state.items() if data["quantity"] > 0
        ]
        assets_to_price = [
            {
                "ticker_symbol": ticker,
                "exchange": asset_map[ticker].exchange,
                "asset_type": asset_map[ticker].asset_type,
            }
            for ticker in current_holdings_tickers
            if ticker in asset_map
        ]
        price_details = financial_data_service.get_current_prices(assets_to_price)

        holdings_list: List[schemas.Holding] = []
        summary_total_value = Decimal("0.0")
        summary_total_invested = Decimal("0.0")
        summary_days_pnl = Decimal("0.0")

        for ticker in current_holdings_tickers:
            asset = asset_map[ticker]
            data = holdings_state[ticker]
            price_info = price_details.get(
                ticker, {"current_price": Decimal(0), "previous_close": Decimal(0)}
            )
            current_price = price_info["current_price"]
            previous_close = price_info["previous_close"]
            quantity = data["quantity"]
            total_invested = data["total_invested"]
            average_buy_price = (
                total_invested / quantity if quantity > 0 else Decimal(0)
            )
            current_value = quantity * current_price
            unrealized_pnl = current_value - total_invested
            unrealized_pnl_percentage = (
                float(unrealized_pnl / total_invested) if total_invested > 0 else 0.0
            )
            days_pnl = (current_price - previous_close) * quantity
            days_pnl_percentage = (
                float((current_price - previous_close) / previous_close)
                if previous_close > 0
                else 0.0
            )

            holdings_list.append(
                schemas.Holding(
                    asset_id=asset.id,
                    ticker_symbol=ticker,
                    asset_name=asset.name,
                    asset_type=asset.asset_type,
                    quantity=quantity,
                    average_buy_price=average_buy_price,
                    total_invested_amount=total_invested,
                    current_price=current_price,
                    current_value=current_value,
                    days_pnl=days_pnl,
                    days_pnl_percentage=days_pnl_percentage,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percentage=unrealized_pnl_percentage,
                )
            )
            summary_total_value += current_value
            summary_total_invested += total_invested
            summary_days_pnl += days_pnl

        summary_data = {
            "total_value": summary_total_value,
            "total_invested": summary_total_invested,
            "days_pnl": summary_days_pnl,
            "realized_pnl": total_realized_pnl,
        }
        return holdings_list, summary_data

    def _process_fixed_income_assets(self, assets: List[models.Asset]):
        holdings_list: List[schemas.Holding] = []
        summary_total_value = Decimal("0.0")
        summary_total_invested = Decimal("0.0")

        for asset in assets:
            if asset.asset_type == "FIXED_DEPOSIT":
                details = asset.fixed_deposit_details
                total_invested = details.principal_amount
                if details.payout_type == "REINVESTMENT":
                    p = float(details.principal_amount)
                    r = float(details.interest_rate) / 100
                    n = {
                        "MONTHLY": 12,
                        "QUARTERLY": 4,
                        "HALF_YEARLY": 2,
                        "ANNUALLY": 1,
                        "AT_MATURITY": 1,
                    }[details.compounding_frequency]
                    t = (date.today() - details.start_date).days / 365.25
                    if details.compounding_frequency == "AT_MATURITY":
                        t = (details.maturity_date - details.start_date).days / 365.25
                    current_value = Decimal(p * (1 + r / n) ** (n * t))
                else:  # PAYOUT
                    current_value = details.principal_amount

                holdings_list.append(
                    schemas.Holding(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        asset_type=asset.asset_type,
                        current_value=current_value,
                        total_invested_amount=total_invested,
                        institution_name=details.institution_name,
                        interest_rate=details.interest_rate,
                        maturity_date=details.maturity_date.isoformat(),
                    )
                )

            elif asset.asset_type == "BOND":
                details = asset.bond_details
                total_invested = details.purchase_price * details.quantity
                current_value = total_invested  # Simplified valuation for now
                holdings_list.append(
                    schemas.Holding(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        asset_type=asset.asset_type,
                        current_value=current_value,
                        total_invested_amount=total_invested,
                        coupon_rate=details.coupon_rate,
                        maturity_date=details.maturity_date.isoformat(),
                        quantity=details.quantity,
                    )
                )

            elif asset.asset_type == "PPF":
                details = asset.ppf_details
                total_invested = details.current_balance  # User-managed value
                current_value = details.current_balance
                holdings_list.append(
                    schemas.Holding(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        asset_type=asset.asset_type,
                        current_value=current_value,
                        total_invested_amount=total_invested,
                        institution_name=details.institution_name,
                        opening_date=details.opening_date.isoformat(),
                    )
                )

            summary_total_value += current_value
            summary_total_invested += total_invested

        summary_data = {
            "total_value": summary_total_value,
            "total_invested": summary_total_invested,
        }
        return holdings_list, summary_data


holding = CRUDHolding()
