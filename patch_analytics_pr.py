import re

with open("backend/app/crud/crud_analytics.py", "r") as f:
    content = f.read()

# Replace Priority 1 and Priority 2 sections to use the new dict structure
# and immediately increment fifo_index.

# Priority 1
search_pattern1 = r"""                buy_copy = buy_id_to_copy_map\.get\(link\.buy_transaction_id\)
                if not buy_copy:
                    logger\.warning\(
                        f"Linked Buy ID \{link\.buy_transaction_id\} "
                        f"not found in transactions\."
                    \)
                    continue

                # Determine quantity to use from this link
                # \(capped by what's left in sell\)
                match_quantity = min\(
                    Decimal\(str\(link\.quantity\)\), sell_quantity_to_match
                \)
                if match_quantity <= 0:
                    continue

                # Safety check: available buy quantity
                if buy_copy\.quantity < match_quantity:
                    logger\.warning\(
                        f"Buy ID \{buy_copy\.id\} has insufficient quantity "
                        f"\(\{buy_copy\.quantity\}\) for link \(\{match_quantity\}\)\. "
                        f"Using available\."
                    \)
                    match_quantity = buy_copy\.quantity

                # --- Price & P&L Calculation logic \(Shared\) ---
                if \(
                    buy_copy\.transaction_type == "RSU_VEST"
                    and buy_copy\.details
                    and "fmv" in buy_copy\.details
                \):
                    buy_price = Decimal\(str\(buy_copy\.details\["fmv"\]\)\)
                else:
                    buy_price = \(
                        buy_copy\.price_per_unit
                        if buy_copy\.price_per_unit is not None
                        else Decimal\("0\.0"\)
                    \)

                buy_fx_rate = \(
                    Decimal\(str\(buy_copy\.details\.get\("fx_rate", 1\)\)\)
                    if buy_copy\.details
                    else Decimal\(1\)
                \)

                buy_cost_for_match = match_quantity \* buy_price \* buy_fx_rate
                sell_proceeds_for_match = match_quantity \* sell_price \* sell_fx_rate

                # P&L
                pnl = sell_proceeds_for_match - buy_cost_for_match
                realized_pnl \+= pnl

                # Cashflows
                realized_cash_flows\.append\(
                    \(buy_copy\.transaction_date\.date\(\), float\(-buy_cost_for_match\)\)
                \)
                realized_cash_flows\.append\(
                    \(
                        sell_tx\.transaction_date\.date\(\),
                        float\(sell_proceeds_for_match\),
                    \)
                \)

                # Update state
                buy_copy\.quantity -= match_quantity
                sell_quantity_to_match -= match_quantity"""

replacement1 = """                lot = buy_id_to_copy_map.get(link.buy_transaction_id)
                if not lot:
                    logger.warning(
                        f"Linked Buy ID {link.buy_transaction_id} "
                        f"not found in transactions."
                    )
                    continue

                buy_tx = lot["transaction"]

                # Determine quantity to use from this link
                # (capped by what's left in sell)
                match_quantity = min(
                    Decimal(str(link.quantity)), sell_quantity_to_match
                )
                if match_quantity <= 0:
                    continue

                # Safety check: available buy quantity
                if lot["available_quantity"] < match_quantity:
                    logger.warning(
                        f"Buy ID {buy_tx.id} has insufficient quantity "
                        f"({lot['available_quantity']}) for link ({match_quantity}). "
                        f"Using available."
                    )
                    match_quantity = lot["available_quantity"]

                # --- Price & P&L Calculation logic (Shared) ---
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

                buy_fx_rate = (
                    Decimal(str(buy_tx.details.get("fx_rate", 1)))
                    if buy_tx.details
                    else Decimal(1)
                )

                buy_cost_for_match = match_quantity * buy_price * buy_fx_rate
                sell_proceeds_for_match = match_quantity * sell_price * sell_fx_rate

                # P&L
                pnl = sell_proceeds_for_match - buy_cost_for_match
                realized_pnl += pnl

                # Cashflows
                realized_cash_flows.append(
                    (buy_tx.transaction_date.date(), float(-buy_cost_for_match))
                )
                realized_cash_flows.append(
                    (
                        sell_tx.transaction_date.date(),
                        float(sell_proceeds_for_match),
                    )
                )

                # Update state
                lot["available_quantity"] -= match_quantity
                sell_quantity_to_match -= match_quantity"""


