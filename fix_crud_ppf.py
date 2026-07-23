import re

with open('backend/app/crud/crud_ppf.py', 'r') as f:
    content = f.read()

new_fetch_logic = """    if transactions is None:
        if portfolio_id:
            transactions = crud.transaction.get_multi_by_portfolio_and_asset(
                db, portfolio_id=portfolio_id, asset_id=ppf_asset.id
            )
        else:
            transactions = crud.transaction.get_multi_by_asset(db, asset_id=ppf_asset.id)
            if user_id:
                # filter in python memory to avoid db schema incompatibilities in test sqlite
                from app.models.portfolio import Portfolio
                user_portfolios = db.query(Portfolio.id).filter(Portfolio.user_id == user_id).all()
                portfolio_ids = {p.id for p in user_portfolios}
                transactions = [t for t in transactions if t.portfolio_id in portfolio_ids]"""

content = re.sub(
    r'    if transactions is None:\n        transactions = crud\.transaction\.get_multi_by_asset\(db, asset_id=ppf_asset\.id\)',
    new_fetch_logic,
    content
)

content = re.sub(
    r'def process_ppf_holding\(\n    db: Session, ppf_asset: Asset, portfolio_id: uuid.UUID \| None,\n    calculation_date: date = None, simulate_only: bool = False,\n    transactions: List\[Transaction\] = None,\n    ppf_rates: List\[HistoricalInterestRate\] = None,\n\) -> schemas.Holding:',
    'def process_ppf_holding(\n    db: Session, ppf_asset: Asset, portfolio_id: uuid.UUID | None,\n    calculation_date: date = None, simulate_only: bool = False,\n    transactions: List[Transaction] = None,\n    ppf_rates: List[HistoricalInterestRate] = None,\n    user_id: uuid.UUID | None = None,\n) -> schemas.Holding:',
    content,
    flags=re.MULTILINE
)


with open('backend/app/crud/crud_ppf.py', 'w') as f:
    f.write(content)
