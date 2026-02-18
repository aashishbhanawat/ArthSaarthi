from datetime import date


# Mocking the service method for isolation
def check_scenario():
    buy_date = date(2023, 3, 1)
    sell_date = date(2026, 1, 1)
    days = (sell_date - buy_date).days

    # Logic extracted from capital_gains_service.py
    DATE_2023_04_01 = date(2023, 4, 1)
    DATE_2024_07_23 = date(2024, 7, 23)

    is_ltcg = False

    # Category = DEBT
    # 1. Invested ON/AFTER 1 Apr 2023
    if buy_date >= DATE_2023_04_01:
        is_ltcg = False
    else:
        # 2. Invested BEFORE 1 Apr 2023
        if sell_date >= DATE_2024_07_23:
            is_ltcg = days > 730
        else:
            is_ltcg = days > 1095

    print(f"Buy: {buy_date}, Sell: {sell_date}")
    print(f"Days: {days}")
    print(f"Result: {'LTCG' if is_ltcg else 'STCG'}")

if __name__ == "__main__":
    check_scenario()
