import re

# Fix Dict in crud_holding.py
with open("backend/app/crud/crud_holding.py", "r") as f:
    content = f.read()

if "from typing import Dict" not in content:
    content = content.replace("from typing import ", "from typing import Dict, ")
content = content.replace('"[__calculate_holdings_and_summary_from_data]', '"[...from_data]')

with open("backend/app/crud/crud_holding.py", "w") as f:
    f.write(content)

# Fix duplicate get_multi_by_portfolios in crud_transaction.py
with open("backend/app/crud/crud_transaction.py", "r") as f:
    content = f.read()

parts = content.split("def get_multi_by_portfolios")
if len(parts) > 2:
    # KEEP ONLY the first one
    keep_part = parts[0] + "def get_multi_by_portfolios" + parts[1]

    # We need to remove the other implementations. They might have been added multiple times by my sed command.
    pass # Wait, let's look at crud_transaction.py
