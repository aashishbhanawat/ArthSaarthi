import re

with open("backend/app/crud/crud_analytics.py", "r") as f:
    content = f.read()

# I also need to change `for buy_tx in buys:` to `for lot in buys:` in the unrealized_cash_flows loop.
search_pattern = r"""    unrealized_cash_flows = \[\]
    for buy_tx in buys:
        if buy_tx\.quantity > 0:
            if \(
                buy_tx\.transaction_type == "RSU_VEST"
                and buy_tx\.details
                and "fmv" in buy_tx\.details
            \):
                buy_price = Decimal\(str\(buy_tx\.details\["fmv"\]\)\)
            else:
                buy_price = \(
                    buy_tx\.price_per_unit
                    if buy_tx\.price_per_unit is not None
                    else Decimal\("0\.0"\)
                \)

            # --- FX Rate Adjustment ---
            buy_fx_rate = \(
                Decimal\(str\(buy_tx\.details\.get\("fx_rate", 1\)\)\)
                if buy_tx\.details
                else Decimal\(1\)
            \)

            unrealized_cash_flows\.append\(
                \(
                    buy_tx\.transaction_date\.date\(\),
                    float\(-lot\["available_quantity"\] \* buy_price \* buy_fx_rate\)
                \)
            \)"""

replacement = """    unrealized_cash_flows = []
    for lot in buys:
        if lot["available_quantity"] > 0:
            buy_tx = lot["transaction"]
            if (
                buy_tx.transaction_type == "RSU_VEST"
                and buy_tx.details
                and "fmv" in buy_tx.details
            ):
                buy_price = Decimal(str(buy_tx.details["fmv"]))
            else:
                buy_price = (
                    buy_tx.price_per_unit
                    if buy_tx.price_per_unit is not None
                    else Decimal("0.0")
                )

            # --- FX Rate Adjustment ---
            buy_fx_rate = (
                Decimal(str(buy_tx.details.get("fx_rate", 1)))
                if buy_tx.details
                else Decimal(1)
            )

            unrealized_cash_flows.append(
                (
                    buy_tx.transaction_date.date(),
                    float(-lot["available_quantity"] * buy_price * buy_fx_rate)
                )
            )"""

content = re.sub(search_pattern, replacement, content)

with open("backend/app/crud/crud_analytics.py", "w") as f:
    f.write(content)
