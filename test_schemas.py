# Pydantic V1/Android Compatibility Verification Script
#
# Use this script to verify that all schemas compile and parse successfully under Pydantic V1.
# This prevents regression errors on Android (Chaquopy runs Pydantic 1.10.x).
#
# Setup instructions:
#   python3 -m venv test_env_v1
#   test_env_v1/bin/pip install pydantic==1.10.13 email-validator==1.3.1
#
# Run instructions:
#   test_env_v1/bin/python test_schemas.py
#

import sys
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any

# Ensure python finds the backend package
sys.path.insert(0, "./backend")

import pydantic
print(f"Loaded Pydantic version: {pydantic.__version__} (Should be 1.10.x for V1 tests)")

# 1. Test Schema Compilation (Imports everything)
try:
    import app.schemas as schemas
    print("✅ All schemas compiled successfully!")
except Exception as e:
    import traceback
    print(f"❌ Schema compilation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Helper to create mock objects for testing from_orm
class MockObject:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# Track test results
passed = []
failed = []

def run_test(name, schema_class, mock_data, is_orm=True):
    try:
        if is_orm:
            # Test from_orm compatibility
            mock_obj = MockObject(**mock_data)
            instance = schema_class.from_orm(mock_obj)
        else:
            # Test dict validation
            instance = schema_class(**mock_data)
        
        passed.append(name)
        print(f"✅ {name}: SUCCESS")
    except Exception as e:
        failed.append((name, str(e)))
        print(f"❌ {name}: FAILED - {e}")

# 2. Test User Schema
run_test("User", schemas.User, {
    "id": uuid.uuid4(),
    "email": "test@example.com",
    "full_name": "Test User",
    "is_active": True,
    "is_admin": False,
    "created_at": datetime.now(),
    "portfolios": []
})

# 3. Test Portfolio Schema
run_test("Portfolio", schemas.Portfolio, {
    "id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "name": "My Core Portfolio",
    "description": "Retirement portfolio",
    "transactions": []
})

# 4. Test Asset Schema
run_test("Asset", schemas.Asset, {
    "id": uuid.uuid4(),
    "ticker_symbol": "RELIANCE",
    "isin": "INE002A01018",
    "name": "Reliance Industries Ltd.",
    "asset_type": "EQUITY",
    "currency": "INR",
    "is_custom": False,
    "current_price": 2500.0,
    "day_change": 1.2
})

# 5. Test AssetAlias Schema
run_test("AssetAlias", schemas.AssetAlias, {
    "id": uuid.uuid4(),
    "asset_id": uuid.uuid4(),
    "alias_symbol": "RELIANCE-EQ",
    "source": "Zerodha"
})

# 6. Test AuditLog Schema
run_test("AuditLog", schemas.AuditLog, {
    "id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "event_type": "CREATE_PORTFOLIO",
    "timestamp": datetime.now(),
    "details": {"name": "Test"}
})

# 7. Test Bond Schema
run_test("Bond", schemas.Bond, {
    "id": uuid.uuid4(),
    "asset_id": uuid.uuid4(),
    "bond_type": "SGB",
    "isin": "INE002A01018",
    "name": "Reliance Bond",
    "coupon_rate": 8.5,
    "maturity_date": date(2030, 6, 30),
    "face_value": 1000.0,
    "interest_payout": "Semi-Annual",
    "is_taxable": True
})

# 8. Test FixedDeposit Schema
run_test("FixedDeposit", schemas.FixedDeposit, {
    "id": uuid.uuid4(),
    "portfolio_id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "name": "HDFC FD",
    "bank": "HDFC Bank",
    "account_number": "123456",
    "principal_amount": 100000.0,
    "interest_rate": 7.1,
    "start_date": date(2023, 1, 1),
    "maturity_date": date(2024, 1, 1),
    "maturity_amount": 107250.0,
    "interest_payout": "Cumulative",
    "compounding_frequency": "Quarterly",
    "is_active": True,
    "notes": "Tax saver FD"
})

# 9. Test RecurringDeposit Schema
run_test("RecurringDeposit", schemas.RecurringDeposit, {
    "id": uuid.uuid4(),
    "portfolio_id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "name": "ICICI RD",
    "bank": "ICICI Bank",
    "account_number": "654321",
    "monthly_installment": 5000.0,
    "interest_rate": 6.8,
    "start_date": date(2023, 1, 1),
    "tenure_months": 12,
    "maturity_amount": 62245.0,
    "interest_payout": "Cumulative",
    "compounding_frequency": "Quarterly",
    "is_active": True,
    "notes": "RD saving"
})

# 10. Test Goal Schema (Checks forward reference to GoalLink)
run_test("Goal", schemas.Goal, {
    "id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "name": "Education",
    "target_amount": 5000000.0,
    "target_date": date(2035, 6, 30),
    "expected_return": 12.0,
    "links": []
})

# 11. Test GoalLink Schema
run_test("GoalLink", schemas.GoalLink, {
    "id": uuid.uuid4(),
    "goal_id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "portfolio_id": uuid.uuid4(),
    "asset_id": uuid.uuid4(),
    "asset": None,
    "portfolio": None
})

# 12. Test HistoricalInterestRate Schema
run_test("HistoricalInterestRate", schemas.HistoricalInterestRate, {
    "id": uuid.uuid4(),
    "scheme_name": "PPF",
    "start_date": date(2023, 4, 1),
    "end_date": date(2024, 3, 31),
    "rate": Decimal("7.100")
})

# 13. Test Holding Schema
run_test("Holding", schemas.Holding, {
    "asset_id": uuid.uuid4(),
    "ticker_symbol": "TCS",
    "asset_name": "Tata Consultancy Services",
    "asset_type": "EQUITY",
    "currency": "INR",
    "group": "EQUITY",
    "quantity": 10.0,
    "average_buy_price": 3200.0,
    "total_invested_amount": 32000.0,
    "current_price": 3500.0,
    "current_value": 35000.0,
    "days_pnl": 300.0,
    "days_pnl_percentage": 0.8,
    "unrealized_pnl": 3000.0,
    "unrealized_pnl_percentage": 9.375,
    "isin": "INE467B01029"
}, is_orm=False)

# 14. Test ImportSession Schema
run_test("ImportSession", schemas.ImportSession, {
    "id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "portfolio_id": uuid.uuid4(),
    "file_name": "trades.csv",
    "file_path": "/path/trades.csv",
    "source": "Zerodha Tradebook",
    "status": "COMPLETED",
    "error_message": None,
    "parsed_file_path": None,
    "portfolio": MockObject(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Mock Portfolio",
        description="mock",
        transactions=[]
    ),
    "user": MockObject(
        id=uuid.uuid4(),
        email="mock@user.com",
        full_name="Mock User",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(),
        portfolios=[]
    )
})

# 15. Test ParsedTransaction Schema (Checks custom datetime string parsing)
run_test("ParsedTransaction", schemas.ParsedTransaction, {
    "transaction_date": "2022-12-09",
    "ticker_symbol": "POLCOR",
    "transaction_type": "BUY",
    "quantity": 30.0,
    "price_per_unit": 1700.0,
    "fees": 391.7,
    "isin": "INE123"
}, is_orm=False)

# 16. Test Watchlist Schema
run_test("Watchlist", schemas.Watchlist, {
    "id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "name": "Tech Stocks",
    "created_at": datetime.now(),
    "items": []
})

# 17. Test CapitalGainsSummary (Checks forward reference to ForeignGainEntry)
run_test("CapitalGainsSummary", schemas.CapitalGainsSummary, {
    "financial_year": "2023-2024",
    "total_stcg": Decimal("50000.0"),
    "total_ltcg": Decimal("120000.0"),
    "estimated_stcg_tax": Decimal("7500.0"),
    "estimated_ltcg_tax": Decimal("12000.0"),
    "itr_schedule_cg": [],
    "schedule_112a": [],
    "gains": [],
    "foreign_gains": []
}, is_orm=False)



# Summary Report
print("\n" + "="*40)
print("           TEST SUMMARY REPORT")
print("="*40)
print(f"Total Tests Run: {len(passed) + len(failed)}")
print(f"Passed: {len(passed)}")
print(f"Failed: {len(failed)}")
print("="*40)

if failed:
    print("\nDetailed Failures:")
    for name, err in failed:
        print(f"- {name}: {err}")
    sys.exit(1)
else:
    print("\n🎉 All schema tests passed successfully!")
    sys.exit(0)
