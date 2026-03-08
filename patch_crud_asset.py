import sys
import re

with open("backend/app/crud/crud_asset.py", "r") as f:
    content = f.read()

# Replace the doubled definition
content = content.replace("""    def get_multi_by_portfolios(
        self, db: Session, *, portfolio_ids: List[uuid.UUID], asset_type: Optional[str] = None
    ) -> List[Asset]:
        self, db: Session, *, portfolio_ids: List[uuid.UUID], asset_type: Optional[str] = None
    ) -> List[Asset]:""", """    def get_multi_by_portfolios(
        self, db: Session, *, portfolio_ids: List[uuid.UUID], asset_type: Optional[str] = None
    ) -> List[Asset]:""")

with open("backend/app/crud/crud_asset.py", "w") as f:
    f.write(content)
