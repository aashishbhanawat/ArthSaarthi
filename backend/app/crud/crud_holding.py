import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app import crud, schemas
from app.services.financial_data_service import financial_data_service


class CRUDHolding:
    """
    CRUD operations for portfolio holdings.
    This is a read-only CRUD module that calculates holdings based on transactions.
    """

    def get_portfolio_holdings_and_summary(
        self, db: Session, *, portfolio_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Calculates the consolidated holdings and a summary for a given portfolio.
        """
        transactions = crud.transaction.get_multi_by_portfolio(
            db=db, portfolio_id=portfolio_id
        )

        if not transactions:
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

        # Sort transactions chronologically to process them in order
        transactions.sort(key=lambda tx: tx.transaction_date)

        # Use defaultdict to easily manage the state of each asset
        holdings_state = defaultdict(
            lambda: {"quantity": Decimal("0.0"), "total_invested": Decimal("0.0")}
        )
        total_realized_pnl = Decimal("0.0")
        asset_map = {tx.asset.ticker_symbol: tx.asset for tx in transactions}

        for tx in transactions:
            ticker = tx.asset.ticker_symbol
            if tx.transaction_type == "BUY":
                holdings_state[ticker]["quantity"] += tx.quantity
                holdings_state[ticker]["total_invested"] += (
                    tx.quantity * tx.price_per_unit
                )
            elif tx.transaction_type == "SELL":
                if holdings_state[ticker]["quantity"] > 0:
                    # Calculate avg buy price before the sale
                    avg_buy_price = (
                        holdings_state[ticker]["total_invested"]
                        / holdings_state[ticker]["quantity"]
                    )
                    # Realized PNL for this sale
                    realized_pnl_for_sale = (
                        tx.price_per_unit - avg_buy_price
                    ) * tx.quantity
                    total_realized_pnl += realized_pnl_for_sale

                    # Update holdings state
                    proportion_sold = tx.quantity / holdings_state[ticker]["quantity"]
                    holdings_state[ticker]["total_invested"] *= 1 - proportion_sold
                    holdings_state[ticker]["quantity"] -= tx.quantity

        # Filter for assets currently held
        current_holdings_tickers = [
            ticker for ticker, data in holdings_state.items() if data["quantity"] > 0
        ]

        assets_to_price = [
            {
                "ticker_symbol": ticker,
                "exchange": asset_map[ticker].exchange,
                "asset_type": asset_map[ticker].asset_type,
            }
            for ticker in current_holdings_tickers if ticker in asset_map
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
                float(unrealized_pnl / total_invested)
                if total_invested > 0
                else 0.0
            )
            days_pnl = (current_price - previous_close) * quantity
            days_pnl_percentage = (
                float((current_price - previous_close) / previous_close)
                if previous_close > 0
                else 0.0
            )

            group_map = {
                "STOCK": "EQUITIES",
                "MUTUAL_FUND": "EQUITIES",
                "ETF": "EQUITIES",
                "FIXED_DEPOSIT": "DEPOSITS",
                "BOND": "BONDS",
                "PPF": "SCHEMES",
            }
            group = group_map.get(asset.asset_type, "MISCELLANEOUS")

            holdings_list.append(
                schemas.Holding(
                    asset_id=asset.id,
                    ticker_symbol=ticker,
                    asset_name=asset.name,
                    asset_type=asset.asset_type,
                    group=group,
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

        summary = schemas.PortfolioSummary(
            total_value=summary_total_value,
            total_invested_amount=summary_total_invested,
            days_pnl=summary_days_pnl,
            total_unrealized_pnl=summary_total_value - summary_total_invested,
            total_realized_pnl=total_realized_pnl,
        )

        return {"summary": summary, "holdings": holdings_list}


holding = CRUDHolding()
