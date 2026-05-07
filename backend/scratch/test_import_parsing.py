
import os
from datetime import datetime

import pandas as pd
from pydantic import BaseModel


class ParsedTransaction(BaseModel):
    transaction_date: datetime
    ticker_symbol: str
    transaction_type: str
    quantity: float
    price_per_unit: float
    fees: float
    isin: str | None = None

def test_serialization():
    # Simulate what happens in the backend
    t = ParsedTransaction(
        transaction_date=datetime(2023, 10, 10),
        ticker_symbol="RIL",
        transaction_type="BUY",
        quantity=10.0,
        price_per_unit=2800.0,
        fees=15.0,
        isin=None
    )

    # model_dump converts datetime to datetime object (in Pydantic v2)
    # or ISO string (if model_dump_json).
    # model_dump() usually keeps it as datetime.

    data = [t.model_dump()]
    df = pd.DataFrame(data)
    # In DF, it becomes Timestamp
    print(f"Initial DF date type: {type(df.iloc[0]['transaction_date'])}")

    json_path = "test_data.json"
    df.to_json(json_path, orient='records', date_format='iso')

    # Read back
    df_read = pd.read_json(json_path, orient='records')
    print(f"Read back DF date type: {type(df_read.iloc[0]['transaction_date'])}")

    for _, row in df_read.iterrows():
        # Clean NaNs to None
        row_data = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        print(f"Row data: {row_data}")
        print(f"Date type in row_data: {type(row_data['transaction_date'])}")
        try:
            ParsedTransaction(**row_data)
            print("Successfully parsed ParsedTransaction")
        except Exception as e:
            print(f"Failed to parse ParsedTransaction: {e}")

    if os.path.exists(json_path):
        os.remove(json_path)

if __name__ == "__main__":
    test_serialization()
