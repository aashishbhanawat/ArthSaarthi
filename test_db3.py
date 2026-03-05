from app.crud.crud_analytics import _get_realized_and_unrealized_cash_flows
import app.schemas.transaction as schemas_tx
from datetime import datetime
from decimal import Decimal
import uuid

tx_id = uuid.uuid4()
tx = schemas_tx.Transaction(
    id=tx_id,
    user_id=tx_id,
    portfolio_id=tx_id,
    asset_id=tx_id,
    transaction_date=datetime.now(),
    transaction_type="BUY",
    quantity=Decimal("10"),
    price_per_unit=Decimal("100"),
    details={},
    asset={"id": tx_id, "name": "Asset 1", "asset_type": "STOCK", "ticker_symbol": "ASSET1"}
)

_get_realized_and_unrealized_cash_flows([tx])
print("SUCCESS")
