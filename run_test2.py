from datetime import date
from decimal import Decimal
from app.crud.crud_analytics import _get_realized_and_unrealized_cash_flows
import app.schemas.transaction as schemas_tx
import uuid

tx_id = uuid.uuid4()
tx1 = schemas_tx.Transaction(
    id=tx_id,
    user_id=tx_id,
    portfolio_id=tx_id,
    asset_id=tx_id,
    transaction_date=date.today(),
    transaction_type="BUY",
    quantity=Decimal("10"),
    price_per_unit=Decimal("100"),
    details={},
    asset={"id": tx_id, "name": "Asset 1", "asset_type": "STOCK", "ticker_symbol": "ASSET1"}
)
tx2 = schemas_tx.Transaction(
    id=uuid.uuid4(),
    user_id=tx_id,
    portfolio_id=tx_id,
    asset_id=tx_id,
    transaction_date=date.today(),
    transaction_type="SELL",
    quantity=Decimal("5"),
    price_per_unit=Decimal("150"),
    details={},
    asset={"id": tx_id, "name": "Asset 1", "asset_type": "STOCK", "ticker_symbol": "ASSET1"}
)

try:
    print(_get_realized_and_unrealized_cash_flows([tx1, tx2]))
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
