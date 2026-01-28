from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List

import pytest
from app.services.schedule_fa_service import ScheduleFAService

# Mock Transaction class-like structure
class MockTx:
    def __init__(self, qty, price, date_str):
        self.quantity = Decimal(qty)
        self.price_per_unit = Decimal(price)
        self.transaction_date = datetime.strptime(date_str, "%Y-%m-%d")

class TestScheduleFAService:
    
    def test_calculate_lot_peak_value_simple_hold(self):
        """
        Test peak value when asset is held for the entire year.
        Should be Max(DailyPrice * Qty).
        """
        service = ScheduleFAService(db=None) 
        
        buy_tx = MockTx(10, 100, "2023-01-01")
        lot = {
            "buy_transaction": buy_tx,
            "disposals": [],
            "id": "lot1"
        }
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        # Prices: 
        # Jan 1: 100 -> Val 1000
        # June 1: 200 -> Val 2000 (Peak)
        # Dec 31: 150 -> Val 1500
        prices = {
            date(2023, 1, 1): Decimal(100),
            date(2023, 6, 1): Decimal(200),
            date(2023, 12, 31): Decimal(150),
        }
        
        peak, peak_date = service._calculate_lot_peak_value(lot, start_date, end_date, prices)
        
        assert peak == Decimal(2000)
        assert peak_date == date(2023, 6, 1)

    def test_calculate_lot_peak_value_with_partial_sell(self):
        """
        Test peak value with a partial sale mid-year.
        Ensures we don't multiply Initial Qty * Peak Price if Peak Price occurred AFTER sale.
        """
        service = ScheduleFAService(db=None)
        
        buy_tx = MockTx(10, 100, "2023-01-01")
        # Sell 5 on July 1.
        disposal = {
            "qty": Decimal(5), 
            "date": datetime(2023, 7, 1),
            "sell_price": Decimal(220) 
        }
        lot = {
            "buy_transaction": buy_tx,
            "disposals": [disposal],
            "id": "lot1"
        }
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        # Scenario:
        # June 1: Price 200. Held 10. Value = 2000.
        # Aug 1: Price 300. Held 5 (Sold 5 on July 1). Value = 1500.
        
        # If logic was wrong (Max Qty * Max Price), it would be 10 * 300 = 3000.
        # Correct logic: Max(2000, 1500) = 2000.
        
        prices = {
            date(2023, 6, 1): Decimal(200),
            date(2023, 8, 1): Decimal(300),
        }
        
        peak, peak_date = service._calculate_lot_peak_value(lot, start_date, end_date, prices)
        
        assert peak == Decimal(2000)
        assert peak_date == date(2023, 6, 1)

    def test_calculate_lot_peak_value_sold_all_before_peak(self):
        """
        Test peak value when all assets are sold before the highest price of the year.
        """
        service = ScheduleFAService(db=None)
        
        buy_tx = MockTx(10, 100, "2023-01-01")
        # Sell ALL 10 on July 1.
        disposal = {
            "qty": Decimal(10), 
            "date": datetime(2023, 7, 1),
            "sell_price": Decimal(150) 
        }
        lot = {
            "buy_transaction": buy_tx,
            "disposals": [disposal],
            "id": "lot1"
        }
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        # Scenario:
        # June 1: Price 150. Held 10. Value = 1500.
        # Dec 1: Price 500. Held 0. Value = 0.
        
        prices = {
            date(2023, 6, 1): Decimal(150),
            date(2023, 12, 1): Decimal(500),
        }
        
        peak, peak_date = service._calculate_lot_peak_value(lot, start_date, end_date, prices)
        
        assert peak == Decimal(1500)
        assert peak_date == date(2023, 6, 1)
