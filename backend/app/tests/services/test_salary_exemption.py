from decimal import Decimal

from app.services.salary_exemption_service import SalaryExemptionService


def test_hra_exemption_excel_benchmark_parity():
    """
    Test Section 10(13A) HRA Exemption calculation benchmarked 100% against
    local/TaxCalc_2027.xlsx (Sheet 'IT 2026-27', Cell D101).

    Formula:
    MIN(Actual HRA, Rent Paid - 10%*(Basic+DA), (50% if Metro else 40%)*(Basic+DA))
    """
    # Test case 1: Excel benchmark standard case
    # Basic = 6,00,000, HRA = 3,00,000, Rent Paid = 2,40,000, Metro = True
    # Opt1 = 3,00,000
    # Opt2 = 2,40,000 - 60,000 = 1,80,000
    # Opt3 = 50% * 6,00,000 = 3,00,000
    # Minimum = 1,80,000
    exemption1 = SalaryExemptionService.calculate_hra_exemption(
        basic_amount=Decimal("600000.00"),
        hra_amount=Decimal("300000.00"),
        da_amount=Decimal("0.00"),
        rent_paid=Decimal("240000.00"),
        is_metro=True,
    )
    assert exemption1 == Decimal("180000.00")

    # Test case 2: Metro vs Non-Metro limit switching
    # Basic = 10,00,000, HRA = 5,00,000, Rent Paid = 6,00,000
    # Opt1 = 5,00,000
    # Opt2 = 6,00,000 - 1,00,000 = 5,00,000
    # Opt3 (Metro 50%) = 5,00,000
    # Opt3 (Non-Metro 40%) = 4,00,000
    exemption_metro = SalaryExemptionService.calculate_hra_exemption(
        basic_amount=Decimal("1000000.00"),
        hra_amount=Decimal("500000.00"),
        da_amount=Decimal("0.00"),
        rent_paid=Decimal("600000.00"),
        is_metro=True,
    )
    assert exemption_metro == Decimal("500000.00")

    exemption_non_metro = SalaryExemptionService.calculate_hra_exemption(
        basic_amount=Decimal("1000000.00"),
        hra_amount=Decimal("500000.00"),
        da_amount=Decimal("0.00"),
        rent_paid=Decimal("600000.00"),
        is_metro=False,
    )
    assert exemption_non_metro == Decimal("400000.00")


def test_hra_exemption_corner_cases():
    # Rent paid less than 10% basic+da
    exemption_low_rent = SalaryExemptionService.calculate_hra_exemption(
        basic_amount=Decimal("500000.00"),
        hra_amount=Decimal("200000.00"),
        # 10% of basic is 50,000 -> Rent - 10% = -10,000 -> max(0, -10000) = 0
        rent_paid=Decimal("40000.00"),
        is_metro=True,
    )
    assert exemption_low_rent == Decimal("0.00")

    # Zero HRA received
    exemption_zero_hra = SalaryExemptionService.calculate_hra_exemption(
        basic_amount=Decimal("500000.00"),
        hra_amount=Decimal("0.00"),
        da_amount=Decimal("0.00"),
        rent_paid=Decimal("100000.00"),
        is_metro=True,
    )
    assert exemption_zero_hra == Decimal("0.00")

    # Zero rent paid
    exemption_zero_rent = SalaryExemptionService.calculate_hra_exemption(
        basic_amount=Decimal("500000.00"),
        hra_amount=Decimal("200000.00"),
        da_amount=Decimal("0.00"),
        rent_paid=Decimal("0.00"),
        is_metro=True,
    )
    assert exemption_zero_rent == Decimal("0.00")
