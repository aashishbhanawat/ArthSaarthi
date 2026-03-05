import re

with open("backend/app/crud/crud_transaction.py", "r") as f:
    content = f.read()

search_pattern = r"""                        take = min\(lot\["available_quantity"\], sell_qty\)
                        lot\["available_quantity"\] -= take
                        sell_qty -= take"""

replacement = """                        take = min(lot["available_quantity"], sell_qty)
                        lot["available_quantity"] -= take
                        sell_qty -= take

                        if lot["available_quantity"] <= 0:
                            fifo_index += 1"""

content = re.sub(search_pattern, replacement, content)

with open("backend/app/crud/crud_transaction.py", "w") as f:
    f.write(content)
