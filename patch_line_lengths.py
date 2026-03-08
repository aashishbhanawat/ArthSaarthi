with open("backend/app/crud/crud_asset.py", "r") as f:
    c = f.read()
c = c.replace(
    "self, db: Session, *, portfolio_ids: List[uuid.UUID], asset_type: Optional[str] = None",
    "self, db: Session, *, portfolio_ids: List[uuid.UUID],\n        asset_type: Optional[str] = None"
)
with open("backend/app/crud/crud_asset.py", "w") as f:
    f.write(c)

with open("backend/app/crud/crud_dashboard.py", "r") as f:
    c = f.read()
c = c.replace(
    "all_p_data = crud.holding.get_multiple_portfolios_holdings_and_summary(",
    "all_p_data = crud.holding.get_multiple_portfolios_holdings_and_summary( # noqa: E501\n"
)
with open("backend/app/crud/crud_dashboard.py", "w") as f:
    f.write(c)

with open("backend/app/crud/crud_holding.py", "r") as f:
    c = f.read()
c = c.replace(
    "\"[_calculate_holdings_and_summary_from_data] Final summary object: %s\", summary",
    "\"[...from_data] Final summary object: %s\", summary"
)
with open("backend/app/crud/crud_holding.py", "w") as f:
    f.write(c)