# Priority 2
search_pattern2 = r"""        # --- Priority 2: FIFO for remaining quantity ---
        if sell_quantity_to_match > 0:
            while fifo_index < len\(buys\) and sell_quantity_to_match > 0:
                buy_copy = buys\[fifo_index\]
                if buy_copy\.quantity <= 0:
                    fifo_index \+= 1
                    continue

                match_quantity = min\(sell_quantity_to_match, buy_copy\.quantity\)

                # --- Price & P&L Calculation logic \(Shared\) ---
                if \(
                    buy_copy\.transaction_type == "RSU_VEST"
                    and buy_copy\.details
                    and "fmv" in buy_copy\.details
                \):
                    buy_price = Decimal\(str\(buy_copy\.details\["fmv"\]\)\)
                else:
                    buy_price = \(
                        buy_copy\.price_per_unit
                        if buy_copy\.price_per_unit is not None
                        else Decimal\("0\.0"\)
                    \)

                buy_fx_rate = \(
                    Decimal\(str\(buy_copy\.details\.get\("fx_rate", 1\)\)\)
                    if buy_copy\.details
                    else Decimal\(1\)
                \)

                buy_cost_for_match = match_quantity \* buy_price \* buy_fx_rate
                sell_proceeds_for_match = match_quantity \* sell_price \* sell_fx_rate

                # P&L
                pnl = sell_proceeds_for_match - buy_cost_for_match
                realized_pnl \+= pnl

                # Cashflows
                realized_cash_flows\.append\(
                    \(buy_copy\.transaction_date\.date\(\), float\(-buy_cost_for_match\)\)
                \)
                realized_cash_flows\.append\(
                    \(
                        sell_tx\.transaction_date\.date\(\),
                        float\(sell_proceeds_for_match\),
                    \)
                \)

                # Update state
                buy_copy\.quantity -= match_quantity
                sell_quantity_to_match -= match_quantity

                if buy_copy\.quantity <= 0:
                    fifo_index \+= 1"""

replacement2 = """        # --- Priority 2: FIFO for remaining quantity ---
        if sell_quantity_to_match > 0:
            while fifo_index < len(buys) and sell_quantity_to_match > 0:
                lot = buys[fifo_index]
                if lot["available_quantity"] <= 0:
                    fifo_index += 1
                    continue

                buy_tx = lot["transaction"]
                match_quantity = min(sell_quantity_to_match, lot["available_quantity"])

                # --- Price & P&L Calculation logic (Shared) ---
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

                buy_fx_rate = (
                    Decimal(str(buy_tx.details.get("fx_rate", 1)))
                    if buy_tx.details
                    else Decimal(1)
                )

                buy_cost_for_match = match_quantity * buy_price * buy_fx_rate
                sell_proceeds_for_match = match_quantity * sell_price * sell_fx_rate

                # P&L
                pnl = sell_proceeds_for_match - buy_cost_for_match
                realized_pnl += pnl

                # Cashflows
                realized_cash_flows.append(
                    (buy_tx.transaction_date.date(), float(-buy_cost_for_match))
                )
                realized_cash_flows.append(
                    (
                        sell_tx.transaction_date.date(),
                        float(sell_proceeds_for_match),
                    )
                )

                # Update state
                lot["available_quantity"] -= match_quantity
                sell_quantity_to_match -= match_quantity

                if lot["available_quantity"] <= 0:
                    fifo_index += 1"""


# Unrealized section
search_pattern3 = r"""    unrealized_cash_flows = \[\]
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

            buy_cost = buy_tx\.quantity \* buy_price \* buy_fx_rate

            unrealized_cash_flows\.append\(
                \(buy_tx\.transaction_date\.date\(\), float\(-buy_cost\)\)
            \)"""

replacement3 = """    unrealized_cash_flows = []
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

            buy_cost = lot["available_quantity"] * buy_price * buy_fx_rate

            unrealized_cash_flows.append(
                (buy_tx.transaction_date.date(), float(-buy_cost))
            )"""

content = re.sub(search_pattern1, replacement1, content)
content = re.sub(search_pattern2, replacement2, content)
content = re.sub(search_pattern3, replacement3, content)


with open("backend/app/crud/crud_analytics.py", "w") as f:
    f.write(content)
