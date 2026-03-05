from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.capital_gains_service import CapitalGainsService
from app.models import Asset, Transaction, TransactionLink

def test_process_single_link_with_fees():
    service = CapitalGainsService(db=MagicMock())

    # Setup Asset
    asset = MagicMock(spec=Asset)
    asset.ticker_symbol = "RELIANCE"
    asset.name = "Reliance Industries"
    asset.asset_type = "STOCK"
    asset.isin = "INE002A01018"
    asset.currency = "INR"
    asset.sector = "Energy"

    # Setup Buy Transaction
    buy_tx = MagicMock(spec=Transaction)
    buy_tx.transaction_date.date.return_value = date(2024, 1, 1)
    buy_tx.price_per_unit = Decimal("2500")
    buy_tx.quantity = Decimal("10")
    buy_tx.fees = Decimal("100")
    buy_tx.transaction_type = "BUY"

    # Setup Sell Transaction
    sell_tx = MagicMock(spec=Transaction)
    sell_tx.transaction_date.date.return_value = date(2024, 6, 1)
    sell_tx.price_per_unit = Decimal("3000")
    sell_tx.quantity = Decimal("10")
    sell_tx.fees = Decimal("150")
    sell_tx.transaction_type = "SELL"

    # Setup Link (selling 5 units)
    link = MagicMock(spec=TransactionLink)
    link.quantity = Decimal("5")
    link.buy_transaction = buy_tx
    link.sell_transaction = sell_tx

    # 1. Test domestic link without grandfathering
    entry, s112a = service._process_single_link(link, asset, sell_tx, buy_tx)

    # Proportional buy fees: (100 / 10) * 5 = 50
    # Proportional sell fees: (150 / 10) * 5 = 75
    # Actual cost: (2500 * 5) + 50 = 12550
    # Gross Consideration: (3000 * 5) = 15000
    # Net sell value: 15000 - 75 = 14925
    # Gain: 14925 - 12550 = 2375

    assert entry.total_buy_value == Decimal("12550")
    assert entry.total_sell_value == Decimal("14925")
    assert entry.gain == Decimal("2375")
    assert s112a is None  # Not grandfathered

def test_process_single_link_grandfathered_with_fees():
    service = CapitalGainsService(db=MagicMock())

    # Setup Asset
    asset = MagicMock(spec=Asset)
    asset.ticker_symbol = "RELIANCE"
    asset.name = "Reliance Industries"
    asset.asset_type = "STOCK"
    asset.isin = "INE002A01018"
    asset.currency = "INR"
    asset.sector = "Energy"
    asset.fmv_2018 = Decimal("1000")

    # Setup Buy Transaction (Before 2018)
    buy_tx = MagicMock(spec=Transaction)
    buy_tx.transaction_date.date.return_value = date(2017, 1, 1)
    buy_tx.price_per_unit = Decimal("800")
    buy_tx.quantity = Decimal("10")
    buy_tx.fees = Decimal("80")
    buy_tx.transaction_type = "BUY"

    # Setup Sell Transaction (LTCG)
    sell_tx = MagicMock(spec=Transaction)
    sell_tx.transaction_date.date.return_value = date(2025, 1, 1)
    sell_tx.price_per_unit = Decimal("1500")
    sell_tx.quantity = Decimal("10")
    sell_tx.fees = Decimal("100")
    sell_tx.transaction_type = "SELL"

    # Setup Link (selling 10 units)
    link = MagicMock(spec=TransactionLink)
    link.quantity = Decimal("10")
    link.buy_transaction = buy_tx
    link.sell_transaction = sell_tx

    service._get_grandfathering_price = MagicMock(return_value=Decimal("1000"))

    entry, s112a = service._process_single_link(link, asset, sell_tx, buy_tx)

    # Proportional buy fees: (80 / 10) * 10 = 80
    # Proportional sell fees: (100 / 10) * 10 = 100
    # Actual cost total: (800 * 10) + 80 = 8080
    # Gross Consideration: (1500 * 10) = 15000
    # Total FMV: (1000 * 10) = 10000

    # Lower of (FMV, Sale): min(10000, 15000) = 10000
    # Final Cost: max(Actual, Lower of FMV/Sale) = max(8080, 10000) = 10000

    # Net sell value: 15000 - 100 = 14900
    # Gain: 14900 - 10000 = 4900

    assert entry.total_buy_value == Decimal("10000")
    assert entry.total_sell_value == Decimal("14900")
    assert entry.gain == Decimal("4900")

    assert s112a is not None
    assert s112a.cost_of_acquisition_orig == Decimal("8080")
    assert s112a.cost_of_acquisition_final == Decimal("10000")
    assert s112a.expenditure == Decimal("100")
    assert s112a.total_deductions == Decimal("10100")  # final + expenditure
    assert s112a.full_value_consideration == Decimal("15000")
    assert s112a.balance == Decimal("4900")  # full - total_deductions

def test_process_foreign_link_with_fees():
    service = CapitalGainsService(db=MagicMock())

    # Setup Asset
    asset = MagicMock(spec=Asset)
    asset.ticker_symbol = "AAPL"
    asset.name = "Apple Inc"
    asset.asset_type = "STOCK"
    asset.currency = "USD"

    # Setup Buy Transaction
    buy_tx = MagicMock(spec=Transaction)
    buy_tx.transaction_date.date.return_value = date(2024, 1, 1)
    buy_tx.price_per_unit = Decimal("180")
    buy_tx.quantity = Decimal("10")
    buy_tx.fees = Decimal("5")
    buy_tx.transaction_type = "BUY"
    buy_tx.details = None

    # Setup Sell Transaction
    sell_tx = MagicMock(spec=Transaction)
    sell_tx.transaction_date.date.return_value = date(2024, 6, 1)
    sell_tx.price_per_unit = Decimal("200")
    sell_tx.quantity = Decimal("10")
    sell_tx.fees = Decimal("8")
    sell_tx.transaction_type = "SELL"

    # Setup Link (selling 4 units)
    link = MagicMock(spec=TransactionLink)
    link.quantity = Decimal("4")
    link.buy_transaction = buy_tx
    link.sell_transaction = sell_tx

    entry = service._process_foreign_link(link, asset, sell_tx, buy_tx)

    # Prop buy fees: (5 / 10) * 4 = 2.0
    # Prop sell fees: (8 / 10) * 4 = 3.2
    # Total buy: (180 * 4) + 2.0 = 722.0
    # Total sell: (200 * 4) - 3.2 = 796.8
    # Gain: 796.8 - 722.0 = 74.8

    assert entry.total_buy_value == Decimal("722.0")
    assert entry.total_sell_value == Decimal("796.8")
    assert entry.gain == Decimal("74.8")
