import time
import uuid
from decimal import Decimal
from datetime import date, timedelta
from app.crud.crud_analytics import _get_realized_and_unrealized_cash_flows
from app.schemas.transaction import Transaction
from app.schemas.asset import Asset
import cProfile

def test_bottleneck(num_txs=1000):
    txs = []
    base_date = date(1980, 1, 1)
    port_id = uuid.uuid4()

    # 1. Create a large number of buys and sells
    for i in range(num_txs):
        txs.append(
            Transaction(
                id=uuid.uuid4(),
                transaction_date=base_date + timedelta(days=i),
                transaction_type="BUY",
                quantity=Decimal("10.0"),
                price_per_unit=Decimal("100.0"),
                asset_id=uuid.uuid4(),
                portfolio_id=port_id,
                asset=Asset(id=uuid.uuid4(), ticker_symbol="MOCK", name="Mock", asset_type="STOCK", currency="INR"),
                details={"fx_rate": "1.0"}
            )
        )

    for i in range(num_txs // 2):
        txs.append(
            Transaction(
                id=uuid.uuid4(),
                transaction_date=base_date + timedelta(days=num_txs + i),
                transaction_type="SELL",
                quantity=Decimal("5.0"),
                price_per_unit=Decimal("150.0"),
                asset_id=uuid.uuid4(),
                portfolio_id=port_id,
                asset=Asset(id=uuid.uuid4(), ticker_symbol="MOCK", name="Mock", asset_type="STOCK", currency="INR"),
                details={"fx_rate": "1.0"}
            )
        )

    for i in range(num_txs * 2):
        txs.append(
            Transaction(
                id=uuid.uuid4(),
                transaction_date=base_date + timedelta(days=int(num_txs * 1.5) + i),
                transaction_type="DIVIDEND",
                quantity=Decimal("100.0"),
                price_per_unit=Decimal("1.0"),
                asset_id=uuid.uuid4(),
                portfolio_id=port_id,
                asset=Asset(id=uuid.uuid4(), ticker_symbol="MOCK", name="Mock", asset_type="STOCK", currency="INR"),
                details={"fx_rate": "1.0"}
            )
        )

    # Fast version logic that I plan to implement
    def fast_calc(sorted_txs, income_flows, sells):
        t0 = time.time()

        # Calculate running balances
        import bisect

        buy_dates = []
        buy_cumulative = []
        current_buys = Decimal("0.0")

        sell_dates = []
        sell_cumulative = []
        current_sells = Decimal("0.0")

        acquisition_types = {"BUY", "ESPP_PURCHASE", "RSU_VEST"}

        for t in sorted_txs:
            if t.transaction_type in acquisition_types:
                current_buys += t.quantity
                buy_dates.append(t.transaction_date.date())
                buy_cumulative.append(current_buys)

        for s in sells:
            current_sells += s.quantity
            sell_dates.append(s.transaction_date.date())
            sell_cumulative.append(current_sells)

        total_sells = current_sells

        realized_income = 0
        unrealized_income = 0

        for income_tx in income_flows:
            income_date = income_tx.transaction_date.date()

            fx_rate = Decimal(str(income_tx.details.get("fx_rate", 1))) if income_tx.details else Decimal(1)
            if income_tx.transaction_type == "COUPON":
                amount_val = income_tx.quantity * fx_rate
            else:
                amount_val = income_tx.quantity * income_tx.price_per_unit * fx_rate

            amount = float(amount_val)

            # Find total shares bought up to the date
            idx = bisect.bisect_right(buy_dates, income_date)
            if idx == 0:
                continue
            bought_at_income_date = buy_cumulative[idx - 1]

            # Find total shares sold AFTER this date
            idx_sell = bisect.bisect_right(sell_dates, income_date)
            if idx_sell == 0:
                sold_from_that_lot = total_sells
            else:
                sold_from_that_lot = total_sells - sell_cumulative[idx_sell - 1]

            proportion_realized = float(sold_from_that_lot / bought_at_income_date)
            proportion_unrealized = 1.0 - proportion_realized

            realized_income += amount * proportion_realized
            unrealized_income += amount * proportion_unrealized

        t1 = time.time()
        print(f"Fast Calc Time: {t1 - t0:.4f}s")
        return realized_income, unrealized_income


    t0 = time.time()
    res_orig = _get_realized_and_unrealized_cash_flows(txs, [])
    t1 = time.time()

    print(f"Original Time for {len(txs)} txs: {t1 - t0:.4f}s")

    # Extract the necessary data to test the fast function
    sorted_txs = sorted(txs, key=lambda t: t.transaction_date)
    sells = [t for t in sorted_txs if t.transaction_type == "SELL"]
    income_flows = [
        t for t in sorted_txs
        if t.transaction_type in ("DIVIDEND", "COUPON", "INTEREST_CREDIT")
    ]

    fast_calc(sorted_txs, income_flows, sells)

if __name__ == "__main__":
    test_bottleneck(2000)
    test_bottleneck(4000)
    test_bottleneck(6000)
