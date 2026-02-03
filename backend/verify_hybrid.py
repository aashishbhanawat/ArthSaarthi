from app.models.asset import Asset
from app.services.capital_gains_service import CapitalGainsService


def verify_hybrid_logic():
    # Mock Service (no DB needed for this helper check)
    service = CapitalGainsService(None)

    test_cases = [
        {
            "name": "HDFC Balanced Advantage Fund",
            "sector": "Mutual Fund",
            "expected": True,
        },
        {"name": "SBI Arbitrage Fund", "sector": "Mutual Fund", "expected": True},
        {
            "name": "ICICI Prudential Equity & Debt Fund",
            "sector": "Hybrid",
            "expected": True,
        },
        {"name": "Kotak Dynamic Bond Fund", "sector": "Debt", "expected": True},
        {
            "name": "Franklin India Other Scheme",
            "sector": "Other Scheme",
            "expected": True,
        },  # New test case
        {"name": "Axis Bluechip Fund", "sector": "Equity", "expected": False},
        {"name": "HDFC Liquid Fund", "sector": "Debt", "expected": False},
    ]

    print("--- Verifying Hybrid Detection ---")
    for case in test_cases:
        asset = Asset(
            name=case["name"],
            sector=case["sector"],
            asset_type="Mutual Fund"
        )
        result = service._is_hybrid_fund(asset)
        status = "PASS" if result == case["expected"] else "FAIL"
        print(
            f"[{status}] {case['name']} ({case['sector']}) -> {result} "
            f"(Expected: {case['expected']})"
        )

if __name__ == "__main__":
    verify_hybrid_logic()
