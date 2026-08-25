import uuid
from decimal import Decimal

from app.models.capital_loss_ledger import CapitalLossLedger
from app.services.tax_setoff_service import (
    TaxSetOffService,
    calculate_years_remaining,
    fy_to_ay,
)


def test_fy_to_ay_conversion():
    assert fy_to_ay("2025-26") == "2026-27"
    assert fy_to_ay("2023-24") == "2024-25"


def test_calculate_years_remaining():
    # Loss in AY 2020-21, evaluated in AY 2026-27: (2020 + 8) - 2026 = 2 years remaining
    assert calculate_years_remaining("2020-21", "2026-27") == 2
    # Loss in AY 2018-19, evaluated in AY 2026-27: (2018 + 8) - 2026 = 0 years remaining
    assert calculate_years_remaining("2018-19", "2026-27") == 0
    # Loss in AY 2017-18, evaluated in AY 2026-27: (2017 + 8) - 2026 = -1 (expired)
    assert calculate_years_remaining("2017-18", "2026-27") == -1


def test_stcl_setoff_against_stcg_and_ltcg(db, monkeypatch):

    """
    Scenario 1: User has STCL ₹20,000 and LTCG ₹50,000.
    STCL is set off against LTCG, reducing net LTCG to ₹30,000.
    """
    user_id = str(uuid.uuid4())
    fy_year = "2025-26"

    # Mock CapitalGainsService calculation
    class MockGain:
        def __init__(self, gain, gain_type):
            self.gain = Decimal(str(gain))
            self.gain_type = gain_type

    class MockSummary:
        gains = [
            MockGain(-20000, "STCG"),  # STCL ₹20,000
            MockGain(50000, "LTCG"),   # LTCG ₹50,000
        ]

    monkeypatch.setattr(
        "app.services.tax_setoff_service.CapitalGainsService.calculate_capital_gains",
        lambda self, portfolio_id, user_id, fy_year, slab_rate: MockSummary(),
    )

    service = TaxSetOffService(db)
    result = service.calculate_net_capital_gains(user_id=user_id, fy_year=fy_year)


    assert result.breakdown.gross_stcl == Decimal("20000.00")
    assert result.breakdown.gross_ltcg == Decimal("50000.00")
    assert result.breakdown.cy_stcl_offset_against_ltcg == Decimal("20000.00")
    assert result.breakdown.net_taxable_stcg == Decimal("0.00")
    assert result.breakdown.net_taxable_ltcg == Decimal("30000.00")
    assert result.breakdown.unabsorbed_stcl_to_carry_forward == Decimal("0.00")


def test_ltcl_cannot_setoff_against_stcg(db, monkeypatch):
    """
    Scenario 2: User has LTCL ₹30,000 and STCG ₹40,000.
    LTCL is NOT set off against STCG.
    LTCL remains unabsorbed (₹30,000) to carry forward.
    """

    user_id = str(uuid.uuid4())
    fy_year = "2025-26"

    class MockGain:
        def __init__(self, gain, gain_type):
            self.gain = Decimal(str(gain))
            self.gain_type = gain_type

    class MockSummary:
        gains = [
            MockGain(-30000, "LTCG"),  # LTCL ₹30,000
            MockGain(40000, "STCG"),   # STCG ₹40,000
        ]

    monkeypatch.setattr(
        "app.services.tax_setoff_service.CapitalGainsService.calculate_capital_gains",
        lambda self, portfolio_id, user_id, fy_year, slab_rate: MockSummary(),
    )

    service = TaxSetOffService(db)
    result = service.calculate_net_capital_gains(user_id=user_id, fy_year=fy_year)


    assert result.breakdown.gross_ltcl == Decimal("30000.00")
    assert result.breakdown.gross_stcg == Decimal("40000.00")
    assert result.breakdown.cy_ltcl_offset_against_ltcg == Decimal("0.00")
    assert result.breakdown.net_taxable_stcg == Decimal("40000.00")
    assert result.breakdown.net_taxable_ltcg == Decimal("0.00")
    assert result.breakdown.unabsorbed_ltcl_to_carry_forward == Decimal("30000.00")


