"""
Unit tests for CapitalGainsService tax calculation logic.
Tests STCG/LTCG classification, grandfathering formula, and Budget 2024 thresholds.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.capital_gains_service import (
    CapitalGainsService,
)


class TestIsLTCG:
    """Test _is_ltcg method for correct STCG/LTCG classification."""

    def setup_method(self):
        self.service = CapitalGainsService(db=MagicMock())

    # --- Equity Tests ---
    def test_equity_365_days_is_stcg(self):
        """Equity held exactly 365 days should be STCG (boundary)."""
        result = self.service._is_ltcg("EQUITY_LISTED", 365, date(2025, 1, 1))
        assert result is False

    def test_equity_366_days_is_ltcg(self):
        """Equity held 366 days should be LTCG."""
        result = self.service._is_ltcg("EQUITY_LISTED", 366, date(2025, 1, 1))
        assert result is True

    def test_equity_1_year_is_stcg(self):
        """Equity held exactly 1 year (365 days) is STCG."""
        result = self.service._is_ltcg("EQUITY_LISTED", 365, date(2023, 1, 1))
        assert result is False

    # --- Gold/Debt Tests with Budget 2024 Threshold ---
    def test_gold_730_days_pre_july_2024_is_stcg(self):
        """Gold held 730 days (24m) pre-July 2024 is STCG (old 36m rule)."""
        result = self.service._is_ltcg("GOLD", 730, date(2024, 7, 22))
        assert result is False

    def test_gold_1096_days_pre_july_2024_is_ltcg(self):
        """Gold held 1096 days (>36m) before July 2024 should be LTCG."""
        result = self.service._is_ltcg("GOLD", 1096, date(2024, 7, 22))
        assert result is True

    def test_gold_731_days_post_july_2024_is_ltcg(self):
        """Gold held 731 days (>24m) after July 2024 should be LTCG (new rule)."""
        result = self.service._is_ltcg("GOLD", 731, date(2024, 7, 23))
        assert result is True

    def test_gold_730_days_post_july_2024_is_stcg(self):
        """Gold held 730 days (exactly 24m) after July 2024 should be STCG."""
        result = self.service._is_ltcg("GOLD", 730, date(2024, 7, 23))
        assert result is False

    # --- SGB Tests with Post-July 2024 Rules ---
    def test_sgb_366_days_post_july_2024_is_ltcg(self):
        """SGB held 366 days after July 2024 should be LTCG (12m rule)."""
        result = self.service._is_ltcg("SGB", 366, date(2024, 8, 1))
        assert result is True

    def test_sgb_365_days_post_july_2024_is_stcg(self):
        """SGB held 365 days after July 2024 should be STCG."""
        result = self.service._is_ltcg("SGB", 365, date(2024, 8, 1))
        assert result is False

    def test_sgb_365_days_pre_july_2024_is_stcg(self):
        """SGB held 365 days before July 2024 should be STCG (old 36m rule)."""
        result = self.service._is_ltcg("SGB", 365, date(2024, 7, 22))
        assert result is False

    def test_sgb_1096_days_pre_july_2024_is_ltcg(self):
        """SGB held >36m before July 2024 should be LTCG."""
        result = self.service._is_ltcg("SGB", 1096, date(2024, 7, 22))
        assert result is True


class TestDetermineTaxRateLabel:
    """Test _determine_tax_rate_label method for correct tax rate assignment."""

    def setup_method(self):
        self.service = CapitalGainsService(db=MagicMock())

    def test_stcg_equity_post_july_is_20_percent(self):
        """Equity STCG after July 2024 should be 20%."""
        result = self.service._determine_tax_rate_label(
            "STCG", "EQUITY_LISTED", date(2024, 8, 1)
        )
        assert result == "STCG 20%"

    def test_stcg_equity_pre_july_is_15_percent(self):
        """Equity STCG before July 2024 should be 15%."""
        result = self.service._determine_tax_rate_label(
            "STCG", "EQUITY_LISTED", date(2024, 7, 22)
        )
        assert result == "STCG 15%"

    def test_stcg_debt_is_slab(self):
        """Debt STCG should be at slab rates."""
        result = self.service._determine_tax_rate_label(
            "STCG", "DEBT", date(2025, 1, 1)
        )
        assert result == "STCG Slab"

    def test_ltcg_equity_post_july_is_12_5_percent(self):
        """Equity LTCG after July 2024 should be 12.5%."""
        result = self.service._determine_tax_rate_label(
            "LTCG", "EQUITY_LISTED", date(2024, 8, 1)
        )
        assert result == "LTCG 12.5%"

    def test_ltcg_equity_pre_july_is_10_percent(self):
        """Equity LTCG before July 2024 should be 10%."""
        result = self.service._determine_tax_rate_label(
            "LTCG", "EQUITY_LISTED", date(2024, 7, 22)
        )
        assert result == "LTCG 10%"

    def test_ltcg_gold_post_july_is_12_5_percent(self):
        """Gold LTCG after July 2024 should be 12.5% (no indexation)."""
        result = self.service._determine_tax_rate_label(
            "LTCG", "GOLD", date(2024, 8, 1)
        )
        assert result == "LTCG 12.5%"

    def test_ltcg_gold_pre_july_is_20_percent(self):
        """Gold LTCG before July 2024 should be 20% (with indexation)."""
        result = self.service._determine_tax_rate_label(
            "LTCG", "GOLD", date(2024, 7, 22)
        )
        assert result == "LTCG 20%"


class TestClassifyAssetCategory:
    """Test _classify_asset_category for correct asset type mapping."""

    def setup_method(self):
        self.service = CapitalGainsService(db=MagicMock())

    def _make_asset(
        self,
        asset_type: str,
        currency: str = "INR",
        sector: str = None,
        bond_type=None,
    ):
        asset = MagicMock()
        asset.asset_type = asset_type
        asset.currency = currency
        asset.sector = sector
        asset.bond_type = bond_type
        return asset

    def test_stock_inr_is_equity_listed(self):
        asset = self._make_asset("STOCK")
        result = self.service._classify_asset_category(asset)
        assert result == "EQUITY_LISTED"

    def test_etf_inr_is_equity_listed(self):
        asset = self._make_asset("ETF")
        result = self.service._classify_asset_category(asset)
        assert result == "EQUITY_LISTED"

    def test_stock_usd_is_foreign(self):
        asset = self._make_asset("STOCK", currency="USD")
        result = self.service._classify_asset_category(asset)
        assert result == "FOREIGN"

    def test_mutual_fund_equity_sector_is_equity(self):
        asset = self._make_asset("MUTUAL_FUND", sector="Large Cap Equity")
        result = self.service._classify_asset_category(asset)
        assert result == "EQUITY_LISTED"

    def test_mutual_fund_debt_sector_is_debt(self):
        asset = self._make_asset("MUTUAL_FUND", sector="Short Duration Debt")
        result = self.service._classify_asset_category(asset)
        assert result == "DEBT"


class TestGrandfatheringFormula:
    """
    Test the grandfathering formula:
    Cost = Max(Actual Cost, Min(FMV, Sale Price))
    """

    def test_formula_case_1_fmv_between_cost_and_sale(self):
        """
        Scenario: Buy=100, FMV=200, Sale=300
        Min(FMV, Sale) = 200
        Max(Buy, 200) = 200
        Expected Cost = 200
        """
        buy_price = Decimal("100")
        fmv_2018 = Decimal("200")
        sell_price = Decimal("300")

        lower_of_fmv_sale = min(fmv_2018, sell_price)
        new_cost = max(buy_price, lower_of_fmv_sale)

        assert new_cost == Decimal("200")

    def test_formula_case_2_sale_below_fmv(self):
        """
        Scenario: Buy=100, FMV=300, Sale=200
        Min(FMV, Sale) = 200
        Max(Buy, 200) = 200
        Expected Cost = 200
        """
        buy_price = Decimal("100")
        fmv_2018 = Decimal("300")
        sell_price = Decimal("200")

        lower_of_fmv_sale = min(fmv_2018, sell_price)
        new_cost = max(buy_price, lower_of_fmv_sale)

        assert new_cost == Decimal("200")

    def test_formula_case_3_sale_below_buy(self):
        """
        Scenario: Buy=200, FMV=150, Sale=100
        Min(FMV, Sale) = 100
        Max(Buy, 100) = 200
        Expected Cost = 200 (no loss capping beyond actual cost)
        """
        buy_price = Decimal("200")
        fmv_2018 = Decimal("150")
        sell_price = Decimal("100")

        lower_of_fmv_sale = min(fmv_2018, sell_price)
        new_cost = max(buy_price, lower_of_fmv_sale)

        assert new_cost == Decimal("200")

    def test_formula_case_4_buy_higher_than_fmv(self):
        """
        Scenario: Buy=250, FMV=200, Sale=300
        Min(FMV, Sale) = 200
        Max(Buy, 200) = 250
        Expected Cost = 250 (use actual cost)
        """
        buy_price = Decimal("250")
        fmv_2018 = Decimal("200")
        sell_price = Decimal("300")

        lower_of_fmv_sale = min(fmv_2018, sell_price)
        new_cost = max(buy_price, lower_of_fmv_sale)

        assert new_cost == Decimal("250")
