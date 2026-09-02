from decimal import ROUND_HALF_UP, Decimal
from typing import Optional


class SalaryExemptionService:
    """
    Statutory Section 10(13A) HRA Exemption calculation service benchmarked 100%
    against local/TaxCalc_2027.xlsx (Sheet 'IT 2026-27', Cell D101).
    """

    @staticmethod
    def calculate_hra_exemption(
        basic_amount: Optional[Decimal] = None,
        hra_amount: Optional[Decimal] = None,
        da_amount: Optional[Decimal] = None,
        rent_paid: Optional[Decimal] = None,
        is_metro: bool = False,
    ) -> Decimal:
        """
        Calculate Section 10(13A) HRA exemption amount.

        Formula:
        HRA Exemption = max(0, min(
            Actual HRA Received,
            Rent Paid - 10% * (Basic + DA),
            (50% if Metro else 40%) * (Basic + DA)
        ))
        """
        basic = basic_amount if basic_amount is not None else Decimal("0.00")
        hra = hra_amount if hra_amount is not None else Decimal("0.00")
        da = da_amount if da_amount is not None else Decimal("0.00")
        rent = rent_paid if rent_paid is not None else Decimal("0.00")

        if hra <= Decimal("0.00") or rent <= Decimal("0.00"):
            return Decimal("0.00")

        basic_da = basic + da
        if basic_da <= Decimal("0.00"):
            return Decimal("0.00")

        # Option 1: Actual HRA Received
        opt1 = hra

        # Option 2: Rent Paid - 10% of (Basic + DA)
        ten_percent_salary = (basic_da * Decimal("0.10")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        opt2 = rent - ten_percent_salary

        # Option 3: 50% of (Basic + DA) for Metro else 40% of (Basic + DA) for Non-Metro
        cap_percent = Decimal("0.50") if is_metro else Decimal("0.40")
        opt3 = (basic_da * cap_percent).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        exemption = min(opt1, opt2, opt3)
        return max(Decimal("0.00"), exemption).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