def test_brought_forward_loss_setoff_and_expiry(
    db, pre_unlocked_key_manager, monkeypatch
):


    """
    Scenario 3: User has brought-forward loss entries:
    - AY 2020-21 (Valid): STCL ₹15,000 (Filed on time)
    - AY 2019-20 (Valid): LTCL ₹25,000 (Filed on time)
    - AY 2021-22 (Invalid): STCL ₹10,000 (Filed LATE) -> Must be ignored
    - AY 2016-17 (Expired >8 years): STCL ₹50,000 -> Must be ignored

    Current FY 2025-26 (AY 2026-27):
    Current realized STCG = ₹20,000, LTCG = ₹30,000.
    Setoff:
    - BF STCL ₹15,000 offsets STCG ₹20,000 -> Net STCG ₹5,000.
    - BF LTCL ₹25,000 offsets LTCG ₹30,000 -> Net LTCG ₹5,000.
    """
    from app.core.security import get_password_hash
    from app.models.user import User

    test_user = User(
        email="test_loss_ledger@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Loss Ledger User",
        is_active=True,
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    user_uuid = test_user.id
    user_id = str(user_uuid)
    fy_year = "2025-26"


    # Add loss ledger entries to DB
    e1 = CapitalLossLedger(
        user_id=user_uuid,
        financial_year="2019-20",
        assessment_year="2020-21",
        stcl_amount=Decimal("15000.00"),
        ltcl_amount=Decimal("0.00"),
        is_itr_filed_on_time=True,
    )
    e2 = CapitalLossLedger(
        user_id=user_uuid,
        financial_year="2018-19",
        assessment_year="2019-20",
        stcl_amount=Decimal("0.00"),
        ltcl_amount=Decimal("25000.00"),
        is_itr_filed_on_time=True,
    )
    e3_late = CapitalLossLedger(
        user_id=user_uuid,
        financial_year="2020-21",
        assessment_year="2021-22",
        stcl_amount=Decimal("10000.00"),
        ltcl_amount=Decimal("0.00"),
        is_itr_filed_on_time=False,  # Late return!
    )
    e4_expired = CapitalLossLedger(
        user_id=user_uuid,
        financial_year="2015-16",
        assessment_year="2016-17",  # >8 years old in AY 2026-27
        stcl_amount=Decimal("50000.00"),
        ltcl_amount=Decimal("0.00"),
        is_itr_filed_on_time=True,
    )
    db.add_all([e1, e2, e3_late, e4_expired])
    db.commit()

    class MockGain:
        def __init__(self, gain, gain_type):
            self.gain = Decimal(str(gain))
            self.gain_type = gain_type

    class MockSummary:
        gains = [
            MockGain(20000, "STCG"),
            MockGain(30000, "LTCG"),
        ]

    monkeypatch.setattr(
        "app.services.tax_setoff_service.CapitalGainsService.calculate_capital_gains",
        lambda self, portfolio_id, user_id, fy_year, slab_rate: MockSummary(),
    )

    service = TaxSetOffService(db)
    result = service.calculate_net_capital_gains(user_id=user_id, fy_year=fy_year)

    assert result.breakdown.bf_stcl_used == Decimal("15000.00")
    assert result.breakdown.bf_ltcl_used == Decimal("25000.00")
    assert result.breakdown.net_taxable_stcg == Decimal("5000.00")
    assert result.breakdown.net_taxable_ltcg == Decimal("5000.00")



def test_tax_loss_harvesting_recommendations(db, monkeypatch):
    """
    Scenario 4: User has open lots with unrealized losses:
    - Lot A: STCL ₹10,000
    - Lot B: LTCL ₹15,000

    Net taxable gains before harvesting: STCG ₹12,000 (Slab 30%),
    LTCG ₹200,000 (12.5% over 1.25L). Engine recommends harvesting
    Lot A (saving ₹3,000 at 30%) and Lot B (saving ₹1,875 at 12.5%).
    """

    user_id = str(uuid.uuid4())
    fy_year = "2025-26"

    class MockGain:
        def __init__(self, gain, gain_type):
            self.gain = Decimal(str(gain))
            self.gain_type = gain_type

    class MockCGSummary:
        gains = [
            MockGain(12000, "STCG"),
            MockGain(200000, "LTCG"),
        ]

    class MockLot:
        def __init__(self, holding_id, ticker, unrealized_gain, gain_type):
            self.holding_id = holding_id
            self.asset_id = str(uuid.uuid4())
            self.asset_ticker = ticker
            self.asset_name = ticker
            self.asset_type = "EQUITY"
            self.buy_date = "2025-05-01"
            self.quantity = Decimal("100")
            self.buy_price = Decimal("200.0")
            self.current_price = Decimal("100.0")
            self.total_cost = Decimal("20000.0")
            self.market_value = Decimal("10000.0")
            self.unrealized_gain = Decimal(str(unrealized_gain))
            self.gain_type = gain_type
            self.holding_days = 100

    class MockUnrealizedSummary:
        lots = [
            MockLot("h1", "TCS", -10000, "STCG"),
            MockLot("h2", "INFY", -15000, "LTCG"),
        ]

    monkeypatch.setattr(
        "app.services.tax_setoff_service.CapitalGainsService.calculate_capital_gains",
        lambda self, portfolio_id, user_id, fy_year, slab_rate: MockCGSummary(),
    )
    monkeypatch.setattr(
        "app.services.tax_setoff_service.UnrealizedTaxService.calculate_unrealized_gains",
        lambda self, user_id, fy_year, portfolio_id, slab_rate: MockUnrealizedSummary(),
    )

    service = TaxSetOffService(db)

    harvesting = service.get_loss_harvesting_opportunities(
        user_id=user_id, fy_year=fy_year, slab_rate=30.0
    )

    assert harvesting.total_harvestable_stcl == Decimal("10000.00")
    assert harvesting.total_harvestable_ltcl == Decimal("15000.00")
    assert len(harvesting.harvesting_opportunities) == 2

    # First item should be highest tax saved (TCS STCL: 10000 * 30% = 3000)
    top_item = harvesting.harvesting_opportunities[0]
    assert top_item.asset_ticker == "TCS"
    assert top_item.potential_tax_saved == Decimal("3000.00")

    second_item = harvesting.harvesting_opportunities[1]
    assert second_item.asset_ticker == "INFY"
    assert second_item.potential_tax_saved == Decimal("1875.00")


def test_tax_loss_harvesting_when_ltcg_below_125k_threshold(db, monkeypatch):
    """
    Scenario 5 (Corner Case): Realized LTCG is ₹28,070 (< ₹125,000 exemption limit).
    Current LTCG tax is ₹0. Harvesting losses yields ₹0 current tax savings,
    and recommendations advise carrying forward losses up to 8 years.
    """
    user_id = str(uuid.uuid4())
    fy_year = "2026-27"

    class MockGain:
        def __init__(self, gain, gain_type):
            self.gain = Decimal(str(gain))
            self.gain_type = gain_type

    class MockCGSummary:
        gains = [MockGain(28070, "LTCG")]
        estimated_stcg_tax = Decimal("0.0")
        estimated_ltcg_tax = Decimal("0.0")
        total_stcg = Decimal("0.0")
        total_ltcg = Decimal("28070.0")

    class MockLot:
        def __init__(self, ticker, unrealized_gain, gain_type):
            self.holding_id = str(uuid.uuid4())
            self.asset_id = str(uuid.uuid4())
            self.asset_ticker = ticker
            self.asset_name = ticker
            self.asset_type = "EQUITY"
            self.buy_date = "2025-05-01"
            self.quantity = Decimal("100")
            self.buy_price = Decimal("200.0")
            self.current_price = Decimal("100.0")
            self.total_cost = Decimal("20000.0")
            self.market_value = Decimal("10000.0")
            self.unrealized_gain = Decimal(str(unrealized_gain))
            self.gain_type = gain_type
            self.holding_days = 100

    class MockUnrealizedSummary:
        lots = [
            MockLot("SILVERBEES", -35760, "STCG"),
            MockLot("VIVIMEDLAB", -18655.8, "LTCG"),
        ]

    monkeypatch.setattr(
        "app.services.tax_setoff_service.CapitalGainsService.calculate_capital_gains",
        lambda self, portfolio_id, user_id, fy_year, slab_rate: MockCGSummary(),
    )
    monkeypatch.setattr(
        "app.services.tax_setoff_service.UnrealizedTaxService.calculate_unrealized_gains",
        lambda self, user_id, fy_year, portfolio_id, slab_rate: MockUnrealizedSummary(),
    )

    service = TaxSetOffService(db)
    harvesting = service.get_loss_harvesting_opportunities(
        user_id=user_id, fy_year=fy_year, slab_rate=30.0
    )

    assert harvesting.total_potential_tax_savings == Decimal("0.00")
    for item in harvesting.harvesting_opportunities:
        assert item.potential_tax_saved == Decimal("0.00")
        assert "carry forward for up to 8 years" in item.recommendation_reason


def test_tax_loss_harvesting_with_equity_stcg_20_percent_rate(db, monkeypatch):
    """
    Scenario 6 (Corner Case): Realized STCG is Equity 111A ₹5,000 (taxed at 20% = ₹1,000 tax).
    Harvesting ₹10,000 STCL offsets ₹5,000 STCG at 20% (saving ₹1,000 tax, NOT 30% slab rate ₹1,500).
    """
    user_id = str(uuid.uuid4())
    fy_year = "2026-27"

    class MockGain:
        def __init__(self, gain, gain_type):
            self.gain = Decimal(str(gain))
            self.gain_type = gain_type

    class MockCGSummary:
        gains = [MockGain(5000, "STCG")]
        estimated_stcg_tax = Decimal("1000.00")  # 20% rate
        estimated_ltcg_tax = Decimal("0.0")
        total_stcg = Decimal("5000.0")
        total_ltcg = Decimal("0.0")

    class MockLot:
        def __init__(self, ticker, unrealized_gain, gain_type):
            self.holding_id = str(uuid.uuid4())
            self.asset_id = str(uuid.uuid4())
            self.asset_ticker = ticker
            self.asset_name = ticker
            self.asset_type = "EQUITY"
            self.buy_date = "2025-05-01"
            self.quantity = Decimal("100")
            self.buy_price = Decimal("200.0")
            self.current_price = Decimal("100.0")
            self.total_cost = Decimal("20000.0")
            self.market_value = Decimal("10000.0")
            self.unrealized_gain = Decimal(str(unrealized_gain))
            self.gain_type = gain_type
            self.holding_days = 100

    class MockUnrealizedSummary:
        lots = [MockLot("GICRE", -10000, "STCG")]

    monkeypatch.setattr(
        "app.services.tax_setoff_service.CapitalGainsService.calculate_capital_gains",
        lambda self, portfolio_id, user_id, fy_year, slab_rate: MockCGSummary(),
    )
    monkeypatch.setattr(
        "app.services.tax_setoff_service.UnrealizedTaxService.calculate_unrealized_gains",
        lambda self, user_id, fy_year, portfolio_id, slab_rate: MockUnrealizedSummary(),
    )

    service = TaxSetOffService(db)
    harvesting = service.get_loss_harvesting_opportunities(
        user_id=user_id, fy_year=fy_year, slab_rate=30.0
    )

    item = harvesting.harvesting_opportunities[0]
    assert item.potential_tax_saved == Decimal("1000.00")
    assert "20.0%" in item.recommendation_reason


def test_setoff_and_harvesting_empty_portfolio_or_no_losses(db, monkeypatch):
    """
    Scenario 7 (Corner Case): User has no realized gains, no brought forward losses,
    and no open negative lots.
    """
    user_id = str(uuid.uuid4())
    fy_year = "2026-27"

    class MockCGSummary:
        gains = []
        estimated_stcg_tax = Decimal("0.0")
        estimated_ltcg_tax = Decimal("0.0")
        total_stcg = Decimal("0.0")
        total_ltcg = Decimal("0.0")

    class MockUnrealizedSummary:
        lots = []

    monkeypatch.setattr(
        "app.services.tax_setoff_service.CapitalGainsService.calculate_capital_gains",
        lambda self, portfolio_id, user_id, fy_year, slab_rate: MockCGSummary(),
    )
    monkeypatch.setattr(
        "app.services.tax_setoff_service.UnrealizedTaxService.calculate_unrealized_gains",
        lambda self, user_id, fy_year, portfolio_id, slab_rate: MockUnrealizedSummary(),
    )

    service = TaxSetOffService(db)
    setoff = service.calculate_net_capital_gains(user_id=user_id, fy_year=fy_year)
    harvesting = service.get_loss_harvesting_opportunities(
        user_id=user_id, fy_year=fy_year
    )

    assert setoff.breakdown.net_taxable_stcg == Decimal("0.0")
    assert setoff.breakdown.net_taxable_ltcg == Decimal("0.0")
    assert setoff.breakdown.net_estimated_tax == Decimal("0.0")
    assert len(harvesting.harvesting_opportunities) == 0
    assert harvesting.total_potential_tax_savings == Decimal("0.0")

