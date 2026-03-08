import sys

with open("backend/app/crud/crud_dashboard.py", "r") as f:
    content = f.read()

replacement = """
            if current_day == end_date:
                try:
                    portfolio_data = crud.holding.get_portfolio_holdings_and_summary(
                        db, portfolio_id=portfolio_id
                    ) if portfolio_id else None

                    if portfolio_data:"""

original = """
            if current_day == end_date:
                try:

                    if portfolio_data:"""

content = content.replace(original, replacement)

with open("backend/app/crud/crud_dashboard.py", "w") as f:
    f.write(content)
