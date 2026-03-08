import sys

with open("backend/app/crud/crud_dashboard.py", "r") as f:
    content = f.read()

replacement = """
                        # If calculating for 'all' portfolios, we have to sum them up
                        portfolios = crud.portfolio.get_multi_by_owner(
                            db=db, user_id=user.id
                        )
                        portfolio_ids = [p.id for p in portfolios]
                        all_p_data = crud.holding.get_multiple_portfolios_holdings_and_summary(
                            db, portfolio_ids=portfolio_ids
                        )
                        for p in portfolios:
                            if p.id in all_p_data:
                                day_total_value += all_p_data[p.id].summary.total_value"""

# find original:
original = """
                        # If calculating for 'all' portfolios, we have to sum them up
                        portfolios = crud.portfolio.get_multi_by_owner(
                            db=db, user_id=user.id
                        )
                        for p in portfolios:
                            p_data = crud.holding.get_portfolio_holdings_and_summary(
                                db, portfolio_id=p.id
                            )
                            day_total_value += p_data.summary.total_value"""

if original in content:
    content = content.replace(original, replacement)
    with open("backend/app/crud/crud_dashboard.py", "w") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Could not find original block")
